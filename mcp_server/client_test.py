"""Scripted MCP client — the chapter's acceptance harness.

Checks (matching the exercise checklist):
  1. The server exposes the three tools (tools/list via the SDK).
  2. Asking «قیمت طلای داخلی الان چقدره؟» makes the model call BOTH
     get_gold_price and get_usd_rate — not just one.
  3. Failure drill (run with --break-usd): with an invalid NAVASAN key the
     tool returns {"error": ...} and the model reports the missing data
     instead of making a number up.

Usage:
    python mcp_server/client_test.py [--break-usd]
"""

import argparse
import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from mcp_server.prompts import GOLD_PRICE_PROMPT, TREND_PROMPT

EXPECTED_TOOLS = {"get_stock_info", "get_gold_price", "get_usd_rate"}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


async def run(break_usd: bool, trend: bool) -> int:
    env = dict(os.environ)
    if break_usd:
        env["NAVASAN_API_KEY"] = "invalid-key-failure-drill"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server/server.py"],
        env=env,
        cwd=ROOT,
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # --- check 1: tools/list ---
            tools_response = await session.list_tools()
            found = {t.name for t in tools_response.tools}
            missing = EXPECTED_TOOLS - found
            print(f"tools/list -> {sorted(found)}")
            if missing:
                print(f"FAIL: missing tools: {missing}")
                return 1
            print("PASS: all three tools are registered\n")

            mcp_tools = {
                t.name: {
                    "name": t.name,
                    "description": t.description or "",
                    "input_schema": t.inputSchema,
                }
                for t in tools_response.tools
            }

            # --- check 2 (+3 in break mode): the composite gold question ---
            system = TREND_PROMPT if trend else GOLD_PRICE_PROMPT
            question = (
                "روند بازار طلا الان چطوره و قیمت سهم فولاد چنده؟"
                if trend
                else "قیمت طلای داخلی الان تقریباً چقدره؟"
            )
            print(f"QUESTION: {question}\n")

            client = Anthropic()
            messages = [{"role": "user", "content": question}]
            called = []
            tool_errors = []

            for _ in range(6):  # bounded agentic loop
                response = client.messages.create(
                    model=os.environ.get("LLM_MODEL", "GLM-5.3-Flash"),
                    max_tokens=4096,
                    thinking={"type": "disabled"},
                    system=system,
                    tools=list(mcp_tools.values()),
                    messages=messages,
                )
                if response.stop_reason != "tool_use":
                    final = "".join(
                        b.text for b in response.content if b.type == "text"
                    )
                    break
                messages.append({"role": "assistant", "content": response.content})
                results = []
                for block in response.content:
                    if block.type != "tool_use":
                        continue
                    called.append(block.name)
                    print(f"  -> model called tool: {block.name}({block.input})")
                    result = await session.call_tool(block.name, block.input)
                    payload = "".join(
                        c.text for c in result.content if hasattr(c, "text")
                    )
                    if '"error"' in payload:
                        tool_errors.append((block.name, payload[:160]))
                    results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": payload,
                    })
                messages.append({"role": "user", "content": results})
            else:
                print("FAIL: tool loop exceeded iteration limit")
                return 1

            print(f"\nANSWER:\n{final}\n")

            if trend:
                # Demo run — no strict assertions, just show the multi-tool path.
                print(f"tools used: {sorted(set(called))}")
                return 0

            # --- acceptance assertions ---
            ok = True
            for tool in ("get_gold_price", "get_usd_rate"):
                if tool not in called:
                    print(f"FAIL: '{tool}' was never called")
                    ok = False
                else:
                    print(f"PASS: '{tool}' was called")

            if break_usd:
                if not tool_errors:
                    print("FAIL: expected a tool error in failure-drill mode")
                    ok = False
                else:
                    print(f"PASS: tool error surfaced: {tool_errors[0][1]}")
                    if "در دسترس نیست" in final or "در دسترس نبود" in final:
                        print("PASS: model explicitly reported the missing data")
                    else:
                        print("WARN: model answer does not explicitly say data unavailable")
            elif tool_errors:
                print(f"FAIL: unexpected tool errors in normal mode: {tool_errors}")
                ok = False

            return 0 if ok else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--break-usd", action="store_true",
                        help="run with an invalid NAVASAN key (failure drill)")
    parser.add_argument("--trend", action="store_true",
                        help="run the extra market-trend question demo")
    args = parser.parse_args()
    sys.exit(asyncio.run(run(args.break_usd, args.trend)))

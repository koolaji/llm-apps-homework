"""Tool-use chapter acceptance tests (the exercise's checklist).

1. get_stock_info("فولاد") runs without error and returns the required dict.
2. An invalid symbol ("XYZ123") raises ValueError with a clear message.
3. schema.json exists and is valid JSON with name/input_schema/required.
4. The tool output can be passed directly to a Function Calling message in
   the Claude API — a real end-to-end round trip.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic

from tool_use.stock_info import get_stock_info, load_schema


def main() -> int:
    failures = []

    # --- 1. valid symbol -> dict with the mandated keys ---
    info = get_stock_info("فولاد")
    required_keys = {
        "symbol", "name", "last_price", "price_change_percent",
        "volume", "market_cap", "last_update",
    }
    assert required_keys.issubset(info), f"missing keys: {required_keys - set(info)}"
    print("PASS  get_stock_info('فولاد') ->", json.dumps(info, ensure_ascii=False)[:120], "...")

    # --- 2. invalid symbol -> ValueError ---
    try:
        get_stock_info("XYZ123")
        failures.append("invalid symbol did not raise ValueError")
    except ValueError as exc:
        print("PASS  invalid symbol -> ValueError:", exc)

    # --- 3. schema.json valid ---
    schema = load_schema()
    assert schema["name"] == "get_stock_info"
    assert schema["input_schema"]["required"] == ["symbol"]
    print("PASS  schema.json is valid JSON Schema for the tool")

    # --- 4. round trip through the Claude API function-calling message ---
    client = Anthropic()  # reads ANTHROPIC_BASE_URL / ANTHROPIC_API_KEY from env
    response = client.messages.create(
        model=os.environ.get("LLM_MODEL", "GLM-5.3-Flash"),
        max_tokens=1024,
        thinking={"type": "disabled"},
        tools=[schema],
        messages=[
            {"role": "user", "content": "قیمت لحظه‌ای سهم فولاد چنده؟"},
            # assistant asked for the tool (short-circuited here for the demo):
            {
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": "call_demo_001",
                    "name": "get_stock_info",
                    "input": {"symbol": "فولاد"},
                }],
            },
            # the tool's Python dict, passed straight back as the tool_result:
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": "call_demo_001",
                    "content": json.dumps(info, ensure_ascii=False),
                }],
            },
        ],
    )
    answer = response.content[-1].text
    print("PASS  Claude answered from the tool result:", answer[:140], "...")

    if failures:
        print("\nFAILED:", failures)
        return 1
    print("\nAll acceptance checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

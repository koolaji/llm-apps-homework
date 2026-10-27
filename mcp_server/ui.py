"""Optional MCP chapter exercise: a small web UI over the finance MCP server.

The UI backend keeps ONE persistent MCP session to a spawned
``mcp_server/server.py`` subprocess (stdio transport), so every question
really goes through the MCP protocol. The tool loop is the same bounded
loop as ``client_test.py``, driven by the composite ``UI_PROMPT``.

Only Starlette + uvicorn are used — both ship as dependencies of the
``mcp`` package, so no extra install is needed.

Run:
    python mcp_server/ui.py                     # http://localhost:8000
Or:
    uvicorn mcp_server.ui:app --host 0.0.0.0 --port 8000
"""

import asyncio
import contextlib
import json
import os
import sys
import time
from contextlib import asynccontextmanager
from pathlib import Path

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from mcp_server.prompts import UI_PROMPT

ROOT = Path(__file__).resolve().parent.parent
MAX_TOOL_ROUNDS = 6

app_state = {}


# ------------------------------------------------------------------ tool loop
async def ask(question: str) -> dict:
    """Run the bounded tool-use loop for one user question."""
    session = app_state["session"]
    client = app_state["client"]

    tools_response = await session.list_tools()
    mcp_tools = [
        {
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        }
        for t in tools_response.tools
    ]

    messages = [{"role": "user", "content": question}]
    called = []
    answer = "پاسخی تولید نشد."

    for _ in range(MAX_TOOL_ROUNDS):
        response = await asyncio.to_thread(
            client.messages.create,
            model=os.environ.get("LLM_MODEL", "GLM-5.3-Flash"),
            max_tokens=4096,
            thinking={"type": "disabled"},
            system=UI_PROMPT,
            tools=mcp_tools,
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            answer = "".join(b.text for b in response.content if b.type == "text")
            break
        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            called.append(block.name)
            result = await session.call_tool(block.name, block.input)
            payload = "".join(c.text for c in result.content if hasattr(c, "text"))
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": payload,
            })
        messages.append({"role": "user", "content": results})

    return {"answer": answer, "tools_used": sorted(set(called))}


# --------------------------------------------------------------------- routes
async def index(request: Request) -> Response:
    return Response(UI_HTML, media_type="text/html; charset=utf-8")


async def api_ask(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JSONResponse({"error": "invalid JSON body"}, status_code=400)
    question = (body.get("question") or "").strip() if isinstance(body, dict) else ""
    if not question:
        return JSONResponse({"error": "question must not be empty"}, status_code=400)

    started = time.perf_counter()
    try:
        result = await ask(question)
    except Exception as exc:  # noqa: BLE001 - surfaced to the UI, not a crash
        return JSONResponse({"error": f"{type(exc).__name__}: {exc}"}, status_code=502)
    result["elapsed_seconds"] = round(time.perf_counter() - started, 1)
    return JSONResponse(result)


# ------------------------------------------------------------------ HTML page
UI_HTML = """<!DOCTYPE html>
<html lang="fa" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>تحلیلگر مالی هوشمند</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body {
    font-family: Vazirmatn, Tahoma, "Segoe UI", sans-serif;
    background: #f4f6f8; color: #1d2733; margin: 0;
    display: flex; justify-content: center; padding: 24px 12px;
  }
  .card {
    width: 100%; max-width: 760px; background: #fff; border-radius: 14px;
    box-shadow: 0 2px 14px rgba(20,40,80,.08); padding: 28px;
  }
  h1 { font-size: 1.45rem; margin: 0 0 4px; }
  .sub { color: #5b6b7c; font-size: .85rem; margin-bottom: 20px; }
  textarea {
    width: 100%; min-height: 84px; resize: vertical; border: 1px solid #cdd7e1;
    border-radius: 10px; padding: 12px; font: inherit; font-size: .95rem;
  }
  .row { display: flex; gap: 10px; margin-top: 12px; align-items: center; flex-wrap: wrap; }
  button {
    background: #1663d8; border: 0; color: #fff; font: inherit; font-size: .95rem;
    padding: 10px 26px; border-radius: 10px; cursor: pointer;
  }
  button:disabled { background: #9db8dd; cursor: wait; }
  .samples { font-size: .8rem; color: #5b6b7c; display: flex; gap: 8px; flex-wrap: wrap; }
  .samples button {
    background: #eef3fa; color: #1663d8; padding: 5px 12px; font-size: .8rem;
  }
  .status { min-height: 1.2em; color: #8a6d1a; font-size: .85rem; }
  .answer {
    margin-top: 18px; padding: 16px; border-radius: 10px; background: #f7f9fc;
    border: 1px solid #e3eaf2; white-space: pre-wrap; line-height: 1.9;
    font-size: .95rem; display: none;
  }
  .tools { margin-top: 10px; display: none; gap: 6px; flex-wrap: wrap; }
  .chip {
    background: #e8f0fe; color: #174ea6; border-radius: 999px;
    padding: 3px 12px; font-size: .75rem;
  }
  .error { color: #b3261e; }
  .meta { color: #8a97a5; font-size: .75rem; margin-top: 8px; }
</style>
</head>
<body>
<div class="card">
  <h1>📊 تحلیلگر مالی هوشمند</h1>
  <div class="sub">بورس، طلا و ارز — هر سوال از طریق پروتکل MCP به ابزارهای واقعی وصل می‌شود؛ مدل حدس نمی‌زند.</div>
  <textarea id="q" placeholder="سوال مالی‌ات را بنویس…"></textarea>
  <div class="row">
    <button id="ask">پرسیدن</button>
    <div class="samples">
      نمونه:
      <button class="s">قیمت طلای داخلی الان تقریباً چقدره؟</button>
      <button class="s">وضعیت سهم فولاد چطوره؟</button>
      <button class="s">روند بازار طلا الان چطوره؟</button>
    </div>
  </div>
  <div class="status" id="status"></div>
  <div class="answer" id="answer"></div>
  <div class="tools" id="tools"></div>
  <div class="meta" id="meta"></div>
</div>
<script>
const q = document.getElementById('q'), ask = document.getElementById('ask'),
      status = document.getElementById('status'), answer = document.getElementById('answer'),
      tools = document.getElementById('tools'), meta = document.getElementById('meta');
document.querySelectorAll('.s').forEach(b => b.onclick = () => { q.value = b.textContent; q.focus(); });
ask.onclick = async () => {
  const question = q.value.trim();
  if (!question) { status.textContent = 'سوال را وارد کن.'; return; }
  ask.disabled = true; answer.style.display = 'none'; tools.style.display = 'none';
  meta.textContent = ''; status.textContent = 'در حال بررسی سوال با ابزارها… (ممکن است تا یک دقیقه طول بکشد)';
  try {
    const r = await fetch('/api/ask', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({question})
    });
    const data = await r.json();
    if (!r.ok) { status.textContent = 'خطا: ' + (data.error || r.status); return; }
    status.textContent = '';
    answer.textContent = data.answer; answer.style.display = 'block';
    tools.innerHTML = '';
    (data.tools_used || []).forEach(t => {
      const c = document.createElement('span');
      c.className = 'chip'; c.textContent = t; tools.appendChild(c);
    });
    if (data.tools_used && data.tools_used.length) tools.style.display = 'flex';
    meta.textContent = 'ابزارهای فراخوانی‌شده بالا ← زمان پاسخ: ' + data.elapsed_seconds + ' ثانیه';
  } catch (e) {
    status.textContent = 'ارتباط با سرور برقرار نشد: ' + e;
  } finally {
    ask.disabled = false;
  }
};
</script>
</body>
</html>
"""

def build_app() -> Starlette:
    # `ask()` needs the session without a request handle; keep a module-level
    # reference filled by the lifespan.
    global app_state

    @asynccontextmanager
    async def _lifespan(_app: Starlette):
        # PYTHONPATH must carry the repo root: the server subprocess resolves
        # `mcp_server` imports relative to it, not to the launcher's sys.path
        # (script-dir is sys.path[0], not the cwd).
        env = dict(os.environ)
        env["PYTHONPATH"] = os.pathsep.join(
            p for p in (str(ROOT), env.get("PYTHONPATH", "")) if p
        )
        server_params = StdioServerParameters(
            command=sys.executable,
            args=["mcp_server/server.py"],
            env=env,
            cwd=str(ROOT),
        )
        async with contextlib.AsyncExitStack() as astack:
            read, write = await astack.enter_async_context(stdio_client(server_params))
            session = await astack.enter_async_context(ClientSession(read, write))
            await session.initialize()
            app_state["session"] = session
            app_state["client"] = Anthropic()
            tools = await session.list_tools()
            print(f"[ui] MCP session ready — tools: {[t.name for t in tools.tools]}",
                  flush=True)
            yield

    return Starlette(routes=[Route("/", index), Route("/api/ask", api_ask, methods=["POST"])],
                     lifespan=_lifespan)


app = build_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("UI_PORT", "8000")))

# LLM Apps Homework — Prompt Engineering · Tool Use · MCP

Solutions for an LLM-applications course, all containerized with Docker.

> **فارسی؟** راهنمای کامل فارسی: [`README.fa.md`](README.fa.md) ·
> گزارش تحویل: [`docs/REPORT.fa.md`](docs/REPORT.fa.md)

Three chapters, one project arc — from prompt engineering basics to a
multi-tool **MCP finance server** (Iranian stock market + gold + USD rates):

| Chapter | Folder | What it builds |
|---|---|---|
| Prompt Engineering | `exercises/ex1..ex5` | 5 LangChain mini-apps with structured output |
| Tool Use | `tool_use/` | `get_stock_info` TSETMC tool + JSON Schema + function-calling round trip |
| MCP | `mcp_server/` | MCP server with 3 tools + a prompt that *forces* multi-tool composition |

> The original exercise briefs (Persian, HTML) are in `docs/`.

## Quick start

```bash
cp .env.example .env        # then fill in your keys
docker compose build        # builds all images
docker compose run --rm ex1 # ...or any exercise below
```

### `.env` keys

| Key | Used by | Where to get it |
|---|---|---|
| `ANTHROPIC_BASE_URL` | everything | your Anthropic-compatible endpoint |
| `ANTHROPIC_API_KEY` | everything | your API token |
| `LLM_MODEL` | everything | model name (default `GLM-5.3-Flash`) |
| `NAVASAN_API_KEY` | MCP `get_usd_rate` | free via Telegram bot `@navasan_contact_bot` |

**Never commit `.env`.** A missing/invalid `NAVASAN_API_KEY` is also the
demo path for the MCP failure drill — the model must report the missing
data instead of guessing.

## Prompt-engineering exercises (chapter 1)

All five use `init_chat_model` + `ChatPromptTemplate` + Pydantic +
`with_structured_output`, with role/delimiter/output-format/no-guessing
principles applied.

```bash
docker compose --profile exercises run --rm ex1   # product review analysis
docker compose --profile exercises run --rm ex2   # resume extraction (fa/en/incomplete)
docker compose --profile exercises run --rm ex3   # support ticket classification
docker compose --profile exercises run --rm ex4   # few-shot technical content generator
docker compose --profile exercises run --rm ex5   # meeting analysis (see below)
```

Exercise 5 keeps three prompt versions to document iterative development:

```bash
docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v1
docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v2
docker compose run --rm ex5   # v3 (final)
```

`exercises/ex5_meeting/prompts.py` contains `CHANGELOG` — what changed in
each version and why.

## Tool-use chapter

```bash
# acceptance tests: valid call, invalid symbol -> ValueError,
# schema.json validity, and a real Claude API function-calling round trip
docker compose --profile tool-use run --rm tool-test

# technical analysis of a symbol — the prompt forces tool use
docker compose --profile tool-use run --rm tool-analysis
```

Files: `tool_use/stock_info.py` (the mandated signature/docstring),
`tool_use/schema.json`, `tool_use/test_function_calling.py`,
`tool_use/technical_analysis.py`.

## MCP chapter

```bash
# scripted client: checks tools/list, the composite gold-price question
# (both tools must fire), prints the answer
docker compose --profile mcp run --rm mcp-test

# failure drill: invalid NAVASAN key -> model must say which data is missing
docker compose --profile mcp run --rm mcp-test python mcp_server/client_test.py --break-usd

# bonus: market-trend question (extra multi-tool demo)
docker compose --profile mcp run --rm mcp-test python mcp_server/client_test.py --trend
```

### Use with Claude Desktop

```json
{
  "mcpServers": {
    "finance": {
      "command": "docker",
      "args": ["run", "-i", "--rm", "--env-file", "/absolute/path/to/.env", "llm-apps-homework-mcp-finance"]
    }
  }
}
```

The image name is `llm-apps-homework-mcp-finance` after `docker compose build`.

### The composite prompt (بخش ب)

*"قیمت طلای داخلی الان تقریباً چقدره؟"* cannot be answered with one tool:

```
per-gram 24k (Toman) = (ounce price USD ÷ 31.1) × USD→Toman rate
per-gram 18k         = 24k price × 0.75
```

The system prompt (`mcp_server/prompts.py`) walks the model through both
tool calls and the formula, and forbids guessing when a tool fails.

## Project layout

```
common/llm.py               shared init_chat_model factory (env-driven)
exercises/ex1..ex5          prompt-engineering mini-apps (+ samples per exercise)
tool_use/                   stock tool, schema.json, acceptance tests, analysis demo
mcp_server/
  server.py                 FastMCP server (stdio) registering the 3 tools
  tools/stock_info.py       re-uses tool_use/stock_info.py (no duplication)
  tools/gold_price.py       gold-api.com  (free, no key)
  tools/usd_rate.py         navasan.tech  (free key from Telegram bot)
  prompts.py                composite gold-price prompt + trend prompt
  client_test.py            scripted MCP client + acceptance checks
  mock_navasan.py           navasan lookalike for keyless testing
docker/requirements-base.txt shared dependencies (installed in every image)
docker-compose.yml           one service per deliverable, profiles per chapter
docs/                        original Persian exercise briefs + submission report
```

## Local (no Docker) development

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r docker/requirements-base.txt
export $(grep -v '^#' .env | xargs)   # load env vars
python -m exercises.ex1_review.analyze_review
python tool_use/test_function_calling.py
python mcp_server/client_test.py
```

## Notes

- Stock data comes from **TSETMC** via `pytse-client` (chosen over the raw
  unofficial API for stability — decision documented per the brief).
- The z.ai endpoint's model is a reasoning model that emits `thinking`
  blocks by default; `common/llm.py` disables thinking for predictable,
  fast structured output.
- Tool errors are returned in-band as `{"error": ...}` from the MCP tools
  so the model can *state* which data is unavailable (checklist item 4)
  instead of crashing the session.

## Testing without a Navasan key

`mcp_server/mock_navasan.py` fakes the navasan endpoint (valid key:
`test-key`, anything else gets 401 — exactly what the failure drill needs):

```bash
python mcp_server/mock_navasan.py &
export NAVASAN_LATEST_URL=http://127.0.0.1:8765/latest NAVASAN_API_KEY=test-key
python mcp_server/client_test.py            # normal mode
python mcp_server/client_test.py --break-usd  # failure drill
```

## Troubleshooting

- **`get_stock_info` fails with "TSETMC is unreachable"** — TSETMC
  geo-blocks non-Iranian/datacenter IPs. Run from an Iranian network, or
  use the offline suite (`python tool_use/offline_test.py`) which mocks
  the ticker and verifies everything else, including the Claude
  function-calling round trip.
- **Docker builds time out on pip** — on constrained networks build with
  `docker build --network=host -f <dockerfile> .` (the compose builds use
  the default bridge network; this flag is only for manual builds).
- **`mcp` 2.x / `pytse-client` 1+** — this repo pins `mcp<2` (the 2.x SDK
  renames `FastMCP` → `MCPServer`) and `pandas<3` (pytse-client targets
  the pandas 2 API). Both pins live in `docker/requirements-base.txt`.

## Tested with

Python 3.13 (venv) and `python:3.12-slim` (Docker): langchain 1.4.7,
langchain-anthropic 1.7.6, pydantic 2.14.1, mcp 1.30.0, pytse-client
0.7.0–0.19.1, anthropic 1.17.0.

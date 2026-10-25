"""Offline verification for the tool-use chapter — runs anywhere.

TSETMC geo-blocks datacenter/non-Iranian IPs, so these tests mock the
pytse-client ``Ticker`` object and verify everything that does not need a
live TSETMC connection:

  1. get_stock_info returns the exact mandated dict shape and correct math.
  2. An invalid symbol raises ValueError (no network needed).
  3. TSETMC connectivity failures surface as a clear RuntimeError.
  4. schema.json is valid and matches the tool contract.
  5. The tool dict passes through a real Claude API function-calling round trip.

Run:  python tool_use/offline_test.py
"""

import json
import os
import sys
from unittest.mock import MagicMock, patch

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tool_use.stock_info import get_stock_info, load_schema

FAILED = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except AssertionError as exc:
        FAILED.append(name)
        print(f"FAIL  {name}: {exc}")
    except Exception as exc:  # noqa: BLE001
        FAILED.append(name)
        print(f"ERROR {name}: {type(exc).__name__}: {exc}")


class _FakeTicker:
    """Stands in for pytse_client.Ticker (no network)."""

    def __init__(self, symbol: str):
        self.title = "فولاد مبارکه اصفهان"
        self.history = pd.DataFrame({
            "close": [8120.0, 8250.0],
            "volume": [51_000_000, 63_500_000],
        })
        self.last_price = 8310.0


def test_valid_symbol_shape():
    with patch("tool_use.stock_info.Ticker", _FakeTicker):
        info = get_stock_info("فولاد")
    required = {
        "symbol", "name", "last_price", "price_change_percent",
        "volume", "market_cap", "last_update",
    }
    assert required.issubset(info), f"missing: {required - set(info)}"
    assert info["last_price"] == 8310.0
    # percent change vs previous day: (8250 - 8120) / 8120 * 100 = 1.6
    assert info["price_change_percent"] == 1.6
    assert info["volume"] == 63_500_000
    assert info["market_cap"] is None
    print("      ->", json.dumps(info, ensure_ascii=False)[:110], "...")


def test_invalid_symbol():
    try:
        get_stock_info("XYZ123")
        raise AssertionError("no ValueError raised")
    except ValueError as exc:
        assert "XYZ123" in str(exc)


def test_unreachable_tsetmc():
    class _Boom:
        def __init__(self, symbol):
            raise OSError("connection reset")

    with patch("tool_use.stock_info.Ticker", _Boom):
        try:
            get_stock_info("فولاد")
            raise AssertionError("no RuntimeError raised")
        except RuntimeError as exc:
            assert "unreachable" in str(exc)


def test_schema():
    schema = load_schema()
    assert schema["name"] == "get_stock_info"
    assert schema["input_schema"]["required"] == ["symbol"]
    assert schema["input_schema"]["properties"]["symbol"]["type"] == "string"


def test_claude_round_trip():
    """The mocked dict goes through a real Claude API function-calling message."""
    from anthropic import Anthropic

    with patch("tool_use.stock_info.Ticker", _FakeTicker):
        info = get_stock_info("فولاد")

    client = Anthropic()
    response = client.messages.create(
        model=os.environ.get("LLM_MODEL", "GLM-5.3-Flash"),
        max_tokens=1024,
        thinking={"type": "disabled"},
        tools=[load_schema()],
        messages=[
            {"role": "user", "content": "قیمت لحظه‌ای سهم فولاد چنده؟"},
            {
                "role": "assistant",
                "content": [{
                    "type": "tool_use",
                    "id": "call_offline_001",
                    "name": "get_stock_info",
                    "input": {"symbol": "فولاد"},
                }],
            },
            {
                "role": "user",
                "content": [{
                    "type": "tool_result",
                    "tool_use_id": "call_offline_001",
                    "content": json.dumps(info, ensure_ascii=False),
                }],
            },
        ],
    )
    answer = response.content[-1].text
    assert "۸" in answer or "8" in answer, f"answer lacks the price: {answer[:80]}"
    print(f"      -> Claude answered from the tool result: {answer[:100]}")


if __name__ == "__main__":
    print("Tool-use chapter — offline verification\n" + "=" * 50)
    check("valid symbol returns the mandated dict", test_valid_symbol_shape)
    check("invalid symbol raises ValueError", test_invalid_symbol)
    check("TSETMC outage raises clear RuntimeError", test_unreachable_tsetmc)
    check("schema.json is a valid tool schema", test_schema)
    if os.environ.get("ANTHROPIC_API_KEY"):
        check("Claude API function-calling round trip", test_claude_round_trip)
    else:
        print("SKIP  Claude round trip (ANTHROPIC_API_KEY not set)")

    print("\n" + ("ALL PASSED" if not FAILED else f"FAILED: {FAILED}"))
    sys.exit(1 if FAILED else 0)

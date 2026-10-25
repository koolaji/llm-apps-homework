"""Tool-use chapter — get_stock_info: live data for one TSETMC symbol.

Returns a dict shaped exactly as mandated by the exercise docstring so an
LLM can consume it in function calling without ambiguity.

Data source: pytse-client (chosen over the raw unofficial TSETMC API —
simpler, maintained, covers live and historical data).

Note: TSETMC geo-blocks non-Iranian/datacenter IPs; on such networks the
function raises RuntimeError with a clear message instead of a raw traceback.
"""

import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

from pytse_client import Ticker, symbols_data

TEHRAN = ZoneInfo("Asia/Tehran")


def get_stock_info(symbol: str) -> dict:
    """
    اطلاعات لحظه‌ای یک نماد بورسی ایران را از TSETMC بازمی‌گرداند.

    Args:
        symbol (str): نماد سهم به فارسی یا انگلیسی، دقیقاً همانطور که در
            TSETMC ثبت شده است. مثال: "فولاد"

    Returns:
        dict: دیکشنری با کلیدهای زیر:
            - symbol (str): نماد سهم
            - name (str): نام کامل شرکت
            - last_price (float): آخرین قیمت معامله‌شده (تومان)
            - price_change_percent (float): درصد تغییر نسبت به روز قبل
            - volume (int): حجم معاملات
            - market_cap (float | None): ارزش بازار در صورت موجود بودن
            - last_update (str): زمان آخرین به‌روزرسانی به فرمت ISO 8601

    Raises:
        ValueError: اگر نماد وارد‌شده در TSETMC یافت نشود.
        RuntimeError: اگر TSETMC در دسترس نباشد (مثلاً محدودیت جغرافیایی).
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("symbol must be a non-empty string, e.g. 'فولاد'")
    symbol = symbol.strip()

    # --- input validation: unknown symbol -> ValueError (never a crash) ---
    try:
        index = symbols_data.get_ticker_index(symbol)
    except (KeyError, ValueError) as exc:
        raise ValueError(
            f"Symbol '{symbol}' was not found in TSETMC. "
            "Use the exact Persian/English ticker registered in TSETMC."
        ) from exc
    if index is None:
        raise ValueError(
            f"Symbol '{symbol}' was not found in TSETMC. "
            "Use the exact Persian/English ticker registered in TSETMC."
        )

    # --- fetch (network errors -> clear RuntimeError, not a raw traceback) ---
    try:
        ticker = Ticker(symbol)
    except Exception as exc:  # noqa: BLE001 - mapped, not swallowed
        raise RuntimeError(
            f"TSETMC is unreachable for symbol '{symbol}': {exc}. "
            "If you are outside Iran, TSETMC may be blocking your network."
        ) from exc

    history = ticker.history
    last_close = float(history["close"].iloc[-1])
    if len(history) >= 2:
        prev_close = float(history["close"].iloc[-2])
        change_percent = round((last_close - prev_close) / prev_close * 100, 2)
    else:
        change_percent = 0.0
    volume = int(history["volume"].iloc[-1])

    # During trading hours the realtime price is fresher than history.
    try:
        last_price = float(ticker.last_price or last_close)
    except (TypeError, ValueError):
        last_price = last_close

    return {
        "symbol": symbol,
        "name": ticker.title,
        "last_price": last_price,
        "price_change_percent": change_percent,
        "volume": volume,
        # pytse-client does not expose market cap; documented as optional in
        # the brief's contract, so None instead of a guessed number.
        "market_cap": None,
        "last_update": datetime.now(TEHRAN).isoformat(),
    }


# The JSON Schema (schema.json) is the same object sent to the LLM API as
# the tool definition — kept in a separate file per the exercise brief.
SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "schema.json")


def load_schema() -> dict:
    """Load the tool's JSON Schema from the adjacent schema.json file."""
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Fetch live TSETMC info for a symbol")
    parser.add_argument("symbol", nargs="?", default="فولاد")
    args = parser.parse_args()
    print(json.dumps(get_stock_info(args.symbol), ensure_ascii=False, indent=2))

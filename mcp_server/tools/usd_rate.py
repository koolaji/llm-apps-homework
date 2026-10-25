"""MCP tool: USD -> Toman rate from navasan.tech.

Needs a free API key (Telegram bot @navasan_contact_bot) in NAVASAN_API_KEY.
The endpoint URL can be overridden with NAVASAN_LATEST_URL (useful for tests).
"""

import os

import requests

DEFAULT_NAVASAN_LATEST_URL = "https://api.navasan.tech/latest/"


def get_usd_rate() -> dict:
    """
    آخرین نرخ دلار آمریکا به تومان را از navasan.tech برمی‌گرداند.

    Returns:
        dict: {"usd_sell_toman": float, "last_update": str}
              یا {"error": str} اگر کلید نامعتبر باشد یا سرویس در دسترس
              نباشد — تا مدل به‌جای حدس زدن، نبود داده را صریح اعلام کند.
    """
    url = os.environ.get("NAVASAN_LATEST_URL", DEFAULT_NAVASAN_LATEST_URL)
    api_key = os.environ.get("NAVASAN_API_KEY", "")
    if not api_key:
        return {"error": "NAVASAN_API_KEY is not configured; USD rate unavailable."}
    try:
        response = requests.get(url, params={"api_key": api_key}, timeout=10)
        response.raise_for_status()
        data = response.json()
        usd_info = data["usd"]
        return {
            "usd_sell_toman": float(usd_info["value"]),
            "last_update": str(usd_info.get("date", "")),
        }
    except (requests.RequestException, KeyError, ValueError, TypeError) as exc:
        return {"error": f"navasan.tech unavailable: {exc}"}

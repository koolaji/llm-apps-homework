"""MCP tool: world gold price (USD per ounce) from gold-api.com.

Free API, no key required. Follows the chapter-1 code rules: type hints,
Google-style docstring, JSON Schema provided by the MCP SDK from the
function signature.
"""

import requests

GOLD_API_URL = "https://api.gold-api.com/price/XAU"


def get_gold_price() -> dict:
    """
    قیمت لحظه‌ای جهانی طلا (هر انس، به دلار) را از gold-api.com برمی‌گرداند.

    Returns:
        dict: {"symbol": "XAU", "price_usd_per_ounce": float, "name": str}
              یا {"error": str} اگر سرویس در دسترس نباشد — تا مدل به‌جای
              حدس زدن، نبود داده را صریح اعلام کند.
    """
    try:
        response = requests.get(GOLD_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        return {"error": f"gold-api.com unavailable: {exc}"}
    return {
        "symbol": data["symbol"],
        "price_usd_per_ounce": data["price"],
        "name": data.get("name", "Gold"),
    }

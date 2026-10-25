"""MCP finance server — three real tools over stdio.

Run directly (stdio transport), or via Docker:
    docker run -i --rm --env-file .env <image>

tools/list is handled by the MCP SDK — no manual listing code needed.
"""

from mcp.server.fastmcp import FastMCP

# Implementations imported under aliases: the @mcp.tool() wrappers below use
# the public tool names, which would otherwise shadow these imports and make
# the wrappers call themselves (RecursionError).
from mcp_server.tools.gold_price import get_gold_price as _get_gold_price_impl
from mcp_server.tools.stock_info import get_stock_info as _get_stock_info_impl
from mcp_server.tools.usd_rate import get_usd_rate as _get_usd_rate_impl

mcp = FastMCP("finance")


@mcp.tool()
def get_stock_info(symbol: str) -> dict:
    """اطلاعات لحظه‌ای یک نماد بورسی ایران را از TSETMC برمی‌گرداند: آخرین قیمت، درصد تغییر روز، حجم معاملات و ارزش بازار."""
    return _get_stock_info_impl(symbol)


@mcp.tool()
def get_gold_price() -> dict:
    """قیمت لحظه‌ای جهانی طلا (هر انس، به دلار) را از gold-api.com برمی‌گرداند."""
    return _get_gold_price_impl()


@mcp.tool()
def get_usd_rate() -> dict:
    """آخرین نرخ دلار آمریکا به تومان را از navasan.tech برمی‌گرداند."""
    return _get_usd_rate_impl()


if __name__ == "__main__":
    mcp.run(transport="stdio")

"""MCP tool: live TSETMC stock info.

Re-exports the chapter-1 tool unchanged (single source of truth).
"""

from tool_use.stock_info import get_stock_info  # noqa: F401 (re-export)

__all__ = ["get_stock_info"]

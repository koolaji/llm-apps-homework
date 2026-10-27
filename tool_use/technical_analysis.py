"""Technical analysis of a TSETMC symbol — forces the LLM to use the tool.

Usage:
    python technical_analysis.py فولاد
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from anthropic import Anthropic

from tool_use.news_search import load_news_schema, search_stock_news
from tool_use.stock_info import get_stock_info, load_schema

# Tool registry: name -> (implementation, schema)
TOOLS = {
    "get_stock_info": (get_stock_info, load_schema()),
    "search_stock_news": (search_stock_news, load_news_schema()),
}

SYSTEM_PROMPT = """تو یک تحلیلگر تکنیکال بازار بورس ایران هستی.

برای تحلیل هر نماد، قبل از هرگونه نظر دادن **حتماً** ابزار get_stock_info را
فراخوانی کن و تحلیل را فقط بر اساس داده‌ای که خود ابزار برمی‌گرداند ارائه بده.
در صورت نیاز می‌توانی برای زمینه‌ی بیشتر از ابزار search_stock_news هم
(اخبار جدید نماد) استفاده کنی، اما تحلیل عددی فقط از داده‌های get_stock_info.
اگر ابزار خطا داد یا نماد پیدا نشد، تحلیل نساز؛ صریحاً بگو داده در دسترس نیست.

ساختار پاسخ:
۱. داده‌های خام (آخرین قیمت، درصد تغییر روز، حجم، ارزش بازار)
۲. تحلیل کوتاه تکنیکال بر اساس همین اعداد (روند، فشار خرید/فروش حاصل از حجم)
۳. یک هشدار ریسک دو خطی

پاسخ را فارسی بده."""


def analyze(symbol: str) -> str:
    client = Anthropic()
    messages = [{"role": "user", "content": f"لطفاً وضعیت سهم «{symbol}» را تحلیل کن."}]

    for _ in range(6):  # bounded agentic loop (two tools may need more turns)
        response = client.messages.create(
            model=os.environ.get("LLM_MODEL", "GLM-5.3-Flash"),
            max_tokens=4096,
            thinking={"type": "disabled"},
            system=SYSTEM_PROMPT,
            tools=[schema for _, schema in TOOLS.values()],
            messages=messages,
        )
        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        results = []
        for block in response.content:
            if block.type == "tool_use":
                try:
                    impl = TOOLS[block.name][0]
                except KeyError:
                    output = {"error": f"unknown tool: {block.name}"}
                else:
                    try:
                        output = impl(**block.input)
                    except Exception as exc:  # noqa: BLE001 - feed error back
                        output = {"error": str(exc)}
                results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(output, ensure_ascii=False),
                })
        messages.append({"role": "user", "content": results})

    return "Tool loop exceeded the iteration limit."


if __name__ == "__main__":
    symbol = sys.argv[1] if len(sys.argv) > 1 else "فولاد"
    print(analyze(symbol))

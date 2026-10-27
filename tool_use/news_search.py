"""Optional tool-use chapter exercise: web news search for a TSE symbol.

Uses Bing News RSS (no API key, works without third-party libraries —
stdlib ``urllib`` + ``xml.etree`` only). Results are rendered as returned
by Bing for personal, non-commercial use (Bing RSS terms).

Usage:
    python news_search.py فولاد
"""

import email.utils
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

BING_NEWS_RSS_URL = "https://www.bing.com/news/search"
SCHEMA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "news_search.schema.json")
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120 Safari/537.36"
)


def load_news_schema() -> dict:
    """Load the tool's JSON Schema from the adjacent news_search.schema.json."""
    with open(SCHEMA_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def search_stock_news(symbol: str, count: int = 5) -> dict:
    """Search the web for recent news about a stock symbol or phrase.

    Args:
        symbol: Symbol or company name to search for (e.g. "فولاد").
        count: Maximum number of news items to return (1 to 10).

    Returns:
        dict with keys:
            - "symbol" (str): the query that was searched.
            - "news" (list[dict]): up to ``count`` items, newest first, each
              with "title", "link", "source", "published" (ISO-8601 UTC) and
              "summary".

    Raises:
        ValueError: if ``symbol`` is empty or ``count`` is outside 1..10.
        RuntimeError: if the news provider is unreachable or its response
            cannot be parsed (never crash on provider problems — errors are
            mapped to a clear exception instead).
    """
    if not symbol or not symbol.strip():
        raise ValueError("symbol must be a non-empty string.")
    if not 1 <= count <= 10:
        raise ValueError("count must be between 1 and 10.")

    url = f"{BING_NEWS_RSS_URL}?q={urllib.parse.quote(symbol)}&format=RSS"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = response.read()
        root = ET.fromstring(payload)
    except (urllib.error.URLError, TimeoutError, OSError, ET.ParseError) as exc:
        raise RuntimeError(
            f"The news provider is unreachable or returned an invalid "
            f"response: {exc}"
        ) from exc

    items = []
    for item in root.findall(".//item"):
        published_raw = (item.findtext("pubDate") or "").strip()
        published = ""
        if published_raw:
            try:
                published = email.utils.parsedate_to_datetime(
                    published_raw
                ).isoformat()
            except (TypeError, ValueError):
                published = published_raw  # keep the raw string if unparsable
        items.append({
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "source": (item.findtext("Source") or "").strip(),
            "published": published,
            "summary": (item.findtext("description") or "").strip(),
        })

    items.sort(key=lambda entry: entry["published"], reverse=True)
    return {"symbol": symbol, "news": items[:count]}


if __name__ == "__main__":
    import json

    query = sys.argv[1] if len(sys.argv) > 1 else "فولاد"
    print(json.dumps(search_stock_news(query), ensure_ascii=False, indent=2))

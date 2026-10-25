"""Tiny mock of the navasan.tech /latest endpoint — for testing without a key.

Serves {"usd": {"value": ..., "date": ...}} like the real API and accepts a
fixed key, so the full MCP gold-price flow can be exercised offline:

    python mcp_server/mock_navasan.py &            # listens on 127.0.0.1:8765
    NAVASAN_LATEST_URL=http://127.0.0.1:8765/latest \
    NAVASAN_API_KEY=test-key \
    python mcp_server/client_test.py

Any other key gets HTTP 401 — which is exactly what the --break-usd failure
drill needs.
"""

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

VALID_KEY = "test-key"
USD_TOMAN = 1_118_000  # plausible placeholder rate for tests


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 (http.server API)
        query = parse_qs(urlparse(self.path).query)
        if query.get("api_key", [""])[0] != VALID_KEY:
            self.send_response(401)
            self.end_headers()
            self.wfile.write(b'{"error": "invalid api key"}')
            return
        body = json.dumps({
            "usd": {"value": str(USD_TOMAN), "date": "1404/08/03"}
        }).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quiet
        pass


if __name__ == "__main__":
    HTTPServer(("127.0.0.1", 8765), Handler).serve_forever()

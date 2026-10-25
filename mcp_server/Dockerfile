# MCP chapter — multi-tool finance MCP server (stdio transport)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY tool_use/stock_info.py /app/tool_use/stock_info.py
COPY tool_use/schema.json /app/tool_use/schema.json
COPY mcp_server/ /app/mcp_server/

# stdio MCP server: speaks MCP on stdin/stdout.
# Claude Desktop launches it with:
#   docker run -i --rm --env-file .env <image>
CMD ["python", "mcp_server/server.py"]

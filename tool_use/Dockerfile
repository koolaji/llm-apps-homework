# Tool-use chapter — stock info tool + function-calling demos
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY tool_use/ /app/tool_use/

# Default runs the tool-use test suite (acceptance checklist).
# For the technical-analysis demo:
#   docker compose run --rm tool-test python tool_use/technical_analysis.py فولاد
CMD ["python", "tool_use/test_function_calling.py"]

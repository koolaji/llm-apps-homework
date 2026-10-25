# Exercise 4 — technical content generation (few-shot prompting)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY exercises/ex4_content/ /app/exercises/ex4_content/

CMD ["python", "-m", "exercises.ex4_content.generate_content"]

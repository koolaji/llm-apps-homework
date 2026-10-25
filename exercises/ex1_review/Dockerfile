# Exercise 1 — product review analysis
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY exercises/ex1_review/ /app/exercises/ex1_review/

CMD ["python", "-m", "exercises.ex1_review.analyze_review"]

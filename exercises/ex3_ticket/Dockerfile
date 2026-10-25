# Exercise 3 — support ticket classification
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY exercises/ex3_ticket/ /app/exercises/ex3_ticket/

CMD ["python", "-m", "exercises.ex3_ticket.ticket_classifier"]

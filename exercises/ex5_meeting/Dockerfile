# Exercise 5 — meeting analysis (iterative prompts, see prompts.py)
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY exercises/ex5_meeting/ /app/exercises/ex5_meeting/

# Default: final prompt version. Override for v1/v2:
#   docker compose run --rm ex5 python -m exercises.ex5_meeting.analyze_meeting --version v1
CMD ["python", "-m", "exercises.ex5_meeting.analyze_meeting"]

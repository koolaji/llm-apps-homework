# Exercise 2 — resume information extraction
FROM python:3.12-slim

WORKDIR /app
ENV PYTHONPATH=/app PYTHONDONTWRITEBYTECODE=1 \
    PIP_DEFAULT_TIMEOUT=180 PIP_RETRIES=8

COPY docker/requirements-base.txt /app/docker/requirements-base.txt
RUN pip install --no-cache-dir -r /app/docker/requirements-base.txt

COPY common/ /app/common/
COPY exercises/ex2_resume/ /app/exercises/ex2_resume/

CMD ["python", "-m", "exercises.ex2_resume.extract_resume_info"]

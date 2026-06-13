FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TOKEN_TRACKER_DATABASE_PATH=/data/harness.db \
    TOKEN_TRACKER_GUARDRAILS_PATH=/app/guardrails.yaml

WORKDIR /app
RUN mkdir -p /data

COPY pyproject.toml ./
COPY guardrails.yaml ./guardrails.yaml
COPY src ./src

RUN pip install --no-cache-dir .

EXPOSE 8000
CMD htb serve --host 0.0.0.0 --port ${PORT:-8000} --proxy-headers

# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Runtime stage
FROM python:3.11-slim

ENV FLASK_APP=wsgi.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PORT=8080

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev \
    libzbar0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/gunicorn /usr/local/bin/gunicorn

COPY backend /app/backend
COPY frontend /app/frontend

RUN mkdir -p /app/backend/static/uploads && chmod 755 /app/backend/static/uploads

RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

WORKDIR /app/backend

ENTRYPOINT ["/bin/bash", "/app/backend/entrypoint.sh"]

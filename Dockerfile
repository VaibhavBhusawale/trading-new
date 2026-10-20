FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY alembic ./alembic
COPY alembic.ini ./
COPY docker/entrypoint.sh /entrypoint.sh
COPY docker/dashboard-entrypoint.sh /dashboard-entrypoint.sh

RUN pip install --no-cache-dir ".[dashboard]" \
    && chmod +x /entrypoint.sh /dashboard-entrypoint.sh

ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV APP_ENV=production

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]

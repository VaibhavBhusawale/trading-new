#!/bin/sh
set -e

echo "Running database migrations..."
alembic upgrade head

PORT="${PORT:-${API_PORT:-8000}}"
echo "Starting Tradex API on 0.0.0.0:${PORT}..."
exec uvicorn tradex.main:app --host 0.0.0.0 --port "${PORT}"

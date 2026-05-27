#!/bin/bash
set -e

echo "Starting FitAI..."
cd /app

echo "Waiting for PostgreSQL..."
for i in $(seq 1 30); do
  if python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL'.replace('postgresql://','postgresql://').split('/')[-1] or '')
conn.close()
" 2>/dev/null; then
    echo "PostgreSQL is ready!"
    break
  fi
  echo "  Attempt $i/30..."
  sleep 2
done

echo "Running migrations..."
alembic upgrade head 2>/dev/null || echo "Migration note: $!"

echo "Starting nginx..."
nginx -g 'daemon on;'

echo "Starting backend..."
exec uvicorn backend.main:app --host 127.0.0.1 --port 8000 --workers 2

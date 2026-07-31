#!/bin/bash
set -euo pipefail

echo "=== FitAI Production Deployment ==="

# Check env file
if [ ! -f .env.production ]; then
    echo "ERROR: .env.production not found. Copy .env.example to .env.production and configure."
    exit 1
fi

# Load env
export $(grep -v '^#' .env.production | xargs)

# Pull latest
echo "[1/6] Pulling latest images..."
docker compose -f docker-compose.prod.yml pull 2>/dev/null || true

# Build
echo "[2/6] Building..."
docker compose -f docker-compose.prod.yml build --no-cache backend celery-worker celery-beat

# Run migrations
echo "[3/6] Running database migrations..."
docker compose -f docker-compose.prod.yml run --rm backend \
    alembic upgrade head

# Collect static files (if needed)
echo "[4/6] Rolling restart..."
docker compose -f docker-compose.prod.yml up -d --force-recreate backend celery-worker celery-beat

# Wait for health
echo "[5/6] Waiting for health check..."
sleep 10
for i in $(seq 1 12); do
    if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        echo "  ✓ Backend is healthy"
        break
    fi
    if [ $i -eq 12 ]; then
        echo "  ✗ Backend failed health check"
        docker compose -f docker-compose.prod.yml logs --tail=50 backend
        exit 1
    fi
    sleep 5
done

# Run ETL backfill if first deploy
echo "[6/6] Running ETL backfill (if needed)..."
docker compose -f docker-compose.prod.yml run --rm backend \
    python -c "
import asyncio
from backend.database import async_engine, AsyncSessionLocal
from backend.services.etl_service import ETLService
from datetime import date, timedelta
async def main():
    async with AsyncSessionLocal() as db:
        await ETLService.backfill_stats(db, org_id=1, start_date=date.today()-timedelta(days=30), end_date=date.today())
asyncio.run(main())
" 2>/dev/null || echo "  (ETL backfill skipped - no data yet)"

echo "=== Deployment Complete ==="

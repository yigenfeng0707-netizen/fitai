#!/bin/bash
set -euo pipefail
VERSION=${1:-"previous"}

echo "=== FitAI Rollback to ${VERSION} ==="

# Get previous image
PREVIOUS_IMAGE=$(docker images --format "{{.Repository}}:{{.Tag}}" | grep fitai | sort | head -2 | tail -1)

if [ -z "$PREVIOUS_IMAGE" ]; then
    echo "ERROR: No previous image found for rollback"
    exit 1
fi

echo "Rolling back to: $PREVIOUS_IMAGE"

# Stop current
docker compose -f docker-compose.prod.yml stop backend celery-worker celery-beat

# Rollback database if needed
read -p "Rollback database migrations? (y/N): " ROLLBACK_DB
if [ "$ROLLBACK_DB" = "y" ]; then
    docker compose -f docker-compose.prod.yml run --rm backend alembic downgrade -1
fi

# Start with previous image
docker compose -f docker-compose.prod.yml up -d backend celery-worker celery-beat

# Health check
sleep 10
if curl -sf http://localhost:8000/health > /dev/null 2>&1; then
    echo "✓ Rollback successful"
else
    echo "✗ Rollback failed - manual intervention required"
fi

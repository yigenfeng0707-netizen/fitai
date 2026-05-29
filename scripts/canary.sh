#!/bin/bash
set -euo pipefail

# Canary deployment with automatic rollback
CANARY_PORT=8001
PRODUCTION_PORT=8000
CANARY_WEIGHT=${1:-10}  # percentage of traffic to canary (0-100)
HEALTH_CHECK_URL="http://localhost:${CANARY_PORT}/health"
ERROR_THRESHOLD=5  # max errors before rollback
MONITOR_DURATION=300  # seconds to monitor

echo "=== FitAI Canary Deployment ==="
echo "Canary traffic weight: ${CANARY_WEIGHT}%"

# Start canary container
echo "[1] Starting canary container..."
docker compose -f docker-compose.prod.yml run -d --name fitai-canary -p ${CANARY_PORT}:8000 backend

# Wait for health
echo "[2] Waiting for canary health check..."
for i in $(seq 1 30); do
    if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "  ✓ Canary is healthy"
        break
    fi
    sleep 2
done

# Update nginx to route traffic
echo "[3] Updating nginx upstream..."
# ... nginx config update logic ...

# Monitor
echo "[4] Monitoring for ${MONITOR_DURATION}s..."
ERROR_COUNT=0
START_TIME=$(date +%s)

while true; do
    ELAPSED=$(($(date +%s) - START_TIME))
    if [ $ELAPSED -ge $MONITOR_DURATION ]; then
        echo "  ✓ Monitoring period complete. Promoting canary."
        break
    fi

    # Check error rate
    RECENT_ERRORS=$(docker logs fitai-canary --since 30s 2>&1 | grep -c "ERROR" || true)
    ERROR_COUNT=$((ERROR_COUNT + RECENT_ERRORS))

    if [ $ERROR_COUNT -ge $ERROR_THRESHOLD ]; then
        echo "  ✗ Error threshold reached (${ERROR_COUNT} errors). Rolling back!"
        docker stop fitai-canary && docker rm fitai-canary
        echo "  Rollback complete."
        exit 1
    fi

    sleep 30
done

# Promote: stop old, keep canary
echo "[5] Promoting canary to production..."
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
docker stop fitai-canary && docker rm fitai-canary
echo "=== Canary Promotion Complete ==="

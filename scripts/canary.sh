#!/bin/bash
set -euo pipefail

# Canary deployment with automatic rollback
CANARY_PORT=8001
PRODUCTION_PORT=8000
CANARY_WEIGHT=${1:-10}  # percentage of traffic to canary (0-100)
HEALTH_CHECK_URL="http://localhost:${CANARY_PORT}/health"
ERROR_THRESHOLD=5  # max errors before rollback
MONITOR_DURATION=300  # seconds to monitor
NGINX_CONF="/etc/nginx/nginx.conf"
NGINX_CONF_BACKUP="/etc/nginx/nginx.conf.bak"

echo "=== FitAI Canary Deployment ==="
echo "Canary traffic weight: ${CANARY_WEIGHT}%"

# Backup current nginx config
echo "[0] Backing up nginx config..."
docker exec fitai-nginx cp /etc/nginx/nginx.conf /etc/nginx/nginx.conf.bak 2>/dev/null || true

# Start canary container
echo "[1] Starting canary container..."
docker compose -f docker-compose.prod.yml run -d --name fitai-canary -p ${CANARY_PORT}:8000 backend

# Wait for health
echo "[2] Waiting for canary health check..."
CANARY_HEALTHY=false
for i in $(seq 1 30); do
    if curl -sf "$HEALTH_CHECK_URL" > /dev/null 2>&1; then
        echo "  ✓ Canary is healthy"
        CANARY_HEALTHY=true
        break
    fi
    sleep 2
done

if [ "$CANARY_HEALTHY" = false ]; then
    echo "  ✗ Canary failed health check. Cleaning up..."
    docker stop fitai-canary 2>/dev/null && docker rm fitai-canary 2>/dev/null || true
    exit 1
fi

# Update nginx to route weighted traffic
echo "[3] Updating nginx upstream (weight: ${CANARY_WEIGHT}%)..."
PRODUCTION_WEIGHT=$((100 - CANARY_WEIGHT))

# Generate weighted upstream config
docker exec fitai-nginx sh -c "cat > /etc/nginx/nginx.conf << 'NGINX_EOF'
upstream backend {
    server backend:8000 weight=${PRODUCTION_WEIGHT};
    server backend:${CANARY_PORT} weight=${CANARY_WEIGHT};
}

server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.fitai.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 20M;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://backend;
        access_log off;
    }

    location /docs {
        deny all;
    }
}
NGINX_EOF"

# Reload nginx
docker exec fitai-nginx nginx -s reload 2>/dev/null && echo "  ✓ Nginx reloaded with weighted upstream" || echo "  ⚠ Nginx reload failed"

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

        # Restore original nginx config
        echo "  Restoring nginx config..."
        docker exec fitai-nginx cp /etc/nginx/nginx.conf.bak /etc/nginx/nginx.conf 2>/dev/null || true
        docker exec fitai-nginx nginx -s reload 2>/dev/null || true

        # Stop canary
        docker stop fitai-canary && docker rm fitai-canary
        echo "  Rollback complete."
        exit 1
    fi

    sleep 30
done

# Promote: update nginx to production-only, stop canary
echo "[5] Promoting canary to production..."
docker exec fitai-nginx sh -c "cat > /etc/nginx/nginx.conf << 'NGINX_EOF'
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name _;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.fitai.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 20M;

    location / {
        proxy_pass http://backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 30s;
        proxy_read_timeout 60s;
    }

    location /health {
        proxy_pass http://backend;
        access_log off;
    }

    location /docs {
        deny all;
    }
}
NGINX_EOF"
docker exec fitai-nginx nginx -s reload 2>/dev/null || true

# Recreate backend with new image
docker compose -f docker-compose.prod.yml up -d --force-recreate backend
docker stop fitai-canary && docker rm fitai-canary
echo "=== Canary Promotion Complete ==="

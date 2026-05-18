#!/bin/bash
set -e

echo "=========================================="
echo "FitAI Automated Deployment Script"
echo "=========================================="

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Docker not found. Please install Docker first."
    exit 1
fi

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env from template..."
    cp .env.production .env
    echo "Please edit .env and set your secure passwords!"
    exit 1
fi

# Pull latest code
if [ -d .git ]; then
    echo "Pulling latest code..."
    git pull origin master
fi

# Build and start services
echo "Building and starting services..."
docker-compose -f docker-compose.production.yml up -d --build

echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="

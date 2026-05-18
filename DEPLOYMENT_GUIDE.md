# FitAI - Automated Deployment Guide

## Quick Start

### Option 1: Zeabur (Recommended)

1. Visit https://zeabur.com
2. Sign in with GitHub
3. Import repository: `yigenfeng0707-netizen/fitai`
4. Add PostgreSQL database
5. Configure environment variables
6. Deploy!

### Option 2: Docker Compose

```bash
git clone https://github.com/yigenfeng0707-netizen/fitai.git
cd fitai
cp .env.production .env
nano .env
docker-compose -f docker-compose.production.yml up -d
```

## CI/CD Pipeline

This repository includes GitHub Actions for automated testing and deployment.

## Environment Variables

See `.env.production` for all required environment variables.

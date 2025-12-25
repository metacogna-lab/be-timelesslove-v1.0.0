#!/bin/bash
# Quick Update Script for AWS Lightsail
# This script pulls the latest code and redeploys

set -e

echo "🔄 Updating Timeless Love Backend..."
echo ""

cd /opt/timeless-love/backend

# Pull latest code
echo "📥 Pulling latest code..."
git pull origin main
echo ""

# Rebuild and restart
echo "🏗️  Rebuilding and restarting..."
docker-compose -f docker-compose.production.yml up -d --build
echo ""

# Wait for health check
echo "⏳ Waiting for services to start..."
sleep 10
echo ""

# Check health
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Update complete! Backend is healthy."
else
    echo "⚠️  Warning: Health check failed"
    docker-compose -f docker-compose.production.yml logs --tail=20 backend
fi
echo ""

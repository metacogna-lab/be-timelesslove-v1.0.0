#!/bin/bash
# AWS Lightsail Deployment Script
# This script deploys the Timeless Love backend to AWS Lightsail

set -e

echo "🚀 Deploying Timeless Love Backend to AWS Lightsail..."
echo ""

# Navigate to backend directory
cd /opt/timeless-love/backend || {
    echo "❌ Error: /opt/timeless-love/backend directory not found"
    echo "Please clone the repository first"
    exit 1
}

# Check for .env.production file
if [ ! -f ".env.production" ]; then
    echo "❌ Error: .env.production file not found"
    echo "Please create .env.production with your configuration"
    exit 1
fi
echo "✅ Environment file found"
echo ""

# Pull latest code (if using git)
echo "📥 Pulling latest code..."
if git rev-parse --git-dir > /dev/null 2>&1; then
    git pull origin main
    echo "✅ Code updated"
else
    echo "⚠️  Not a git repository, skipping pull"
fi
echo ""

# Stop existing containers
echo "🛑 Stopping existing containers..."
docker-compose -f docker-compose.production.yml down
echo "✅ Existing containers stopped"
echo ""

# Build new images
echo "🏗️  Building Docker images..."
docker-compose -f docker-compose.production.yml build --no-cache
echo "✅ Docker images built"
echo ""

# Start containers
echo "🚀 Starting containers..."
docker-compose -f docker-compose.production.yml --env-file .env.production up -d
echo "✅ Containers started"
echo ""

# Wait for health checks
echo "⏳ Waiting for health checks..."
sleep 10
echo ""

# Check container status
echo "📊 Container Status:"
docker-compose -f docker-compose.production.yml ps
echo ""

# Check backend health
echo "🏥 Checking backend health..."
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Backend is healthy"
else
    echo "⚠️  Backend health check failed, checking logs..."
    docker-compose -f docker-compose.production.yml logs --tail=50 backend
fi
echo ""

# Clean up old images
echo "🧹 Cleaning up old Docker images..."
docker image prune -f
echo "✅ Cleanup complete"
echo ""

echo "✅ Deployment complete!"
echo ""
echo "📊 Service URLs:"
echo "   - API: http://$(curl -s ifconfig.me)"
echo "   - Health: http://$(curl -s ifconfig.me)/health"
echo "   - Docs: http://$(curl -s ifconfig.me)/docs (if DEBUG=true)"
echo ""
echo "📝 View logs with: docker-compose -f docker-compose.production.yml logs -f"
echo "🛑 Stop services with: docker-compose -f docker-compose.production.yml down"
echo ""

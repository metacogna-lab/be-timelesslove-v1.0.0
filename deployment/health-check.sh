#!/bin/bash
# Health Check Script for Monitoring

set -e

echo "🏥 Running health checks..."
echo ""

# Check Docker containers
echo "📦 Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# Check backend health endpoint
echo "🔍 Backend Health Check:"
if curl -f http://localhost/health 2>/dev/null; then
    echo "✅ Backend is responding"
else
    echo "❌ Backend is not responding"
fi
echo ""

# Check Nginx
echo "🌐 Nginx Status:"
if curl -f http://localhost 2>/dev/null > /dev/null; then
    echo "✅ Nginx is responding"
else
    echo "❌ Nginx is not responding"
fi
echo ""

# Check SSL certificate expiry (if HTTPS is set up)
if [ -f "/opt/timeless-love/backend/nginx/ssl/fullchain.pem" ]; then
    echo "🔒 SSL Certificate Status:"
    EXPIRY=$(openssl x509 -enddate -noout -in /opt/timeless-love/backend/nginx/ssl/fullchain.pem | cut -d= -f2)
    echo "   Expires: $EXPIRY"
    echo ""
fi

# Check disk space
echo "💾 Disk Space:"
df -h / | tail -1
echo ""

# Check memory usage
echo "🧠 Memory Usage:"
free -h | grep Mem
echo ""

echo "✅ Health check complete"

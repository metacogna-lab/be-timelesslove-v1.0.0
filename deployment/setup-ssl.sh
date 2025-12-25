#!/bin/bash
# SSL Certificate Setup Script for AWS Lightsail
# This script sets up Let's Encrypt SSL certificates using Certbot

set -e

echo "🔒 Setting up SSL certificates for Timeless Love Backend..."
echo ""

# Check if domain is set
read -p "Enter your API domain (e.g., api.yourdomain.com): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Error: Domain is required"
    exit 1
fi

echo "📧 Setting up SSL for: $DOMAIN"
echo ""

# Check if Certbot is installed
if ! command -v certbot &> /dev/null; then
    echo "❌ Error: Certbot is not installed"
    echo "Run setup-lightsail.sh first"
    exit 1
fi

# Stop Nginx to allow Certbot to bind to port 80
echo "🛑 Stopping Nginx..."
cd /opt/timeless-love/backend
docker-compose -f docker-compose.production.yml stop nginx
echo ""

# Get SSL certificate
echo "🔐 Obtaining SSL certificate from Let's Encrypt..."
sudo certbot certonly --standalone \
    --preferred-challenges http \
    --agree-tos \
    --email admin@${DOMAIN#*.} \
    -d $DOMAIN

if [ $? -eq 0 ]; then
    echo "✅ SSL certificate obtained successfully"
else
    echo "❌ Error: Failed to obtain SSL certificate"
    exit 1
fi
echo ""

# Copy certificates to Nginx directory
echo "📋 Copying certificates to Nginx directory..."
sudo cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /opt/timeless-love/backend/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/privkey.pem /opt/timeless-love/backend/nginx/ssl/
sudo cp /etc/letsencrypt/live/$DOMAIN/chain.pem /opt/timeless-love/backend/nginx/ssl/
sudo chmod 644 /opt/timeless-love/backend/nginx/ssl/*.pem
echo "✅ Certificates copied"
echo ""

# Update Nginx configuration with domain
echo "📝 Updating Nginx configuration with domain..."
sed -i "s/api.yourdomain.com/$DOMAIN/g" /opt/timeless-love/backend/nginx/conf.d/backend.conf
echo "✅ Nginx configuration updated"
echo ""

# Restart Nginx
echo "🔄 Restarting Nginx..."
docker-compose -f docker-compose.production.yml up -d nginx
echo "✅ Nginx restarted"
echo ""

# Set up automatic certificate renewal
echo "⏰ Setting up automatic certificate renewal..."
CRON_JOB="0 0 * * * certbot renew --quiet --post-hook 'cp /etc/letsencrypt/live/$DOMAIN/*.pem /opt/timeless-love/backend/nginx/ssl/ && cd /opt/timeless-love/backend && docker-compose -f docker-compose.production.yml restart nginx'"

(crontab -l 2>/dev/null | grep -v "certbot renew"; echo "$CRON_JOB") | crontab -
echo "✅ Automatic renewal configured (runs daily at midnight)"
echo ""

echo "✅ SSL setup complete!"
echo ""
echo "🌐 Your API is now available at: https://$DOMAIN"
echo "🏥 Health check: https://$DOMAIN/health"
echo "📚 API docs: https://$DOMAIN/docs (if DEBUG=true)"
echo ""
echo "🔄 Certificate will auto-renew 30 days before expiration"
echo ""

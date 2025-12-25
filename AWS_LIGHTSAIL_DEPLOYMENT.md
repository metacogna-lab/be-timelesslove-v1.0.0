# AWS Lightsail Deployment Guide

This guide walks you through deploying the Timeless Love backend API to AWS Lightsail with a static IP address.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Static IP Configuration](#static-ip-configuration)
- [SSL/TLS Setup](#ssltls-setup)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)
- [Security Best Practices](#security-best-practices)

## Prerequisites

- AWS account with billing enabled
- Domain name (for SSL certificates)
- Supabase project set up
- GitHub repository access
- SSH client installed locally

## Overview

This deployment uses:
- ✅ **AWS Lightsail**: VPS hosting with static IP
- ✅ **Docker + Docker Compose**: Containerized deployment
- ✅ **Nginx**: Reverse proxy with SSL termination
- ✅ **Let's Encrypt**: Free SSL/TLS certificates
- ✅ **FastAPI + Uvicorn**: Python backend with 4 workers
- ✅ **Health checks**: Automatic container monitoring

**Architecture**:
```
Internet → Static IP → Nginx (Port 443/80) → FastAPI (Port 8000)
```

## Quick Start

### 1. Create Lightsail Instance

1. Log in to [AWS Lightsail Console](https://lightsail.aws.amazon.com/)
2. Click **Create instance**
3. Select:
   - **Platform**: Linux/Unix
   - **Blueprint**: OS Only → Ubuntu 22.04 LTS
   - **Instance plan**: $10/month (2 GB RAM, 1 vCPU, 60 GB SSD) - Recommended
   - **Instance name**: `timeless-love-api`
4. Click **Create instance**
5. Wait for instance to start (status: Running)

### 2. Attach Static IP

1. In Lightsail console, go to **Networking** tab
2. Click **Create static IP**
3. Select your instance (`timeless-love-api`)
4. Name it: `timeless-love-api-static-ip`
5. Click **Create**
6. **Note the IP address** (e.g., `3.16.152.87`)

### 3. Configure DNS

Point your domain to the static IP:

**DNS Records** (in your domain registrar or DNS provider):
```
Type: A
Name: api (or @ for root domain)
Value: <your-static-ip>
TTL: 300 (or default)
```

Example:
- `api.yourdomain.com` → `3.16.152.87`

**Verify DNS propagation**:
```bash
dig api.yourdomain.com
# or
nslookup api.yourdomain.com
```

### 4. Connect via SSH

```bash
# Download SSH key from Lightsail console (if not done already)
# Account → SSH keys → Download

# Set permissions
chmod 400 ~/Downloads/LightsailDefaultKey-*.pem

# Connect to instance
ssh -i ~/Downloads/LightsailDefaultKey-*.pem ubuntu@<your-static-ip>
```

### 5. Run Setup Script

```bash
# Download and run setup script
wget https://raw.githubusercontent.com/yourusername/timelesslove-alpha-0.3/main/backend/deployment/setup-lightsail.sh
chmod +x setup-lightsail.sh
./setup-lightsail.sh

# Log out and log back in for Docker group changes
exit
ssh -i ~/Downloads/LightsailDefaultKey-*.pem ubuntu@<your-static-ip>
```

### 6. Clone Repository

```bash
# Clone to /opt/timeless-love
cd /opt
sudo git clone https://github.com/yourusername/timelesslove-alpha-0.3.git timeless-love
sudo chown -R ubuntu:ubuntu /opt/timeless-love
cd /opt/timeless-love/backend
```

### 7. Configure Environment

```bash
# Create production environment file
cp .env.production.example .env.production

# Edit with your values
nano .env.production
```

**Required variables** (see `.env.production.example` for full list):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `JWT_SECRET_KEY` (generate with: `openssl rand -hex 32`)
- `CORS_ORIGINS` (include your Cloudflare Pages domain)

### 8. Update Nginx Configuration

```bash
# Edit Nginx backend configuration
nano nginx/conf.d/backend.conf

# Replace "api.yourdomain.com" with your actual domain
# Replace "https://yourdomain.com" with your frontend domain in CORS headers
```

### 9. Deploy Application

```bash
# Run deployment script
./deployment/deploy.sh
```

This will:
- Build Docker images
- Start backend and Nginx containers
- Run health checks

### 10. Set Up SSL

```bash
# Run SSL setup script
./deployment/setup-ssl.sh

# Enter your domain when prompted (e.g., api.yourdomain.com)
```

This will:
- Obtain Let's Encrypt SSL certificate
- Configure Nginx for HTTPS
- Set up automatic certificate renewal

### 11. Verify Deployment

```bash
# Check services
docker ps

# Test health endpoint
curl https://api.yourdomain.com/health

# View logs
./deployment/logs.sh
```

**Expected response**:
```json
{"status": "healthy"}
```

## Detailed Setup

### Instance Specifications

**Recommended plans**:

| Plan | RAM | vCPU | Storage | Transfer | Price |
|------|-----|------|---------|----------|-------|
| Small | 2 GB | 1 | 60 GB | 3 TB | $10/month |
| Medium | 4 GB | 2 | 80 GB | 4 TB | $20/month |
| Large | 8 GB | 2 | 160 GB | 5 TB | $40/month |

**For production**: Start with $10/month plan, upgrade as needed.

### Firewall Configuration

Lightsail automatically configures firewall rules. Verify these ports are open:

| Port | Protocol | Purpose |
|------|----------|---------|
| 22 | TCP | SSH access |
| 80 | TCP | HTTP (redirects to HTTPS) |
| 443 | TCP | HTTPS (production traffic) |

**To modify firewall**:
1. In Lightsail console, select your instance
2. Go to **Networking** tab
3. Click **Edit rules** under Firewall
4. Add/remove rules as needed

### Storage Management

Monitor disk usage:
```bash
df -h
```

**Disk cleanup**:
```bash
# Remove old Docker images
docker image prune -a -f

# Remove old containers
docker container prune -f

# Remove old volumes
docker volume prune -f

# System cleanup
sudo apt-get autoremove -y
sudo apt-get clean
```

## Static IP Configuration

### Creating a Static IP

Static IPs in Lightsail:
- ✅ **Free** when attached to a running instance
- ✅ **Persistent** across instance restarts
- ✅ **Portable** - can be moved between instances
- ⚠️ **Charged** $0.005/hour (~$3.60/month) when not attached

**To create**:
```bash
# Via AWS CLI (optional)
aws lightsail allocate-static-ip --static-ip-name timeless-love-api-static-ip

# Attach to instance
aws lightsail attach-static-ip \
  --static-ip-name timeless-love-api-static-ip \
  --instance-name timeless-love-api
```

### Moving Static IP

To move static IP to a new instance:
1. Create new instance
2. Detach static IP from old instance
3. Attach static IP to new instance
4. Update instance (no DNS changes needed!)

## SSL/TLS Setup

### Let's Encrypt Certificates

The `setup-ssl.sh` script automates SSL setup:

**Manual setup**:
```bash
# Stop Nginx
docker-compose -f docker-compose.production.yml stop nginx

# Get certificate
sudo certbot certonly --standalone \
  --preferred-challenges http \
  --agree-tos \
  --email admin@yourdomain.com \
  -d api.yourdomain.com

# Copy to Nginx directory
sudo cp /etc/letsencrypt/live/api.yourdomain.com/fullchain.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/privkey.pem nginx/ssl/
sudo cp /etc/letsencrypt/live/api.yourdomain.com/chain.pem nginx/ssl/
sudo chmod 644 nginx/ssl/*.pem

# Start Nginx
docker-compose -f docker-compose.production.yml up -d nginx
```

### Certificate Renewal

Certificates auto-renew via cron job (set up by `setup-ssl.sh`).

**Manual renewal**:
```bash
# Test renewal (dry run)
sudo certbot renew --dry-run

# Actual renewal
sudo certbot renew

# Reload Nginx after renewal
docker-compose -f docker-compose.production.yml restart nginx
```

**Check expiry**:
```bash
sudo certbot certificates
```

### SSL Configuration

Nginx is configured with:
- ✅ TLS 1.2 and TLS 1.3 only
- ✅ Strong cipher suites
- ✅ OCSP stapling
- ✅ HSTS headers
- ✅ Perfect Forward Secrecy

**Test SSL configuration**:
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- Expected grade: A or A+

## Environment Configuration

### Required Environment Variables

Create `.env.production` from template:

```bash
cp .env.production.example .env.production
nano .env.production
```

**Critical variables**:

1. **Supabase Configuration**:
   ```env
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=eyJ...
   SUPABASE_SERVICE_ROLE_KEY=eyJ...
   ```

2. **JWT Configuration**:
   ```env
   JWT_SECRET_KEY=$(openssl rand -hex 32)
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
   JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
   ```

3. **CORS Configuration**:
   ```env
   CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com,https://your-project.pages.dev
   ```

4. **Database Configuration**:
   ```env
   SUPABASE_DB_URL=postgresql://postgres.abc123:password@aws-0-us-west-1.pooler.supabase.com:6543/postgres
   SUPABASE_DB_PASSWORD=your-db-password
   ```

### Security Best Practices

1. **Never commit `.env.production`** to version control
2. **Use strong, unique secrets** for JWT_SECRET_KEY
3. **Rotate secrets** periodically (every 90 days)
4. **Limit CORS origins** to only your frontend domains
5. **Keep DEBUG=false** in production
6. **Use environment-specific values** for staging vs production

## Deployment

### Initial Deployment

```bash
cd /opt/timeless-love/backend
./deployment/deploy.sh
```

**What it does**:
1. Stops existing containers
2. Builds fresh Docker images
3. Starts containers with production config
4. Runs health checks
5. Cleans up old images

### Updating Deployment

```bash
# Quick update (pull + rebuild + restart)
./deployment/update.sh

# Or manual steps:
git pull origin main
docker-compose -f docker-compose.production.yml up -d --build
```

### Rollback

If deployment fails, rollback to previous version:

```bash
# Find previous Docker image
docker images

# Tag and use previous image
docker tag <previous-image-id> backend:latest

# Restart with previous image
docker-compose -f docker-compose.production.yml up -d
```

Or rollback via Git:
```bash
git log --oneline
git checkout <previous-commit>
./deployment/deploy.sh
```

### Zero-Downtime Deployment

For zero-downtime updates:

```bash
# Build new image without stopping containers
docker-compose -f docker-compose.production.yml build

# Rolling update (one worker at a time)
docker-compose -f docker-compose.production.yml up -d --no-deps --build backend

# Nginx continues serving old containers until new ones are healthy
```

## Monitoring & Maintenance

### Health Checks

**Automatic health checks**:
- Docker healthcheck runs every 30 seconds
- Nginx upstream health monitoring
- Unhealthy containers auto-restart

**Manual health check**:
```bash
./deployment/health-check.sh
```

### Viewing Logs

```bash
# All logs
./deployment/logs.sh

# Backend logs only
./deployment/logs.sh backend

# Nginx logs only
./deployment/logs.sh nginx

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100

# Follow logs in real-time
docker-compose -f docker-compose.production.yml logs -f
```

### Performance Monitoring

**Container stats**:
```bash
docker stats
```

**System resources**:
```bash
# CPU usage
top

# Memory usage
free -h

# Disk usage
df -h

# Network usage
iftop
```

### Database Monitoring

**Check Supabase connection**:
```bash
# Test from container
docker exec -it timeless-love-backend python3 -c "
from app.db.supabase_client import get_supabase_client
client = get_supabase_client()
print('Supabase connection: OK')
"
```

**Monitor database pool**:
- Check Supabase dashboard → Database → Connection Pooling
- Monitor active connections and queries

### Backup Strategy

**Database backups**:
- Supabase automatically backs up database (Point-in-time recovery)
- Backups retained for 7 days (Free plan) or 30 days (Pro plan)

**Configuration backups**:
```bash
# Backup environment and configs
cd /opt/timeless-love/backend
tar -czf ~/backup-$(date +%Y%m%d).tar.gz \
  .env.production \
  nginx/conf.d/backend.conf \
  docker-compose.production.yml

# Copy to S3 or local machine
scp ubuntu@<static-ip>:~/backup-*.tar.gz ~/backups/
```

### Automated Monitoring (Optional)

**Set up monitoring with cron**:
```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * /opt/timeless-love/backend/deployment/health-check.sh >> /opt/timeless-love/logs/health.log 2>&1
```

**External monitoring** (recommended):
- **UptimeRobot**: Free uptime monitoring
- **Pingdom**: Comprehensive monitoring
- **Datadog**: Full observability (paid)
- **CloudWatch**: AWS native monitoring

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

**Symptoms**:
- `docker ps` shows container missing or restarting
- Health check fails

**Solutions**:
```bash
# Check logs
docker-compose -f docker-compose.production.yml logs backend

# Common causes:
# - Missing environment variables
# - Invalid Supabase credentials
# - Port already in use

# Verify environment file
cat .env.production

# Test Supabase connection
curl https://$SUPABASE_URL/rest/v1/
```

#### 2. SSL Certificate Issues

**Symptoms**:
- HTTPS not working
- Certificate expired

**Solutions**:
```bash
# Check certificate expiry
sudo certbot certificates

# Renew certificate
sudo certbot renew --force-renewal

# Restart Nginx
docker-compose -f docker-compose.production.yml restart nginx
```

#### 3. CORS Errors

**Symptoms**:
- Frontend can't connect to API
- "CORS policy" errors in browser console

**Solutions**:
```bash
# Check CORS_ORIGINS in .env.production
grep CORS_ORIGINS .env.production

# Ensure it includes your frontend domain
# Example: CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Restart backend
docker-compose -f docker-compose.production.yml restart backend
```

#### 4. High Memory Usage

**Symptoms**:
- Instance slow or unresponsive
- Out of memory errors

**Solutions**:
```bash
# Check memory usage
free -h
docker stats

# Restart containers to free memory
docker-compose -f docker-compose.production.yml restart

# Consider upgrading instance plan
# Or reduce Uvicorn workers in Dockerfile.production
```

#### 5. Database Connection Issues

**Symptoms**:
- "Connection refused" errors
- Timeout errors

**Solutions**:
```bash
# Verify Supabase DB URL
echo $SUPABASE_DB_URL

# Test connection
docker exec -it timeless-love-backend psql $SUPABASE_DB_URL

# Common causes:
# - Wrong pooler port (use 6543 for transaction pooler)
# - Firewall blocking connection
# - Invalid credentials
```

### Debugging Tools

```bash
# Enter backend container
docker exec -it timeless-love-backend bash

# Check environment variables
docker exec timeless-love-backend env

# Test API from inside container
docker exec timeless-love-backend curl http://localhost:8000/health

# Check Nginx configuration
docker exec timeless-love-nginx nginx -t

# Reload Nginx config
docker exec timeless-love-nginx nginx -s reload
```

### Log Analysis

```bash
# Search logs for errors
docker-compose -f docker-compose.production.yml logs | grep ERROR

# Filter by timestamp
docker-compose -f docker-compose.production.yml logs --since 1h

# Export logs
docker-compose -f docker-compose.production.yml logs > debug.log
```

## Cost Estimation

### AWS Lightsail Costs

**Instance costs** (monthly):
- **$10/month**: 2 GB RAM, 1 vCPU, 60 GB SSD, 3 TB transfer (Recommended)
- **$20/month**: 4 GB RAM, 2 vCPU, 80 GB SSD, 4 TB transfer
- **$40/month**: 8 GB RAM, 2 vCPU, 160 GB SSD, 5 TB transfer

**Additional costs**:
- **Static IP**: Free when attached to running instance
- **Snapshots**: $0.05/GB per month (optional, for backups)
- **Data transfer**: Included in plan (3-5 TB/month)
- **SSL certificate**: Free (Let's Encrypt)

**Total estimated cost**: **$10-40/month** depending on plan.

### Cost Optimization

1. **Right-size instance**: Start small, upgrade as needed
2. **Delete old snapshots**: Keep only essential backups
3. **Monitor data transfer**: Included transfer is generous
4. **Use Lightsail CDN**: If serving static assets (not needed for API)

## Security Best Practices

### Instance Security

1. **SSH Key Authentication**:
   - Use SSH keys (not passwords)
   - Disable password authentication:
     ```bash
     sudo nano /etc/ssh/sshd_config
     # Set: PasswordAuthentication no
     sudo systemctl restart sshd
     ```

2. **Firewall**:
   - Only open required ports (22, 80, 443)
   - Use Lightsail firewall rules
   - Consider fail2ban for SSH protection

3. **Regular Updates**:
   ```bash
   sudo apt-get update && sudo apt-get upgrade -y
   ```

4. **Non-root User**:
   - Always use `ubuntu` user (not root)
   - Containers run as non-root user

### Application Security

1. **Environment Variables**:
   - Never commit `.env.production`
   - Use strong, unique secrets
   - Rotate secrets regularly

2. **CORS Configuration**:
   - Limit to specific frontend domains
   - Never use `*` in production

3. **Rate Limiting**:
   - Nginx configured with rate limits
   - 10 req/s for API, 5 req/s for auth

4. **HTTPS Only**:
   - All HTTP redirects to HTTPS
   - HSTS headers enabled
   - TLS 1.2+ only

5. **Security Headers**:
   - X-Frame-Options: DENY
   - X-Content-Type-Options: nosniff
   - Strict-Transport-Security
   - Configured in Nginx

### Monitoring Security

1. **Log Monitoring**:
   - Review logs for suspicious activity
   - Monitor failed authentication attempts

2. **SSL Monitoring**:
   - Monitor certificate expiry
   - Use SSL Labs for periodic tests

3. **Dependency Updates**:
   ```bash
   # Update Python dependencies
   cd /opt/timeless-love/backend
   pip list --outdated
   ```

## Additional Resources

### Documentation

- [AWS Lightsail Documentation](https://docs.aws.amazon.com/lightsail/)
- [Docker Documentation](https://docs.docker.com/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Tools

- [AWS Lightsail Console](https://lightsail.aws.amazon.com/)
- [Supabase Dashboard](https://app.supabase.com/)
- [SSL Labs Test](https://www.ssllabs.com/ssltest/)
- [DNS Checker](https://dnschecker.org/)

### Support

- [AWS Lightsail Support](https://console.aws.amazon.com/support/)
- [FastAPI Community](https://github.com/tiangolo/fastapi/discussions)
- [Nginx Community](https://forum.nginx.org/)

## Next Steps

After deploying the backend:

1. ✅ Verify health endpoint: `https://api.yourdomain.com/health`
2. ✅ Test API documentation: `https://api.yourdomain.com/docs` (if DEBUG=true)
3. ✅ Update frontend `VITE_API_BASE_URL` to point to your domain
4. ✅ Test authentication flow end-to-end
5. ✅ Set up monitoring (UptimeRobot, Datadog, etc.)
6. ✅ Configure backup strategy
7. ✅ Set up staging environment (optional)
8. ✅ Load testing (optional)

## Maintenance Checklist

**Weekly**:
- [ ] Check container health
- [ ] Review error logs
- [ ] Monitor disk space

**Monthly**:
- [ ] Update system packages
- [ ] Review SSL certificate expiry
- [ ] Check Supabase usage metrics
- [ ] Review API error rates

**Quarterly**:
- [ ] Rotate JWT secret
- [ ] Update Python dependencies
- [ ] Review and optimize Docker images
- [ ] Backup configuration files

---

**Questions or issues?** Check the troubleshooting section or create an issue in the repository.

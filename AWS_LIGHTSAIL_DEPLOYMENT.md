# AWS Lightsail + Cloudflare Tunnel Deployment Guide

This guide walks you through deploying the Timeless Love backend API to AWS Lightsail using [Cloudflare Tunnel](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/) for secure, zero-config HTTPS exposure (no Nginx needed).

## Table of Contents

- [Prerequisites](#prerequisites)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Firewall Configuration](#firewall-configuration)
- [Cloudflare Tunnel Setup](#cloudflare-tunnel-setup)
- [Environment Configuration](#environment-configuration)
- [Deployment](#deployment)
- [Monitoring & Maintenance](#monitoring--maintenance)
- [Troubleshooting](#troubleshooting)
- [Cost Estimation](#cost-estimation)
- [Security Best Practices](#security-best-practices)

## Prerequisites

- AWS account with billing enabled
- [Cloudflare account](https://dash.cloudflare.com/) with your domain added and using Cloudflare DNS
- Supabase project set up
- GitHub repository access
- SSH client installed locally

## Overview

This deployment uses:
- ✅ **AWS Lightsail**: VPS hosting
- ✅ **Docker + Docker Compose**: Containerized deployment
- ✅ **Cloudflare Tunnel**: Secure, auto-SSL tunneling for HTTPS exposure—no web server or ports need to be exposed
- ✅ **FastAPI + Uvicorn**: Python backend with multiple workers
- ✅ **Health checks**: Automatic container monitoring

**Architecture**:
```
Client → Cloudflare (HTTPS) → Cloudflare Tunnel → FastAPI (localhost:8000)
```

No direct inbound ports need to be open to the instance except SSH!

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

### 2. (Optional) Attach Static IP

Not strictly needed when using Cloudflare Tunnel, but you may want one for SSH stability.

1. In Lightsail console, go to **Networking** tab  
2. Click **Create static IP**  
3. Select your instance  
4. Name it: `timeless-love-api-static-ip`  
5. Click **Create**  
6. Note the IP address (for SSH)

### 3. Connect via SSH

```bash
# Download SSH key from Lightsail console (if not done already)
chmod 400 ~/Downloads/LightsailDefaultKey-*.pem

# Connect to instance
ssh -i ~/Downloads/LightsailDefaultKey-*.pem ubuntu@<your-static-ip>
```

### 4. Run Setup Script

```bash
# Download and run setup script (installs Docker)
wget https://raw.githubusercontent.com/yourusername/timelesslove-alpha-0.3/main/backend/deployment/setup-lightsail.sh
chmod +x setup-lightsail.sh
./setup-lightsail.sh

# Log out and log back in for Docker group changes
exit
ssh -i ~/Downloads/LightsailDefaultKey-*.pem ubuntu@<your-static-ip>
```

### 5. Clone Repository

```bash
cd /opt
sudo git clone https://github.com/yourusername/timelesslove-alpha-0.3.git timeless-love
sudo chown -R ubuntu:ubuntu /opt/timeless-love
cd /opt/timeless-love/backend
```

### 6. Configure Environment

```bash
cp .env.production.example .env.production
nano .env.production
```

**Required variables** (see `.env.production.example` for full list):
- `SUPABASE_URL`
- `SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY`
- `JWT_SECRET_KEY` (generate with: `openssl rand -hex 32`)
- `CORS_ORIGINS` (include your frontend/Cloudflare Pages domains)

### 7. Deploy Application

```bash
./deployment/deploy.sh
```

- Builds Docker images for FastAPI backend
- Starts containers (no Nginx needed)
- Runs health checks

### 8. Set Up Cloudflare Tunnel

#### 1. Install Cloudflare Tunnel (cloudflared)

On your Lightsail instance:
```bash
wget -O cloudflared https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64
sudo mv cloudflared /usr/local/bin/
sudo chmod +x /usr/local/bin/cloudflared
cloudflared --version
```

#### 2. Authenticate cloudflared

Run:
```bash
cloudflared tunnel login
```
This opens a browser — follow Cloudflare's instructions to authenticate.

#### 3. Create and Run Tunnel

```bash
cloudflared tunnel create timeless-love-tunnel
```
This outputs a tunnel ID.

#### 4. Configure the Tunnel Routing

Create a configuration file (e.g. `/home/ubuntu/.cloudflared/config.yml`) with:
```yaml
tunnel: <tunnel-id-from-above>
credentials-file: /home/ubuntu/.cloudflared/<tunnel-id-from-above>.json

ingress:
  - hostname: api.timelesslove.ai
    service: http://localhost:8000
  - service: http_status:404
```

#### 5. Add CNAME in Cloudflare DNS

In the Cloudflare dashboard for your domain, add a **CNAME** DNS record:
- **Name**: `api`
- **Target**: `<tunnel-UUID>.cfargotunnel.com`
- **Proxy status**: Proxied (orange cloud)

#### 6. Start the Tunnel as a Service

```bash
cloudflared service install
sudo systemctl start cloudflared
sudo systemctl enable cloudflared
sudo systemctl status cloudflared
```

Your API will now be accessible at `https://api.timelesslove.ai` with automatic SSL (using Cloudflare's certs)!

### 9. Verify Deployment

```bash
docker ps
curl -i https://api.timelesslove.ai/health
./deployment/logs.sh
```

**Expected response**:
```json
{"status":"healthy"}
```

## Detailed Setup

### Instance Specifications

**Recommended plans**:

| Plan   | RAM | vCPU | Storage | Transfer | Price      |
|--------|-----|------|---------|----------|------------|
| Small  | 2GB | 1    | 60GB    | 3TB      | $10/month  |
| Medium | 4GB | 2    | 80GB    | 4TB      | $20/month  |
| Large  | 8GB | 2    | 160GB   | 5TB      | $40/month  |

**For production**: Start with $10/month, upgrade as needed.

### Firewall Configuration

With Cloudflare Tunnel, you **DO NOT need to open ports 80 or 443**—only port **22** (SSH) should remain open.  
Verify Lightsail firewall:

| Port | Protocol | Purpose   |
|------|----------|-----------|
| 22   | TCP      | SSH access|

You may close all others for maximum security.

### Storage Management

Monitor disk usage:
```bash
df -h
```
Clean up Docker artifacts:
```bash
docker image prune -a -f
docker container prune -f
docker volume prune -f
sudo apt-get autoremove -y
sudo apt-get clean
```

## Cloudflare Tunnel Setup

**Advantages**:
- No Nginx or web server on VM
- No SSL/TLS setup on VM (Cloudflare manages SSL)
- No public inbound ports beyond SSH

See "Quick Start" above for a step-by-step guide.

**CORS Note:**  
You **must** set `CORS_ORIGINS` in the backend environment to match your frontend domain(s), including those that Cloudflare proxies.

**Extra Security:**  
You can use Cloudflare Access to require login/authentication before requests reach your backend, if desired.

## Environment Configuration

Copy `.env.production.example` to `.env.production` and edit as needed:

**Critical variables** (same as prior Nginx-based deploy):

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

1. Never commit `.env.production`
2. Use a strong, unique JWT_SECRET_KEY
3. Rotate secrets at least every 90 days
4. Limit CORS origins
5. Keep DEBUG=false in production

## Deployment

### Initial Deployment

```bash
cd /opt/timeless-love/backend
./deployment/deploy.sh
```

- Stops existing backend container
- Rebuilds image
- Starts container with production config

### Updating Deployment

```bash
./deployment/update.sh

# Or manually:
git pull origin main
docker-compose -f docker-compose.production.yml up -d --build
```

### Rollback

```bash
# Find previous Docker image
docker images

# Tag back and restart
docker tag <previous-image-id> backend:latest
docker-compose -f docker-compose.production.yml up -d
```

Or via Git:
```bash
git log --oneline
git checkout <previous-commit>
./deployment/deploy.sh
```

### Zero-Downtime Deployment

```bash
docker-compose -f docker-compose.production.yml build
docker-compose -f docker-compose.production.yml up -d --no-deps --build backend
```

Cloudflare Tunnel will keep serving healthy backend processes.

## Monitoring & Maintenance

### Health Checks

- Docker healthcheck runs every 30 seconds
- Cloudflare will report unhealthy tunnels if down

Manual health check:
```bash
./deployment/health-check.sh
```

### Viewing Logs

```bash
./deployment/logs.sh
./deployment/logs.sh backend

# Last 100 lines
docker-compose -f docker-compose.production.yml logs --tail=100
```

### Performance Monitoring

```bash
docker stats
top    # CPU usage
free -h  # Memory usage
df -h  # Disk usage
```

### Database Monitoring

Check Supabase connection (see earlier).

### Backup Strategy

Back up `.env.production`, `docker-compose.production.yml`:
```bash
cd /opt/timeless-love/backend
tar -czf ~/backup-$(date +%Y%m%d).tar.gz \
  .env.production \
  docker-compose.production.yml

scp ubuntu@<static-ip>:~/backup-*.tar.gz ~/backups/
```

### Automated Monitoring (Optional)

Set up cron for health check:
```bash
crontab -e
*/5 * * * * /opt/timeless-love/backend/deployment/health-check.sh >> /opt/timeless-love/logs/health.log 2>&1
```

**External monitoring**:
- UptimeRobot
- Pingdom  
- Datadog

## Troubleshooting

### Common Issues

#### 1. Container Won't Start

- Check Docker logs:
```bash
docker-compose -f docker-compose.production.yml logs backend
```
Common causes: env file issues, invalid secrets

#### 2. Cloudflare Tunnel Not Working

- Check tunnel logs:
```bash
journalctl -u cloudflared.service -n 100 --no-pager
```
- Validate tunnel config
- Ensure DNS CNAME record exists and matches tunnel ID (see above)
- Restart service:
```bash
sudo systemctl restart cloudflared
sudo systemctl status cloudflared
```

#### 3. CORS Errors

- Check `CORS_ORIGINS` in `.env.production`

#### 4. High Memory Usage

```bash
free -h
docker stats
docker-compose -f docker-compose.production.yml restart
```

#### 5. Database Connection Issues

Check `SUPABASE_DB_URL`, try connecting from inside the container.

### Debugging Tools

```bash
docker exec -it timeless-love-backend bash
docker exec timeless-love-backend env
docker exec timeless-love-backend curl http://localhost:8000/health
journalctl -u cloudflared.service -n 100 --no-pager
```

### Log Analysis

```bash
docker-compose -f docker-compose.production.yml logs | grep ERROR
docker-compose -f docker-compose.production.yml logs --since 1h
docker-compose -f docker-compose.production.yml logs > debug.log
```

## Cost Estimation

### AWS Lightsail Costs

**Instance costs** (monthly):
- $10/month: 2 GB RAM, 1 vCPU, 60 GB SSD, 3 TB transfer
- $20/month: 4 GB RAM, 2 vCPU, 80 GB SSD, 4 TB transfer
- $40/month: 8 GB RAM, 2 vCPU, 160 GB SSD, 5 TB transfer

**Cloudflare Tunnel**: Free (no per-tunnel traffic charges under normal Cloudflare plans)

**Total estimated cost**: $10–40/month (Lightsail only).

### Cost Optimization

- Use smallest suitable instance size
- Delete old snapshots
- Data transfer is routed over Cloudflare

## Security Best Practices

### Instance Security

1. SSH Key Authentication only  
2. **Close all inbound ports except 22 (SSH)**
3. Keep packages updated
4. Use `ubuntu` non-root user

### Application Security

1. Never commit `.env.production`  
2. Use strong JWT secrets, CORS origins
3. All SSL/TLS is enforced by Cloudflare
4. Use Cloudflare Access if you want access control to certain API endpoints

### Monitoring Security

- Watch logs for suspicious activity
- Consider enabling extra Cloudflare protections (WAF, bot management)
- Review expired API tokens and credentials

## Additional Resources

### Documentation

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Cloudflare Quick Start](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/)
- [AWS Lightsail Documentation](https://docs.aws.amazon.com/lightsail/)
- [Docker Documentation](https://docs.docker.com/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

### Tools

- [Cloudflare Dashboard](https://dash.cloudflare.com/)
- [AWS Lightsail Console](https://lightsail.aws.amazon.com/)
- [Supabase Dashboard](https://app.supabase.com/)
- [DNS Checker](https://dnschecker.org/)

### Support

- [Cloudflare Community](https://community.cloudflare.com/)
- [AWS Lightsail Support](https://console.aws.amazon.com/support/)
- [FastAPI Community](https://github.com/tiangolo/fastapi/discussions)

## Next Steps

After deploying the backend:

1. ✅ Verify health endpoint: `https://api.timelesslove.ai/health`
2. ✅ Test API documentation: `https://api.timelesslove.ai/docs` (if DEBUG=true)
3. ✅ Update frontend `VITE_API_BASE_URL` to point to your domain
4. ✅ Test authentication flow end-to-end
5. ✅ Set up monitoring (UptimeRobot, Datadog, etc.)
6. ✅ Configure backup strategy
7. ✅ Set up staging environment (optional)
8. ✅ Load testing (optional)

## Maintenance Checklist

**Weekly**:
- [ ] Check container and tunnel health
- [ ] Review error logs
- [ ] Monitor disk space

**Monthly**:
- [ ] Update system packages
- [ ] Review tunnel and Cloudflare dashboard
- [ ] Check Supabase metrics
- [ ] Review API error rates

**Quarterly**:
- [ ] Rotate JWT secret
- [ ] Update Python dependencies
- [ ] Review/optimize Docker images
- [ ] Backup configuration files

---

**Questions or issues?** Check the troubleshooting section or create an issue in the repository.

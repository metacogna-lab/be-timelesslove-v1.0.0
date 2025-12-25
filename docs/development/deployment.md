---
title: Deployment
description: Deployment process, environment setup, and monitoring
sidebar:
  order: 10
---

# Deployment

This guide covers the deployment process for the Timeless Love backend, including environment setup, database migrations, and monitoring.

## Pre-Deployment Checklist

### Environment Variables

Ensure all required environment variables are set:

```env
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-minimum-32-bytes
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Application Configuration
ENVIRONMENT=production
DEBUG=false
API_VERSION=v1

# CORS Configuration
CORS_ORIGINS=https://app.timelesslove.ai

# Media Processing
MEDIA_MAX_FILE_SIZE_MB=50
MEDIA_MAX_MEMORY_SIZE_MB=200
MEDIA_THUMBNAIL_SIZE=400
```

### Database Setup

1. **Apply Migrations**
   - Run all migrations from `db/migrations/`
   - Verify in Supabase Dashboard

2. **Storage Bucket**
   - Create `memories` bucket
   - Set to private
   - Configure RLS policies

3. **Row Level Security**
   - Verify RLS policies are enabled
   - Test family boundary enforcement

### Security Review

- [ ] JWT secret key is strong (minimum 32 bytes)
- [ ] Service role key is secure
- [ ] CORS origins are restricted
- [ ] Debug mode is disabled
- [ ] HTTPS is enforced
- [ ] Environment variables are secure

## Deployment Options

### Option 1: Platform-as-a-Service

#### Railway

1. **Connect Repository**
   - Link GitHub repository
   - Select backend directory

2. **Configure Environment**
   - Add all environment variables
   - Set Python version (3.11+)

3. **Deploy**
   - Automatic deployment on push
   - Manual deployment available

#### Render

1. **Create Web Service**
   - Connect repository
   - Select backend directory

2. **Build Command**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start Command**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```

4. **Environment Variables**
   - Add all required variables

#### Fly.io

1. **Install Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Initialize**
   ```bash
   fly launch
   ```

3. **Configure**
   - Set environment variables
   - Configure scaling

4. **Deploy**
   ```bash
   fly deploy
   ```

### Option 2: Container Deployment

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_ANON_KEY=${SUPABASE_ANON_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    env_file:
      - .env
```

#### Deploy to Cloud

**AWS ECS/Fargate:**
1. Build and push Docker image
2. Create ECS task definition
3. Configure environment variables
4. Deploy service

**Google Cloud Run:**
1. Build and push to Container Registry
2. Deploy to Cloud Run
3. Configure environment variables
4. Set scaling options

**Azure Container Instances:**
1. Build and push to Container Registry
2. Create container instance
3. Configure environment variables
4. Deploy

### Option 3: Traditional Server

#### Setup

1. **Install Dependencies**
   ```bash
   sudo apt update
   sudo apt install python3.11 python3-pip nginx
   ```

2. **Create Application User**
   ```bash
   sudo useradd -m -s /bin/bash timelesslove
   ```

3. **Clone Repository**
   ```bash
   git clone <repository-url> /opt/timelesslove
   cd /opt/timelesslove/backend
   ```

4. **Setup Virtual Environment**
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```

5. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

#### Process Manager (systemd)

Create `/etc/systemd/system/timelesslove.service`:

```ini
[Unit]
Description=Timeless Love Backend
After=network.target

[Service]
User=timelesslove
Group=timelesslove
WorkingDirectory=/opt/timelesslove/backend
Environment="PATH=/opt/timelesslove/backend/venv/bin"
ExecStart=/opt/timelesslove/backend/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable timelesslove
sudo systemctl start timelesslove
sudo systemctl status timelesslove
```

#### Reverse Proxy (Nginx)

Create `/etc/nginx/sites-available/timelesslove`:

```nginx
server {
    listen 80;
    server_name api.timelesslove.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable and restart:

```bash
sudo ln -s /etc/nginx/sites-available/timelesslove /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## Database Migrations

### Applying Migrations

1. **Review Migrations**
   ```bash
   ls -la db/migrations/
   ```

2. **Apply via Supabase Dashboard**
   - Go to SQL Editor
   - Copy migration SQL
   - Execute and verify

3. **Verify Migration**
   ```sql
   SELECT * FROM information_schema.tables 
   WHERE table_schema = 'public';
   ```

### Migration Best Practices

- Test migrations on development first
- Backup production database before migrations
- Apply migrations during maintenance window
- Verify data integrity after migration
- Rollback plan ready

## Monitoring

### Health Checks

The application provides a health check endpoint:

```bash
curl https://api.timelesslove.com/health
```

**Response:**
```json
{
  "status": "healthy"
}
```

### Logging

Structured logging is enabled by default:

- Request ID tracking
- User context in logs
- Error categorization
- Performance metrics

### Metrics

Monitor these key metrics:

- **API Request Rate**: Requests per second
- **Error Rate**: 4xx/5xx responses
- **Response Time**: P50, P95, P99 latencies
- **Database Connections**: Active connections
- **Storage Usage**: Media file storage

### Alerts

Set up alerts for:

- High error rate (> 1%)
- Slow response times (> 1s P95)
- Database connection issues
- Storage quota warnings
- Failed media processing

## Post-Deployment

### Verification

1. **Health Check**
   ```bash
   curl https://api.timelesslove.com/health
   ```

2. **API Documentation**
   - Visit `/docs` endpoint
   - Verify OpenAPI spec loads

3. **Test Authentication**
   ```bash
   curl -X POST https://api.timelesslove.com/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email": "test@example.com", "password": "test"}'
   ```

4. **Test Endpoints**
   - Verify all endpoints respond
   - Check error handling
   - Validate RBAC enforcement

### Rollback Plan

If issues occur:

1. **Revert Code**
   ```bash
   git revert <commit-hash>
   git push
   ```

2. **Rollback Database** (if needed)
   - Restore from backup
   - Revert migration if possible

3. **Restart Service**
   ```bash
   sudo systemctl restart timelesslove
   ```

## Scaling

### Horizontal Scaling

- Use load balancer (Nginx, AWS ALB, etc.)
- Multiple application instances
- Shared database (Supabase)
- Shared storage (Supabase Storage)

### Vertical Scaling

- Increase server resources
- Optimize database queries
- Add caching layer (Redis)
- CDN for media files

### Database Scaling

- Supabase handles database scaling
- Monitor connection pool usage
- Optimize queries with indexes
- Consider read replicas for heavy reads

## Security Hardening

### Production Security

1. **HTTPS Only**
   - Enforce HTTPS
   - Redirect HTTP to HTTPS
   - Use TLS 1.2+

2. **CORS Configuration**
   - Restrict to production frontend URL
   - No wildcard origins

3. **Rate Limiting**
   - Implement rate limiting (future)
   - Protect against DDoS

4. **Secrets Management**
   - Use secret management service
   - Rotate secrets regularly
   - Never commit secrets

5. **Security Headers**
   - Add security headers
   - Content Security Policy
   - X-Frame-Options

## Maintenance

### Regular Tasks

1. **Update Dependencies**
   ```bash
   pip list --outdated
   pip install --upgrade <package>
   ```

2. **Database Maintenance**
   - Monitor database size
   - Clean up old analytics data
   - Optimize indexes

3. **Storage Cleanup**
   - Remove orphaned media files
   - Archive old memories
   - Monitor storage usage

4. **Log Rotation**
   - Configure log rotation
   - Archive old logs
   - Monitor disk space

## Related Documentation

- [Getting Started](../getting-started.md)
- [Architecture Overview](../architecture/overview.md)
- [Contributing](./contributing.md)


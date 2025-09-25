# Istanbul Plus E-commerce Deployment Guide

## Overview

This guide covers the deployment of the Istanbul Plus E-commerce platform with its advanced authentication system.

## Prerequisites

### System Requirements

- Ubuntu 20.04+ or CentOS 8+
- Python 3.9+
- PostgreSQL 13+
- Redis 6+
- Nginx 1.18+
- SSL Certificate

### Required Services

- SMTP server for email delivery
- SMS gateway (Kavenegar or similar)
- Domain name with DNS configuration

## Installation Steps

### 1. System Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install system dependencies
sudo apt install -y python3-pip python3-venv postgresql postgresql-contrib redis-server nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash istanbulplus
sudo usermod -aG sudo istanbulplus
```

### 2. Database Setup

```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE istanbulplus;
CREATE USER istanbulplus WITH PASSWORD 'secure_password_here';
ALTER ROLE istanbulplus SET client_encoding TO 'utf8';
ALTER ROLE istanbulplus SET default_transaction_isolation TO 'read committed';
ALTER ROLE istanbulplus SET timezone TO 'Asia/Tehran';
GRANT ALL PRIVILEGES ON DATABASE istanbulplus TO istanbulplus;
\q
```

### 3. Redis Configuration

```bash
# Edit Redis configuration
sudo nano /etc/redis/redis.conf

# Add these settings:
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000

# Restart Redis
sudo systemctl restart redis-server
sudo systemctl enable redis-server
```

### 4. Application Deployment

```bash
# Switch to application user
sudo su - istanbulplus

# Clone repository
git clone https://github.com/your-org/istanbulplus.git
cd istanbulplus

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements/prod.txt

# Create environment file
cp .env.example .env
nano .env
```

### 5. Environment Configuration

Create `.env` file with production settings:

```bash
# Django Settings
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=istanbulplus.ir,www.istanbulplus.ir

# Database
DB_NAME=istanbulplus
DB_USER=istanbulplus
DB_PASSWORD=secure_password_here
DB_HOST=localhost
DB_PORT=5432

# Redis
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_RATE_LIMIT_URL=redis://127.0.0.1:6379/2

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=noreply@istanbulplus.ir
EMAIL_HOST_PASSWORD=your_email_password
DEFAULT_FROM_EMAIL=noreply@istanbulplus.ir

# Site Configuration
SITE_URL=https://istanbulplus.ir

# SMS Configuration
OTP_SMS_BACKEND=kavenegar
OTP_SMS_API_KEY=your_kavenegar_api_key

# Payment Gateway
PAYMENT_MERCHANT_ID=your_merchant_id

# Security
SECURITY_REPORT_EMAIL=admin@istanbulplus.ir
```

### 6. Database Migration

```bash
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Optimize database
python manage.py optimize_db --analyze
```

### 7. Gunicorn Configuration

Create `/home/istanbulplus/istanbulplus/gunicorn.conf.py`:

```python
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "istanbulplus"
group = "istanbulplus"
tmp_upload_dir = None
errorlog = "/var/log/gunicorn/error.log"
accesslog = "/var/log/gunicorn/access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
loglevel = "info"
```

### 8. Systemd Service

Create `/etc/systemd/system/istanbulplus.service`:

```ini
[Unit]
Description=Istanbul Plus E-commerce
After=network.target postgresql.service redis.service

[Service]
Type=exec
User=istanbulplus
Group=istanbulplus
WorkingDirectory=/home/istanbulplus/istanbulplus
Environment=PATH=/home/istanbulplus/istanbulplus/venv/bin
EnvironmentFile=/home/istanbulplus/istanbulplus/.env
ExecStart=/home/istanbulplus/istanbulplus/venv/bin/gunicorn istanbulplusir.wsgi:application -c gunicorn.conf.py
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

### 9. Nginx Configuration

Create `/etc/nginx/sites-available/istanbulplus`:

```nginx
upstream istanbulplus {
    server 127.0.0.1:8000;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name istanbulplus.ir www.istanbulplus.ir;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name istanbulplus.ir www.istanbulplus.ir;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/istanbulplus.ir/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/istanbulplus.ir/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; img-src 'self' data: https:; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self';" always;

    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    # Main location
    location / {
        proxy_pass http://istanbulplus;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://istanbulplus;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Auth endpoints with stricter rate limiting
    location /api/auth/ {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://istanbulplus;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /home/istanbulplus/istanbulplus/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    # Media files
    location /media/ {
        alias /home/istanbulplus/istanbulplus/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    # Security
    location ~ /\. {
        deny all;
    }

    location ~ ^/(\.env|\.git|requirements|scripts) {
        deny all;
    }
}
```

### 10. SSL Certificate

```bash
# Install SSL certificate
sudo certbot --nginx -d istanbulplus.ir -d www.istanbulplus.ir

# Test auto-renewal
sudo certbot renew --dry-run
```

### 11. Log Directory Setup

```bash
# Create log directories
sudo mkdir -p /var/log/django /var/log/gunicorn
sudo chown istanbulplus:istanbulplus /var/log/django /var/log/gunicorn

# Setup log rotation
sudo nano /etc/logrotate.d/istanbulplus
```

Add to logrotate configuration:

```
/var/log/django/*.log /var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 istanbulplus istanbulplus
    postrotate
        systemctl reload istanbulplus
    endscript
}
```

### 12. Cron Jobs Setup

```bash
# Edit crontab for istanbulplus user
sudo -u istanbulplus crontab -e

# Add these entries:
# Clean up expired data every hour
0 * * * * /home/istanbulplus/istanbulplus/venv/bin/python /home/istanbulplus/istanbulplus/manage.py cleanup_expired_data

# Optimize database daily at 2 AM
0 2 * * * /home/istanbulplus/istanbulplus/venv/bin/python /home/istanbulplus/istanbulplus/manage.py optimize_db --analyze

# Weekly database vacuum (Sundays at 3 AM)
0 3 * * 0 /home/istanbulplus/istanbulplus/venv/bin/python /home/istanbulplus/istanbulplus/manage.py optimize_db --vacuum --analyze

# Generate security reports weekly (Mondays at 9 AM)
0 9 * * 1 /home/istanbulplus/istanbulplus/venv/bin/python /home/istanbulplus/istanbulplus/manage.py generate_security_report
```

### 13. Start Services

```bash
# Enable and start services
sudo systemctl enable istanbulplus
sudo systemctl start istanbulplus

sudo systemctl enable nginx
sudo systemctl restart nginx

# Check status
sudo systemctl status istanbulplus
sudo systemctl status nginx
```

## Monitoring and Maintenance

### Health Checks

Create a simple health check endpoint and monitor it:

```bash
# Check application health
curl -f https://istanbulplus.ir/api/health/ || echo "Application down"

# Check database connection
sudo -u istanbulplus /home/istanbulplus/istanbulplus/venv/bin/python /home/istanbulplus/istanbulplus/manage.py check --database default

# Check Redis connection
redis-cli ping
```

### Backup Strategy

```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/istanbulplus"

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
pg_dump -h localhost -U istanbulplus istanbulplus | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
tar -czf $BACKUP_DIR/media_$DATE.tar.gz -C /home/istanbulplus/istanbulplus media/

# Keep only last 30 days of backups
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

### Performance Monitoring

Monitor these key metrics:

- Response times
- Error rates
- Database query performance
- Redis memory usage
- Failed authentication attempts
- Rate limit violations

### Security Checklist

- [ ] SSL certificate installed and auto-renewal configured
- [ ] Security headers properly configured
- [ ] Rate limiting enabled
- [ ] Database credentials secured
- [ ] Environment variables properly set
- [ ] Log files properly rotated
- [ ] Backup strategy implemented
- [ ] Monitoring alerts configured
- [ ] Firewall rules configured
- [ ] Regular security updates scheduled

## Troubleshooting

### Common Issues

1. **Application won't start**

   - Check logs: `sudo journalctl -u istanbulplus -f`
   - Verify environment variables
   - Check database connectivity

2. **High memory usage**

   - Monitor Redis memory usage
   - Check for memory leaks in application
   - Adjust Gunicorn worker count

3. **Slow response times**

   - Check database query performance
   - Monitor Redis cache hit rates
   - Review Nginx access logs

4. **Authentication issues**
   - Check OTP delivery (SMS/Email)
   - Verify rate limiting settings
   - Review security logs

### Log Locations

- Application logs: `/var/log/django/`
- Gunicorn logs: `/var/log/gunicorn/`
- Nginx logs: `/var/log/nginx/`
- System logs: `journalctl -u istanbulplus`

## Updates and Maintenance

### Application Updates

```bash
# Switch to application user
sudo su - istanbulplus
cd istanbulplus

# Backup current version
git tag backup-$(date +%Y%m%d)

# Pull updates
git pull origin main

# Update dependencies
source venv/bin/activate
pip install -r requirements/prod.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application
sudo systemctl restart istanbulplus
```

### Security Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Python packages
pip list --outdated
pip install -U package_name

# Check for security vulnerabilities
pip-audit
```

This deployment guide ensures a secure, scalable, and maintainable production environment for the Istanbul Plus E-commerce platform.

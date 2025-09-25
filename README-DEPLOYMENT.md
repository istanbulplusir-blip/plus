# 🚀 Istanbul Plus - Multi-Project Deployment

## 📋 Overview

This repository contains the complete deployment configuration for running **Istanbul Plus E-commerce** alongside the existing **peykan-tourism** project on a single server using Docker and Nginx.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Nginx Proxy                         │
│                    (Port 80/443)                           │
└─────────────────┬───────────────────┬───────────────────────┘
                  │                   │
                  ▼                   ▼
┌─────────────────────────┐ ┌─────────────────────────┐
│    Istanbul Plus        │ │    Peykan Tourism        │
│    (Port 8001)          │ │    (Port 8000)           │
│                         │ │                         │
│  ┌─────────────────┐    │ │  ┌─────────────────┐    │
│  │   Django App    │    │ │  │   Django App    │    │
│  │   + Celery      │    │ │  │   + Celery      │    │
│  └─────────────────┘    │ │  └─────────────────┘    │
│           │              │ │           │              │
│           ▼              │ │           ▼              │
│  ┌─────────────────┐    │ │  ┌─────────────────┐    │
│  │   PostgreSQL    │    │ │  │   PostgreSQL    │    │
│  │   (Port 5433)   │    │ │  │   (Port 5432)   │    │
│  └─────────────────┘    │ │  └─────────────────┘    │
└─────────────────────────┘ └─────────────────────────┘
                  │                   │
                  └─────────┬─────────┘
                            ▼
                  ┌─────────────────┐
                  │   Redis Cache   │
                  │   (Port 6379)   │
                  └─────────────────┘
```

## 🚀 Quick Start

### 1. Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM minimum
- 50GB SSD storage
- Domain names configured

### 2. Clone and Setup
```bash
git clone https://github.com/istanbulplusir-blip/plus.git
cd plus
cp env.example .env
nano .env  # Configure your settings
```

### 3. Deploy
```bash
chmod +x scripts/*.sh
./scripts/deploy.sh
```

## 📁 Project Structure

```
├── Dockerfile                 # Istanbul Plus container
├── docker-compose.yml         # Multi-project orchestration
├── env.example               # Environment template
├── DEPLOYMENT.md             # Detailed deployment guide
├── nginx/                    # Nginx configuration
│   ├── nginx.conf           # Main nginx config
│   ├── conf.d/              # Site configurations
│   │   ├── istanbulplus.conf
│   │   └── peykan.conf
│   └── ssl/                 # SSL certificates
├── scripts/                  # Deployment scripts
│   ├── deploy.sh            # Main deployment script
│   ├── backup.sh            # Backup script
│   ├── restore.sh           # Restore script
│   └── init-db.sql          # Database initialization
└── monitoring/              # Monitoring configuration
    └── prometheus.yml       # Prometheus config
```

## 🔧 Configuration

### Environment Variables
Key variables to configure in `.env`:

```bash
# Django Settings
SECRET_KEY=your_very_secure_secret_key
DEBUG=False
ALLOWED_HOSTS=istanbulplus.ir,www.istanbulplus.ir

# Database
DB_PASSWORD=your_secure_database_password
PEYKAN_DB_PASSWORD=your_peykan_database_password

# Email & SMS
EMAIL_HOST_USER=noreply@istanbulplus.ir
EMAIL_HOST_PASSWORD=your_email_password
OTP_SMS_API_KEY=your_kavenegar_api_key

# Payment
PAYMENT_MERCHANT_ID=your_merchant_id
```

### Domain Configuration
- **Istanbul Plus**: `istanbulplus.ir`, `www.istanbulplus.ir`
- **Peykan Tourism**: `peykan-tourism.ir`, `www.peykan-tourism.ir`

## 🐳 Docker Services

### Istanbul Plus Services
- **istanbulplus-web**: Django application (Port 8001)
- **istanbulplus-db**: PostgreSQL database (Port 5433)
- **istanbulplus-celery**: Background tasks

### Peykan Tourism Services
- **peykan-web**: Django application (Port 8000)
- **peykan-db**: PostgreSQL database (Port 5432)

### Shared Services
- **nginx**: Reverse proxy (Port 80/443)
- **redis**: Cache and sessions (Port 6379)
- **prometheus**: Monitoring (Port 9090)
- **grafana**: Dashboards (Port 3000)

## 📊 Monitoring

### Available Dashboards
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application Health**: https://istanbulplus.ir/health/

### Key Metrics
- Response times and error rates
- Database performance
- Redis memory usage
- Failed authentication attempts
- System resource usage

## 💾 Backup & Restore

### Automated Backup
```bash
# Create backup
./scripts/backup.sh

# List backups
./scripts/restore.sh --list

# Restore from backup
./scripts/restore.sh --date 20240101_120000
```

### Backup Contents
- Database dump (PostgreSQL)
- Media files (user uploads)
- Static files (CSS, JS, images)
- Configuration files

## 🔒 Security Features

### SSL/TLS
- Automatic HTTP to HTTPS redirect
- TLS 1.2+ only
- HSTS headers
- Secure cipher suites

### Rate Limiting
- API endpoints: 10 requests/second
- Authentication: 5 requests/second
- General traffic: 20 requests/second

### Security Headers
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Content-Security-Policy
- Strict-Transport-Security

## 🛠️ Management Commands

### Service Management
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart istanbulplus-web

# View logs
docker-compose logs -f istanbulplus-web
```

### Database Management
```bash
# Run migrations
docker-compose exec istanbulplus-web python manage.py migrate

# Create superuser
docker-compose exec istanbulplus-web python manage.py createsuperuser

# Optimize database
docker-compose exec istanbulplus-web python manage.py optimize_db --analyze
```

### Maintenance Tasks
```bash
# Clean up expired data
docker-compose exec istanbulplus-web python manage.py cleanup_expired_data

# Collect static files
docker-compose exec istanbulplus-web python manage.py collectstatic --noinput

# Update application
git pull && docker-compose build && docker-compose up -d
```

## 🚨 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory
free -h
```

#### Database Connection Issues
```bash
# Test database connection
docker-compose exec istanbulplus-web python manage.py check --database default

# Check database status
docker-compose exec istanbulplus-db pg_isready -U istanbulplus_user
```

#### SSL Certificate Issues
```bash
# Renew certificates
sudo certbot renew

# Check certificate
openssl x509 -in nginx/ssl/istanbulplus.ir.crt -text -noout
```

### Log Locations
- **Application**: `docker-compose logs istanbulplus-web`
- **Nginx**: `docker-compose logs nginx`
- **Database**: `docker-compose logs istanbulplus-db`
- **System**: `/var/log/syslog`

## 📈 Performance Optimization

### Nginx Optimization
- Gzip compression enabled
- Static file caching (1 year)
- Media file caching (1 month)
- HTTP/2 support

### Database Optimization
- Regular VACUUM and ANALYZE
- Proper indexing
- Connection pooling
- Query optimization

### Redis Optimization
- Memory limit: 512MB
- Eviction policy: allkeys-lru
- Persistence enabled
- Multiple databases for isolation

## 🔄 Updates and Maintenance

### Update Procedure
1. **Backup**: Create backup before update
2. **Test**: Test in staging environment
3. **Deploy**: Deploy during maintenance window
4. **Monitor**: Monitor after deployment
5. **Rollback**: Have rollback plan ready

### Regular Maintenance
- **Daily**: Monitor logs and performance
- **Weekly**: Database optimization
- **Monthly**: Security updates
- **Quarterly**: Full system review

## 📞 Support

### Documentation
- **Deployment Guide**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **API Documentation**: https://istanbulplus.ir/api/docs/
- **User Guide**: https://docs.istanbulplus.ir

### Contact
- **Technical Support**: support@istanbulplus.ir
- **GitHub Issues**: https://github.com/istanbulplusir-blip/plus/issues
- **Documentation**: https://docs.istanbulplus.ir

## 📄 License

This project is proprietary software. All rights reserved.

---

**⚠️ Important**: This deployment configuration is designed for production use. Make sure to:
1. Configure proper SSL certificates
2. Set strong passwords
3. Enable monitoring
4. Set up regular backups
5. Test thoroughly before going live

**🚀 Ready to deploy?** Start with the [Quick Start](#-quick-start) section above!

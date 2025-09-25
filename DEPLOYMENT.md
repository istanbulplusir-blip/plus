# Istanbul Plus Deployment Guide

## Overview

This guide covers the deployment of Istanbul Plus E-commerce platform alongside the existing peykan-tourism project using Docker and Nginx.

## Prerequisites

### System Requirements
- Ubuntu 20.04+ or CentOS 8+
- Docker 20.10+
- Docker Compose 2.0+
- 8GB RAM (minimum 4GB)
- 50GB SSD storage
- 1Gbps network connection

### Required Services
- Domain names configured
- SSL certificates (Let's Encrypt recommended)
- SMTP server for email delivery
- SMS gateway (Kavenegar)

## Quick Start

### 1. Clone and Setup
```bash
# Clone the repository
git clone https://github.com/istanbulplusir-blip/plus.git
cd plus

# Copy environment file
cp env.example .env

# Edit environment variables
nano .env
```

### 2. Configure Environment
Edit `.env` file with your actual values:
```bash
# Django Settings
SECRET_KEY=your_very_secure_secret_key_here
DEBUG=False
ALLOWED_HOSTS=istanbulplus.ir,www.istanbulplus.ir

# Database
DB_PASSWORD=your_secure_database_password
PEYKAN_DB_PASSWORD=your_peykan_database_password

# Email
EMAIL_HOST_USER=noreply@istanbulplus.ir
EMAIL_HOST_PASSWORD=your_email_password

# SMS
OTP_SMS_API_KEY=your_kavenegar_api_key

# Payment
PAYMENT_MERCHANT_ID=your_merchant_id
```

### 3. Deploy
```bash
# Make scripts executable
chmod +x scripts/*.sh

# Run deployment script
./scripts/deploy.sh
```

## Manual Deployment

### 1. System Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. SSL Certificates
```bash
# Install Certbot
sudo apt install certbot

# Generate certificates
sudo certbot certonly --standalone -d istanbulplus.ir -d www.istanbulplus.ir
sudo certbot certonly --standalone -d peykan-tourism.ir -d www.peykan-tourism.ir

# Copy certificates to nginx directory
sudo cp /etc/letsencrypt/live/istanbulplus.ir/fullchain.pem nginx/ssl/istanbulplus.ir.crt
sudo cp /etc/letsencrypt/live/istanbulplus.ir/privkey.pem nginx/ssl/istanbulplus.ir.key
sudo cp /etc/letsencrypt/live/peykan-tourism.ir/fullchain.pem nginx/ssl/peykan-tourism.ir.crt
sudo cp /etc/letsencrypt/live/peykan-tourism.ir/privkey.pem nginx/ssl/peykan-tourism.ir.key
```

### 3. Start Services
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

## Service Architecture

### Container Layout
```
┌─────────────────┐    ┌─────────────────┐
│   Nginx Proxy   │    │   Nginx Proxy   │
│   Port: 80/443  │    │   Port: 80/443  │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ Istanbul Plus   │    │ Peykan Tourism  │
│ Port: 8001      │    │ Port: 8000      │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│ PostgreSQL DB   │    │ PostgreSQL DB   │
│ Port: 5433      │    │ Port: 5432      │
└─────────────────┘    └─────────────────┘
          │                      │
          └──────────┬───────────┘
                     ▼
            ┌─────────────────┐
            │   Redis Cache   │
            │   Port: 6379    │
            └─────────────────┘
```

### Network Configuration
- **istanbulplus_network**: Isolated network for Istanbul Plus services
- **peykan_network**: Isolated network for Peykan Tourism services
- **shared_network**: Shared network for Nginx and Redis
- **monitoring_network**: Network for monitoring services

## Database Configuration

### Istanbul Plus Database
- **Database**: istanbulplus_db
- **User**: istanbulplus_user
- **Port**: 5433
- **Redis DB**: 3-4

### Peykan Tourism Database
- **Database**: peykan_db
- **User**: peykan_user
- **Port**: 5432
- **Redis DB**: 0-2

## Monitoring and Logging

### Available Services
- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **Application Logs**: `docker-compose logs -f`

### Key Metrics
- Response times
- Error rates
- Database performance
- Redis memory usage
- Failed authentication attempts

## Backup and Restore

### Automated Backup
```bash
# Run backup script
./scripts/backup.sh

# List available backups
./scripts/restore.sh --list

# Restore from specific backup
./scripts/restore.sh --date 20240101_120000
```

### Manual Backup
```bash
# Database backup
docker-compose exec -T istanbulplus-db pg_dump -U istanbulplus_user istanbulplus_db | gzip > backup_$(date +%Y%m%d_%H%M%S).sql.gz

# Media files backup
docker run --rm -v istanbulplus_media:/data -v $(pwd):/backup alpine tar -czf /backup/media_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

## Maintenance

### Regular Tasks
```bash
# Update application
git pull origin main
docker-compose build
docker-compose up -d

# Clean up old containers
docker system prune -f

# Optimize database
docker-compose exec istanbulplus-web python manage.py optimize_db --analyze

# Clean up expired data
docker-compose exec istanbulplus-web python manage.py cleanup_expired_data
```

### Health Checks
```bash
# Check application health
curl -f https://istanbulplus.ir/health/

# Check database connection
docker-compose exec istanbulplus-web python manage.py check --database default

# Check Redis connection
docker-compose exec redis redis-cli ping
```

## Troubleshooting

### Common Issues

#### 1. Services Won't Start
```bash
# Check logs
docker-compose logs

# Check disk space
df -h

# Check memory usage
free -h
```

#### 2. Database Connection Issues
```bash
# Check database status
docker-compose exec istanbulplus-db pg_isready -U istanbulplus_user

# Check network connectivity
docker-compose exec istanbulplus-web ping istanbulplus-db
```

#### 3. SSL Certificate Issues
```bash
# Renew certificates
sudo certbot renew

# Check certificate validity
openssl x509 -in nginx/ssl/istanbulplus.ir.crt -text -noout
```

#### 4. High Memory Usage
```bash
# Check Redis memory
docker-compose exec redis redis-cli info memory

# Check container resource usage
docker stats
```

### Log Locations
- **Application logs**: `docker-compose logs istanbulplus-web`
- **Nginx logs**: `docker-compose logs nginx`
- **Database logs**: `docker-compose logs istanbulplus-db`
- **System logs**: `/var/log/syslog`

## Security Considerations

### Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### SSL/TLS Configuration
- Use TLS 1.2+ only
- Enable HSTS
- Configure proper cipher suites
- Regular certificate renewal

### Database Security
- Use strong passwords
- Limit network access
- Regular security updates
- Enable SSL connections

## Performance Optimization

### Nginx Optimization
- Enable gzip compression
- Configure caching headers
- Use HTTP/2
- Optimize worker processes

### Database Optimization
- Regular VACUUM and ANALYZE
- Proper indexing
- Connection pooling
- Query optimization

### Redis Optimization
- Memory limit configuration
- Eviction policies
- Persistence settings
- Monitoring memory usage

## Scaling Considerations

### Horizontal Scaling
- Load balancer configuration
- Database replication
- Redis clustering
- CDN integration

### Vertical Scaling
- Increase container resources
- Optimize database settings
- Add more Redis memory
- Upgrade server hardware

## Support and Maintenance

### Monitoring Setup
1. Configure Prometheus alerts
2. Set up Grafana dashboards
3. Configure log aggregation
4. Set up uptime monitoring

### Backup Strategy
1. Daily automated backups
2. Weekly full system backups
3. Monthly backup testing
4. Off-site backup storage

### Update Procedure
1. Test updates in staging
2. Create backup before update
3. Deploy during maintenance window
4. Monitor after deployment
5. Rollback plan ready

## Contact Information

- **Technical Support**: support@istanbulplus.ir
- **Documentation**: https://docs.istanbulplus.ir
- **GitHub Repository**: https://github.com/istanbulplusir-blip/plus

---

**Note**: This deployment guide assumes you have basic knowledge of Docker, Nginx, and Linux system administration. For production deployments, consider consulting with a DevOps engineer.

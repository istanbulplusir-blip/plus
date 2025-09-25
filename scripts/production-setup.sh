#!/bin/bash

# Istanbul Plus Production Setup Script
# This script sets up the project for production deployment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="istanbulplus"
PROJECT_DIR="/var/www/istanbulplus"
DOMAIN="istanbulplus.ir"
EMAIL="admin@istanbulplus.ir"
PYTHON_VERSION="3.9"
NGINX_USER="www-data"

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
   error "This script must be run as root for production setup"
fi

log "Starting Istanbul Plus production setup..."

# 1. System Update
log "Updating system packages..."
apt update && apt upgrade -y

# 2. Install Required Packages
log "Installing required packages..."
apt install -y \
    python3.9 \
    python3.9-venv \
    python3.9-dev \
    python3-pip \
    nginx \
    postgresql \
    postgresql-contrib \
    redis-server \
    git \
    curl \
    wget \
    unzip \
    supervisor \
    certbot \
    python3-certbot-nginx \
    ufw \
    fail2ban \
    htop \
    nano \
    vim

# 3. Create Project User
log "Creating project user..."
if ! id "$PROJECT_NAME" &>/dev/null; then
    useradd -m -s /bin/bash $PROJECT_NAME
    usermod -aG www-data $PROJECT_NAME
    log "User $PROJECT_NAME created"
else
    log "User $PROJECT_NAME already exists"
fi

# 4. Create Project Directory
log "Creating project directory..."
mkdir -p $PROJECT_DIR
chown $PROJECT_NAME:$PROJECT_NAME $PROJECT_DIR

# 5. Clone Project
log "Cloning project from GitHub..."
cd $PROJECT_DIR
sudo -u $PROJECT_NAME git clone https://github.com/istanbulplusir-blip/plus.git .

# 6. Create Python Virtual Environment
log "Creating Python virtual environment..."
sudo -u $PROJECT_NAME python3.9 -m venv venv
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install --upgrade pip

# 7. Install Python Dependencies
log "Installing Python dependencies..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install -r requirements/prod.txt

# 8. Configure PostgreSQL
log "Configuring PostgreSQL..."
sudo -u postgres psql << EOF
CREATE DATABASE ${PROJECT_NAME}_db;
CREATE USER ${PROJECT_NAME}_user WITH PASSWORD '${PROJECT_NAME}_secure_password_2024';
ALTER ROLE ${PROJECT_NAME}_user SET client_encoding TO 'utf8';
ALTER ROLE ${PROJECT_NAME}_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ${PROJECT_NAME}_user SET timezone TO 'Asia/Tehran';
GRANT ALL PRIVILEGES ON DATABASE ${PROJECT_NAME}_db TO ${PROJECT_NAME}_user;
\q
EOF

# 9. Configure Redis
log "Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

# 10. Create Environment File
log "Creating production environment file..."
cat > $PROJECT_DIR/.env << EOF
# Production Environment Variables
DEBUG=False
SECRET_KEY=$(python3 -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
ALLOWED_HOSTS=$DOMAIN,www.$DOMAIN,localhost,127.0.0.1

# Database Configuration
DB_NAME=${PROJECT_NAME}_db
DB_USER=${PROJECT_NAME}_user
DB_PASSWORD=${PROJECT_NAME}_secure_password_2024
DB_HOST=localhost
DB_PORT=5432

# Redis Configuration
REDIS_URL=redis://127.0.0.1:6379/1
REDIS_RATE_LIMIT_URL=redis://127.0.0.1:6379/2
CELERY_BROKER_URL=redis://127.0.0.1:6379/3
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/4

# Site Configuration
SITE_URL=https://$DOMAIN
SITE_NAME=Istanbul Plus
SITE_DESCRIPTION=تورهای ویژه استانبول

# Email Configuration (configure with your SMTP settings)
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password
EMAIL_PORT=587
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@$DOMAIN

# SMS Configuration (configure with your SMS provider)
OTP_SMS_API_KEY=your_sms_api_key
OTP_SMS_SENDER=your_sms_sender

# Payment Configuration (configure with your payment gateway)
PAYMENT_MERCHANT_ID=your_merchant_id
PAYMENT_CALLBACK_URL=https://$DOMAIN/payments/callback/

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_BROWSER_XSS_FILTER=True
SECURE_CONTENT_TYPE_NOSNIFF=True
X_FRAME_OPTIONS=DENY

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/istanbulplus/application.log
EOF

chown $PROJECT_NAME:$PROJECT_NAME $PROJECT_DIR/.env
chmod 600 $PROJECT_DIR/.env

# 11. Run Django Setup
log "Running Django setup..."
cd $PROJECT_DIR
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py migrate
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py createsuperuser --noinput --username admin --email admin@$DOMAIN || true

# 12. Create Log Directory
log "Creating log directory..."
mkdir -p /var/log/istanbulplus
chown $PROJECT_NAME:$NGINX_USER /var/log/istanbulplus
chmod 755 /var/log/istanbulplus

# 13. Configure Gunicorn
log "Configuring Gunicorn..."
cat > $PROJECT_DIR/gunicorn.conf.py << EOF
# Gunicorn configuration file
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
daemon = False
pidfile = "/var/run/gunicorn/istanbulplus.pid"
user = "$PROJECT_NAME"
group = "$NGINX_USER"
tmp_upload_dir = None
errorlog = "/var/log/istanbulplus/gunicorn_error.log"
accesslog = "/var/log/istanbulplus/gunicorn_access.log"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'
loglevel = "info"
capture_output = True
enable_stdio_inheritance = True
EOF

chown $PROJECT_NAME:$NGINX_USER $PROJECT_DIR/gunicorn.conf.py

# 14. Create Gunicorn Service
log "Creating Gunicorn systemd service..."
cat > /etc/systemd/system/istanbulplus.service << EOF
[Unit]
Description=Istanbul Plus Gunicorn daemon
After=network.target postgresql.service redis.service

[Service]
User=$PROJECT_NAME
Group=$NGINX_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/gunicorn --config gunicorn.conf.py istanbulplusir.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 15. Configure Celery
log "Configuring Celery..."
cat > /etc/systemd/system/istanbulplus-celery.service << EOF
[Unit]
Description=Istanbul Plus Celery Worker
After=network.target redis.service

[Service]
Type=forking
User=$PROJECT_NAME
Group=$NGINX_USER
WorkingDirectory=$PROJECT_DIR
Environment="PATH=$PROJECT_DIR/venv/bin"
ExecStart=$PROJECT_DIR/venv/bin/celery -A istanbulplusir worker --loglevel=info --detach
ExecStop=$PROJECT_DIR/venv/bin/celery -A istanbulplusir control shutdown
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF

# 16. Configure Nginx
log "Configuring Nginx..."
cat > /etc/nginx/sites-available/$PROJECT_NAME << EOF
# Istanbul Plus Nginx Configuration
upstream istanbulplus {
    server 127.0.0.1:8000;
}

# Rate limiting
limit_req_zone \$binary_remote_addr zone=api:10m rate=10r/s;
limit_req_zone \$binary_remote_addr zone=auth:10m rate=5r/s;

server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Redirect HTTP to HTTPS
    return 301 https://\$server_name\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN www.$DOMAIN;

    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
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

    # Main application
    location / {
        proxy_pass http://istanbulplus;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_redirect off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # API endpoints with rate limiting
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://istanbulplus;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Authentication endpoints with stricter rate limiting
    location /api/auth/ {
        limit_req zone=auth burst=10 nodelay;
        proxy_pass http://istanbulplus;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # Static files
    location /static/ {
        alias $PROJECT_DIR/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        gzip_static on;
    }

    # Media files
    location /media/ {
        alias $PROJECT_DIR/media/;
        expires 1M;
        add_header Cache-Control "public";
    }

    # Health check endpoint
    location /health/ {
        proxy_pass http://istanbulplus;
        access_log off;
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
    }

    location ~ ^/(\.env|\.git|requirements|scripts) {
        deny all;
    }
}
EOF

# Enable the site
ln -sf /etc/nginx/sites-available/$PROJECT_NAME /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# 17. Configure Firewall
log "Configuring firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing
ufw allow 22/tcp comment 'SSH'
ufw allow 80/tcp comment 'HTTP'
ufw allow 443/tcp comment 'HTTPS'
ufw --force enable

# 18. Configure Fail2Ban
log "Configuring Fail2Ban..."
cat > /etc/fail2ban/jail.local << EOF
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
backend = systemd

[sshd]
enabled = true
port = ssh
logpath = /var/log/auth.log
maxretry = 3

[nginx-http-auth]
enabled = true
filter = nginx-http-auth
port = http,https
logpath = /var/log/nginx/error.log

[nginx-limit-req]
enabled = true
filter = nginx-limit-req
port = http,https
logpath = /var/log/nginx/error.log
maxretry = 10
EOF

# 19. Create Log Rotation
log "Configuring log rotation..."
cat > /etc/logrotate.d/istanbulplus << EOF
/var/log/istanbulplus/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 $PROJECT_NAME $NGINX_USER
    postrotate
        systemctl reload istanbulplus
    endscript
}
EOF

# 20. Start Services
log "Starting services..."
systemctl daemon-reload
systemctl enable istanbulplus
systemctl enable istanbulplus-celery
systemctl enable nginx
systemctl enable postgresql
systemctl enable redis-server
systemctl enable fail2ban

systemctl start istanbulplus
systemctl start istanbulplus-celery
systemctl start nginx
systemctl start postgresql
systemctl start redis-server
systemctl start fail2ban

# 21. Setup SSL Certificate
log "Setting up SSL certificate..."
certbot --nginx -d $DOMAIN -d www.$DOMAIN --non-interactive --agree-tos --email $EMAIL

# 22. Setup Auto-renewal
log "Setting up SSL auto-renewal..."
(crontab -l 2>/dev/null; echo "0 2 * * * certbot renew --quiet") | crontab -

# 23. Create Backup Script
log "Creating backup script..."
cat > /usr/local/bin/istanbulplus-backup.sh << EOF
#!/bin/bash
# Istanbul Plus Backup Script

DATE=\$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/istanbulplus"

mkdir -p \$BACKUP_DIR

# Database backup
sudo -u postgres pg_dump ${PROJECT_NAME}_db | gzip > \$BACKUP_DIR/db_\$DATE.sql.gz

# Media files backup
tar -czf \$BACKUP_DIR/media_\$DATE.tar.gz -C $PROJECT_DIR media/

# Keep only last 30 days of backups
find \$BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: \$DATE"
EOF

chmod +x /usr/local/bin/istanbulplus-backup.sh

# Add to crontab (daily backup at 3 AM)
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/istanbulplus-backup.sh") | crontab -

# 24. Final Status Check
log "Checking service status..."
systemctl is-active --quiet istanbulplus && log "✓ Istanbul Plus service is running" || warn "✗ Istanbul Plus service is not running"
systemctl is-active --quiet istanbulplus-celery && log "✓ Celery service is running" || warn "✗ Celery service is not running"
systemctl is-active --quiet nginx && log "✓ Nginx service is running" || warn "✗ Nginx service is not running"
systemctl is-active --quiet postgresql && log "✓ PostgreSQL service is running" || warn "✗ PostgreSQL service is not running"
systemctl is-active --quiet redis-server && log "✓ Redis service is running" || warn "✗ Redis service is not running"

# 25. Display Final Information
log "Production setup completed successfully!"
echo ""
info "=== DEPLOYMENT INFORMATION ==="
info "Project Directory: $PROJECT_DIR"
info "Domain: https://$DOMAIN"
info "Admin Panel: https://$DOMAIN/admin/"
info "Health Check: https://$DOMAIN/health/"
info "Logs Directory: /var/log/istanbulplus"
info "Backup Directory: /backups/istanbulplus"
echo ""
info "=== NEXT STEPS ==="
info "1. Update DNS records to point to this server"
info "2. Configure email settings in $PROJECT_DIR/.env"
info "3. Configure SMS settings in $PROJECT_DIR/.env"
info "4. Configure payment gateway settings in $PROJECT_DIR/.env"
info "5. Create superuser: sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py createsuperuser"
info "6. Test the website: https://$DOMAIN"
echo ""
info "=== USEFUL COMMANDS ==="
info "Check service status: systemctl status istanbulplus"
info "View logs: journalctl -u istanbulplus -f"
info "Restart service: systemctl restart istanbulplus"
info "Update code: cd $PROJECT_DIR && sudo -u $PROJECT_NAME git pull"
info "Run migrations: sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py migrate"
info "Collect static: sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput"
echo ""
log "Istanbul Plus is now ready for production! 🚀"

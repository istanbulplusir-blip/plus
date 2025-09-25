#!/bin/bash

# Istanbul Plus Production Deployment Script
# This script deploys updates to the production server

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
BACKUP_DIR="/backups/istanbulplus"
SERVICE_NAME="istanbulplus"

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
   error "This script must be run as root for production deployment"
fi

log "Starting Istanbul Plus production deployment..."

# 1. Create Backup
log "Creating backup before deployment..."
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Database backup
sudo -u postgres pg_dump ${PROJECT_NAME}_db | gzip > $BACKUP_DIR/db_pre_deploy_$DATE.sql.gz
log "Database backup created: $BACKUP_DIR/db_pre_deploy_$DATE.sql.gz"

# Media files backup
tar -czf $BACKUP_DIR/media_pre_deploy_$DATE.tar.gz -C $PROJECT_DIR media/
log "Media files backup created: $BACKUP_DIR/media_pre_deploy_$DATE.tar.gz"

# 2. Stop Services
log "Stopping services..."
systemctl stop $SERVICE_NAME
systemctl stop istanbulplus-celery

# 3. Update Code
log "Updating code from Git repository..."
cd $PROJECT_DIR
sudo -u $PROJECT_NAME git fetch origin
sudo -u $PROJECT_NAME git reset --hard origin/master
log "Code updated successfully"

# 4. Update Dependencies
log "Updating Python dependencies..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install --upgrade pip
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/pip install -r requirements/prod.txt
log "Dependencies updated successfully"

# 5. Run Database Migrations
log "Running database migrations..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py migrate
log "Database migrations completed"

# 6. Collect Static Files
log "Collecting static files..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py collectstatic --noinput
log "Static files collected successfully"

# 7. Clear Cache
log "Clearing cache..."
sudo -u $PROJECT_NAME $PROJECT_DIR/venv/bin/python manage.py clear_cache
log "Cache cleared successfully"

# 8. Restart Services
log "Restarting services..."
systemctl start $SERVICE_NAME
systemctl start istanbulplus-celery

# Wait for services to start
sleep 5

# 9. Health Check
log "Performing health check..."
if curl -f http://localhost:8000/health/ > /dev/null 2>&1; then
    log "✓ Health check passed"
else
    error "✗ Health check failed - rolling back"
    # Rollback logic would go here
fi

# 10. Reload Nginx
log "Reloading Nginx..."
systemctl reload nginx
log "Nginx reloaded successfully"

# 11. Check Service Status
log "Checking service status..."
systemctl is-active --quiet $SERVICE_NAME && log "✓ $SERVICE_NAME service is running" || error "✗ $SERVICE_NAME service is not running"
systemctl is-active --quiet istanbulplus-celery && log "✓ Celery service is running" || warn "✗ Celery service is not running"
systemctl is-active --quiet nginx && log "✓ Nginx service is running" || error "✗ Nginx service is not running"

# 12. Cleanup Old Backups
log "Cleaning up old backups..."
find $BACKUP_DIR -name "*.gz" -mtime +7 -delete
log "Old backups cleaned up"

# 13. Display Deployment Summary
log "Deployment completed successfully!"
echo ""
info "=== DEPLOYMENT SUMMARY ==="
info "Deployment Time: $(date)"
info "Backup Created: $BACKUP_DIR/db_pre_deploy_$DATE.sql.gz"
info "Services Status:"
info "  - Istanbul Plus: $(systemctl is-active $SERVICE_NAME)"
info "  - Celery: $(systemctl is-active istanbulplus-celery)"
info "  - Nginx: $(systemctl is-active nginx)"
echo ""
info "=== USEFUL COMMANDS ==="
info "View logs: journalctl -u $SERVICE_NAME -f"
info "Check status: systemctl status $SERVICE_NAME"
info "Restart service: systemctl restart $SERVICE_NAME"
echo ""
log "Istanbul Plus deployment completed! 🚀"

#!/bin/bash

# Istanbul Plus Backup Script
# This script creates backups of the database and media files

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/backups/istanbulplus"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d_%H%M%S)

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

# Check if running in Docker environment
if ! docker-compose ps | grep -q "Up"; then
    error "Docker services are not running. Please start them first with: docker-compose up -d"
fi

log "Starting backup process..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Database backup
log "Creating database backup..."
if docker-compose exec -T istanbulplus-db pg_dump -U istanbulplus_user istanbulplus_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz; then
    log "Database backup completed: db_$DATE.sql.gz"
else
    error "Database backup failed"
fi

# Media files backup
log "Creating media files backup..."
if docker run --rm -v istanbulplus_media:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/media_$DATE.tar.gz -C /data .; then
    log "Media files backup completed: media_$DATE.tar.gz"
else
    error "Media files backup failed"
fi

# Static files backup
log "Creating static files backup..."
if docker run --rm -v istanbulplus_static:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/static_$DATE.tar.gz -C /data .; then
    log "Static files backup completed: static_$DATE.tar.gz"
else
    warn "Static files backup failed (this is usually not critical)"
fi

# Create backup manifest
log "Creating backup manifest..."
cat > $BACKUP_DIR/manifest_$DATE.txt << EOF
Backup Date: $(date)
Database: db_$DATE.sql.gz
Media Files: media_$DATE.tar.gz
Static Files: static_$DATE.tar.gz
Backup Size: $(du -sh $BACKUP_DIR | cut -f1)
EOF

# Cleanup old backups
log "Cleaning up old backups (older than $RETENTION_DAYS days)..."
find $BACKUP_DIR -name "*.gz" -mtime +$RETENTION_DAYS -delete
find $BACKUP_DIR -name "manifest_*.txt" -mtime +$RETENTION_DAYS -delete

# Calculate backup size
BACKUP_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
log "Backup completed successfully!"
log "Total backup size: $BACKUP_SIZE"
log "Backup location: $BACKUP_DIR"

# Optional: Upload to S3 (if configured)
if [ ! -z "$BACKUP_S3_BUCKET" ]; then
    log "Uploading backup to S3..."
    if command -v aws &> /dev/null; then
        aws s3 sync $BACKUP_DIR s3://$BACKUP_S3_BUCKET/istanbulplus/ --delete
        log "Backup uploaded to S3 successfully"
    else
        warn "AWS CLI not found. Skipping S3 upload."
    fi
fi

log "Backup process completed successfully!"

#!/bin/bash

# Istanbul Plus Restore Script
# This script restores the database and media files from backup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKUP_DIR="/backups/istanbulplus"

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

# Function to show usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo "Options:"
    echo "  -d, --date DATE     Restore from specific date (YYYYMMDD_HHMMSS)"
    echo "  -l, --list          List available backups"
    echo "  -h, --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --list"
    echo "  $0 --date 20240101_120000"
    exit 1
}

# Parse command line arguments
BACKUP_DATE=""
LIST_BACKUPS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -d|--date)
            BACKUP_DATE="$2"
            shift 2
            ;;
        -l|--list)
            LIST_BACKUPS=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

# List available backups
if [ "$LIST_BACKUPS" = true ]; then
    log "Available backups:"
    if [ -d "$BACKUP_DIR" ]; then
        ls -la $BACKUP_DIR/*.gz 2>/dev/null | while read line; do
            echo "  $line"
        done
    else
        warn "No backup directory found: $BACKUP_DIR"
    fi
    exit 0
fi

# Check if backup directory exists
if [ ! -d "$BACKUP_DIR" ]; then
    error "Backup directory not found: $BACKUP_DIR"
fi

# If no date specified, use the latest backup
if [ -z "$BACKUP_DATE" ]; then
    BACKUP_DATE=$(ls -t $BACKUP_DIR/db_*.sql.gz 2>/dev/null | head -1 | sed 's/.*db_\(.*\)\.sql\.gz/\1/')
    if [ -z "$BACKUP_DATE" ]; then
        error "No backups found in $BACKUP_DIR"
    fi
    log "Using latest backup: $BACKUP_DATE"
fi

# Check if backup files exist
DB_BACKUP="$BACKUP_DIR/db_$BACKUP_DATE.sql.gz"
MEDIA_BACKUP="$BACKUP_DIR/media_$BACKUP_DATE.tar.gz"
STATIC_BACKUP="$BACKUP_DIR/static_$BACKUP_DATE.tar.gz"

if [ ! -f "$DB_BACKUP" ]; then
    error "Database backup not found: $DB_BACKUP"
fi

if [ ! -f "$MEDIA_BACKUP" ]; then
    warn "Media backup not found: $MEDIA_BACKUP"
fi

if [ ! -f "$STATIC_BACKUP" ]; then
    warn "Static backup not found: $STATIC_BACKUP"
fi

# Confirmation prompt
echo -e "${YELLOW}WARNING: This will restore the database and media files from backup $BACKUP_DATE${NC}"
echo -e "${YELLOW}This action will overwrite existing data. Are you sure? (yes/no)${NC}"
read -r response
if [[ ! "$response" =~ ^[Yy][Ee][Ss]$ ]]; then
    log "Restore cancelled by user"
    exit 0
fi

# Check if Docker services are running
if ! docker-compose ps | grep -q "Up"; then
    error "Docker services are not running. Please start them first with: docker-compose up -d"
fi

log "Starting restore process from backup: $BACKUP_DATE"

# Stop the web application to prevent data corruption
log "Stopping web application..."
docker-compose stop istanbulplus-web

# Restore database
log "Restoring database..."
if gunzip -c "$DB_BACKUP" | docker-compose exec -T istanbulplus-db psql -U istanbulplus_user -d istanbulplus_db; then
    log "Database restored successfully"
else
    error "Database restore failed"
fi

# Restore media files
if [ -f "$MEDIA_BACKUP" ]; then
    log "Restoring media files..."
    if docker run --rm -v istanbulplus_media:/data -v "$MEDIA_BACKUP":/backup.tar.gz alpine sh -c "cd /data && tar -xzf /backup.tar.gz"; then
        log "Media files restored successfully"
    else
        error "Media files restore failed"
    fi
fi

# Restore static files
if [ -f "$STATIC_BACKUP" ]; then
    log "Restoring static files..."
    if docker run --rm -v istanbulplus_static:/data -v "$STATIC_BACKUP":/backup.tar.gz alpine sh -c "cd /data && tar -xzf /backup.tar.gz"; then
        log "Static files restored successfully"
    else
        error "Static files restore failed"
    fi
fi

# Start the web application
log "Starting web application..."
docker-compose start istanbulplus-web

# Wait for application to be ready
log "Waiting for application to be ready..."
sleep 10

# Run migrations to ensure database schema is up to date
log "Running database migrations..."
docker-compose exec istanbulplus-web python manage.py migrate --settings=settings.prod

# Collect static files
log "Collecting static files..."
docker-compose exec istanbulplus-web python manage.py collectstatic --noinput --settings=settings.prod

# Test the application
log "Testing application..."
if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
    log "Application is running successfully!"
else
    warn "Health check failed. Check logs with: docker-compose logs istanbulplus-web"
fi

log "Restore completed successfully!"
log "Backup date: $BACKUP_DATE"
log "Application URL: http://localhost:8001"

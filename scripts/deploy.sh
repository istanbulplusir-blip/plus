#!/bin/bash

# Istanbul Plus Deployment Script
# This script deploys the Istanbul Plus project alongside existing peykan-tourism

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   error "This script should not be run as root for security reasons"
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    error "Docker is not installed. Please install Docker first."
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    error "Docker Compose is not installed. Please install Docker Compose first."
fi

# Check if .env file exists
if [ ! -f .env ]; then
    error ".env file not found. Please copy env.example to .env and configure it."
fi

log "Starting Istanbul Plus deployment..."

# Create necessary directories
log "Creating necessary directories..."
mkdir -p nginx/ssl
mkdir -p logs
mkdir -p backups

# Generate SSL certificates if they don't exist
if [ ! -f nginx/ssl/istanbulplus.ir.crt ]; then
    warn "SSL certificates not found. Generating self-signed certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout nginx/ssl/istanbulplus.ir.key \
        -out nginx/ssl/istanbulplus.ir.crt \
        -subj "/C=IR/ST=Tehran/L=Tehran/O=Istanbul Plus/CN=istanbulplus.ir"
fi

# Stop existing containers
log "Stopping existing containers..."
docker-compose down || true

# Pull latest images
log "Pulling latest images..."
docker-compose pull

# Build Istanbul Plus image
log "Building Istanbul Plus Docker image..."
docker-compose build istanbulplus-web

# Start services
log "Starting services..."
docker-compose up -d

# Wait for services to be ready
log "Waiting for services to be ready..."
sleep 30

# Check if services are running
log "Checking service status..."
if ! docker-compose ps | grep -q "Up"; then
    error "Some services failed to start. Check logs with: docker-compose logs"
fi

# Run database migrations
log "Running database migrations..."
docker-compose exec istanbulplus-web python manage.py migrate --settings=settings.prod

# Create superuser if it doesn't exist
log "Creating superuser..."
docker-compose exec -T istanbulplus-web python manage.py shell --settings=settings.prod << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@istanbulplus.ir', 'admin123')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

# Collect static files
log "Collecting static files..."
docker-compose exec istanbulplus-web python manage.py collectstatic --noinput --settings=settings.prod

# Optimize database
log "Optimizing database..."
docker-compose exec istanbulplus-web python manage.py optimize_db --analyze --settings=settings.prod

# Setup cron jobs
log "Setting up cron jobs..."
(crontab -l 2>/dev/null; echo "0 2 * * * cd $(pwd) && docker-compose exec -T istanbulplus-web python manage.py cleanup_expired_data --settings=settings.prod") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * 0 cd $(pwd) && docker-compose exec -T istanbulplus-web python manage.py optimize_db --vacuum --analyze --settings=settings.prod") | crontab -

# Create backup script
log "Creating backup script..."
cat > scripts/backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/istanbulplus"

mkdir -p $BACKUP_DIR

# Database backup
docker-compose exec -T istanbulplus-db pg_dump -U istanbulplus_user istanbulplus_db | gzip > $BACKUP_DIR/db_$DATE.sql.gz

# Media files backup
docker run --rm -v istanbulplus_media:/data -v $BACKUP_DIR:/backup alpine tar -czf /backup/media_$DATE.tar.gz -C /data .

echo "Backup completed: $DATE"
EOF

chmod +x scripts/backup.sh

# Test deployment
log "Testing deployment..."
if curl -f http://localhost:8001/health/ > /dev/null 2>&1; then
    log "Istanbul Plus is running successfully!"
else
    warn "Health check failed. Check logs with: docker-compose logs istanbulplus-web"
fi

# Display service information
log "Deployment completed successfully!"
echo ""
echo -e "${BLUE}Service Information:${NC}"
echo -e "Istanbul Plus: https://istanbulplus.ir (or http://localhost:8001)"
echo -e "Peykan Tourism: https://peykan-tourism.ir (or http://localhost:8000)"
echo -e "Grafana: http://localhost:3000"
echo -e "Prometheus: http://localhost:9090"
echo ""
echo -e "${BLUE}Useful Commands:${NC}"
echo -e "View logs: docker-compose logs -f"
echo -e "Restart services: docker-compose restart"
echo -e "Stop services: docker-compose down"
echo -e "Backup: ./scripts/backup.sh"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Configure your domain DNS to point to this server"
echo -e "2. Update SSL certificates with Let's Encrypt"
echo -e "3. Configure monitoring alerts"
echo -e "4. Test all functionality"

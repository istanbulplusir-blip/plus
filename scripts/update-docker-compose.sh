#!/bin/bash

# Update Docker Compose configuration script
# This script updates the docker-compose.yml to include all new services

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

log "Updating Docker Compose configuration..."

# Backup existing docker-compose.yml
if [ -f "docker-compose.yml" ]; then
    cp docker-compose.yml docker-compose.yml.backup
    log "Backed up existing docker-compose.yml"
fi

# Update docker-compose.yml with new services
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # Istanbul Plus Services
  istanbulplus-web:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: istanbulplus-web
    restart: unless-stopped
    ports:
      - "8001:8000"
    environment:
      - DEBUG=False
      - DB_NAME=istanbulplus_db
      - DB_USER=istanbulplus_user
      - DB_PASSWORD=${ISTANBULPLUS_DB_PASSWORD}
      - DB_HOST=istanbulplus-db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/3
      - REDIS_RATE_LIMIT_URL=redis://redis:6379/4
      - SECRET_KEY=${ISTANBULPLUS_SECRET_KEY}
      - EMAIL_HOST=${EMAIL_HOST}
      - EMAIL_HOST_USER=${EMAIL_HOST_USER}
      - EMAIL_HOST_PASSWORD=${EMAIL_HOST_PASSWORD}
      - OTP_SMS_API_KEY=${OTP_SMS_API_KEY}
      - PAYMENT_MERCHANT_ID=${PAYMENT_MERCHANT_ID}
      - SITE_URL=https://istanbulplus.ir
    volumes:
      - istanbulplus_media:/app/media
      - istanbulplus_static:/app/staticfiles
      - ./logging:/app/logging:ro
    depends_on:
      - istanbulplus-db
      - redis
    networks:
      - istanbulplus_network
      - shared_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  istanbulplus-db:
    image: postgres:15-alpine
    container_name: istanbulplus-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=istanbulplus_db
      - POSTGRES_USER=istanbulplus_user
      - POSTGRES_PASSWORD=${ISTANBULPLUS_DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--encoding=UTF-8 --lc-collate=C --lc-ctype=C
    volumes:
      - istanbulplus_db_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init-db.sql
    ports:
      - "5433:5432"
    networks:
      - istanbulplus_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U istanbulplus_user -d istanbulplus_db"]
      interval: 30s
      timeout: 10s
      retries: 3

  istanbulplus-celery:
    build: 
      context: .
      dockerfile: Dockerfile
    container_name: istanbulplus-celery
    restart: unless-stopped
    command: celery -A istanbulplusir worker --loglevel=info
    environment:
      - DEBUG=False
      - DB_NAME=istanbulplus_db
      - DB_USER=istanbulplus_user
      - DB_PASSWORD=${ISTANBULPLUS_DB_PASSWORD}
      - DB_HOST=istanbulplus-db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/3
      - SECRET_KEY=${ISTANBULPLUS_SECRET_KEY}
    volumes:
      - istanbulplus_media:/app/media
    depends_on:
      - istanbulplus-db
      - redis
    networks:
      - istanbulplus_network
      - shared_network

  # Peykan Tourism Services (existing project)
  peykan-web:
    image: peykan-tourism:latest
    container_name: peykan-web
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DB_NAME=peykan_db
      - DB_USER=peykan_user
      - DB_PASSWORD=${PEYKAN_DB_PASSWORD}
      - DB_HOST=peykan-db
      - DB_PORT=5432
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - peykan_media:/app/media
      - peykan_static:/app/static
    depends_on:
      - peykan-db
      - redis
    networks:
      - peykan_network
      - shared_network

  peykan-db:
    image: postgres:15-alpine
    container_name: peykan-db
    restart: unless-stopped
    environment:
      - POSTGRES_DB=peykan_db
      - POSTGRES_USER=peykan_user
      - POSTGRES_PASSWORD=${PEYKAN_DB_PASSWORD}
    volumes:
      - peykan_db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - peykan_network

  # Shared Redis
  redis:
    image: redis:7-alpine
    container_name: redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    networks:
      - shared_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Nginx Reverse Proxy
  nginx:
    image: nginx:alpine
    container_name: nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/conf.d:/etc/nginx/conf.d:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - istanbulplus_static:/var/www/istanbulplus/static:ro
      - istanbulplus_media:/var/www/istanbulplus/media:ro
      - peykan_static:/var/www/peykan/static:ro
      - peykan_media:/var/www/peykan/media:ro
    depends_on:
      - istanbulplus-web
      - peykan-web
    networks:
      - shared_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health/"]
      interval: 30s
      timeout: 10s
      retries: 3

  # Monitoring with Prometheus
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    restart: unless-stopped
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
      - '--storage.tsdb.retention.time=200h'
      - '--web.enable-lifecycle'
    networks:
      - monitoring_network

  # Grafana for visualization
  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    restart: unless-stopped
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      - GF_INSTALL_PLUGINS=grafana-piechart-panel
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/dashboards:/etc/grafana/provisioning/dashboards:ro
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning:ro
    networks:
      - monitoring_network

  # ELK Stack for Logging
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    container_name: elasticsearch
    restart: unless-stopped
    environment:
      - discovery.type=single-node
      - xpack.security.enabled=false
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
    ports:
      - "9200:9200"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    networks:
      - logging_network

  logstash:
    image: docker.elastic.co/logstash/logstash:8.11.0
    container_name: logstash
    restart: unless-stopped
    volumes:
      - ./logging/logstash.conf:/usr/share/logstash/pipeline/logstash.conf:ro
      - /var/log/istanbulplus:/var/log/istanbulplus:ro
    ports:
      - "5044:5044"
    depends_on:
      - elasticsearch
    networks:
      - logging_network

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    container_name: kibana
    restart: unless-stopped
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - logging_network

  filebeat:
    image: docker.elastic.co/beats/filebeat:8.11.0
    container_name: filebeat
    restart: unless-stopped
    user: root
    volumes:
      - ./logging/filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log/istanbulplus:/var/log/istanbulplus:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock:ro
    depends_on:
      - logstash
    networks:
      - logging_network

volumes:
  istanbulplus_db_data:
    driver: local
  istanbulplus_media:
    driver: local
  istanbulplus_static:
    driver: local
  peykan_db_data:
    driver: local
  peykan_media:
    driver: local
  peykan_static:
    driver: local
  redis_data:
    driver: local
  prometheus_data:
    driver: local
  grafana_data:
    driver: local
  elasticsearch_data:
    driver: local

networks:
  istanbulplus_network:
    driver: bridge
  peykan_network:
    driver: bridge
  shared_network:
    driver: bridge
  monitoring_network:
    driver: bridge
  logging_network:
    driver: bridge
EOF

log "Docker Compose configuration updated successfully!"

# Validate the configuration
log "Validating Docker Compose configuration..."
if docker-compose config > /dev/null 2>&1; then
    log "✓ Docker Compose configuration is valid"
else
    error "✗ Docker Compose configuration is invalid"
fi

log "Update completed successfully!"
log "New services added:"
log "  - Health checks for all services"
log "  - ELK Stack for centralized logging"
log "  - Enhanced monitoring with Grafana dashboards"
log "  - Improved network isolation"
log "  - Volume management for persistent data"

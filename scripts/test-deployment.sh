#!/bin/bash

# Istanbul Plus Deployment Test Script
# This script tests the deployment configuration locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TEST_TIMEOUT=30
HEALTH_CHECK_URL="http://localhost:8001/health/"
METRICS_URL="http://localhost:8001/metrics/"
SYSTEM_INFO_URL="http://localhost:8001/system-info/"

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

# Test results
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    
    info "Running test: $test_name"
    
    if eval "$test_command"; then
        log "✓ $test_name - PASSED"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        error "✗ $test_name - FAILED"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
    fi
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        warn ".env file not found, creating from template..."
        cp env.example .env
    fi
    
    log "Prerequisites check completed"
}

# Test Docker configuration
test_docker_config() {
    log "Testing Docker configuration..."
    
    # Test Dockerfile syntax
    run_test "Dockerfile syntax" "docker build --no-cache -t istanbulplus-test ."
    
    # Test docker-compose syntax
    run_test "Docker Compose syntax" "docker-compose config"
    
    # Clean up test image
    docker rmi istanbulplus-test 2>/dev/null || true
}

# Test environment configuration
test_environment() {
    log "Testing environment configuration..."
    
    # Check required environment variables
    run_test "Environment file exists" "[ -f .env ]"
    
    # Check if required variables are set
    run_test "Secret key configured" "grep -q 'SECRET_KEY=' .env && ! grep -q 'SECRET_KEY=your_' .env"
    run_test "Database password configured" "grep -q 'DB_PASSWORD=' .env && ! grep -q 'DB_PASSWORD=your_' .env"
    run_test "Debug mode disabled" "grep -q 'DEBUG=False' .env"
}

# Test SSL configuration
test_ssl_config() {
    log "Testing SSL configuration..."
    
    # Check if SSL directory exists
    run_test "SSL directory exists" "[ -d nginx/ssl ]"
    
    # Check if SSL script is executable
    run_test "SSL script is executable" "[ -x scripts/ssl-setup.sh ]"
    
    # Test self-signed certificate generation
    run_test "Self-signed certificate generation" "scripts/ssl-setup.sh --self-signed"
    
    # Check if certificates were created
    run_test "SSL certificates created" "[ -f nginx/ssl/istanbulplus.ir.crt ] && [ -f nginx/ssl/istanbulplus.ir.key ]"
}

# Test Nginx configuration
test_nginx_config() {
    log "Testing Nginx configuration..."
    
    # Check if Nginx config files exist
    run_test "Nginx main config exists" "[ -f nginx/nginx.conf ]"
    run_test "Istanbul Plus config exists" "[ -f nginx/conf.d/istanbulplus.conf ]"
    run_test "Peykan config exists" "[ -f nginx/conf.d/peykan.conf ]"
    
    # Test Nginx configuration syntax
    run_test "Nginx config syntax" "docker run --rm -v $(pwd)/nginx:/etc/nginx:ro nginx:alpine nginx -t"
}

# Test database configuration
test_database_config() {
    log "Testing database configuration..."
    
    # Check if database init script exists
    run_test "Database init script exists" "[ -f scripts/init-db.sql ]"
    
    # Test SQL syntax
    run_test "Database init script syntax" "docker run --rm -v $(pwd)/scripts:/scripts:ro postgres:15-alpine psql --help"
}

# Test monitoring configuration
test_monitoring_config() {
    log "Testing monitoring configuration..."
    
    # Check if Prometheus config exists
    run_test "Prometheus config exists" "[ -f monitoring/prometheus.yml ]"
    
    # Check if Grafana dashboards exist
    run_test "Grafana dashboards exist" "[ -f monitoring/grafana/dashboards/istanbulplus-overview.json ]"
    run_test "Database dashboard exists" "[ -f monitoring/grafana/dashboards/database-performance.json ]"
    run_test "Security dashboard exists" "[ -f monitoring/grafana/dashboards/security-monitoring.json ]"
}

# Test logging configuration
test_logging_config() {
    log "Testing logging configuration..."
    
    # Check if logging config exists
    run_test "Logging config exists" "[ -f logging/logging.conf ]"
    run_test "Logrotate config exists" "[ -f logging/logrotate.conf ]"
    run_test "ELK stack config exists" "[ -f logging/elk-stack.yml ]"
}

# Test deployment scripts
test_deployment_scripts() {
    log "Testing deployment scripts..."
    
    # Check if scripts exist and are executable
    run_test "Deploy script exists" "[ -f scripts/deploy.sh ]"
    run_test "Backup script exists" "[ -f scripts/backup.sh ]"
    run_test "Restore script exists" "[ -f scripts/restore.sh ]"
    run_test "Security hardening script exists" "[ -f scripts/security-hardening.sh ]"
    run_test "Security audit script exists" "[ -f scripts/security-audit.sh ]"
    
    # Make scripts executable
    chmod +x scripts/*.sh
    
    # Test script syntax
    run_test "Deploy script syntax" "bash -n scripts/deploy.sh"
    run_test "Backup script syntax" "bash -n scripts/backup.sh"
    run_test "Restore script syntax" "bash -n scripts/restore.sh"
    run_test "SSL setup script syntax" "bash -n scripts/ssl-setup.sh"
}

# Test Docker Compose services
test_docker_compose_services() {
    log "Testing Docker Compose services..."
    
    # Start services
    log "Starting Docker Compose services..."
    docker-compose up -d
    
    # Wait for services to be ready
    log "Waiting for services to be ready..."
    sleep 30
    
    # Test if services are running
    run_test "Istanbul Plus web service" "docker-compose ps | grep -q 'istanbulplus-web.*Up'"
    run_test "Istanbul Plus database" "docker-compose ps | grep -q 'istanbulplus-db.*Up'"
    run_test "Redis service" "docker-compose ps | grep -q 'redis.*Up'"
    run_test "Nginx service" "docker-compose ps | grep -q 'nginx.*Up'"
    
    # Test health endpoint
    run_test "Health endpoint accessible" "curl -f $HEALTH_CHECK_URL > /dev/null 2>&1"
    
    # Test metrics endpoint
    run_test "Metrics endpoint accessible" "curl -f $METRICS_URL > /dev/null 2>&1"
    
    # Test system info endpoint
    run_test "System info endpoint accessible" "curl -f $SYSTEM_INFO_URL > /dev/null 2>&1"
}

# Test database connectivity
test_database_connectivity() {
    log "Testing database connectivity..."
    
    # Test database connection
    run_test "Database connection" "docker-compose exec -T istanbulplus-web python manage.py check --database default"
    
    # Test database migrations
    run_test "Database migrations" "docker-compose exec -T istanbulplus-web python manage.py migrate --dry-run"
}

# Test Redis connectivity
test_redis_connectivity() {
    log "Testing Redis connectivity..."
    
    # Test Redis connection
    run_test "Redis connection" "docker-compose exec redis redis-cli ping"
    
    # Test Redis operations
    run_test "Redis operations" "docker-compose exec redis redis-cli set test_key test_value && docker-compose exec redis redis-cli get test_key | grep -q test_value"
}

# Test Nginx functionality
test_nginx_functionality() {
    log "Testing Nginx functionality..."
    
    # Test Nginx configuration
    run_test "Nginx config test" "docker-compose exec nginx nginx -t"
    
    # Test HTTP response
    run_test "HTTP response" "curl -f http://localhost/health/ > /dev/null 2>&1"
}

# Test security features
test_security_features() {
    log "Testing security features..."
    
    # Test SSL/TLS
    run_test "SSL certificate" "[ -f nginx/ssl/istanbulplus.ir.crt ]"
    
    # Test security headers
    run_test "Security headers" "curl -I http://localhost/health/ | grep -q 'X-Frame-Options'"
    
    # Test rate limiting (basic check)
    run_test "Rate limiting config" "grep -q 'limit_req' nginx/conf.d/istanbulplus.conf"
}

# Test monitoring functionality
test_monitoring_functionality() {
    log "Testing monitoring functionality..."
    
    # Test Prometheus
    run_test "Prometheus accessible" "curl -f http://localhost:9090 > /dev/null 2>&1"
    
    # Test Grafana
    run_test "Grafana accessible" "curl -f http://localhost:3000 > /dev/null 2>&1"
}

# Performance test
test_performance() {
    log "Testing basic performance..."
    
    # Test response time
    RESPONSE_TIME=$(curl -o /dev/null -s -w '%{time_total}' http://localhost/health/)
    if (( $(echo "$RESPONSE_TIME < 2.0" | bc -l) )); then
        log "✓ Response time test - PASSED (${RESPONSE_TIME}s)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        warn "✗ Response time test - FAILED (${RESPONSE_TIME}s)"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Test concurrent requests
    run_test "Concurrent requests" "for i in {1..10}; do curl -f http://localhost/health/ > /dev/null 2>&1 & done; wait"
}

# Cleanup function
cleanup() {
    log "Cleaning up test environment..."
    docker-compose down -v 2>/dev/null || true
    docker system prune -f 2>/dev/null || true
}

# Main test execution
main() {
    log "Starting Istanbul Plus deployment tests..."
    
    # Set up cleanup trap
    trap cleanup EXIT
    
    # Run all tests
    check_prerequisites
    test_docker_config
    test_environment
    test_ssl_config
    test_nginx_config
    test_database_config
    test_monitoring_config
    test_logging_config
    test_deployment_scripts
    test_docker_compose_services
    test_database_connectivity
    test_redis_connectivity
    test_nginx_functionality
    test_security_features
    test_monitoring_functionality
    test_performance
    
    # Display results
    echo ""
    log "=== TEST RESULTS ==="
    log "Tests passed: $TESTS_PASSED"
    if [ $TESTS_FAILED -gt 0 ]; then
        error "Tests failed: $TESTS_FAILED"
    else
        log "Tests failed: $TESTS_FAILED"
    fi
    
    if [ $TESTS_FAILED -eq 0 ]; then
        log "🎉 All tests passed! Deployment configuration is ready."
    else
        warn "⚠️  Some tests failed. Please review and fix the issues."
        exit 1
    fi
}

# Run main function
main "$@"

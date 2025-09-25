#!/bin/bash

# SSL Certificate Management Script for Istanbul Plus
# This script handles SSL certificate generation and renewal

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOMAINS=("istanbulplus.ir" "www.istanbulplus.ir" "peykan-tourism.ir" "www.peykan-tourism.ir")
EMAIL="admin@istanbulplus.ir"
NGINX_SSL_DIR="./nginx/ssl"
CERTBOT_DIR="/etc/letsencrypt"

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
    echo "  -g, --generate     Generate new SSL certificates"
    echo "  -r, --renew        Renew existing certificates"
    echo "  -s, --self-signed  Generate self-signed certificates for testing"
    echo "  -c, --copy         Copy certificates to nginx directory"
    echo "  -h, --help         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --generate"
    echo "  $0 --renew"
    echo "  $0 --self-signed"
    exit 1
}

# Check if running as root for certbot operations
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This operation requires root privileges. Please run with sudo."
    fi
}

# Install certbot if not installed
install_certbot() {
    if ! command -v certbot &> /dev/null; then
        log "Installing certbot..."
        apt update
        apt install -y certbot python3-certbot-nginx
    fi
}

# Generate Let's Encrypt certificates
generate_certificates() {
    check_root
    install_certbot
    
    log "Generating SSL certificates for domains: ${DOMAINS[*]}"
    
    # Stop nginx to free port 80
    docker-compose stop nginx || true
    
    for domain in "${DOMAINS[@]}"; do
        log "Generating certificate for $domain..."
        
        if [[ $domain == *"istanbulplus"* ]]; then
            certbot certonly \
                --standalone \
                --non-interactive \
                --agree-tos \
                --email $EMAIL \
                -d $domain
        else
            certbot certonly \
                --standalone \
                --non-interactive \
                --agree-tos \
                --email $EMAIL \
                -d $domain
        fi
    done
    
    # Copy certificates to nginx directory
    copy_certificates
    
    # Start nginx
    docker-compose start nginx
    
    log "SSL certificates generated successfully!"
}

# Renew existing certificates
renew_certificates() {
    check_root
    
    log "Renewing SSL certificates..."
    
    # Stop nginx
    docker-compose stop nginx
    
    # Renew certificates
    certbot renew --standalone --non-interactive
    
    # Copy certificates to nginx directory
    copy_certificates
    
    # Start nginx
    docker-compose start nginx
    
    log "SSL certificates renewed successfully!"
}

# Generate self-signed certificates for testing
generate_self_signed() {
    log "Generating self-signed certificates for testing..."
    
    # Create SSL directory
    mkdir -p $NGINX_SSL_DIR
    
    # Generate private key
    openssl genrsa -out $NGINX_SSL_DIR/istanbulplus.ir.key 2048
    
    # Generate certificate signing request
    openssl req -new -key $NGINX_SSL_DIR/istanbulplus.ir.key \
        -out $NGINX_SSL_DIR/istanbulplus.ir.csr \
        -subj "/C=IR/ST=Tehran/L=Tehran/O=Istanbul Plus/CN=istanbulplus.ir"
    
    # Generate self-signed certificate
    openssl x509 -req -days 365 \
        -in $NGINX_SSL_DIR/istanbulplus.ir.csr \
        -signkey $NGINX_SSL_DIR/istanbulplus.ir.key \
        -out $NGINX_SSL_DIR/istanbulplus.ir.crt
    
    # Generate for peykan-tourism
    openssl genrsa -out $NGINX_SSL_DIR/peykan-tourism.ir.key 2048
    openssl req -new -key $NGINX_SSL_DIR/peykan-tourism.ir.key \
        -out $NGINX_SSL_DIR/peykan-tourism.ir.csr \
        -subj "/C=IR/ST=Tehran/L=Tehran/O=Peykan Tourism/CN=peykan-tourism.ir"
    openssl x509 -req -days 365 \
        -in $NGINX_SSL_DIR/peykan-tourism.ir.csr \
        -signkey $NGINX_SSL_DIR/peykan-tourism.ir.key \
        -out $NGINX_SSL_DIR/peykan-tourism.ir.crt
    
    # Clean up CSR files
    rm $NGINX_SSL_DIR/*.csr
    
    # Set proper permissions
    chmod 600 $NGINX_SSL_DIR/*.key
    chmod 644 $NGINX_SSL_DIR/*.crt
    
    log "Self-signed certificates generated successfully!"
    warn "These are self-signed certificates for testing only!"
}

# Copy certificates from Let's Encrypt to nginx directory
copy_certificates() {
    log "Copying certificates to nginx directory..."
    
    # Create nginx SSL directory
    mkdir -p $NGINX_SSL_DIR
    
    # Copy Istanbul Plus certificates
    if [ -f "$CERTBOT_DIR/live/istanbulplus.ir/fullchain.pem" ]; then
        cp $CERTBOT_DIR/live/istanbulplus.ir/fullchain.pem $NGINX_SSL_DIR/istanbulplus.ir.crt
        cp $CERTBOT_DIR/live/istanbulplus.ir/privkey.pem $NGINX_SSL_DIR/istanbulplus.ir.key
        log "Istanbul Plus certificates copied"
    else
        warn "Istanbul Plus certificates not found in Let's Encrypt directory"
    fi
    
    # Copy Peykan Tourism certificates
    if [ -f "$CERTBOT_DIR/live/peykan-tourism.ir/fullchain.pem" ]; then
        cp $CERTBOT_DIR/live/peykan-tourism.ir/fullchain.pem $NGINX_SSL_DIR/peykan-tourism.ir.crt
        cp $CERTBOT_DIR/live/peykan-tourism.ir/privkey.pem $NGINX_SSL_DIR/peykan-tourism.ir.key
        log "Peykan Tourism certificates copied"
    else
        warn "Peykan Tourism certificates not found in Let's Encrypt directory"
    fi
    
    # Set proper permissions
    chmod 600 $NGINX_SSL_DIR/*.key
    chmod 644 $NGINX_SSL_DIR/*.crt
    
    log "Certificates copied successfully!"
}

# Check certificate validity
check_certificates() {
    log "Checking certificate validity..."
    
    for domain in "${DOMAINS[@]}"; do
        if [[ $domain == *"istanbulplus"* ]]; then
            cert_file="$NGINX_SSL_DIR/istanbulplus.ir.crt"
        else
            cert_file="$NGINX_SSL_DIR/peykan-tourism.ir.crt"
        fi
        
        if [ -f "$cert_file" ]; then
            expiry_date=$(openssl x509 -enddate -noout -in "$cert_file" | cut -d= -f2)
            expiry_epoch=$(date -d "$expiry_date" +%s)
            current_epoch=$(date +%s)
            days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [ $days_until_expiry -gt 30 ]; then
                log "$domain certificate is valid for $days_until_expiry days"
            elif [ $days_until_expiry -gt 0 ]; then
                warn "$domain certificate expires in $days_until_expiry days"
            else
                error "$domain certificate has expired!"
            fi
        else
            warn "Certificate file not found for $domain: $cert_file"
        fi
    done
}

# Setup automatic renewal
setup_auto_renewal() {
    check_root
    
    log "Setting up automatic certificate renewal..."
    
    # Create renewal script
    cat > /usr/local/bin/renew-ssl.sh << 'EOF'
#!/bin/bash
cd /path/to/istanbulplus/project
docker-compose stop nginx
certbot renew --standalone --non-interactive
./scripts/ssl-setup.sh --copy
docker-compose start nginx
EOF
    
    chmod +x /usr/local/bin/renew-ssl.sh
    
    # Add to crontab (run twice daily)
    (crontab -l 2>/dev/null; echo "0 2,14 * * * /usr/local/bin/renew-ssl.sh") | crontab -
    
    log "Automatic renewal setup completed!"
}

# Parse command line arguments
GENERATE=false
RENEW=false
SELF_SIGNED=false
COPY=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -g|--generate)
            GENERATE=true
            shift
            ;;
        -r|--renew)
            RENEW=true
            shift
            ;;
        -s|--self-signed)
            SELF_SIGNED=true
            shift
            ;;
        -c|--copy)
            COPY=true
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

# Execute requested operations
if [ "$GENERATE" = true ]; then
    generate_certificates
elif [ "$RENEW" = true ]; then
    renew_certificates
elif [ "$SELF_SIGNED" = true ]; then
    generate_self_signed
elif [ "$COPY" = true ]; then
    copy_certificates
else
    # Default: check certificates
    check_certificates
fi

log "SSL setup completed successfully!"

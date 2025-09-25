#!/bin/bash

# Istanbul Plus Quick Deploy Script for Windows/Local Development
# This script provides a quick way to deploy the project locally for testing

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_DIR="$(pwd)"
DOMAIN="localhost"
PORT="8000"

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

log "Starting Istanbul Plus quick deployment..."

# 1. Check Python Installation
log "Checking Python installation..."
if ! command -v python &> /dev/null; then
    error "Python is not installed. Please install Python 3.9+ first."
fi

PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
log "Python version: $PYTHON_VERSION"

# 2. Check if Virtual Environment Exists
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python -m venv venv
fi

# 3. Activate Virtual Environment
log "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# 4. Install/Update Dependencies
log "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements/prod.txt

# 5. Check Environment File
if [ ! -f ".env" ]; then
    log "Creating environment file..."
    cp env.example .env
    warn "Please update .env file with your configuration"
fi

# 6. Run Database Migrations
log "Running database migrations..."
python manage.py migrate

# 7. Collect Static Files
log "Collecting static files..."
python manage.py collectstatic --noinput

# 8. Create Superuser (if not exists)
log "Creating superuser (if not exists)..."
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
EOF

# 9. Start Development Server
log "Starting development server..."
log "Server will be available at: http://$DOMAIN:$PORT"
log "Admin panel: http://$DOMAIN:$PORT/admin/"
log "Health check: http://$DOMAIN:$PORT/health/"
log ""
log "Press Ctrl+C to stop the server"
echo ""

# Start the server
python manage.py runserver 0.0.0.0:$PORT

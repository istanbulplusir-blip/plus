# Istanbul Plus Quick Deploy Script for Windows PowerShell
# This script provides a quick way to deploy the project locally for testing

param(
    [string]$Port = "8000",
    [string]$ServerHost = "0.0.0.0"
)

# Colors for output
$Red = "Red"
$Green = "Green"
$Yellow = "Yellow"
$Blue = "Blue"

# Logging function
function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor $Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] WARNING: $Message" -ForegroundColor $Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] ERROR: $Message" -ForegroundColor $Red
    exit 1
}

function Write-Info {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] INFO: $Message" -ForegroundColor $Blue
}

Write-Log "Starting Istanbul Plus quick deployment..."

# 1. Check Python Installation
Write-Log "Checking Python installation..."
try {
    $pythonVersion = python --version 2>&1
    Write-Log "Python version: $pythonVersion"
} catch {
    Write-Error "Python is not installed. Please install Python 3.9+ first."
}

# 2. Check if Virtual Environment Exists
if (-not (Test-Path "venv")) {
    Write-Log "Creating virtual environment..."
    python -m venv venv
}

# 3. Activate Virtual Environment
Write-Log "Activating virtual environment..."
& "venv\Scripts\Activate.ps1"

# 4. Install/Update Dependencies
Write-Log "Installing/updating dependencies..."
python -m pip install --upgrade pip
pip install -r requirements/prod.txt

# 5. Check Environment File
if (-not (Test-Path ".env")) {
    Write-Log "Creating environment file..."
    Copy-Item "env.example" ".env"
    Write-Warning "Please update .env file with your configuration"
}

# 6. Run Database Migrations
Write-Log "Running database migrations..."
python manage.py migrate

# 7. Collect Static Files
Write-Log "Collecting static files..."
python manage.py collectstatic --noinput

# 8. Create Superuser (if not exists)
Write-Log "Creating superuser (if not exists)..."
$superuserScript = @"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@localhost', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"@

$superuserScript | python manage.py shell

# 9. Start Development Server
Write-Log "Starting development server..."
Write-Log "Server will be available at: http://$ServerHost`:$Port"
Write-Log "Admin panel: http://$ServerHost`:$Port/admin/"
Write-Log "Health check: http://$ServerHost`:$Port/health/"
Write-Log ""
Write-Log "Press Ctrl+C to stop the server"
Write-Host ""

# Start the server
python manage.py runserver "$ServerHost`:$Port"

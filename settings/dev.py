from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', 'testserver']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# SECRET_KEY for dev
SECRET_KEY = 'dev-insecure-changeme-in-prod'

# Email configuration for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
EMAIL_USE_TLS = False
DEFAULT_FROM_EMAIL = 'development@istanbulplus.ir'

# Site URL for email links
SITE_URL = 'http://localhost:8000'

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Cache settings - Local memory for development (Redis not available)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    },
    'rate_limit': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'rate-limit-cache',
    }
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
]

# Django Debug Toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

# OTP SMS settings for development (prints to console)
OTP_SMS_BACKEND = 'dev'
OTP_SMS_API_KEY = 'dummy-key'

# Payment gateway settings for development (sandbox)
PAYMENT_GATEWAY = {
    'sandbox': True,
    'merchant_id': 'dummy-merchant',
    'callback_url': 'http://localhost:8000/payments/verify/',
}

# No need to override STATICFILES_DIRS as it's properly set in base.py
# Using STATIC_ROOT from base.py

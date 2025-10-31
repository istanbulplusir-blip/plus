from .base import *
import os

# Add CSRF exempt middleware for admin (temporary fix)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'users.middleware.security_headers.SecurityHeadersMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cart.middleware.cart_middleware',
]

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = [
    'istanbulplus.ir',
    'www.istanbulplus.ir',
    'localhost',
    '127.0.0.1',
    'istanbulplus-web',  # Docker container name
]

# Database - PostgreSQL for production
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'istanbulplus'),
        'USER': os.environ.get('DB_USER', 'istanbulplus'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'disable',
        },
    }
}

# SECRET_KEY from environment
SECRET_KEY = os.environ.get('SECRET_KEY')

# Email configuration for production
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL',
                                    'noreply@istanbulplus.ir')

# Site URL for email links
SITE_URL = os.environ.get('SITE_URL', 'https://istanbulplus.ir')

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Cache settings - Redis for production with password authentication
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://redis:6379/3'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    },
    'rate_limit': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_RATE_LIMIT_URL', 'redis://redis:6379/4'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'PASSWORD': os.environ.get('REDIS_PASSWORD'),
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

# Session engine - use Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# CORS settings for production
CORS_ALLOWED_ORIGINS = [
    'https://istanbulplus.ir',
    'https://www.istanbulplus.ir',
]

# CSRF settings for production
CSRF_TRUSTED_ORIGINS = [
    'https://istanbulplus.ir',
    'https://www.istanbulplus.ir',
]
CSRF_COOKIE_DOMAIN = None  # Let Django handle it automatically
CSRF_USE_SESSIONS = False  # Use cookies for better compatibility with nginx
CSRF_COOKIE_SECURE = True  # Always True in production (DEBUG=False)
CSRF_FAILURE_VIEW = 'django.views.csrf.csrf_failure'

# Add proxy SSL header for reverse proxy setup
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# OTP SMS settings for production
OTP_SMS_BACKEND = os.environ.get('OTP_SMS_BACKEND', 'kavenegar')
OTP_SMS_API_KEY = os.environ.get('OTP_SMS_API_KEY')

# Payment gateway settings for production
PAYMENT_GATEWAY = {
    'sandbox': False,
    'merchant_id': os.environ.get('PAYMENT_MERCHANT_ID'),
    'callback_url': f"{SITE_URL}/payments/verify/",
}

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# HTTPS settings
SECURE_SSL_REDIRECT = False  # Nginx handles SSL termination
SESSION_COOKIE_SECURE = not DEBUG  # Only secure in production
CSRF_COOKIE_SECURE = not DEBUG  # Only secure in production
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_DOMAIN = None  # Let Django handle it automatically

# Additional security headers
SECURE_CROSS_ORIGIN_OPENER_POLICY = 'same-origin'
SECURE_PERMISSIONS_POLICY = {
    'accelerometer': [],
    'ambient-light-sensor': [],
    'autoplay': [],
    'battery': [],
    'camera': [],
    'display-capture': [],
    'document-domain': [],
    'encrypted-media': [],
    'execution-while-not-rendered': [],
    'execution-while-out-of-viewport': [],
    'fullscreen': [],
    'geolocation': [],
    'gyroscope': [],
    'layout-animations': [],
    'legacy-image-formats': [],
    'magnetometer': [],
    'microphone': [],
    'midi': [],
    'navigation-override': [],
    'oversized-images': [],
    'payment': [],
    'picture-in-picture': [],
    'publickey-credentials-get': [],
    'sync-xhr': [],
    'usb': [],
    'vr': [],
    'wake-lock': [],
    'xr-spatial-tracking': [],
}

# Static files - use simple storage for production with Nginx
# STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# CSS Optimization Settings
CSS_OPTIMIZATION = {
    'ENABLED': True,
    'MINIFY': True,
    'GZIP': True,
    'CRITICAL_CSS': True,
    'PURGE_UNUSED': True,
    'CACHE_BUSTING': True,
}

# Static files compression
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Additional static files settings for optimization
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Whitenoise settings for better static file serving
# MIDDLEWARE.insert(1, 'django.middleware.security.SecurityMiddleware')
MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')

# WhiteNoise configuration for media files
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = True

# Static files storage backend - use simple storage for production with Nginx
# Use STORAGES for Django 4.2+ - Override any default settings
if 'STORAGES' not in dir():
    STORAGES = {}
STORAGES.update({
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
})

# Add compression headers for static files
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True

# Cache control for static files
STATICFILES_STORAGE_OPTIONS = {
    'max_age': 31536000,  # 1 year cache for static files
}

# Logging for production
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'users': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# FINAL OVERRIDE: Force Django to use StaticFilesStorage instead of WhiteNoise
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
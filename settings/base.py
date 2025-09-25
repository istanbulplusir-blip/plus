from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Import payment gateway settings
try:
    from .payment_gateways import *
except ImportError:
    pass


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Third party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'mptt',
    'corsheaders',
    'drf_spectacular',
    # Local
    'users.apps.UsersConfig',
    'products.apps.ProductsConfig',
    'cart.apps.CartConfig',
    'orders.apps.OrdersConfig',
    'payments.apps.PaymentsConfig',
    'core.apps.CoreConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'users.middleware.security_headers.SecurityHeadersMiddleware',  # Additional security headers
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',  # Internationalization middleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'cart.middleware.cart_middleware',
]

ROOT_URLCONF = 'urls'

# Authentication URLs
LOGIN_URL = '/users/login/'
# LOGIN_REDIRECT_URL removed - will be handled dynamically
LOGOUT_REDIRECT_URL = '/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'cart.context_processors.cart_context',
                'core.context_processors.site_context',
                'core.context_processors.navigation_context',
                'core.context_processors.footer_context',
                'core.context_processors.seo_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'wsgi.application'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'fa'

LANGUAGES = [
    ('fa', 'Persian'),
    ('en', 'English'),
]

LOCALE_PATHS = [
    BASE_DIR / 'locale',
]

TIME_ZONE = 'Asia/Tehran'

USE_I18N = True
USE_L10N = True

USE_TZ = True

ALLOWED_HOSTS = []

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files (Uploaded files)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth
AUTH_USER_MODEL = 'users.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# API Documentation
SPECTACULAR_SETTINGS = {
    'TITLE': 'Istanbul Plus E-commerce API',
    'DESCRIPTION': '''
    API documentation for Istanbul Plus E-commerce platform with advanced authentication system.
    
    ## Features
    - JWT-based authentication
    - Two-factor authentication (OTP via SMS/Email)
    - Email and phone verification
    - Password reset functionality
    - Session management
    - Rate limiting and security features
    - Comprehensive user profile management
    
    ## Authentication
    Most endpoints require authentication. Include the JWT token in the Authorization header:
    ```
    Authorization: Bearer <your_jwt_token>
    ```
    
    ## Rate Limiting
    The API implements rate limiting:
    - OTP requests: 5 per hour
    - Login attempts: 10 per hour
    - Password reset: 3 per hour
    - General API: 1000 per hour per user
    ''',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/',
    'TAGS': [
        {
            'name': 'Authentication', 
            'description': 'User registration, login, OTP verification, and password reset'
        },
        {
            'name': 'Profile', 
            'description': 'User profile management and settings'
        },
        {
            'name': 'Security', 
            'description': 'Session management, security logs, and two-factor authentication'
        },
        {
            'name': 'Verification', 
            'description': 'Email and phone number verification'
        },
        {
            'name': 'Products', 
            'description': 'Product catalog management'
        },
        {
            'name': 'Cart', 
            'description': 'Shopping cart operations'
        },
        {
            'name': 'Orders', 
            'description': 'Order management and tracking'
        },
        {
            'name': 'Payments', 
            'description': 'Payment processing and transaction management'
        },
    ],
    'CONTACT': {
        'name': 'Istanbul Plus Support',
        'email': 'support@istanbulplus.ir',
        'url': 'https://istanbulplus.ir/support'
    },
    'LICENSE': {
        'name': 'Proprietary',
        'url': 'https://istanbulplus.ir/license'
    },
    'EXTERNAL_DOCS': {
        'description': 'User Guide and Migration Documentation',
        'url': 'https://docs.istanbulplus.ir'
    },
    'SERVERS': [
        {
            'url': 'https://istanbulplus.ir/api',
            'description': 'Production server'
        },
        {
            'url': 'https://staging.istanbulplus.ir/api',
            'description': 'Staging server'
        },
        {
            'url': 'http://localhost:8000/api',
            'description': 'Development server'
        }
    ],
    'SECURITY': [
        {
            'type': 'http',
            'scheme': 'bearer',
            'bearerFormat': 'JWT',
        }
    ],
    'COMPONENTS': {
        'securitySchemes': {
            'bearerAuth': {
                'type': 'http',
                'scheme': 'bearer',
                'bearerFormat': 'JWT',
            }
        }
    },
    'PREPROCESSING_HOOKS': [
        'docs.api_documentation.custom_preprocessing_hook',
    ],
    'POSTPROCESSING_HOOKS': [
        'docs.api_documentation.custom_postprocessing_hook',
    ],
}

# JWT
from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'BLACKLIST_AFTER_ROTATION': True,
}

# OTP
OTP_CODE_EXPIRY_MINUTES = 5
OTP_MAX_SEND_PER_HOUR = 5
OTP_MAX_VERIFY_ATTEMPTS = 3

# Celery Configuration
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/3'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Tehran'

# Email
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS
CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
]

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django.request': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}

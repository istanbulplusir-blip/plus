# Istanbul Plus E-commerce - Optimization Features

## Overview

This document describes the optimization and performance features implemented in task 12 of the user authentication system.

## Redis Configuration

### Cache Setup

- **Default Cache**: Used for general caching (Redis DB 1)
- **Rate Limit Cache**: Dedicated for rate limiting (Redis DB 2)
- **Celery Broker**: Background task queue (Redis DB 0)
- **Celery Results**: Task result storage (Redis DB 3)

### Configuration Files

- Development: `istanbulplusir/settings/dev.py`
- Production: `istanbulplusir/settings/prod.py`

### Redis Optimization Settings

```redis
maxmemory 256mb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

## Database Optimization

### Index Optimization

#### User Model Indexes

- Single field indexes: `email`, `phone`, `email_verified`, `phone_verified`, `locked_until`, `last_login`, `date_joined`, `is_active`
- Composite indexes:
  - `(email, is_active)`
  - `(phone, is_active)`
  - `(email_verified, phone_verified)`

#### OtpCode Model Indexes

- Single field indexes: `contact_info`, `purpose`, `expires_at`, `used`, `ip_address`, `created_at`
- Composite indexes:
  - `(contact_info, purpose, used)`
  - `(expires_at, used)`
  - `(ip_address, created_at)`

#### UserSession Model Indexes

- Single field indexes: `session_key`, `ip_address`, `is_active`, `last_activity`, `created_at`
- Composite indexes:
  - `(user, is_active)`
  - `(ip_address, is_active)`
  - `(last_activity, is_active)`

#### SecurityLog Model Indexes

- Single field indexes: `event_type`, `severity`, `ip_address`, `created_at`
- Composite indexes:
  - `(user, event_type)`
  - `(event_type, severity)`
  - `(ip_address, event_type)`
  - `(created_at, severity)`
  - `(user, created_at)`

### Database Management Commands

#### optimize_db Command

```bash
# Analyze database statistics
python manage.py optimize_db --analyze

# Vacuum database (PostgreSQL only)
python manage.py optimize_db --vacuum

# Both operations
python manage.py optimize_db --analyze --vacuum
```

#### Features

- PostgreSQL optimization with ANALYZE and VACUUM
- SQLite optimization with PRAGMA commands
- Performance monitoring and logging
- Automatic statistics updates

## Security Headers

### Implemented Headers

- **Content-Security-Policy**: Prevents XSS attacks
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking
- **X-XSS-Protection**: Browser XSS protection
- **Referrer-Policy**: Controls referrer information
- **Cross-Origin-Opener-Policy**: Isolates browsing contexts
- **Cross-Origin-Embedder-Policy**: Enables cross-origin isolation

### HTTPS Configuration

- **Strict-Transport-Security**: Forces HTTPS connections
- **Secure cookies**: Session and CSRF cookies only over HTTPS
- **SSL redirect**: Automatic HTTP to HTTPS redirection
- **HSTS preload**: Browser preload list inclusion

### Security Middleware

- Custom `SecurityHeadersMiddleware` for additional headers
- Server information hiding
- Content Security Policy enforcement

## Data Cleanup System

### Automated Cleanup

#### cleanup_expired_data Command

```bash
# Clean up expired data
python manage.py cleanup_expired_data

# Dry run (show what would be deleted)
python manage.py cleanup_expired_data --dry-run

# Custom retention period
python manage.py cleanup_expired_data --days 60
```

#### Cleaned Data Types

- Expired OTP codes
- Expired password reset tokens
- Expired email verification tokens
- Old security logs (30+ days)
- Inactive user sessions (30+ days)
- Used tokens and codes (30+ days)

### Background Tasks (Celery)

#### Scheduled Tasks

- **cleanup_expired_data**: Every hour
- **optimize_database**: Daily at 2 AM
- **clear_rate_limit_cache**: Every hour
- **generate_security_report**: Weekly on Mondays

#### Task Configuration

```python
# Celery beat schedule
beat_schedule={
    'cleanup-expired-data': {
        'task': 'users.tasks.cleanup_expired_data',
        'schedule': 3600.0,  # Every hour
    },
    'optimize-database': {
        'task': 'users.tasks.optimize_database',
        'schedule': 86400.0,  # Daily
    },
    # ... more tasks
}
```

### Cron Jobs (Alternative)

```bash
# Hourly cleanup
0 * * * * /path/to/venv/bin/python /path/to/project/manage.py cleanup_expired_data

# Daily optimization
0 2 * * * /path/to/venv/bin/python /path/to/project/manage.py optimize_db --analyze

# Weekly vacuum (PostgreSQL)
0 3 * * 0 /path/to/venv/bin/python /path/to/project/manage.py optimize_db --vacuum --analyze
```

## API Documentation

### Swagger/OpenAPI Integration

- **drf-spectacular**: Automatic API documentation generation
- **Swagger UI**: Interactive API documentation at `/api/docs/`
- **ReDoc**: Alternative documentation at `/api/redoc/`
- **Schema endpoint**: Machine-readable schema at `/api/schema/`

### Documentation Features

- Automatic endpoint discovery
- Request/response examples
- Authentication documentation
- Error response documentation
- Rate limiting information

### Configuration

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Istanbul Plus E-commerce API',
    'DESCRIPTION': 'API documentation for Istanbul Plus E-commerce platform',
    'VERSION': '1.0.0',
    'TAGS': [
        {'name': 'Authentication', 'description': 'User authentication'},
        {'name': 'Profile', 'description': 'User profile management'},
        # ... more tags
    ],
}
```

## Performance Monitoring

### Metrics to Monitor

- Database query performance
- Redis memory usage and hit rates
- Response times
- Error rates
- Authentication success/failure rates
- Rate limiting violations
- Background task performance

### Logging Configuration

- Structured logging with JSON format
- Security event logging
- Performance metrics logging
- Error tracking and alerting

### Health Checks

```python
# Database health check
python manage.py check --database default

# Redis health check
redis-cli ping

# Application health check
curl -f https://istanbulplus.ir/api/health/
```

## Security Optimizations

### Rate Limiting

- Redis-based rate limiting
- Per-IP and per-user limits
- Different limits for different endpoints
- Graceful degradation under load

### Session Security

- JWT token optimization
- Session tracking and management
- Concurrent session limits
- Automatic session cleanup

### Data Protection

- Sensitive data encryption
- Secure token generation
- Password hashing optimization
- PII data minimization

## Deployment Optimizations

### Production Settings

- Debug mode disabled
- Secure cookie settings
- HTTPS enforcement
- Static file optimization
- Database connection pooling

### Server Configuration

- Nginx optimization
- Gunicorn worker tuning
- SSL/TLS optimization
- Caching strategies

### Monitoring and Alerting

- Real-time security alerts
- Performance monitoring
- Error tracking
- Capacity planning

## Usage Examples

### Running Optimizations

```bash
# Full optimization routine
python manage.py optimize_db --analyze --vacuum
python manage.py cleanup_expired_data
python manage.py collectstatic --noinput

# Check optimization results
python manage.py shell -c "
from django.core.cache import cache
from users.models import OtpCode
print(f'Cache status: {cache.get(\"test\") or \"OK\"}')
print(f'Expired OTPs: {OtpCode.objects.filter(expires_at__lt=timezone.now()).count()}')
"
```

### Monitoring Commands

```bash
# Check Redis memory usage
redis-cli info memory

# Monitor database performance
python manage.py dbshell -c "SELECT * FROM pg_stat_activity;"

# Check security logs
python manage.py shell -c "
from users.models import SecurityLog
print(SecurityLog.objects.filter(severity='high').count())
"
```

### Background Task Management

```bash
# Start Celery worker
celery -A istanbulplusir worker -l info

# Start Celery beat scheduler
celery -A istanbulplusir beat -l info

# Monitor tasks
celery -A istanbulplusir flower
```

## Best Practices

### Database Optimization

- Regular ANALYZE operations
- Periodic VACUUM (PostgreSQL)
- Index monitoring and optimization
- Query performance analysis

### Cache Management

- Appropriate cache expiration times
- Cache invalidation strategies
- Memory usage monitoring
- Cache hit rate optimization

### Security Maintenance

- Regular security log reviews
- Automated threat detection
- Incident response procedures
- Security update management

### Performance Tuning

- Regular performance testing
- Capacity planning
- Resource utilization monitoring
- Bottleneck identification

This optimization system ensures the Istanbul Plus E-commerce platform maintains high performance, security, and reliability as it scales.

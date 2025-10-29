"""
Health check endpoints for Plus system monitoring
"""
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import time


def health_check(request):
    """
    Basic health check endpoint
    Returns 200 if service is running
    """
    return JsonResponse({
        'status': 'healthy',
        'service': 'plus',
        'timestamp': time.time()
    })


def health_detailed(request):
    """
    Detailed health check with component status
    Checks database, Redis, and cache connectivity
    """
    health_status = {
        'status': 'healthy',
        'service': 'plus',
        'timestamp': time.time(),
        'components': {}
    }
    
    overall_healthy = True
    
    # Check database
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        health_status['components']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        health_status['components']['database'] = {
            'status': 'unhealthy',
            'message': f'Database error: {str(e)}'
        }
        overall_healthy = False
    
    # Check cache (Redis)
    try:
        cache.set('health_check', 'ok', 10)
        result = cache.get('health_check')
        if result == 'ok':
            health_status['components']['cache'] = {
                'status': 'healthy',
                'message': 'Cache connection successful'
            }
        else:
            health_status['components']['cache'] = {
                'status': 'unhealthy',
                'message': 'Cache read/write failed'
            }
            overall_healthy = False
    except Exception as e:
        health_status['components']['cache'] = {
            'status': 'unhealthy',
            'message': f'Cache error: {str(e)}'
        }
        overall_healthy = False
    
    # Check Redis directly (for Celery)
    try:
        redis_url = getattr(settings, 'CELERY_BROKER_URL', None)
        if redis_url:
            r = redis.from_url(redis_url)
            r.ping()
            health_status['components']['redis'] = {
                'status': 'healthy',
                'message': 'Redis connection successful'
            }
        else:
            health_status['components']['redis'] = {
                'status': 'unknown',
                'message': 'Redis URL not configured'
            }
    except Exception as e:
        health_status['components']['redis'] = {
            'status': 'unhealthy',
            'message': f'Redis error: {str(e)}'
        }
        overall_healthy = False
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
        return JsonResponse(health_status, status=503)
    
    return JsonResponse(health_status)


def readiness_check(request):
    """
    Readiness check - indicates if service is ready to accept traffic
    """
    try:
        # Quick database check
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        
        return JsonResponse({
            'status': 'ready',
            'service': 'plus',
            'timestamp': time.time()
        })
    except Exception as e:
        return JsonResponse({
            'status': 'not_ready',
            'service': 'plus',
            'error': str(e),
            'timestamp': time.time()
        }, status=503)


def liveness_check(request):
    """
    Liveness check - indicates if service is alive
    Simple check that doesn't depend on external services
    """
    return JsonResponse({
        'status': 'alive',
        'service': 'plus',
        'timestamp': time.time()
    })

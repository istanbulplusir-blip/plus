from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import redis
import psutil
import os
from datetime import datetime


@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring and load balancers
    """
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'services': {}
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        health_status['services']['database'] = 'healthy'
    except Exception as e:
        health_status['services']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check Redis connection
    try:
        cache.set('health_check', 'test', 10)
        cache.get('health_check')
        health_status['services']['redis'] = 'healthy'
    except Exception as e:
        health_status['services']['redis'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'
    
    # Check disk space
    try:
        disk_usage = psutil.disk_usage('/')
        free_space_gb = disk_usage.free / (1024**3)
        health_status['services']['disk_space'] = f'healthy ({free_space_gb:.2f}GB free)'
        if free_space_gb < 1:  # Less than 1GB free
            health_status['services']['disk_space'] = f'warning ({free_space_gb:.2f}GB free)'
    except Exception as e:
        health_status['services']['disk_space'] = f'unhealthy: {str(e)}'
    
    # Check memory usage
    try:
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        health_status['services']['memory'] = f'healthy ({memory_percent:.1f}% used)'
        if memory_percent > 90:
            health_status['services']['memory'] = f'warning ({memory_percent:.1f}% used)'
    except Exception as e:
        health_status['services']['memory'] = f'unhealthy: {str(e)}'
    
    # Check Celery workers
    try:
        from celery import current_app
        inspect = current_app.control.inspect()
        active_workers = inspect.active()
        if active_workers:
            health_status['services']['celery'] = f'healthy ({len(active_workers)} workers)'
        else:
            health_status['services']['celery'] = 'warning (no active workers)'
    except Exception as e:
        health_status['services']['celery'] = f'unhealthy: {str(e)}'
    
    # Return appropriate HTTP status
    status_code = 200 if health_status['status'] == 'healthy' else 503
    
    return JsonResponse(health_status, status=status_code)


@require_http_methods(["GET"])
def metrics(request):
    """
    Prometheus metrics endpoint
    """
    metrics_data = []
    
    # Database metrics
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM django_session")
            session_count = cursor.fetchone()[0]
            metrics_data.append(f'django_sessions_total {session_count}')
            
            cursor.execute("SELECT COUNT(*) FROM users_user")
            user_count = cursor.fetchone()[0]
            metrics_data.append(f'django_users_total {user_count}')
    except Exception:
        pass
    
    # Cache metrics
    try:
        cache_info = cache._cache.get_client().info()
        metrics_data.append(f'redis_connected_clients {cache_info.get("connected_clients", 0)}')
        metrics_data.append(f'redis_used_memory {cache_info.get("used_memory", 0)}')
    except Exception:
        pass
    
    # System metrics
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        metrics_data.append(f'system_cpu_percent {cpu_percent}')
        
        memory = psutil.virtual_memory()
        metrics_data.append(f'system_memory_percent {memory.percent}')
        
        disk = psutil.disk_usage('/')
        metrics_data.append(f'system_disk_percent {disk.percent}')
    except Exception:
        pass
    
    response = '\n'.join(metrics_data) + '\n'
    return JsonResponse({'metrics': response}, content_type='text/plain')


@require_http_methods(["GET"])
def system_info(request):
    """
    System information endpoint for debugging
    """
    info = {
        'django_version': settings.DJANGO_VERSION if hasattr(settings, 'DJANGO_VERSION') else 'Unknown',
        'python_version': os.sys.version,
        'debug': settings.DEBUG,
        'allowed_hosts': settings.ALLOWED_HOSTS,
        'database_engine': settings.DATABASES['default']['ENGINE'],
        'cache_backend': settings.CACHES['default']['BACKEND'],
        'timezone': settings.TIME_ZONE,
        'language_code': settings.LANGUAGE_CODE,
    }
    
    return JsonResponse(info)
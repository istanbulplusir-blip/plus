import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.prod')

app = Celery('istanbulplusir')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery configuration
app.conf.update(
    # Task routing
    task_routes={
        'users.tasks.cleanup_expired_data': {
            'queue': 'maintenance'
        },
        'users.tasks.optimize_database': {
            'queue': 'maintenance'
        },
        'users.tasks.generate_security_report': {
            'queue': 'reports'
        },
    },

    # Task scheduling
    beat_schedule={
        'cleanup-expired-data': {
            'task': 'users.tasks.cleanup_expired_data',
            'schedule': 3600.0,  # Every hour
        },
        'optimize-database': {
            'task': 'users.tasks.optimize_database',
            'schedule': 86400.0,  # Daily
        },
        'clear-rate-limit-cache': {
            'task': 'users.tasks.clear_rate_limit_cache',
            'schedule': 3600.0,  # Every hour
        },
        'generate-security-report': {
            'task': 'users.tasks.generate_security_report',
            'schedule': 604800.0,  # Weekly
        },
    },

    # Worker configuration
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,

    # Result backend
    result_backend='redis://127.0.0.1:6379/3',
    result_expires=3600,

    # Task serialization
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Tehran',
    enable_utc=True,
)


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
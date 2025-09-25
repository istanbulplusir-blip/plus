"""
URL patterns for security monitoring dashboard.
"""
from django.urls import path
from users.views.monitoring import (
    security_dashboard,
    security_logs_api,
    security_stats_api,
    unlock_user_account,
    block_ip_address
)

app_name = 'monitoring'

urlpatterns = [
    path('dashboard/', security_dashboard, name='security_dashboard'),
    path('logs-api/', security_logs_api, name='security_logs_api'),
    path('stats-api/', security_stats_api, name='security_stats_api'),
    path('unlock-user/', unlock_user_account, name='unlock_user'),
    path('block-ip/', block_ip_address, name='block_ip'),
]
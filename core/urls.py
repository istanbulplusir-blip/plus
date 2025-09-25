from django.urls import path
from .views import HomePageView, about, contact, health_check, metrics, system_info

app_name = 'core'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
    path('health/', health_check, name='health'),
    path('metrics/', metrics, name='metrics'),
    path('system-info/', system_info, name='system_info'),
]

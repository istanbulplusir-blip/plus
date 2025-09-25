from django.urls import path, include

app_name = 'payments'

urlpatterns = [
    path('api/', include('payments.urls.api', namespace='api')),
    path('', include('payments.urls.web', namespace='web')),
]
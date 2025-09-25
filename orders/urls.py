from django.urls import path, include

app_name = 'orders'

urlpatterns = [
    path('api/', include('orders.urls.api', namespace='api')),
    path('', include('orders.urls.web', namespace='web')),
]
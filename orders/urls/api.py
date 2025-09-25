from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.views.api import OrderViewSet

router = DefaultRouter()
router.register(r'', OrderViewSet, basename='orders')

app_name = 'api_orders'

urlpatterns = [
    path('', include(router.urls)),
]
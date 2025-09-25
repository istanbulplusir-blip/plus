from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views.api import PaymentViewSet

router = DefaultRouter()
router.register(r'', PaymentViewSet, basename='payments')

app_name = 'api_payments'

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path, include

urlpatterns = [
    path('api/', include('cart.urls.api')),
    path('', include('cart.urls.web')),
]
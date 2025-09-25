from django.urls import path
from cart.views.web import CartView

app_name = 'cart'

urlpatterns = [
    path('', CartView.as_view(), name='cart_detail'),
]
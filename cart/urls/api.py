from django.urls import path
from cart.views.api import (
    CartDetailAPIView, CartItemCreateAPIView,
    CartItemUpdateAPIView, CartItemDeleteAPIView,
    CartCountAPIView, CartTotalAPIView, CartTransferAPIView
)

app_name = 'api_cart'

urlpatterns = [
    path('', CartDetailAPIView.as_view(), name='cart_detail'),
    path('items/', CartItemCreateAPIView.as_view(), name='cart_item_create'),
    path('items/<int:pk>/update/', CartItemUpdateAPIView.as_view(), name='cart_item_update'),
    path('items/<int:pk>/delete/', CartItemDeleteAPIView.as_view(), name='cart_item_delete'),
    path('count/', CartCountAPIView.as_view(), name='cart_count'),
    path('total/', CartTotalAPIView.as_view(), name='cart_total'),
    path('transfer/', CartTransferAPIView.as_view(), name='cart_transfer'),
]
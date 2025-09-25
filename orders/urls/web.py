from django.urls import path
from orders.views.web import OrderListView, OrderDetailView, CheckoutView, CreateOrderView

app_name = 'orders'

urlpatterns = [
    path('', OrderListView.as_view(), name='order_list'),
    path('<int:pk>/', OrderDetailView.as_view(), name='order_detail'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('create/', CreateOrderView.as_view(), name='create_order'),
]
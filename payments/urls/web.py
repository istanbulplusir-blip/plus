from django.urls import path
from payments.views.web import (
    PaymentListView, PaymentDetailView, PaymentResultView,
    InitiatePaymentView, PaymentCallbackView, SimulatePaymentView,
    PaymentStatusAPIView
)
from payments.views.gateway_selection import GatewaySelectionView

app_name = 'payments'

urlpatterns = [
    path('', PaymentListView.as_view(), name='payment_list'),
    path('<int:pk>/', PaymentDetailView.as_view(), name='payment_detail'),
    path('result/<int:payment_id>/', PaymentResultView.as_view(), name='payment_result'),
    path('initiate/<int:order_id>/', InitiatePaymentView.as_view(), name='initiate_payment'),
    path('gateway/<int:order_id>/', GatewaySelectionView.as_view(), name='gateway_selection'),
    path('callback/', PaymentCallbackView.as_view(), name='payment_callback'),
    path('simulate/<int:payment_id>/', SimulatePaymentView.as_view(), name='simulate_payment'),
    path('status/<int:payment_id>/', PaymentStatusAPIView.as_view(), name='payment_status'),
]
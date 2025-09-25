from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from orders.models import Order
from payments.services import PaymentService
import logging

logger = logging.getLogger(__name__)


class GatewaySelectionView(LoginRequiredMixin, TemplateView):
    """
    View for selecting payment gateway
    """
    template_name = 'payments/gateway_selection.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        
        try:
            order = get_object_or_404(Order, id=order_id, user=self.request.user)
            context['order'] = order
            
            # Calculate total amount
            total_amount = 0
            for item in order.items.all():
                total_amount += item.price * item.quantity
            context['total_amount'] = total_amount
            
            # Available gateways
            context['gateways'] = [
                {
                    'name': 'zarinpal',
                    'title': 'زرین‌پال',
                    'description': 'پرداخت امن و سریع با زرین‌پال',
                    'icon': 'bi-credit-card',
                    'color': 'primary'
                },
                {
                    'name': 'idpay',
                    'title': 'آیدی پی',
                    'description': 'پرداخت آنلاین با آیدی پی',
                    'icon': 'bi-wallet2',
                    'color': 'success'
                },
                {
                    'name': 'nextpay',
                    'title': 'نکست پی',
                    'description': 'پرداخت سریع با نکست پی',
                    'icon': 'bi-paypal',
                    'color': 'info'
                }
            ]
            
        except Exception as e:
            logger.error(f"Gateway selection error: {str(e)}")
            messages.error(self.request, 'خطا در بارگذاری اطلاعات')
            context['order'] = None
        
        return context
    
    def post(self, request, order_id):
        """
        Handle gateway selection and initiate payment
        """
        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            gateway_name = request.POST.get('gateway')
            
            if not gateway_name:
                messages.error(request, 'لطفاً درگاه پرداخت را انتخاب کنید')
                return redirect('payments:gateway_selection', order_id=order_id)
            
            # Initiate payment with selected gateway
            result = PaymentService.initiate_payment(order, gateway_name)
            
            if result['success']:
                payment_id = result['payment_id']
                redirect_url = result.get('redirect_url')
                
                if redirect_url:
                    # Redirect to payment gateway
                    return redirect(redirect_url)
                else:
                    # Redirect to payment detail page
                    return redirect('payments:payment_detail', pk=payment_id)
            else:
                messages.error(request, result.get('error', 'خطا در آغاز پرداخت'))
                return redirect('payments:gateway_selection', order_id=order_id)
                
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            messages.error(request, 'خطا در سیستم پرداخت')
            return redirect('orders:order_detail', pk=order_id)

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, TemplateView, View
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from payments.models import Payment
from payments.services import PaymentService
from orders.models import Order
import logging

logger = logging.getLogger(__name__)


class PaymentListView(LoginRequiredMixin, ListView):
    model = Payment
    template_name = 'payments/payment_list.html'
    context_object_name = 'payments'

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)


class PaymentDetailView(LoginRequiredMixin, DetailView):
    model = Payment
    template_name = 'payments/payment_detail.html'
    context_object_name = 'payment'

    def get_queryset(self):
        return Payment.objects.filter(order__user=self.request.user)


class PaymentResultView(LoginRequiredMixin, TemplateView):
    template_name = 'payments/payment_result.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        payment_id = self.kwargs.get('payment_id')
        try:
            payment = Payment.objects.get(id=payment_id, order__user=self.request.user)
            context['payment'] = payment
            context['order'] = payment.order
        except Payment.DoesNotExist:
            context['payment'] = None
            context['order'] = None
        return context


class InitiatePaymentView(LoginRequiredMixin, View):
    """
    Initiate payment for an order
    """
    
    def post(self, request, order_id):
        try:
            order = get_object_or_404(Order, id=order_id, user=request.user)
            
            # Check if order is in pending status
            if order.status != 'pending':
                messages.error(request, 'این سفارش قابل پرداخت نیست')
                return redirect('orders:order_detail', pk=order.id)
            
            # Check if payment already exists
            existing_payment = Payment.objects.filter(order=order, status='initiated').first()
            if existing_payment:
                messages.info(request, 'پرداخت قبلاً آغاز شده است')
                return redirect('payments:payment_detail', pk=existing_payment.id)
            
            # Initiate payment
            result = PaymentService.initiate_payment(order)
            
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
                return redirect('orders:order_detail', pk=order.id)
                
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            messages.error(request, 'خطا در سیستم پرداخت')
            return redirect('orders:order_detail', pk=order_id)


class PaymentCallbackView(View):
    """
    Handle payment gateway callback for Iranian gateways
    """
    
    def get(self, request):
        payment_id = request.GET.get('payment_id')
        
        # Zarinpal callback parameters
        authority = request.GET.get('Authority')
        status = request.GET.get('Status')
        
        # IDPay callback parameters
        idpay_id = request.GET.get('id')
        idpay_order_id = request.GET.get('order_id')
        idpay_status = request.GET.get('status')
        
        # NextPay callback parameters
        trans_id = request.GET.get('trans_id')
        order_id = request.GET.get('order_id')
        nextpay_status = request.GET.get('status')
        
        if not payment_id:
            messages.error(request, 'اطلاعات پرداخت نامعتبر است')
            return redirect('orders:order_list')
        
        try:
            payment = Payment.objects.get(id=payment_id)
            gateway_name = None
            tracking_code = None
            
            # Determine gateway and tracking code based on callback parameters
            if authority and status:
                # Zarinpal callback
                gateway_name = 'zarinpal'
                tracking_code = authority
                if status != 'OK':
                    messages.error(request, 'پرداخت توسط کاربر لغو شد')
                    return redirect('orders:order_detail', pk=payment.order.id)
                    
            elif idpay_id and idpay_order_id:
                # IDPay callback
                gateway_name = 'idpay'
                tracking_code = idpay_id
                if idpay_status != '100':
                    messages.error(request, 'پرداخت ناموفق بود')
                    return redirect('orders:order_detail', pk=payment.order.id)
                    
            elif trans_id and order_id:
                # NextPay callback
                gateway_name = 'nextpay'
                tracking_code = trans_id
                if nextpay_status != '0':
                    messages.error(request, 'پرداخت ناموفق بود')
                    return redirect('orders:order_detail', pk=payment.order.id)
            
            # Verify payment
            result = PaymentService.verify_payment(payment_id, tracking_code, gateway_name)
            
            if result['success']:
                payment = result['payment']
                order = result['order']
                
                # Get appropriate tracking code for display
                display_code = payment.tracking_code
                if gateway_name == 'zarinpal' and 'gateway_response' in result:
                    display_code = result['gateway_response'].get('ref_id', payment.tracking_code)
                
                messages.success(request, f'پرداخت با موفقیت انجام شد. شماره پیگیری: {display_code}')
                return redirect('payments:payment_result', payment_id=payment.id)
            else:
                messages.error(request, result.get('error', 'پرداخت ناموفق بود'))
                return redirect('orders:order_detail', pk=payment.order.id)
                
        except Payment.DoesNotExist:
            messages.error(request, 'پرداخت یافت نشد')
            return redirect('orders:order_list')
        except Exception as e:
            logger.error(f"Payment callback failed: {str(e)}")
            messages.error(request, 'خطا در تایید پرداخت')
            return redirect('orders:order_list')


class SimulatePaymentView(LoginRequiredMixin, View):
    """
    Simulate payment in development mode
    """
    
    def get(self, request, payment_id):
        try:
            payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
            
            # Simulate payment verification
            result = PaymentService.verify_payment(payment_id)
            
            if result['success']:
                messages.success(request, 'پرداخت با موفقیت شبیه‌سازی شد')
                return redirect('payments:payment_result', payment_id=payment.id)
            else:
                messages.error(request, 'شبیه‌سازی پرداخت ناموفق بود')
                return redirect('orders:order_detail', pk=payment.order.id)
                
        except Exception as e:
            logger.error(f"Payment simulation failed: {str(e)}")
            messages.error(request, 'خطا در شبیه‌سازی پرداخت')
            return redirect('orders:order_list')


class PaymentStatusAPIView(LoginRequiredMixin, View):
    """
    API endpoint to check payment status
    """
    
    def get(self, request, payment_id):
        try:
            result = PaymentService.get_payment_status(payment_id)
            
            if result['success']:
                payment = result['payment']
                # Check if user owns this payment
                if payment.order.user != request.user:
                    return JsonResponse({'error': 'دسترسی غیرمجاز'}, status=403)
                
                return JsonResponse({
                    'success': True,
                    'status': payment.status,
                    'amount': payment.amount,
                    'tracking_code': payment.tracking_code,
                    'created_at': payment.created_at.isoformat()
                })
            else:
                return JsonResponse({'error': result['error']}, status=404)
                
        except Exception as e:
            logger.error(f"Payment status check failed: {str(e)}")
            return JsonResponse({'error': 'خطا در سیستم'}, status=500)
from django.conf import settings
from orders.models import Order
from payments.models import Payment
from payments.gateways import PaymentGatewayFactory
import requests
import json
import logging
from decimal import Decimal
import uuid

logger = logging.getLogger(__name__)


class PaymentService:
    """
    Service for handling payment operations with Iranian gateways
    """
    
    # Default gateway configuration
    DEFAULT_GATEWAY = getattr(settings, 'DEFAULT_PAYMENT_GATEWAY', 'zarinpal')
    CALLBACK_URL = getattr(settings, 'PAYMENT_CALLBACK_URL', 'http://localhost:8000/payments/callback/')
    
    @classmethod
    def initiate_payment(cls, order, gateway_name=None):
        """
        Initiate payment for an order using Iranian payment gateways
        
        Args:
            order: Order instance
            gateway_name: Specific gateway to use (optional)
            
        Returns:
            dict: Payment response with redirect URL or error
        """
        try:
            # Calculate total amount
            total_amount = cls._calculate_order_total(order)
            
            if total_amount <= 0:
                return {
                    'success': False,
                    'error': 'مبلغ سفارش نامعتبر است'
                }
            
            # Create payment record
            payment = Payment.objects.create(
                order=order,
                amount=total_amount,
                status='initiated'
            )
            
            # Use specified gateway or default
            gateway_name = gateway_name or cls.DEFAULT_GATEWAY
            gateway = PaymentGatewayFactory.get_gateway(gateway_name)
            
            if not gateway:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_name} پشتیبانی نمی‌شود'
                }
            
            # In development mode, simulate payment
            if settings.DEBUG and not getattr(settings, 'USE_REAL_GATEWAY', False):
                return cls._simulate_payment(payment, gateway_name)
            
            # Prepare callback URL with payment ID
            callback_url = f"{cls.CALLBACK_URL}?payment_id={payment.id}"
            
            # Request payment based on gateway type
            if gateway_name.lower() == 'zarinpal':
                response = gateway.request_payment(
                    amount=total_amount,
                    description=f'پرداخت سفارش #{order.id}',
                    callback_url=callback_url,
                    mobile=order.billing_phone,
                    email=order.user.email if order.user.email else None
                )
                
                if response.get('success'):
                    payment.tracking_code = response.get('authority')
                    payment.raw_response = json.dumps(response)
                    payment.save()
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'redirect_url': response.get('redirect_url'),
                        'tracking_code': payment.tracking_code,
                        'gateway': 'zarinpal'
                    }
                    
            elif gateway_name.lower() == 'idpay':
                response = gateway.request_payment(
                    amount=total_amount,
                    order_id=order.id,
                    description=f'پرداخت سفارش #{order.id}',
                    callback_url=callback_url,
                    name=order.billing_name,
                    phone=order.billing_phone,
                    mail=order.user.email if order.user.email else None
                )
                
                if response.get('success'):
                    payment.tracking_code = response.get('payment_id')
                    payment.raw_response = json.dumps(response)
                    payment.save()
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'redirect_url': response.get('redirect_url'),
                        'tracking_code': payment.tracking_code,
                        'gateway': 'idpay'
                    }
                    
            elif gateway_name.lower() == 'nextpay':
                response = gateway.request_payment(
                    amount=total_amount,
                    order_id=order.id,
                    description=f'پرداخت سفارش #{order.id}',
                    callback_url=callback_url,
                    customer_phone=order.billing_phone
                )
                
                if response.get('success'):
                    payment.tracking_code = response.get('trans_id')
                    payment.raw_response = json.dumps(response)
                    payment.save()
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'redirect_url': response.get('redirect_url'),
                        'tracking_code': payment.tracking_code,
                        'gateway': 'nextpay'
                    }
            
            # If we reach here, payment request failed
            payment.status = 'failed'
            payment.raw_response = json.dumps(response)
            payment.save()
            
            return {
                'success': False,
                'error': response.get('error', 'خطا در پردازش پرداخت')
            }
                
        except Exception as e:
            logger.error(f"Payment initiation failed for order {order.id}: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در سیستم پرداخت'
            }
    
    @classmethod
    def verify_payment(cls, payment_id, tracking_code=None, gateway_name=None):
        """
        Verify payment status with Iranian payment gateways
        
        Args:
            payment_id: Payment ID
            tracking_code: Payment tracking code (authority, trans_id, etc.)
            gateway_name: Gateway name (optional)
            
        Returns:
            dict: Verification result
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            
            # In development mode, simulate verification
            if settings.DEBUG and not getattr(settings, 'USE_REAL_GATEWAY', False):
                return cls._simulate_payment_verification(payment)
            
            # Use specified gateway or default
            gateway_name = gateway_name or cls.DEFAULT_GATEWAY
            gateway = PaymentGatewayFactory.get_gateway(gateway_name)
            
            if not gateway:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_name} پشتیبانی نمی‌شود'
                }
            
            # Verify payment based on gateway type
            if gateway_name.lower() == 'zarinpal':
                response = gateway.verify_payment(
                    authority=tracking_code or payment.tracking_code,
                    amount=payment.amount
                )
                
            elif gateway_name.lower() == 'idpay':
                response = gateway.verify_payment(
                    payment_id=tracking_code or payment.tracking_code,
                    order_id=payment.order.id,
                    amount=payment.amount
                )
                
            elif gateway_name.lower() == 'nextpay':
                response = gateway.verify_payment(
                    trans_id=tracking_code or payment.tracking_code,
                    amount=payment.amount,
                    order_id=payment.order.id
                )
            else:
                return {
                    'success': False,
                    'error': f'درگاه پرداخت {gateway_name} پشتیبانی نمی‌شود'
                }
            
            if response.get('success'):
                payment.status = 'success'
                payment.raw_response = json.dumps(response)
                payment.save()
                
                # Update order status
                order = payment.order
                order.status = 'paid'
                order.save()
                
                # Send notification email
                from core.services import NotificationService
                NotificationService.send_payment_success_email(order.user, payment)
                
                return {
                    'success': True,
                    'payment': payment,
                    'order': order,
                    'gateway_response': response
                }
            else:
                payment.status = 'failed'
                payment.raw_response = json.dumps(response)
                payment.save()
                
                return {
                    'success': False,
                    'error': response.get('error', 'پرداخت ناموفق')
                }
                
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'پرداخت یافت نشد'
            }
        except Exception as e:
            logger.error(f"Payment verification failed: {str(e)}")
            return {
                'success': False,
                'error': 'خطا در تایید پرداخت'
            }
    
    @classmethod
    def _calculate_order_total(cls, order):
        """
        Calculate total amount for order
        
        Args:
            order: Order instance
            
        Returns:
            int: Total amount in Toman
        """
        total = 0
        for item in order.items.all():
            total += item.price * item.quantity
        return total
    
    
    @classmethod
    def _simulate_payment(cls, payment, gateway_name):
        """
        Simulate payment in development mode
        
        Args:
            payment: Payment instance
            gateway_name: Gateway name for simulation
            
        Returns:
            dict: Simulated payment response
        """
        # Generate tracking code based on gateway
        if gateway_name.lower() == 'zarinpal':
            tracking_code = f"A00000000000000000000000000000000000000000"
        elif gateway_name.lower() == 'idpay':
            tracking_code = f"SIM_{uuid.uuid4().hex[:12].upper()}"
        elif gateway_name.lower() == 'nextpay':
            tracking_code = f"SIM_{uuid.uuid4().hex[:12].upper()}"
        else:
            tracking_code = f"SIM_{uuid.uuid4().hex[:12].upper()}"
        
        payment.tracking_code = tracking_code
        payment.raw_response = json.dumps({
            'gateway': gateway_name,
            'simulation': True,
            'amount': payment.amount
        })
        payment.save()
        
        return {
            'success': True,
            'payment_id': payment.id,
            'redirect_url': f'/payments/simulate/{payment.id}/',
            'tracking_code': tracking_code,
            'gateway': gateway_name
        }
    
    @classmethod
    def _simulate_payment_verification(cls, payment):
        """
        Simulate payment verification in development mode
        
        Args:
            payment: Payment instance
            
        Returns:
            dict: Simulated verification response
        """
        # Simulate successful payment
        payment.status = 'success'
        payment.save()
        
        # Update order status
        order = payment.order
        order.status = 'paid'
        order.save()
        
        return {
            'success': True,
            'payment': payment,
            'order': order
        }
    
    @classmethod
    def get_payment_status(cls, payment_id):
        """
        Get payment status
        
        Args:
            payment_id: Payment ID
            
        Returns:
            dict: Payment status information
        """
        try:
            payment = Payment.objects.get(id=payment_id)
            return {
                'success': True,
                'payment': payment,
                'order': payment.order,
                'status': payment.status
            }
        except Payment.DoesNotExist:
            return {
                'success': False,
                'error': 'پرداخت یافت نشد'
            }

from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """
    Service for sending notifications to users
    """
    
    @staticmethod
    def send_order_confirmation_email(user, order):
        """
        Send order confirmation email
        
        Args:
            user: User instance
            order: Order instance
        """
        try:
            subject = f'تایید سفارش #{order.id}'
            
            context = {
                'user': user,
                'order': order,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            }
            
            html_message = render_to_string('emails/order_confirmation.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Order confirmation email sent to {user.email} for order {order.id}")
            
        except Exception as e:
            logger.error(f"Failed to send order confirmation email: {str(e)}")
    
    @staticmethod
    def send_payment_success_email(user, payment):
        """
        Send payment success email
        
        Args:
            user: User instance
            payment: Payment instance
        """
        try:
            subject = f'تایید پرداخت سفارش #{payment.order.id}'
            
            context = {
                'user': user,
                'payment': payment,
                'order': payment.order,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            }
            
            html_message = render_to_string('emails/payment_success.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Payment success email sent to {user.email} for payment {payment.id}")
            
        except Exception as e:
            logger.error(f"Failed to send payment success email: {str(e)}")
    
    @staticmethod
    def send_payment_failed_email(user, payment):
        """
        Send payment failed email
        
        Args:
            user: User instance
            payment: Payment instance
        """
        try:
            subject = f'خطا در پرداخت سفارش #{payment.order.id}'
            
            context = {
                'user': user,
                'payment': payment,
                'order': payment.order,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            }
            
            html_message = render_to_string('emails/payment_failed.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Payment failed email sent to {user.email} for payment {payment.id}")
            
        except Exception as e:
            logger.error(f"Failed to send payment failed email: {str(e)}")
    
    @staticmethod
    def send_order_status_update_email(user, order, old_status, new_status):
        """
        Send order status update email
        
        Args:
            user: User instance
            order: Order instance
            old_status: Previous status
            new_status: New status
        """
        try:
            subject = f'به‌روزرسانی وضعیت سفارش #{order.id}'
            
            context = {
                'user': user,
                'order': order,
                'old_status': old_status,
                'new_status': new_status,
                'site_url': getattr(settings, 'SITE_URL', 'http://localhost:8000')
            }
            
            html_message = render_to_string('emails/order_status_update.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject=subject,
                message=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                html_message=html_message,
                fail_silently=False
            )
            
            logger.info(f"Order status update email sent to {user.email} for order {order.id}")
            
        except Exception as e:
            logger.error(f"Failed to send order status update email: {str(e)}")
    
    @staticmethod
    def send_sms_notification(phone_number, message):
        """
        Send SMS notification (placeholder for SMS service integration)
        
        Args:
            phone_number: Phone number
            message: SMS message
        """
        try:
            # TODO: Integrate with SMS service provider
            logger.info(f"SMS sent to {phone_number}: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send SMS: {str(e)}")
            return False

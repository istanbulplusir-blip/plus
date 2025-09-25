"""
Email service for sending various types of emails including OTP, verification, and security alerts.
"""
import logging
from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EmailService:
    """Service class for handling email operations"""
    
    @staticmethod
    def _send_email(
        subject: str,
        recipient: str,
        template_name: str,
        context: Dict[str, Any],
        from_email: Optional[str] = None
    ) -> bool:
        """
        Send an email using HTML template with fallback to plain text.
        
        Args:
            subject: Email subject
            recipient: Recipient email address
            template_name: Template name (without .html extension)
            context: Template context variables
            from_email: Sender email (uses DEFAULT_FROM_EMAIL if None)
            
        Returns:
            bool: True if email sent successfully, False otherwise
        """
        try:
            from_email = from_email or getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@istanbulplus.ir')
            
            # Render HTML template
            html_content = render_to_string(f'emails/{template_name}.html', context)
            
            # Create plain text version by stripping HTML tags
            text_content = strip_tags(html_content)
            
            # Create email message
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=from_email,
                to=[recipient]
            )
            
            # Attach HTML version
            email.attach_alternative(html_content, "text/html")
            
            # Send email
            email.send()
            
            logger.info(f"Email sent successfully to {recipient} with subject: {subject}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp_email(email: str, code: str, purpose: str = 'login') -> bool:
        """
        Send OTP code via email.
        
        Args:
            email: Recipient email address
            code: OTP code to send
            purpose: Purpose of OTP (login, register, etc.)
            
        Returns:
            bool: True if email sent successfully
        """
        purpose_titles = {
            'login': 'ورود به حساب کاربری',
            'register': 'تأیید ثبت‌نام',
            'password_reset': 'بازیابی رمز عبور',
            'email_verify': 'تأیید ایمیل',
            'phone_verify': 'تأیید شماره موبایل'
        }
        
        subject = f"کد تأیید - {purpose_titles.get(purpose, 'احراز هویت')}"
        
        context = {
            'code': code,
            'purpose': purpose,
            'purpose_title': purpose_titles.get(purpose, 'احراز هویت'),
            'expiry_minutes': getattr(settings, 'OTP_CODE_EXPIRY_MINUTES', 5),
            'site_name': 'استانبول پلاس'
        }
        
        return EmailService._send_email(
            subject=subject,
            recipient=email,
            template_name='otp_code',
            context=context
        )
    
    @staticmethod
    def send_verification_email(user, verification_token: str) -> bool:
        """
        Send email verification link.
        
        Args:
            user: User instance
            verification_token: Verification token
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "تأیید ایمیل - استانبول پلاس"
        
        # Build verification URL
        verification_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/auth/verify-email/{verification_token}/"
        
        context = {
            'user': user,
            'verification_url': verification_url,
            'site_name': 'استانبول پلاس'
        }
        
        return EmailService._send_email(
            subject=subject,
            recipient=user.email,
            template_name='email_verification',
            context=context
        )
    
    @staticmethod
    def send_password_reset_email(user, reset_token: str) -> bool:
        """
        Send password reset link.
        
        Args:
            user: User instance
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "بازیابی رمز عبور - استانبول پلاس"
        
        # Build reset URL
        reset_url = f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/auth/password-reset/confirm/{reset_token}/"
        
        context = {
            'user': user,
            'reset_url': reset_url,
            'expiry_hours': 24,  # Password reset tokens typically expire in 24 hours
            'site_name': 'استانبول پلاس'
        }
        
        return EmailService._send_email(
            subject=subject,
            recipient=user.email,
            template_name='password_reset',
            context=context
        )
    
    @staticmethod
    def send_security_alert(user, event: str, ip_address: str, details: Optional[Dict] = None) -> bool:
        """
        Send security alert email.
        
        Args:
            user: User instance
            event: Security event type
            ip_address: IP address of the event
            details: Additional event details
            
        Returns:
            bool: True if email sent successfully
        """
        event_titles = {
            'login_from_new_location': 'ورود از مکان جدید',
            'password_changed': 'تغییر رمز عبور',
            'account_locked': 'قفل شدن حساب کاربری',
            'suspicious_activity': 'فعالیت مشکوک',
            'multiple_failed_logins': 'تلاش‌های ناموفق متعدد برای ورود'
        }
        
        subject = f"هشدار امنیتی - {event_titles.get(event, 'رویداد امنیتی')}"
        
        context = {
            'user': user,
            'event': event,
            'event_title': event_titles.get(event, 'رویداد امنیتی'),
            'ip_address': ip_address,
            'details': details or {},
            'site_name': 'استانبول پلاس'
        }
        
        return EmailService._send_email(
            subject=subject,
            recipient=user.email,
            template_name='security_alert',
            context=context
        )
    
    @staticmethod
    def send_welcome_email(user) -> bool:
        """
        Send welcome email to new users.
        
        Args:
            user: User instance
            
        Returns:
            bool: True if email sent successfully
        """
        subject = "خوش آمدید به استانبول پلاس"
        
        context = {
            'user': user,
            'site_name': 'استانبول پلاس',
            'login_url': f"{getattr(settings, 'SITE_URL', 'http://localhost:8000')}/auth/login/"
        }
        
        return EmailService._send_email(
            subject=subject,
            recipient=user.email,
            template_name='welcome',
            context=context
        )
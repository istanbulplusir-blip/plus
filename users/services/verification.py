"""
Verification service for handling email and phone verification.
"""
import secrets
import logging
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from typing import Optional, Tuple
from users.models import User, EmailVerificationToken
from users.services.email import EmailService
from users.services.otp import OTPService
from users.services.security import SecurityService

logger = logging.getLogger(__name__)


class VerificationService:
    """Service class for handling email and phone verification"""
    
    @staticmethod
    def generate_verification_token() -> str:
        """Generate a secure verification token"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def send_email_verification(
        user,
        email: Optional[str] = None,
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str]:
        """
        Send email verification link.
        
        Args:
            user: User instance
            email: Email to verify (defaults to user.email)
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            email = email or user.email
            if not email:
                return False, "No email address provided"
            
            # Check rate limiting
            if not SecurityService.check_rate_limit(ip_address, 'email_verification')[0]:
                return False, "تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید."
            
            # Generate verification token
            token = VerificationService.generate_verification_token()
            
            # Set expiry time (24 hours)
            expiry_hours = getattr(settings, 'EMAIL_VERIFICATION_EXPIRY_HOURS', 24)
            expires_at = timezone.now() + timedelta(hours=expiry_hours)
            
            # Invalidate previous unused tokens for the same email
            EmailVerificationToken.objects.filter(
                user=user,
                email=email,
                used=False
            ).update(used=True)
            
            # Create new verification token
            verification_token = EmailVerificationToken.objects.create(
                user=user,
                email=email,
                token=token,
                expires_at=expires_at,
                ip_address=ip_address
            )
            
            # Send verification email
            success = EmailService.send_verification_email(user, token)
            
            if success:
                # Log security event
                SecurityService.log_security_event(
                    event_type='email_verification_sent',
                    ip_address=ip_address,
                    user=user,
                    severity='low',
                    details={'email': email}
                )
                
                logger.info(f"Email verification sent to {email} for user {user.username}")
                return True, "لینک تأیید ایمیل با موفقیت ارسال شد."
            else:
                # Delete the token if sending failed
                verification_token.delete()
                return False, "خطا در ارسال ایمیل تأیید. لطفاً دوباره تلاش کنید."
                
        except Exception as e:
            logger.error(f"Error in send_email_verification: {str(e)}")
            return False, "خطای سیستمی رخ داده است."
    
    @staticmethod
    def verify_email(
        token: str,
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str, Optional[User]]:
        """
        Verify email using verification token.
        
        Args:
            token: Verification token
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str, Optional[User]]: (success, message, user)
        """
        try:
            # Find the verification token
            verification_token = EmailVerificationToken.objects.filter(
                token=token
            ).first()
            
            if not verification_token:
                return False, "لینک تأیید نامعتبر است.", None
            
            # Check if token is still valid
            if not verification_token.is_valid():
                if verification_token.is_expired():
                    return False, "لینک تأیید منقضی شده است.", None
                else:
                    return False, "لینک تأیید قبلاً استفاده شده است.", None
            
            # Mark token as used
            verification_token.mark_as_used()
            
            # Update user's email verification status
            user = verification_token.user
            user.email_verified = True
            user.email = verification_token.email  # Update email in case it was changed
            user.save(update_fields=['email_verified', 'email'])
            
            # Log security event
            SecurityService.log_security_event(
                event_type='email_verified',
                ip_address=ip_address,
                user=user,
                severity='low',
                details={'email': verification_token.email}
            )
            
            logger.info(f"Email verified successfully for user {user.username}")
            return True, "ایمیل با موفقیت تأیید شد.", user
            
        except Exception as e:
            logger.error(f"Error in verify_email: {str(e)}")
            return False, "خطای سیستمی رخ داده است.", None
    
    @staticmethod
    def send_phone_verification(
        user,
        phone: Optional[str] = None,
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str]:
        """
        Send phone verification OTP.
        
        Args:
            user: User instance
            phone: Phone number to verify (defaults to user.phone)
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            phone = phone or user.phone
            if not phone:
                return False, "No phone number provided"
            
            # Send OTP via SMS
            success, message = OTPService.send_otp(
                contact_info=phone,
                delivery_method='sms',
                purpose='phone_verify',
                user=user,
                ip_address=ip_address
            )
            
            if success:
                # Log security event
                SecurityService.log_security_event(
                    event_type='phone_verification_sent',
                    ip_address=ip_address,
                    user=user,
                    severity='low',
                    details={'phone': phone}
                )
                
                logger.info(f"Phone verification OTP sent to {phone} for user {user.username}")
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error in send_phone_verification: {str(e)}")
            return False, "خطای سیستمی رخ داده است."
    
    @staticmethod
    def verify_phone(
        user,
        phone: str,
        otp_code: str,
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str]:
        """
        Verify phone using OTP code.
        
        Args:
            user: User instance
            phone: Phone number to verify
            otp_code: OTP code
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Verify OTP
            success, message, otp_obj = OTPService.verify_otp(
                contact_info=phone,
                code=otp_code,
                purpose='phone_verify',
                ip_address=ip_address
            )
            
            if success:
                # Update user's phone verification status
                user.phone_verified = True
                user.phone = phone  # Update phone in case it was changed
                user.save(update_fields=['phone_verified', 'phone'])
                
                # Log security event
                SecurityService.log_security_event(
                    event_type='phone_verified',
                    ip_address=ip_address,
                    user=user,
                    severity='low',
                    details={'phone': phone}
                )
                
                logger.info(f"Phone verified successfully for user {user.username}")
                return True, "شماره موبایل با موفقیت تأیید شد."
            
            return success, message
            
        except Exception as e:
            logger.error(f"Error in verify_phone: {str(e)}")
            return False, "خطای سیستمی رخ داده است."
    
    @staticmethod
    def cleanup_expired_tokens():
        """Clean up expired email verification tokens"""
        try:
            expired_count = EmailVerificationToken.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            logger.info(f"Cleaned up {expired_count} expired email verification tokens")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired tokens: {str(e)}")
            return 0
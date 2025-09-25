"""
OTP service for sending and verifying OTP codes via SMS and Email.
"""
import random
import requests
import logging
from django.conf import settings
from django.utils import timezone
from django.core.cache import cache
from datetime import timedelta
from typing import Optional, Tuple
from users.models import OtpCode, generate_hash

logger = logging.getLogger(__name__)


class OTPService:
    """Service class for handling OTP operations"""
    
    @staticmethod
    def generate_otp() -> str:
        """Generate a 6-digit OTP code"""
        return str(random.randint(100000, 999999))
    
    @staticmethod
    def _check_rate_limit(contact_info: str, ip_address: str) -> bool:
        """
        Check if rate limit is exceeded for OTP requests.
        
        Args:
            contact_info: Email or phone number
            ip_address: IP address of the request
            
        Returns:
            bool: True if within rate limit, False if exceeded
        """
        max_per_hour = getattr(settings, 'OTP_MAX_SEND_PER_HOUR', 5)
        
        # Check rate limit by contact info
        contact_key = f"otp_rate_limit_contact_{contact_info}"
        contact_count = cache.get(contact_key, 0)
        
        # Check rate limit by IP
        ip_key = f"otp_rate_limit_ip_{ip_address}"
        ip_count = cache.get(ip_key, 0)
        
        if contact_count >= max_per_hour or ip_count >= max_per_hour:
            logger.warning(f"Rate limit exceeded for {contact_info} from IP {ip_address}")
            return False
        
        return True
    
    @staticmethod
    def _increment_rate_limit(contact_info: str, ip_address: str):
        """Increment rate limit counters"""
        contact_key = f"otp_rate_limit_contact_{contact_info}"
        ip_key = f"otp_rate_limit_ip_{ip_address}"
        
        # Increment counters with 1 hour expiry
        cache.set(contact_key, cache.get(contact_key, 0) + 1, 3600)
        cache.set(ip_key, cache.get(ip_key, 0) + 1, 3600)
    
    @staticmethod
    def _send_sms(phone: str, code: str, purpose: str) -> bool:
        """
        Send OTP via SMS.
        
        Args:
            phone: Phone number
            code: OTP code
            purpose: Purpose of OTP
            
        Returns:
            bool: True if SMS sent successfully
        """
        try:
            if settings.DEBUG or getattr(settings, 'OTP_SMS_BACKEND', 'kavenegar') == 'dev':
                # Development mode - print to console
                print(f"SMS OTP for {phone} ({purpose}): {code}")
                return True
            
            # Production mode - use Kavenegar API
            api_key = getattr(settings, 'KAVENEGAR_API_KEY', '')
            if not api_key:
                logger.error("KAVENEGAR_API_KEY not configured")
                return False
            
            url = f'https://api.kavenegar.com/v1/{api_key}/sms/send.json'
            
            # Create Persian message based on purpose
            purpose_messages = {
                'login': f'کد ورود شما: {code}',
                'register': f'کد تأیید ثبت‌نام: {code}',
                'password_reset': f'کد بازیابی رمز عبور: {code}',
                'phone_verify': f'کد تأیید شماره موبایل: {code}'
            }
            
            message = purpose_messages.get(purpose, f'کد تأیید شما: {code}')
            
            data = {
                'sender': getattr(settings, 'SMS_SENDER_NUMBER', '10004346'),
                'receptor': phone.replace('+', ''),
                'message': message
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 200:
                logger.info(f"SMS sent successfully to {phone}")
                return True
            else:
                logger.error(f"Failed to send SMS to {phone}: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending SMS to {phone}: {str(e)}")
            return False
    
    @staticmethod
    def send_otp(
        contact_info: str,
        delivery_method: str = 'sms',
        purpose: str = 'login',
        user=None,
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str]:
        """
        Send OTP code via SMS or Email.
        
        Args:
            contact_info: Email or phone number
            delivery_method: 'sms' or 'email'
            purpose: Purpose of OTP
            user: User instance (optional)
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str]: (success, error_message)
        """
        try:
            # Check rate limiting
            if not OTPService._check_rate_limit(contact_info, ip_address):
                return False, "تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید."
            
            # Generate OTP code
            code = OTPService.generate_otp()
            hashed_code = generate_hash(code)
            
            # Log OTP code for testing purposes
            logger.info(f"🔐 OTP CODE GENERATED: {code} for {contact_info} (purpose: {purpose})")
            print(f"🔐 OTP CODE FOR TESTING: {code} - Contact: {contact_info} - Purpose: {purpose}")
            
            # Set expiry time
            expiry_minutes = getattr(settings, 'OTP_CODE_EXPIRY_MINUTES', 5)
            
            # Also print in a more visible format for testing
            print("=" * 60)
            print(f"🔐 OTP CODE FOR REGISTRATION: {code}")
            print(f"📧 Contact: {contact_info}")
            print(f"🎯 Purpose: {purpose}")
            print(f"⏰ Expires in: {expiry_minutes} minutes")
            print("=" * 60)
            expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
            
            # Invalidate previous unused OTP codes for the same contact and purpose
            OtpCode.objects.filter(
                contact_info=contact_info,
                purpose=purpose,
                used=False
            ).update(used=True)
            
            # Create new OTP record
            otp_obj = OtpCode.objects.create(
                user=user,
                contact_info=contact_info,
                delivery_method=delivery_method,
                hashed_code=hashed_code,
                purpose=purpose,
                expires_at=expires_at,
                ip_address=ip_address
            )
            
            # Send OTP based on delivery method
            if delivery_method == 'sms':
                success = OTPService._send_sms(contact_info, code, purpose)
            elif delivery_method == 'email':
                from users.services.email import EmailService
                success = EmailService.send_otp_email(contact_info, code, purpose)
            else:
                return False, "روش ارسال نامعتبر است."
            
            if success:
                # Increment rate limit counters
                OTPService._increment_rate_limit(contact_info, ip_address)
                logger.info(f"OTP sent successfully to {contact_info} via {delivery_method}")
                return True, "کد تأیید با موفقیت ارسال شد."
            else:
                # Delete the OTP record if sending failed
                otp_obj.delete()
                return False, "خطا در ارسال کد تأیید. لطفاً دوباره تلاش کنید."
                
        except Exception as e:
            logger.error(f"Error in send_otp: {str(e)}")
            return False, "خطای سیستمی رخ داده است."
    
    @staticmethod
    def verify_otp(
        contact_info: str,
        code: str,
        purpose: str = 'login',
        ip_address: str = '127.0.0.1'
    ) -> Tuple[bool, str, Optional[object]]:
        """
        Verify OTP code.
        
        Args:
            contact_info: Email or phone number
            code: OTP code to verify
            purpose: Purpose of OTP
            ip_address: IP address of the request
            
        Returns:
            Tuple[bool, str, Optional[OtpCode]]: (success, message, otp_object)
        """
        try:
            # Find the latest unused OTP for this contact and purpose
            otp_obj = OtpCode.objects.filter(
                contact_info=contact_info,
                purpose=purpose,
                used=False
            ).order_by('-created_at').first()
            
            if not otp_obj:
                return False, "کد تأیید یافت نشد یا منقضی شده است.", None
            
            # Check if OTP is still valid
            if not otp_obj.is_valid():
                if otp_obj.is_expired():
                    return False, "کد تأیید منقضی شده است.", None
                elif otp_obj.attempts >= getattr(settings, 'OTP_MAX_VERIFY_ATTEMPTS', 3):
                    return False, "تعداد تلاش‌های شما از حد مجاز گذشته است.", None
                else:
                    return False, "کد تأیید نامعتبر است.", None
            
            # Verify the code
            if otp_obj.verify_code(code):
                # Mark as used
                otp_obj.mark_as_used()
                logger.info(f"OTP verified successfully for {contact_info}")
                return True, "کد تأیید با موفقیت تأیید شد.", otp_obj
            else:
                # Increment attempts
                otp_obj.increment_attempts()
                remaining_attempts = getattr(settings, 'OTP_MAX_VERIFY_ATTEMPTS', 3) - otp_obj.attempts
                
                if remaining_attempts > 0:
                    return False, f"کد تأیید اشتباه است. {remaining_attempts} تلاش باقی مانده.", None
                else:
                    return False, "تعداد تلاش‌های شما از حد مجاز گذشته است.", None
                    
        except Exception as e:
            logger.error(f"Error in verify_otp: {str(e)}")
            return False, "خطای سیستمی رخ داده است.", None
    
    @staticmethod
    def cleanup_expired_otps():
        """Clean up expired OTP codes"""
        try:
            expired_count = OtpCode.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            logger.info(f"Cleaned up {expired_count} expired OTP codes")
            return expired_count
            
        except Exception as e:
            logger.error(f"Error cleaning up expired OTPs: {str(e)}")
            return 0


# Backward compatibility functions
def generate_otp():
    """Backward compatibility function"""
    return OTPService.generate_otp()


def send_otp(phone, purpose='login'):
    """Backward compatibility function for SMS only"""
    success, message = OTPService.send_otp(
        contact_info=phone,
        delivery_method='sms',
        purpose=purpose
    )
    return success


def verify_otp(phone, code, purpose='login'):
    """Backward compatibility function"""
    success, message, otp_obj = OTPService.verify_otp(
        contact_info=phone,
        code=code,
        purpose=purpose
    )
    return success

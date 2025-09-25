import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.utils import timezone
from users.serializers import (
    RegisterSerializer, UserProfileSerializer, LoginSerializer,
    SendOtpSerializer, VerifyOtpSerializer, PasswordResetRequestSerializer,
    PasswordResetVerifySerializer, PasswordResetConfirmSerializer,
    SendEmailVerificationSerializer, VerifyEmailSerializer,
    SendPhoneVerificationSerializer, VerifyPhoneSerializer,
    ResendVerificationSerializer, Step1ContactSerializer, 
    Step1OTPVerifySerializer, Step2PersonalInfoSerializer, Step3PasswordSerializer
)
from users.services.otp import OTPService
from users.services.security import SecurityService
from users.services.verification import VerificationService

logger = logging.getLogger(__name__)

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class RegisterAPIView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    queryset = User.objects.all()
    permission_classes = []  # Allow anonymous registration

    def create(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting for registration
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='registration'
        )
        
        if not is_allowed:
            SecurityService.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=ip_address,
                severity='medium',
                user_agent=user_agent,
                details={'action': 'registration', 'rate_info': rate_info}
            )
            return Response({
                'success': False,
                'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 3600)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user
        user = serializer.save()
        
        # Increment rate limit counter
        SecurityService.increment_rate_limit(ip_address, 'registration')
        
        # Log security event
        SecurityService.log_security_event(
            event_type='user_registered',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent=user_agent,
            details={
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified,
                'registration_method': 'standard'
            }
        )
        
        # Generate JWT tokens for immediate login
        refresh = RefreshToken.for_user(user)
        
        # Create user session record
        self._create_user_session(user, request, ip_address, user_agent)
        
        # Get smart redirect URL
        from users.services.redirect import SmartRedirectService
        redirect_url = SmartRedirectService.get_smart_redirect_url(request, user, is_registration=True)
        
        return Response({
            'success': True,
            'message': 'ثبت‌نام با موفقیت انجام شد.',
            'redirect_url': redirect_url,
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'avatar': user.avatar.url if user.avatar else None,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified,
                'two_factor_enabled': user.two_factor_enabled
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'verification_status': {
                'email_verification_sent': bool(user.email and not user.email_verified),
                'phone_verified': user.phone_verified,
                'next_steps': self._get_next_verification_steps(user)
            }
        }, status=status.HTTP_201_CREATED)
    
    def _create_user_session(self, user, request, ip_address, user_agent):
        """Create user session record for tracking"""
        try:
            from users.models import UserSession
            session_key = request.session.session_key or 'api_session'
            
            # Try to get location from IP
            location = ''
            try:
                from django.contrib.gis.geoip2 import GeoIP2
                g = GeoIP2()
                location_data = g.city(ip_address)
                if location_data:
                    city = location_data.get('city', '')
                    country = location_data.get('country_name', '')
                    location = f"{city}, {country}" if city and country else country
            except Exception:
                pass
            
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                location=location
            )
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
    
    def _get_next_verification_steps(self, user):
        """Get next verification steps for the user"""
        steps = []
        if user.email and not user.email_verified:
            steps.append({
                'type': 'email',
                'message': 'لطفاً ایمیل خود را بررسی کرده و روی لینک تأیید کلیک کنید.',
                'action': 'check_email'
            })
        if user.phone and not user.phone_verified:
            steps.append({
                'type': 'phone',
                'message': 'شماره موبایل شما هنوز تأیید نشده است.',
                'action': 'verify_phone'
            })
        return steps


class LoginAPIView(APIView):
    serializer_class = LoginSerializer
    permission_classes = []  # Allow anonymous access

    def get_serializer(self, data=None):
        return self.serializer_class(data=data)

    def dispatch(self, request, *args, **kwargs):
        # Disable CSRF for this view
        setattr(request, '_dont_enforce_csrf_checks', True)
        return super().dispatch(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting for login attempts
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='login_attempts'
        )
        
        if not is_allowed:
            SecurityService.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=ip_address,
                severity='medium',
                user_agent=user_agent,
                details={'action': 'login_attempts', 'rate_info': rate_info}
            )
            return Response({
                'success': False,
                'message': 'تعداد تلاش‌های ورود شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 900)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Check if IP is blocked
        if SecurityService.is_ip_blocked(ip_address):
            SecurityService.log_security_event(
                event_type='blocked_ip_attempt',
                ip_address=ip_address,
                severity='high',
                user_agent=user_agent,
                details={'action': 'login_attempt'}
            )
            return Response({
                'success': False,
                'message': 'دسترسی شما به دلیل فعالیت مشکوک محدود شده است.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            # Parse JSON data from request body
            import json
            try:
                data = json.loads(request.body.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                return Response({
                    'success': False,
                    'message': 'Invalid JSON data'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            user = serializer.validated_data['user']
            
            # Check if user account is locked
            if user.is_locked():
                SecurityService.log_security_event(
                    event_type='login_attempt_locked_account',
                    ip_address=ip_address,
                    user=user,
                    severity='medium',
                    user_agent=user_agent,
                    details={'locked_until': user.locked_until.isoformat() if user.locked_until else None}
                )
                return Response({
                    'success': False,
                    'message': 'حساب کاربری شما موقتاً قفل شده است. لطفاً بعداً تلاش کنید.',
                    'locked_until': user.locked_until.isoformat() if user.locked_until else None
                }, status=status.HTTP_423_LOCKED)
            
            # Check for suspicious activity
            is_suspicious, reason = SecurityService.check_suspicious_activity(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                action='login'
            )
            
            if is_suspicious:
                SecurityService.log_security_event(
                    event_type='suspicious_login_attempt',
                    ip_address=ip_address,
                    user=user,
                    severity='high',
                    user_agent=user_agent,
                    details={'reason': reason}
                )
                
                # For highly suspicious activity, require additional verification
                if 'different country' in reason.lower():
                    return Response({
                        'success': False,
                        'message': 'ورود از مکان جدید تشخیص داده شد. لطفاً هویت خود را تأیید کنید.',
                        'requires_verification': True,
                        'verification_methods': ['email', 'phone'] if user.phone else ['email']
                    }, status=status.HTTP_202_ACCEPTED)
            
            # Successful login - reset failed attempts
            user.reset_failed_attempts()
            
            # Update last login IP
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            
            # Store session key before login (it changes after login)
            session_key = request.session.session_key
            
            # Login user in Django session for web interface
            from django.contrib.auth import login
            login(request, user)
            
            # Transfer guest cart to user if session exists
            if session_key:
                from users.services import UserCartService
                UserCartService.transfer_guest_cart_on_login(user, session_key)
            
            # Create/update user session
            self._create_or_update_session(user, request, ip_address, user_agent)
            
            # Get smart redirect URL
            from users.services.redirect import SmartRedirectService
            
            redirect_url = SmartRedirectService.get_smart_redirect_url(request, user, is_registration=False)
            
            # Log successful login
            SecurityService.log_security_event(
                event_type='login_success',
                ip_address=ip_address,
                user=user,
                severity='low',
                user_agent=user_agent,
                details={
                    'login_method': 'password',
                    'new_location': user.last_login_ip != ip_address
                }
            )
            
            # Send security alert for new location login
            if is_suspicious and 'different country' in reason.lower():
                try:
                    from users.services.email import EmailService
                    EmailService.send_security_alert(
                        user=user,
                        event='new_location_login',
                        ip_address=ip_address,
                        details={'location': reason}
                    )
                except Exception as e:
                    logger.error(f"Failed to send security alert: {str(e)}")
            
            return Response({
                'success': True,
                'message': 'ورود با موفقیت انجام شد.',
                'redirect_url': redirect_url,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'avatar': user.avatar.url if user.avatar else None,
                    'email_verified': user.email_verified,
                    'phone_verified': user.phone_verified,
                    'two_factor_enabled': user.two_factor_enabled
                },
                'tokens': {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                },
                'security_info': {
                    'last_login_ip': user.last_login_ip,
                    'new_location': is_suspicious and 'different country' in reason.lower(),
                    'requires_verification': False
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Handle login failure
            try:
                data = json.loads(request.body.decode('utf-8'))
                username = data.get('username', '')
            except (json.JSONDecodeError, UnicodeDecodeError):
                username = ''
            
            # Try to find user for failed attempt logging
            try:
                failed_user = User.objects.filter(username=username).first()
                if failed_user:
                    failed_user.increment_failed_attempts()
                    
                    SecurityService.log_security_event(
                        event_type='login_failed',
                        ip_address=ip_address,
                        user=failed_user,
                        severity='medium',
                        user_agent=user_agent,
                        details={
                            'reason': str(e),
                            'failed_attempts': failed_user.failed_login_attempts
                        }
                    )
                else:
                    # Log failed attempt for non-existent user
                    SecurityService.log_security_event(
                        event_type='login_failed',
                        ip_address=ip_address,
                        severity='low',
                        user_agent=user_agent,
                        details={
                            'reason': 'User not found',
                            'attempted_username': username
                        }
                    )
            except Exception as log_error:
                logger.error(f"Failed to log login failure: {str(log_error)}")
            
            # Increment rate limit counter for failed attempts
            SecurityService.increment_rate_limit(ip_address, 'login_attempts')
            
            return Response({
                'success': False,
                'message': 'نام کاربری یا رمز عبور اشتباه است.'
            }, status=status.HTTP_401_UNAUTHORIZED)
    
    def _create_or_update_session(self, user, request, ip_address, user_agent):
        """Create or update user session record"""
        try:
            from users.models import UserSession
            session_key = request.session.session_key or f"api_session_{user.id}"
            
            # Try to get location from IP
            location = ''
            try:
                from django.contrib.gis.geoip2 import GeoIP2
                g = GeoIP2()
                location_data = g.city(ip_address)
                if location_data:
                    city = location_data.get('city', '')
                    country = location_data.get('country_name', '')
                    location = f"{city}, {country}" if city and country else country
            except Exception:
                pass
            
            # Update existing session or create new one
            session, created = UserSession.objects.update_or_create(
                user=user,
                session_key=session_key,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location': location,
                    'is_active': True
                }
            )
            
            if created:
                SecurityService.log_security_event(
                    event_type='session_created',
                    ip_address=ip_address,
                    user=user,
                    severity='low',
                    details={'session_id': session.id, 'location': location}
                )
                
        except Exception as e:
            logger.error(f"Failed to create/update user session: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class SendOtpAPIView(generics.GenericAPIView):
    serializer_class = SendOtpSerializer

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting for OTP requests
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='otp_requests'
        )
        
        if not is_allowed:
            SecurityService.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=ip_address,
                severity='medium',
                user_agent=user_agent,
                details={'action': 'otp_requests', 'rate_info': rate_info}
            )
            return Response({
                'success': False,
                'message': 'تعداد درخواست‌های OTP شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 3600)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Enhanced serializer validation
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_info = serializer.validated_data.get('contact_info')  # Can be phone or email
        delivery_method = serializer.validated_data.get('delivery_method', 'sms')
        purpose = serializer.validated_data.get('purpose', 'login')
        
        # Backward compatibility: if 'phone' is provided, use it as contact_info
        if not contact_info and 'phone' in serializer.validated_data:
            contact_info = serializer.validated_data['phone']
            delivery_method = 'sms'
        
        if not contact_info:
            return Response({
                'success': False,
                'message': 'اطلاعات تماس (ایمیل یا شماره موبایل) الزامی است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Find user if exists
        user = None
        try:
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            
            try:
                validate_email(contact_info)
                # It's an email
                user = User.objects.filter(email=contact_info).first()
                if delivery_method == 'sms' and not user:
                    return Response({
                        'success': False,
                        'message': 'برای ارسال SMS، شماره موبایل معتبر الزامی است.'
                    }, status=status.HTTP_400_BAD_REQUEST)
            except DjangoValidationError:
                # It's a phone number
                user = User.objects.filter(phone=contact_info).first()
                if delivery_method == 'email' and not user:
                    return Response({
                        'success': False,
                        'message': 'برای ارسال ایمیل، آدرس ایمیل معتبر الزامی است.'
                    }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error finding user: {str(e)}")
        
        # Send OTP using the enhanced OTP service
        success, message = OTPService.send_otp(
            contact_info=contact_info,
            delivery_method=delivery_method,
            purpose=purpose,
            user=user,
            ip_address=ip_address
        )
        
        if success:
            # Increment rate limit counter
            SecurityService.increment_rate_limit(ip_address, 'otp_requests')
            
            # Log security event
            SecurityService.log_security_event(
                event_type='otp_sent',
                ip_address=ip_address,
                user=user,
                severity='low',
                user_agent=user_agent,
                details={
                    'contact_info': contact_info,
                    'delivery_method': delivery_method,
                    'purpose': purpose
                }
            )
            
            return Response({
                'success': True,
                'message': message,
                'delivery_info': {
                    'method': delivery_method,
                    'contact_info': contact_info[:3] + '*' * (len(contact_info) - 6) + contact_info[-3:] if len(contact_info) > 6 else contact_info,
                    'expires_in_minutes': getattr(settings, 'OTP_CODE_EXPIRY_MINUTES', 5)
                }
            }, status=status.HTTP_200_OK)
        else:
            # Log failed OTP send attempt
            SecurityService.log_security_event(
                event_type='otp_send_failed',
                ip_address=ip_address,
                user=user,
                severity='low',
                user_agent=user_agent,
                details={
                    'contact_info': contact_info,
                    'delivery_method': delivery_method,
                    'purpose': purpose,
                    'error_message': message
                }
            )
            
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyOtpAPIView(generics.GenericAPIView):
    serializer_class = VerifyOtpSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data['phone']
        otp = serializer.validated_data['otp']
        success, user = verify_otp(phone, otp)
        if success and user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'success': True,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response({
            'success': False,
            'message': 'Invalid OTP'
        }, status=status.HTTP_400_BAD_REQUEST)


class ProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):
        """Enhanced profile retrieval with additional information"""
        user = self.get_object()
        serializer = self.get_serializer(user)
        
        # Get additional profile information
        profile_data = serializer.data.copy()
        
        # Add verification status
        profile_data['verification_status'] = {
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'two_factor_enabled': user.two_factor_enabled
        }
        
        # Add security information
        profile_data['security_info'] = {
            'last_login_ip': user.last_login_ip,
            'account_locked': user.is_locked(),
            'failed_login_attempts': user.failed_login_attempts,
            'locked_until': user.locked_until.isoformat() if user.locked_until else None
        }
        
        # Add settings
        profile_data['settings'] = {
            'email_notifications': user.email_notifications,
            'sms_notifications': user.sms_notifications
        }
        
        # Add active sessions count
        try:
            from users.models import UserSession
            active_sessions = UserSession.objects.filter(
                user=user,
                is_active=True
            ).count()
            profile_data['active_sessions_count'] = active_sessions
        except Exception:
            profile_data['active_sessions_count'] = 0
        
        return Response({
            'success': True,
            'user': profile_data
        }, status=status.HTTP_200_OK)
    
    def update(self, request, *args, **kwargs):
        """Enhanced profile update with security logging"""
        user = self.get_object()
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Store original values for comparison
        original_data = {
            'email': user.email,
            'phone': user.phone,
            'first_name': user.first_name,
            'last_name': user.last_name
        }
        
        # Perform the update
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(user, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        
        # Check for sensitive changes that require password confirmation
        sensitive_fields = ['email', 'phone']
        sensitive_changes = []
        
        for field in sensitive_fields:
            if field in serializer.validated_data:
                new_value = serializer.validated_data[field]
                if new_value != original_data[field]:
                    sensitive_changes.append(field)
        
        # If sensitive changes are detected, require password confirmation
        if sensitive_changes and not request.data.get('current_password'):
            return Response({
                'success': False,
                'message': 'برای تغییر اطلاعات حساس، وارد کردن رمز عبور فعلی الزامی است.',
                'requires_password': True,
                'sensitive_fields': sensitive_changes
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password for sensitive changes
        if sensitive_changes and request.data.get('current_password'):
            if not user.check_password(request.data['current_password']):
                SecurityService.log_security_event(
                    event_type='profile_update_failed',
                    ip_address=ip_address,
                    user=user,
                    severity='medium',
                    user_agent=user_agent,
                    details={
                        'reason': 'Invalid current password',
                        'attempted_changes': sensitive_changes
                    }
                )
                return Response({
                    'success': False,
                    'message': 'رمز عبور فعلی اشتباه است.'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Save the changes
        updated_user = serializer.save()
        
        # Determine what changed
        changes = {}
        for field, original_value in original_data.items():
            new_value = getattr(updated_user, field)
            if new_value != original_value:
                changes[field] = {
                    'old': original_value,
                    'new': new_value
                }
        
        # If email changed, mark as unverified and send verification
        if 'email' in changes:
            updated_user.email_verified = False
            updated_user.save(update_fields=['email_verified'])
            
            # Send email verification
            try:
                from users.services.verification import VerificationService
                VerificationService.send_email_verification(
                    user=updated_user,
                    email=updated_user.email,
                    ip_address=ip_address
                )
            except Exception as e:
                logger.error(f"Failed to send email verification: {str(e)}")
        
        # If phone changed, mark as unverified
        if 'phone' in changes:
            updated_user.phone_verified = False
            updated_user.save(update_fields=['phone_verified'])
        
        # Log profile update
        SecurityService.log_security_event(
            event_type='profile_updated',
            ip_address=ip_address,
            user=updated_user,
            severity='medium' if sensitive_changes else 'low',
            user_agent=user_agent,
            details={
                'changes': changes,
                'sensitive_changes': sensitive_changes
            }
        )
        
        # Send security alert for sensitive changes
        if sensitive_changes:
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=updated_user,
                    event='profile_updated',
                    ip_address=ip_address,
                    details={'changes': sensitive_changes}
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {str(e)}")
        
        # Return updated profile data
        response_data = serializer.data.copy()
        response_data['verification_status'] = {
            'email_verified': updated_user.email_verified,
            'phone_verified': updated_user.phone_verified,
            'two_factor_enabled': updated_user.two_factor_enabled
        }
        
        return Response({
            'success': True,
            'message': 'پروفایل با موفقیت به‌روزرسانی شد.',
            'user': response_data,
            'changes': list(changes.keys()),
            'verification_required': {
                'email': 'email' in changes,
                'phone': 'phone' in changes
            }
        }, status=status.HTTP_200_OK)


class LogoutAPIView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetRequestAPIView(generics.GenericAPIView):
    """API view for requesting password reset OTP"""
    serializer_class = PasswordResetRequestSerializer
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        # Get client IP
        ip_address = SecurityService.get_client_ip(request)
        
        # Check rate limiting
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='password_reset'
        )
        
        if not is_allowed:
            SecurityService.log_security_event(
                event_type='rate_limit_exceeded',
                ip_address=ip_address,
                severity='medium',
                details={'action': 'password_reset', 'rate_info': rate_info}
            )
            return Response({
                'success': False,
                'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 3600)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_info = serializer.validated_data['contact_info']
        delivery_method = serializer.validated_data['delivery_method']
        
        # Find user
        from django.core.validators import validate_email
        from django.core.exceptions import ValidationError as DjangoValidationError
        
        try:
            validate_email(contact_info)
            user = User.objects.get(email=contact_info)
        except DjangoValidationError:
            user = User.objects.get(phone=contact_info)
        
        # Send OTP
        success, message = OTPService.send_otp(
            contact_info=contact_info,
            delivery_method=delivery_method,
            purpose='password_reset',
            user=user,
            ip_address=ip_address
        )
        
        if success:
            # Increment rate limit counter
            SecurityService.increment_rate_limit(ip_address, 'password_reset')
            
            # Log security event
            SecurityService.log_security_event(
                event_type='password_reset_requested',
                ip_address=ip_address,
                user=user,
                severity='medium',
                details={
                    'contact_info': contact_info,
                    'delivery_method': delivery_method
                }
            )
            
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetVerifyAPIView(generics.GenericAPIView):
    """API view for verifying password reset OTP"""
    serializer_class = PasswordResetVerifySerializer
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        contact_info = serializer.validated_data['contact_info']
        otp_code = serializer.validated_data['otp_code']
        
        # Verify OTP
        success, message, otp_obj = OTPService.verify_otp(
            contact_info=contact_info,
            code=otp_code,
            purpose='password_reset',
            ip_address=ip_address
        )
        
        if success:
            # Find user
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            
            try:
                validate_email(contact_info)
                user = User.objects.get(email=contact_info)
            except DjangoValidationError:
                user = User.objects.get(phone=contact_info)
            
            # Log security event
            SecurityService.log_security_event(
                event_type='password_reset_otp_verified',
                ip_address=ip_address,
                user=user,
                severity='medium',
                details={'contact_info': contact_info}
            )
            
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            # Log failed attempt
            SecurityService.log_security_event(
                event_type='password_reset_otp_failed',
                ip_address=ip_address,
                severity='low',
                details={
                    'contact_info': contact_info,
                    'reason': message
                }
            )
            
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class PasswordResetConfirmAPIView(generics.GenericAPIView):
    """API view for confirming password reset with new password"""
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            # Save new password
            user = serializer.save()
            
            # Log security event
            SecurityService.log_security_event(
                event_type='password_changed',
                ip_address=ip_address,
                user=user,
                severity='high',
                details={'method': 'password_reset'}
            )
            
            # Send security alert email
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=user,
                    event='password_changed',
                    ip_address=ip_address,
                    details={'method': 'Password reset via OTP'}
                )
            except Exception as e:
                # Don't fail the request if email fails
                pass
            
            return Response({
                'success': True,
                'message': 'رمز عبور با موفقیت تغییر یافت.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'success': False,
                'message': 'خطا در تغییر رمز عبور. لطفاً دوباره تلاش کنید.'
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SendEmailVerificationAPIView(generics.GenericAPIView):
    """API view for sending email verification link"""
    serializer_class = SendEmailVerificationSerializer
    permission_classes = []  # Allow both authenticated and anonymous users

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        # Check rate limiting
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='email_verification'
        )
        
        if not is_allowed:
            return Response({
                'success': False,
                'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 3600)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        
        # Find or create user for this email
        if request.user.is_authenticated:
            user = request.user
        else:
            # For anonymous users, find user by email
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'کاربری با این ایمیل یافت نشد.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Send verification email
        success, message = VerificationService.send_email_verification(
            user=user,
            email=email,
            ip_address=ip_address
        )
        
        if success:
            SecurityService.increment_rate_limit(ip_address, 'email_verification')
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyEmailAPIView(generics.GenericAPIView):
    """API view for verifying email with token"""
    serializer_class = VerifyEmailSerializer
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        token = serializer.validated_data['token']
        
        # Verify email
        success, message, user = VerificationService.verify_email(
            token=token,
            ip_address=ip_address
        )
        
        if success:
            return Response({
                'success': True,
                'message': message,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'email_verified': user.email_verified
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class SendPhoneVerificationAPIView(generics.GenericAPIView):
    """API view for sending phone verification OTP"""
    serializer_class = SendPhoneVerificationSerializer
    permission_classes = []  # Allow both authenticated and anonymous users

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        
        # Find user for this phone
        if request.user.is_authenticated:
            user = request.user
        else:
            # For anonymous users, find user by phone
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'کاربری با این شماره موبایل یافت نشد.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Send verification OTP
        success, message = VerificationService.send_phone_verification(
            user=user,
            phone=phone,
            ip_address=ip_address
        )
        
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class VerifyPhoneAPIView(generics.GenericAPIView):
    """API view for verifying phone with OTP"""
    serializer_class = VerifyPhoneSerializer
    permission_classes = []  # Allow both authenticated and anonymous users

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        phone = serializer.validated_data['phone']
        otp_code = serializer.validated_data['otp_code']
        
        # Find user for this phone
        if request.user.is_authenticated:
            user = request.user
        else:
            # For anonymous users, find user by phone
            try:
                user = User.objects.get(phone=phone)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'کاربری با این شماره موبایل یافت نشد.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Verify phone
        success, message = VerificationService.verify_phone(
            user=user,
            phone=phone,
            otp_code=otp_code,
            ip_address=ip_address
        )
        
        if success:
            return Response({
                'success': True,
                'message': message,
                'user': {
                    'id': str(user.id),
                    'username': user.username,
                    'phone': user.phone,
                    'phone_verified': user.phone_verified
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(csrf_exempt, name='dispatch')
class ResendVerificationAPIView(generics.GenericAPIView):
    """API view for resending verification (email or phone)"""
    serializer_class = ResendVerificationSerializer
    permission_classes = []  # Allow both authenticated and anonymous users

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        
        verification_type = serializer.validated_data['verification_type']
        contact_info = serializer.validated_data['contact_info']
        
        # Find user
        if request.user.is_authenticated:
            user = request.user
        else:
            # For anonymous users, find user by contact info
            try:
                if verification_type == 'email':
                    user = User.objects.get(email=contact_info)
                else:  # phone
                    user = User.objects.get(phone=contact_info)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'message': 'کاربری با این اطلاعات یافت نشد.'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Send verification based on type
        if verification_type == 'email':
            success, message = VerificationService.send_email_verification(
                user=user,
                email=contact_info,
                ip_address=ip_address
            )
        else:  # phone
            success, message = VerificationService.send_phone_verification(
                user=user,
                phone=contact_info,
                ip_address=ip_address
            )
        
        if success:
            return Response({
                'success': True,
                'message': message
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)


class UserSessionsAPIView(generics.ListAPIView):
    """API view for listing user's active sessions"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        """Get list of user's active sessions"""
        try:
            from users.models import UserSession
            
            sessions = UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).order_by('-last_activity')
            
            sessions_data = []
            current_session_key = request.session.session_key
            
            for session in sessions:
                session_data = {
                    'id': session.id,
                    'ip_address': session.ip_address,
                    'location': session.location,
                    'user_agent': session.user_agent,
                    'created_at': session.created_at.isoformat(),
                    'last_activity': session.last_activity.isoformat(),
                    'is_current': session.session_key == current_session_key
                }
                sessions_data.append(session_data)
            
            return Response({
                'success': True,
                'sessions': sessions_data,
                'total_count': len(sessions_data)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error getting user sessions: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در دریافت لیست جلسات.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TerminateSessionAPIView(generics.GenericAPIView):
    """API view for terminating a specific session"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, session_id, *args, **kwargs):
        """Terminate a specific session"""
        ip_address = SecurityService.get_client_ip(request)
        
        try:
            from users.models import UserSession
            
            session = UserSession.objects.get(
                id=session_id,
                user=request.user,
                is_active=True
            )
            
            # Deactivate the session
            session.deactivate()
            
            # Log the event
            SecurityService.log_security_event(
                event_type='session_terminated',
                ip_address=ip_address,
                user=request.user,
                severity='low',
                details={
                    'terminated_session_id': session_id,
                    'terminated_session_ip': session.ip_address
                }
            )
            
            return Response({
                'success': True,
                'message': 'جلسه با موفقیت خاتمه یافت.'
            }, status=status.HTTP_200_OK)
            
        except UserSession.DoesNotExist:
            return Response({
                'success': False,
                'message': 'جلسه یافت نشد.'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error terminating session: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در خاتمه جلسه.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutAllDevicesAPIView(generics.GenericAPIView):
    """API view for logging out from all devices"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        """Logout from all devices by deactivating all sessions"""
        ip_address = SecurityService.get_client_ip(request)
        
        try:
            from users.models import UserSession
            
            # Deactivate all user sessions
            sessions_count = UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).count()
            
            UserSession.objects.filter(
                user=request.user,
                is_active=True
            ).update(is_active=False)
            
            # Log the event
            SecurityService.log_security_event(
                event_type='logout_all_devices',
                ip_address=ip_address,
                user=request.user,
                severity='medium',
                details={
                    'terminated_sessions_count': sessions_count
                }
            )
            
            # Send security alert
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=request.user,
                    event='logout_all_devices',
                    ip_address=ip_address,
                    details={'sessions_count': sessions_count}
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {str(e)}")
            
            return Response({
                'success': True,
                'message': f'خروج از {sessions_count} جلسه با موفقیت انجام شد.',
                'terminated_sessions': sessions_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error logging out from all devices: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در خروج از همه دستگاه‌ها.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ChangePasswordAPIView(generics.GenericAPIView):
    """API view for changing user password"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return Response({
                'success': False,
                'message': 'تمام فیلدها الزامی هستند.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({
                'success': False,
                'message': 'رمزهای عبور جدید مطابقت ندارند.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify current password
        if not user.check_password(current_password):
            SecurityService.log_security_event(
                event_type='password_change_failed',
                ip_address=ip_address,
                user=user,
                severity='medium',
                user_agent=user_agent,
                details={'reason': 'Invalid current password'}
            )
            return Response({
                'success': False,
                'message': 'رمز عبور فعلی اشتباه است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate new password
        try:
            from django.contrib.auth.password_validation import validate_password
            validate_password(new_password, user)
        except Exception as e:
            return Response({
                'success': False,
                'message': f'رمز عبور جدید نامعتبر است: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Reset failed login attempts
        user.reset_failed_attempts()
        
        # Log security event
        SecurityService.log_security_event(
            event_type='password_changed',
            ip_address=ip_address,
            user=user,
            severity='high',
            user_agent=user_agent,
            details={'method': 'user_initiated'}
        )
        
        # Send security alert
        try:
            from users.services.email import EmailService
            EmailService.send_security_alert(
                user=user,
                event='password_changed',
                ip_address=ip_address,
                details={'method': 'User-initiated password change'}
            )
        except Exception as e:
            logger.error(f"Failed to send security alert: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'رمز عبور با موفقیت تغییر یافت.'
        }, status=status.HTTP_200_OK)


class TwoFactorToggleAPIView(generics.GenericAPIView):
    """API view for toggling two-factor authentication"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        enabled = request.data.get('enabled', False)
        
        # Update two-factor setting
        user.two_factor_enabled = enabled
        user.save(update_fields=['two_factor_enabled'])
        
        # Log security event
        SecurityService.log_security_event(
            event_type='two_factor_toggled',
            ip_address=ip_address,
            user=user,
            severity='medium',
            user_agent=user_agent,
            details={'enabled': enabled}
        )
        
        # Send security alert for enabling 2FA
        if enabled:
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=user,
                    event='two_factor_enabled',
                    ip_address=ip_address,
                    details={'enabled_at': timezone.now().isoformat()}
                )
            except Exception as e:
                logger.error(f"Failed to send security alert: {str(e)}")
        
        return Response({
            'success': True,
            'message': 'احراز هویت دو مرحله‌ای فعال شد.' if enabled else 'احراز هویت دو مرحله‌ای غیرفعال شد.'
        }, status=status.HTTP_200_OK)


class ResetFailedAttemptsAPIView(generics.GenericAPIView):
    """API view for resetting failed login attempts"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        user = request.user
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Reset failed attempts
        old_attempts = user.failed_login_attempts
        user.reset_failed_attempts()
        
        # Log security event
        SecurityService.log_security_event(
            event_type='failed_attempts_reset',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent=user_agent,
            details={'previous_attempts': old_attempts}
        )
        
        return Response({
            'success': True,
            'message': 'تلاش‌های ناموفق بازنشانی شد.'
        }, status=status.HTTP_200_OK)


class DownloadPersonalDataAPIView(generics.GenericAPIView):
    """API view for downloading personal data (GDPR compliance)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request, *args, **kwargs):
        user = request.user
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        try:
            # Collect user data
            user_data = {
                'user_info': {
                    'id': str(user.id),
                    'username': user.username,
                    'email': user.email,
                    'phone': user.phone,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'birth_date': user.birth_date.isoformat() if user.birth_date else None,
                    'date_joined': user.date_joined.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'email_verified': user.email_verified,
                    'phone_verified': user.phone_verified,
                    'two_factor_enabled': user.two_factor_enabled,
                    'email_notifications': user.email_notifications,
                    'sms_notifications': user.sms_notifications,
                },
                'security_info': {
                    'last_login_ip': user.last_login_ip,
                    'failed_login_attempts': user.failed_login_attempts,
                    'locked_until': user.locked_until.isoformat() if user.locked_until else None,
                },
                'sessions': [],
                'security_logs': [],
                'export_date': timezone.now().isoformat()
            }
            
            # Add sessions data
            try:
                from users.models import UserSession
                sessions = UserSession.objects.filter(user=user).order_by('-created_at')[:50]
                user_data['sessions'] = [
                    {
                        'ip_address': session.ip_address,
                        'user_agent': session.user_agent,
                        'location': session.location,
                        'created_at': session.created_at.isoformat(),
                        'last_activity': session.last_activity.isoformat(),
                        'is_active': session.is_active
                    }
                    for session in sessions
                ]
            except Exception as e:
                logger.error(f"Error collecting sessions data: {str(e)}")
            
            # Add security logs
            try:
                from users.models import SecurityLog
                logs = SecurityLog.objects.filter(user=user).order_by('-created_at')[:100]
                user_data['security_logs'] = [
                    {
                        'event_type': log.event_type,
                        'severity': log.severity,
                        'ip_address': log.ip_address,
                        'created_at': log.created_at.isoformat(),
                        'details': log.details
                    }
                    for log in logs
                ]
            except Exception as e:
                logger.error(f"Error collecting security logs: {str(e)}")
            
            # Log the data export
            SecurityService.log_security_event(
                event_type='personal_data_exported',
                ip_address=ip_address,
                user=user,
                severity='medium',
                user_agent=user_agent,
                details={'export_timestamp': timezone.now().isoformat()}
            )
            
            # Create JSON response
            import json
            from django.http import HttpResponse
            
            response = HttpResponse(
                json.dumps(user_data, indent=2, ensure_ascii=False),
                content_type='application/json; charset=utf-8'
            )
            response['Content-Disposition'] = f'attachment; filename="personal_data_{user.username}_{timezone.now().strftime("%Y%m%d")}.json"'
            
            return response
            
        except Exception as e:
            logger.error(f"Error exporting personal data: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در تهیه اطلاعات شخصی.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DeleteAccountAPIView(generics.GenericAPIView):
    """API view for deleting user account"""
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, *args, **kwargs):
        user = request.user
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        password = request.data.get('password')
        
        if not password:
            return Response({
                'success': False,
                'message': 'رمز عبور برای تأیید حذف حساب الزامی است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verify password
        if not user.check_password(password):
            SecurityService.log_security_event(
                event_type='account_deletion_failed',
                ip_address=ip_address,
                user=user,
                severity='high',
                user_agent=user_agent,
                details={'reason': 'Invalid password'}
            )
            return Response({
                'success': False,
                'message': 'رمز عبور اشتباه است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Log the account deletion before deleting
            SecurityService.log_security_event(
                event_type='account_deleted',
                ip_address=ip_address,
                user=user,
                severity='critical',
                user_agent=user_agent,
                details={
                    'username': user.username,
                    'email': user.email,
                    'deletion_timestamp': timezone.now().isoformat()
                }
            )
            
            # Send final notification email
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=user,
                    event='account_deleted',
                    ip_address=ip_address,
                    details={'deletion_time': timezone.now().isoformat()}
                )
            except Exception as e:
                logger.error(f"Failed to send deletion notification: {str(e)}")
            
            # Delete the user account
            user.delete()
            
            return Response({
                'success': True,
                'message': 'حساب کاربری با موفقیت حذف شد.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error deleting account: {str(e)}")
            return Response({
                'success': False,
                'message': 'خطا در حذف حساب کاربری.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Multi-Step Registration Views
@method_decorator(csrf_exempt, name='dispatch')
class Step1ContactAPIView(APIView):
    """API view for Step 1: Contact info validation and OTP sending"""
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Check rate limiting
        is_allowed, rate_info = SecurityService.check_rate_limit(
            identifier=ip_address,
            action='registration'
        )
        
        if not is_allowed:
            return Response({
                'success': False,
                'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                'retry_after': rate_info.get('retry_after', 3600)
            }, status=status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'فرمت داده نامعتبر است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = Step1ContactSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Get contact data from serializer instance
        contact_data = serializer.contact_data
        contact_info = contact_data['value']
        contact_type = contact_data['type']
        delivery_method = contact_data['delivery_method']
        
        # Check if user already exists
        try:
            if contact_type == 'email':
                existing_user = User.objects.filter(email=contact_info).first()
            else:
                existing_user = User.objects.filter(phone=contact_info).first()
            
            if existing_user:
                return Response({
                    'success': False,
                    'message': 'کاربری با این مشخصات قبلاً ثبت‌نام کرده است.',
                    'action': 'login_required',
                    'login_url': '/users/login/',
                    'contact_type': contact_type
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error checking existing user: {str(e)}")
        
        # Send OTP
        success, message = OTPService.send_otp(
            contact_info=contact_info,
            delivery_method=delivery_method,
            purpose='register',
            user=None,
            ip_address=ip_address
        )
        
        # Log for testing - OTP will be logged in OTPService.send_otp
        logger.info(f"📧 OTP SENT TO: {contact_info} via {delivery_method}")
        
        # Additional console output for testing
        print(f"\n🚀 REGISTRATION STEP 1 - OTP SENT")
        print(f"📧 To: {contact_info}")
        print(f"📱 Method: {delivery_method}")
        print(f"🔗 API: /api/auth/register/step1/contact/")
        print(f"⏰ Check console for OTP code above\n")
        
        if success:
            # Increment rate limit counter
            SecurityService.increment_rate_limit(ip_address, 'registration')
            
            # Log security event
            SecurityService.log_security_event(
                event_type='registration_otp_sent',
                ip_address=ip_address,
                severity='low',
                user_agent=user_agent,
                details={
                    'contact_info': contact_info,
                    'contact_type': contact_type,
                    'delivery_method': delivery_method
                }
            )
            
            return Response({
                'success': True,
                'message': f'کد تأیید به {contact_info} ارسال شد.',
                'contact_info': contact_info,
                'contact_type': contact_type,
                'delivery_method': delivery_method,
                'masked_contact': self._mask_contact_info(contact_info, contact_type)
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'success': False,
                'message': message
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _mask_contact_info(self, contact_info, contact_type):
        """Mask contact info for display"""
        if contact_type == 'email':
            local, domain = contact_info.split('@')
            return f"{local[:2]}***@{domain}"
        else:
            return f"{contact_info[:4]}***{contact_info[-3:]}"


@method_decorator(csrf_exempt, name='dispatch')
class Step1OTPVerifyAPIView(APIView):
    """API view for Step 1: OTP verification and temporary user creation"""
    permission_classes = []  # Allow anonymous access

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'فرمت داده نامعتبر است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = Step1OTPVerifySerializer(data=data, context={'ip_address': ip_address})
        serializer.is_valid(raise_exception=True)
        
        contact_info = serializer.validated_data['contact_info']
        
        # Create temporary user with random password
        import secrets
        import string
        
        # Generate random password
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        random_password = ''.join(secrets.choice(alphabet) for _ in range(16))
        
        # Generate username from contact info
        if '@' in contact_info:
            username = contact_info.split('@')[0] + '_' + str(secrets.randbelow(1000))
            email = contact_info
            phone = None
        else:
            username = 'user_' + contact_info[-8:] + '_' + str(secrets.randbelow(1000))
            email = None
            phone = contact_info
        
        # Ensure username is unique
        while User.objects.filter(username=username).exists():
            username += str(secrets.randbelow(10))
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            phone=phone,
            password=random_password,
            is_active=True
        )
        
        # Log user creation for testing
        print(f"\n✅ USER CREATED SUCCESSFULLY")
        print(f"👤 Username: {username}")
        print(f"📧 Email: {email}")
        print(f"📱 Phone: {phone}")
        print(f"🔑 Random Password: {random_password}")
        print(f"🆔 User ID: {user.id}")
        print(f"🔗 API: /api/auth/register/step1/verify/")
        print(f"⏰ User is now logged in with temporary password\n")
        
        # Mark contact as verified
        if email:
            user.email_verified = True
        if phone:
            user.phone_verified = True
        user.save(update_fields=['email_verified', 'phone_verified'])
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        # Create user session
        self._create_user_session(user, request, ip_address, user_agent)
        
        # Log security event
        SecurityService.log_security_event(
            event_type='user_registered_temp',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent=user_agent,
            details={
                'contact_info': contact_info,
                'registration_method': 'multi_step',
                'step': 1
            }
        )
        
        return Response({
            'success': True,
            'message': 'کد تأیید صحیح است. لطفاً اطلاعات شخصی خود را تکمیل کنید.',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'email': user.email,
                'phone': user.phone,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'next_step': 'personal_info'
        }, status=status.HTTP_200_OK)
    
    def _create_user_session(self, user, request, ip_address, user_agent):
        """Create user session record"""
        try:
            from users.models import UserSession
            import secrets
            
            # Use Django session key if available, otherwise generate one
            session_key = request.session.session_key or f"api_session_{secrets.token_hex(16)}"
            
            # Check if session already exists for this user
            existing_session = UserSession.objects.filter(user=user, is_active=True).first()
            if existing_session:
                existing_session.is_active = False
                existing_session.save()
            
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                location=''
            )
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")


@method_decorator(csrf_exempt, name='dispatch')
class Step2PersonalInfoAPIView(APIView):
    """API view for Step 2: Personal information completion"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user
        
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'فرمت داده نامعتبر است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = Step2PersonalInfoSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Update user with personal information
        user.first_name = serializer.validated_data.get('first_name', '')
        user.last_name = serializer.validated_data.get('last_name', '')
        user.username = serializer.validated_data['username']
        user.save(update_fields=['first_name', 'last_name', 'username'])
        
        # Log security event
        SecurityService.log_security_event(
            event_type='user_profile_updated',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent=user_agent,
            details={
                'step': 2,
                'fields_updated': ['first_name', 'last_name', 'username']
            }
        )
        
        return Response({
            'success': True,
            'message': 'اطلاعات شخصی با موفقیت ثبت شد. لطفاً رمز عبور خود را انتخاب کنید.',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone
            },
            'next_step': 'password'
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class Step3PasswordAPIView(APIView):
    """API view for Step 3: Password creation"""
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        ip_address = SecurityService.get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        user = request.user
        
        # Parse JSON data from request body
        import json
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({
                'success': False,
                'message': 'فرمت داده نامعتبر است.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = Step3PasswordSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        
        # Set new password
        new_password = serializer.validated_data['new_password']
        user.set_password(new_password)
        user.save(update_fields=['password'])
        
        # Generate new JWT tokens after password change
        refresh = RefreshToken.for_user(user)
        
        # Login user in Django session for web interface
        from django.contrib.auth import login
        login(request, user)
        
        # Transfer guest cart to user if session exists
        session_key = request.session.session_key
        if session_key:
            from users.services import UserCartService
            UserCartService.transfer_guest_cart_on_registration(user, session_key)
        
        # Create new user session after password change
        self._create_user_session(user, request, ip_address, user_agent)
        
        # Log registration completion for testing
        print(f"\n🎉 REGISTRATION COMPLETED SUCCESSFULLY!")
        print(f"👤 Username: {user.username}")
        print(f"📧 Email: {user.email}")
        print(f"📱 Phone: {user.phone}")
        print(f"👨‍💼 Name: {user.first_name} {user.last_name}")
        print(f"🔑 Password: [SET BY USER]")
        print(f"🆔 User ID: {user.id}")
        print(f"✅ Email Verified: {user.email_verified}")
        print(f"✅ Phone Verified: {user.phone_verified}")
        print(f"🔗 Redirect to: /users/profile/")
        print(f"⏰ Registration completed at: {timezone.now()}")
        print(f"🔑 New Access Token: {str(refresh.access_token)[:50]}...")
        print(f"🔄 New Refresh Token: {str(refresh)[:50]}...\n")
        
        # Log security event
        SecurityService.log_security_event(
            event_type='user_registration_completed',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent=user_agent,
            details={
                'step': 3,
                'registration_method': 'multi_step'
            }
        )
        
        # Get smart redirect URL for completed registration
        from users.services.redirect import SmartRedirectService
        redirect_url = SmartRedirectService.get_smart_redirect_url(request, user, is_registration=True)
        
        return Response({
            'success': True,
            'message': 'ثبت‌نام با موفقیت تکمیل شد! خوش آمدید.',
            'user': {
                'id': str(user.id),
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'phone': user.phone,
                'email_verified': user.email_verified,
                'phone_verified': user.phone_verified
            },
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'next_step': 'completed',
            'redirect_url': redirect_url,
            'auto_login': True
        }, status=status.HTTP_200_OK)
    
    def _create_user_session(self, user, request, ip_address, user_agent):
        """Create user session record"""
        try:
            from users.models import UserSession
            import secrets
            
            # Use Django session key if available, otherwise generate one
            session_key = request.session.session_key or f"api_session_{secrets.token_hex(16)}"
            
            # Check if session already exists for this user
            existing_session = UserSession.objects.filter(user=user, is_active=True).first()
            if existing_session:
                existing_session.is_active = False
                existing_session.save()
            
            UserSession.objects.create(
                user=user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent,
                location=''
            )
        except Exception as e:
            logger.error(f"Failed to create user session: {str(e)}")
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import TemplateView, FormView
from django.contrib.auth import views as auth_views
from django.shortcuts import render, redirect
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import json
from users.services.otp import OTPService
from users.services.security import SecurityService


class LoginTemplateView(TemplateView):
    template_name = 'users/login.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preserve the next URL for redirect after login
        context['next'] = self.request.GET.get('next', '')
        return context


class RegisterTemplateView(TemplateView):
    template_name = 'users/register-multistep.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preserve the next URL for redirect after registration
        context['next'] = self.request.GET.get('next', '')
        return context


class MultiStepRegisterTemplateView(TemplateView):
    """Multi-step registration template view"""
    template_name = 'users/register-multistep.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Preserve the next URL for redirect after registration
        context['next'] = self.request.GET.get('next', '')
        return context


class ProfileTemplateView(TemplateView):
    template_name = 'users/profile.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)


class LogoutView(TemplateView):
    """Custom logout view that supports both GET and POST methods"""
    
    def get_next_page(self):
        """Determine where to redirect after logout"""
        next_page = self.request.GET.get('next')
        if next_page:
            return next_page
        return reverse_lazy('core:home')
    
    def get(self, request, *args, **kwargs):
        """Handle GET requests for logout"""
        from django.contrib.auth import logout
        logout(request)
        return redirect(self.get_next_page())
    
    def post(self, request, *args, **kwargs):
        """Handle POST requests for logout"""
        from django.contrib.auth import logout
        logout(request)
        return redirect(self.get_next_page())


class PasswordResetRequestView(TemplateView):
    """Web view for password reset request form"""
    template_name = 'users/password_reset_request.html'

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request, *args, **kwargs):
        """Handle password reset request via AJAX"""
        try:
            data = json.loads(request.body)
            contact_info = data.get('contact_info', '').strip()
            delivery_method = data.get('delivery_method', 'email')
            
            if not contact_info:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفاً ایمیل یا شماره موبایل خود را وارد کنید.'
                })
            
            # Get client IP
            ip_address = SecurityService.get_client_ip(request)
            
            # Check rate limiting
            is_allowed, rate_info = SecurityService.check_rate_limit(
                identifier=ip_address,
                action='password_reset'
            )
            
            if not is_allowed:
                return JsonResponse({
                    'success': False,
                    'message': 'تعداد درخواست‌های شما از حد مجاز گذشته است. لطفاً بعداً تلاش کنید.',
                    'retry_after': rate_info.get('retry_after', 3600)
                })
            
            # Find user
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            from django.contrib.auth import get_user_model
            
            User = get_user_model()
            
            try:
                validate_email(contact_info)
                user = User.objects.filter(email=contact_info).first()
                if not user:
                    return JsonResponse({
                        'success': False,
                        'message': 'کاربری با این ایمیل یافت نشد.'
                    })
            except DjangoValidationError:
                user = User.objects.filter(phone=contact_info).first()
                if not user:
                    return JsonResponse({
                        'success': False,
                        'message': 'کاربری با این شماره موبایل یافت نشد.'
                    })
            
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
                
                return JsonResponse({
                    'success': True,
                    'message': message,
                    'contact_info': contact_info,
                    'delivery_method': delivery_method
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': message
                })
                
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'درخواست نامعتبر است.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای سیستمی رخ داده است.'
            })


class PasswordResetVerifyView(TemplateView):
    """Web view for password reset OTP verification and new password form"""
    template_name = 'users/password_reset_verify.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['contact_info'] = self.request.GET.get('contact_info', '')
        context['delivery_method'] = self.request.GET.get('delivery_method', 'email')
        return context

    @method_decorator(csrf_exempt, name='dispatch')
    def post(self, request, *args, **kwargs):
        """Handle password reset verification and confirmation via AJAX"""
        try:
            data = json.loads(request.body)
            contact_info = data.get('contact_info', '').strip()
            otp_code = data.get('otp_code', '').strip()
            new_password = data.get('new_password', '')
            confirm_password = data.get('confirm_password', '')
            
            # Validate input
            if not all([contact_info, otp_code, new_password, confirm_password]):
                return JsonResponse({
                    'success': False,
                    'message': 'لطفاً تمام فیلدها را پر کنید.'
                })
            
            if new_password != confirm_password:
                return JsonResponse({
                    'success': False,
                    'message': 'رمزهای عبور مطابقت ندارند.'
                })
            
            if len(new_password) < 8:
                return JsonResponse({
                    'success': False,
                    'message': 'رمز عبور باید حداقل 8 کاراکتر باشد.'
                })
            
            # Get client IP
            ip_address = SecurityService.get_client_ip(request)
            
            # Verify OTP
            success, message, otp_obj = OTPService.verify_otp(
                contact_info=contact_info,
                code=otp_code,
                purpose='password_reset',
                ip_address=ip_address
            )
            
            if not success:
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
                
                return JsonResponse({
                    'success': False,
                    'message': message
                })
            
            # Find user and set new password
            from django.core.validators import validate_email
            from django.core.exceptions import ValidationError as DjangoValidationError
            from django.contrib.auth import get_user_model
            from django.contrib.auth.password_validation import validate_password
            
            User = get_user_model()
            
            try:
                validate_email(contact_info)
                user = User.objects.get(email=contact_info)
            except DjangoValidationError:
                user = User.objects.get(phone=contact_info)
            
            # Validate password strength
            try:
                validate_password(new_password, user)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'رمز عبور نامعتبر است: {str(e)}'
                })
            
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
            except Exception:
                # Don't fail the request if email fails
                pass
            
            return JsonResponse({
                'success': True,
                'message': 'رمز عبور با موفقیت تغییر یافت. اکنون می‌توانید وارد شوید.'
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'درخواست نامعتبر است.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای سیستمی رخ داده است.'
            })


class EmailVerificationView(TemplateView):
    """Web view for email verification via link"""
    template_name = 'users/email_verification.html'

    def get(self, request, token, *args, **kwargs):
        """Handle email verification via GET request with token"""
        from users.services.verification import VerificationService
        
        ip_address = SecurityService.get_client_ip(request)
        
        # Verify email
        success, message, user = VerificationService.verify_email(
            token=token,
            ip_address=ip_address
        )
        
        context = {
            'success': success,
            'message': message,
            'user': user
        }
        
        if success:
            messages.success(request, message)
            # If user is not logged in, suggest login
            if not request.user.is_authenticated:
                context['suggest_login'] = True
        else:
            messages.error(request, message)
        
        return render(request, self.template_name, context)


class VerificationStatusView(TemplateView):
    """Web view for checking verification status"""
    template_name = 'users/verification_status.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        user = request.user
        context = {
            'user': user,
            'email_verified': user.email_verified,
            'phone_verified': user.phone_verified,
            'verification_needed': not (user.email_verified and user.phone_verified)
        }
        return render(request, self.template_name, context)

    @method_decorator(csrf_exempt, name='dispatch')
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle verification requests via AJAX"""
        try:
            data = json.loads(request.body)
            verification_type = data.get('verification_type')
            
            if verification_type not in ['email', 'phone']:
                return JsonResponse({
                    'success': False,
                    'message': 'نوع تأیید نامعتبر است.'
                })
            
            ip_address = SecurityService.get_client_ip(request)
            user = request.user
            
            if verification_type == 'email':
                if not user.email:
                    return JsonResponse({
                        'success': False,
                        'message': 'ایمیلی برای حساب شما ثبت نشده است.'
                    })
                
                if user.email_verified:
                    return JsonResponse({
                        'success': False,
                        'message': 'ایمیل شما قبلاً تأیید شده است.'
                    })
                
                from users.services.verification import VerificationService
                success, message = VerificationService.send_email_verification(
                    user=user,
                    email=user.email,
                    ip_address=ip_address
                )
                
            else:  # phone
                if not user.phone:
                    return JsonResponse({
                        'success': False,
                        'message': 'شماره موبایلی برای حساب شما ثبت نشده است.'
                    })
                
                if user.phone_verified:
                    return JsonResponse({
                        'success': False,
                        'message': 'شماره موبایل شما قبلاً تأیید شده است.'
                    })
                
                from users.services.verification import VerificationService
                success, message = VerificationService.send_phone_verification(
                    user=user,
                    phone=user.phone,
                    ip_address=ip_address
                )
            
            return JsonResponse({
                'success': success,
                'message': message
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'درخواست نامعتبر است.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای سیستمی رخ داده است.'
            })


class PhoneVerificationView(TemplateView):
    """Web view for phone verification with OTP"""
    template_name = 'users/phone_verification.html'

    @method_decorator(login_required)
    def get(self, request, *args, **kwargs):
        user = request.user
        context = {
            'user': user,
            'phone': user.phone,
            'phone_verified': user.phone_verified
        }
        return render(request, self.template_name, context)

    @method_decorator(csrf_exempt, name='dispatch')
    @method_decorator(login_required)
    def post(self, request, *args, **kwargs):
        """Handle phone verification via AJAX"""
        try:
            data = json.loads(request.body)
            otp_code = data.get('otp_code', '').strip()
            
            if not otp_code:
                return JsonResponse({
                    'success': False,
                    'message': 'لطفاً کد تأیید را وارد کنید.'
                })
            
            user = request.user
            if not user.phone:
                return JsonResponse({
                    'success': False,
                    'message': 'شماره موبایلی برای حساب شما ثبت نشده است.'
                })
            
            if user.phone_verified:
                return JsonResponse({
                    'success': False,
                    'message': 'شماره موبایل شما قبلاً تأیید شده است.'
                })
            
            ip_address = SecurityService.get_client_ip(request)
            
            from users.services.verification import VerificationService
            success, message = VerificationService.verify_phone(
                user=user,
                phone=user.phone,
                otp_code=otp_code,
                ip_address=ip_address
            )
            
            return JsonResponse({
                'success': success,
                'message': message,
                'phone_verified': user.phone_verified if success else False
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'message': 'درخواست نامعتبر است.'
            })
        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': 'خطای سیستمی رخ داده است.'
            })


class SuccessView(TemplateView):
    """Web view for success pages after user operations"""
    template_name = 'users/success.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get success type from URL parameter
        success_type = self.request.GET.get('type', 'general')
        
        # Define success page configurations
        success_configs = {
            'registration': {
                'page_title': 'ثبت‌نام موفقیت‌آمیز',
                'page_message': 'حساب کاربری شما با موفقیت ایجاد شد. خوش آمدید!',
                'success_details': [
                    'حساب کاربری شما فعال است',
                    'ایمیل تأیید ارسال شد',
                    'می‌توانید از تمام امکانات استفاده کنید'
                ],
                'primary_action_url': reverse_lazy('users:profile'),
                'primary_action_text': 'مشاهده پروفایل',
                'primary_action_icon': 'person',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'login': {
                'page_title': 'ورود موفقیت‌آمیز',
                'page_message': 'با موفقیت وارد حساب کاربری خود شدید.',
                'success_details': [
                    'جلسه شما فعال است',
                    'می‌توانید از تمام امکانات استفاده کنید'
                ],
                'primary_action_url': reverse_lazy('users:profile'),
                'primary_action_text': 'مشاهده پروفایل',
                'primary_action_icon': 'person',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'logout': {
                'page_title': 'خروج موفقیت‌آمیز',
                'page_message': 'با موفقیت از حساب کاربری خود خارج شدید.',
                'success_details': [
                    'جلسه شما بسته شد',
                    'اطلاعات شما محفوظ است'
                ],
                'primary_action_url': reverse_lazy('users:login'),
                'primary_action_text': 'ورود مجدد',
                'primary_action_icon': 'box-arrow-in-right',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'password_reset': {
                'page_title': 'تغییر رمز عبور موفقیت‌آمیز',
                'page_message': 'رمز عبور شما با موفقیت تغییر یافت.',
                'success_details': [
                    'رمز عبور جدید فعال است',
                    'ایمیل تأیید ارسال شد',
                    'می‌توانید با رمز جدید وارد شوید'
                ],
                'primary_action_url': reverse_lazy('users:login'),
                'primary_action_text': 'ورود با رمز جدید',
                'primary_action_icon': 'box-arrow-in-right',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'email_verified': {
                'page_title': 'تأیید ایمیل موفقیت‌آمیز',
                'page_message': 'ایمیل شما با موفقیت تأیید شد.',
                'success_details': [
                    'ایمیل شما تأیید شد',
                    'می‌توانید از تمام امکانات استفاده کنید'
                ],
                'primary_action_url': reverse_lazy('users:profile'),
                'primary_action_text': 'مشاهده پروفایل',
                'primary_action_icon': 'person',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'phone_verified': {
                'page_title': 'تأیید شماره موبایل موفقیت‌آمیز',
                'page_message': 'شماره موبایل شما با موفقیت تأیید شد.',
                'success_details': [
                    'شماره موبایل شما تأیید شد',
                    'می‌توانید از تمام امکانات استفاده کنید'
                ],
                'primary_action_url': reverse_lazy('users:profile'),
                'primary_action_text': 'مشاهده پروفایل',
                'primary_action_icon': 'person',
                'secondary_action_url': reverse_lazy('core:home'),
                'secondary_action_text': 'بازگشت به خانه',
                'secondary_action_icon': 'house'
            },
            'general': {
                'page_title': 'عملیات موفقیت‌آمیز',
                'page_message': 'عملیات شما با موفقیت انجام شد.',
                'primary_action_url': reverse_lazy('core:home'),
                'primary_action_text': 'بازگشت به خانه',
                'primary_action_icon': 'house'
            }
        }
        
        # Get configuration for success type
        config = success_configs.get(success_type, success_configs['general'])
        
        # Update context with configuration
        context.update(config)
        
        # Add auto redirect if specified
        auto_redirect_url = self.request.GET.get('redirect')
        auto_redirect_delay = self.request.GET.get('delay', '3')
        
        if auto_redirect_url:
            context['auto_redirect_url'] = auto_redirect_url
            context['auto_redirect_delay'] = auto_redirect_delay
        
        return context
from django.urls import path
from users.views.api import (
    RegisterAPIView, LoginAPIView, SendOtpAPIView, VerifyOtpAPIView,
    ProfileAPIView, LogoutAPIView, PasswordResetRequestAPIView,
    PasswordResetVerifyAPIView, PasswordResetConfirmAPIView,
    SendEmailVerificationAPIView, VerifyEmailAPIView,
    SendPhoneVerificationAPIView, VerifyPhoneAPIView,
    ResendVerificationAPIView, UserSessionsAPIView, TerminateSessionAPIView,
    LogoutAllDevicesAPIView, ChangePasswordAPIView, TwoFactorToggleAPIView,
    ResetFailedAttemptsAPIView, DownloadPersonalDataAPIView, DeleteAccountAPIView,
    Step1ContactAPIView, Step1OTPVerifyAPIView, Step2PersonalInfoAPIView, Step3PasswordAPIView
)

app_name = 'api_users'

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('login/', LoginAPIView.as_view(), name='login'),
    path('send-otp/', SendOtpAPIView.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOtpAPIView.as_view(), name='verify-otp'),
    path('profile/', ProfileAPIView.as_view(), name='profile'),
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    
    # Password reset endpoints
    path('password-reset/request/', PasswordResetRequestAPIView.as_view(), name='password-reset-request'),
    path('password-reset/verify/', PasswordResetVerifyAPIView.as_view(), name='password-reset-verify'),
    path('password-reset/confirm/', PasswordResetConfirmAPIView.as_view(), name='password-reset-confirm'),
    
    # Verification endpoints
    path('send-email-verification/', SendEmailVerificationAPIView.as_view(), name='send-email-verification'),
    path('verify-email/', VerifyEmailAPIView.as_view(), name='verify-email'),
    path('send-phone-verification/', SendPhoneVerificationAPIView.as_view(), name='send-phone-verification'),
    path('verify-phone/', VerifyPhoneAPIView.as_view(), name='verify-phone'),
    path('resend-verification/', ResendVerificationAPIView.as_view(), name='resend-verification'),
    
    # Session management endpoints
    path('sessions/', UserSessionsAPIView.as_view(), name='user-sessions'),
    path('sessions/<int:session_id>/', TerminateSessionAPIView.as_view(), name='terminate-session'),
    path('logout-all/', LogoutAllDevicesAPIView.as_view(), name='logout-all-devices'),
    
    # Enhanced profile management endpoints
    path('change-password/', ChangePasswordAPIView.as_view(), name='change-password'),
    path('two-factor/', TwoFactorToggleAPIView.as_view(), name='two-factor-toggle'),
    path('reset-failed-attempts/', ResetFailedAttemptsAPIView.as_view(), name='reset-failed-attempts'),
    path('download-data/', DownloadPersonalDataAPIView.as_view(), name='download-personal-data'),
    path('delete-account/', DeleteAccountAPIView.as_view(), name='delete-account'),
    
    # Multi-step registration endpoints
    path('register/step1/contact/', Step1ContactAPIView.as_view(), name='register-step1-contact'),
    path('register/step1/verify/', Step1OTPVerifyAPIView.as_view(), name='register-step1-verify'),
    path('register/step2/personal/', Step2PersonalInfoAPIView.as_view(), name='register-step2-personal'),
    path('register/step3/password/', Step3PasswordAPIView.as_view(), name='register-step3-password'),
]
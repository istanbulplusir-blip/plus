from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.utils import timezone


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, unique=True, blank=True, null=True, help_text="E.164 format, e.g. +989123456789")
    
    # Profile fields
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    birth_date = models.DateField(blank=True, null=True)
    
    # Verification status
    email_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    
    # Security fields
    failed_login_attempts = models.IntegerField(default=0)
    locked_until = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    # Settings
    two_factor_enabled = models.BooleanField(default=False)
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=True)

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
            models.Index(fields=['email_verified']),
            models.Index(fields=['phone_verified']),
            models.Index(fields=['locked_until']),
            models.Index(fields=['last_login']),
            models.Index(fields=['date_joined']),
            models.Index(fields=['is_active']),
            # Composite indexes for common queries
            models.Index(fields=['email', 'is_active']),
            models.Index(fields=['phone', 'is_active']),
            models.Index(fields=['email_verified', 'phone_verified']),
        ]
        
    def is_locked(self):
        """Check if user account is currently locked"""
        if self.locked_until:
            return timezone.now() < self.locked_until
        return False
        
    def lock_account(self, duration_minutes=30):
        """Lock user account for specified duration"""
        self.locked_until = timezone.now() + timezone.timedelta(minutes=duration_minutes)
        self.save(update_fields=['locked_until'])
        
    def unlock_account(self):
        """Unlock user account"""
        self.locked_until = None
        self.failed_login_attempts = 0
        self.save(update_fields=['locked_until', 'failed_login_attempts'])
        
    def increment_failed_attempts(self):
        """Increment failed login attempts counter"""
        self.failed_login_attempts += 1
        if self.failed_login_attempts >= 3:
            self.lock_account()
        else:
            self.save(update_fields=['failed_login_attempts'])
            
    def reset_failed_attempts(self):
        """Reset failed login attempts counter"""
        self.failed_login_attempts = 0
        self.save(update_fields=['failed_login_attempts'])


def generate_hash(code):
    import hashlib
    return hashlib.sha256(code.encode()).hexdigest()


class OtpCode(models.Model):
    DELIVERY_CHOICES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
    ]

    PURPOSE_CHOICES = [
        ('login', 'Login'),
        ('register', 'Register'),
        ('password_reset', 'Password Reset'),
        ('email_verify', 'Email Verification'),
        ('phone_verify', 'Phone Verification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    contact_info = models.CharField(max_length=255, default='')  # email or phone
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='sms')
    hashed_code = models.CharField(max_length=64)  # SHA-256 hash
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES, default='login')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.IntegerField(default=0)
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField(default='127.0.0.1')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['contact_info']),
            models.Index(fields=['purpose']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['used']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
            # Composite indexes for common queries
            models.Index(fields=['contact_info', 'purpose', 'used']),
            models.Index(fields=['expires_at', 'used']),
            models.Index(fields=['ip_address', 'created_at']),
        ]

    def is_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.used and not self.is_expired() and self.attempts < 3

    def verify_code(self, code):
        return generate_hash(code) == self.hashed_code
        
    def increment_attempts(self):
        """Increment verification attempts"""
        self.attempts += 1
        self.save(update_fields=['attempts'])
        
    def mark_as_used(self):
        """Mark OTP as used"""
        self.used = True
        self.save(update_fields=['used'])


class UserSession(models.Model):
    """Model to track user sessions for security purposes"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    location = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-last_activity']
        verbose_name = 'User Session'
        verbose_name_plural = 'User Sessions'
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_activity']),
            models.Index(fields=['created_at']),
            # Composite indexes for common queries
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ip_address', 'is_active']),
            models.Index(fields=['last_activity', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.ip_address}"
        
    def deactivate(self):
        """Deactivate this session"""
        self.is_active = False
        self.save(update_fields=['is_active'])


class PasswordResetToken(models.Model):
    """Model to handle password reset tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='password_reset_tokens')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Password Reset Token'
        verbose_name_plural = 'Password Reset Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['used']),
        ]

    def __str__(self):
        return f"Reset token for {self.user.username}"
        
    def is_expired(self):
        """Check if token is expired"""
        return timezone.now() > self.expires_at
        
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
        
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save(update_fields=['used'])


class EmailVerificationToken(models.Model):
    """Model to handle email verification tokens"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='email_verification_tokens')
    email = models.EmailField()  # Store email in case user changes it before verification
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    ip_address = models.GenericIPAddressField()

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Email Verification Token'
        verbose_name_plural = 'Email Verification Tokens'
        indexes = [
            models.Index(fields=['token']),
            models.Index(fields=['email']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['used']),
        ]

    def __str__(self):
        return f"Email verification token for {self.email}"
        
    def is_expired(self):
        """Check if token is expired"""
        return timezone.now() > self.expires_at
        
    def is_valid(self):
        """Check if token is valid (not used and not expired)"""
        return not self.used and not self.is_expired()
        
    def mark_as_used(self):
        """Mark token as used"""
        self.used = True
        self.save(update_fields=['used'])


class SecurityLog(models.Model):
    """Model to track security events and activities"""
    
    EVENT_TYPES = [
        ('login_success', 'Successful Login'),
        ('login_failed', 'Failed Login'),
        ('login_locked', 'Account Locked'),
        ('password_changed', 'Password Changed'),
        ('otp_sent', 'OTP Sent'),
        ('otp_failed', 'OTP Verification Failed'),
        ('rate_limit_exceeded', 'Rate Limit Exceeded'),
        ('suspicious_activity', 'Suspicious Activity'),
        ('account_unlocked', 'Account Unlocked'),
        ('session_created', 'Session Created'),
        ('session_terminated', 'Session Terminated'),
        ('email_verification_sent', 'Email Verification Sent'),
        ('email_verified', 'Email Verified'),
        ('phone_verification_sent', 'Phone Verification Sent'),
        ('phone_verified', 'Phone Verified'),
    ]
    
    SEVERITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='security_logs')
    event_type = models.CharField(max_length=30, choices=EVENT_TYPES)
    severity = models.CharField(max_length=10, choices=SEVERITY_LEVELS, default='low')
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Security Log'
        verbose_name_plural = 'Security Logs'
        indexes = [
            models.Index(fields=['event_type']),
            models.Index(fields=['severity']),
            models.Index(fields=['ip_address']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user', 'event_type']),
            # Composite indexes for security monitoring
            models.Index(fields=['event_type', 'severity']),
            models.Index(fields=['ip_address', 'event_type']),
            models.Index(fields=['created_at', 'severity']),
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        user_info = f"{self.user.username}" if self.user else "Anonymous"
        return f"{self.event_type} - {user_info} - {self.ip_address}"

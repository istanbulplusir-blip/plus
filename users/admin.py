from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from .models import User, OtpCode, UserSession, PasswordResetToken, SecurityLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for User model"""
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'avatar', 'birth_date')
        }),
        (_('Verification'), {
            'fields': ('email_verified', 'phone_verified')
        }),
        (_('Security'), {
            'fields': ('failed_login_attempts', 'locked_until', 'last_login_ip', 'two_factor_enabled')
        }),
        (_('Notifications'), {
            'fields': ('email_notifications', 'sms_notifications')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'phone', 'password1', 'password2'),
        }),
    )
    
    list_display = ('username', 'email', 'phone', 'email_verified', 'phone_verified', 
                   'is_staff', 'is_active', 'failed_login_attempts', 'locked_until')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'email_verified', 
                  'phone_verified', 'two_factor_enabled', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    ordering = ('username',)
    readonly_fields = ('last_login', 'date_joined', 'last_login_ip')


@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    """Admin interface for OtpCode model"""
    
    list_display = ('user', 'contact_info', 'delivery_method', 'purpose', 
                   'created_at', 'expires_at', 'attempts', 'used', 'ip_address')
    list_filter = ('delivery_method', 'purpose', 'used', 'created_at')
    search_fields = ('user__username', 'user__email', 'contact_info', 'ip_address')
    readonly_fields = ('hashed_code', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'contact_info', 'delivery_method', 'purpose')
        }),
        (_('Code Info'), {
            'fields': ('hashed_code', 'attempts', 'used')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at')
        }),
        (_('Security'), {
            'fields': ('ip_address',)
        }),
    )


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    """Admin interface for UserSession model"""
    
    list_display = ('user', 'ip_address', 'location', 'created_at', 
                   'last_activity', 'is_active')
    list_filter = ('is_active', 'created_at', 'last_activity')
    search_fields = ('user__username', 'user__email', 'ip_address', 'location')
    readonly_fields = ('session_key', 'created_at', 'last_activity')
    ordering = ('-last_activity',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'session_key', 'is_active')
        }),
        (_('Location Info'), {
            'fields': ('ip_address', 'location', 'user_agent')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_activity')
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding sessions through admin"""
        return False


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """Admin interface for PasswordResetToken model"""
    
    list_display = ('user', 'token', 'created_at', 'expires_at', 'used', 'ip_address')
    list_filter = ('used', 'created_at')
    search_fields = ('user__username', 'user__email', 'token', 'ip_address')
    readonly_fields = ('token', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'token', 'used')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'expires_at')
        }),
        (_('Security'), {
            'fields': ('ip_address',)
        }),
    )
    
    def has_add_permission(self, request):
        """Disable adding tokens through admin"""
        return False


@admin.register(SecurityLog)
class SecurityLogAdmin(admin.ModelAdmin):
    """Admin interface for SecurityLog model"""
    
    list_display = ('event_type', 'user', 'severity_colored', 'ip_address', 
                   'created_at', 'has_details')
    list_filter = ('event_type', 'severity', 'created_at')
    search_fields = ('user__username', 'user__email', 'ip_address', 'event_type')
    readonly_fields = ('event_type', 'user', 'severity', 'ip_address', 
                      'user_agent', 'details', 'created_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('event_type', 'user', 'severity')
        }),
        (_('Request Info'), {
            'fields': ('ip_address', 'user_agent')
        }),
        (_('Details'), {
            'fields': ('details',)
        }),
        (_('Timestamp'), {
            'fields': ('created_at',)
        }),
    )
    
    def severity_colored(self, obj):
        """Display severity with color coding"""
        colors = {
            'low': 'green',
            'medium': 'orange', 
            'high': 'red',
            'critical': 'darkred'
        }
        color = colors.get(obj.severity, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_severity_display()
        )
    severity_colored.short_description = 'Severity'
    
    def has_details(self, obj):
        """Show if log has additional details"""
        return bool(obj.details)
    has_details.boolean = True
    has_details.short_description = 'Has Details'
    
    def has_add_permission(self, request):
        """Disable adding security logs through admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Disable changing security logs through admin"""
        return False
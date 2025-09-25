"""
Celery tasks for background processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from django.core.cache import cache
from .models import OtpCode, PasswordResetToken, EmailVerificationToken, SecurityLog, UserSession
import logging

logger = logging.getLogger(__name__)


@shared_task
def cleanup_expired_data():
    """
    Celery task to clean up expired OTP codes, tokens, and old logs
    """
    try:
        # Clean up expired OTP codes
        expired_otps = OtpCode.objects.filter(expires_at__lt=timezone.now())
        otp_count = expired_otps.count()
        expired_otps.delete()
        
        # Clean up expired password reset tokens
        expired_reset_tokens = PasswordResetToken.objects.filter(expires_at__lt=timezone.now())
        reset_count = expired_reset_tokens.count()
        expired_reset_tokens.delete()
        
        # Clean up expired email verification tokens
        expired_email_tokens = EmailVerificationToken.objects.filter(expires_at__lt=timezone.now())
        email_count = expired_email_tokens.count()
        expired_email_tokens.delete()
        
        # Clean up old security logs (keep 30 days)
        cutoff_date = timezone.now() - timedelta(days=30)
        old_logs = SecurityLog.objects.filter(created_at__lt=cutoff_date)
        log_count = old_logs.count()
        old_logs.delete()
        
        # Clean up old inactive sessions
        session_cutoff = timezone.now() - timedelta(days=30)
        old_sessions = UserSession.objects.filter(
            last_activity__lt=session_cutoff,
            is_active=False
        )
        session_count = old_sessions.count()
        old_sessions.delete()
        
        logger.info(
            f"Cleanup completed: {otp_count} OTPs, {reset_count} reset tokens, "
            f"{email_count} email tokens, {log_count} logs, {session_count} sessions"
        )
        
        return {
            'status': 'success',
            'cleaned': {
                'otps': otp_count,
                'reset_tokens': reset_count,
                'email_tokens': email_count,
                'security_logs': log_count,
                'sessions': session_count
            }
        }
        
    except Exception as e:
        logger.error(f"Cleanup task failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def optimize_database():
    """
    Celery task to optimize database performance
    """
    try:
        call_command('optimize_db', '--analyze')
        logger.info("Database optimization completed")
        return {'status': 'success', 'message': 'Database optimized'}
    except Exception as e:
        logger.error(f"Database optimization failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def clear_rate_limit_cache():
    """
    Clear rate limiting cache entries that are older than 1 hour
    """
    try:
        rate_limit_cache = cache.get_cache('rate_limit')
        # This would need custom implementation based on your rate limiting keys
        # For now, we'll just clear the entire rate limit cache
        rate_limit_cache.clear()
        
        logger.info("Rate limit cache cleared")
        return {'status': 'success', 'message': 'Rate limit cache cleared'}
    except Exception as e:
        logger.error(f"Rate limit cache clear failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}


@shared_task
def generate_security_report():
    """
    Generate weekly security report
    """
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Get security statistics for the past week
        week_ago = timezone.now() - timedelta(days=7)
        
        failed_logins = SecurityLog.objects.filter(
            event_type='login_failed',
            created_at__gte=week_ago
        ).count()
        
        locked_accounts = SecurityLog.objects.filter(
            event_type='login_locked',
            created_at__gte=week_ago
        ).count()
        
        rate_limits = SecurityLog.objects.filter(
            event_type='rate_limit_exceeded',
            created_at__gte=week_ago
        ).count()
        
        suspicious_activities = SecurityLog.objects.filter(
            event_type='suspicious_activity',
            created_at__gte=week_ago
        ).count()
        
        # Create report
        report = f"""
        Security Report - Week of {week_ago.strftime('%Y-%m-%d')}
        
        Summary:
        - Failed login attempts: {failed_logins}
        - Accounts locked: {locked_accounts}
        - Rate limit violations: {rate_limits}
        - Suspicious activities: {suspicious_activities}
        
        Please review the security logs for more details.
        """
        
        # Send email report (if configured)
        if hasattr(settings, 'SECURITY_REPORT_EMAIL'):
            send_mail(
                'Weekly Security Report',
                report,
                settings.DEFAULT_FROM_EMAIL,
                [settings.SECURITY_REPORT_EMAIL],
                fail_silently=False,
            )
        
        logger.info("Security report generated and sent")
        return {
            'status': 'success',
            'report': {
                'failed_logins': failed_logins,
                'locked_accounts': locked_accounts,
                'rate_limits': rate_limits,
                'suspicious_activities': suspicious_activities
            }
        }
        
    except Exception as e:
        logger.error(f"Security report generation failed: {str(e)}")
        return {'status': 'error', 'message': str(e)}
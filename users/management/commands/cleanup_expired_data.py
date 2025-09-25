from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from users.models import OtpCode, PasswordResetToken, EmailVerificationToken, SecurityLog, UserSession


class Command(BaseCommand):
    help = 'Clean up expired OTP codes, tokens, and old security logs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days to keep security logs (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_to_keep = options['days']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will be deleted'))
        
        self.stdout.write(self.style.SUCCESS('Starting cleanup of expired data...'))
        
        # Clean up expired OTP codes
        expired_otps = OtpCode.objects.filter(expires_at__lt=timezone.now())
        otp_count = expired_otps.count()
        
        if not dry_run:
            expired_otps.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {otp_count} expired OTP codes')
        )
        
        # Clean up expired password reset tokens
        expired_reset_tokens = PasswordResetToken.objects.filter(expires_at__lt=timezone.now())
        reset_token_count = expired_reset_tokens.count()
        
        if not dry_run:
            expired_reset_tokens.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {reset_token_count} expired password reset tokens')
        )
        
        # Clean up expired email verification tokens
        expired_email_tokens = EmailVerificationToken.objects.filter(expires_at__lt=timezone.now())
        email_token_count = expired_email_tokens.count()
        
        if not dry_run:
            expired_email_tokens.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {email_token_count} expired email verification tokens')
        )
        
        # Clean up old security logs (keep only specified number of days)
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        old_security_logs = SecurityLog.objects.filter(created_at__lt=cutoff_date)
        security_log_count = old_security_logs.count()
        
        if not dry_run:
            old_security_logs.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {security_log_count} old security logs (older than {days_to_keep} days)')
        )
        
        # Clean up inactive user sessions (older than 30 days)
        session_cutoff = timezone.now() - timedelta(days=30)
        old_sessions = UserSession.objects.filter(
            last_activity__lt=session_cutoff,
            is_active=False
        )
        session_count = old_sessions.count()
        
        if not dry_run:
            old_sessions.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {session_count} old inactive sessions')
        )
        
        # Clean up used tokens and codes
        used_otps = OtpCode.objects.filter(used=True, created_at__lt=cutoff_date)
        used_otp_count = used_otps.count()
        
        if not dry_run:
            used_otps.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {used_otp_count} old used OTP codes')
        )
        
        used_reset_tokens = PasswordResetToken.objects.filter(used=True, created_at__lt=cutoff_date)
        used_reset_count = used_reset_tokens.count()
        
        if not dry_run:
            used_reset_tokens.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {used_reset_count} old used password reset tokens')
        )
        
        used_email_tokens = EmailVerificationToken.objects.filter(used=True, created_at__lt=cutoff_date)
        used_email_count = used_email_tokens.count()
        
        if not dry_run:
            used_email_tokens.delete()
            
        self.stdout.write(
            self.style.SUCCESS(f'{"Would delete" if dry_run else "Deleted"} {used_email_count} old used email verification tokens')
        )
        
        total_cleaned = (
            otp_count + reset_token_count + email_token_count + 
            security_log_count + session_count + used_otp_count + 
            used_reset_count + used_email_count
        )
        
        self.stdout.write(
            self.style.SUCCESS(f'Cleanup completed! Total items {"would be" if dry_run else ""} cleaned: {total_cleaned}')
        )
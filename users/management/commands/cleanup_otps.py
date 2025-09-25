"""
Management command to clean up expired OTP codes.
This can be run as a cron job to keep the database clean.
"""
from django.core.management.base import BaseCommand
from users.services.otp import OTPService


class Command(BaseCommand):
    help = 'Clean up expired OTP codes from the database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            from users.models import OtpCode
            from django.utils import timezone
            
            expired_count = OtpCode.objects.filter(
                expires_at__lt=timezone.now()
            ).count()
            
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: Would delete {expired_count} expired OTP codes'
                )
            )
        else:
            self.stdout.write('Cleaning up expired OTP codes...')
            
            cleaned_count = OTPService.cleanup_expired_otps()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleaned up {cleaned_count} expired OTP codes'
                )
            )
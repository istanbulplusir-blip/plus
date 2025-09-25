"""
Management command to clean up old security logs.
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from users.services.security import SecurityService


class Command(BaseCommand):
    help = 'Clean up old security logs'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep logs (default: 90)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
    
    def handle(self, *args, **options):
        days_to_keep = options['days']
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would clean up security logs older than {days_to_keep} days')
            )
            # For dry run, we would need to implement a count method
            # For now, just show the message
            self.stdout.write('Use --no-dry-run to actually perform the cleanup')
        else:
            self.stdout.write(f'Cleaning up security logs older than {days_to_keep} days...')
            
            deleted_count = SecurityService.cleanup_security_logs(days_to_keep=days_to_keep)
            
            if deleted_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully deleted {deleted_count} old security logs')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('No old security logs found to delete')
                )
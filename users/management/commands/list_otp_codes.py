"""
Management command to list OTP codes for debugging and testing.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from users.models import OtpCode, User


class Command(BaseCommand):
    help = 'List OTP codes for debugging and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--user',
            type=str,
            help='Filter by username, email, or phone'
        )
        parser.add_argument(
            '--purpose',
            type=str,
            choices=['login', 'register', 'password_reset', 'email_verify', 'phone_verify'],
            help='Filter by OTP purpose'
        )
        parser.add_argument(
            '--delivery-method',
            type=str,
            choices=['sms', 'email'],
            help='Filter by delivery method'
        )
        parser.add_argument(
            '--active-only',
            action='store_true',
            help='Show only active (unused and not expired) OTP codes'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Limit number of results (default: 20)'
        )
    
    def handle(self, *args, **options):
        user_filter = options.get('user')
        purpose_filter = options.get('purpose')
        delivery_method_filter = options.get('delivery_method')
        active_only = options.get('active_only')
        limit = options.get('limit')
        
        # Build query
        queryset = OtpCode.objects.all()
        
        if user_filter:
            # Try to find user by username, email, or phone
            user = User.objects.filter(
                models.Q(username__icontains=user_filter) |
                models.Q(email__icontains=user_filter) |
                models.Q(phone__icontains=user_filter)
            ).first()
            
            if user:
                queryset = queryset.filter(user=user)
                self.stdout.write(f'Filtering by user: {user.username} ({user.email})')
            else:
                # Filter by contact_info if user not found
                queryset = queryset.filter(contact_info__icontains=user_filter)
                self.stdout.write(f'Filtering by contact info: {user_filter}')
        
        if purpose_filter:
            queryset = queryset.filter(purpose=purpose_filter)
        
        if delivery_method_filter:
            queryset = queryset.filter(delivery_method=delivery_method_filter)
        
        if active_only:
            queryset = queryset.filter(used=False, expires_at__gt=timezone.now())
        
        # Order by creation time (newest first)
        queryset = queryset.order_by('-created_at')
        
        # Apply limit
        otp_codes = queryset[:limit]
        
        if not otp_codes:
            self.stdout.write(self.style.WARNING('No OTP codes found matching the criteria.'))
            return
        
        # Display results
        self.stdout.write('\n' + '='*100)
        self.stdout.write(self.style.SUCCESS(f'FOUND {otp_codes.count()} OTP CODE(S)'))
        self.stdout.write('='*100)
        
        for otp in otp_codes:
            # Status indicators
            status = []
            if otp.used:
                status.append(self.style.ERROR('USED'))
            elif otp.is_expired():
                status.append(self.style.WARNING('EXPIRED'))
            else:
                status.append(self.style.SUCCESS('ACTIVE'))
            
            if otp.attempts > 0:
                status.append(f'ATTEMPTS: {otp.attempts}')
            
            status_str = ' | '.join(status)
            
            # Time remaining
            if not otp.used and not otp.is_expired():
                remaining = otp.expires_at - timezone.now()
                remaining_str = f'{remaining.seconds // 60}m {remaining.seconds % 60}s'
            else:
                remaining_str = 'N/A'
            
            self.stdout.write(f'\nID: {otp.id}')
            self.stdout.write(f'User: {otp.user.username if otp.user else "N/A"} ({otp.user.email if otp.user else "N/A"})')
            self.stdout.write(f'Contact: {otp.contact_info}')
            self.stdout.write(f'Method: {otp.delivery_method.upper()}')
            self.stdout.write(f'Purpose: {otp.purpose.upper()}')
            self.stdout.write(f'Status: {status_str}')
            self.stdout.write(f'Created: {otp.created_at.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'Expires: {otp.expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
            self.stdout.write(f'Time Remaining: {remaining_str}')
            self.stdout.write(f'IP: {otp.ip_address}')
            self.stdout.write(f'Hash: {otp.hashed_code[:16]}...')
            self.stdout.write('-' * 50)
        
        # Summary
        active_count = queryset.filter(used=False, expires_at__gt=timezone.now()).count()
        used_count = queryset.filter(used=True).count()
        expired_count = queryset.filter(used=False, expires_at__lte=timezone.now()).count()
        
        self.stdout.write('\n' + self.style.SUCCESS('SUMMARY:'))
        self.stdout.write(f'Active: {active_count}')
        self.stdout.write(f'Used: {used_count}')
        self.stdout.write(f'Expired: {expired_count}')
        self.stdout.write(f'Total: {queryset.count()}')
        
        # Show how to use OTP codes
        if active_count > 0:
            self.stdout.write('\n' + self.style.SUCCESS('HOW TO USE ACTIVE OTP CODES:'))
            self.stdout.write('1. Note the contact_info (phone/email)')
            self.stdout.write('2. Use the OTP verification API endpoint')
            self.stdout.write('3. The actual OTP code is not stored (only hash)')
            self.stdout.write('4. You need to know the original code or create a new one')
            
            self.stdout.write('\n' + self.style.SUCCESS('TO CREATE A NEW OTP WITH KNOWN CODE:'))
            self.stdout.write('python manage.py create_test_user --otp-code 123456 --purpose login')

"""
Management command to test OTP verification functionality.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import models
from users.models import OtpCode, User
from users.services.otp import OTPService


class Command(BaseCommand):
    help = 'Test OTP verification functionality'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--contact-info',
            type=str,
            required=True,
            help='Contact info (phone or email) to test'
        )
        parser.add_argument(
            '--otp-code',
            type=str,
            required=True,
            help='OTP code to verify'
        )
        parser.add_argument(
            '--purpose',
            type=str,
            default='login',
            choices=['login', 'register', 'password_reset', 'email_verify', 'phone_verify'],
            help='Purpose of the OTP (default: login)'
        )
        parser.add_argument(
            '--create-if-not-exists',
            action='store_true',
            help='Create OTP code if it does not exist'
        )
    
    def handle(self, *args, **options):
        contact_info = options['contact_info']
        otp_code = options['otp_code']
        purpose = options['purpose']
        create_if_not_exists = options['create_if_not_exists']
        
        self.stdout.write(f'Testing OTP verification for: {contact_info}')
        self.stdout.write(f'OTP Code: {otp_code}')
        self.stdout.write(f'Purpose: {purpose}')
        self.stdout.write('-' * 50)
        
        # Check if OTP code exists
        otp_obj = OtpCode.objects.filter(
            contact_info=contact_info,
            purpose=purpose,
            used=False
        ).order_by('-created_at').first()
        
        if not otp_obj:
            if create_if_not_exists:
                self.stdout.write('OTP code not found. Creating new one...')
                
                # Find or create user
                user = User.objects.filter(
                    models.Q(email=contact_info) | models.Q(phone=contact_info)
                ).first()
                
                if not user:
                    # Create a test user
                    username = contact_info.replace('@', '_').replace('+', '')
                    user = User.objects.create_user(
                        username=username,
                        email=contact_info if '@' in contact_info else '',
                        phone=contact_info if '@' not in contact_info else '',
                        password='TestPassword123!'
                    )
                    self.stdout.write(f'Created test user: {username}')
                
                # Create OTP code
                from users.models import generate_hash
                from datetime import timedelta
                
                otp_obj = OtpCode.objects.create(
                    user=user,
                    contact_info=contact_info,
                    delivery_method='email' if '@' in contact_info else 'sms',
                    hashed_code=generate_hash(otp_code),
                    purpose=purpose,
                    expires_at=timezone.now() + timedelta(minutes=5),
                    ip_address='127.0.0.1'
                )
                
                self.stdout.write(f'Created OTP code with hash: {otp_obj.hashed_code[:16]}...')
            else:
                self.stdout.write(
                    self.style.ERROR('OTP code not found. Use --create-if-not-exists to create one.')
                )
                return
        else:
            self.stdout.write(f'Found existing OTP code: {otp_obj.hashed_code[:16]}...')
        
        # Test verification
        self.stdout.write('\nTesting OTP verification...')
        
        success, message, verified_otp = OTPService.verify_otp(
            contact_info=contact_info,
            code=otp_code,
            purpose=purpose,
            ip_address='127.0.0.1'
        )
        
        if success:
            self.stdout.write(self.style.SUCCESS(f'✓ OTP verification successful: {message}'))
            self.stdout.write(f'Verified OTP ID: {verified_otp.id}')
            self.stdout.write(f'User: {verified_otp.user.username if verified_otp.user else "N/A"}')
        else:
            self.stdout.write(self.style.ERROR(f'✗ OTP verification failed: {message}'))
        
        # Show OTP status
        otp_obj.refresh_from_db()
        self.stdout.write('\nOTP Status:')
        self.stdout.write(f'Used: {otp_obj.used}')
        self.stdout.write(f'Attempts: {otp_obj.attempts}')
        self.stdout.write(f'Expired: {otp_obj.is_expired()}')
        self.stdout.write(f'Valid: {otp_obj.is_valid()}')
        
        # Show how to use in API
        self.stdout.write('\n' + self.style.SUCCESS('API USAGE:'))
        self.stdout.write('POST /api/users/verify-otp/')
        self.stdout.write('{')
        self.stdout.write(f'  "contact_info": "{contact_info}",')
        self.stdout.write(f'  "otp": "{otp_code}",')
        self.stdout.write(f'  "purpose": "{purpose}"')
        self.stdout.write('}')

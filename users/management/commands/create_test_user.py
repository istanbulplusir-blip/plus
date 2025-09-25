"""
Management command to create test users with OTP codes for development and testing.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import OtpCode, generate_hash
from users.services.otp import OTPService

User = get_user_model()


class Command(BaseCommand):
    help = 'Create test users with OTP codes for development and testing'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default='testuser',
            help='Username for the test user (default: testuser)'
        )
        parser.add_argument(
            '--email',
            type=str,
            default='test@example.com',
            help='Email for the test user (default: test@example.com)'
        )
        parser.add_argument(
            '--phone',
            type=str,
            default='+989123456789',
            help='Phone number for the test user (default: +989123456789)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='TestPassword123!',
            help='Password for the test user (default: TestPassword123!)'
        )
        parser.add_argument(
            '--otp-code',
            type=str,
            default='123456',
            help='OTP code to create (default: 123456)'
        )
        parser.add_argument(
            '--purpose',
            type=str,
            default='login',
            choices=['login', 'register', 'password_reset', 'email_verify', 'phone_verify'],
            help='Purpose of the OTP (default: login)'
        )
        parser.add_argument(
            '--delivery-method',
            type=str,
            default='sms',
            choices=['sms', 'email'],
            help='Delivery method for OTP (default: sms)'
        )
        parser.add_argument(
            '--expires-minutes',
            type=int,
            default=5,
            help='OTP expiration time in minutes (default: 5)'
        )
        parser.add_argument(
            '--superuser',
            action='store_true',
            help='Create a superuser instead of regular user'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if user already exists'
        )
    
    def handle(self, *args, **options):
        username = options['username']
        email = options['email']
        phone = options['phone']
        password = options['password']
        otp_code = options['otp_code']
        purpose = options['purpose']
        delivery_method = options['delivery_method']
        expires_minutes = options['expires_minutes']
        is_superuser = options['superuser']
        force = options['force']
        
        # Check if user already exists
        user_exists = User.objects.filter(username=username).exists()
        
        if user_exists and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'User "{username}" already exists. Use --force to recreate or choose a different username.'
                )
            )
            return
        
        # Create or get user
        if user_exists and force:
            user = User.objects.get(username=username)
            user.email = email
            user.phone = phone
            user.set_password(password)
            if is_superuser:
                user.is_superuser = True
                user.is_staff = True
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f'Updated existing user: {username}')
            )
        elif user_exists:
            user = User.objects.get(username=username)
            self.stdout.write(
                self.style.SUCCESS(f'Using existing user: {username}')
            )
        else:
            if is_superuser:
                user = User.objects.create_superuser(
                    username=username,
                    email=email,
                    phone=phone,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created superuser: {username}')
                )
            else:
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    phone=phone,
                    password=password
                )
                self.stdout.write(
                    self.style.SUCCESS(f'Created user: {username}')
                )
        
        # Create OTP code
        contact_info = phone if delivery_method == 'sms' else email
        expires_at = timezone.now() + timedelta(minutes=expires_minutes)
        
        # Clean up any existing OTP codes for this contact and purpose
        OtpCode.objects.filter(
            contact_info=contact_info,
            purpose=purpose,
            used=False
        ).delete()
        
        # Create new OTP code
        otp_obj = OtpCode.objects.create(
            user=user,
            contact_info=contact_info,
            delivery_method=delivery_method,
            hashed_code=generate_hash(otp_code),
            purpose=purpose,
            expires_at=expires_at,
            ip_address='127.0.0.1'
        )
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Created OTP code: {otp_code} for {contact_info} '
                f'(expires in {expires_minutes} minutes)'
            )
        )
        
        # Display summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('TEST USER CREATED SUCCESSFULLY'))
        self.stdout.write('='*50)
        self.stdout.write(f'Username: {username}')
        self.stdout.write(f'Email: {email}')
        self.stdout.write(f'Phone: {phone}')
        self.stdout.write(f'Password: {password}')
        self.stdout.write(f'OTP Code: {otp_code}')
        self.stdout.write(f'OTP Purpose: {purpose}')
        self.stdout.write(f'Delivery Method: {delivery_method}')
        self.stdout.write(f'Expires: {expires_at.strftime("%Y-%m-%d %H:%M:%S")}')
        self.stdout.write(f'Is Superuser: {is_superuser}')
        self.stdout.write('='*50)
        
        # Show login instructions
        self.stdout.write('\n' + self.style.SUCCESS('LOGIN INSTRUCTIONS:'))
        self.stdout.write('1. Go to the login page')
        self.stdout.write('2. Enter username/email/phone and password')
        self.stdout.write('3. If OTP is required, use the OTP code above')
        self.stdout.write('4. You can also test OTP verification directly via API')
        
        # Show API endpoints
        self.stdout.write('\n' + self.style.SUCCESS('API ENDPOINTS:'))
        self.stdout.write('Send OTP: POST /api/users/send-otp/')
        self.stdout.write('Verify OTP: POST /api/users/verify-otp/')
        self.stdout.write('Login: POST /api/users/login/')
        
        # Show admin access
        if is_superuser:
            self.stdout.write('\n' + self.style.SUCCESS('ADMIN ACCESS:'))
            self.stdout.write('You can access Django admin with this user')
            self.stdout.write('Admin URL: /admin/')

"""
Demo script to showcase the EmailService and OTPService functionality.
This script demonstrates how to use the new services.
"""
from django.contrib.auth import get_user_model
from users.services.otp import OTPService
from users.services.email import EmailService

User = get_user_model()


def demo_otp_service():
    """Demonstrate OTP service functionality"""
    print("=== OTP Service Demo ===")
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@example.com',
            'phone': '+989123456789',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    print(f"Using user: {user.username} ({user.email})")
    
    # Demo 1: Send OTP via SMS
    print("\n1. Sending OTP via SMS...")
    success, message = OTPService.send_otp(
        contact_info=user.phone,
        delivery_method='sms',
        purpose='login',
        user=user,
        ip_address='192.168.1.100'
    )
    print(f"SMS OTP Result: {success} - {message}")
    
    # Demo 2: Send OTP via Email
    print("\n2. Sending OTP via Email...")
    success, message = OTPService.send_otp(
        contact_info=user.email,
        delivery_method='email',
        purpose='register',
        user=user,
        ip_address='192.168.1.100'
    )
    print(f"Email OTP Result: {success} - {message}")
    
    # Demo 3: Verify OTP (this would normally use the actual code sent)
    print("\n3. Verifying OTP...")
    # In a real scenario, you'd get the code from the user
    # For demo purposes, we'll show what happens with a wrong code
    success, message, otp_obj = OTPService.verify_otp(
        contact_info=user.email,
        code='123456',  # This will likely be wrong
        purpose='register',
        ip_address='192.168.1.100'
    )
    print(f"OTP Verification Result: {success} - {message}")
    
    # Demo 4: Cleanup expired OTPs
    print("\n4. Cleaning up expired OTPs...")
    cleaned_count = OTPService.cleanup_expired_otps()
    print(f"Cleaned up {cleaned_count} expired OTP codes")


def demo_email_service():
    """Demonstrate Email service functionality"""
    print("\n=== Email Service Demo ===")
    
    # Get or create a test user
    user, created = User.objects.get_or_create(
        username='demo_user',
        defaults={
            'email': 'demo@example.com',
            'phone': '+989123456789',
            'first_name': 'Demo',
            'last_name': 'User'
        }
    )
    
    print(f"Using user: {user.username} ({user.email})")
    
    # Demo 1: Send OTP Email
    print("\n1. Sending OTP Email...")
    success = EmailService.send_otp_email(
        email=user.email,
        code='123456',
        purpose='login'
    )
    print(f"OTP Email Result: {success}")
    
    # Demo 2: Send Verification Email
    print("\n2. Sending Verification Email...")
    success = EmailService.send_verification_email(
        user=user,
        verification_token='demo-token-123'
    )
    print(f"Verification Email Result: {success}")
    
    # Demo 3: Send Password Reset Email
    print("\n3. Sending Password Reset Email...")
    success = EmailService.send_password_reset_email(
        user=user,
        reset_token='reset-token-456'
    )
    print(f"Password Reset Email Result: {success}")
    
    # Demo 4: Send Security Alert
    print("\n4. Sending Security Alert...")
    success = EmailService.send_security_alert(
        user=user,
        event='login_from_new_location',
        ip_address='192.168.1.100',
        details={
            'location': 'Tehran, Iran',
            'timestamp': 'همین الان',
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    )
    print(f"Security Alert Email Result: {success}")
    
    # Demo 5: Send Welcome Email
    print("\n5. Sending Welcome Email...")
    success = EmailService.send_welcome_email(user=user)
    print(f"Welcome Email Result: {success}")


def main():
    """Main demo function"""
    print("Email and OTP Services Demo")
    print("=" * 40)
    
    try:
        demo_otp_service()
        demo_email_service()
        
        print("\n" + "=" * 40)
        print("Demo completed successfully!")
        print("Check your console for email output (in development mode)")
        
    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    # This would be run with: python manage.py shell < users/services/demo.py
    main()
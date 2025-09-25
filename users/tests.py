from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from users.models import OtpCode, UserSession, PasswordResetToken, generate_hash

User = get_user_model()


class UserModelTest(TestCase):
    """Test cases for the User model"""
    
    def setUp(self):
        """Set up test data"""
        self.user_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+989123456789',
            'first_name': 'Test',
            'last_name': 'User',
        }
        self.user = User.objects.create_user(**self.user_data)
    
    def test_user_creation(self):
        """Test user creation with new fields"""
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
        self.assertEqual(self.user.phone, '+989123456789')
        self.assertFalse(self.user.email_verified)
        self.assertFalse(self.user.phone_verified)
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertIsNone(self.user.locked_until)
        self.assertFalse(self.user.two_factor_enabled)
        self.assertTrue(self.user.email_notifications)
        self.assertTrue(self.user.sms_notifications)
    
    def test_is_locked_method(self):
        """Test the is_locked method"""
        # User should not be locked initially
        self.assertFalse(self.user.is_locked())
        
        # Lock user for 30 minutes
        self.user.locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()
        self.assertTrue(self.user.is_locked())
        
        # Set lock time in the past
        self.user.locked_until = timezone.now() - timedelta(minutes=30)
        self.user.save()
        self.assertFalse(self.user.is_locked())
    
    def test_lock_account_method(self):
        """Test the lock_account method"""
        self.user.lock_account(60)  # Lock for 60 minutes
        self.assertTrue(self.user.is_locked())
        self.assertIsNotNone(self.user.locked_until)
    
    def test_unlock_account_method(self):
        """Test the unlock_account method"""
        # First lock the account
        self.user.failed_login_attempts = 3
        self.user.lock_account()
        
        # Then unlock it
        self.user.unlock_account()
        self.assertFalse(self.user.is_locked())
        self.assertIsNone(self.user.locked_until)
        self.assertEqual(self.user.failed_login_attempts, 0)
    
    def test_increment_failed_attempts(self):
        """Test the increment_failed_attempts method"""
        # First attempt
        self.user.increment_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 1)
        self.assertFalse(self.user.is_locked())
        
        # Second attempt
        self.user.increment_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 2)
        self.assertFalse(self.user.is_locked())
        
        # Third attempt should lock the account
        self.user.increment_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 3)
        self.assertTrue(self.user.is_locked())
    
    def test_reset_failed_attempts(self):
        """Test the reset_failed_attempts method"""
        self.user.failed_login_attempts = 2
        self.user.save()
        
        self.user.reset_failed_attempts()
        self.assertEqual(self.user.failed_login_attempts, 0)


class OtpCodeModelTest(TestCase):
    """Test cases for the OtpCode model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789'
        )
        
        self.otp_data = {
            'user': self.user,
            'contact_info': 'test@example.com',
            'delivery_method': 'email',
            'hashed_code': generate_hash('123456'),
            'purpose': 'login',
            'expires_at': timezone.now() + timedelta(minutes=5),
            'ip_address': '192.168.1.1'
        }
        self.otp = OtpCode.objects.create(**self.otp_data)
    
    def test_otp_creation(self):
        """Test OTP creation with new fields"""
        self.assertEqual(self.otp.user, self.user)
        self.assertEqual(self.otp.contact_info, 'test@example.com')
        self.assertEqual(self.otp.delivery_method, 'email')
        self.assertEqual(self.otp.purpose, 'login')
        self.assertEqual(self.otp.attempts, 0)
        self.assertFalse(self.otp.used)
        self.assertEqual(self.otp.ip_address, '192.168.1.1')
    
    def test_is_expired_method(self):
        """Test the is_expired method"""
        # Should not be expired initially
        self.assertFalse(self.otp.is_expired())
        
        # Set expiry in the past
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save()
        self.assertTrue(self.otp.is_expired())
    
    def test_is_valid_method(self):
        """Test the is_valid method"""
        # Should be valid initially
        self.assertTrue(self.otp.is_valid())
        
        # Should be invalid if used
        self.otp.used = True
        self.otp.save()
        self.assertFalse(self.otp.is_valid())
        
        # Reset and test expiry
        self.otp.used = False
        self.otp.expires_at = timezone.now() - timedelta(minutes=1)
        self.otp.save()
        self.assertFalse(self.otp.is_valid())
        
        # Reset and test max attempts
        self.otp.expires_at = timezone.now() + timedelta(minutes=5)
        self.otp.attempts = 3
        self.otp.save()
        self.assertFalse(self.otp.is_valid())
    
    def test_verify_code_method(self):
        """Test the verify_code method"""
        self.assertTrue(self.otp.verify_code('123456'))
        self.assertFalse(self.otp.verify_code('654321'))
    
    def test_increment_attempts_method(self):
        """Test the increment_attempts method"""
        initial_attempts = self.otp.attempts
        self.otp.increment_attempts()
        self.assertEqual(self.otp.attempts, initial_attempts + 1)
    
    def test_mark_as_used_method(self):
        """Test the mark_as_used method"""
        self.assertFalse(self.otp.used)
        self.otp.mark_as_used()
        self.assertTrue(self.otp.used)


class UserSessionModelTest(TestCase):
    """Test cases for the UserSession model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        self.session_data = {
            'user': self.user,
            'session_key': 'test_session_key_123',
            'ip_address': '192.168.1.1',
            'user_agent': 'Mozilla/5.0 Test Browser',
            'location': 'Tehran, Iran'
        }
        self.session = UserSession.objects.create(**self.session_data)
    
    def test_session_creation(self):
        """Test session creation"""
        self.assertEqual(self.session.user, self.user)
        self.assertEqual(self.session.session_key, 'test_session_key_123')
        self.assertEqual(self.session.ip_address, '192.168.1.1')
        self.assertEqual(self.session.user_agent, 'Mozilla/5.0 Test Browser')
        self.assertEqual(self.session.location, 'Tehran, Iran')
        self.assertTrue(self.session.is_active)
    
    def test_deactivate_method(self):
        """Test the deactivate method"""
        self.assertTrue(self.session.is_active)
        self.session.deactivate()
        self.assertFalse(self.session.is_active)
    
    def test_string_representation(self):
        """Test the __str__ method"""
        expected = f"{self.user.username} - {self.session.ip_address}"
        self.assertEqual(str(self.session), expected)


class PasswordResetTokenModelTest(TestCase):
    """Test cases for the PasswordResetToken model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        
        self.token_data = {
            'user': self.user,
            'token': 'test_reset_token_123',
            'expires_at': timezone.now() + timedelta(hours=1),
            'ip_address': '192.168.1.1'
        }
        self.reset_token = PasswordResetToken.objects.create(**self.token_data)
    
    def test_token_creation(self):
        """Test token creation"""
        self.assertEqual(self.reset_token.user, self.user)
        self.assertEqual(self.reset_token.token, 'test_reset_token_123')
        self.assertEqual(self.reset_token.ip_address, '192.168.1.1')
        self.assertFalse(self.reset_token.used)
    
    def test_is_expired_method(self):
        """Test the is_expired method"""
        # Should not be expired initially
        self.assertFalse(self.reset_token.is_expired())
        
        # Set expiry in the past
        self.reset_token.expires_at = timezone.now() - timedelta(minutes=1)
        self.reset_token.save()
        self.assertTrue(self.reset_token.is_expired())
    
    def test_is_valid_method(self):
        """Test the is_valid method"""
        # Should be valid initially
        self.assertTrue(self.reset_token.is_valid())
        
        # Should be invalid if used
        self.reset_token.used = True
        self.reset_token.save()
        self.assertFalse(self.reset_token.is_valid())
        
        # Reset and test expiry
        self.reset_token.used = False
        self.reset_token.expires_at = timezone.now() - timedelta(minutes=1)
        self.reset_token.save()
        self.assertFalse(self.reset_token.is_valid())
    
    def test_mark_as_used_method(self):
        """Test the mark_as_used method"""
        self.assertFalse(self.reset_token.used)
        self.reset_token.mark_as_used()
        self.assertTrue(self.reset_token.used)
    
    def test_string_representation(self):
        """Test the __str__ method"""
        expected = f"Reset token for {self.user.username}"
        self.assertEqual(str(self.reset_token), expected)
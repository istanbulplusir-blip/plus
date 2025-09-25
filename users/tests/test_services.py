"""
Unit tests for user services (OTP and Email).
"""
import unittest
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone
from django.core.cache import cache
from django.core import mail
from datetime import timedelta

from users.models import User, OtpCode
from users.services.otp import OTPService
from users.services.email import EmailService


class OTPServiceTestCase(TestCase):
    """Test cases for OTPService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789'
        )
        self.ip_address = '192.168.1.1'
        cache.clear()
    
    def tearDown(self):
        """Clean up after tests"""
        cache.clear()
    
    def test_generate_otp(self):
        """Test OTP generation"""
        otp = OTPService.generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
        self.assertTrue(100000 <= int(otp) <= 999999)
    
    def test_rate_limit_check_within_limit(self):
        """Test rate limiting when within limits"""
        contact_info = 'test@example.com'
        
        # Should be within limit initially
        self.assertTrue(OTPService._check_rate_limit(contact_info, self.ip_address))
    
    def test_rate_limit_check_exceeded(self):
        """Test rate limiting when limit exceeded"""
        contact_info = 'test@example.com'
        
        # Simulate exceeding rate limit
        cache.set(f"otp_rate_limit_contact_{contact_info}", 6, 3600)
        
        self.assertFalse(OTPService._check_rate_limit(contact_info, self.ip_address))
    
    def test_increment_rate_limit(self):
        """Test rate limit counter increment"""
        contact_info = 'test@example.com'
        
        # Initially should be 0
        self.assertEqual(cache.get(f"otp_rate_limit_contact_{contact_info}", 0), 0)
        
        # Increment
        OTPService._increment_rate_limit(contact_info, self.ip_address)
        
        # Should be 1 now
        self.assertEqual(cache.get(f"otp_rate_limit_contact_{contact_info}"), 1)
        self.assertEqual(cache.get(f"otp_rate_limit_ip_{self.ip_address}"), 1)
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_send_otp_sms_success(self, mock_send_sms):
        """Test successful SMS OTP sending"""
        mock_send_sms.return_value = True
        
        success, message = OTPService.send_otp(
            contact_info='+989123456789',
            delivery_method='sms',
            purpose='login',
            user=self.user,
            ip_address=self.ip_address
        )
        
        self.assertTrue(success)
        self.assertIn('موفقیت', message)
        
        # Check OTP record created
        otp_obj = OtpCode.objects.filter(
            contact_info='+989123456789',
            purpose='login'
        ).first()
        self.assertIsNotNone(otp_obj)
        self.assertEqual(otp_obj.delivery_method, 'sms')
        self.assertEqual(otp_obj.user, self.user)
    
    @patch('users.services.email.EmailService.send_otp_email')
    def test_send_otp_email_success(self, mock_send_email):
        """Test successful email OTP sending"""
        mock_send_email.return_value = True
        
        success, message = OTPService.send_otp(
            contact_info='test@example.com',
            delivery_method='email',
            purpose='login',
            user=self.user,
            ip_address=self.ip_address
        )
        
        self.assertTrue(success)
        self.assertIn('موفقیت', message)
        
        # Check OTP record created
        otp_obj = OtpCode.objects.filter(
            contact_info='test@example.com',
            purpose='login'
        ).first()
        self.assertIsNotNone(otp_obj)
        self.assertEqual(otp_obj.delivery_method, 'email')
    
    def test_send_otp_rate_limit_exceeded(self):
        """Test OTP sending when rate limit exceeded"""
        contact_info = 'test@example.com'
        
        # Set rate limit exceeded
        cache.set(f"otp_rate_limit_contact_{contact_info}", 6, 3600)
        
        success, message = OTPService.send_otp(
            contact_info=contact_info,
            delivery_method='email',
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertFalse(success)
        self.assertIn('حد مجاز', message)
    
    def test_send_otp_invalid_delivery_method(self):
        """Test OTP sending with invalid delivery method"""
        success, message = OTPService.send_otp(
            contact_info='test@example.com',
            delivery_method='invalid',
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertFalse(success)
        self.assertIn('نامعتبر', message)
    
    def test_verify_otp_success(self):
        """Test successful OTP verification"""
        # Create OTP record
        from users.models import generate_hash
        code = '123456'
        hashed_code = generate_hash(code)
        
        otp_obj = OtpCode.objects.create(
            user=self.user,
            contact_info='test@example.com',
            delivery_method='email',
            hashed_code=hashed_code,
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            ip_address=self.ip_address
        )
        
        success, message, returned_otp = OTPService.verify_otp(
            contact_info='test@example.com',
            code=code,
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertTrue(success)
        self.assertIn('موفقیت', message)
        self.assertEqual(returned_otp, otp_obj)
        
        # Check OTP marked as used
        otp_obj.refresh_from_db()
        self.assertTrue(otp_obj.used)
    
    def test_verify_otp_invalid_code(self):
        """Test OTP verification with invalid code"""
        # Create OTP record
        from users.models import generate_hash
        code = '123456'
        hashed_code = generate_hash(code)
        
        OtpCode.objects.create(
            user=self.user,
            contact_info='test@example.com',
            delivery_method='email',
            hashed_code=hashed_code,
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            ip_address=self.ip_address
        )
        
        success, message, returned_otp = OTPService.verify_otp(
            contact_info='test@example.com',
            code='654321',  # Wrong code
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertFalse(success)
        self.assertIn('اشتباه', message)
        self.assertIsNone(returned_otp)
    
    def test_verify_otp_expired(self):
        """Test OTP verification with expired code"""
        # Create expired OTP record
        from users.models import generate_hash
        code = '123456'
        hashed_code = generate_hash(code)
        
        OtpCode.objects.create(
            user=self.user,
            contact_info='test@example.com',
            delivery_method='email',
            hashed_code=hashed_code,
            purpose='login',
            expires_at=timezone.now() - timedelta(minutes=1),  # Expired
            ip_address=self.ip_address
        )
        
        success, message, returned_otp = OTPService.verify_otp(
            contact_info='test@example.com',
            code=code,
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertFalse(success)
        self.assertIn('منقضی', message)
        self.assertIsNone(returned_otp)
    
    def test_verify_otp_not_found(self):
        """Test OTP verification when no OTP exists"""
        success, message, returned_otp = OTPService.verify_otp(
            contact_info='test@example.com',
            code='123456',
            purpose='login',
            ip_address=self.ip_address
        )
        
        self.assertFalse(success)
        self.assertIn('یافت نشد', message)
        self.assertIsNone(returned_otp)
    
    def test_cleanup_expired_otps(self):
        """Test cleanup of expired OTP codes"""
        # Create expired OTP
        from users.models import generate_hash
        OtpCode.objects.create(
            user=self.user,
            contact_info='test@example.com',
            delivery_method='email',
            hashed_code=generate_hash('123456'),
            purpose='login',
            expires_at=timezone.now() - timedelta(minutes=10),
            ip_address=self.ip_address
        )
        
        # Create valid OTP
        OtpCode.objects.create(
            user=self.user,
            contact_info='test2@example.com',
            delivery_method='email',
            hashed_code=generate_hash('654321'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            ip_address=self.ip_address
        )
        
        # Should have 2 OTPs
        self.assertEqual(OtpCode.objects.count(), 2)
        
        # Cleanup expired
        cleaned_count = OTPService.cleanup_expired_otps()
        
        # Should have cleaned 1 and left 1
        self.assertEqual(cleaned_count, 1)
        self.assertEqual(OtpCode.objects.count(), 1)
    
    @override_settings(DEBUG=True)
    def test_send_sms_debug_mode(self):
        """Test SMS sending in debug mode"""
        with patch('builtins.print') as mock_print:
            result = OTPService._send_sms('+989123456789', '123456', 'login')
            self.assertTrue(result)
            mock_print.assert_called_once()
    
    @override_settings(DEBUG=False, KAVENEGAR_API_KEY='test-key', OTP_SMS_BACKEND='kavenegar')
    @patch('requests.post')
    def test_send_sms_production_success(self, mock_post):
        """Test SMS sending in production mode - success"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        result = OTPService._send_sms('+989123456789', '123456', 'login')
        self.assertTrue(result)
        mock_post.assert_called_once()
    
    @override_settings(DEBUG=False, KAVENEGAR_API_KEY='test-key', OTP_SMS_BACKEND='kavenegar')
    @patch('requests.post')
    def test_send_sms_production_failure(self, mock_post):
        """Test SMS sending in production mode - failure"""
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_post.return_value = mock_response
        
        result = OTPService._send_sms('+989123456789', '123456', 'login')
        self.assertFalse(result)


class EmailServiceTestCase(TestCase):
    """Test cases for EmailService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            first_name='Test',
            last_name='User'
        )
    
    def test_send_otp_email(self):
        """Test sending OTP email"""
        success = EmailService.send_otp_email(
            email='test@example.com',
            code='123456',
            purpose='login'
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('کد تأیید', email.subject)
        self.assertIn('123456', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    def test_send_verification_email(self):
        """Test sending email verification"""
        success = EmailService.send_verification_email(
            user=self.user,
            verification_token='test-token-123'
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('تأیید ایمیل', email.subject)
        self.assertIn('test-token-123', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    def test_send_password_reset_email(self):
        """Test sending password reset email"""
        success = EmailService.send_password_reset_email(
            user=self.user,
            reset_token='reset-token-456'
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('بازیابی رمز عبور', email.subject)
        self.assertIn('reset-token-456', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    def test_send_security_alert(self):
        """Test sending security alert email"""
        success = EmailService.send_security_alert(
            user=self.user,
            event='login_from_new_location',
            ip_address='192.168.1.1',
            details={'location': 'Tehran, Iran'}
        )
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('هشدار امنیتی', email.subject)
        self.assertIn('192.168.1.1', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    def test_send_welcome_email(self):
        """Test sending welcome email"""
        success = EmailService.send_welcome_email(user=self.user)
        
        self.assertTrue(success)
        self.assertEqual(len(mail.outbox), 1)
        
        email = mail.outbox[0]
        self.assertIn('خوش آمدید', email.subject)
        self.assertIn('Test', email.body)
        self.assertEqual(email.to, ['test@example.com'])
    
    @patch('users.services.email.render_to_string')
    def test_send_email_template_error(self, mock_render):
        """Test email sending with template error"""
        mock_render.side_effect = Exception("Template error")
        
        success = EmailService.send_otp_email(
            email='test@example.com',
            code='123456',
            purpose='login'
        )
        
        self.assertFalse(success)
        self.assertEqual(len(mail.outbox), 0)
    
    def test_send_email_with_html_content(self):
        """Test that emails contain both HTML and text content"""
        EmailService.send_otp_email(
            email='test@example.com',
            code='123456',
            purpose='login'
        )
        
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        
        # Check that email has alternatives (HTML version)
        self.assertTrue(hasattr(email, 'alternatives'))
        self.assertTrue(len(email.alternatives) > 0)
        
        # Check HTML content
        html_content = email.alternatives[0][0]
        self.assertIn('<html', html_content)
        self.assertIn('123456', html_content)
    
    def test_otp_email_different_purposes(self):
        """Test OTP email with different purposes"""
        purposes = ['login', 'register', 'password_reset', 'email_verify']
        
        for purpose in purposes:
            with self.subTest(purpose=purpose):
                mail.outbox.clear()
                
                success = EmailService.send_otp_email(
                    email='test@example.com',
                    code='123456',
                    purpose=purpose
                )
                
                self.assertTrue(success)
                self.assertEqual(len(mail.outbox), 1)
                
                email = mail.outbox[0]
                self.assertIn('کد تأیید', email.subject)


class BackwardCompatibilityTestCase(TestCase):
    """Test backward compatibility functions"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789'
        )
    
    def test_generate_otp_function(self):
        """Test backward compatibility generate_otp function"""
        from users.services.otp import generate_otp
        
        otp = generate_otp()
        self.assertEqual(len(otp), 6)
        self.assertTrue(otp.isdigit())
    
    @patch('users.services.otp.OTPService.send_otp')
    def test_send_otp_function(self, mock_send_otp):
        """Test backward compatibility send_otp function"""
        from users.services.otp import send_otp
        
        mock_send_otp.return_value = (True, 'Success')
        
        result = send_otp('+989123456789', 'login')
        self.assertTrue(result)
        
        mock_send_otp.assert_called_once_with(
            contact_info='+989123456789',
            delivery_method='sms',
            purpose='login'
        )
    
    @patch('users.services.otp.OTPService.verify_otp')
    def test_verify_otp_function(self, mock_verify_otp):
        """Test backward compatibility verify_otp function"""
        from users.services.otp import verify_otp
        
        mock_verify_otp.return_value = (True, 'Success', None)
        
        result = verify_otp('+989123456789', '123456', 'login')
        self.assertTrue(result)
        
        mock_verify_otp.assert_called_once_with(
            contact_info='+989123456789',
            code='123456',
            purpose='login'
        )
"""
Integration tests for password reset functionality.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.conf import settings
from unittest.mock import patch, MagicMock
from users.models import OtpCode, SecurityLog
from users.services.otp import OTPService
from users.services.security import SecurityService

User = get_user_model()


class PasswordResetIntegrationTest(TestCase):
    """Integration tests for the complete password reset flow"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test users
        self.user_with_email = User.objects.create_user(
            username='testuser1',
            email='test@example.com',
            password='oldpassword123'
        )
        
        self.user_with_phone = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            phone='+989123456789',
            password='oldpassword123'
        )
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_complete_password_reset_flow_with_email(self):
        """Test complete password reset flow using email"""
        
        # Step 1: Request password reset
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            self.assertIn('کد تأیید با موفقیت ارسال شد', data['message'])
            
            # Verify OTP was created
            otp = OtpCode.objects.filter(
                contact_info='test@example.com',
                purpose='password_reset',
                used=False
            ).first()
            self.assertIsNotNone(otp)
            self.assertEqual(otp.delivery_method, 'email')
            
            # Verify email was called
            mock_email.assert_called_once()
        
        # Step 2: Verify OTP (should fail with wrong code)
        response = self.client.post(
            reverse('api_users:password-reset-verify'),
            data=json.dumps({
                'contact_info': 'test@example.com',
                'otp_code': '000000'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        print(f"Response data: {data}")  # Debug print
        self.assertFalse(data.get('success', False))
        
        # Step 3: Verify OTP with correct code
        with patch('users.services.otp.OTPService.verify_otp') as mock_verify:
            mock_verify.return_value = (True, 'کد تأیید با موفقیت تأیید شد.', None)
            
            response = self.client.post(
                reverse('api_users:password-reset-verify'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'otp_code': '123456'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
        
        # Step 4: Set new password (should fail - OTP already used)
        response = self.client.post(
            reverse('api_users:password-reset-confirm'),
            data=json.dumps({
                'contact_info': 'test@example.com',
                'otp_code': '123456',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Step 5: Request new OTP and complete the flow
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Request new OTP
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Set new password with mocked OTP verification
            with patch('users.services.otp.OTPService.verify_otp') as mock_verify_confirm:
                with patch('users.services.email.EmailService.send_security_alert') as mock_alert:
                    mock_verify_confirm.return_value = (True, 'کد تأیید با موفقیت تأیید شد.', None)
                    mock_alert.return_value = True
                    
                    response = self.client.post(
                        reverse('api_users:password-reset-confirm'),
                        data=json.dumps({
                            'contact_info': 'test@example.com',
                            'otp_code': '654321',
                            'new_password': 'newpassword123',
                            'confirm_password': 'newpassword123'
                        }),
                        content_type='application/json'
                    )
                    
                    self.assertEqual(response.status_code, 200)
                    data = response.json()
                    self.assertTrue(data['success'])
                    self.assertIn('رمز عبور با موفقیت تغییر یافت', data['message'])
                    
                    # Verify security alert was sent
                    mock_alert.assert_called_once()
        
        # Step 6: Verify password was changed
        self.user_with_email.refresh_from_db()
        self.assertTrue(self.user_with_email.check_password('newpassword123'))
        self.assertFalse(self.user_with_email.check_password('oldpassword123'))
        
        # Verify failed login attempts were reset
        self.assertEqual(self.user_with_email.failed_login_attempts, 0)
        
        # Verify security log was created
        security_logs = SecurityLog.objects.filter(
            user=self.user_with_email,
            event_type='password_changed'
        )
        self.assertTrue(security_logs.exists())
    
    def test_complete_password_reset_flow_with_sms(self):
        """Test complete password reset flow using SMS"""
        
        with patch('users.services.otp.OTPService._send_sms') as mock_sms:
            mock_sms.return_value = True
            
            # Request password reset via SMS
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': '+989123456789',
                    'delivery_method': 'sms'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
            
            # Verify OTP was created with SMS delivery method
            otp = OtpCode.objects.filter(
                contact_info='+989123456789',
                purpose='password_reset',
                used=False
            ).first()
            self.assertIsNotNone(otp)
            self.assertEqual(otp.delivery_method, 'sms')
            
            # Verify SMS was called
            mock_sms.assert_called_once()
    
    def test_password_reset_rate_limiting(self):
        """Test rate limiting for password reset requests"""
        
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Make multiple requests to trigger rate limiting
            for i in range(4):  # Default limit is 3 per hour
                response = self.client.post(
                    reverse('api_users:password-reset-request'),
                    data=json.dumps({
                        'contact_info': 'test@example.com',
                        'delivery_method': 'email'
                    }),
                    content_type='application/json'
                )
                
                if i < 3:
                    self.assertEqual(response.status_code, 200)
                else:
                    # Should be rate limited
                    self.assertEqual(response.status_code, 429)
                    data = response.json()
                    self.assertFalse(data['success'])
                    self.assertIn('تعداد درخواست‌های شما از حد مجاز گذشته است', data['message'])
    
    def test_password_reset_with_invalid_contact_info(self):
        """Test password reset with non-existent contact info"""
        
        # Test with non-existent email
        response = self.client.post(
            reverse('api_users:password-reset-request'),
            data=json.dumps({
                'contact_info': 'nonexistent@example.com',
                'delivery_method': 'email'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        
        # Test with non-existent phone
        response = self.client.post(
            reverse('api_users:password-reset-request'),
            data=json.dumps({
                'contact_info': '+989999999999',
                'delivery_method': 'sms'
            }),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
    
    def test_password_reset_otp_expiry(self):
        """Test OTP expiry handling"""
        
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Request password reset
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Get OTP and manually expire it
            otp = OtpCode.objects.filter(
                contact_info='test@example.com',
                purpose='password_reset',
                used=False
            ).first()
            
            from django.utils import timezone
            from datetime import timedelta
            otp.expires_at = timezone.now() - timedelta(minutes=1)
            otp.save()
            
            # Try to verify expired OTP
            response = self.client.post(
                reverse('api_users:password-reset-verify'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'otp_code': '123456'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            # DRF validation errors don't have 'success' key
            data = response.json()
            self.assertTrue('non_field_errors' in data or 'otp_code' in data)
    
    def test_password_reset_max_attempts(self):
        """Test maximum OTP verification attempts"""
        
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Request password reset
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Try wrong OTP multiple times
            for i in range(4):  # Default max attempts is 3
                response = self.client.post(
                    reverse('api_users:password-reset-verify'),
                    data=json.dumps({
                        'contact_info': 'test@example.com',
                        'otp_code': '000000'
                    }),
                    content_type='application/json'
                )
                
                self.assertEqual(response.status_code, 400)
                # DRF validation errors don't have 'success' key
                data = response.json()
                self.assertTrue('non_field_errors' in data or 'otp_code' in data)
    
    def test_password_validation(self):
        """Test password validation in reset confirm"""
        
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Request and get valid OTP
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            otp = OtpCode.objects.filter(
                contact_info='test@example.com',
                purpose='password_reset',
                used=False
            ).first()
            
            test_code = '123456'
            from users.models import generate_hash
            otp.hashed_code = generate_hash(test_code)
            otp.save()
            
            # Test password mismatch
            response = self.client.post(
                reverse('api_users:password-reset-confirm'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'otp_code': test_code,
                    'new_password': 'newpassword123',
                    'confirm_password': 'differentpassword123'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
            
            # Test weak password
            otp.used = False
            otp.save()
            
            response = self.client.post(
                reverse('api_users:password-reset-confirm'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'otp_code': test_code,
                    'new_password': '123',
                    'confirm_password': '123'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 400)
    
    def test_web_password_reset_flow(self):
        """Test web interface for password reset"""
        
        # Test password reset request page
        response = self.client.get(reverse('users:password-reset-request'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'فراموشی رمز عبور')
        
        # Test password reset verify page
        response = self.client.get(
            reverse('users:password-reset-verify') + 
            '?contact_info=test@example.com&delivery_method=email'
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تأیید کد و تنظیم رمز جدید')
        
        # Test AJAX request to password reset request
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            response = self.client.post(
                reverse('users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data['success'])
    
    def test_security_logging(self):
        """Test that security events are properly logged"""
        
        with patch('users.services.email.EmailService.send_otp_email') as mock_email:
            mock_email.return_value = True
            
            # Request password reset
            response = self.client.post(
                reverse('api_users:password-reset-request'),
                data=json.dumps({
                    'contact_info': 'test@example.com',
                    'delivery_method': 'email'
                }),
                content_type='application/json'
            )
            
            # Check that security log was created
            security_logs = SecurityLog.objects.filter(
                event_type='password_reset_requested',
                user=self.user_with_email
            )
            self.assertTrue(security_logs.exists())
            
            log = security_logs.first()
            self.assertEqual(log.severity, 'medium')
            self.assertEqual(log.details['contact_info'], 'test@example.com')
            self.assertEqual(log.details['delivery_method'], 'email')
    
    def test_cleanup_expired_otps(self):
        """Test cleanup of expired OTP codes"""
        
        # Create some expired OTPs
        from django.utils import timezone
        from datetime import timedelta
        
        expired_otp = OtpCode.objects.create(
            user=self.user_with_email,
            contact_info='test@example.com',
            delivery_method='email',
            hashed_code='dummy_hash',
            purpose='password_reset',
            expires_at=timezone.now() - timedelta(hours=1),
            ip_address='127.0.0.1'
        )
        
        # Run cleanup
        deleted_count = OTPService.cleanup_expired_otps()
        
        # Verify expired OTP was deleted
        self.assertGreater(deleted_count, 0)
        self.assertFalse(OtpCode.objects.filter(id=expired_otp.id).exists())


class PasswordResetSerializerTest(TestCase):
    """Test password reset serializers"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='oldpassword123'
        )
    
    def test_password_reset_request_serializer_validation(self):
        """Test PasswordResetRequestSerializer validation"""
        from users.serializers import PasswordResetRequestSerializer
        
        # Valid email
        serializer = PasswordResetRequestSerializer(data={
            'contact_info': 'test@example.com',
            'delivery_method': 'email'
        })
        self.assertTrue(serializer.is_valid())
        
        # Valid phone
        serializer = PasswordResetRequestSerializer(data={
            'contact_info': '+989123456789',
            'delivery_method': 'sms'
        })
        self.assertTrue(serializer.is_valid())
        
        # Invalid email (user doesn't exist)
        serializer = PasswordResetRequestSerializer(data={
            'contact_info': 'nonexistent@example.com',
            'delivery_method': 'email'
        })
        self.assertFalse(serializer.is_valid())
        
        # Invalid phone (user doesn't exist)
        serializer = PasswordResetRequestSerializer(data={
            'contact_info': '+989999999999',
            'delivery_method': 'sms'
        })
        self.assertFalse(serializer.is_valid())
    
    def test_password_reset_confirm_serializer(self):
        """Test PasswordResetConfirmSerializer"""
        from users.serializers import PasswordResetConfirmSerializer
        
        # Create valid OTP
        with patch('users.services.otp.OTPService.verify_otp') as mock_verify:
            mock_verify.return_value = (True, 'Success', None)
            
            # Valid data
            serializer = PasswordResetConfirmSerializer(data={
                'contact_info': 'test@example.com',
                'otp_code': '123456',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            })
            self.assertTrue(serializer.is_valid())
            
            # Password mismatch
            serializer = PasswordResetConfirmSerializer(data={
                'contact_info': 'test@example.com',
                'otp_code': '123456',
                'new_password': 'newpassword123',
                'confirm_password': 'differentpassword'
            })
            self.assertFalse(serializer.is_valid())
            self.assertIn('Passwords do not match', str(serializer.errors))
        
        # Invalid OTP
        with patch('users.services.otp.OTPService.verify_otp') as mock_verify:
            mock_verify.return_value = (False, 'Invalid OTP', None)
            
            serializer = PasswordResetConfirmSerializer(data={
                'contact_info': 'test@example.com',
                'otp_code': '000000',
                'new_password': 'newpassword123',
                'confirm_password': 'newpassword123'
            })
            self.assertFalse(serializer.is_valid())
"""
Integration tests for email and phone verification system.
"""
import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, MagicMock

from users.models import EmailVerificationToken, OtpCode
from users.services.verification import VerificationService
from users.services.otp import OTPService

User = get_user_model()


class EmailVerificationIntegrationTest(TestCase):
    """Integration tests for email verification system"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_send_email_verification_api(self):
        """Test sending email verification via API"""
        url = reverse('api_users:send-email-verification')
        response = self.client.post(url, {
            'email': self.user.email
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that token was created
        self.assertTrue(EmailVerificationToken.objects.filter(
            user=self.user,
            email=self.user.email
        ).exists())
        
        # Check that email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('تأیید ایمیل', mail.outbox[0].subject)
    
    def test_verify_email_api(self):
        """Test email verification via API"""
        # First send verification
        success, message = VerificationService.send_email_verification(
            user=self.user,
            email=self.user.email
        )
        self.assertTrue(success)
        
        # Get the token
        token_obj = EmailVerificationToken.objects.get(
            user=self.user,
            email=self.user.email
        )
        
        # Verify email
        url = reverse('api_users:verify-email')
        response = self.client.post(url, {
            'token': token_obj.token
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that user is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
        
        # Check that token is marked as used
        token_obj.refresh_from_db()
        self.assertTrue(token_obj.used)
    
    def test_verify_email_web_view(self):
        """Test email verification via web view"""
        # First send verification
        success, message = VerificationService.send_email_verification(
            user=self.user,
            email=self.user.email
        )
        self.assertTrue(success)
        
        # Get the token
        token_obj = EmailVerificationToken.objects.get(
            user=self.user,
            email=self.user.email
        )
        
        # Verify email via web
        url = reverse('users:verify-email', kwargs={'token': token_obj.token})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'با موفقیت تأیید شد')
        
        # Check that user is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.email_verified)
    
    def test_expired_email_verification_token(self):
        """Test that expired tokens are rejected"""
        # Create expired token
        token = VerificationService.generate_verification_token()
        EmailVerificationToken.objects.create(
            user=self.user,
            email=self.user.email,
            token=token,
            expires_at=timezone.now() - timedelta(hours=1),
            ip_address='127.0.0.1'
        )
        
        # Try to verify with expired token
        url = reverse('api_users:verify-email')
        response = self.client.post(url, {
            'token': token
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('منقضی', data['message'])
        
        # Check that user is not verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.email_verified)
    
    def test_invalid_email_verification_token(self):
        """Test that invalid tokens are rejected"""
        url = reverse('api_users:verify-email')
        response = self.client.post(url, {
            'token': 'invalid-token'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('نامعتبر', data['message'])


class PhoneVerificationIntegrationTest(TestCase):
    """Integration tests for phone verification system"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_send_phone_verification_api(self, mock_send_sms):
        """Test sending phone verification via API"""
        mock_send_sms.return_value = True
        
        url = reverse('api_users:send-phone-verification')
        response = self.client.post(url, {
            'phone': self.user.phone
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that OTP was created
        self.assertTrue(OtpCode.objects.filter(
            user=self.user,
            contact_info=self.user.phone,
            purpose='phone_verify'
        ).exists())
        
        # Check that SMS was sent
        mock_send_sms.assert_called_once()
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_verify_phone_api(self, mock_send_sms):
        """Test phone verification via API"""
        mock_send_sms.return_value = True
        
        # First send verification OTP
        success, message = VerificationService.send_phone_verification(
            user=self.user,
            phone=self.user.phone
        )
        self.assertTrue(success)
        
        # Get the OTP (we need to get the actual code for testing)
        otp_obj = OtpCode.objects.get(
            user=self.user,
            contact_info=self.user.phone,
            purpose='phone_verify'
        )
        
        # For testing, we'll create a known OTP
        test_code = '123456'
        from users.models import generate_hash
        otp_obj.hashed_code = generate_hash(test_code)
        otp_obj.save()
        
        # Verify phone
        url = reverse('api_users:verify-phone')
        response = self.client.post(url, {
            'phone': self.user.phone,
            'otp_code': test_code
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that user is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)
        
        # Check that OTP is marked as used
        otp_obj.refresh_from_db()
        self.assertTrue(otp_obj.used)
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_verify_phone_web_view(self, mock_send_sms):
        """Test phone verification via web view"""
        mock_send_sms.return_value = True
        
        # Send verification OTP
        success, message = VerificationService.send_phone_verification(
            user=self.user,
            phone=self.user.phone
        )
        self.assertTrue(success)
        
        # Get the OTP and set known code
        otp_obj = OtpCode.objects.get(
            user=self.user,
            contact_info=self.user.phone,
            purpose='phone_verify'
        )
        
        test_code = '123456'
        from users.models import generate_hash
        otp_obj.hashed_code = generate_hash(test_code)
        otp_obj.save()
        
        # Verify phone via web
        url = reverse('users:verify-phone')
        response = self.client.post(url, json.dumps({
            'otp_code': test_code
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that user is marked as verified
        self.user.refresh_from_db()
        self.assertTrue(self.user.phone_verified)
    
    def test_invalid_phone_otp(self):
        """Test that invalid OTP codes are rejected"""
        url = reverse('api_users:verify-phone')
        response = self.client.post(url, {
            'phone': self.user.phone,
            'otp_code': '000000'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        
        # Check that user is not verified
        self.user.refresh_from_db()
        self.assertFalse(self.user.phone_verified)


class RegistrationWithVerificationTest(TestCase):
    """Integration tests for registration with verification"""
    
    def setUp(self):
        self.client = Client()
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_registration_with_phone_verification(self, mock_send_sms):
        """Test registration with phone verification"""
        mock_send_sms.return_value = True
        
        phone = '+989123456789'
        
        # First send OTP for registration
        success, message = OTPService.send_otp(
            contact_info=phone,
            delivery_method='sms',
            purpose='register'
        )
        self.assertTrue(success)
        
        # Get the OTP and set known code
        otp_obj = OtpCode.objects.get(
            contact_info=phone,
            purpose='register'
        )
        
        test_code = '123456'
        from users.models import generate_hash
        otp_obj.hashed_code = generate_hash(test_code)
        otp_obj.save()
        
        # Register with phone verification
        url = reverse('api_users:register')
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': phone,
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'phone_otp_code': test_code,
            'send_email_verification': True
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.phone, phone)
        self.assertTrue(user.phone_verified)  # Should be verified from registration
        self.assertFalse(user.email_verified)  # Email verification sent but not verified yet
        
        # Check that email verification was sent
        self.assertTrue(EmailVerificationToken.objects.filter(
            user=user,
            email=user.email
        ).exists())
        
        # Check response includes verification status
        self.assertIn('verification_status', data)
        self.assertTrue(data['verification_status']['phone_verified'])
        self.assertTrue(data['verification_status']['email_verification_sent'])
    
    def test_registration_without_phone_verification(self):
        """Test registration without phone (email only)"""
        url = reverse('api_users:register')
        response = self.client.post(url, {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'send_email_verification': True
        }, content_type='application/json')
        
        # Debug: print response details if test fails
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.content}")
        
        self.assertEqual(response.status_code, 201)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertEqual(user.phone, '')
        self.assertFalse(user.phone_verified)
        self.assertFalse(user.email_verified)
        
        # Check that email verification was sent
        self.assertTrue(EmailVerificationToken.objects.filter(
            user=user,
            email=user.email
        ).exists())


class VerificationStatusWebViewTest(TestCase):
    """Integration tests for verification status web view"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_verification_status_page(self):
        """Test verification status page displays correctly"""
        url = reverse('users:verification-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'وضعیت تأیید حساب')
        self.assertContains(response, self.user.email)
        self.assertContains(response, self.user.phone)
        self.assertContains(response, 'تأیید نشده')  # Both should be unverified
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_send_verification_via_status_page(self, mock_send_sms):
        """Test sending verification via status page AJAX"""
        mock_send_sms.return_value = True
        
        url = reverse('users:verification-status')
        
        # Test email verification request
        response = self.client.post(url, json.dumps({
            'verification_type': 'email'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that email verification token was created
        self.assertTrue(EmailVerificationToken.objects.filter(
            user=self.user,
            email=self.user.email
        ).exists())
        
        # Test phone verification request
        response = self.client.post(url, json.dumps({
            'verification_type': 'phone'
        }), content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Check that phone verification OTP was created
        self.assertTrue(OtpCode.objects.filter(
            user=self.user,
            contact_info=self.user.phone,
            purpose='phone_verify'
        ).exists())


class ResendVerificationTest(TestCase):
    """Integration tests for resending verification"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_resend_verification_api(self, mock_send_sms):
        """Test resending verification via API"""
        mock_send_sms.return_value = True
        
        url = reverse('api_users:resend-verification')
        
        # Test resend email verification
        response = self.client.post(url, {
            'verification_type': 'email',
            'contact_info': self.user.email
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        
        # Test resend phone verification
        response = self.client.post(url, {
            'verification_type': 'phone',
            'contact_info': self.user.phone
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
    
    def test_resend_verification_for_nonexistent_user(self):
        """Test resending verification for non-existent user"""
        self.client.logout()  # Test as anonymous user
        
        url = reverse('api_users:resend-verification')
        response = self.client.post(url, {
            'verification_type': 'email',
            'contact_info': 'nonexistent@example.com'
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 404)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('یافت نشد', data['message'])


class RateLimitingTest(TestCase):
    """Integration tests for rate limiting in verification"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    @patch('users.services.security.SecurityService.check_rate_limit')
    def test_email_verification_rate_limiting(self, mock_rate_limit):
        """Test rate limiting for email verification"""
        # Mock rate limit exceeded
        mock_rate_limit.return_value = (False, {'retry_after': 3600})
        
        url = reverse('api_users:send-email-verification')
        response = self.client.post(url, {
            'email': self.user.email
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 429)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('حد مجاز', data['message'])
        self.assertEqual(data['retry_after'], 3600)
    
    @patch('users.services.otp.OTPService._check_rate_limit')
    def test_phone_verification_rate_limiting(self, mock_rate_limit):
        """Test rate limiting for phone verification"""
        # Mock rate limit exceeded
        mock_rate_limit.return_value = False
        
        url = reverse('api_users:send-phone-verification')
        response = self.client.post(url, {
            'phone': self.user.phone
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('حد مجاز', data['message'])
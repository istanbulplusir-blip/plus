"""
Integration tests for the user authentication system.
These tests cover complete user flows and interactions between components.
"""

import json
import time
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.test import TestCase, TransactionTestCase
from django.test.client import Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core import mail
from django.conf import settings
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import OtpCode, UserSession, PasswordResetToken, SecurityLog, generate_hash
from users.services.otp import OTPService
from users.services.security import SecurityService

User = get_user_model()


class RegistrationIntegrationTest(APITestCase):
    """Integration tests for the complete registration process"""
    
    def setUp(self):
        self.client = APIClient()
        self.registration_url = reverse('api_users:register')
        self.valid_registration_data = {
            'username': 'testuser',
            'email': 'test@example.com',
            'phone': '+989123456789',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_complete_registration_flow(self):
        """Test the complete registration flow from start to finish"""
        # Step 1: Register user
        response = self.client.post(self.registration_url, self.valid_registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('verification_status', response.data)
        
        # Verify user was created in database
        user = User.objects.get(username='testuser')
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.phone, '+989123456789')
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        
        # Verify security log was created
        security_logs = SecurityLog.objects.filter(
            user=user,
            event_type='user_registered'
        )
        self.assertTrue(security_logs.exists())
        
        # Verify user session was created
        sessions = UserSession.objects.filter(user=user, is_active=True)
        self.assertTrue(sessions.exists())
        
        # Step 2: Verify tokens work for authenticated requests
        access_token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        profile_url = reverse('api_users:profile')
        profile_response = self.client.get(profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertEqual(profile_response.data['user']['username'], 'testuser')
    
    def test_registration_with_duplicate_email(self):
        """Test registration with duplicate email"""
        # Create existing user
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='password123'
        )
        
        # Try to register with same email
        response = self.client.post(self.registration_url, self.valid_registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_registration_rate_limiting(self):
        """Test registration rate limiting"""
        # Mock rate limiting to trigger limit
        with patch.object(SecurityService, 'check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = (False, {'retry_after': 3600})
            
            response = self.client.post(self.registration_url, self.valid_registration_data)
            
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertFalse(response.data['success'])
            self.assertIn('retry_after', response.data)
    
    def test_registration_validation_errors(self):
        """Test registration with various validation errors"""
        # Test weak password
        weak_password_data = self.valid_registration_data.copy()
        weak_password_data['password'] = '123'
        weak_password_data['password_confirm'] = '123'
        
        response = self.client.post(self.registration_url, weak_password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test password mismatch
        mismatch_data = self.valid_registration_data.copy()
        mismatch_data['password_confirm'] = 'DifferentPassword123!'
        
        response = self.client.post(self.registration_url, mismatch_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test invalid email
        invalid_email_data = self.valid_registration_data.copy()
        invalid_email_data['email'] = 'invalid-email'
        
        response = self.client.post(self.registration_url, invalid_email_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class LoginIntegrationTest(APITestCase):
    """Integration tests for the complete login process"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('api_users:login')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
    
    def test_successful_login_flow(self):
        """Test successful login flow"""
        login_data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(self.login_url, login_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('user', response.data)
        self.assertIn('tokens', response.data)
        self.assertIn('security_info', response.data)
        
        # Verify security log was created
        security_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_success'
        )
        self.assertTrue(security_logs.exists())
        
        # Verify user session was created/updated
        sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertTrue(sessions.exists())
        
        # Verify failed attempts were reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
    
    def test_failed_login_attempts_and_lockout(self):
        """Test failed login attempts and account lockout"""
        login_data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        
        # First two failed attempts
        for i in range(2):
            response = self.client.post(self.login_url, login_data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            self.user.refresh_from_db()
            self.assertEqual(self.user.failed_login_attempts, i + 1)
            self.assertFalse(self.user.is_locked())
        
        # Third failed attempt should lock the account
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 3)
        self.assertTrue(self.user.is_locked())
        
        # Fourth attempt should return locked account error
        response = self.client.post(self.login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertIn('locked_until', response.data)
        
        # Verify security logs
        failed_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_failed'
        )
        self.assertEqual(failed_logs.count(), 3)
        
        locked_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_attempt_locked_account'
        )
        self.assertTrue(locked_logs.exists())
    
    def test_login_rate_limiting(self):
        """Test login rate limiting"""
        with patch.object(SecurityService, 'check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = (False, {'retry_after': 900})
            
            login_data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(self.login_url, login_data)
            
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertFalse(response.data['success'])
            self.assertIn('retry_after', response.data)
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection during login"""
        with patch.object(SecurityService, 'check_suspicious_activity') as mock_suspicious:
            mock_suspicious.return_value = (True, 'Login from different country: Unknown')
            
            login_data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(self.login_url, login_data)
            
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertFalse(response.data['success'])
            self.assertTrue(response.data['requires_verification'])
            self.assertIn('verification_methods', response.data)
            
            # Verify security log was created
            security_logs = SecurityLog.objects.filter(
                user=self.user,
                event_type='suspicious_login_attempt'
            )
            self.assertTrue(security_logs.exists())


class OTPIntegrationTest(APITestCase):
    """Integration tests for OTP functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.send_otp_url = reverse('api_users:send-otp')
        self.verify_otp_url = reverse('api_users:verify-otp')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_sms_otp_flow(self, mock_send_sms):
        """Test complete SMS OTP flow"""
        mock_send_sms.return_value = True
        
        # Step 1: Send OTP
        send_data = {
            'contact_info': '+989123456789',
            'delivery_method': 'sms',
            'purpose': 'login'
        }
        
        response = self.client.post(self.send_otp_url, send_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('delivery_info', response.data)
        
        # Verify OTP was created in database
        otp_codes = OtpCode.objects.filter(
            contact_info='+989123456789',
            delivery_method='sms',
            purpose='login',
            used=False
        )
        self.assertTrue(otp_codes.exists())
        otp_code = otp_codes.first()
        
        # Step 2: Verify OTP (simulate correct code)
        with patch.object(OtpCode, 'verify_code', return_value=True):
            verify_data = {
                'contact_info': '+989123456789',
                'otp': '123456',
                'purpose': 'login'
            }
            
            response = self.client.post(self.verify_otp_url, verify_data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            
            # Verify OTP was marked as used
            otp_code.refresh_from_db()
            self.assertTrue(otp_code.used)
    
    @patch('users.services.email.EmailService.send_otp_email')
    def test_email_otp_flow(self, mock_send_email):
        """Test complete email OTP flow"""
        mock_send_email.return_value = True
        
        # Step 1: Send OTP via email
        send_data = {
            'contact_info': 'test@example.com',
            'delivery_method': 'email',
            'purpose': 'login'
        }
        
        response = self.client.post(self.send_otp_url, send_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify OTP was created
        otp_codes = OtpCode.objects.filter(
            contact_info='test@example.com',
            delivery_method='email',
            purpose='login',
            used=False
        )
        self.assertTrue(otp_codes.exists())
    
    def test_otp_rate_limiting(self):
        """Test OTP rate limiting"""
        with patch.object(SecurityService, 'check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = (False, {'retry_after': 3600})
            
            send_data = {
                'contact_info': '+989123456789',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            
            response = self.client.post(self.send_otp_url, send_data)
            
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            self.assertFalse(response.data['success'])
            self.assertIn('retry_after', response.data)
    
    def test_otp_expiry_and_attempts(self):
        """Test OTP expiry and attempt limits"""
        # Create expired OTP
        expired_otp = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('123456'),
            purpose='login',
            expires_at=timezone.now() - timedelta(minutes=1),
            ip_address='127.0.0.1'
        )
        
        # Try to verify expired OTP
        verify_data = {
            'contact_info': '+989123456789',
            'otp': '123456',
            'purpose': 'login'
        }
        
        response = self.client.post(self.verify_otp_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Create OTP with max attempts
        max_attempts_otp = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('654321'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            attempts=3,
            ip_address='127.0.0.1'
        )
        
        # Try to verify OTP with max attempts
        verify_data['otp'] = '654321'
        response = self.client.post(self.verify_otp_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class PasswordResetIntegrationTest(APITestCase):
    """Integration tests for password reset functionality"""
    
    def setUp(self):
        self.client = APIClient()
        self.request_url = reverse('api_users:password-reset-request')
        self.verify_url = reverse('api_users:password-reset-verify')
        self.confirm_url = reverse('api_users:password-reset-confirm')
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='OldPassword123!'
        )
    
    @patch('users.services.otp.OTPService.send_otp')
    def test_complete_password_reset_flow(self, mock_send_otp):
        """Test complete password reset flow"""
        mock_send_otp.return_value = (True, 'OTP sent successfully')
        
        # Step 1: Request password reset
        request_data = {
            'contact_info': 'test@example.com',
            'delivery_method': 'email'
        }
        
        response = self.client.post(self.request_url, request_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify OTP was created
        otp_codes = OtpCode.objects.filter(
            contact_info='test@example.com',
            purpose='password_reset',
            used=False
        )
        self.assertTrue(otp_codes.exists())
        
        # Step 2: Verify OTP and get reset token
        with patch.object(OtpCode, 'verify_code', return_value=True):
            verify_data = {
                'contact_info': 'test@example.com',
                'otp': '123456',
                'purpose': 'password_reset'
            }
            
            response = self.client.post(self.verify_url, verify_data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertIn('reset_token', response.data)
            
            reset_token = response.data['reset_token']
        
        # Step 3: Confirm new password
        confirm_data = {
            'token': reset_token,
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify password was changed
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('NewPassword123!'))
        self.assertFalse(self.user.check_password('OldPassword123!'))
        
        # Verify reset token was marked as used
        reset_tokens = PasswordResetToken.objects.filter(token=reset_token)
        self.assertTrue(reset_tokens.exists())
        self.assertTrue(reset_tokens.first().used)
    
    def test_password_reset_with_invalid_token(self):
        """Test password reset with invalid token"""
        confirm_data = {
            'token': 'invalid_token_123',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_password_reset_token_expiry(self):
        """Test password reset with expired token"""
        # Create expired token
        expired_token = PasswordResetToken.objects.create(
            user=self.user,
            token='expired_token_123',
            expires_at=timezone.now() - timedelta(hours=1),
            ip_address='127.0.0.1'
        )
        
        confirm_data = {
            'token': 'expired_token_123',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(self.confirm_url, confirm_data)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class SessionManagementIntegrationTest(APITestCase):
    """Integration tests for session management"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        self.sessions_url = reverse('api_users:user-sessions')
        self.logout_all_url = reverse('api_users:logout-all-devices')
        
        # Authenticate user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_session_listing(self):
        """Test listing user sessions"""
        # Create some sessions
        UserSession.objects.create(
            user=self.user,
            session_key='session1',
            ip_address='192.168.1.1',
            user_agent='Browser 1',
            location='Tehran, Iran'
        )
        UserSession.objects.create(
            user=self.user,
            session_key='session2',
            ip_address='192.168.1.2',
            user_agent='Browser 2',
            location='Isfahan, Iran'
        )
        
        response = self.client.get(self.sessions_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('sessions', response.data)
        self.assertEqual(len(response.data['sessions']), 2)
    
    def test_terminate_specific_session(self):
        """Test terminating a specific session"""
        session = UserSession.objects.create(
            user=self.user,
            session_key='session_to_terminate',
            ip_address='192.168.1.1',
            user_agent='Browser 1'
        )
        
        terminate_url = reverse('api_users:terminate-session', kwargs={'session_id': session.id})
        response = self.client.delete(terminate_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify session was deactivated
        session.refresh_from_db()
        self.assertFalse(session.is_active)
    
    def test_logout_all_devices(self):
        """Test logging out from all devices"""
        # Create multiple sessions
        sessions = []
        for i in range(3):
            session = UserSession.objects.create(
                user=self.user,
                session_key=f'session_{i}',
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i+1}'
            )
            sessions.append(session)
        
        response = self.client.post(self.logout_all_url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify all sessions were deactivated
        for session in sessions:
            session.refresh_from_db()
            self.assertFalse(session.is_active)


class SecurityIntegrationTest(TransactionTestCase):
    """Integration tests for security features"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        cache.clear()  # Clear cache before each test
    
    def test_rate_limiting_integration(self):
        """Test rate limiting across multiple endpoints"""
        # Test registration rate limiting
        registration_url = reverse('api_users:register')
        
        # Make multiple registration attempts
        for i in range(6):  # Assuming limit is 5
            data = {
                'username': f'user{i}',
                'email': f'user{i}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            response = self.client.post(registration_url, data)
            
            if i < 5:  # First 5 should succeed
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            else:  # 6th should be rate limited
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_brute_force_protection(self):
        """Test brute force protection across login attempts"""
        login_url = reverse('api_users:login')
        
        # Make multiple failed login attempts
        for i in range(4):
            data = {
                'username': 'testuser',
                'password': 'WrongPassword'
            }
            response = self.client.post(login_url, data)
            
            if i < 3:  # First 3 attempts should return 401
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            else:  # 4th attempt should return 423 (locked)
                self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        
        # Verify user is locked
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        
        # Verify security logs were created
        failed_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_failed'
        )
        self.assertEqual(failed_logs.count(), 3)
    
    def test_security_logging_integration(self):
        """Test security logging across different events"""
        # Test registration logging
        registration_url = reverse('api_users:register')
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        response = self.client.post(registration_url, registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify registration was logged
        new_user = User.objects.get(username='newuser')
        reg_logs = SecurityLog.objects.filter(
            user=new_user,
            event_type='user_registered'
        )
        self.assertTrue(reg_logs.exists())
        
        # Test login logging
        login_url = reverse('api_users:login')
        login_data = {
            'username': 'newuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify login was logged
        login_logs = SecurityLog.objects.filter(
            user=new_user,
            event_type='login_success'
        )
        self.assertTrue(login_logs.exists())


class PerformanceIntegrationTest(APITestCase):
    """Integration tests for performance-critical endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        # Create multiple users for load testing
        self.users = []
        for i in range(10):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
    
    def test_login_endpoint_performance(self):
        """Test login endpoint performance under load"""
        login_url = reverse('api_users:login')
        
        # Measure time for multiple login requests
        start_time = time.time()
        
        for user in self.users[:5]:  # Test with 5 users
            data = {
                'username': user.username,
                'password': 'TestPassword123!'
            }
            response = self.client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert that 5 logins complete within reasonable time (e.g., 2 seconds)
        self.assertLess(total_time, 2.0, f"Login performance too slow: {total_time}s for 5 requests")
    
    def test_registration_endpoint_performance(self):
        """Test registration endpoint performance"""
        registration_url = reverse('api_users:register')
        
        start_time = time.time()
        
        for i in range(5):
            data = {
                'username': f'perfuser{i}',
                'email': f'perfuser{i}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            response = self.client.post(registration_url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert that 5 registrations complete within reasonable time
        self.assertLess(total_time, 3.0, f"Registration performance too slow: {total_time}s for 5 requests")
    
    def test_profile_endpoint_performance(self):
        """Test profile endpoint performance with database queries"""
        profile_url = reverse('api_users:profile')
        
        # Authenticate as first user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.users[0])
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        # Create some related data to test query optimization
        UserSession.objects.create(
            user=self.users[0],
            session_key='test_session',
            ip_address='127.0.0.1',
            user_agent='Test Browser'
        )
        
        start_time = time.time()
        
        # Make multiple profile requests
        for _ in range(10):
            response = self.client.get(profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Assert that 10 profile requests complete within reasonable time
        self.assertLess(total_time, 1.0, f"Profile performance too slow: {total_time}s for 10 requests")


class CrossBrowserCompatibilityTest(TestCase):
    """Tests for cross-browser compatibility (simulated through different user agents)"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
    
    def test_different_user_agents(self):
        """Test authentication with different user agents (simulating different browsers)"""
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        login_url = reverse('api_users:login')
        
        for user_agent in user_agents:
            with self.subTest(user_agent=user_agent):
                response = self.client.post(
                    login_url,
                    {
                        'username': 'testuser',
                        'password': 'TestPassword123!'
                    },
                    HTTP_USER_AGENT=user_agent,
                    content_type='application/json'
                )
                
                self.assertEqual(response.status_code, 200)
                response_data = json.loads(response.content)
                self.assertTrue(response_data['success'])
                
                # Verify session was created with correct user agent
                sessions = UserSession.objects.filter(
                    user=self.user,
                    user_agent=user_agent
                )
                self.assertTrue(sessions.exists())
    
    def test_mobile_user_agents(self):
        """Test authentication with mobile user agents"""
        mobile_user_agents = [
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G991B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        ]
        
        registration_url = reverse('api_users:register')
        
        for i, user_agent in enumerate(mobile_user_agents):
            with self.subTest(user_agent=user_agent):
                response = self.client.post(
                    registration_url,
                    {
                        'username': f'mobileuser{i}',
                        'email': f'mobileuser{i}@example.com',
                        'password': 'TestPassword123!',
                        'password_confirm': 'TestPassword123!'
                    },
                    HTTP_USER_AGENT=user_agent,
                    content_type='application/json'
                )
                
                self.assertEqual(response.status_code, 201)
                response_data = json.loads(response.content)
                self.assertTrue(response_data['success'])
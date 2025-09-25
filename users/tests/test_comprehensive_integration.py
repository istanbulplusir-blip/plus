"""
Comprehensive integration tests for the complete user authentication system.
This file covers end-to-end testing of all authentication flows and security features.
"""

import json
import time
import threading
from datetime import timedelta
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import (
    OtpCode, UserSession, PasswordResetToken, SecurityLog, 
    EmailVerificationToken, generate_hash
)
from users.services.otp import OTPService
from users.services.security import SecurityService
from users.services.verification import VerificationService

User = get_user_model()


class CompleteRegistrationFlowTest(APITestCase):
    """Test complete registration flow from start to finish"""
    
    def setUp(self):
        self.client = APIClient()
        self.registration_url = reverse('api_users:register')
        self.send_otp_url = reverse('api_users:send-otp')
        self.verify_otp_url = reverse('api_users:verify-otp')
        self.profile_url = reverse('api_users:profile')
        
        cache.clear()  # Clear cache before each test
    
    def test_complete_registration_with_email_verification(self):
        """Test complete registration flow with email verification"""
        # Step 1: Register user
        registration_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '+989123456789',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'New',
            'last_name': 'User'
        }
        
        response = self.client.post(self.registration_url, registration_data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('tokens', response.data)
        
        # Verify user was created
        user = User.objects.get(username='newuser')
        self.assertEqual(user.email, 'newuser@example.com')
        self.assertFalse(user.email_verified)
        self.assertFalse(user.phone_verified)
        
        # Step 2: Use access token for authenticated requests
        access_token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Step 3: Send email verification
        with patch('users.services.email.EmailService.send_verification_email') as mock_email:
            mock_email.return_value = True
            
            verification_response = VerificationService.send_email_verification(
                user=user,
                ip_address='127.0.0.1'
            )
            
            self.assertTrue(verification_response[0])
            mock_email.assert_called_once()
        
        # Step 4: Verify email with token
        verification_token = EmailVerificationToken.objects.filter(user=user).first()
        self.assertIsNotNone(verification_token)
        
        verify_response = VerificationService.verify_email(
            token=verification_token.token,
            ip_address='127.0.0.1'
        )
        
        self.assertTrue(verify_response[0])
        self.assertEqual(verify_response[2], user)
        
        # Verify user email is now verified
        user.refresh_from_db()
        self.assertTrue(user.email_verified)
        
        # Step 5: Send phone verification OTP
        with patch('users.services.otp.OTPService._send_sms') as mock_sms:
            mock_sms.return_value = True
            
            phone_verification_response = VerificationService.send_phone_verification(
                user=user,
                ip_address='127.0.0.1'
            )
            
            self.assertTrue(phone_verification_response[0])
            mock_sms.assert_called_once()
        
        # Step 6: Verify phone with OTP
        otp_code = OtpCode.objects.filter(
            user=user,
            purpose='phone_verify'
        ).first()
        self.assertIsNotNone(otp_code)
        
        # Mock OTP verification
        with patch.object(OtpCode, 'verify_code', return_value=True):
            phone_verify_response = VerificationService.verify_phone(
                user=user,
                phone=user.phone,
                otp_code='123456',
                ip_address='127.0.0.1'
            )
            
            self.assertTrue(phone_verify_response[0])
        
        # Verify user phone is now verified
        user.refresh_from_db()
        self.assertTrue(user.phone_verified)
        
        # Step 7: Check final profile status
        profile_response = self.client.get(self.profile_url)
        
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)
        self.assertTrue(profile_response.data['user']['email_verified'])
        self.assertTrue(profile_response.data['user']['phone_verified'])
        
        # Verify security logs were created
        security_logs = SecurityLog.objects.filter(user=user)
        self.assertGreater(security_logs.count(), 0)
        
        # Verify session was created
        sessions = UserSession.objects.filter(user=user, is_active=True)
        self.assertTrue(sessions.exists())
    
    def test_registration_with_validation_errors(self):
        """Test registration with various validation errors"""
        # Test weak password
        weak_password_data = {
            'username': 'weakuser',
            'email': 'weak@example.com',
            'password': '123',
            'password_confirm': '123'
        }
        
        response = self.client.post(self.registration_url, weak_password_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test password mismatch
        mismatch_data = {
            'username': 'mismatchuser',
            'email': 'mismatch@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'DifferentPassword123!'
        }
        
        response = self.client.post(self.registration_url, mismatch_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Test duplicate email
        User.objects.create_user(
            username='existing',
            email='duplicate@example.com',
            password='TestPassword123!'
        )
        
        duplicate_data = {
            'username': 'newuser',
            'email': 'duplicate@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        response = self.client.post(self.registration_url, duplicate_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CompleteLoginWithOTPFlowTest(APITestCase):
    """Test complete login flow with OTP verification"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('api_users:login')
        self.send_otp_url = reverse('api_users:send-otp')
        self.verify_otp_url = reverse('api_users:verify-otp')
        
        self.user = User.objects.create_user(
            username='otpuser',
            email='otpuser@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
        
        cache.clear()
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_complete_sms_otp_login_flow(self, mock_send_sms):
        """Test complete SMS OTP login flow"""
        mock_send_sms.return_value = True
        
        # Step 1: Send OTP via SMS
        otp_data = {
            'contact_info': '+989123456789',
            'delivery_method': 'sms',
            'purpose': 'login'
        }
        
        response = self.client.post(self.send_otp_url, otp_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['delivery_info']['method'], 'sms')
        
        # Verify OTP was created
        otp_codes = OtpCode.objects.filter(
            contact_info='+989123456789',
            delivery_method='sms',
            purpose='login',
            used=False
        )
        self.assertTrue(otp_codes.exists())
        
        # Step 2: Verify OTP
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
            otp_code = otp_codes.first()
            otp_code.refresh_from_db()
            self.assertTrue(otp_code.used)
        
        # Step 3: Verify security logs
        security_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='otp_sent'
        )
        self.assertTrue(security_logs.exists())
        
        mock_send_sms.assert_called_once()
    
    @patch('users.services.email.EmailService.send_otp_email')
    def test_complete_email_otp_login_flow(self, mock_send_email):
        """Test complete email OTP login flow"""
        mock_send_email.return_value = True
        
        # Step 1: Send OTP via email
        otp_data = {
            'contact_info': 'otpuser@example.com',
            'delivery_method': 'email',
            'purpose': 'login'
        }
        
        response = self.client.post(self.send_otp_url, otp_data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['delivery_info']['method'], 'email')
        
        # Verify OTP was created
        otp_codes = OtpCode.objects.filter(
            contact_info='otpuser@example.com',
            delivery_method='email',
            purpose='login',
            used=False
        )
        self.assertTrue(otp_codes.exists())
        
        # Step 2: Verify OTP
        with patch.object(OtpCode, 'verify_code', return_value=True):
            verify_data = {
                'contact_info': 'otpuser@example.com',
                'otp': '123456',
                'purpose': 'login'
            }
            
            response = self.client.post(self.verify_otp_url, verify_data)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
        
        mock_send_email.assert_called_once()
    
    def test_otp_expiry_and_attempts_limit(self):
        """Test OTP expiry and maximum attempts"""
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
        self.assertFalse(response.data['success'])
        
        # Create OTP with maximum attempts
        max_attempts_otp = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('654321'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            attempts=3,  # Maximum attempts reached
            ip_address='127.0.0.1'
        )
        
        verify_data['otp'] = '654321'
        response = self.client.post(self.verify_otp_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class SecurityIntegrationTest(TransactionTestCase):
    """Comprehensive security integration tests"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='securityuser',
            email='security@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
        
        cache.clear()
    
    def test_rate_limiting_across_endpoints(self):
        """Test rate limiting across different endpoints"""
        # Test login rate limiting
        login_url = reverse('api_users:login')
        
        # Make multiple failed login attempts
        for i in range(6):  # Assuming limit is 5
            data = {
                'username': 'securityuser',
                'password': 'WrongPassword'
            }
            response = self.client.post(login_url, data)
            
            if i < 5:
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            else:
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test OTP rate limiting
        send_otp_url = reverse('api_users:send-otp')
        
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            for i in range(6):  # Assuming limit is 5
                data = {
                    'contact_info': f'+98912345678{i}',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                response = self.client.post(send_otp_url, data)
                
                if i < 5:
                    self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])
                else:
                    self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_brute_force_protection_complete_flow(self):
        """Test complete brute force protection flow"""
        login_url = reverse('api_users:login')
        
        # Step 1: Make failed login attempts
        for i in range(3):
            data = {
                'username': 'securityuser',
                'password': 'WrongPassword'
            }
            response = self.client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
            
            # Verify failed attempts are being tracked
            self.user.refresh_from_db()
            self.assertEqual(self.user.failed_login_attempts, i + 1)
        
        # Step 2: Account should be locked after 3 failed attempts
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        
        # Step 3: Next login attempt should return locked status
        data = {
            'username': 'securityuser',
            'password': 'TestPassword123!'  # Correct password
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        
        # Step 4: Verify security logs
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
        
        # Step 5: Unlock account and verify successful login
        self.user.unlock_account()
        
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify failed attempts were reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
    
    def test_suspicious_activity_detection_and_response(self):
        """Test suspicious activity detection and response"""
        login_url = reverse('api_users:login')
        
        # Mock suspicious activity detection
        with patch.object(SecurityService, 'check_suspicious_activity') as mock_suspicious:
            mock_suspicious.return_value = (True, 'Login from different country: Unknown')
            
            data = {
                'username': 'securityuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(login_url, data)
            
            # Should require additional verification
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertFalse(response.data['success'])
            self.assertTrue(response.data['requires_verification'])
            
            # Verify security log was created
            suspicious_logs = SecurityLog.objects.filter(
                user=self.user,
                event_type='suspicious_login_attempt'
            )
            self.assertTrue(suspicious_logs.exists())
    
    def test_ip_blocking_functionality(self):
        """Test IP blocking functionality"""
        test_ip = '192.168.1.100'
        
        # Block IP
        SecurityService.block_ip(
            ip_address=test_ip,
            duration_minutes=60,
            reason="Too many failed attempts"
        )
        
        # Verify IP is blocked
        self.assertTrue(SecurityService.is_ip_blocked(test_ip))
        
        # Verify security log was created
        block_logs = SecurityLog.objects.filter(
            event_type='ip_blocked',
            ip_address=test_ip
        )
        self.assertTrue(block_logs.exists())
    
    def test_security_logging_comprehensive(self):
        """Test comprehensive security logging"""
        # Test various security events
        events_to_test = [
            ('login_success', 'low'),
            ('login_failed', 'medium'),
            ('otp_sent', 'low'),
            ('otp_failed', 'medium'),
            ('suspicious_activity', 'high'),
            ('account_locked', 'critical')
        ]
        
        for event_type, severity in events_to_test:
            SecurityService.log_security_event(
                event_type=event_type,
                ip_address='127.0.0.1',
                user=self.user,
                severity=severity,
                details={'test': True}
            )
        
        # Verify all logs were created
        for event_type, severity in events_to_test:
            logs = SecurityLog.objects.filter(
                user=self.user,
                event_type=event_type,
                severity=severity
            )
            self.assertTrue(logs.exists())
        
        # Test security summary generation
        summary = SecurityService.get_security_summary(self.user, days=30)
        
        self.assertEqual(summary['total_events'], len(events_to_test))
        self.assertEqual(summary['failed_logins'], 1)
        self.assertEqual(summary['successful_logins'], 1)
        self.assertEqual(summary['high_severity_events'], 2)  # high + critical


class PerformanceIntegrationTest(APITestCase):
    """Performance tests for high-traffic endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        
        # Create multiple test users
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'perfuser{i}',
                email=f'perfuser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
    
    def test_concurrent_login_performance(self):
        """Test concurrent login requests performance"""
        login_url = reverse('api_users:login')
        
        def login_user(user_index):
            client = APIClient()
            data = {
                'username': f'perfuser{user_index}',
                'password': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = client.post(login_url, data)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'user_index': user_index
            }
        
        # Test with 10 concurrent logins
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(login_user, i) for i in range(10)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        successful_logins = sum(1 for r in results if r['status_code'] == 200)
        self.assertEqual(successful_logins, 10)
        
        # Performance assertions
        self.assertLess(total_time, 5.0, f"Concurrent logins took too long: {total_time}s")
        
        max_response_time = max(r['response_time'] for r in results)
        self.assertLess(max_response_time, 3.0, f"Slowest login: {max_response_time}s")
    
    def test_concurrent_registration_performance(self):
        """Test concurrent registration requests performance"""
        registration_url = reverse('api_users:register')
        
        def register_user(user_index):
            client = APIClient()
            data = {
                'username': f'concuser{user_index}',
                'email': f'concuser{user_index}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = client.post(registration_url, data)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'user_index': user_index
            }
        
        # Test with 5 concurrent registrations
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_user, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All requests should succeed
        successful_registrations = sum(1 for r in results if r['status_code'] == 201)
        self.assertEqual(successful_registrations, 5)
        
        # Performance assertions
        self.assertLess(total_time, 10.0, f"Concurrent registrations took too long: {total_time}s")
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_concurrent_otp_requests_performance(self, mock_send_sms):
        """Test concurrent OTP requests performance"""
        mock_send_sms.return_value = True
        send_otp_url = reverse('api_users:send-otp')
        
        def send_otp_request(request_index):
            client = APIClient()
            data = {
                'contact_info': f'+98912345{request_index:04d}',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            
            start_time = time.time()
            response = client.post(send_otp_url, data)
            end_time = time.time()
            
            return {
                'status_code': response.status_code,
                'response_time': end_time - start_time,
                'request_index': request_index
            }
        
        # Test with 5 concurrent OTP requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(send_otp_request, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Most requests should succeed (some might hit rate limits)
        successful_requests = sum(1 for r in results if r['status_code'] == 200)
        self.assertGreaterEqual(successful_requests, 3)
        
        # Performance assertions
        self.assertLess(total_time, 5.0, f"Concurrent OTP requests took too long: {total_time}s")
    
    def test_database_query_optimization(self):
        """Test database query optimization for common operations"""
        # Test user lookup optimization
        start_time = time.time()
        
        for i in range(10):
            user = User.objects.get(username=f'perfuser{i}')
            self.assertIsNotNone(user)
        
        end_time = time.time()
        lookup_time = end_time - start_time
        
        self.assertLess(lookup_time, 0.5, f"User lookups took too long: {lookup_time}s")
        
        # Test session queries optimization
        user = self.users[0]
        
        # Create some sessions
        for i in range(5):
            UserSession.objects.create(
                user=user,
                session_key=f'session_{i}',
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i}'
            )
        
        start_time = time.time()
        sessions = list(UserSession.objects.filter(user=user, is_active=True))
        end_time = time.time()
        
        query_time = end_time - start_time
        self.assertLess(query_time, 0.1, f"Session query took too long: {query_time}s")
        self.assertGreater(len(sessions), 0)


class BrowserCompatibilityIntegrationTest(APITestCase):
    """Integration tests for browser compatibility"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='browseruser',
            email='browser@example.com',
            password='TestPassword123!'
        )
        
        # Common user agents
        self.user_agents = {
            'chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'safari': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'edge': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
            'mobile_chrome': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'mobile_safari': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'
        }
    
    def test_login_across_different_browsers(self):
        """Test login functionality across different browsers"""
        login_url = reverse('api_users:login')
        
        for browser_name, user_agent in self.user_agents.items():
            with self.subTest(browser=browser_name):
                # Set user agent
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': 'browseruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                self.assertIn('tokens', response.data)
                
                # Verify session was created with correct user agent
                session = UserSession.objects.filter(
                    user=self.user,
                    user_agent=user_agent
                ).first()
                self.assertIsNotNone(session)
    
    def test_registration_across_different_browsers(self):
        """Test registration functionality across different browsers"""
        registration_url = reverse('api_users:register')
        
        for i, (browser_name, user_agent) in enumerate(self.user_agents.items()):
            with self.subTest(browser=browser_name):
                # Set user agent
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': f'browseruser{i}',
                    'email': f'browseruser{i}@example.com',
                    'password': 'TestPassword123!',
                    'password_confirm': 'TestPassword123!'
                }
                
                response = self.client.post(registration_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)
                self.assertTrue(response.data['success'])
                
                # Verify user was created
                user = User.objects.get(username=f'browseruser{i}')
                self.assertIsNotNone(user)
    
    def test_api_responses_format_consistency(self):
        """Test API response format consistency across browsers"""
        login_url = reverse('api_users:login')
        
        expected_fields = ['success', 'user', 'tokens', 'security_info']
        
        for browser_name, user_agent in self.user_agents.items():
            with self.subTest(browser=browser_name):
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': 'browseruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                
                # Check response format consistency
                for field in expected_fields:
                    self.assertIn(field, response.data)
                
                # Check JSON serialization works properly
                json_response = json.dumps(response.data, default=str)
                self.assertIsInstance(json_response, str)
    
    def test_header_handling_across_browsers(self):
        """Test proper handling of different browser headers"""
        login_url = reverse('api_users:login')
        
        # Test different header combinations
        header_combinations = [
            {'HTTP_ACCEPT': 'application/json'},
            {'HTTP_ACCEPT': 'application/json, text/plain, */*'},
            {'HTTP_ACCEPT_LANGUAGE': 'en-US,en;q=0.9'},
            {'HTTP_ACCEPT_ENCODING': 'gzip, deflate, br'},
            {'HTTP_CONNECTION': 'keep-alive'},
            {'HTTP_CACHE_CONTROL': 'no-cache'},
        ]
        
        for headers in header_combinations:
            with self.subTest(headers=headers):
                # Apply headers
                for key, value in headers.items():
                    self.client.defaults[key] = value
                
                data = {
                    'username': 'browseruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Clean up headers
                for key in headers.keys():
                    if key in self.client.defaults:
                        del self.client.defaults[key]


class EndToEndWorkflowTest(APITestCase):
    """End-to-end workflow tests covering complete user journeys"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()
    
    def test_complete_user_lifecycle(self):
        """Test complete user lifecycle from registration to account management"""
        # Step 1: Registration
        registration_url = reverse('api_users:register')
        registration_data = {
            'username': 'lifecycleuser',
            'email': 'lifecycle@example.com',
            'phone': '+989123456789',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!',
            'first_name': 'Lifecycle',
            'last_name': 'User'
        }
        
        response = self.client.post(registration_url, registration_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        user = User.objects.get(username='lifecycleuser')
        access_token = response.data['tokens']['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
        
        # Step 2: Email verification
        with patch('users.services.email.EmailService.send_verification_email', return_value=True):
            verification_success, message = VerificationService.send_email_verification(
                user=user,
                ip_address='127.0.0.1'
            )
            self.assertTrue(verification_success)
        
        verification_token = EmailVerificationToken.objects.filter(user=user).first()
        verify_success, message, verified_user = VerificationService.verify_email(
            token=verification_token.token,
            ip_address='127.0.0.1'
        )
        self.assertTrue(verify_success)
        
        # Step 3: Phone verification
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            phone_success, message = VerificationService.send_phone_verification(
                user=user,
                ip_address='127.0.0.1'
            )
            self.assertTrue(phone_success)
        
        with patch.object(OtpCode, 'verify_code', return_value=True):
            phone_verify_success, message = VerificationService.verify_phone(
                user=user,
                phone=user.phone,
                otp_code='123456',
                ip_address='127.0.0.1'
            )
            self.assertTrue(phone_verify_success)
        
        # Step 4: Profile update
        profile_url = reverse('api_users:profile')
        profile_data = {
            'first_name': 'Updated',
            'last_name': 'Name',
            'birth_date': '1990-01-01'
        }
        
        response = self.client.patch(profile_url, profile_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 5: Password change
        password_change_data = {
            'current_password': 'TestPassword123!',
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        # Assuming password change endpoint exists
        # response = self.client.post(password_change_url, password_change_data)
        # self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 6: Session management
        sessions_url = reverse('api_users:user-sessions')
        response = self.client.get(sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('sessions', response.data)
        
        # Step 7: Logout from all devices
        logout_all_url = reverse('api_users:logout-all-devices')
        response = self.client.post(logout_all_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify all sessions were deactivated
        active_sessions = UserSession.objects.filter(user=user, is_active=True)
        self.assertEqual(active_sessions.count(), 0)
        
        # Step 8: Verify security logs were created throughout the process
        security_logs = SecurityLog.objects.filter(user=user)
        self.assertGreater(security_logs.count(), 5)  # Multiple events should be logged
    
    def test_password_reset_complete_workflow(self):
        """Test complete password reset workflow"""
        # Create user
        user = User.objects.create_user(
            username='resetuser',
            email='reset@example.com',
            password='OldPassword123!'
        )
        
        # Step 1: Request password reset
        request_url = reverse('api_users:password-reset-request')
        request_data = {
            'contact_info': 'reset@example.com',
            'delivery_method': 'email'
        }
        
        with patch('users.services.otp.OTPService.send_otp', return_value=(True, 'OTP sent')):
            response = self.client.post(request_url, request_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 2: Verify OTP and get reset token
        verify_url = reverse('api_users:password-reset-verify')
        verify_data = {
            'contact_info': 'reset@example.com',
            'otp': '123456',
            'purpose': 'password_reset'
        }
        
        with patch.object(OtpCode, 'verify_code', return_value=True):
            response = self.client.post(verify_url, verify_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            reset_token = response.data['reset_token']
        
        # Step 3: Confirm new password
        confirm_url = reverse('api_users:password-reset-confirm')
        confirm_data = {
            'token': reset_token,
            'new_password': 'NewPassword123!',
            'confirm_password': 'NewPassword123!'
        }
        
        response = self.client.post(confirm_url, confirm_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Step 4: Verify password was changed
        user.refresh_from_db()
        self.assertTrue(user.check_password('NewPassword123!'))
        self.assertFalse(user.check_password('OldPassword123!'))
        
        # Step 5: Verify reset token was marked as used
        reset_tokens = PasswordResetToken.objects.filter(token=reset_token)
        self.assertTrue(reset_tokens.exists())
        self.assertTrue(reset_tokens.first().used)
        
        # Step 6: Test login with new password
        login_url = reverse('api_users:login')
        login_data = {
            'username': 'resetuser',
            'password': 'NewPassword123!'
        }
        
        response = self.client.post(login_url, login_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
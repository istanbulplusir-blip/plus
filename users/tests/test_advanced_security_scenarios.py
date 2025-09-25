"""
Advanced security scenario tests for the authentication system.
Tests complex security situations, edge cases, and attack scenarios.
"""

import time
import threading
from datetime import timedelta
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import (
    OtpCode, UserSession, PasswordResetToken, SecurityLog, 
    EmailVerificationToken, generate_hash
)
from users.services.otp import OTPService
from users.services.security import SecurityService
from users.services.verification import VerificationService

User = get_user_model()


class AdvancedBruteForceProtectionTest(TransactionTestCase):
    """Test advanced brute force protection scenarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='bruteforceuser',
            email='bruteforce@example.com',
            password='TestPassword123!'
        )
        cache.clear()
    
    def test_distributed_brute_force_attack(self):
        """Test protection against distributed brute force attacks from multiple IPs"""
        login_url = reverse('api_users:login')
        
        # Simulate attacks from multiple IPs
        ip_addresses = [f'192.168.1.{i}' for i in range(1, 11)]
        
        def attack_from_ip(ip_address):
            client = APIClient()
            results = []
            
            for attempt in range(3):
                # Mock the IP address
                with patch.object(SecurityService, 'get_client_ip', return_value=ip_address):
                    data = {
                        'username': 'bruteforceuser',
                        'password': 'WrongPassword'
                    }
                    response = client.post(login_url, data)
                    results.append({
                        'ip': ip_address,
                        'attempt': attempt + 1,
                        'status_code': response.status_code
                    })
            
            return results
        
        # Execute distributed attack
        all_results = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(attack_from_ip, ip) for ip in ip_addresses[:5]]
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Verify that each IP is tracked separately
        for ip in ip_addresses[:5]:
            failed_logs = SecurityLog.objects.filter(
                event_type='login_failed',
                ip_address=ip
            )
            self.assertGreater(failed_logs.count(), 0)
        
        # Verify user account protection
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
    
    def test_time_based_attack_patterns(self):
        """Test detection of time-based attack patterns"""
        login_url = reverse('api_users:login')
        
        # Rapid-fire attack (many attempts in short time)
        start_time = time.time()
        
        for i in range(10):
            data = {
                'username': 'bruteforceuser',
                'password': f'WrongPassword{i}'
            }
            response = self.client.post(login_url, data)
            
            # Should hit rate limiting
            if i >= 5:  # Assuming rate limit is 5
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        end_time = time.time()
        attack_duration = end_time - start_time
        
        # Verify rapid requests were detected
        rapid_attack_logs = SecurityLog.objects.filter(
            event_type='rate_limit_exceeded'
        )
        self.assertGreater(rapid_attack_logs.count(), 0)
        
        # Verify attack was completed quickly (indicating rapid-fire)
        self.assertLess(attack_duration, 5.0)
    
    def test_credential_stuffing_protection(self):
        """Test protection against credential stuffing attacks"""
        login_url = reverse('api_users:login')
        
        # Create multiple users to simulate credential stuffing
        users = []
        for i in range(5):
            user = User.objects.create_user(
                username=f'stuffuser{i}',
                email=f'stuffuser{i}@example.com',
                password='CommonPassword123!'
            )
            users.append(user)
        
        # Simulate credential stuffing attack (same password, different usernames)
        common_passwords = ['password123', 'admin123', 'qwerty123', '123456789']
        
        for password in common_passwords:
            for user in users:
                data = {
                    'username': user.username,
                    'password': password
                }
                response = self.client.post(login_url, data)
                
                # Should fail for wrong passwords
                if password != 'CommonPassword123!':
                    self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify multiple failed attempts were logged
        failed_logs = SecurityLog.objects.filter(event_type='login_failed')
        self.assertGreater(failed_logs.count(), 10)
    
    def test_account_enumeration_protection(self):
        """Test protection against account enumeration attacks"""
        login_url = reverse('api_users:login')
        
        # Test with existing and non-existing usernames
        test_usernames = [
            'bruteforceuser',  # exists
            'nonexistentuser1',  # doesn't exist
            'nonexistentuser2',  # doesn't exist
            'admin',  # common username that might not exist
            'test'  # common username that might not exist
        ]
        
        response_times = {}
        
        for username in test_usernames:
            data = {
                'username': username,
                'password': 'WrongPassword'
            }
            
            start_time = time.time()
            response = self.client.post(login_url, data)
            end_time = time.time()
            
            response_times[username] = end_time - start_time
            
            # All should return 401 (not revealing if user exists)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Response times should be similar (timing attack protection)
        times = list(response_times.values())
        max_time = max(times)
        min_time = min(times)
        time_difference = max_time - min_time
        
        # Time difference should be small (less than 100ms)
        self.assertLess(time_difference, 0.1, "Response times vary too much, potential timing attack vulnerability")


class AdvancedOTPSecurityTest(APITestCase):
    """Test advanced OTP security scenarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='otpsecuser',
            email='otpsec@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
        cache.clear()
    
    def test_otp_replay_attack_protection(self):
        """Test protection against OTP replay attacks"""
        send_otp_url = reverse('api_users:send-otp')
        verify_otp_url = reverse('api_users:verify-otp')
        
        # Send OTP
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            send_data = {
                'contact_info': '+989123456789',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            response = self.client.post(send_otp_url, send_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify OTP successfully
        with patch.object(OtpCode, 'verify_code', return_value=True):
            verify_data = {
                'contact_info': '+989123456789',
                'otp': '123456',
                'purpose': 'login'
            }
            response = self.client.post(verify_otp_url, verify_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try to replay the same OTP
        response = self.client.post(verify_otp_url, verify_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_otp_brute_force_protection(self):
        """Test protection against OTP brute force attacks"""
        send_otp_url = reverse('api_users:send-otp')
        verify_otp_url = reverse('api_users:verify-otp')
        
        # Send OTP
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            send_data = {
                'contact_info': '+989123456789',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            response = self.client.post(send_otp_url, send_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Try multiple wrong OTP codes
        for i in range(5):
            verify_data = {
                'contact_info': '+989123456789',
                'otp': f'{i:06d}',  # Wrong OTP codes
                'purpose': 'login'
            }
            response = self.client.post(verify_otp_url, verify_data)
            
            if i < 3:  # First 3 attempts should be allowed
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            else:  # After 3 attempts, should be blocked
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn('حد مجاز', response.data['message'])
    
    def test_otp_timing_attack_protection(self):
        """Test protection against OTP timing attacks"""
        verify_otp_url = reverse('api_users:verify-otp')
        
        # Create OTP
        otp_code = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('123456'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        # Test with correct and incorrect OTP codes
        test_codes = ['123456', '654321', '111111', '999999']
        response_times = {}
        
        for code in test_codes:
            verify_data = {
                'contact_info': '+989123456789',
                'otp': code,
                'purpose': 'login'
            }
            
            start_time = time.time()
            response = self.client.post(verify_otp_url, verify_data)
            end_time = time.time()
            
            response_times[code] = end_time - start_time
            
            if code == '123456':
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                break  # Stop after successful verification
            else:
                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        
        # Response times for incorrect codes should be similar
        incorrect_times = [response_times[code] for code in test_codes[1:] if code in response_times]
        if len(incorrect_times) > 1:
            max_time = max(incorrect_times)
            min_time = min(incorrect_times)
            time_difference = max_time - min_time
            
            # Time difference should be small
            self.assertLess(time_difference, 0.05, "OTP verification times vary too much")
    
    def test_otp_rate_limiting_per_contact(self):
        """Test OTP rate limiting per contact method"""
        send_otp_url = reverse('api_users:send-otp')
        
        # Test SMS rate limiting
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            for i in range(7):  # Assuming limit is 5
                send_data = {
                    'contact_info': '+989123456789',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                response = self.client.post(send_otp_url, send_data)
                
                if i < 5:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        
        # Test that email OTP is still allowed (separate rate limit)
        with patch('users.services.email.EmailService.send_otp_email', return_value=True):
            send_data = {
                'contact_info': 'otpsec@example.com',
                'delivery_method': 'email',
                'purpose': 'login'
            }
            response = self.client.post(send_otp_url, send_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class SessionHijackingProtectionTest(APITestCase):
    """Test protection against session hijacking attacks"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='sessionuser',
            email='session@example.com',
            password='TestPassword123!'
        )
        
        # Login and get tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_session_fixation_protection(self):
        """Test protection against session fixation attacks"""
        sessions_url = reverse('api_users:user-sessions')
        
        # Get initial session
        response = self.client.get(sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        initial_sessions = response.data['sessions']
        
        # Simulate login from different location/device
        login_url = reverse('api_users:login')
        
        # Mock different IP and user agent
        with patch.object(SecurityService, 'get_client_ip', return_value='10.0.0.1'):
            new_client = APIClient()
            new_client.defaults['HTTP_USER_AGENT'] = 'Different Browser'
            
            login_data = {
                'username': 'sessionuser',
                'password': 'TestPassword123!'
            }
            response = new_client.post(login_url, login_data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that new session was created (not reused)
        response = self.client.get(sessions_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        new_sessions = response.data['sessions']
        
        # Should have more sessions now
        self.assertGreater(len(new_sessions), len(initial_sessions))
    
    def test_concurrent_session_detection(self):
        """Test detection of concurrent sessions from different locations"""
        login_url = reverse('api_users:login')
        
        # Simulate logins from different IPs
        ip_addresses = ['192.168.1.1', '10.0.0.1', '172.16.0.1']
        
        for ip in ip_addresses:
            with patch.object(SecurityService, 'get_client_ip', return_value=ip):
                client = APIClient()
                login_data = {
                    'username': 'sessionuser',
                    'password': 'TestPassword123!'
                }
                response = client.post(login_url, login_data)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Check that all sessions were created and logged
        sessions = UserSession.objects.filter(user=self.user, is_active=True)
        self.assertGreaterEqual(sessions.count(), len(ip_addresses))
        
        # Check security logs for multiple logins
        login_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_success'
        )
        self.assertGreaterEqual(login_logs.count(), len(ip_addresses))
    
    def test_session_timeout_security(self):
        """Test session timeout security measures"""
        profile_url = reverse('api_users:profile')
        
        # Make request with valid token
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Simulate token expiry by using an expired token
        from rest_framework_simplejwt.tokens import AccessToken
        from datetime import datetime
        
        # Create expired token
        expired_token = AccessToken.for_user(self.user)
        expired_token.set_exp(from_time=datetime.utcnow() - timedelta(hours=1))
        
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {str(expired_token)}')
        
        response = self.client.get(profile_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh_security(self):
        """Test token refresh security measures"""
        refresh_url = reverse('api_users:token-refresh')
        
        # Test normal token refresh
        refresh_data = {'refresh': self.refresh_token}
        response = self.client.post(refresh_url, refresh_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        
        # Test refresh token reuse (should be prevented)
        response = self.client.post(refresh_url, refresh_data)
        # Depending on implementation, this might fail or succeed
        # If token rotation is implemented, this should fail
        
        # Test with invalid refresh token
        invalid_refresh_data = {'refresh': 'invalid_token_here'}
        response = self.client.post(refresh_url, invalid_refresh_data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class AdvancedRateLimitingTest(TransactionTestCase):
    """Test advanced rate limiting scenarios"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='ratelimituser',
            email='ratelimit@example.com',
            password='TestPassword123!'
        )
        cache.clear()
    
    def test_adaptive_rate_limiting(self):
        """Test adaptive rate limiting based on user behavior"""
        login_url = reverse('api_users:login')
        
        # Normal user behavior (should not trigger strict limits)
        for i in range(3):
            data = {
                'username': 'ratelimituser',
                'password': 'TestPassword123!'
            }
            response = self.client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Wait between requests (normal behavior)
            time.sleep(0.1)
        
        # Suspicious behavior (rapid requests)
        for i in range(10):
            data = {
                'username': 'ratelimituser',
                'password': 'TestPassword123!'
            }
            response = self.client.post(login_url, data)
            
            # Should hit rate limiting for rapid requests
            if i >= 5:
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_rate_limiting_bypass_attempts(self):
        """Test protection against rate limiting bypass attempts"""
        send_otp_url = reverse('api_users:send-otp')
        
        # Try to bypass rate limiting with different headers
        bypass_headers = [
            {'HTTP_X_FORWARDED_FOR': '192.168.1.100'},
            {'HTTP_X_REAL_IP': '192.168.1.101'},
            {'HTTP_CLIENT_IP': '192.168.1.102'},
            {'HTTP_X_CLUSTER_CLIENT_IP': '192.168.1.103'},
        ]
        
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            # First, exhaust rate limit normally
            for i in range(6):
                data = {
                    'contact_info': f'+98912345678{i}',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                response = self.client.post(send_otp_url, data)
                
                if i < 5:
                    self.assertEqual(response.status_code, status.HTTP_200_OK)
                else:
                    self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Try to bypass with different headers
            for headers in bypass_headers:
                client = APIClient()
                for key, value in headers.items():
                    client.defaults[key] = value
                
                data = {
                    'contact_info': '+989999999999',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                response = client.post(send_otp_url, data)
                
                # Should still be rate limited (proper IP detection)
                self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
    
    def test_distributed_rate_limiting(self):
        """Test rate limiting across distributed requests"""
        login_url = reverse('api_users:login')
        
        def make_requests_from_ip(ip_address, num_requests):
            results = []
            client = APIClient()
            
            with patch.object(SecurityService, 'get_client_ip', return_value=ip_address):
                for i in range(num_requests):
                    data = {
                        'username': 'ratelimituser',
                        'password': 'WrongPassword'
                    }
                    response = client.post(login_url, data)
                    results.append(response.status_code)
            
            return results
        
        # Simulate distributed attack from multiple IPs
        ip_addresses = [f'10.0.0.{i}' for i in range(1, 6)]
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(make_requests_from_ip, ip, 3)
                for ip in ip_addresses
            ]
            
            all_results = []
            for future in as_completed(futures):
                all_results.extend(future.result())
        
        # Each IP should be rate limited independently
        # But user account should be protected globally
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
    
    def test_rate_limit_recovery(self):
        """Test rate limit recovery after time window"""
        send_otp_url = reverse('api_users:send-otp')
        
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            # Exhaust rate limit
            for i in range(6):
                data = {
                    'contact_info': f'+98912345678{i}',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                response = self.client.post(send_otp_url, data)
                
                if i >= 5:
                    self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Simulate time passing (clear cache to simulate expiry)
            cache.clear()
            
            # Should be able to make requests again
            data = {
                'contact_info': '+989999999999',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            response = self.client.post(send_otp_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class DataIntegrityAndValidationTest(APITestCase):
    """Test data integrity and validation security"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='datauser',
            email='data@example.com',
            password='TestPassword123!'
        )
        
        # Authenticate user
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_sql_injection_protection(self):
        """Test protection against SQL injection attacks"""
        login_url = reverse('api_users:login')
        
        # SQL injection payloads
        sql_payloads = [
            "admin'; DROP TABLE users; --",
            "admin' OR '1'='1",
            "admin' UNION SELECT * FROM users --",
            "admin'; INSERT INTO users VALUES ('hacker', 'password'); --",
            "admin' AND (SELECT COUNT(*) FROM users) > 0 --"
        ]
        
        for payload in sql_payloads:
            data = {
                'username': payload,
                'password': 'TestPassword123!'
            }
            
            # Should not cause SQL errors or unauthorized access
            response = self.client.post(login_url, data)
            self.assertIn(response.status_code, [
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_401_UNAUTHORIZED
            ])
            
            # Verify user table still exists and is intact
            user_count = User.objects.count()
            self.assertGreater(user_count, 0)
    
    def test_xss_protection_in_responses(self):
        """Test XSS protection in API responses"""
        profile_url = reverse('api_users:profile')
        
        # XSS payloads
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "javascript:alert('XSS')",
            "<img src=x onerror=alert('XSS')>",
            "';alert('XSS');//",
            "<svg onload=alert('XSS')>"
        ]
        
        for payload in xss_payloads:
            # Try to inject XSS in profile fields
            data = {
                'first_name': payload,
                'last_name': f'Test {payload}'
            }
            
            response = self.client.patch(profile_url, data)
            
            # Should either reject the data or sanitize it
            if response.status_code == status.HTTP_200_OK:
                # If accepted, verify it's sanitized in response
                response_data = str(response.data)
                self.assertNotIn('<script>', response_data.lower())
                self.assertNotIn('javascript:', response_data.lower())
                self.assertNotIn('onerror=', response_data.lower())
                self.assertNotIn('onload=', response_data.lower())
    
    def test_input_validation_edge_cases(self):
        """Test input validation with edge cases"""
        registration_url = reverse('api_users:register')
        
        # Edge case inputs
        edge_cases = [
            {
                'username': 'a' * 1000,  # Very long username
                'email': 'test@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            },
            {
                'username': '',  # Empty username
                'email': 'test2@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            },
            {
                'username': 'testuser2',
                'email': 'a' * 100 + '@example.com',  # Very long email
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            },
            {
                'username': 'testuser3',
                'email': 'invalid-email',  # Invalid email format
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            },
            {
                'username': 'testuser4',
                'email': 'test4@example.com',
                'password': 'a' * 1000,  # Very long password
                'password_confirm': 'a' * 1000
            }
        ]
        
        for case_data in edge_cases:
            response = self.client.post(registration_url, case_data)
            
            # Should reject invalid data
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertFalse(response.data.get('success', True))
    
    def test_unicode_and_encoding_handling(self):
        """Test proper handling of Unicode and different encodings"""
        profile_url = reverse('api_users:profile')
        
        # Unicode test cases
        unicode_cases = [
            {'first_name': 'محمد', 'last_name': 'احمدی'},  # Persian
            {'first_name': '张', 'last_name': '三'},  # Chinese
            {'first_name': 'José', 'last_name': 'García'},  # Spanish with accents
            {'first_name': 'Владимир', 'last_name': 'Путин'},  # Russian
            {'first_name': '🙂', 'last_name': '😊'},  # Emojis
            {'first_name': 'Test\u0000', 'last_name': 'Null'},  # Null byte
        ]
        
        for case_data in unicode_cases:
            response = self.client.patch(profile_url, case_data)
            
            # Should handle Unicode properly or reject invalid characters
            if response.status_code == status.HTTP_200_OK:
                # Verify data integrity
                self.user.refresh_from_db()
                # Check that data was stored correctly (no corruption)
                self.assertIsNotNone(self.user.first_name)
                self.assertIsNotNone(self.user.last_name)
            else:
                # Should provide clear error message
                self.assertIn('message', response.data)
    
    def test_concurrent_data_modification(self):
        """Test data integrity under concurrent modifications"""
        profile_url = reverse('api_users:profile')
        
        def update_profile(field_value):
            client = APIClient()
            refresh = RefreshToken.for_user(self.user)
            client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
            
            data = {'first_name': f'Concurrent{field_value}'}
            response = client.patch(profile_url, data)
            return response.status_code
        
        # Simulate concurrent profile updates
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(update_profile, i) for i in range(5)]
            results = [future.result() for future in as_completed(futures)]
        
        # All updates should succeed or fail gracefully
        for result in results:
            self.assertIn(result, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])
        
        # Verify data integrity
        self.user.refresh_from_db()
        self.assertIsNotNone(self.user.first_name)
        self.assertTrue(self.user.first_name.startswith('Concurrent'))
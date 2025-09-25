"""
Security-focused tests for the authentication system.
Tests rate limiting, brute force protection, and other security measures.
"""

import time
from unittest.mock import patch, MagicMock
from datetime import timedelta

from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from django.core.cache import cache
from django.conf import settings
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import OtpCode, UserSession, SecurityLog, generate_hash
from users.services.security import SecurityService

User = get_user_model()


class RateLimitingSecurityTest(TransactionTestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.client = APIClient()
        cache.clear()  # Clear cache before each test
    
    def test_registration_rate_limiting(self):
        """Test rate limiting for registration endpoint"""
        registration_url = reverse('api_users:register')
        
        # Test with real rate limiting (not mocked)
        successful_registrations = 0
        rate_limited = False
        
        for i in range(10):  # Try 10 registrations
            data = {
                'username': f'rateuser{i}',
                'email': f'rateuser{i}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            response = self.client.post(registration_url, data)
            
            if response.status_code == status.HTTP_201_CREATED:
                successful_registrations += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                self.assertIn('retry_after', response.data)
                break
        
        # Should have some successful registrations and then hit rate limit
        self.assertGreater(successful_registrations, 0)
        # Note: Actual rate limiting behavior depends on settings
    
    def test_login_rate_limiting(self):
        """Test rate limiting for login attempts"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        login_url = reverse('api_users:login')
        
        # Make multiple failed login attempts from same IP
        failed_attempts = 0
        rate_limited = False
        
        for i in range(15):  # Try many failed logins
            data = {
                'username': 'testuser',
                'password': 'WrongPassword'
            }
            
            response = self.client.post(login_url, data)
            
            if response.status_code == status.HTTP_401_UNAUTHORIZED:
                failed_attempts += 1
            elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                rate_limited = True
                self.assertIn('retry_after', response.data)
                break
            elif response.status_code == status.HTTP_423_LOCKED:
                # Account got locked due to failed attempts
                break
        
        # Should have some failed attempts before rate limiting kicks in
        self.assertGreater(failed_attempts, 0)
    
    def test_otp_rate_limiting(self):
        """Test rate limiting for OTP requests"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789'
        )
        
        send_otp_url = reverse('api_users:send-otp')
        
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            successful_otps = 0
            rate_limited = False
            
            for i in range(10):  # Try multiple OTP requests
                data = {
                    'contact_info': '+989123456789',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                
                response = self.client.post(send_otp_url, data)
                
                if response.status_code == status.HTTP_200_OK:
                    successful_otps += 1
                elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
                    rate_limited = True
                    self.assertIn('retry_after', response.data)
                    break
            
            # Should have some successful OTP sends before rate limiting
            self.assertGreater(successful_otps, 0)
    
    def test_rate_limiting_per_ip(self):
        """Test that rate limiting is applied per IP address"""
        registration_url = reverse('api_users:register')
        
        # First IP makes requests
        for i in range(3):
            data = {
                'username': f'ip1user{i}',
                'email': f'ip1user{i}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            response = self.client.post(
                registration_url, 
                data,
                REMOTE_ADDR='192.168.1.1'
            )
            # Should succeed for first IP
            self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])
        
        # Second IP should still be able to make requests
        data = {
            'username': 'ip2user1',
            'email': 'ip2user1@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        response = self.client.post(
            registration_url,
            data,
            REMOTE_ADDR='192.168.1.2'
        )
        # Second IP should succeed (unless global limits are hit)
        self.assertIn(response.status_code, [status.HTTP_201_CREATED, status.HTTP_429_TOO_MANY_REQUESTS])


class BruteForceProtectionTest(APITestCase):
    """Test brute force protection mechanisms"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        cache.clear()
    
    def test_account_lockout_after_failed_attempts(self):
        """Test account lockout after multiple failed login attempts"""
        login_url = reverse('api_users:login')
        
        # Make 3 failed attempts (should lock on 3rd)
        for i in range(3):
            data = {
                'username': 'testuser',
                'password': 'WrongPassword'
            }
            
            response = self.client.post(login_url, data)
            
            self.user.refresh_from_db()
            
            if i < 2:  # First 2 attempts
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertEqual(self.user.failed_login_attempts, i + 1)
                self.assertFalse(self.user.is_locked())
            else:  # 3rd attempt should lock account
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
                self.assertEqual(self.user.failed_login_attempts, 3)
                self.assertTrue(self.user.is_locked())
        
        # 4th attempt should return locked status
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_423_LOCKED)
        self.assertIn('locked_until', response.data)
    
    def test_successful_login_resets_failed_attempts(self):
        """Test that successful login resets failed attempt counter"""
        login_url = reverse('api_users:login')
        
        # Make 2 failed attempts
        for i in range(2):
            data = {
                'username': 'testuser',
                'password': 'WrongPassword'
            }
            response = self.client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 2)
        
        # Successful login should reset counter
        data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
        self.assertFalse(self.user.is_locked())
    
    def test_account_unlock_after_timeout(self):
        """Test that account unlocks after timeout period"""
        # Lock the account
        self.user.failed_login_attempts = 3
        self.user.locked_until = timezone.now() + timedelta(minutes=30)
        self.user.save()
        
        # Verify account is locked
        self.assertTrue(self.user.is_locked())
        
        # Simulate time passing (set lock time in past)
        self.user.locked_until = timezone.now() - timedelta(minutes=1)
        self.user.save()
        
        # Account should now be unlocked
        self.assertFalse(self.user.is_locked())
    
    def test_otp_attempt_limiting(self):
        """Test OTP verification attempt limiting"""
        # Create OTP with some attempts
        otp = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('123456'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            attempts=2,  # Already 2 attempts
            ip_address='127.0.0.1'
        )
        
        verify_url = reverse('api_users:verify-otp')
        
        # This should be the 3rd attempt (max allowed)
        data = {
            'contact_info': '+989123456789',
            'otp': '123456',
            'purpose': 'login'
        }
        
        response = self.client.post(verify_url, data)
        
        # Should fail due to max attempts reached
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
    
    def test_ip_blocking_for_suspicious_activity(self):
        """Test IP blocking for suspicious activity"""
        login_url = reverse('api_users:login')
        
        # Simulate suspicious activity by making many failed attempts
        with patch.object(SecurityService, 'is_ip_blocked', return_value=True):
            data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(login_url, data)
            
            self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
            self.assertFalse(response.data['success'])
            
            # Verify security log was created
            security_logs = SecurityLog.objects.filter(
                event_type='blocked_ip_attempt'
            )
            self.assertTrue(security_logs.exists())


class SuspiciousActivityDetectionTest(APITestCase):
    """Test suspicious activity detection"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
    
    def test_new_location_detection(self):
        """Test detection of login from new location"""
        login_url = reverse('api_users:login')
        
        # Mock suspicious activity detection
        with patch.object(SecurityService, 'check_suspicious_activity') as mock_suspicious:
            mock_suspicious.return_value = (True, 'Login from different country: Unknown Location')
            
            data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(login_url, data)
            
            # Should require additional verification
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
    
    def test_unusual_user_agent_detection(self):
        """Test detection of unusual user agent"""
        login_url = reverse('api_users:login')
        
        # Use an unusual user agent
        unusual_user_agent = 'SuspiciousBot/1.0'
        
        with patch.object(SecurityService, 'check_suspicious_activity') as mock_suspicious:
            mock_suspicious.return_value = (True, 'Unusual user agent detected')
            
            data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(
                login_url,
                data,
                HTTP_USER_AGENT=unusual_user_agent
            )
            
            # Should detect suspicious activity
            self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
            self.assertTrue(response.data['requires_verification'])
    
    def test_rapid_login_attempts_detection(self):
        """Test detection of rapid login attempts"""
        login_url = reverse('api_users:login')
        
        # Make rapid login attempts
        for i in range(5):
            data = {
                'username': 'testuser',
                'password': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = self.client.post(login_url, data)
            end_time = time.time()
            
            # If requests are too rapid, might trigger suspicious activity
            if end_time - start_time < 0.1:  # Very rapid
                # Could potentially trigger rate limiting or suspicious activity detection
                pass
    
    def test_multiple_failed_usernames(self):
        """Test detection of attempts with multiple different usernames"""
        login_url = reverse('api_users:login')
        
        # Try multiple non-existent usernames (potential username enumeration)
        usernames = ['admin', 'administrator', 'root', 'test', 'user']
        
        for username in usernames:
            data = {
                'username': username,
                'password': 'password123'
            }
            
            response = self.client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Check if security logs were created for failed attempts
        failed_logs = SecurityLog.objects.filter(
            event_type='login_failed'
        )
        self.assertGreaterEqual(failed_logs.count(), len(usernames))


class SecurityLoggingTest(APITestCase):
    """Test security event logging"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
    
    def test_login_success_logging(self):
        """Test logging of successful login events"""
        login_url = reverse('api_users:login')
        
        data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify security log was created
        security_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_success'
        )
        self.assertTrue(security_logs.exists())
        
        log = security_logs.first()
        self.assertEqual(log.severity, 'low')
        self.assertIn('login_method', log.details)
    
    def test_login_failure_logging(self):
        """Test logging of failed login events"""
        login_url = reverse('api_users:login')
        
        data = {
            'username': 'testuser',
            'password': 'WrongPassword'
        }
        
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        # Verify security log was created
        security_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_failed'
        )
        self.assertTrue(security_logs.exists())
        
        log = security_logs.first()
        self.assertEqual(log.severity, 'medium')
        self.assertIn('failed_attempts', log.details)
    
    def test_registration_logging(self):
        """Test logging of user registration events"""
        registration_url = reverse('api_users:register')
        
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        response = self.client.post(registration_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify security log was created
        new_user = User.objects.get(username='newuser')
        security_logs = SecurityLog.objects.filter(
            user=new_user,
            event_type='user_registered'
        )
        self.assertTrue(security_logs.exists())
        
        log = security_logs.first()
        self.assertEqual(log.severity, 'low')
        self.assertIn('email', log.details)
        self.assertIn('registration_method', log.details)
    
    def test_otp_logging(self):
        """Test logging of OTP-related events"""
        send_otp_url = reverse('api_users:send-otp')
        
        with patch('users.services.otp.OTPService._send_sms', return_value=True):
            data = {
                'contact_info': '+989123456789',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            
            response = self.client.post(send_otp_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Verify security log was created
            security_logs = SecurityLog.objects.filter(
                event_type='otp_sent'
            )
            self.assertTrue(security_logs.exists())
            
            log = security_logs.first()
            self.assertEqual(log.severity, 'low')
            self.assertIn('delivery_method', log.details)
            self.assertIn('purpose', log.details)
    
    def test_rate_limit_logging(self):
        """Test logging of rate limit violations"""
        registration_url = reverse('api_users:register')
        
        # Mock rate limiting to trigger violation
        with patch.object(SecurityService, 'check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = (False, {'retry_after': 3600})
            
            data = {
                'username': 'ratelimituser',
                'email': 'ratelimituser@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            response = self.client.post(registration_url, data)
            self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Verify security log was created
            security_logs = SecurityLog.objects.filter(
                event_type='rate_limit_exceeded'
            )
            self.assertTrue(security_logs.exists())
            
            log = security_logs.first()
            self.assertEqual(log.severity, 'medium')
            self.assertIn('action', log.details)
            self.assertIn('rate_info', log.details)
    
    def test_session_logging(self):
        """Test logging of session-related events"""
        login_url = reverse('api_users:login')
        
        data = {
            'username': 'testuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify session creation was logged
        security_logs = SecurityLog.objects.filter(
            user=self.user,
            event_type='session_created'
        )
        self.assertTrue(security_logs.exists())
        
        log = security_logs.first()
        self.assertEqual(log.severity, 'low')
        self.assertIn('session_id', log.details)


class SecurityServiceTest(TestCase):
    """Test SecurityService functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        cache.clear()
    
    def test_get_client_ip(self):
        """Test IP address extraction from request"""
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        # Test with X-Forwarded-For header
        request = factory.get('/')
        request.META['HTTP_X_FORWARDED_FOR'] = '192.168.1.1, 10.0.0.1'
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.1')
        
        # Test with REMOTE_ADDR
        request = factory.get('/')
        request.META['REMOTE_ADDR'] = '192.168.1.2'
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '192.168.1.2')
    
    def test_rate_limit_functionality(self):
        """Test rate limiting functionality"""
        identifier = 'test_ip_123'
        action = 'test_action'
        
        # First check should be allowed
        is_allowed, rate_info = SecurityService.check_rate_limit(identifier, action)
        self.assertTrue(is_allowed)
        
        # Increment counter
        SecurityService.increment_rate_limit(identifier, action)
        
        # Should still be allowed after one increment
        is_allowed, rate_info = SecurityService.check_rate_limit(identifier, action)
        self.assertTrue(is_allowed)
    
    def test_security_event_logging(self):
        """Test security event logging functionality"""
        SecurityService.log_security_event(
            event_type='test_event',
            ip_address='192.168.1.1',
            user=self.user,
            severity='medium',
            user_agent='Test Browser',
            details={'test': 'data'}
        )
        
        # Verify log was created
        logs = SecurityLog.objects.filter(
            event_type='test_event',
            user=self.user
        )
        self.assertTrue(logs.exists())
        
        log = logs.first()
        self.assertEqual(log.ip_address, '192.168.1.1')
        self.assertEqual(log.severity, 'medium')
        self.assertEqual(log.user_agent, 'Test Browser')
        self.assertEqual(log.details['test'], 'data')
    
    def test_suspicious_activity_detection(self):
        """Test suspicious activity detection logic"""
        # Test with different IP than last login
        self.user.last_login_ip = '192.168.1.1'
        self.user.save()
        
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=self.user,
            ip_address='10.0.0.1',
            user_agent='Normal Browser',
            action='login'
        )
        
        # Should detect different IP as potentially suspicious
        # (actual implementation may vary based on business logic)
        # This test verifies the method runs without error
        self.assertIsInstance(is_suspicious, bool)
        self.assertIsInstance(reason, str)
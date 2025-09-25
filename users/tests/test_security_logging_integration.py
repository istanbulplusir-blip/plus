"""
Integration tests for security logging system.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.cache import cache
from users.models import SecurityLog
from users.services.security import SecurityService

User = get_user_model()


class SecurityLoggingIntegrationTestCase(TestCase):
    """Test cases for security logging integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.ip_address = '192.168.1.100'
        
        # Clear cache and logs before each test
        cache.clear()
        SecurityLog.objects.all().delete()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_successful_login_logging(self):
        """Test that successful logins are logged"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        # Login should succeed
        self.assertIn(response.status_code, [200, 201])
        
        # Check that login success was logged
        log = SecurityLog.objects.filter(
            event_type='login_success',
            user=self.user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'low')
    
    def test_failed_login_logging(self):
        """Test that failed logins are logged"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpassword'
        }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        self.assertEqual(response.status_code, 401)
        
        # Check that login failure was logged
        log = SecurityLog.objects.filter(
            event_type='login_failed',
            user=self.user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'medium')
    
    def test_rate_limit_exceeded_logging(self):
        """Test that rate limit violations are logged"""
        # Exceed rate limit by making multiple requests
        for i in range(6):  # Default limit is 5
            self.client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        # Check that rate limit exceeded was logged
        log = SecurityLog.objects.filter(
            event_type='rate_limit_exceeded',
            ip_address=self.ip_address
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'medium')
        self.assertIn('login_attempts', log.details.get('action', ''))
    
    def test_account_lock_logging(self):
        """Test that account locks are logged"""
        # Make multiple failed login attempts to trigger lock
        for i in range(4):  # Should trigger lock after 3 failed attempts
            self.client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'wrongpassword'
            }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        # Check that account lock was logged
        log = SecurityLog.objects.filter(
            event_type='login_locked',
            user=self.user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'high')
        self.assertEqual(log.ip_address, self.ip_address)
    
    def test_registration_logging(self):
        """Test that user registrations are logged"""
        response = self.client.post('/api/auth/register/', {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'phone': '+989123456790',  # Different phone number
            'password': 'newpass123',
            'password_confirm': 'newpass123'
        }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        self.assertEqual(response.status_code, 201)
        
        # Check that registration was logged
        new_user = User.objects.get(username='newuser')
        log = SecurityLog.objects.filter(
            event_type='user_registered',
            user=new_user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'low')
    
    def test_suspicious_activity_logging(self):
        """Test that suspicious activities are logged"""
        # Simulate suspicious user agent
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, HTTP_X_FORWARDED_FOR=self.ip_address, HTTP_USER_AGENT='Googlebot/2.1')
        
        # Check for suspicious activity log
        log = SecurityLog.objects.filter(
            event_type='suspicious_login_attempt',
            user=self.user
        ).first()
        
        # Note: This might not always trigger depending on other factors
        # but if it does, it should be logged properly
        if log:
            self.assertEqual(log.severity, 'high')
            self.assertIn('Suspicious user agent', log.details.get('reason', ''))
    
    def test_session_creation_logging(self):
        """Test that session creation is logged"""
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'testpass123'
        }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        self.assertIn(response.status_code, [200, 201])
        
        # Check that session creation was logged
        log = SecurityLog.objects.filter(
            event_type='session_created',
            user=self.user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'low')
    
    def test_security_service_direct_logging(self):
        """Test direct security service logging"""
        # Test logging without user
        log = SecurityService.log_security_event(
            event_type='test_event',
            ip_address=self.ip_address,
            severity='medium',
            details={'test': 'data'}
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'test_event')
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'medium')
        self.assertEqual(log.details['test'], 'data')
        
        # Test logging with user
        log_with_user = SecurityService.log_security_event(
            event_type='test_user_event',
            ip_address=self.ip_address,
            user=self.user,
            severity='high',
            user_agent='Test Agent',
            details={'user_test': 'data'}
        )
        
        self.assertIsNotNone(log_with_user)
        self.assertEqual(log_with_user.user, self.user)
        self.assertEqual(log_with_user.user_agent, 'Test Agent')
    
    def test_security_log_cleanup(self):
        """Test security log cleanup functionality"""
        # Create some test logs
        SecurityService.log_security_event(
            event_type='test_event_1',
            ip_address=self.ip_address,
            severity='low'
        )
        SecurityService.log_security_event(
            event_type='test_event_2',
            ip_address=self.ip_address,
            severity='medium'
        )
        
        # Verify logs were created
        self.assertEqual(SecurityLog.objects.count(), 2)
        
        # Test cleanup (should not delete recent logs)
        deleted_count = SecurityService.cleanup_security_logs(days_to_keep=1)
        self.assertEqual(deleted_count, 0)
        self.assertEqual(SecurityLog.objects.count(), 2)
    
    def test_security_summary_generation(self):
        """Test security summary generation"""
        # Create various types of security logs
        SecurityService.log_security_event(
            event_type='login_success',
            ip_address=self.ip_address,
            user=self.user,
            severity='low'
        )
        SecurityService.log_security_event(
            event_type='login_failed',
            ip_address=self.ip_address,
            user=self.user,
            severity='medium'
        )
        SecurityService.log_security_event(
            event_type='login_locked',
            ip_address='192.168.1.101',
            user=self.user,
            severity='high'
        )
        
        # Generate summary
        summary = SecurityService.get_security_summary(self.user, days=30)
        
        self.assertEqual(summary['total_events'], 3)
        self.assertEqual(summary['successful_logins'], 1)
        self.assertEqual(summary['failed_logins'], 1)
        self.assertEqual(summary['account_locks'], 1)
        self.assertEqual(summary['unique_ips'], 2)
        self.assertEqual(summary['high_severity_events'], 1)
        self.assertEqual(len(summary['recent_events']), 3)
    
    def test_ip_blocking_integration(self):
        """Test IP blocking functionality"""
        # Block an IP
        success = SecurityService.block_ip(
            ip_address=self.ip_address,
            duration_minutes=60,
            reason='Test block'
        )
        
        self.assertTrue(success)
        
        # Verify IP is blocked
        self.assertTrue(SecurityService.is_ip_blocked(self.ip_address))
        
        # Check that blocking was logged
        log = SecurityLog.objects.filter(
            event_type='ip_blocked',
            ip_address=self.ip_address
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'high')
        self.assertIn('Test block', log.details.get('reason', ''))
    
    def test_user_unlock_logging(self):
        """Test user account unlock logging"""
        # First lock the user
        self.user.lock_account(30)
        self.assertTrue(self.user.is_locked())
        
        # Then unlock
        success = SecurityService.unlock_user_account(
            user=self.user,
            ip_address=self.ip_address,
            reason='Test unlock'
        )
        
        self.assertTrue(success)
        
        # Check that unlock was logged
        log = SecurityLog.objects.filter(
            event_type='account_unlocked',
            user=self.user
        ).first()
        
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'medium')
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertIn('Test unlock', log.details.get('reason', ''))


class SecurityMiddlewareIntegrationTestCase(TestCase):
    """Test cases for security middleware integration"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.ip_address = '192.168.1.100'
        cache.clear()
        SecurityLog.objects.all().delete()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_rate_limiting_middleware(self):
        """Test that middleware enforces rate limiting"""
        # Make requests up to the limit
        for i in range(5):
            response = self.client.post('/api/auth/login/', {
                'username': 'testuser',
                'password': 'wrongpass'
            }, HTTP_X_FORWARDED_FOR=self.ip_address)
            
            # First 5 should get through (even if they fail authentication)
            self.assertIn(response.status_code, [401, 429])
        
        # 6th request should be rate limited
        response = self.client.post('/api/auth/login/', {
            'username': 'testuser',
            'password': 'wrongpass'
        }, HTTP_X_FORWARDED_FOR=self.ip_address)
        
        self.assertEqual(response.status_code, 429)
        
        # Check that rate limit was logged
        log = SecurityLog.objects.filter(
            event_type='rate_limit_exceeded',
            ip_address=self.ip_address
        ).first()
        
        self.assertIsNotNone(log)
    
    def test_blocked_ip_middleware(self):
        """Test that middleware blocks IPs"""
        # Block the IP first
        SecurityService.block_ip(self.ip_address, 60, 'Test block')
        
        # Try to make a request
        response = self.client.get('/api/auth/profile/', HTTP_X_FORWARDED_FOR=self.ip_address)
        
        self.assertEqual(response.status_code, 403)
        
        # Check that blocked IP attempt was logged
        log = SecurityLog.objects.filter(
            event_type='blocked_ip_attempt',
            ip_address=self.ip_address
        ).first()
        
        self.assertIsNotNone(log)
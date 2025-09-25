"""
Unit tests for SecurityService.
"""
import json
from datetime import timedelta
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.core.cache import cache
from django.utils import timezone
from django.contrib.auth import get_user_model
from users.services.security import SecurityService
from users.models import SecurityLog

User = get_user_model()


class SecurityServiceTestCase(TestCase):
    """Test cases for SecurityService"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ip_address = '192.168.1.100'
        self.user_agent = 'Mozilla/5.0 (Test Browser)'
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_check_rate_limit_within_limit(self):
        """Test rate limit check when within limit"""
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        
        self.assertTrue(is_allowed)
        self.assertEqual(info['current_count'], 0)
        self.assertEqual(info['max_count'], 5)
        self.assertEqual(info['remaining'], 5)
    
    def test_check_rate_limit_exceeded(self):
        """Test rate limit check when limit is exceeded"""
        # Simulate exceeding the limit
        for i in range(6):
            SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        
        self.assertFalse(is_allowed)
        self.assertEqual(info['current_count'], 6)
        self.assertEqual(info['max_count'], 5)
        self.assertIn('retry_after', info)
    
    def test_check_rate_limit_custom_limit(self):
        """Test rate limit check with custom limit"""
        custom_limit = {'count': 2, 'window': 300}
        
        # First two should be allowed
        for i in range(2):
            SecurityService.increment_rate_limit(
                self.ip_address, 
                'login_attempts', 
                custom_limit
            )
        
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts',
            custom_limit=custom_limit
        )
        
        self.assertFalse(is_allowed)
        self.assertEqual(info['max_count'], 2)
    
    def test_increment_rate_limit(self):
        """Test incrementing rate limit counter"""
        # First increment
        count1 = SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        self.assertEqual(count1, 1)
        
        # Second increment
        count2 = SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        self.assertEqual(count2, 2)
    
    def test_reset_rate_limit(self):
        """Test resetting rate limit counter"""
        # Set some count
        SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        
        # Reset
        result = SecurityService.reset_rate_limit(self.ip_address, 'login_attempts')
        self.assertTrue(result)
        
        # Check it's reset
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        self.assertTrue(is_allowed)
        self.assertEqual(info['current_count'], 0)
    
    def test_check_suspicious_activity_no_user(self):
        """Test suspicious activity check without user"""
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=None,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        # Should not be suspicious for new IP without history
        self.assertFalse(is_suspicious)
        self.assertEqual(reason, "")
    
    def test_check_suspicious_activity_bot_user_agent(self):
        """Test suspicious activity detection for bot user agents"""
        bot_user_agent = 'Mozilla/5.0 (compatible; Googlebot/2.1)'
        
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=self.user,
            ip_address=self.ip_address,
            user_agent=bot_user_agent
        )
        
        self.assertTrue(is_suspicious)
        self.assertIn("Suspicious user agent", reason)
    
    def test_check_suspicious_activity_rapid_requests(self):
        """Test suspicious activity detection for rapid requests"""
        # Simulate rapid requests
        rapid_requests_key = f"security_rapid_requests_{self.ip_address}"
        cache.set(rapid_requests_key, 60, 300)  # 60 requests in 5 minutes
        
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=self.user,
            ip_address=self.ip_address,
            user_agent=self.user_agent
        )
        
        self.assertTrue(is_suspicious)
        self.assertIn("Rapid requests from IP", reason)
    
    def test_check_suspicious_activity_multiple_failed_attempts(self):
        """Test suspicious activity detection for multiple failed attempts"""
        # Simulate multiple failed attempts
        failed_attempts_key = f"security_failed_attempts_{self.ip_address}"
        cache.set(failed_attempts_key, 15, 900)  # 15 failed attempts
        
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=self.user,
            ip_address=self.ip_address,
            user_agent=self.user_agent,
            action='login'
        )
        
        self.assertTrue(is_suspicious)
        self.assertIn("Multiple failed login attempts from IP", reason)
    
    def test_lock_user_account(self):
        """Test locking user account"""
        result = SecurityService.lock_user_account(
            user=self.user,
            duration_minutes=30,
            reason="Test lock",
            ip_address=self.ip_address
        )
        
        self.assertTrue(result)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        
        # Check security log was created
        log = SecurityLog.objects.filter(
            user=self.user,
            event_type='login_locked'
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'high')
        self.assertEqual(log.ip_address, self.ip_address)
    
    def test_unlock_user_account(self):
        """Test unlocking user account"""
        # First lock the account
        self.user.lock_account(30)
        self.assertTrue(self.user.is_locked())
        
        # Then unlock it
        result = SecurityService.unlock_user_account(
            user=self.user,
            ip_address=self.ip_address,
            reason="Test unlock"
        )
        
        self.assertTrue(result)
        
        # Refresh user from database
        self.user.refresh_from_db()
        self.assertFalse(self.user.is_locked())
        self.assertEqual(self.user.failed_login_attempts, 0)
        
        # Check security log was created
        log = SecurityLog.objects.filter(
            user=self.user,
            event_type='account_unlocked'
        ).first()
        self.assertIsNotNone(log)
    
    def test_log_security_event(self):
        """Test logging security events"""
        details = {'test_key': 'test_value', 'number': 123}
        
        log = SecurityService.log_security_event(
            event_type='login_success',
            ip_address=self.ip_address,
            user=self.user,
            severity='low',
            user_agent=self.user_agent,
            details=details
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'login_success')
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'low')
        self.assertEqual(log.user_agent, self.user_agent)
        self.assertEqual(log.details, details)
    
    def test_log_security_event_without_user(self):
        """Test logging security events without user"""
        log = SecurityService.log_security_event(
            event_type='rate_limit_exceeded',
            ip_address=self.ip_address,
            severity='medium'
        )
        
        self.assertIsNotNone(log)
        self.assertEqual(log.event_type, 'rate_limit_exceeded')
        self.assertIsNone(log.user)
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.severity, 'medium')
    
    def test_get_client_ip_x_forwarded_for(self):
        """Test getting client IP from X-Forwarded-For header"""
        request = MagicMock()
        request.META = {
            'HTTP_X_FORWARDED_FOR': '203.0.113.1, 192.168.1.1',
            'REMOTE_ADDR': '10.0.0.1'
        }
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.1')
    
    def test_get_client_ip_x_real_ip(self):
        """Test getting client IP from X-Real-IP header"""
        request = MagicMock()
        request.META = {
            'HTTP_X_REAL_IP': '203.0.113.2',
            'REMOTE_ADDR': '10.0.0.1'
        }
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.2')
    
    def test_get_client_ip_remote_addr(self):
        """Test getting client IP from REMOTE_ADDR"""
        request = MagicMock()
        request.META = {
            'REMOTE_ADDR': '203.0.113.3'
        }
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '203.0.113.3')
    
    def test_get_client_ip_fallback(self):
        """Test getting client IP fallback"""
        request = MagicMock()
        request.META = {}
        
        ip = SecurityService.get_client_ip(request)
        self.assertEqual(ip, '127.0.0.1')
    
    def test_is_ip_blocked_false(self):
        """Test checking if IP is blocked when it's not"""
        is_blocked = SecurityService.is_ip_blocked(self.ip_address)
        self.assertFalse(is_blocked)
    
    def test_is_ip_blocked_true(self):
        """Test checking if IP is blocked when it is"""
        # Block the IP first
        SecurityService.block_ip(self.ip_address, 60, "Test block")
        
        is_blocked = SecurityService.is_ip_blocked(self.ip_address)
        self.assertTrue(is_blocked)
    
    def test_block_ip(self):
        """Test blocking IP address"""
        result = SecurityService.block_ip(
            ip_address=self.ip_address,
            duration_minutes=60,
            reason="Test block"
        )
        
        self.assertTrue(result)
        
        # Check if IP is actually blocked
        is_blocked = SecurityService.is_ip_blocked(self.ip_address)
        self.assertTrue(is_blocked)
        
        # Check security log was created
        log = SecurityLog.objects.filter(
            event_type='ip_blocked',
            ip_address=self.ip_address
        ).first()
        self.assertIsNotNone(log)
        self.assertEqual(log.severity, 'high')
    
    def test_cleanup_security_logs(self):
        """Test cleaning up old security logs"""
        # Create some old logs
        old_date = timezone.now() - timedelta(days=100)
        old_log = SecurityLog.objects.create(
            event_type='login_success',
            ip_address=self.ip_address
        )
        # Manually update the created_at field since it's auto_now_add
        SecurityLog.objects.filter(id=old_log.id).update(created_at=old_date)
        
        # Create a recent log
        SecurityLog.objects.create(
            event_type='login_success',
            ip_address=self.ip_address
        )
        
        # Clean up logs older than 90 days
        deleted_count = SecurityService.cleanup_security_logs(days_to_keep=90)
        
        self.assertEqual(deleted_count, 1)
        self.assertEqual(SecurityLog.objects.count(), 1)
    
    def test_get_security_summary(self):
        """Test getting security summary for user"""
        # Create various security logs
        SecurityLog.objects.create(
            user=self.user,
            event_type='login_success',
            ip_address=self.ip_address,
            severity='low'
        )
        SecurityLog.objects.create(
            user=self.user,
            event_type='login_failed',
            ip_address=self.ip_address,
            severity='medium'
        )
        SecurityLog.objects.create(
            user=self.user,
            event_type='otp_failed',
            ip_address='192.168.1.101',
            severity='medium'
        )
        SecurityLog.objects.create(
            user=self.user,
            event_type='login_locked',
            ip_address=self.ip_address,
            severity='high'
        )
        
        summary = SecurityService.get_security_summary(self.user, days=30)
        
        self.assertEqual(summary['total_events'], 4)
        self.assertEqual(summary['failed_logins'], 1)
        self.assertEqual(summary['successful_logins'], 1)
        self.assertEqual(summary['otp_failures'], 1)
        self.assertEqual(summary['account_locks'], 1)
        self.assertEqual(summary['unique_ips'], 2)
        self.assertEqual(summary['high_severity_events'], 1)
        self.assertEqual(len(summary['recent_events']), 4)
    
    def test_unknown_rate_limit_action(self):
        """Test handling unknown rate limit action"""
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='unknown_action'
        )
        
        # Should allow unknown actions
        self.assertTrue(is_allowed)
        self.assertEqual(info, {})
    
    @patch('users.services.security.logger')
    def test_error_handling_in_rate_limit_check(self, mock_logger):
        """Test error handling in rate limit check"""
        with patch('django.core.cache.cache.get', side_effect=Exception("Cache error")):
            is_allowed, info = SecurityService.check_rate_limit(
                identifier=self.ip_address,
                action='login_attempts'
            )
            
            # Should allow request on error
            self.assertTrue(is_allowed)
            self.assertIn('error', info)
            mock_logger.error.assert_called()
    
    @patch('users.services.security.logger')
    def test_error_handling_in_log_security_event(self, mock_logger):
        """Test error handling in log security event"""
        with patch('users.models.SecurityLog.objects.create', side_effect=Exception("DB error")):
            log = SecurityService.log_security_event(
                event_type='test_event',
                ip_address=self.ip_address
            )
            
            self.assertIsNone(log)
            mock_logger.error.assert_called()


class SecurityLogModelTestCase(TestCase):
    """Test cases for SecurityLog model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.ip_address = '192.168.1.100'
    
    def test_security_log_creation(self):
        """Test creating security log"""
        details = {'key': 'value', 'number': 42}
        
        log = SecurityLog.objects.create(
            user=self.user,
            event_type='login_success',
            severity='low',
            ip_address=self.ip_address,
            user_agent='Test Agent',
            details=details
        )
        
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.event_type, 'login_success')
        self.assertEqual(log.severity, 'low')
        self.assertEqual(log.ip_address, self.ip_address)
        self.assertEqual(log.user_agent, 'Test Agent')
        self.assertEqual(log.details, details)
        self.assertIsNotNone(log.created_at)
    
    def test_security_log_str_representation(self):
        """Test string representation of security log"""
        log = SecurityLog.objects.create(
            user=self.user,
            event_type='login_failed',
            ip_address=self.ip_address
        )
        
        expected_str = f"login_failed - {self.user.username} - {self.ip_address}"
        self.assertEqual(str(log), expected_str)
    
    def test_security_log_without_user(self):
        """Test creating security log without user"""
        log = SecurityLog.objects.create(
            event_type='rate_limit_exceeded',
            ip_address=self.ip_address
        )
        
        self.assertIsNone(log.user)
        self.assertEqual(log.event_type, 'rate_limit_exceeded')
        
        expected_str = f"rate_limit_exceeded - Anonymous - {self.ip_address}"
        self.assertEqual(str(log), expected_str)
    
    def test_security_log_ordering(self):
        """Test security log ordering"""
        # Create logs with different timestamps
        log1 = SecurityLog.objects.create(
            event_type='login_success',
            ip_address=self.ip_address
        )
        log2 = SecurityLog.objects.create(
            event_type='login_failed',
            ip_address=self.ip_address
        )
        
        # Should be ordered by created_at descending
        logs = list(SecurityLog.objects.all())
        self.assertEqual(logs[0], log2)  # Most recent first
        self.assertEqual(logs[1], log1)
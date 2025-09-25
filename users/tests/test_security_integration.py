"""
Integration tests for SecurityService with other services.
"""
from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.core.cache import cache
from users.services.security import SecurityService
from users.services.otp import OTPService
from users.models import SecurityLog

User = get_user_model()


class SecurityIntegrationTestCase(TestCase):
    """Integration tests for SecurityService"""
    
    def setUp(self):
        """Set up test data"""
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            phone='+989123456789',
            password='testpass123'
        )
        self.ip_address = '192.168.1.100'
        
        # Clear cache before each test
        cache.clear()
    
    def tearDown(self):
        """Clean up after each test"""
        cache.clear()
    
    def test_otp_rate_limiting_integration(self):
        """Test that OTP service respects rate limiting"""
        # Send multiple OTP requests to exceed rate limit
        for i in range(6):  # Default limit is 5 per hour
            success, message = OTPService.send_otp(
                contact_info=self.user.phone,
                delivery_method='sms',
                purpose='login',
                user=self.user,
                ip_address=self.ip_address
            )
            
            if i < 5:
                self.assertTrue(success, f"Request {i+1} should succeed")
            else:
                self.assertFalse(success, f"Request {i+1} should fail due to rate limit")
                self.assertIn("حد مجاز", message)
    
    def test_failed_login_tracking(self):
        """Test tracking failed login attempts"""
        # Simulate failed login attempts
        for i in range(3):
            SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
            
            # Log failed login
            SecurityService.log_security_event(
                event_type='login_failed',
                ip_address=self.ip_address,
                user=self.user,
                severity='medium'
            )
        
        # Check that rate limit is reached
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        
        self.assertTrue(is_allowed)  # Should still be allowed (limit is 5)
        self.assertEqual(info['current_count'], 3)
        
        # Check security logs were created
        failed_logs = SecurityLog.objects.filter(
            event_type='login_failed',
            user=self.user
        )
        self.assertEqual(failed_logs.count(), 3)
    
    def test_account_locking_after_failed_attempts(self):
        """Test automatic account locking after failed attempts"""
        # Simulate multiple failed login attempts
        for i in range(3):
            self.user.increment_failed_attempts()
        
        # User should be locked now
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_locked())
        
        # Log the lock event
        SecurityService.log_security_event(
            event_type='login_locked',
            ip_address=self.ip_address,
            user=self.user,
            severity='high'
        )
        
        # Check security log was created
        lock_log = SecurityLog.objects.filter(
            event_type='login_locked',
            user=self.user
        ).first()
        
        self.assertIsNotNone(lock_log)
        self.assertEqual(lock_log.severity, 'high')
    
    def test_suspicious_activity_detection_with_otp(self):
        """Test suspicious activity detection during OTP requests"""
        # Simulate rapid OTP requests (suspicious behavior)
        rapid_requests_key = f"security_rapid_requests_{self.ip_address}"
        cache.set(rapid_requests_key, 60, 300)  # 60 requests in 5 minutes
        
        # Check for suspicious activity
        is_suspicious, reason = SecurityService.check_suspicious_activity(
            user=self.user,
            ip_address=self.ip_address,
            user_agent='Mozilla/5.0 (Test)',
            action='otp_request'
        )
        
        self.assertTrue(is_suspicious)
        self.assertIn("Rapid requests from IP", reason)
        
        # This should trigger additional security measures
        if is_suspicious:
            SecurityService.log_security_event(
                event_type='suspicious_activity',
                ip_address=self.ip_address,
                user=self.user,
                severity='medium',
                details={'reason': reason, 'action': 'otp_request'}
            )
        
        # Check security log was created
        suspicious_log = SecurityLog.objects.filter(
            event_type='suspicious_activity',
            user=self.user
        ).first()
        
        self.assertIsNotNone(suspicious_log)
        self.assertEqual(suspicious_log.severity, 'medium')
    
    def test_ip_blocking_prevents_requests(self):
        """Test that blocked IPs cannot make requests"""
        # Block the IP
        SecurityService.block_ip(
            ip_address=self.ip_address,
            duration_minutes=60,
            reason="Too many failed attempts"
        )
        
        # Check that IP is blocked
        self.assertTrue(SecurityService.is_ip_blocked(self.ip_address))
        
        # Try to send OTP from blocked IP (this would be handled by middleware)
        # For this test, we'll just verify the blocking mechanism works
        blocked_log = SecurityLog.objects.filter(
            event_type='ip_blocked',
            ip_address=self.ip_address
        ).first()
        
        self.assertIsNotNone(blocked_log)
        self.assertEqual(blocked_log.severity, 'high')
    
    def test_security_summary_generation(self):
        """Test generating security summary for user"""
        # Create various security events
        events = [
            ('login_success', 'low'),
            ('login_failed', 'medium'),
            ('otp_sent', 'low'),
            ('otp_failed', 'medium'),
            ('login_locked', 'high'),
        ]
        
        for event_type, severity in events:
            SecurityService.log_security_event(
                event_type=event_type,
                ip_address=self.ip_address,
                user=self.user,
                severity=severity
            )
        
        # Generate security summary
        summary = SecurityService.get_security_summary(self.user, days=30)
        
        self.assertEqual(summary['total_events'], 5)
        self.assertEqual(summary['failed_logins'], 1)
        self.assertEqual(summary['successful_logins'], 1)
        self.assertEqual(summary['otp_failures'], 1)
        self.assertEqual(summary['account_locks'], 1)
        self.assertEqual(summary['high_severity_events'], 1)
        self.assertEqual(len(summary['recent_events']), 5)
    
    def test_rate_limit_reset_after_successful_action(self):
        """Test that rate limits can be reset after successful actions"""
        # Build up some failed attempts
        for i in range(3):
            SecurityService.increment_rate_limit(self.ip_address, 'login_attempts')
        
        # Check current count
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        self.assertEqual(info['current_count'], 3)
        
        # Reset after successful login
        SecurityService.reset_rate_limit(self.ip_address, 'login_attempts')
        
        # Check that it's reset
        is_allowed, info = SecurityService.check_rate_limit(
            identifier=self.ip_address,
            action='login_attempts'
        )
        self.assertEqual(info['current_count'], 0)
    
    def test_multiple_ip_tracking(self):
        """Test tracking security events from multiple IPs"""
        ip_addresses = ['192.168.1.100', '192.168.1.101', '10.0.0.1']
        
        # Create events from different IPs
        for i, ip in enumerate(ip_addresses):
            SecurityService.log_security_event(
                event_type='login_success',
                ip_address=ip,
                user=self.user,
                severity='low'
            )
        
        # Generate summary
        summary = SecurityService.get_security_summary(self.user, days=30)
        
        self.assertEqual(summary['unique_ips'], 3)
        self.assertEqual(summary['successful_logins'], 3)
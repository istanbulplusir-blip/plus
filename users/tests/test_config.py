"""
Configuration for comprehensive authentication system tests.
Defines test settings, constants, and utilities.
"""

import os
from django.conf import settings

# Test Configuration
TEST_CONFIG = {
    'PERFORMANCE': {
        'MAX_RESPONSE_TIME': 2.0,  # seconds
        'MAX_LOGIN_TIME': 1.0,  # seconds
        'MAX_REGISTRATION_TIME': 3.0,  # seconds
        'MAX_OTP_TIME': 0.5,  # seconds
        'CONCURRENT_USERS': 50,
        'LOAD_TEST_DURATION': 30,  # seconds
        'MAX_MEMORY_INCREASE': 100,  # MB
    },
    
    'SECURITY': {
        'MAX_LOGIN_ATTEMPTS': 3,
        'MAX_OTP_ATTEMPTS': 3,
        'RATE_LIMIT_LOGIN': 5,  # per 15 minutes
        'RATE_LIMIT_OTP': 5,  # per hour
        'RATE_LIMIT_REGISTRATION': 3,  # per hour
        'ACCOUNT_LOCK_DURATION': 30,  # minutes
        'OTP_EXPIRY_MINUTES': 5,
        'PASSWORD_RESET_EXPIRY_HOURS': 1,
        'EMAIL_VERIFICATION_EXPIRY_HOURS': 24,
    },
    
    'BROWSER_COMPATIBILITY': {
        'SUPPORTED_BROWSERS': [
            'Chrome 70+',
            'Firefox 60+',
            'Safari 12+',
            'Edge 79+',
            'Opera 60+',
            'Mobile Chrome 70+',
            'Mobile Safari 12+',
        ],
        'LEGACY_SUPPORT': [
            'IE 11',
            'Chrome 60+',
            'Firefox 50+',
        ]
    },
    
    'DATABASE': {
        'MAX_QUERY_TIME': 0.1,  # seconds
        'MAX_QUERIES_PER_REQUEST': 20,
        'BULK_OPERATION_THRESHOLD': 1000,
    },
    
    'CACHE': {
        'MAX_CACHE_TIME': 0.05,  # seconds
        'EXPECTED_HIT_RATIO': 80,  # percent
        'MAX_CACHE_SIZE': 100,  # MB
    }
}

# Test Data Templates
TEST_DATA = {
    'VALID_USER': {
        'username': 'testuser',
        'email': 'test@example.com',
        'phone': '+989123456789',
        'password': 'TestPassword123!',
        'first_name': 'Test',
        'last_name': 'User'
    },
    
    'INVALID_PASSWORDS': [
        '123',  # Too short
        'password',  # Too common
        '12345678',  # No letters
        'abcdefgh',  # No numbers
        'Password',  # No special chars
        'a' * 129,  # Too long
    ],
    
    'INVALID_EMAILS': [
        'invalid-email',
        '@example.com',
        'test@',
        'test..test@example.com',
        'test@example',
        'a' * 100 + '@example.com',  # Too long
    ],
    
    'INVALID_PHONES': [
        '123',  # Too short
        'abcdefgh',  # Not numeric
        '+1234567890123456',  # Too long
        '09123456789',  # Wrong format
    ],
    
    'SQL_INJECTION_PAYLOADS': [
        "admin'; DROP TABLE users; --",
        "admin' OR '1'='1",
        "admin' UNION SELECT * FROM users --",
        "admin'; INSERT INTO users VALUES ('hacker', 'password'); --",
        "admin' AND (SELECT COUNT(*) FROM users) > 0 --"
    ],
    
    'XSS_PAYLOADS': [
        "<script>alert('XSS')</script>",
        "javascript:alert('XSS')",
        "<img src=x onerror=alert('XSS')>",
        "';alert('XSS');//",
        "<svg onload=alert('XSS')>",
        "<iframe src=javascript:alert('XSS')></iframe>",
    ],
    
    'UNICODE_TEST_CASES': [
        {'first_name': 'محمد', 'last_name': 'احمدی'},  # Persian
        {'first_name': '张', 'last_name': '三'},  # Chinese
        {'first_name': 'José', 'last_name': 'García'},  # Spanish with accents
        {'first_name': 'Владимир', 'last_name': 'Путин'},  # Russian
        {'first_name': '🙂', 'last_name': '😊'},  # Emojis
        {'first_name': 'Test\u0000', 'last_name': 'Null'},  # Null byte
    ]
}

# User Agents for Browser Testing
USER_AGENTS = {
    'chrome_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'chrome_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'chrome_linux': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'firefox_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'firefox_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0',
    'firefox_linux': 'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
    'safari_mac': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
    'safari_ios': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
    'edge_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59',
    'chrome_mobile': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
    'chrome_tablet': 'Mozilla/5.0 (Linux; Android 10; SM-T870) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Safari/537.36',
    'opera_windows': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.172',
    'ie11_windows': 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
    'old_chrome': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36',
    'old_firefox': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
}

# HTTP Headers for Testing
HTTP_HEADERS = {
    'ACCEPT_HEADERS': [
        'application/json',
        'application/json, text/plain, */*',
        'application/json;charset=UTF-8',
        'application/json, application/xml, text/plain, */*',
        '*/*',
        'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
    ],
    
    'LANGUAGE_HEADERS': [
        'en-US,en;q=0.9',
        'fa-IR,fa;q=0.9,en;q=0.8',
        'ar-SA,ar;q=0.9',
        'zh-CN,zh;q=0.9',
        'es-ES,es;q=0.9',
        'fr-FR,fr;q=0.9'
    ],
    
    'ENCODING_HEADERS': [
        'gzip, deflate, br',
        'gzip, deflate',
        'gzip',
        'deflate',
        'br',
        'identity',
        '*'
    ],
    
    'CUSTOM_HEADERS': {
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        'HTTP_X_CSRF_TOKEN': 'test-csrf-token',
        'HTTP_X_API_VERSION': '1.0',
        'HTTP_X_CLIENT_VERSION': '2.1.0',
        'HTTP_ORIGIN': 'https://example.com',
        'HTTP_REFERER': 'https://example.com/login'
    }
}

# Test Utilities
class TestUtils:
    """Utility functions for tests"""
    
    @staticmethod
    def get_test_config(category, key=None):
        """Get test configuration value"""
        if key:
            return TEST_CONFIG.get(category, {}).get(key)
        return TEST_CONFIG.get(category, {})
    
    @staticmethod
    def get_test_data(category, key=None):
        """Get test data"""
        if key:
            return TEST_DATA.get(category, {}).get(key)
        return TEST_DATA.get(category, {})
    
    @staticmethod
    def get_user_agent(browser):
        """Get user agent string for browser"""
        return USER_AGENTS.get(browser, USER_AGENTS['chrome_windows'])
    
    @staticmethod
    def get_http_headers(category):
        """Get HTTP headers for testing"""
        return HTTP_HEADERS.get(category, [])
    
    @staticmethod
    def create_test_user(username_suffix='', **kwargs):
        """Create a test user with default values"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        default_data = TEST_DATA['VALID_USER'].copy()
        default_data['username'] += username_suffix
        default_data['email'] = f"test{username_suffix}@example.com"
        default_data.update(kwargs)
        
        password = default_data.pop('password')
        user = User.objects.create_user(password=password, **default_data)
        return user
    
    @staticmethod
    def create_bulk_test_users(count, prefix='bulkuser'):
        """Create multiple test users for load testing"""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        users = []
        for i in range(count):
            user = User.objects.create_user(
                username=f'{prefix}{i}',
                email=f'{prefix}{i}@example.com',
                password='TestPassword123!'
            )
            users.append(user)
        
        return users
    
    @staticmethod
    def measure_response_time(func, *args, **kwargs):
        """Measure function execution time"""
        import time
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result, end_time - start_time
    
    @staticmethod
    def assert_performance(response_time, max_time, operation_name):
        """Assert performance requirements"""
        if response_time > max_time:
            raise AssertionError(
                f"{operation_name} took too long: {response_time:.3f}s > {max_time:.3f}s"
            )
    
    @staticmethod
    def clean_test_data():
        """Clean up test data"""
        from django.contrib.auth import get_user_model
        from users.models import UserSession, SecurityLog, OtpCode, PasswordResetToken, EmailVerificationToken
        
        User = get_user_model()
        
        # Delete test users
        User.objects.filter(username__startswith='test').delete()
        User.objects.filter(username__startswith='bulk').delete()
        User.objects.filter(username__startswith='perf').delete()
        User.objects.filter(username__startswith='load').delete()
        User.objects.filter(username__startswith='conc').delete()
        User.objects.filter(username__startswith='scale').delete()
        
        # Clean up related data
        UserSession.objects.filter(session_key__startswith='test').delete()
        SecurityLog.objects.filter(event_type__startswith='test').delete()
        OtpCode.objects.filter(contact_info__contains='test').delete()
        PasswordResetToken.objects.filter(token__startswith='test').delete()
        EmailVerificationToken.objects.filter(token__startswith='test').delete()


# Test Decorators
def performance_test(max_time=None):
    """Decorator for performance tests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            
            if max_time and (end_time - start_time) > max_time:
                raise AssertionError(
                    f"Performance test failed: {func.__name__} took {end_time - start_time:.3f}s > {max_time}s"
                )
            
            return result
        return wrapper
    return decorator


def security_test(func):
    """Decorator for security tests"""
    def wrapper(*args, **kwargs):
        # Clear cache before security tests
        from django.core.cache import cache
        cache.clear()
        
        try:
            return func(*args, **kwargs)
        finally:
            # Clean up after security tests
            cache.clear()
    
    return wrapper


def browser_compatibility_test(browsers=None):
    """Decorator for browser compatibility tests"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if browsers is None:
                test_browsers = list(USER_AGENTS.keys())
            else:
                test_browsers = browsers
            
            results = {}
            for browser in test_browsers:
                try:
                    result = func(*args, browser=browser, **kwargs)
                    results[browser] = {'success': True, 'result': result}
                except Exception as e:
                    results[browser] = {'success': False, 'error': str(e)}
            
            # Check if any browsers failed
            failed_browsers = [b for b, r in results.items() if not r['success']]
            if failed_browsers:
                raise AssertionError(f"Browser compatibility test failed for: {failed_browsers}")
            
            return results
        return wrapper
    return decorator


# Test Mixins
class PerformanceTestMixin:
    """Mixin for performance testing utilities"""
    
    def assertResponseTime(self, response_time, max_time, operation_name="Operation"):
        """Assert response time is within limits"""
        self.assertLess(
            response_time, max_time,
            f"{operation_name} took too long: {response_time:.3f}s > {max_time}s"
        )
    
    def measureResponseTime(self, func, *args, **kwargs):
        """Measure and return function execution time"""
        return TestUtils.measure_response_time(func, *args, **kwargs)


class SecurityTestMixin:
    """Mixin for security testing utilities"""
    
    def assertSecurityEvent(self, event_type, user=None, severity=None):
        """Assert that a security event was logged"""
        from users.models import SecurityLog
        
        filters = {'event_type': event_type}
        if user:
            filters['user'] = user
        if severity:
            filters['severity'] = severity
        
        logs = SecurityLog.objects.filter(**filters)
        self.assertTrue(logs.exists(), f"Security event '{event_type}' was not logged")
    
    def assertRateLimited(self, response):
        """Assert that response indicates rate limiting"""
        self.assertEqual(response.status_code, 429)
        self.assertFalse(response.data.get('success', True))


class BrowserCompatibilityTestMixin:
    """Mixin for browser compatibility testing utilities"""
    
    def setUserAgent(self, browser_name):
        """Set user agent for browser"""
        user_agent = TestUtils.get_user_agent(browser_name)
        self.client.defaults['HTTP_USER_AGENT'] = user_agent
        return user_agent
    
    def clearUserAgent(self):
        """Clear user agent"""
        if 'HTTP_USER_AGENT' in self.client.defaults:
            del self.client.defaults['HTTP_USER_AGENT']
    
    def testAcrossBrowsers(self, test_func, browsers=None):
        """Run test function across multiple browsers"""
        if browsers is None:
            browsers = list(USER_AGENTS.keys())
        
        results = {}
        for browser in browsers:
            with self.subTest(browser=browser):
                self.setUserAgent(browser)
                try:
                    result = test_func()
                    results[browser] = {'success': True, 'result': result}
                except Exception as e:
                    results[browser] = {'success': False, 'error': str(e)}
                    raise
                finally:
                    self.clearUserAgent()
        
        return results
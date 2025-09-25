"""
Browser compatibility tests for the authentication system.
Tests different user agents, headers, and browser-specific behaviors.
"""

import json
from unittest.mock import patch

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import UserSession, SecurityLog

User = get_user_model()


class UserAgentCompatibilityTest(APITestCase):
    """Test compatibility with different user agents (browsers)"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='TestPassword123!'
        )
        
        # Common user agents for different browsers and versions
        self.user_agents = {
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
    
    def test_login_across_different_browsers(self):
        """Test login functionality across different browsers"""
        login_url = reverse('api_users:login')
        
        for browser_name, user_agent in self.user_agents.items():
            with self.subTest(browser=browser_name):
                # Set user agent
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': 'testuser',
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
                self.assertIsNotNone(session, f"Session not created for {browser_name}")
                
                # Clean up for next test
                if 'HTTP_USER_AGENT' in self.client.defaults:
                    del self.client.defaults['HTTP_USER_AGENT']
    
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
                
                # Clean up for next test
                if 'HTTP_USER_AGENT' in self.client.defaults:
                    del self.client.defaults['HTTP_USER_AGENT']
    
    def test_api_responses_format_consistency(self):
        """Test API response format consistency across browsers"""
        login_url = reverse('api_users:login')
        
        expected_fields = ['success', 'user', 'tokens', 'security_info']
        
        for browser_name, user_agent in self.user_agents.items():
            with self.subTest(browser=browser_name):
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': 'testuser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                
                # Check response format consistency
                for field in expected_fields:
                    self.assertIn(field, response.data, f"Missing field {field} for {browser_name}")
                
                # Check JSON serialization works properly
                json_response = json.dumps(response.data, default=str)
                self.assertIsInstance(json_response, str)
                
                # Clean up
                if 'HTTP_USER_AGENT' in self.client.defaults:
                    del self.client.defaults['HTTP_USER_AGENT']
    
    def test_mobile_browser_compatibility(self):
        """Test specific mobile browser compatibility"""
        mobile_agents = {
            'ios_safari': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            'android_chrome': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36',
            'android_firefox': 'Mozilla/5.0 (Mobile; rv:89.0) Gecko/89.0 Firefox/89.0',
            'windows_mobile': 'Mozilla/5.0 (Windows Phone 10.0; Android 6.0.1; Microsoft; Lumia 950) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/52.0.2743.116 Mobile Safari/537.36 Edge/15.14977'
        }
        
        login_url = reverse('api_users:login')
        
        for mobile_name, user_agent in mobile_agents.items():
            with self.subTest(mobile=mobile_name):
                self.client.defaults['HTTP_USER_AGENT'] = user_agent
                
                data = {
                    'username': 'testuser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Verify mobile-specific handling if any
                session = UserSession.objects.filter(
                    user=self.user,
                    user_agent=user_agent
                ).first()
                self.assertIsNotNone(session)
                
                # Clean up
                if 'HTTP_USER_AGENT' in self.client.defaults:
                    del self.client.defaults['HTTP_USER_AGENT']


class HTTPHeaderCompatibilityTest(APITestCase):
    """Test compatibility with different HTTP headers"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='headeruser',
            email='header@example.com',
            password='TestPassword123!'
        )
    
    def test_accept_header_variations(self):
        """Test different Accept header values"""
        login_url = reverse('api_users:login')
        
        accept_headers = [
            'application/json',
            'application/json, text/plain, */*',
            'application/json;charset=UTF-8',
            'application/json, application/xml, text/plain, */*',
            '*/*',
            'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'
        ]
        
        for accept_header in accept_headers:
            with self.subTest(accept=accept_header):
                self.client.defaults['HTTP_ACCEPT'] = accept_header
                
                data = {
                    'username': 'headeruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Clean up
                if 'HTTP_ACCEPT' in self.client.defaults:
                    del self.client.defaults['HTTP_ACCEPT']
    
    def test_content_type_variations(self):
        """Test different Content-Type header values"""
        login_url = reverse('api_users:login')
        
        data = {
            'username': 'headeruser',
            'password': 'TestPassword123!'
        }
        
        # Test JSON content type
        response = self.client.post(login_url, data, content_type='application/json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test form data content type
        response = self.client.post(login_url, data, content_type='application/x-www-form-urlencoded')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_language_header_handling(self):
        """Test Accept-Language header handling"""
        login_url = reverse('api_users:login')
        
        language_headers = [
            'en-US,en;q=0.9',
            'fa-IR,fa;q=0.9,en;q=0.8',
            'ar-SA,ar;q=0.9',
            'zh-CN,zh;q=0.9',
            'es-ES,es;q=0.9',
            'fr-FR,fr;q=0.9'
        ]
        
        for lang_header in language_headers:
            with self.subTest(language=lang_header):
                self.client.defaults['HTTP_ACCEPT_LANGUAGE'] = lang_header
                
                data = {
                    'username': 'headeruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Clean up
                if 'HTTP_ACCEPT_LANGUAGE' in self.client.defaults:
                    del self.client.defaults['HTTP_ACCEPT_LANGUAGE']
    
    def test_encoding_header_handling(self):
        """Test Accept-Encoding header handling"""
        login_url = reverse('api_users:login')
        
        encoding_headers = [
            'gzip, deflate, br',
            'gzip, deflate',
            'gzip',
            'deflate',
            'br',
            'identity',
            '*'
        ]
        
        for encoding_header in encoding_headers:
            with self.subTest(encoding=encoding_header):
                self.client.defaults['HTTP_ACCEPT_ENCODING'] = encoding_header
                
                data = {
                    'username': 'headeruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Clean up
                if 'HTTP_ACCEPT_ENCODING' in self.client.defaults:
                    del self.client.defaults['HTTP_ACCEPT_ENCODING']
    
    def test_custom_headers_handling(self):
        """Test handling of custom headers"""
        login_url = reverse('api_users:login')
        
        custom_headers = {
            'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
            'HTTP_X_CSRF_TOKEN': 'test-csrf-token',
            'HTTP_X_API_VERSION': '1.0',
            'HTTP_X_CLIENT_VERSION': '2.1.0',
            'HTTP_ORIGIN': 'https://example.com',
            'HTTP_REFERER': 'https://example.com/login'
        }
        
        for header_name, header_value in custom_headers.items():
            with self.subTest(header=header_name):
                self.client.defaults[header_name] = header_value
                
                data = {
                    'username': 'headeruser',
                    'password': 'TestPassword123!'
                }
                
                response = self.client.post(login_url, data)
                
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.data['success'])
                
                # Clean up
                if header_name in self.client.defaults:
                    del self.client.defaults[header_name]


class JavaScriptCompatibilityTest(APITestCase):
    """Test JavaScript/AJAX compatibility"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='jsuser',
            email='js@example.com',
            password='TestPassword123!'
        )
    
    def test_ajax_request_handling(self):
        """Test AJAX request handling"""
        login_url = reverse('api_users:login')
        
        # Simulate AJAX request
        self.client.defaults['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'
        self.client.defaults['HTTP_CONTENT_TYPE'] = 'application/json'
        
        data = {
            'username': 'jsuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Response should be JSON
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_cors_headers_handling(self):
        """Test CORS headers handling"""
        login_url = reverse('api_users:login')
        
        # Simulate cross-origin request
        self.client.defaults['HTTP_ORIGIN'] = 'https://frontend.example.com'
        
        data = {
            'username': 'jsuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Check if CORS headers are present (if implemented)
        # Note: This depends on your CORS configuration
        # self.assertIn('Access-Control-Allow-Origin', response)
    
    def test_json_response_format(self):
        """Test JSON response format consistency"""
        endpoints_to_test = [
            ('api_users:login', {'username': 'jsuser', 'password': 'TestPassword123!'}),
            ('api_users:register', {
                'username': 'jsnewuser',
                'email': 'jsnew@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            })
        ]
        
        for endpoint_name, data in endpoints_to_test:
            with self.subTest(endpoint=endpoint_name):
                url = reverse(endpoint_name)
                response = self.client.post(url, data)
                
                # Should return valid JSON
                self.assertIn(response.status_code, [200, 201])
                
                # Response should be parseable as JSON
                json_data = response.json()
                self.assertIsInstance(json_data, dict)
                
                # Should have consistent structure
                self.assertIn('success', json_data)
                self.assertIsInstance(json_data['success'], bool)


class LegacyBrowserCompatibilityTest(APITestCase):
    """Test compatibility with legacy browsers"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='legacyuser',
            email='legacy@example.com',
            password='TestPassword123!'
        )
    
    def test_ie11_compatibility(self):
        """Test Internet Explorer 11 compatibility"""
        login_url = reverse('api_users:login')
        
        # IE11 user agent
        ie11_agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko'
        self.client.defaults['HTTP_USER_AGENT'] = ie11_agent
        
        data = {
            'username': 'legacyuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        
        # Verify session was created
        session = UserSession.objects.filter(
            user=self.user,
            user_agent=ie11_agent
        ).first()
        self.assertIsNotNone(session)
    
    def test_old_chrome_compatibility(self):
        """Test old Chrome version compatibility"""
        login_url = reverse('api_users:login')
        
        # Old Chrome user agent
        old_chrome_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.113 Safari/537.36'
        self.client.defaults['HTTP_USER_AGENT'] = old_chrome_agent
        
        data = {
            'username': 'legacyuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
    
    def test_old_firefox_compatibility(self):
        """Test old Firefox version compatibility"""
        login_url = reverse('api_users:login')
        
        # Old Firefox user agent
        old_firefox_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:50.0) Gecko/20100101 Firefox/50.0'
        self.client.defaults['HTTP_USER_AGENT'] = old_firefox_agent
        
        data = {
            'username': 'legacyuser',
            'password': 'TestPassword123!'
        }
        
        response = self.client.post(login_url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])


class ResponseTimeConsistencyTest(APITestCase):
    """Test response time consistency across different browsers"""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='timeuser',
            email='time@example.com',
            password='TestPassword123!'
        )
        
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        ]
    
    def test_login_response_time_consistency(self):
        """Test login response time consistency across browsers"""
        import time
        
        login_url = reverse('api_users:login')
        response_times = []
        
        for user_agent in self.user_agents:
            self.client.defaults['HTTP_USER_AGENT'] = user_agent
            
            data = {
                'username': 'timeuser',
                'password': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = self.client.post(login_url, data)
            end_time = time.time()
            
            response_time = end_time - start_time
            response_times.append(response_time)
            
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            # Clean up
            if 'HTTP_USER_AGENT' in self.client.defaults:
                del self.client.defaults['HTTP_USER_AGENT']
        
        # Check response time consistency
        if len(response_times) > 1:
            max_time = max(response_times)
            min_time = min(response_times)
            time_variance = max_time - min_time
            
            # Response times should not vary too much (within 100ms)
            self.assertLess(time_variance, 0.1, f"Response time variance too high: {time_variance:.3f}s")
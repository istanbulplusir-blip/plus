"""
Performance tests for authentication system endpoints.
Tests response times, database query optimization, and concurrent access.
"""

import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import patch

from django.test import TestCase, TransactionTestCase
from django.test.utils import override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection
from django.core.cache import cache
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from users.models import UserSession, SecurityLog, OtpCode

User = get_user_model()


class LoginPerformanceTest(APITestCase):
    """Performance tests for login endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.login_url = reverse('api_users:login')
        
        # Create test users
        self.users = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'perfuser{i}',
                email=f'perfuser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
    
    def test_single_login_response_time(self):
        """Test single login request response time"""
        data = {
            'username': 'perfuser0',
            'password': 'TestPassword123!'
        }
        
        start_time = time.time()
        response = self.client.post(self.login_url, data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5, f"Login took too long: {response_time}s")
    
    def test_multiple_sequential_logins(self):
        """Test multiple sequential login requests"""
        start_time = time.time()
        
        for i in range(10):
            data = {
                'username': f'perfuser{i}',
                'password': 'TestPassword123!'
            }
            
            response = self.client.post(self.login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 10
        
        self.assertLess(total_time, 5.0, f"10 logins took too long: {total_time}s")
        self.assertLess(avg_time, 0.5, f"Average login time too slow: {avg_time}s")
    
    def test_concurrent_logins(self):
        """Test concurrent login requests"""
        def login_user(user_index):
            client = APIClient()
            data = {
                'username': f'perfuser{user_index}',
                'password': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = client.post(self.login_url, data)
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
        
        # Total time should be reasonable for concurrent requests
        self.assertLess(total_time, 3.0, f"Concurrent logins took too long: {total_time}s")
        
        # Individual response times should be reasonable
        max_response_time = max(r['response_time'] for r in results)
        self.assertLess(max_response_time, 2.0, f"Slowest login: {max_response_time}s")
    
    def test_login_database_queries(self):
        """Test number of database queries during login"""
        data = {
            'username': 'perfuser0',
            'password': 'TestPassword123!'
        }
        
        with self.assertNumQueries(10):  # Adjust based on actual implementation
            response = self.client.post(self.login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class RegistrationPerformanceTest(APITestCase):
    """Performance tests for registration endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.registration_url = reverse('api_users:register')
    
    def test_single_registration_response_time(self):
        """Test single registration request response time"""
        data = {
            'username': 'perfreguser',
            'email': 'perfreguser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        start_time = time.time()
        response = self.client.post(self.registration_url, data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertLess(response_time, 1.0, f"Registration took too long: {response_time}s")
    
    def test_multiple_sequential_registrations(self):
        """Test multiple sequential registration requests"""
        start_time = time.time()
        
        for i in range(5):  # Fewer than login tests due to unique constraints
            data = {
                'username': f'seqreguser{i}',
                'email': f'seqreguser{i}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            response = self.client.post(self.registration_url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 5
        
        self.assertLess(total_time, 5.0, f"5 registrations took too long: {total_time}s")
        self.assertLess(avg_time, 1.0, f"Average registration time too slow: {avg_time}s")
    
    def test_concurrent_registrations(self):
        """Test concurrent registration requests"""
        def register_user(user_index):
            client = APIClient()
            data = {
                'username': f'concreguser{user_index}',
                'email': f'concreguser{user_index}@example.com',
                'password': 'TestPassword123!',
                'password_confirm': 'TestPassword123!'
            }
            
            start_time = time.time()
            response = client.post(self.registration_url, data)
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
        
        # Total time should be reasonable for concurrent requests
        self.assertLess(total_time, 5.0, f"Concurrent registrations took too long: {total_time}s")
    
    def test_registration_database_queries(self):
        """Test number of database queries during registration"""
        data = {
            'username': 'dbqueryuser',
            'email': 'dbqueryuser@example.com',
            'password': 'TestPassword123!',
            'password_confirm': 'TestPassword123!'
        }
        
        with self.assertNumQueries(15):  # Adjust based on actual implementation
            response = self.client.post(self.registration_url, data)
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class OTPPerformanceTest(APITestCase):
    """Performance tests for OTP endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.send_otp_url = reverse('api_users:send-otp')
        self.verify_otp_url = reverse('api_users:verify-otp')
        
        # Create test user
        self.user = User.objects.create_user(
            username='otpuser',
            email='otpuser@example.com',
            phone='+989123456789',
            password='TestPassword123!'
        )
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_otp_send_response_time(self, mock_send_sms):
        """Test OTP send response time"""
        mock_send_sms.return_value = True
        
        data = {
            'contact_info': '+989123456789',
            'delivery_method': 'sms',
            'purpose': 'login'
        }
        
        start_time = time.time()
        response = self.client.post(self.send_otp_url, data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5, f"OTP send took too long: {response_time}s")
    
    @patch('users.services.otp.OTPService._send_sms')
    def test_multiple_otp_sends(self, mock_send_sms):
        """Test multiple OTP send requests"""
        mock_send_sms.return_value = True
        
        start_time = time.time()
        
        for i in range(5):
            data = {
                'contact_info': f'+98912345678{i}',
                'delivery_method': 'sms',
                'purpose': 'login'
            }
            
            response = self.client.post(self.send_otp_url, data)
            # Note: May hit rate limiting, so check for both success and rate limit
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_429_TOO_MANY_REQUESTS])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        self.assertLess(total_time, 3.0, f"5 OTP sends took too long: {total_time}s")
    
    def test_otp_verification_response_time(self):
        """Test OTP verification response time"""
        # Create OTP for testing
        from users.models import generate_hash
        from django.utils import timezone
        from datetime import timedelta
        
        otp = OtpCode.objects.create(
            user=self.user,
            contact_info='+989123456789',
            delivery_method='sms',
            hashed_code=generate_hash('123456'),
            purpose='login',
            expires_at=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        data = {
            'contact_info': '+989123456789',
            'otp': '123456',
            'purpose': 'login'
        }
        
        start_time = time.time()
        response = self.client.post(self.verify_otp_url, data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.3, f"OTP verification took too long: {response_time}s")


class ProfilePerformanceTest(APITestCase):
    """Performance tests for profile endpoint"""
    
    def setUp(self):
        self.client = APIClient()
        self.profile_url = reverse('api_users:profile')
        
        # Create test user with related data
        self.user = User.objects.create_user(
            username='profileuser',
            email='profileuser@example.com',
            password='TestPassword123!'
        )
        
        # Create related sessions and logs
        for i in range(10):
            UserSession.objects.create(
                user=self.user,
                session_key=f'session_{i}',
                ip_address=f'192.168.1.{i+1}',
                user_agent=f'Browser {i}'
            )
            
            SecurityLog.objects.create(
                user=self.user,
                event_type='login_success',
                ip_address=f'192.168.1.{i+1}',
                severity='low'
            )
        
        # Authenticate user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_profile_retrieval_response_time(self):
        """Test profile retrieval response time"""
        start_time = time.time()
        response = self.client.get(self.profile_url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.3, f"Profile retrieval took too long: {response_time}s")
    
    def test_multiple_profile_requests(self):
        """Test multiple profile requests"""
        start_time = time.time()
        
        for _ in range(20):
            response = self.client.get(self.profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / 20
        
        self.assertLess(total_time, 3.0, f"20 profile requests took too long: {total_time}s")
        self.assertLess(avg_time, 0.15, f"Average profile request too slow: {avg_time}s")
    
    def test_profile_database_queries(self):
        """Test number of database queries for profile retrieval"""
        with self.assertNumQueries(5):  # Adjust based on actual implementation
            response = self.client.get(self.profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_profile_update_response_time(self):
        """Test profile update response time"""
        data = {
            'first_name': 'Updated',
            'last_name': 'Name'
        }
        
        start_time = time.time()
        response = self.client.patch(self.profile_url, data)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5, f"Profile update took too long: {response_time}s")


class SessionManagementPerformanceTest(APITestCase):
    """Performance tests for session management endpoints"""
    
    def setUp(self):
        self.client = APIClient()
        self.sessions_url = reverse('api_users:user-sessions')
        
        # Create test user
        self.user = User.objects.create_user(
            username='sessionuser',
            email='sessionuser@example.com',
            password='TestPassword123!'
        )
        
        # Create many sessions
        for i in range(50):
            UserSession.objects.create(
                user=self.user,
                session_key=f'session_{i}',
                ip_address=f'192.168.{i//255}.{i%255}',
                user_agent=f'Browser {i}',
                is_active=i % 2 == 0  # Mix of active and inactive
            )
        
        # Authenticate user
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
    
    def test_sessions_list_response_time(self):
        """Test sessions list response time"""
        start_time = time.time()
        response = self.client.get(self.sessions_url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 0.5, f"Sessions list took too long: {response_time}s")
    
    def test_sessions_list_database_queries(self):
        """Test number of database queries for sessions list"""
        with self.assertNumQueries(3):  # Adjust based on actual implementation
            response = self.client.get(self.sessions_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_logout_all_devices_performance(self):
        """Test logout all devices performance"""
        logout_all_url = reverse('api_users:logout-all-devices')
        
        start_time = time.time()
        response = self.client.post(logout_all_url)
        end_time = time.time()
        
        response_time = end_time - start_time
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertLess(response_time, 1.0, f"Logout all devices took too long: {response_time}s")


class CachePerformanceTest(TestCase):
    """Performance tests for caching functionality"""
    
    def setUp(self):
        cache.clear()
    
    def test_rate_limiting_cache_performance(self):
        """Test rate limiting cache performance"""
        from users.services.security import SecurityService
        
        identifier = 'test_cache_performance'
        action = 'test_action'
        
        # Test cache write performance
        start_time = time.time()
        
        for i in range(100):
            SecurityService.increment_rate_limit(f'{identifier}_{i}', action)
        
        end_time = time.time()
        write_time = end_time - start_time
        
        self.assertLess(write_time, 1.0, f"Cache writes took too long: {write_time}s")
        
        # Test cache read performance
        start_time = time.time()
        
        for i in range(100):
            is_allowed, rate_info = SecurityService.check_rate_limit(f'{identifier}_{i}', action)
        
        end_time = time.time()
        read_time = end_time - start_time
        
        self.assertLess(read_time, 0.5, f"Cache reads took too long: {read_time}s")
    
    def test_session_cache_performance(self):
        """Test session-related cache performance"""
        # This would test session caching if implemented
        # For now, just verify cache operations work quickly
        
        start_time = time.time()
        
        for i in range(50):
            cache.set(f'session_test_{i}', {'user_id': i, 'data': 'test'}, 300)
        
        end_time = time.time()
        cache_set_time = end_time - start_time
        
        self.assertLess(cache_set_time, 0.5, f"Cache set operations took too long: {cache_set_time}s")
        
        start_time = time.time()
        
        for i in range(50):
            value = cache.get(f'session_test_{i}')
            self.assertIsNotNone(value)
        
        end_time = time.time()
        cache_get_time = end_time - start_time
        
        self.assertLess(cache_get_time, 0.3, f"Cache get operations took too long: {cache_get_time}s")


class DatabaseOptimizationTest(TransactionTestCase):
    """Tests for database query optimization"""
    
    def setUp(self):
        # Create test data
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'dbuser{i}',
                email=f'dbuser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
            
            # Create related data
            for j in range(5):
                UserSession.objects.create(
                    user=user,
                    session_key=f'session_{i}_{j}',
                    ip_address=f'192.168.{i}.{j}',
                    user_agent=f'Browser {j}'
                )
                
                SecurityLog.objects.create(
                    user=user,
                    event_type='login_success',
                    ip_address=f'192.168.{i}.{j}',
                    severity='low'
                )
    
    def test_user_lookup_optimization(self):
        """Test user lookup query optimization"""
        # Test lookup by username (should use index)
        start_time = time.time()
        
        for i in range(10):
            user = User.objects.get(username=f'dbuser{i}')
            self.assertIsNotNone(user)
        
        end_time = time.time()
        lookup_time = end_time - start_time
        
        self.assertLess(lookup_time, 0.1, f"User lookups took too long: {lookup_time}s")
    
    def test_session_queries_optimization(self):
        """Test session-related query optimization"""
        user = self.users[0]
        
        # Test fetching user sessions (should use select_related/prefetch_related)
        start_time = time.time()
        
        sessions = list(UserSession.objects.filter(user=user, is_active=True))
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 0.05, f"Session query took too long: {query_time}s")
        self.assertGreater(len(sessions), 0)
    
    def test_security_log_queries_optimization(self):
        """Test security log query optimization"""
        user = self.users[0]
        
        # Test fetching recent security logs
        start_time = time.time()
        
        logs = list(SecurityLog.objects.filter(user=user).order_by('-created_at')[:10])
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 0.05, f"Security log query took too long: {query_time}s")
        self.assertGreater(len(logs), 0)
    
    def test_bulk_operations_performance(self):
        """Test bulk database operations performance"""
        # Test bulk session deactivation (logout all devices scenario)
        user = self.users[0]
        
        start_time = time.time()
        
        # Bulk update sessions
        UserSession.objects.filter(user=user).update(is_active=False)
        
        end_time = time.time()
        bulk_update_time = end_time - start_time
        
        self.assertLess(bulk_update_time, 0.1, f"Bulk update took too long: {bulk_update_time}s")
        
        # Verify update worked
        active_sessions = UserSession.objects.filter(user=user, is_active=True).count()
        self.assertEqual(active_sessions, 0)
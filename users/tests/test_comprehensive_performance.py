"""
Comprehensive performance tests for the authentication system.
Tests load handling, memory usage, database optimization, and scalability.
"""

import time
import threading
import psutil
import gc
from datetime import timedelta
from unittest.mock import patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.test import TestCase, TransactionTestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.db import connection, transaction
from django.core.cache import cache
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from users.models import (
    OtpCode, UserSession, PasswordResetToken, SecurityLog, 
    EmailVerificationToken, generate_hash
)
from users.services.otp import OTPService
from users.services.security import SecurityService

User = get_user_model()


class LoadTestingTest(TransactionTestCase):
    """Load testing for authentication endpoints"""
    
    def setUp(self):
        # Create test users for load testing
        self.users = []
        for i in range(100):
            user = User.objects.create_user(
                username=f'loaduser{i}',
                email=f'loaduser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
        
        cache.clear()
    
    def test_high_volume_login_requests(self):
        """Test system under high volume of login requests"""
        login_url = reverse('api_users:login')
        
        def perform_login(user_index):
            client = APIClient()
            data = {
                'username': f'loaduser{user_index}',
                'password': 'TestPassword123!'
            }
            
            start_time = time.time()
            try:
                response = client.post(login_url, data)
                end_time = time.time()
                
                return {
                    'success': response.status_code == 200,
                    'response_time': end_time - start_time,
                    'status_code': response.status_code,
                    'user_index': user_index
                }
            except Exception as e:
                end_time = time.time()
                return {
                    'success': False,
                    'response_time': end_time - start_time,
                    'error': str(e),
                    'user_index': user_index
                }
        
        # Test with 50 concurrent login requests
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = [executor.submit(perform_login, i) for i in range(50)]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Analyze results
        successful_logins = sum(1 for r in results if r['success'])
        failed_logins = len(results) - successful_logins
        
        response_times = [r['response_time'] for r in results if 'response_time' in r]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        # Performance assertions
        self.assertGreaterEqual(successful_logins, 45, f"Too many failed logins: {failed_logins}")
        self.assertLess(total_time, 30.0, f"Load test took too long: {total_time}s")
        self.assertLess(avg_response_time, 2.0, f"Average response time too slow: {avg_response_time}s")
        self.assertLess(max_response_time, 5.0, f"Slowest response too slow: {max_response_time}s")
        
        print(f"Load Test Results:")
        print(f"  Total time: {total_time:.2f}s")
        print(f"  Successful logins: {successful_logins}/{len(results)}")
        print(f"  Average response time: {avg_response_time:.3f}s")
        print(f"  Min/Max response time: {min_response_time:.3f}s / {max_response_time:.3f}s")
    
    def test_sustained_load_over_time(self):
        """Test system performance under sustained load"""
        login_url = reverse('api_users:login')
        
        def sustained_login_worker(duration_seconds):
            client = APIClient()
            start_time = time.time()
            request_count = 0
            successful_requests = 0
            
            while time.time() - start_time < duration_seconds:
                user_index = request_count % len(self.users)
                data = {
                    'username': f'loaduser{user_index}',
                    'password': 'TestPassword123!'
                }
                
                try:
                    response = client.post(login_url, data)
                    if response.status_code == 200:
                        successful_requests += 1
                    request_count += 1
                    
                    # Small delay to simulate realistic usage
                    time.sleep(0.1)
                    
                except Exception:
                    request_count += 1
            
            return {
                'total_requests': request_count,
                'successful_requests': successful_requests,
                'duration': time.time() - start_time
            }
        
        # Run sustained load for 30 seconds with 5 concurrent workers
        test_duration = 30
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(sustained_login_worker, test_duration)
                for _ in range(5)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze sustained load results
        total_requests = sum(r['total_requests'] for r in results)
        total_successful = sum(r['successful_requests'] for r in results)
        success_rate = (total_successful / total_requests) * 100 if total_requests > 0 else 0
        
        requests_per_second = total_requests / test_duration
        
        # Performance assertions
        self.assertGreater(success_rate, 90, f"Success rate too low: {success_rate:.1f}%")
        self.assertGreater(requests_per_second, 10, f"Throughput too low: {requests_per_second:.1f} req/s")
        
        print(f"Sustained Load Results:")
        print(f"  Duration: {test_duration}s")
        print(f"  Total requests: {total_requests}")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Requests per second: {requests_per_second:.1f}")
    
    def test_memory_usage_under_load(self):
        """Test memory usage under load"""
        login_url = reverse('api_users:login')
        
        # Measure initial memory usage
        gc.collect()  # Force garbage collection
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        def memory_intensive_login(user_index):
            client = APIClient()
            data = {
                'username': f'loaduser{user_index}',
                'password': 'TestPassword123!'
            }
            
            # Perform multiple requests to stress memory
            for _ in range(5):
                response = client.post(login_url, data)
            
            return response.status_code
        
        # Perform memory-intensive operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(memory_intensive_login, i % len(self.users))
                for i in range(100)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        # Measure memory after load
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage assertions
        self.assertLess(memory_increase, 100, f"Memory usage increased too much: {memory_increase:.1f}MB")
        
        print(f"Memory Usage Test:")
        print(f"  Initial memory: {initial_memory:.1f}MB")
        print(f"  Final memory: {final_memory:.1f}MB")
        print(f"  Memory increase: {memory_increase:.1f}MB")


class DatabaseOptimizationTest(TransactionTestCase):
    """Test database query optimization and performance"""
    
    def setUp(self):
        # Create test data with relationships
        self.users = []
        for i in range(50):
            user = User.objects.create_user(
                username=f'dbuser{i}',
                email=f'dbuser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
            
            # Create related data
            for j in range(10):
                UserSession.objects.create(
                    user=user,
                    session_key=f'session_{i}_{j}',
                    ip_address=f'192.168.{i//255}.{i%255}',
                    user_agent=f'Browser {j}',
                    is_active=j % 2 == 0
                )
                
                SecurityLog.objects.create(
                    user=user,
                    event_type='login_success',
                    ip_address=f'192.168.{i//255}.{i%255}',
                    severity='low'
                )
    
    def test_user_lookup_query_performance(self):
        """Test user lookup query performance"""
        # Test username lookup (should use index)
        start_time = time.time()
        
        for i in range(100):
            user_index = i % len(self.users)
            user = User.objects.get(username=f'dbuser{user_index}')
            self.assertIsNotNone(user)
        
        end_time = time.time()
        lookup_time = end_time - start_time
        
        self.assertLess(lookup_time, 0.5, f"User lookups took too long: {lookup_time:.3f}s")
        
        # Test email lookup (should use index)
        start_time = time.time()
        
        for i in range(100):
            user_index = i % len(self.users)
            user = User.objects.get(email=f'dbuser{user_index}@example.com')
            self.assertIsNotNone(user)
        
        end_time = time.time()
        email_lookup_time = end_time - start_time
        
        self.assertLess(email_lookup_time, 0.5, f"Email lookups took too long: {email_lookup_time:.3f}s")
    
    def test_session_queries_optimization(self):
        """Test session-related query optimization"""
        user = self.users[0]
        
        # Test fetching active sessions
        start_time = time.time()
        
        for _ in range(50):
            sessions = list(UserSession.objects.filter(user=user, is_active=True))
            self.assertGreater(len(sessions), 0)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 0.5, f"Session queries took too long: {query_time:.3f}s")
        
        # Test session count query
        start_time = time.time()
        
        for _ in range(100):
            count = UserSession.objects.filter(user=user, is_active=True).count()
            self.assertGreater(count, 0)
        
        end_time = time.time()
        count_time = end_time - start_time
        
        self.assertLess(count_time, 0.3, f"Session count queries took too long: {count_time:.3f}s")
    
    def test_security_log_queries_optimization(self):
        """Test security log query optimization"""
        user = self.users[0]
        
        # Test recent logs query
        start_time = time.time()
        
        for _ in range(50):
            logs = list(SecurityLog.objects.filter(user=user).order_by('-created_at')[:10])
            self.assertGreater(len(logs), 0)
        
        end_time = time.time()
        query_time = end_time - start_time
        
        self.assertLess(query_time, 0.5, f"Security log queries took too long: {query_time:.3f}s")
        
        # Test filtered logs query
        start_time = time.time()
        
        for _ in range(50):
            logs = list(SecurityLog.objects.filter(
                user=user,
                event_type='login_success',
                severity='low'
            ))
            self.assertGreater(len(logs), 0)
        
        end_time = time.time()
        filtered_query_time = end_time - start_time
        
        self.assertLess(filtered_query_time, 0.5, f"Filtered log queries took too long: {filtered_query_time:.3f}s")
    
    def test_bulk_operations_performance(self):
        """Test bulk database operations performance"""
        user = self.users[0]
        
        # Test bulk session deactivation
        start_time = time.time()
        
        updated_count = UserSession.objects.filter(user=user).update(is_active=False)
        
        end_time = time.time()
        bulk_update_time = end_time - start_time
        
        self.assertLess(bulk_update_time, 0.1, f"Bulk update took too long: {bulk_update_time:.3f}s")
        self.assertGreater(updated_count, 0)
        
        # Test bulk log creation
        start_time = time.time()
        
        logs_to_create = [
            SecurityLog(
                user=user,
                event_type='test_event',
                ip_address=f'10.0.0.{i}',
                severity='low'
            )
            for i in range(100)
        ]
        
        SecurityLog.objects.bulk_create(logs_to_create)
        
        end_time = time.time()
        bulk_create_time = end_time - start_time
        
        self.assertLess(bulk_create_time, 0.5, f"Bulk create took too long: {bulk_create_time:.3f}s")
    
    def test_query_count_optimization(self):
        """Test that endpoints don't generate excessive queries"""
        user = self.users[0]
        
        # Test login endpoint query count
        login_url = reverse('api_users:login')
        data = {
            'username': user.username,
            'password': 'TestPassword123!'
        }
        
        with self.assertNumQueries(15):  # Adjust based on actual implementation
            client = APIClient()
            response = client.post(login_url, data)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Test profile endpoint query count
        profile_url = reverse('api_users:profile')
        refresh = RefreshToken.for_user(user)
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {refresh.access_token}')
        
        with self.assertNumQueries(8):  # Adjust based on actual implementation
            response = client.get(profile_url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class CachePerformanceTest(TestCase):
    """Test caching performance and effectiveness"""
    
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username='cacheuser',
            email='cache@example.com',
            password='TestPassword123!'
        )
    
    def test_rate_limiting_cache_performance(self):
        """Test rate limiting cache performance"""
        # Test cache write performance
        start_time = time.time()
        
        for i in range(1000):
            SecurityService.increment_rate_limit(f'test_ip_{i}', 'login_attempts')
        
        end_time = time.time()
        write_time = end_time - start_time
        
        self.assertLess(write_time, 2.0, f"Cache writes took too long: {write_time:.3f}s")
        
        # Test cache read performance
        start_time = time.time()
        
        for i in range(1000):
            is_allowed, rate_info = SecurityService.check_rate_limit(f'test_ip_{i}', 'login_attempts')
        
        end_time = time.time()
        read_time = end_time - start_time
        
        self.assertLess(read_time, 1.0, f"Cache reads took too long: {read_time:.3f}s")
    
    def test_cache_hit_ratio(self):
        """Test cache hit ratio for common operations"""
        # Populate cache
        for i in range(100):
            cache.set(f'test_key_{i}', f'test_value_{i}', 300)
        
        # Test cache hits
        hit_count = 0
        miss_count = 0
        
        start_time = time.time()
        
        for i in range(200):  # 100 hits, 100 misses
            value = cache.get(f'test_key_{i}')
            if value is not None:
                hit_count += 1
            else:
                miss_count += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        hit_ratio = hit_count / (hit_count + miss_count) * 100
        
        self.assertEqual(hit_count, 100)
        self.assertEqual(miss_count, 100)
        self.assertEqual(hit_ratio, 50.0)
        self.assertLess(total_time, 0.5, f"Cache operations took too long: {total_time:.3f}s")
    
    def test_cache_memory_efficiency(self):
        """Test cache memory efficiency"""
        # Store large amounts of data in cache
        large_data = 'x' * 1000  # 1KB per entry
        
        start_time = time.time()
        
        for i in range(1000):  # 1MB total
            cache.set(f'large_key_{i}', large_data, 300)
        
        end_time = time.time()
        storage_time = end_time - start_time
        
        self.assertLess(storage_time, 5.0, f"Cache storage took too long: {storage_time:.3f}s")
        
        # Test retrieval performance
        start_time = time.time()
        
        for i in range(1000):
            value = cache.get(f'large_key_{i}')
            self.assertIsNotNone(value)
        
        end_time = time.time()
        retrieval_time = end_time - start_time
        
        self.assertLess(retrieval_time, 2.0, f"Cache retrieval took too long: {retrieval_time:.3f}s")


class ConcurrencyStressTest(TransactionTestCase):
    """Test system behavior under high concurrency"""
    
    def setUp(self):
        self.users = []
        for i in range(20):
            user = User.objects.create_user(
                username=f'concuser{i}',
                email=f'concuser{i}@example.com',
                password='TestPassword123!'
            )
            self.users.append(user)
        
        cache.clear()
    
    def test_concurrent_user_operations(self):
        """Test concurrent user operations (login, profile update, etc.)"""
        
        def mixed_operations(user_index):
            client = APIClient()
            user = self.users[user_index]
            results = []
            
            # Login
            login_data = {
                'username': user.username,
                'password': 'TestPassword123!'
            }
            response = client.post(reverse('api_users:login'), login_data)
            results.append(('login', response.status_code))
            
            if response.status_code == 200:
                # Get access token
                access_token = response.data['tokens']['access']
                client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')
                
                # Profile update
                profile_data = {'first_name': f'Concurrent{user_index}'}
                response = client.patch(reverse('api_users:profile'), profile_data)
                results.append(('profile_update', response.status_code))
                
                # Get sessions
                response = client.get(reverse('api_users:user-sessions'))
                results.append(('get_sessions', response.status_code))
            
            return results
        
        # Execute concurrent operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(mixed_operations, i)
                for i in range(len(self.users))
            ]
            all_results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        login_successes = sum(1 for results in all_results for op, status in results if op == 'login' and status == 200)
        profile_successes = sum(1 for results in all_results for op, status in results if op == 'profile_update' and status == 200)
        
        self.assertGreaterEqual(login_successes, len(self.users) * 0.9)  # 90% success rate
        self.assertGreaterEqual(profile_successes, len(self.users) * 0.8)  # 80% success rate
    
    def test_concurrent_otp_operations(self):
        """Test concurrent OTP operations"""
        send_otp_url = reverse('api_users:send-otp')
        verify_otp_url = reverse('api_users:verify-otp')
        
        def otp_operations(request_index):
            client = APIClient()
            
            with patch('users.services.otp.OTPService._send_sms', return_value=True):
                # Send OTP
                send_data = {
                    'contact_info': f'+98912345{request_index:04d}',
                    'delivery_method': 'sms',
                    'purpose': 'login'
                }
                send_response = client.post(send_otp_url, send_data)
                
                if send_response.status_code == 200:
                    # Verify OTP (simulate correct code)
                    with patch.object(OtpCode, 'verify_code', return_value=True):
                        verify_data = {
                            'contact_info': f'+98912345{request_index:04d}',
                            'otp': '123456',
                            'purpose': 'login'
                        }
                        verify_response = client.post(verify_otp_url, verify_data)
                        return (send_response.status_code, verify_response.status_code)
                
                return (send_response.status_code, None)
        
        # Execute concurrent OTP operations
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(otp_operations, i) for i in range(20)]
            results = [future.result() for future in as_completed(futures)]
        
        # Analyze results
        successful_sends = sum(1 for send_status, _ in results if send_status == 200)
        successful_verifies = sum(1 for _, verify_status in results if verify_status == 200)
        
        # Some requests might hit rate limits, but most should succeed
        self.assertGreaterEqual(successful_sends, 10)
        self.assertGreaterEqual(successful_verifies, 5)
    
    def test_database_connection_handling(self):
        """Test database connection handling under high concurrency"""
        
        def database_intensive_operation(operation_index):
            # Perform multiple database operations
            user = User.objects.get(username=f'concuser{operation_index % len(self.users)}')
            
            # Create session
            session = UserSession.objects.create(
                user=user,
                session_key=f'stress_session_{operation_index}',
                ip_address=f'10.0.{operation_index//255}.{operation_index%255}',
                user_agent=f'StressTest {operation_index}'
            )
            
            # Create security log
            SecurityLog.objects.create(
                user=user,
                event_type='stress_test',
                ip_address=session.ip_address,
                severity='low'
            )
            
            # Query operations
            sessions_count = UserSession.objects.filter(user=user).count()
            logs_count = SecurityLog.objects.filter(user=user).count()
            
            return (sessions_count, logs_count)
        
        # Execute database-intensive operations
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [
                executor.submit(database_intensive_operation, i)
                for i in range(100)
            ]
            results = [future.result() for future in as_completed(futures)]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # All operations should complete successfully
        self.assertEqual(len(results), 100)
        self.assertLess(total_time, 30.0, f"Database operations took too long: {total_time:.2f}s")
        
        # Verify data integrity
        total_sessions = UserSession.objects.filter(session_key__startswith='stress_session_').count()
        total_logs = SecurityLog.objects.filter(event_type='stress_test').count()
        
        self.assertEqual(total_sessions, 100)
        self.assertEqual(total_logs, 100)


class ScalabilityTest(TransactionTestCase):
    """Test system scalability characteristics"""
    
    def test_user_growth_scalability(self):
        """Test system performance as user count grows"""
        user_counts = [100, 500, 1000]
        performance_results = {}
        
        for user_count in user_counts:
            # Create users
            users = []
            start_time = time.time()
            
            for i in range(user_count):
                user = User.objects.create_user(
                    username=f'scaleuser{i}',
                    email=f'scaleuser{i}@example.com',
                    password='TestPassword123!'
                )
                users.append(user)
            
            creation_time = time.time() - start_time
            
            # Test login performance with this user count
            login_url = reverse('api_users:login')
            
            start_time = time.time()
            
            for i in range(min(50, user_count)):  # Test with up to 50 logins
                client = APIClient()
                data = {
                    'username': f'scaleuser{i}',
                    'password': 'TestPassword123!'
                }
                response = client.post(login_url, data)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
            
            login_time = time.time() - start_time
            
            performance_results[user_count] = {
                'creation_time': creation_time,
                'login_time': login_time,
                'avg_login_time': login_time / min(50, user_count)
            }
            
            # Clean up for next iteration
            User.objects.filter(username__startswith='scaleuser').delete()
        
        # Analyze scalability
        print("Scalability Test Results:")
        for user_count, results in performance_results.items():
            print(f"  {user_count} users:")
            print(f"    Creation time: {results['creation_time']:.2f}s")
            print(f"    Login time: {results['login_time']:.2f}s")
            print(f"    Avg login time: {results['avg_login_time']:.3f}s")
        
        # Performance should not degrade significantly with more users
        if len(performance_results) >= 2:
            small_scale = performance_results[user_counts[0]]
            large_scale = performance_results[user_counts[-1]]
            
            # Login time should not increase more than 2x
            performance_ratio = large_scale['avg_login_time'] / small_scale['avg_login_time']
            self.assertLess(performance_ratio, 2.0, f"Performance degraded too much: {performance_ratio:.2f}x")
    
    def test_data_volume_scalability(self):
        """Test system performance with large amounts of data"""
        user = User.objects.create_user(
            username='datavolumeuser',
            email='datavolume@example.com',
            password='TestPassword123!'
        )
        
        # Create large amounts of related data
        data_volumes = [1000, 5000, 10000]
        query_times = {}
        
        for volume in data_volumes:
            # Create sessions
            sessions = [
                UserSession(
                    user=user,
                    session_key=f'volume_session_{i}',
                    ip_address=f'192.168.{i//255}.{i%255}',
                    user_agent=f'Browser {i}'
                )
                for i in range(volume)
            ]
            UserSession.objects.bulk_create(sessions)
            
            # Create security logs
            logs = [
                SecurityLog(
                    user=user,
                    event_type='volume_test',
                    ip_address=f'192.168.{i//255}.{i%255}',
                    severity='low'
                )
                for i in range(volume)
            ]
            SecurityLog.objects.bulk_create(logs)
            
            # Test query performance
            start_time = time.time()
            
            # Query active sessions
            active_sessions = list(UserSession.objects.filter(user=user, is_active=True)[:100])
            
            # Query recent logs
            recent_logs = list(SecurityLog.objects.filter(user=user).order_by('-created_at')[:100])
            
            end_time = time.time()
            query_time = end_time - start_time
            
            query_times[volume] = query_time
            
            print(f"Data Volume {volume}: Query time {query_time:.3f}s")
            
            # Clean up for next iteration
            UserSession.objects.filter(user=user).delete()
            SecurityLog.objects.filter(user=user).delete()
        
        # Query performance should remain reasonable even with large data volumes
        for volume, query_time in query_times.items():
            self.assertLess(query_time, 1.0, f"Query time too slow for {volume} records: {query_time:.3f}s")
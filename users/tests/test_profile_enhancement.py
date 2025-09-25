"""
Tests for enhanced profile functionality
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
import json

User = get_user_model()


class ProfileEnhancementTestCase(TestCase):
    """Test case for enhanced profile functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='+989123456789'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_profile_page_loads(self):
        """Test that the enhanced profile page loads correctly"""
        response = self.client.get(reverse('users:profile'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'پروفایل کاربری')
        self.assertContains(response, 'اطلاعات شخصی')
        self.assertContains(response, 'جلسات فعال')
        self.assertContains(response, 'تنظیمات امنیتی')
    
    def test_profile_form_fields(self):
        """Test that all required form fields are present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'name="first_name"')
        self.assertContains(response, 'name="last_name"')
        self.assertContains(response, 'name="email"')
        self.assertContains(response, 'name="phone"')
        self.assertContains(response, 'name="birth_date"')
        self.assertContains(response, 'name="email_notifications"')
        self.assertContains(response, 'name="sms_notifications"')
    
    def test_verification_badges_display(self):
        """Test that verification badges are displayed correctly"""
        response = self.client.get(reverse('users:profile'))
        # Should show unverified badges by default
        self.assertContains(response, 'تأیید نشده')
        
        # Update user to verified
        self.user.email_verified = True
        self.user.phone_verified = True
        self.user.save()
        
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'تأیید شده')
    
    def test_avatar_section_present(self):
        """Test that avatar upload section is present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'avatar-upload')
        self.assertContains(response, 'avatar-preview')
        self.assertContains(response, 'avatar-input')
    
    def test_security_settings_section(self):
        """Test that security settings section is present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'احراز هویت دو مرحله‌ای')
        self.assertContains(response, 'آخرین ورود')
        self.assertContains(response, 'وضعیت حساب')
        self.assertContains(response, 'تلاش‌های ناموفق ورود')
    
    def test_sessions_management_section(self):
        """Test that sessions management section is present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'جلسات فعال')
        self.assertContains(response, 'خروج از همه دستگاه‌ها')
    
    def test_change_password_modal(self):
        """Test that change password modal is present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'changePasswordModal')
        self.assertContains(response, 'تغییر رمز عبور')
        self.assertContains(response, 'name="current_password"')
        self.assertContains(response, 'name="new_password"')
        self.assertContains(response, 'name="confirm_password"')
    
    def test_phone_verification_modal(self):
        """Test that phone verification modal is present"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'phoneVerificationModal')
        self.assertContains(response, 'تأیید شماره موبایل')
        self.assertContains(response, 'name="otp_code"')


class ProfileAPIEnhancementTestCase(APITestCase):
    """Test case for enhanced profile API functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            first_name='Test',
            last_name='User',
            phone='+989123456789'
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
    
    def test_profile_api_retrieval(self):
        """Test enhanced profile API retrieval"""
        response = self.client.get('/api/auth/profile/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        self.assertIn('user', data)
        self.assertIn('verification_status', data['user'])
        self.assertIn('security_info', data['user'])
        self.assertIn('settings', data['user'])
        self.assertIn('active_sessions_count', data['user'])
    
    def test_change_password_api(self):
        """Test change password API endpoint"""
        data = {
            'current_password': 'testpass123',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        
        response = self.client.post('/api/auth/change-password/', data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        self.assertIn('رمز عبور با موفقیت تغییر یافت', result['message'])
    
    def test_change_password_invalid_current(self):
        """Test change password with invalid current password"""
        data = {
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123'
        }
        
        response = self.client.post('/api/auth/change-password/', data)
        self.assertEqual(response.status_code, 400)
        
        result = response.json()
        self.assertFalse(result['success'])
        self.assertIn('رمز عبور فعلی اشتباه است', result['message'])
    
    def test_two_factor_toggle_api(self):
        """Test two-factor authentication toggle API"""
        data = {'enabled': True}
        
        response = self.client.post('/api/auth/two-factor/', data)
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        
        # Verify user was updated
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)
    
    def test_reset_failed_attempts_api(self):
        """Test reset failed attempts API"""
        # Set some failed attempts
        self.user.failed_login_attempts = 2
        self.user.save()
        
        response = self.client.post('/api/auth/reset-failed-attempts/')
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        
        # Verify attempts were reset
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 0)
    
    def test_download_personal_data_api(self):
        """Test download personal data API"""
        response = self.client.get('/api/auth/download-data/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json; charset=utf-8')
        self.assertIn('attachment', response['Content-Disposition'])
    
    def test_sessions_api(self):
        """Test user sessions API"""
        response = self.client.get('/api/auth/sessions/')
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        self.assertIn('sessions', result)
    
    def test_logout_all_devices_api(self):
        """Test logout all devices API"""
        response = self.client.post('/api/auth/logout-all/')
        self.assertEqual(response.status_code, 200)
        
        result = response.json()
        self.assertTrue(result['success'])
        self.assertIn('خروج از', result['message'])


class ProfileJavaScriptTestCase(TestCase):
    """Test case for profile JavaScript functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_profile_js_included(self):
        """Test that profile JavaScript file is included"""
        response = self.client.get(reverse('users:profile'))
        self.assertContains(response, 'static/js/profile.js')
    
    def test_required_js_functions_present(self):
        """Test that required JavaScript functions are present in the file"""
        with open('static/js/profile.js', 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # Check for main initialization functions
        self.assertIn('initializeProfile', js_content)
        self.assertIn('initializeSessions', js_content)
        self.assertIn('initializeSecuritySettings', js_content)
        
        # Check for profile update functions
        self.assertIn('handleProfileUpdate', js_content)
        self.assertIn('updateProfile', js_content)
        self.assertIn('handleAvatarUpload', js_content)
        
        # Check for session management functions
        self.assertIn('loadActiveSessions', js_content)
        self.assertIn('terminateSession', js_content)
        self.assertIn('logoutAllDevices', js_content)
        
        # Check for security functions
        self.assertIn('toggleTwoFactor', js_content)
        self.assertIn('resetFailedAttempts', js_content)
        self.assertIn('downloadPersonalData', js_content)
        
        # Check for verification functions
        self.assertIn('sendPhoneVerification', js_content)
        self.assertIn('verifyPhoneCode', js_content)
        self.assertIn('resendEmailVerification', js_content)
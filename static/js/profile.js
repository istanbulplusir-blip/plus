// Profile page JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize profile functionality
    initializeProfile();
    initializeSessions();
    initializeSecuritySettings();
});

// Global variables
let currentAction = null;
let pendingFormData = null;

// Initialize profile functionality
function initializeProfile() {
    // Profile form submission
    document.getElementById('profile-form').addEventListener('submit', handleProfileUpdate);
    
    // Avatar upload
    document.getElementById('avatar-input').addEventListener('change', handleAvatarUpload);
    
    // Change password button
    document.getElementById('change-password-btn').addEventListener('click', function() {
        const modal = new bootstrap.Modal(document.getElementById('changePasswordModal'));
        modal.show();
    });
    
    // Save password button
    document.getElementById('save-password-btn').addEventListener('click', handlePasswordChange);
    
    // Email verification resend
    const resendEmailBtn = document.getElementById('resend-email-verification');
    if (resendEmailBtn) {
        resendEmailBtn.addEventListener('click', function(e) {
            e.preventDefault();
            resendEmailVerification();
        });
    }
    
    // Phone verification
    const verifyPhoneBtn = document.getElementById('verify-phone');
    if (verifyPhoneBtn) {
        verifyPhoneBtn.addEventListener('click', function(e) {
            e.preventDefault();
            sendPhoneVerification();
        });
    }
    
    // Phone verification modal
    document.getElementById('verify-phone-btn').addEventListener('click', verifyPhoneCode);
    document.getElementById('resend-phone-otp').addEventListener('click', function(e) {
        e.preventDefault();
        sendPhoneVerification();
    });
    
    // Password confirmation modal
    document.getElementById('password-confirm-form').addEventListener('submit', handlePasswordConfirmation);
}

// Initialize sessions functionality
function initializeSessions() {
    // Load sessions when tab is shown
    document.getElementById('sessions-tab').addEventListener('shown.bs.tab', loadActiveSessions);
    
    // Logout all devices
    document.getElementById('logout-all-btn').addEventListener('click', logoutAllDevices);
}

// Initialize security settings
function initializeSecuritySettings() {
    // Two-factor authentication toggle
    document.getElementById('two_factor_enabled').addEventListener('change', toggleTwoFactor);
    
    // Reset failed attempts
    const resetBtn = document.getElementById('reset-failed-attempts');
    if (resetBtn) {
        resetBtn.addEventListener('click', resetFailedAttempts);
    }
    
    // Download data
    document.getElementById('download-data-btn').addEventListener('click', downloadPersonalData);
    
    // Delete account
    document.getElementById('delete-account-btn').addEventListener('click', deleteAccount);
}

// Handle profile update
async function handleProfileUpdate(e) {
    e.preventDefault();
    
    const formData = new FormData(e.target);
    const data = Object.fromEntries(formData.entries());
    
    // Check if sensitive fields are being changed
    const sensitiveFields = ['email', 'phone'];
    const currentEmail = document.getElementById('email').defaultValue;
    const currentPhone = document.getElementById('phone').defaultValue;
    
    let requiresPassword = false;
    if (data.email !== currentEmail || data.phone !== currentPhone) {
        requiresPassword = true;
    }
    
    if (requiresPassword) {
        // Show password confirmation modal
        currentAction = 'update_profile';
        pendingFormData = data;
        showPasswordModal();
        return;
    }
    
    // Proceed with update
    await updateProfile(data);
}

// Update profile
async function updateProfile(data, currentPassword = null) {
    try {
        showLoading('profile-form');
        
        const requestData = { ...data };
        if (currentPassword) {
            requestData.current_password = currentPassword;
        }
        
        const response = await fetch('/api/auth/profile/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'Authorization': `Bearer ${getAccessToken()}`
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'اطلاعات با موفقیت به‌روزرسانی شد.');
            
            // Update verification badges
            updateVerificationBadges(result.user);
            
            // Update avatar if changed
            if (result.user.avatar) {
                document.getElementById('avatar-preview').src = result.user.avatar;
            }
        } else {
            if (result.requires_password) {
                currentAction = 'update_profile';
                pendingFormData = data;
                showPasswordModal();
            } else {
                showAlert('danger', result.message || 'خطا در به‌روزرسانی اطلاعات');
            }
        }
    } catch (error) {
        console.error('Profile update error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    } finally {
        hideLoading('profile-form');
    }
}

// Handle avatar upload
function handleAvatarUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    // Validate file
    if (!file.type.startsWith('image/')) {
        showAlert('danger', 'لطفاً یک فایل تصویری انتخاب کنید.');
        return;
    }
    
    if (file.size > 5 * 1024 * 1024) {
        showAlert('danger', 'حجم فایل نباید بیشتر از 5 مگابایت باشد.');
        return;
    }
    
    // Preview image
    const reader = new FileReader();
    reader.onload = function(e) {
        document.getElementById('avatar-preview').src = e.target.result;
    };
    reader.readAsDataURL(file);
    
    // Upload avatar
    uploadAvatar(file);
}

// Upload avatar
async function uploadAvatar(file) {
    try {
        const formData = new FormData();
        formData.append('avatar', file);
        
        const response = await fetch('/api/auth/profile/', {
            method: 'PATCH',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'Authorization': `Bearer ${getAccessToken()}`
            },
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'تصویر پروفایل با موفقیت به‌روزرسانی شد.');
        } else {
            showAlert('danger', result.message || 'خطا در آپلود تصویر');
        }
    } catch (error) {
        console.error('Avatar upload error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Handle password change
async function handlePasswordChange() {
    const form = document.getElementById('change-password-form');
    const formData = new FormData(form);
    const data = Object.fromEntries(formData.entries());
    
    if (data.new_password !== data.confirm_password) {
        showAlert('danger', 'رمزهای عبور جدید مطابقت ندارند.');
        return;
    }
    
    if (data.new_password.length < 8) {
        showAlert('danger', 'رمز عبور باید حداقل 8 کاراکتر باشد.');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/change-password/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'Authorization': `Bearer ${getAccessToken()}`
            },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'رمز عبور با موفقیت تغییر یافت.');
            bootstrap.Modal.getInstance(document.getElementById('changePasswordModal')).hide();
            form.reset();
        } else {
            showAlert('danger', result.message || 'خطا در تغییر رمز عبور');
        }
    } catch (error) {
        console.error('Password change error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Load active sessions
async function loadActiveSessions() {
    try {
        const sessionsList = document.getElementById('sessions-list');
        sessionsList.innerHTML = '<div class="loading-spinner"><div class="spinner-border" role="status"></div></div>';
        
        const response = await fetch('/api/auth/sessions/', {
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            displaySessions(result.sessions);
        } else {
            sessionsList.innerHTML = '<p class="text-muted">خطا در بارگذاری جلسات</p>';
        }
    } catch (error) {
        console.error('Load sessions error:', error);
        document.getElementById('sessions-list').innerHTML = '<p class="text-muted">خطا در بارگذاری جلسات</p>';
    }
}

// Display sessions
function displaySessions(sessions) {
    const sessionsList = document.getElementById('sessions-list');
    
    if (!sessions || sessions.length === 0) {
        sessionsList.innerHTML = '<p class="text-muted">هیچ جلسه فعالی یافت نشد.</p>';
        return;
    }
    
    const sessionsHtml = sessions.map(session => `
        <div class="session-item ${session.is_current ? 'current-session' : ''}">
            <div class="d-flex justify-content-between align-items-start">
                <div>
                    <h6 class="mb-1">
                        ${session.user_agent_info.browser || 'مرورگر نامشخص'} 
                        ${session.user_agent_info.os || ''}
                        ${session.is_current ? '<span class="badge bg-success ms-2">جلسه فعلی</span>' : ''}
                    </h6>
                    <p class="mb-1 text-muted">
                        <i class="fas fa-map-marker-alt"></i> ${session.location || 'مکان نامشخص'}
                        <br>
                        <i class="fas fa-globe"></i> ${session.ip_address}
                    </p>
                    <small class="text-muted">
                        آخرین فعالیت: ${formatDate(session.last_activity)}
                        <br>
                        ایجاد شده: ${formatDate(session.created_at)}
                    </small>
                </div>
                ${!session.is_current ? `
                    <button class="btn btn-sm btn-outline-danger" onclick="terminateSession(${session.id})">
                        <i class="fas fa-times"></i> خروج
                    </button>
                ` : ''}
            </div>
        </div>
    `).join('');
    
    sessionsList.innerHTML = sessionsHtml;
}

// Terminate session
async function terminateSession(sessionId) {
    if (!confirm('آیا از خروج از این جلسه اطمینان دارید؟')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/auth/sessions/${sessionId}/`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'جلسه با موفقیت خاتمه یافت.');
            loadActiveSessions(); // Reload sessions
        } else {
            showAlert('danger', result.message || 'خطا در خاتمه جلسه');
        }
    } catch (error) {
        console.error('Terminate session error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Logout all devices
async function logoutAllDevices() {
    if (!confirm('آیا از خروج از همه دستگاه‌ها اطمینان دارید؟ پس از این عملیات باید مجدداً وارد شوید.')) {
        return;
    }
    
    try {
        const response = await fetch('/api/auth/logout-all/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'از همه دستگاه‌ها خارج شدید.');
            // Redirect to login after a delay
            setTimeout(() => {
                window.location.href = '/login/';
            }, 2000);
        } else {
            showAlert('danger', result.message || 'خطا در خروج از دستگاه‌ها');
        }
    } catch (error) {
        console.error('Logout all error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Toggle two-factor authentication
async function toggleTwoFactor(e) {
    const enabled = e.target.checked;
    
    try {
        const response = await fetch('/api/auth/two-factor/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ enabled })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', enabled ? 'احراز هویت دو مرحله‌ای فعال شد.' : 'احراز هویت دو مرحله‌ای غیرفعال شد.');
        } else {
            // Revert checkbox state
            e.target.checked = !enabled;
            showAlert('danger', result.message || 'خطا در تغییر تنظیمات');
        }
    } catch (error) {
        console.error('Two-factor toggle error:', error);
        e.target.checked = !enabled;
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Reset failed attempts
async function resetFailedAttempts() {
    try {
        const response = await fetch('/api/auth/reset-failed-attempts/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'تلاش‌های ناموفق بازنشانی شد.');
            location.reload(); // Reload to update display
        } else {
            showAlert('danger', result.message || 'خطا در بازنشانی');
        }
    } catch (error) {
        console.error('Reset failed attempts error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Download personal data
async function downloadPersonalData() {
    try {
        const response = await fetch('/api/auth/download-data/', {
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`
            }
        });
        
        if (response.ok) {
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'personal-data.json';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            
            showAlert('success', 'اطلاعات شخصی دانلود شد.');
        } else {
            showAlert('danger', 'خطا در دانلود اطلاعات');
        }
    } catch (error) {
        console.error('Download data error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Delete account
async function deleteAccount() {
    if (!confirm('آیا از حذف حساب کاربری خود اطمینان دارید؟ این عملیات غیرقابل بازگشت است.')) {
        return;
    }
    
    const password = prompt('برای تأیید حذف حساب، رمز عبور خود را وارد کنید:');
    if (!password) return;
    
    try {
        const response = await fetch('/api/auth/delete-account/', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ password })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'حساب کاربری حذف شد.');
            setTimeout(() => {
                // Use redirect URL from response or fallback to home
                const redirectUrl = result.redirect_url || '/';
                window.location.href = redirectUrl;
            }, 2000);
        } else {
            showAlert('danger', result.message || 'خطا در حذف حساب');
        }
    } catch (error) {
        console.error('Delete account error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Resend email verification
async function resendEmailVerification() {
    try {
        const response = await fetch('/api/auth/send-email-verification/', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'ایمیل تأیید مجدداً ارسال شد.');
        } else {
            showAlert('danger', result.message || 'خطا در ارسال ایمیل');
        }
    } catch (error) {
        console.error('Resend email error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Send phone verification
async function sendPhoneVerification() {
    const phone = document.getElementById('phone').value;
    if (!phone) {
        showAlert('danger', 'لطفاً شماره موبایل خود را وارد کنید.');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/send-phone-verification/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ phone })
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('phone-display').textContent = phone;
            const modal = new bootstrap.Modal(document.getElementById('phoneVerificationModal'));
            modal.show();
        } else {
            showAlert('danger', result.message || 'خطا در ارسال کد تأیید');
        }
    } catch (error) {
        console.error('Send phone verification error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Verify phone code
async function verifyPhoneCode() {
    const otpCode = document.getElementById('otp_code').value;
    const phone = document.getElementById('phone').value;
    
    if (!otpCode) {
        showAlert('danger', 'لطفاً کد تأیید را وارد کنید.');
        return;
    }
    
    try {
        const response = await fetch('/api/auth/verify-phone/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${getAccessToken()}`,
                'X-CSRFToken': getCsrfToken()
            },
            body: JSON.stringify({ phone, otp_code: otpCode })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showAlert('success', 'شماره موبایل با موفقیت تأیید شد.');
            bootstrap.Modal.getInstance(document.getElementById('phoneVerificationModal')).hide();
            
            // Update verification badge
            const phoneGroup = document.getElementById('phone').closest('.form-group');
            const badge = phoneGroup.querySelector('.verification-badge');
            badge.className = 'badge bg-success verification-badge';
            badge.textContent = 'تأیید شده';
            
            // Remove verification link
            const verifyLink = document.getElementById('verify-phone');
            if (verifyLink) {
                verifyLink.remove();
            }
        } else {
            showAlert('danger', result.message || 'کد تأیید نامعتبر است');
        }
    } catch (error) {
        console.error('Verify phone error:', error);
        showAlert('danger', 'خطای سیستمی رخ داده است.');
    }
}

// Password confirmation modal functions
function showPasswordModal() {
    document.getElementById('password-confirm-modal').style.display = 'block';
}

function closePasswordModal() {
    document.getElementById('password-confirm-modal').style.display = 'none';
    document.getElementById('current-password').value = '';
    currentAction = null;
    pendingFormData = null;
}

// Handle password confirmation
async function handlePasswordConfirmation(e) {
    e.preventDefault();
    
    const password = document.getElementById('current-password').value;
    if (!password) {
        showAlert('danger', 'لطفاً رمز عبور را وارد کنید.');
        return;
    }
    
    closePasswordModal();
    
    if (currentAction === 'update_profile' && pendingFormData) {
        await updateProfile(pendingFormData, password);
    }
}

// Update verification badges
function updateVerificationBadges(user) {
    // Update email badge
    const emailGroup = document.getElementById('email').closest('.form-group');
    const emailBadge = emailGroup.querySelector('.verification-badge');
    if (user.email_verified) {
        emailBadge.className = 'badge bg-success verification-badge';
        emailBadge.textContent = 'تأیید شده';
    } else {
        emailBadge.className = 'badge bg-warning verification-badge';
        emailBadge.textContent = 'تأیید نشده';
    }
    
    // Update phone badge
    const phoneGroup = document.getElementById('phone').closest('.form-group');
    const phoneBadge = phoneGroup.querySelector('.verification-badge');
    if (user.phone_verified) {
        phoneBadge.className = 'badge bg-success verification-badge';
        phoneBadge.textContent = 'تأیید شده';
    } else {
        phoneBadge.className = 'badge bg-warning verification-badge';
        phoneBadge.textContent = 'تأیید نشده';
    }
}

// Utility functions
function showAlert(type, message) {
    // Remove existing alerts
    const existingAlerts = document.querySelectorAll('.alert');
    existingAlerts.forEach(alert => alert.remove());
    
    // Create new alert
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at top of container
    const container = document.querySelector('.container');
    container.insertBefore(alertDiv, container.firstChild);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}

function showLoading(formId) {
    const form = document.getElementById(formId);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>در حال پردازش...';
    }
}

function hideLoading(formId) {
    const form = document.getElementById(formId);
    const submitBtn = form.querySelector('button[type="submit"]');
    if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.innerHTML = '<i class="fas fa-save"></i> ذخیره تغییرات';
    }
}

function getCsrfToken() {
    return document.querySelector('[name=csrfmiddlewaretoken]').value;
}

function getAccessToken() {
    return localStorage.getItem('access_token') || '';
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('fa-IR') + ' ' + date.toLocaleTimeString('fa-IR');
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modal = document.getElementById('password-confirm-modal');
    if (event.target === modal) {
        closePasswordModal();
    }
}
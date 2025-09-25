/**
 * Authentication JavaScript
 * Handles login, registration, and authentication-related interactions
 */

class AuthManager {
    constructor() {
        this.redirectUrl = null;
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.setupFormValidation();
        this.setupLoadingStates();
    }

    setRedirectUrl(url) {
        this.redirectUrl = url;
    }

    getCSRFToken() {
        const token = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                     document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') ||
                     document.cookie.split('; ').find(row => row.startsWith('csrftoken='))?.split('=')[1];
        return token || '';
    }

    setupEventListeners() {
        // Delivery method selection
        document.querySelectorAll('.auth-delivery-btn, .modern-delivery-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleDeliveryMethodChange(e));
            btn.addEventListener('keydown', (e) => this.handleDeliveryMethodKeydown(e));
        });

        // Form submissions
        document.querySelectorAll('form[id$="-form"]').forEach(form => {
            form.addEventListener('submit', (e) => this.handleFormSubmit(e));
        });

        // OTP send buttons
        document.querySelectorAll('.send-otp-btn').forEach(btn => {
            btn.addEventListener('click', (e) => this.handleSendOTP(e));
        });

        // Password strength checker
        document.querySelectorAll('input[name="password"]').forEach(input => {
            input.addEventListener('input', (e) => this.handlePasswordStrength(e));
        });

        // Password confirmation
        document.querySelectorAll('input[name="password_confirm"]').forEach(input => {
            input.addEventListener('input', (e) => this.handlePasswordConfirmation(e));
        });

        // Real-time validation
        document.querySelectorAll('.form-control').forEach(input => {
            input.addEventListener('blur', (e) => this.handleFieldValidation(e));
            input.addEventListener('input', (e) => this.handleFieldValidation(e));
        });
    }

    setupFormValidation() {
        // Add custom validation styles
        const style = document.createElement('style');
        style.textContent = `
            .form-control.is-valid {
                border-color: var(--success-color);
            }
            
            .form-control.is-invalid {
                border-color: var(--error-color);
            }
        `;
        document.head.appendChild(style);
    }

    setupLoadingStates() {
        this.createLoadingOverlay();
    }

    createLoadingOverlay() {
        const overlay = document.createElement('div');
        overlay.id = 'auth-loading-overlay';
        overlay.className = 'auth-loading-overlay';
        overlay.innerHTML = `
            <div class="auth-loading-content">
                <div class="auth-loading-spinner"></div>
                <div class="auth-loading-text">در حال پردازش...</div>
            </div>
        `;
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.8);
            backdrop-filter: blur(10px);
            display: none;
            align-items: center;
            justify-content: center;
            z-index: 9999;
        `;
        
        document.body.appendChild(overlay);
    }

    showLoading(message = 'در حال پردازش...') {
        const overlay = document.getElementById('auth-loading-overlay');
        const text = overlay.querySelector('.auth-loading-text');
        text.textContent = message;
        overlay.style.display = 'flex';
    }

    hideLoading() {
        const overlay = document.getElementById('auth-loading-overlay');
        overlay.style.display = 'none';
    }

    handleDeliveryMethodChange(e) {
        const btn = e.currentTarget;
        const group = btn.closest('.auth-delivery-group, .modern-delivery-group');
        
        // Remove active class from all buttons
        group.querySelectorAll('.auth-delivery-btn, .modern-delivery-btn').forEach(b => {
            b.classList.remove('active');
            b.setAttribute('aria-checked', 'false');
            b.setAttribute('tabindex', '-1');
        });
        
        // Add active class to clicked button
        btn.classList.add('active');
        btn.setAttribute('aria-checked', 'true');
        btn.setAttribute('tabindex', '0');
        btn.focus();
        
        // Update hidden input if exists
        const hiddenInput = document.querySelector('input[name="delivery_method"]');
        if (hiddenInput) {
            hiddenInput.value = btn.dataset.method;
        }
    }

    handleDeliveryMethodKeydown(e) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.handleDeliveryMethodChange(e);
        }
    }

    async handleSendOTP(e) {
        e.preventDefault();
        
        const btn = e.currentTarget;
        const form = btn.closest('form');
        const spinner = btn.querySelector('.auth-loading-spinner, .loading-spinner');
        const icon = btn.querySelector('i:not(.auth-loading-spinner):not(.loading-spinner)');
        const text = btn.querySelector('.btn-text');
        
        // Validate required fields
        const requiredFields = form.querySelectorAll('input[required]:not(#otp_code)');
        let isValid = true;
        
        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('is-invalid');
                isValid = false;
            } else {
                field.classList.remove('is-invalid');
                field.classList.add('is-valid');
            }
        });
        
        if (!isValid) {
            this.showNotification('لطفاً همه فیلدهای ضروری را تکمیل کنید', 'error');
            return;
        }
        
        // Show loading state
        btn.classList.add('auth-btn-loading', 'btn-loading');
        if (spinner) spinner.classList.remove('d-none');
        if (icon) icon.classList.add('d-none');
        if (text) text.textContent = 'در حال ارسال...';
        
        try {
            // Simulate OTP request
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // Show OTP field
            const otpField = form.querySelector('.auth-otp-field, .otp-field');
            if (otpField) {
                otpField.style.display = 'block';
                otpField.setAttribute('aria-hidden', 'false');
                otpField.querySelector('input').focus();
            }
            
            // Update progress if exists
            this.updateProgress(2);
            
            // Show success message
            this.showNotification('کد تأیید با موفقیت ارسال شد', 'success');
            
            // Update button text
            if (text) text.textContent = 'ارسال مجدد کد';
        } catch (error) {
            console.error('OTP send error:', error);
            this.showNotification('خطا در ارسال کد تأیید', 'error');
        } finally {
            // Reset button state
            btn.classList.remove('auth-btn-loading', 'btn-loading');
            if (spinner) spinner.classList.add('d-none');
            if (icon) icon.classList.remove('d-none');
        }
    }

    async handleFormSubmit(e) {
        e.preventDefault();
        
        const form = e.currentTarget;
        const submitBtn = form.querySelector('button[type="submit"]');
        const spinner = submitBtn?.querySelector('.auth-loading-spinner, .loading-spinner');
        const icon = submitBtn?.querySelector('i:not(.auth-loading-spinner):not(.loading-spinner)');
        const text = submitBtn?.querySelector('.btn-text');
        
        // Validate form
        if (!form.checkValidity()) {
            form.classList.add('was-validated');
            this.showNotification('لطفاً تمام فیلدها را به درستی پر کنید', 'error');
            return;
        }
        
        // Show loading state
        if (submitBtn) {
            submitBtn.classList.add('auth-btn-loading', 'btn-loading');
            if (spinner) spinner.classList.remove('d-none');
            if (icon) icon.classList.add('d-none');
            if (text) text.textContent = 'در حال پردازش...';
        }
        
        this.showLoading('در حال پردازش درخواست...');
        
        try {
            // Make actual API call instead of simulation
            const formData = new FormData(form);
            const formDataObj = {};
            for (let [key, value] of formData.entries()) {
                formDataObj[key] = value;
            }

                const response = await fetch(form.action || '/api/users/login/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCSRFToken()
                    },
                    body: JSON.stringify(formDataObj)
                });

                const result = await response.json();

            if (result.success) {
                // Show success state
                form.classList.add('auth-success-animation', 'form-success-animation');
                
                // Update progress if exists
                this.updateProgress(3);
                
                // Show success message
                this.showNotification('عملیات با موفقیت انجام شد', 'success');
                
                // Redirect after delay - use smart redirect
                    setTimeout(() => {
                        // Check if we have a redirect URL from the response
                        if (result && result.redirect_url && result.redirect_url !== '') {
                            window.location.href = result.redirect_url;
                        } else if (this.redirectUrl) {
                            window.location.href = this.redirectUrl;
                        } else {
                            // Fallback to profile for form submissions
                            window.location.href = '/users/profile/';
                        }
                    }, 2000);
            } else {
                // Show error message
                this.showNotification(result.message || 'خطا در انجام عملیات', 'error');
            }
        } catch (error) {
            console.error('Form submission error:', error);
            this.showNotification('خطا در پردازش درخواست', 'error');
        } finally {
            this.hideLoading();
            
            if (submitBtn) {
                submitBtn.classList.remove('auth-btn-loading', 'btn-loading');
                if (spinner) spinner.classList.add('d-none');
                if (icon) icon.classList.remove('d-none');
                if (text) text.textContent = text.dataset.originalText || 'ارسال';
            }
        }
    }

    handlePasswordStrength(e) {
        const input = e.target;
        const strengthBar = document.getElementById('password-strength-bar') || 
                           input.closest('.auth-form-group, .modern-form-group')?.querySelector('.auth-password-strength-bar, .modern-password-strength-bar');
        const strengthText = input.closest('.auth-form-group, .modern-form-group')?.querySelector('.auth-password-strength-text, .password-strength-text');
        
        if (!strengthBar || !strengthText) return;
        
        const password = input.value;
        let strength = 0;
        let feedback = 'ضعیف';
        let className = 'weak';
        
        // Length check
        if (password.length >= 8) strength++;
        if (password.length >= 12) strength++;
        
        // Character variety checks
        if (/[a-z]/.test(password)) strength++;
        if (/[A-Z]/.test(password)) strength++;
        if (/[0-9]/.test(password)) strength++;
        if (/[^A-Za-z0-9]/.test(password)) strength++;
        
        // Determine strength level
        if (strength <= 2) {
            feedback = 'ضعیف';
            className = 'weak';
        } else if (strength <= 4) {
            feedback = 'متوسط';
            className = 'fair';
        } else if (strength <= 5) {
            feedback = 'خوب';
            className = 'good';
        } else {
            feedback = 'قوی';
            className = 'strong';
        }
        
        strengthBar.className = `auth-password-strength-bar modern-password-strength-bar ${className}`;
        strengthText.textContent = `قدرت رمز عبور: ${feedback}`;
        strengthText.className = `auth-password-strength-text password-strength-text ${className}`;
    }

    handlePasswordConfirmation(e) {
        const input = e.target;
        const passwordInput = input.closest('form').querySelector('input[name="password"]');
        
        if (input.value && input.value !== passwordInput.value) {
            input.setCustomValidity('رمزهای عبور مطابقت ندارند');
            input.classList.add('is-invalid');
        } else {
            input.setCustomValidity('');
            input.classList.remove('is-invalid');
            if (input.value) input.classList.add('is-valid');
        }
    }

    handleFieldValidation(e) {
        const input = e.target;
        
        if (input.checkValidity()) {
            input.classList.remove('is-invalid');
            input.classList.add('is-valid');
        } else {
            input.classList.remove('is-valid');
        }
    }

    updateProgress(step) {
        const progressSteps = document.querySelectorAll('.auth-progress-step, .modern-progress-step');
        if (progressSteps.length === 0) return;
        
        progressSteps.forEach((stepEl, index) => {
            stepEl.classList.remove('active', 'completed');
            if (index + 1 < step) {
                stepEl.classList.add('completed');
            } else if (index + 1 === step) {
                stepEl.classList.add('active');
            }
        });
        
        // Update progress bar aria-valuenow
        const progressBar = document.querySelector('.auth-progress, .modern-form-progress');
        if (progressBar) {
            progressBar.setAttribute('aria-valuenow', step);
        }
    }

    showNotification(message, type = 'info') {
        // Use ModernAlerts if available, otherwise create a simple notification
        if (window.ModernAlerts) {
            window.ModernAlerts[type](message);
        } else {
            this.createSimpleNotification(message, type);
        }
    }

    createSimpleNotification(message, type) {
        const notification = document.createElement('div');
        notification.className = `auth-notification auth-notification-${type}`;
        notification.innerHTML = `
            <div class="auth-notification-content">
                <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
                <span>${message}</span>
            </div>
        `;
        
        // Add styles
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: ${type === 'success' ? 'var(--success-color)' : 'var(--error-color)'};
            color: white;
            padding: 15px 20px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            z-index: 1000;
            animation: slideInRight 0.3s ease-out;
            max-width: 400px;
        `;
        
        document.body.appendChild(notification);
        
        // Remove after 3 seconds
        setTimeout(() => {
            notification.style.animation = 'slideOutRight 0.3s ease-out';
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.authManager = new AuthManager();
});

// Add CSS for animations (only if not already added)
if (!document.getElementById('auth-animations-style')) {
    const style = document.createElement('style');
    style.id = 'auth-animations-style';
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
        
        .auth-notification-content {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .auth-notification-content i {
            font-size: 1.25rem;
        }
    `;
    document.head.appendChild(style);
}
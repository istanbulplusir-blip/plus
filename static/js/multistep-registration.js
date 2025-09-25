/**
 * Multi-Step Registration Manager
 * Handles the complete multi-step registration flow
 */

class MultiStepRegistration {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.contactInfo = null;
        this.contactType = null;
        this.accessToken = null;
        this.refreshToken = null;
        
        this.init();
    }

    init() {
        this.bindEvents();
        this.updateStepIndicator();
    }

    bindEvents() {
        // Step 1: Contact form
        document.getElementById('contact-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleContactSubmit();
        });

        // Step 2: OTP form
        document.getElementById('otp-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleOTPSubmit();
        });

        // OTP input handling
        this.setupOTPInputs();

        // Resend OTP button
        document.getElementById('resend-otp-btn').addEventListener('click', () => {
            this.resendOTP();
        });

        // Step 3: Personal info form
        document.getElementById('personal-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handlePersonalSubmit();
        });

        // Step 4: Password form
        document.getElementById('password-form').addEventListener('submit', (e) => {
            e.preventDefault();
            this.handlePasswordSubmit();
        });

        // Password confirmation validation
        document.getElementById('confirm_password').addEventListener('input', () => {
            this.validatePasswordConfirmation();
        });
    }

    setupOTPInputs() {
        const otpInputs = document.querySelectorAll('.otp-input');
        
        otpInputs.forEach((input, index) => {
            input.addEventListener('input', (e) => {
                const value = e.target.value;
                
                // Only allow numbers
                if (!/^\d$/.test(value)) {
                    e.target.value = '';
                    return;
                }
                
                // Move to next input
                if (value && index < otpInputs.length - 1) {
                    otpInputs[index + 1].focus();
                }
            });
            
            input.addEventListener('keydown', (e) => {
                // Handle backspace
                if (e.key === 'Backspace' && !e.target.value && index > 0) {
                    otpInputs[index - 1].focus();
                }
            });
            
            input.addEventListener('paste', (e) => {
                e.preventDefault();
                const pastedData = e.clipboardData.getData('text');
                const digits = pastedData.replace(/\D/g, '').slice(0, 6);
                
                digits.split('').forEach((digit, i) => {
                    if (otpInputs[i]) {
                        otpInputs[i].value = digit;
                    }
                });
                
                // Focus last filled input
                const lastFilledIndex = Math.min(digits.length - 1, otpInputs.length - 1);
                otpInputs[lastFilledIndex].focus();
            });
        });
    }

    async handleContactSubmit() {
        const form = document.getElementById('contact-form');
        const formData = new FormData(form);
        const contactInfo = formData.get('contact_info').trim();
        
        if (!contactInfo) {
            this.showAlert('لطفاً ایمیل یا شماره موبایل وارد کنید.', 'error');
            return;
        }

        this.setButtonLoading('send-otp-btn', true);

        try {
            const response = await fetch('/api/auth/register/step1/contact/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ contact_info: contactInfo })
            });

            const result = await response.json();

            if (result.success) {
                this.contactInfo = result.contact_info;
                this.contactType = result.contact_type;
                
                // Update contact display
                this.updateContactDisplay(result.masked_contact, result.contact_type);
                
                // Move to step 2
                this.nextStep();
                
                this.showAlert(result.message, 'success');
            } else {
                // Handle validation errors
                if (result.action === 'login_required') {
                    this.showAlert(result.message, 'warning');
                    // Show login link
                    setTimeout(() => {
                        window.location.href = result.login_url;
                    }, 2000);
                } else {
                    const errorMessage = this.extractErrorMessage(result);
                    this.showAlert(errorMessage, 'error');
                    // Reset current step after validation error
                    this.resetCurrentStep();
                }
            }
        } catch (error) {
            console.error('Contact submit error:', error);
            this.showAlert('خطای سیستمی رخ داده است.', 'error');
            this.resetCurrentStep();
        } finally {
            this.setButtonLoading('send-otp-btn', false);
        }
    }

    async handleOTPSubmit() {
        const otpCode = this.getOTPCode();
        
        if (otpCode.length !== 6) {
            this.showAlert('لطفاً کد 6 رقمی را کامل وارد کنید.', 'error');
            return;
        }

        this.setButtonLoading('verify-otp-btn', true);

        try {
            const response = await fetch('/api/auth/register/step1/verify/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({
                    contact_info: this.contactInfo,
                    otp_code: otpCode
                })
            });

            const result = await response.json();

            if (result.success) {
                // Store tokens
                this.accessToken = result.tokens.access;
                this.refreshToken = result.tokens.refresh;
                
                // Set authorization header for future requests
                this.setAuthHeader();
                
                // Move to step 3
                this.nextStep();
                
                this.showAlert(result.message, 'success');
            } else {
                // Handle validation errors
                const errorMessage = this.extractErrorMessage(result);
                this.showAlert(errorMessage, 'error');
                // Reset OTP step specifically
                this.resetOTPStep();
            }
        } catch (error) {
            console.error('OTP submit error:', error);
            this.showAlert('خطای سیستمی رخ داده است.', 'error');
            this.resetCurrentStep();
        } finally {
            this.setButtonLoading('verify-otp-btn', false);
        }
    }

    async handlePersonalSubmit() {
        const form = document.getElementById('personal-form');
        const formData = new FormData(form);
        const data = {
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name'),
            username: formData.get('username')
        };

        if (!data.username) {
            this.showAlert('نام کاربری الزامی است.', 'error');
            return;
        }

        this.setButtonLoading('save-personal-btn', true);

        try {
            const response = await fetch('/api/auth/register/step2/personal/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                    'Authorization': `Bearer ${this.accessToken}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                // Move to step 4
                this.nextStep();
                
                this.showAlert(result.message, 'success');
            } else {
                // Handle validation errors
                const errorMessage = this.extractErrorMessage(result);
                this.showAlert(errorMessage, 'error');
                // Reset current step after validation error
                this.resetCurrentStep();
            }
        } catch (error) {
            console.error('Personal submit error:', error);
            this.showAlert('خطای سیستمی رخ داده است.', 'error');
            this.resetCurrentStep();
        } finally {
            this.setButtonLoading('save-personal-btn', false);
        }
    }

    async handlePasswordSubmit() {
        const form = document.getElementById('password-form');
        const formData = new FormData(form);
        const data = {
            new_password: formData.get('new_password'),
            confirm_password: formData.get('confirm_password')
        };

        if (data.new_password !== data.confirm_password) {
            this.showAlert('رمزهای عبور مطابقت ندارند.', 'error');
            return;
        }

        if (data.new_password.length < 8) {
            this.showAlert('رمز عبور باید حداقل 8 کاراکتر باشد.', 'error');
            return;
        }

        this.setButtonLoading('save-password-btn', true);

        try {
            const response = await fetch('/api/auth/register/step3/password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken(),
                    'Authorization': `Bearer ${this.accessToken}`
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                // Store new tokens after password change
                if (result.tokens) {
                    this.accessToken = result.tokens.access;
                    this.refreshToken = result.tokens.refresh;
                    this.setAuthHeader();
                }
                
                // Show success state
                this.showSuccess();
                
                this.showAlert(result.message, 'success');
                
                // Redirect after delay with auto-login
                setTimeout(() => {
                    // Use redirect URL from result, context, or fallback to home
                    const redirectUrl = result.redirect_url || window.nextUrl || '/';
                    this.redirectWithAutoLogin(redirectUrl, result.auto_login);
                }, 3000);
            } else {
                // Handle validation errors
                const errorMessage = this.extractErrorMessage(result);
                this.showAlert(errorMessage, 'error');
                // Reset current step after validation error
                this.resetCurrentStep();
            }
        } catch (error) {
            console.error('Password submit error:', error);
            this.showAlert('خطای سیستمی رخ داده است.', 'error');
            this.resetCurrentStep();
        } finally {
            this.setButtonLoading('save-password-btn', false);
        }
    }

    async resendOTP() {
        this.setButtonLoading('resend-otp-btn', true);

        try {
            const response = await fetch('/api/auth/register/step1/contact/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCsrfToken()
                },
                body: JSON.stringify({ contact_info: this.contactInfo })
            });

            const result = await response.json();

            if (result.success) {
                this.showAlert('کد تأیید مجدداً ارسال شد.', 'success');
                this.clearOTPInputs();
            } else {
                this.showAlert(result.message, 'error');
                // Reset current step after validation error
                this.resetCurrentStep();
            }
        } catch (error) {
            console.error('Resend OTP error:', error);
            this.showAlert('خطای سیستمی رخ داده است.', 'error');
            this.resetCurrentStep();
        } finally {
            this.setButtonLoading('resend-otp-btn', false);
        }
    }

    nextStep() {
        if (this.currentStep < this.totalSteps) {
            this.currentStep++;
            this.updateStepIndicator();
            this.showStep(this.currentStep);
        }
    }

    showStep(stepNumber) {
        // Hide all steps
        document.querySelectorAll('.step-content').forEach(step => {
            step.classList.remove('active');
        });

        // Show current step
        const currentStepElement = document.getElementById(`step-${stepNumber}`);
        if (currentStepElement) {
            currentStepElement.classList.add('active');
        }

        // Focus first input in the step
        setTimeout(() => {
            const firstInput = currentStepElement?.querySelector('input, textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 300);
    }

    updateStepIndicator() {
        const steps = document.querySelectorAll('.step');
        const progressBar = document.querySelector('.step-indicator');
        
        steps.forEach((step, index) => {
            const stepNumber = index + 1;
            step.classList.remove('active', 'completed');
            
            if (stepNumber < this.currentStep) {
                step.classList.add('completed');
            } else if (stepNumber === this.currentStep) {
                step.classList.add('active');
            }
        });

        // Update progress bar aria-valuenow
        if (progressBar) {
            progressBar.setAttribute('aria-valuenow', this.currentStep);
        }
    }

    updateContactDisplay(maskedContact, contactType) {
        const indicator = document.getElementById('contact-indicator');
        const display = document.getElementById('contact-display');
        const icon = indicator.querySelector('i');
        
        if (contactType === 'email') {
            icon.className = 'bi bi-envelope';
            display.textContent = `کد تأیید به ${maskedContact} ارسال شد`;
        } else {
            icon.className = 'bi bi-phone';
            display.textContent = `کد تأیید به ${maskedContact} ارسال شد`;
        }
    }

    showSuccess() {
        this.currentStep = 'success';
        this.updateStepIndicator();
        
        // Hide all steps
        document.querySelectorAll('.step-content').forEach(step => {
            step.classList.remove('active');
        });

        // Show success step
        document.getElementById('step-success').classList.add('active');
        
        // Update success message with auto-login info
        const successMessage = document.querySelector('#step-success h4');
        if (successMessage) {
            successMessage.innerHTML = 'ثبت‌نام با موفقیت تکمیل شد!<br><small class="text-muted">شما خودکار وارد شدید</small>';
        }
    }

    getOTPCode() {
        const otpInputs = document.querySelectorAll('.otp-input');
        return Array.from(otpInputs).map(input => input.value).join('');
    }

    clearOTPInputs() {
        console.log('🔄 Clearing OTP inputs...');
        const otpInputs = document.querySelectorAll('.otp-input');
        console.log(`Found ${otpInputs.length} OTP inputs`);
        
        otpInputs.forEach((input, index) => {
            console.log(`Clearing OTP input ${index + 1}: ${input.value} -> ''`);
            input.value = '';
            // Also clear any validation states
            input.classList.remove('is-invalid', 'is-valid');
            input.setCustomValidity('');
            input.disabled = false;
            input.style.pointerEvents = 'auto';
            input.style.opacity = '1';
            input.style.cursor = 'text';
        });
        
        if (otpInputs[0]) {
            otpInputs[0].focus();
            console.log('✅ Focused first OTP input');
        }
        console.log('✅ OTP inputs cleared');
    }

    validatePasswordConfirmation() {
        const password = document.getElementById('new_password').value;
        const confirmPassword = document.getElementById('confirm_password').value;
        const confirmInput = document.getElementById('confirm_password');
        
        if (confirmPassword && password !== confirmPassword) {
            confirmInput.setCustomValidity('رمزهای عبور مطابقت ندارند');
            confirmInput.classList.add('is-invalid');
        } else {
            confirmInput.setCustomValidity('');
            confirmInput.classList.remove('is-invalid');
            if (confirmPassword) {
                confirmInput.classList.add('is-valid');
            }
        }
    }

    setButtonLoading(buttonId, isLoading) {
        const button = document.getElementById(buttonId);
        if (!button) return; // Safety check
        
        const spinner = button.querySelector('.loading-spinner');
        const icon = button.querySelector('i:not(.loading-spinner)');
        const text = button.querySelector('.btn-text');
        
        if (isLoading) {
            button.classList.add('btn-loading');
            button.disabled = true; // Explicitly disable button
            if (spinner) spinner.classList.remove('d-none');
            if (icon) icon.classList.add('d-none');
            if (text) text.textContent = 'در حال پردازش...';
        } else {
            button.classList.remove('btn-loading');
            button.disabled = false; // Explicitly enable button
            if (spinner) spinner.classList.add('d-none');
            if (icon) icon.classList.remove('d-none');
            if (text) {
                // Restore original text
                const originalTexts = {
                    'send-otp-btn': 'ارسال کد تأیید',
                    'verify-otp-btn': 'تأیید کد',
                    'resend-otp-btn': 'ارسال مجدد',
                    'save-personal-btn': 'ادامه',
                    'save-password-btn': 'تکمیل ثبت‌نام'
                };
                text.textContent = originalTexts[buttonId] || 'ارسال';
            }
        }
    }

    showAlert(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container');
        const alertClass = {
            'success': 'alert-success',
            'error': 'alert-danger',
            'warning': 'alert-warning',
            'info': 'alert-info'
        }[type] || 'alert-info';

        const iconClass = {
            'success': 'bi-check-circle',
            'error': 'bi-exclamation-triangle',
            'warning': 'bi-exclamation-triangle',
            'info': 'bi-info-circle'
        }[type] || 'bi-info-circle';

        alertContainer.innerHTML = `
            <div class="alert ${alertClass} alert-dismissible fade show" role="alert">
                <i class="bi ${iconClass} me-2" aria-hidden="true"></i>
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="بستن"></button>
            </div>
        `;

        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            const alert = alertContainer.querySelector('.alert');
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, 5000);
    }

    extractErrorMessage(result) {
        // Handle validation errors from Django REST Framework
        if (result.contact_info && Array.isArray(result.contact_info)) {
            let errorMessage = result.contact_info[0];
            
            // Handle nested array format: ["['error message']"]
            if (typeof errorMessage === 'string' && errorMessage.startsWith("['") && errorMessage.endsWith("']")) {
                // Extract the actual error message from the nested format
                errorMessage = errorMessage.slice(2, -2); // Remove [' and ']
            }
            
            return errorMessage;
        }
        
        // Handle other field errors
        const fieldErrors = ['username', 'first_name', 'last_name', 'new_password', 'confirm_password', 'otp_code'];
        for (const field of fieldErrors) {
            if (result[field] && Array.isArray(result[field])) {
                let errorMessage = result[field][0];
                
                // Handle nested array format
                if (typeof errorMessage === 'string' && errorMessage.startsWith("['") && errorMessage.endsWith("']")) {
                    errorMessage = errorMessage.slice(2, -2);
                }
                
                return errorMessage;
            }
        }
        
        // Return general message if no specific field error found
        return result.message || 'خطای نامشخص رخ داده است.';
    }

    getCsrfToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]').value;
    }

    setAuthHeader() {
        // Store tokens in localStorage for future use
        if (this.accessToken) {
            localStorage.setItem('access_token', this.accessToken);
        }
        if (this.refreshToken) {
            localStorage.setItem('refresh_token', this.refreshToken);
        }
        
        // Also set in sessionStorage for immediate use
        if (this.accessToken) {
            sessionStorage.setItem('access_token', this.accessToken);
        }
        if (this.refreshToken) {
            sessionStorage.setItem('refresh_token', this.refreshToken);
        }
        
        // Set authorization header for future requests
        if (this.accessToken) {
            // This will be used by fetch requests
            this.authHeader = `Bearer ${this.accessToken}`;
        }
    }

    redirectWithAutoLogin(url, autoLogin = true) {
        if (autoLogin && this.accessToken) {
            // User is already logged in with new tokens
            console.log('🔄 Auto-login successful, redirecting to:', url);
            window.location.href = url;
        } else {
            // Fallback redirect
            console.log('🔄 Redirecting to:', url);
            window.location.href = url;
        }
    }

    resetFormState() {
        console.log('🔄 Resetting form state...');
        
        // Reset all buttons to normal state
        const buttonIds = ['send-otp-btn', 'verify-otp-btn', 'resend-otp-btn', 'save-personal-btn', 'save-password-btn'];
        buttonIds.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                console.log(`🔄 Resetting button: ${buttonId}`);
                // Force reset button state
                button.classList.remove('btn-loading');
                button.disabled = false;
                button.style.pointerEvents = 'auto';
                button.style.opacity = '1';
                button.style.cursor = 'pointer';
                
                // Reset button content
                const spinner = button.querySelector('.loading-spinner');
                const icon = button.querySelector('i:not(.loading-spinner)');
                const text = button.querySelector('.btn-text');
                
                if (spinner) spinner.classList.add('d-none');
                if (icon) icon.classList.remove('d-none');
                if (text) {
                    const originalTexts = {
                        'send-otp-btn': 'ارسال کد تأیید',
                        'verify-otp-btn': 'تأیید کد',
                        'resend-otp-btn': 'ارسال مجدد',
                        'save-personal-btn': 'ادامه',
                        'save-password-btn': 'تکمیل ثبت‌نام'
                    };
                    text.textContent = originalTexts[buttonId] || 'ارسال';
                }
            }
        });
        
        // Clear input values and validation states
        document.querySelectorAll('.form-control').forEach(input => {
            // Clear input value
            input.value = '';
            // Remove validation classes
            input.classList.remove('is-invalid', 'is-valid');
            // Clear custom validity
            input.setCustomValidity('');
            // Reset input state
            input.disabled = false;
            input.style.pointerEvents = 'auto';
            input.style.opacity = '1';
            input.style.cursor = 'text';
        });
        
        // Clear OTP inputs specifically
        this.clearOTPInputs();
        
        // Clear any error states
        document.querySelectorAll('.alert').forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
        
        // Remove any form-submitting classes
        document.querySelectorAll('.form-submitting').forEach(form => {
            form.classList.remove('form-submitting');
        });
        
        console.log('✅ Form state reset completed');
    }

    resetCurrentStep() {
        console.log(`🔄 Resetting current step: ${this.currentStep}`);
        
        // Get current step element
        const currentStepElement = document.getElementById(`step-${this.currentStep}`);
        if (!currentStepElement) return;
        
        // Clear inputs in current step (but don't clear contact_info in step 1)
        const inputs = currentStepElement.querySelectorAll('.form-control');
        console.log(`Found ${inputs.length} inputs in step ${this.currentStep}`);
        
        inputs.forEach((input, index) => {
            console.log(`Processing input ${index + 1}: ${input.id || input.name || 'unnamed'}`);
            
            // Don't clear contact_info in step 1 to preserve user input
            if (this.currentStep === 1 && input.id === 'contact_info') {
                // Only clear validation states, keep the value
                console.log('Preserving contact_info value, clearing validation states');
                input.classList.remove('is-invalid', 'is-valid');
                input.setCustomValidity('');
            } else {
                // Clear everything for other inputs
                console.log(`Clearing input: ${input.value} -> ''`);
                input.value = '';
                input.classList.remove('is-invalid', 'is-valid');
                input.setCustomValidity('');
            }
            
            // Always reset input state
            input.disabled = false;
            input.style.pointerEvents = 'auto';
            input.style.opacity = '1';
            input.style.cursor = 'text';
        });
        
        // Reset button in current step
        const buttonIds = {
            1: 'send-otp-btn',
            2: 'verify-otp-btn',
            3: 'save-personal-btn',
            4: 'save-password-btn'
        };
        
        const buttonId = buttonIds[this.currentStep];
        if (buttonId) {
            const button = document.getElementById(buttonId);
            if (button) {
                button.classList.remove('btn-loading');
                button.disabled = false;
                button.style.pointerEvents = 'auto';
                button.style.opacity = '1';
                button.style.cursor = 'pointer';
                
                const spinner = button.querySelector('.loading-spinner');
                const icon = button.querySelector('i:not(.loading-spinner)');
                const text = button.querySelector('.btn-text');
                
                if (spinner) spinner.classList.add('d-none');
                if (icon) icon.classList.remove('d-none');
                if (text) {
                    const originalTexts = {
                        'send-otp-btn': 'ارسال کد تأیید',
                        'verify-otp-btn': 'تأیید کد',
                        'save-personal-btn': 'ادامه',
                        'save-password-btn': 'تکمیل ثبت‌نام'
                    };
                    text.textContent = originalTexts[buttonId] || 'ارسال';
                }
            }
        }
        
        // Clear alerts in current step
        const alerts = currentStepElement.querySelectorAll('.alert');
        alerts.forEach(alert => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
        
        // Focus first input in current step
        setTimeout(() => {
            const firstInput = currentStepElement.querySelector('input:not([type="hidden"]), textarea, select');
            if (firstInput) {
                firstInput.focus();
            }
        }, 100);
        
        console.log(`✅ Step ${this.currentStep} reset completed`);
    }

    resetOTPStep() {
        console.log('🔄 Resetting OTP step specifically');
        
        // Clear OTP inputs
        this.clearOTPInputs();
        
        // Reset OTP button
        const verifyButton = document.getElementById('verify-otp-btn');
        if (verifyButton) {
            console.log('🔄 Resetting verify button...');
            verifyButton.classList.remove('btn-loading');
            verifyButton.disabled = false;
            verifyButton.style.pointerEvents = 'auto';
            verifyButton.style.opacity = '1';
            verifyButton.style.cursor = 'pointer';
            
            const spinner = verifyButton.querySelector('.loading-spinner');
            const icon = verifyButton.querySelector('i:not(.loading-spinner)');
            const text = verifyButton.querySelector('.btn-text');
            
            if (spinner) {
                spinner.classList.add('d-none');
                console.log('✅ Spinner hidden');
            }
            if (icon) {
                icon.classList.remove('d-none');
                console.log('✅ Icon shown');
            }
            if (text) {
                text.textContent = 'تأیید کد';
                console.log('✅ Button text reset');
            }
        } else {
            console.log('❌ Verify button not found');
        }
        
        // Clear alerts in OTP step
        const otpStep = document.getElementById('step-2');
        if (otpStep) {
            const alerts = otpStep.querySelectorAll('.alert');
            console.log(`Found ${alerts.length} alerts in OTP step`);
            alerts.forEach(alert => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            });
        } else {
            console.log('❌ OTP step not found');
        }
        
        // Focus first OTP input
        setTimeout(() => {
            const firstOTPInput = document.querySelector('.otp-input');
            if (firstOTPInput) {
                firstOTPInput.focus();
                console.log('✅ Focused first OTP input');
            } else {
                console.log('❌ No OTP input found to focus');
            }
        }, 100);
        
        console.log('✅ OTP step reset completed');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const registration = new MultiStepRegistration();
    
    // Add global debug function for testing
    window.debugRegistration = function() {
        console.log('🔍 Registration Debug Info:');
        console.log('Current Step:', registration.currentStep);
        console.log('Contact Info:', registration.contactInfo);
        console.log('Access Token:', registration.accessToken ? 'Present' : 'None');
        
        // Check button states
        const buttonIds = ['send-otp-btn', 'verify-otp-btn', 'resend-otp-btn', 'save-personal-btn', 'save-password-btn'];
        buttonIds.forEach(buttonId => {
            const button = document.getElementById(buttonId);
            if (button) {
                console.log(`${buttonId}:`, {
                    disabled: button.disabled,
                    hasLoadingClass: button.classList.contains('btn-loading'),
                    pointerEvents: button.style.pointerEvents,
                    opacity: button.style.opacity
                });
            }
        });
    };
    
    // Add global reset function for testing
    window.resetRegistrationForm = function() {
        console.log('🔄 Manual form reset triggered');
        registration.resetFormState();
    };
    
    // Add global reset current step function for testing
    window.resetCurrentStep = function() {
        console.log('🔄 Manual current step reset triggered');
        registration.resetCurrentStep();
    };
    
    // Add global reset OTP step function for testing
    window.resetOTPStep = function() {
        console.log('🔄 Manual OTP step reset triggered');
        registration.resetOTPStep();
    };
    
    // Add global function to debug OTP inputs
    window.debugOTPInputs = function() {
        console.log('🔍 Debugging OTP inputs...');
        const otpInputs = document.querySelectorAll('.otp-input');
        console.log(`Found ${otpInputs.length} OTP inputs`);
        
        otpInputs.forEach((input, index) => {
            console.log(`OTP Input ${index + 1}:`, {
                value: input.value,
                disabled: input.disabled,
                style: {
                    pointerEvents: input.style.pointerEvents,
                    opacity: input.style.opacity,
                    cursor: input.style.cursor
                },
                classes: Array.from(input.classList),
                validity: input.validity
            });
        });
        
        const verifyButton = document.getElementById('verify-otp-btn');
        if (verifyButton) {
            console.log('Verify Button:', {
                disabled: verifyButton.disabled,
                classes: Array.from(verifyButton.classList),
                style: {
                    pointerEvents: verifyButton.style.pointerEvents,
                    opacity: verifyButton.style.opacity,
                    cursor: verifyButton.style.cursor
                }
            });
        } else {
            console.log('❌ Verify button not found');
        }
    };
    
    // Add global function to force clear OTP inputs
    window.forceClearOTP = function() {
        console.log('🔄 Force clearing OTP inputs...');
        const otpInputs = document.querySelectorAll('.otp-input');
        console.log(`Found ${otpInputs.length} OTP inputs`);
        
        otpInputs.forEach((input, index) => {
            console.log(`Force clearing OTP input ${index + 1}`);
            input.value = '';
            input.disabled = false;
            input.style.pointerEvents = 'auto';
            input.style.opacity = '1';
            input.style.cursor = 'text';
            input.classList.remove('is-invalid', 'is-valid');
            input.setCustomValidity('');
            input.removeAttribute('readonly');
        });
        
        if (otpInputs[0]) {
            otpInputs[0].focus();
            console.log('✅ Focused first OTP input');
        }
        
        console.log('✅ OTP inputs force cleared');
    };
});

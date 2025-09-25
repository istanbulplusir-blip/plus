/**
 * Modern Form Enhancements
 * Provides enhanced form interactions, validation, and user experience
 */

class FormEnhancer {
  constructor() {
    this.init();
  }

  init() {
    this.setupFloatingLabels();
    this.setupPasswordStrength();
    this.setupOTPInputs();
    this.setupDeliveryMethodButtons();
    this.setupFormValidation();
    this.setupAccessibility();
  }

  /**
   * Enhanced floating label behavior
   */
  setupFloatingLabels() {
    const floatingInputs = document.querySelectorAll('.form-floating input, .form-floating select, .form-floating textarea');
    
    floatingInputs.forEach(input => {
      // Handle initial state
      this.updateFloatingLabel(input);
      
      // Handle focus/blur events
      input.addEventListener('focus', () => {
        input.parentElement.classList.add('focused');
      });
      
      input.addEventListener('blur', () => {
        input.parentElement.classList.remove('focused');
        this.updateFloatingLabel(input);
      });
      
      // Handle input events
      input.addEventListener('input', () => {
        this.updateFloatingLabel(input);
      });
    });
  }

  updateFloatingLabel(input) {
    const hasValue = input.value.trim() !== '';
    const container = input.parentElement;
    
    if (hasValue) {
      container.classList.add('has-value');
    } else {
      container.classList.remove('has-value');
    }
  }

  /**
   * Password strength indicator
   */
  setupPasswordStrength() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    
    passwordInputs.forEach(input => {
      const strengthContainer = input.parentElement.querySelector('.password-strength');
      if (!strengthContainer) return;
      
      const strengthBar = strengthContainer.querySelector('.password-strength-bar');
      
      input.addEventListener('input', () => {
        const strength = this.calculatePasswordStrength(input.value);
        this.updatePasswordStrengthUI(strengthBar, strength);
      });
    });
  }

  calculatePasswordStrength(password) {
    let score = 0;
    let feedback = [];

    // Length check
    if (password.length >= 8) score += 1;
    else feedback.push('حداقل 8 کاراکتر');

    // Lowercase check
    if (/[a-z]/.test(password)) score += 1;
    else feedback.push('حروف کوچک');

    // Uppercase check
    if (/[A-Z]/.test(password)) score += 1;
    else feedback.push('حروف بزرگ');

    // Number check
    if (/\d/.test(password)) score += 1;
    else feedback.push('اعداد');

    // Special character check
    if (/[!@#$%^&*(),.?":{}|<>]/.test(password)) score += 1;
    else feedback.push('کاراکترهای خاص');

    return {
      score,
      feedback,
      level: this.getStrengthLevel(score)
    };
  }

  getStrengthLevel(score) {
    if (score <= 1) return 'weak';
    if (score <= 2) return 'fair';
    if (score <= 3) return 'good';
    return 'strong';
  }

  updatePasswordStrengthUI(strengthBar, strength) {
    // Remove existing classes
    strengthBar.classList.remove('weak', 'fair', 'good', 'strong');
    
    // Add new class
    strengthBar.classList.add(strength.level);
    
    // Update width based on score
    const widthPercentage = (strength.score / 5) * 100;
    strengthBar.style.width = `${widthPercentage}%`;
  }

  /**
   * Enhanced OTP input behavior
   */
  setupOTPInputs() {
    const otpInputs = document.querySelectorAll('.otp-input');
    
    otpInputs.forEach(input => {
      // Only allow numeric input
      input.addEventListener('input', (e) => {
        e.target.value = e.target.value.replace(/[^0-9]/g, '');
        
        // Auto-submit when 6 digits are entered
        if (e.target.value.length === 6) {
          const form = e.target.closest('form');
          if (form) {
            // Add a small delay for better UX
            setTimeout(() => {
              const submitBtn = form.querySelector('button[type="submit"]');
              if (submitBtn && !submitBtn.disabled) {
                submitBtn.focus();
              }
            }, 300);
          }
        }
      });

      // Handle paste events
      input.addEventListener('paste', (e) => {
        e.preventDefault();
        const paste = (e.clipboardData || window.clipboardData).getData('text');
        const numericPaste = paste.replace(/[^0-9]/g, '').substring(0, 6);
        e.target.value = numericPaste;
        
        // Trigger input event
        e.target.dispatchEvent(new Event('input', { bubbles: true }));
      });

      // Enhanced focus behavior
      input.addEventListener('focus', () => {
        input.select();
      });
    });
  }

  /**
   * Delivery method button functionality
   */
  setupDeliveryMethodButtons() {
    const deliveryGroups = document.querySelectorAll('.delivery-method-group');
    
    deliveryGroups.forEach(group => {
      const buttons = group.querySelectorAll('.delivery-method-btn');
      
      buttons.forEach(button => {
        button.addEventListener('click', () => {
          // Remove active class from all buttons in this group
          buttons.forEach(btn => btn.classList.remove('active'));
          
          // Add active class to clicked button
          button.classList.add('active');
          
          // Store selected method
          const method = button.dataset.method;
          const hiddenInput = group.parentElement.querySelector('input[name="delivery_method"]');
          if (hiddenInput) {
            hiddenInput.value = method;
          }
          
          // Dispatch custom event
          button.dispatchEvent(new CustomEvent('deliveryMethodChanged', {
            detail: { method },
            bubbles: true
          }));
        });
      });
    });
  }

  /**
   * Enhanced form validation
   */
  setupFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
      const inputs = form.querySelectorAll('input, select, textarea');
      
      inputs.forEach(input => {
        // Real-time validation
        input.addEventListener('blur', () => {
          this.validateField(input);
        });
        
        input.addEventListener('input', () => {
          // Clear validation state on input
          if (input.classList.contains('is-invalid')) {
            input.classList.remove('is-invalid');
            this.clearFieldError(input);
          }
        });
      });
      
      // Form submission validation
      form.addEventListener('submit', (e) => {
        if (!this.validateForm(form)) {
          e.preventDefault();
          e.stopPropagation();
        }
      });
    });
  }

  validateField(field) {
    const isValid = field.checkValidity();
    
    if (isValid) {
      field.classList.remove('is-invalid');
      field.classList.add('is-valid');
      this.clearFieldError(field);
    } else {
      field.classList.remove('is-valid');
      field.classList.add('is-invalid');
      this.showFieldError(field, field.validationMessage);
    }
    
    return isValid;
  }

  validateForm(form) {
    const fields = form.querySelectorAll('input, select, textarea');
    let isValid = true;
    
    fields.forEach(field => {
      if (!this.validateField(field)) {
        isValid = false;
      }
    });
    
    return isValid;
  }

  showFieldError(field, message) {
    let errorElement = field.parentElement.querySelector('.invalid-feedback');
    
    if (!errorElement) {
      errorElement = document.createElement('div');
      errorElement.className = 'invalid-feedback';
      field.parentElement.appendChild(errorElement);
    }
    
    errorElement.textContent = message;
    errorElement.style.display = 'block';
  }

  clearFieldError(field) {
    const errorElement = field.parentElement.querySelector('.invalid-feedback');
    if (errorElement) {
      errorElement.style.display = 'none';
    }
  }

  /**
   * Accessibility enhancements
   */
  setupAccessibility() {
    // Enhanced keyboard navigation
    const focusableElements = document.querySelectorAll(
      'input, select, textarea, button, [tabindex]:not([tabindex="-1"])'
    );
    
    focusableElements.forEach(element => {
      element.addEventListener('keydown', (e) => {
        // Enhanced Enter key behavior
        if (e.key === 'Enter' && element.tagName !== 'TEXTAREA') {
          if (element.type === 'submit' || element.tagName === 'BUTTON') {
            return; // Let default behavior handle it
          }
          
          // Move to next focusable element or submit form
          const form = element.closest('form');
          if (form) {
            const formElements = Array.from(form.querySelectorAll(
              'input, select, textarea, button'
            ));
            const currentIndex = formElements.indexOf(element);
            const nextElement = formElements[currentIndex + 1];
            
            if (nextElement) {
              nextElement.focus();
            } else {
              const submitBtn = form.querySelector('button[type="submit"]');
              if (submitBtn) {
                submitBtn.click();
              }
            }
          }
        }
      });
    });

    // ARIA enhancements
    this.enhanceARIA();
  }

  enhanceARIA() {
    // Add ARIA labels to form controls without labels
    const inputs = document.querySelectorAll('input, select, textarea');
    
    inputs.forEach(input => {
      if (!input.getAttribute('aria-label') && !input.getAttribute('aria-labelledby')) {
        const label = input.parentElement.querySelector('label');
        if (label) {
          const labelId = label.id || `label-${Math.random().toString(36).substr(2, 9)}`;
          label.id = labelId;
          input.setAttribute('aria-labelledby', labelId);
        }
      }
    });

    // Add ARIA live regions for dynamic content
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
      alertContainer.setAttribute('aria-live', 'polite');
      alertContainer.setAttribute('aria-atomic', 'true');
    }
  }

  /**
   * Utility methods
   */
  static debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout);
        func(...args);
      };
      clearTimeout(timeout);
      timeout = setTimeout(later, wait);
    };
  }

  static throttle(func, limit) {
    let inThrottle;
    return function() {
      const args = arguments;
      const context = this;
      if (!inThrottle) {
        func.apply(context, args);
        inThrottle = true;
        setTimeout(() => inThrottle = false, limit);
      }
    };
  }
}

// Auto-initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.formEnhancer = new FormEnhancer();
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
  module.exports = FormEnhancer;
}
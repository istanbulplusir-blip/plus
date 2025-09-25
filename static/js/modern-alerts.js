/**
 * Modern Alerts & States Manager - 2025
 * Comprehensive alert system with glassmorphism effects and animations
 */

class ModernAlerts {
  constructor() {
    this.container = this.createContainer();
    this.toastContainer = this.createToastContainer();
    this.alerts = new Map();
    this.init();
  }

  init() {
    // Append containers to body
    document.body.appendChild(this.container);
    document.body.appendChild(this.toastContainer);
    
    // Handle keyboard navigation
    this.setupKeyboardHandlers();
    
    // Handle focus management
    this.setupFocusManagement();
  }

  createContainer() {
    const container = document.createElement('div');
    container.className = 'modern-alert-container';
    container.setAttribute('aria-live', 'assertive');
    container.setAttribute('aria-atomic', 'false');
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', 'اعلان‌ها');
    return container;
  }

  createToastContainer() {
    const container = document.createElement('div');
    container.className = 'modern-toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('aria-atomic', 'false');
    container.setAttribute('role', 'region');
    container.setAttribute('aria-label', 'پیام‌های سیستم');
    return container;
  }

  /**
   * Show alert with glassmorphism effect
   * @param {Object} options - Alert configuration
   */
  show(options = {}) {
    const {
      type = 'info',
      title = '',
      message = '',
      duration = 5000,
      persistent = false,
      actions = [],
      position = 'top-right'
    } = options;

    const id = this.generateId();
    const alert = this.createAlert(id, type, title, message, persistent, actions);
    
    this.alerts.set(id, {
      element: alert,
      type,
      title,
      message,
      persistent,
      timer: null
    });

    // Add to container
    this.container.appendChild(alert);

    // Trigger show animation
    requestAnimationFrame(() => {
      alert.classList.add('show');
    });

    // Auto dismiss if not persistent
    if (!persistent && duration > 0) {
      this.setAutoDismiss(id, duration);
    }

    // Announce to screen readers
    this.announceToScreenReader(type, title, message);

    return id;
  }

  /**
   * Create alert element
   */
  createAlert(id, type, title, message, persistent, actions) {
    const alert = document.createElement('div');
    alert.className = `modern-alert ${type}`;
    alert.setAttribute('role', type === 'error' ? 'alert' : 'status');
    alert.setAttribute('data-alert-id', id);
    alert.setAttribute('tabindex', '-1');

    // Icon
    const icon = this.createIcon(type);
    
    // Content
    const content = document.createElement('div');
    content.className = 'modern-alert-content';
    
    if (title) {
      const titleEl = document.createElement('div');
      titleEl.className = 'modern-alert-title';
      titleEl.textContent = title;
      content.appendChild(titleEl);
    }
    
    if (message) {
      const messageEl = document.createElement('div');
      messageEl.className = 'modern-alert-message';
      messageEl.textContent = message;
      content.appendChild(messageEl);
    }

    // Actions
    if (actions.length > 0) {
      const actionsEl = this.createActions(actions, id);
      content.appendChild(actionsEl);
    }

    // Close button (if not persistent)
    const closeBtn = this.createCloseButton(id);

    // Progress bar (for auto-dismiss)
    const progress = this.createProgressBar();

    alert.appendChild(icon);
    alert.appendChild(content);
    if (!persistent) {
      alert.appendChild(closeBtn);
      alert.appendChild(progress);
    }

    return alert;
  }

  createIcon(type) {
    const iconContainer = document.createElement('div');
    iconContainer.className = 'modern-alert-icon';
    iconContainer.setAttribute('aria-hidden', 'true');

    const icons = {
      success: '✓',
      error: '✕',
      warning: '!',
      info: 'i'
    };

    iconContainer.textContent = icons[type] || icons.info;
    return iconContainer;
  }

  createActions(actions, alertId) {
    const actionsContainer = document.createElement('div');
    actionsContainer.className = 'modern-alert-actions';

    actions.forEach((action, index) => {
      const btn = document.createElement('button');
      btn.className = `modern-alert-action ${action.type || 'secondary'}`;
      btn.textContent = action.text;
      btn.setAttribute('data-action', action.id || index);
      
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        if (action.handler) {
          action.handler(alertId);
        }
        if (action.dismiss !== false) {
          this.dismiss(alertId);
        }
      });

      actionsContainer.appendChild(btn);
    });

    return actionsContainer;
  }

  createCloseButton(id) {
    const btn = document.createElement('button');
    btn.className = 'modern-alert-close';
    btn.innerHTML = '×';
    btn.setAttribute('aria-label', 'بستن اعلان');
    btn.setAttribute('type', 'button');
    
    btn.addEventListener('click', () => {
      this.dismiss(id);
    });

    return btn;
  }

  createProgressBar() {
    const progress = document.createElement('div');
    progress.className = 'modern-alert-progress';
    
    const bar = document.createElement('div');
    bar.className = 'modern-alert-progress-bar';
    
    progress.appendChild(bar);
    return progress;
  }

  setAutoDismiss(id, duration) {
    const alertData = this.alerts.get(id);
    if (!alertData) return;

    const progressBar = alertData.element.querySelector('.modern-alert-progress-bar');
    
    if (progressBar) {
      progressBar.style.transitionDuration = `${duration}ms`;
      progressBar.style.width = '100%';
    }

    alertData.timer = setTimeout(() => {
      this.dismiss(id);
    }, duration);
  }

  /**
   * Dismiss alert
   */
  dismiss(id) {
    const alertData = this.alerts.get(id);
    if (!alertData) return;

    const { element, timer } = alertData;
    
    if (timer) {
      clearTimeout(timer);
    }

    element.classList.remove('show');
    element.classList.add('hide');

    setTimeout(() => {
      if (element.parentNode) {
        element.parentNode.removeChild(element);
      }
      this.alerts.delete(id);
    }, 300);
  }

  /**
   * Show toast notification
   */
  toast(options = {}) {
    const {
      type = 'info',
      message = '',
      duration = 3000
    } = options;

    const toast = document.createElement('div');
    toast.className = `modern-toast ${type}`;
    
    const icon = this.createIcon(type);
    const content = document.createElement('div');
    content.textContent = message;
    
    toast.appendChild(icon);
    toast.appendChild(content);
    
    this.toastContainer.appendChild(toast);
    
    requestAnimationFrame(() => {
      toast.classList.add('show');
    });

    if (duration > 0) {
      setTimeout(() => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        setTimeout(() => {
          if (toast.parentNode) {
            toast.parentNode.removeChild(toast);
          }
        }, 300);
      }, duration);
    }
  }

  /**
   * Show form state
   */
  showFormState(form, type, title, message) {
    // Remove existing state
    const existingState = form.querySelector('.modern-form-state');
    if (existingState) {
      existingState.remove();
    }

    const state = document.createElement('div');
    state.className = `modern-form-state ${type}`;
    state.setAttribute('role', type === 'error' ? 'alert' : 'status');

    const icon = document.createElement('div');
    icon.className = 'modern-form-state-icon';
    icon.innerHTML = this.getIconHTML(type);

    const content = document.createElement('div');
    content.className = 'modern-form-state-content';

    if (title) {
      const titleEl = document.createElement('div');
      titleEl.className = 'modern-form-state-title';
      titleEl.textContent = title;
      content.appendChild(titleEl);
    }

    if (message) {
      const messageEl = document.createElement('div');
      messageEl.className = 'modern-form-state-message';
      messageEl.textContent = message;
      content.appendChild(messageEl);
    }

    state.appendChild(icon);
    state.appendChild(content);

    // Insert at the beginning of the form
    form.insertBefore(state, form.firstChild);

    // Trigger animation
    requestAnimationFrame(() => {
      state.classList.add('show');
    });

    // Scroll into view
    state.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }

  /**
   * Show field validation state
   */
  showFieldState(field, type, message) {
    const fieldContainer = field.closest('.modern-form-group') || field.parentNode;
    
    // Remove existing feedback
    const existingFeedback = fieldContainer.querySelector('.modern-field-feedback');
    if (existingFeedback) {
      existingFeedback.remove();
    }

    // Remove existing classes
    fieldContainer.classList.remove('modern-field-error', 'modern-field-success');
    
    if (type && message) {
      // Add new state
      fieldContainer.classList.add(`modern-field-${type}`);
      
      const feedback = document.createElement('div');
      feedback.className = `modern-field-feedback ${type}`;
      feedback.setAttribute('role', type === 'error' ? 'alert' : 'status');
      
      const icon = document.createElement('i');
      icon.className = this.getFieldIconClass(type);
      icon.setAttribute('aria-hidden', 'true');
      
      const text = document.createElement('span');
      text.textContent = message;
      
      feedback.appendChild(icon);
      feedback.appendChild(text);
      
      fieldContainer.appendChild(feedback);
    }
  }

  /**
   * Show loading state on button
   */
  showButtonLoading(button, loadingText = 'در حال بارگذاری...') {
    if (button.classList.contains('loading')) return;

    button.setAttribute('data-original-text', button.textContent);
    button.textContent = loadingText;
    button.classList.add('loading');
    button.disabled = true;
  }

  /**
   * Hide loading state on button
   */
  hideButtonLoading(button) {
    const originalText = button.getAttribute('data-original-text');
    if (originalText) {
      button.textContent = originalText;
      button.removeAttribute('data-original-text');
    }
    button.classList.remove('loading');
    button.disabled = false;
  }

  /**
   * Show loading overlay on container
   */
  showLoadingOverlay(container) {
    let overlay = container.querySelector('.modern-loading-overlay');
    
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.className = 'modern-loading-overlay';
      overlay.innerHTML = '<div class="modern-loading-spinner" role="status" aria-label="در حال بارگذاری"></div>';
      container.style.position = 'relative';
      container.appendChild(overlay);
    }
    
    requestAnimationFrame(() => {
      overlay.classList.add('show');
    });
  }

  /**
   * Hide loading overlay
   */
  hideLoadingOverlay(container) {
    const overlay = container.querySelector('.modern-loading-overlay');
    if (overlay) {
      overlay.classList.remove('show');
      setTimeout(() => {
        if (overlay.parentNode) {
          overlay.parentNode.removeChild(overlay);
        }
      }, 300);
    }
  }

  /**
   * Show success animation
   */
  showSuccessAnimation(container) {
    // Check if container exists
    if (!container) {
      console.warn('showSuccessAnimation: container is null');
      return;
    }
    
    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.classList.add('modern-success-checkmark');
    svg.setAttribute('viewBox', '0 0 52 52');
    
    const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
    circle.classList.add('modern-success-checkmark-circle');
    circle.setAttribute('cx', '26');
    circle.setAttribute('cy', '26');
    circle.setAttribute('r', '25');
    circle.setAttribute('fill', 'none');
    
    const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    path.classList.add('modern-success-checkmark-check');
    path.setAttribute('fill', 'none');
    path.setAttribute('d', 'M14.1 27.2l7.1 7.2 16.7-16.8');
    
    svg.appendChild(circle);
    svg.appendChild(path);
    
    container.appendChild(svg);
  }

  // Utility methods
  getIconHTML(type) {
    const icons = {
      success: '<i class="bi bi-check-circle"></i>',
      error: '<i class="bi bi-x-circle"></i>',
      warning: '<i class="bi bi-exclamation-triangle"></i>',
      info: '<i class="bi bi-info-circle"></i>'
    };
    return icons[type] || icons.info;
  }

  getFieldIconClass(type) {
    const icons = {
      success: 'bi bi-check-circle',
      error: 'bi bi-x-circle',
      warning: 'bi bi-exclamation-triangle'
    };
    return icons[type] || '';
  }

  generateId() {
    return `alert-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  announceToScreenReader(type, title, message) {
    const announcement = `${title ? title + '. ' : ''}${message}`;
    const liveRegion = document.createElement('div');
    liveRegion.setAttribute('aria-live', 'assertive');
    liveRegion.setAttribute('aria-atomic', 'true');
    liveRegion.className = 'visually-hidden';
    liveRegion.textContent = announcement;
    
    document.body.appendChild(liveRegion);
    
    setTimeout(() => {
      document.body.removeChild(liveRegion);
    }, 1000);
  }

  setupKeyboardHandlers() {
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        // Close the most recent non-persistent alert
        const visibleAlerts = this.container.querySelectorAll('.modern-alert.show');
        if (visibleAlerts.length > 0) {
          const lastAlert = visibleAlerts[visibleAlerts.length - 1];
          const alertId = lastAlert.getAttribute('data-alert-id');
          const alertData = this.alerts.get(alertId);
          
          if (alertData && !alertData.persistent) {
            this.dismiss(alertId);
            e.preventDefault();
          }
        }
      }
    });
  }

  setupFocusManagement() {
    // Focus management for alerts
    this.container.addEventListener('focusin', (e) => {
      if (e.target.classList.contains('modern-alert')) {
        e.target.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }
    });
  }

  // Static convenience methods
  static success(message, title = 'موفق', options = {}) {
    return window.modernAlerts.show({
      type: 'success',
      title,
      message,
      ...options
    });
  }

  static error(message, title = 'خطا', options = {}) {
    return window.modernAlerts.show({
      type: 'error',
      title,
      message,
      ...options
    });
  }

  static warning(message, title = 'هشدار', options = {}) {
    return window.modernAlerts.show({
      type: 'warning',
      title,
      message,
      ...options
    });
  }

  static info(message, title = 'اطلاعات', options = {}) {
    return window.modernAlerts.show({
      type: 'info',
      title,
      message,
      ...options
    });
  }

  static toast(message, type = 'info') {
    return window.modernAlerts.toast({ type, message });
  }
}

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.modernAlerts = new ModernAlerts();
});

// Export for module usage
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernAlerts;
}

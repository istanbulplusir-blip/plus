/**
 * Modern Navigation Component JavaScript
 * Handles glassmorphism effects, smooth animations, and micro-interactions
 */

class ModernNavigation {
  constructor() {
    this.navbar = document.getElementById('mainNavbar');
    this.navbarToggler = document.querySelector('.navbar-toggler');
    this.navbarCollapse = document.querySelector('.navbar-collapse');
    this.cartBadge = document.querySelector('.cart-badge');
    this.dropdownToggles = document.querySelectorAll('[data-bs-toggle="dropdown"]');
    
    this.init();
  }

  init() {
    this.setupScrollEffects();
    this.setupMobileMenu();
    this.setupDropdownEffects();
    this.setupCartAnimations();
    this.setupActiveNavLinks();
    this.setupKeyboardNavigation();
    this.setupReducedMotion();
    this.setupCartEventListeners();
  }

  /**
   * Enhanced scroll effects with glassmorphism
   */
  setupScrollEffects() {
    if (!this.navbar) return;

    let ticking = false;
    let lastScrollY = 0;

    const updateNavbar = () => {
      const scrollY = window.scrollY;
      const scrollDirection = scrollY > lastScrollY ? 'down' : 'up';
      
      // Add/remove scrolled class for glassmorphism effect
      if (scrollY > 50) {
        this.navbar.classList.add('scrolled');
      } else {
        this.navbar.classList.remove('scrolled');
      }

      // Hide navbar on scroll down, show on scroll up (optional enhancement)
      if (Math.abs(scrollY - lastScrollY) > 10) {
        if (scrollDirection === 'down' && scrollY > 200) {
          this.navbar.style.transform = 'translateY(-100%)';
        } else if (scrollDirection === 'up') {
          this.navbar.style.transform = 'translateY(0)';
        }
      }

      lastScrollY = scrollY;
      ticking = false;
    };

    window.addEventListener('scroll', () => {
      if (!ticking) {
        requestAnimationFrame(updateNavbar);
        ticking = true;
      }
    }, { passive: true });
  }

  /**
   * Enhanced mobile menu with slide animations
   */
  setupMobileMenu() {
    if (!this.navbarToggler || !this.navbarCollapse) return;

    // Add smooth slide animation
    this.navbarCollapse.addEventListener('show.bs.collapse', () => {
      this.navbarCollapse.style.animation = 'slideInDown 0.3s ease-out';
    });

    this.navbarCollapse.addEventListener('hide.bs.collapse', () => {
      this.navbarCollapse.style.animation = 'slideInUp 0.3s ease-in reverse';
    });

    // Close mobile menu when clicking nav links
    const navLinks = this.navbarCollapse.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
      link.addEventListener('click', () => {
        if (window.innerWidth < 992) {
          const bsCollapse = new bootstrap.Collapse(this.navbarCollapse, {
            toggle: false
          });
          bsCollapse.hide();
        }
      });
    });

    // Close mobile menu when clicking outside
    document.addEventListener('click', (e) => {
      if (window.innerWidth < 992 && 
          !this.navbar.contains(e.target) && 
          this.navbarCollapse.classList.contains('show')) {
        const bsCollapse = new bootstrap.Collapse(this.navbarCollapse, {
          toggle: false
        });
        bsCollapse.hide();
      }
    });
  }

  /**
   * Enhanced dropdown effects
   */
  setupDropdownEffects() {
    this.dropdownToggles.forEach(toggle => {
      const dropdown = toggle.nextElementSibling;
      if (!dropdown) return;

      // Add entrance animation
      toggle.addEventListener('show.bs.dropdown', () => {
        dropdown.style.animation = 'slideInDown 0.2s ease-out';
      });

      // Add exit animation
      toggle.addEventListener('hide.bs.dropdown', () => {
        dropdown.style.animation = 'fadeOut 0.15s ease-in';
      });

      // Add hover effects for dropdown items
      const dropdownItems = dropdown.querySelectorAll('.dropdown-item');
      dropdownItems.forEach((item, index) => {
        item.style.animationDelay = `${index * 0.05}s`;
        
        item.addEventListener('mouseenter', () => {
          if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
            item.style.transform = 'translateX(4px)';
          }
        });

        item.addEventListener('mouseleave', () => {
          item.style.transform = 'translateX(0)';
        });
      });
    });
  }

  /**
   * Cart badge animations and micro-interactions
   */
  setupCartAnimations() {
    if (!this.cartBadge) return;

    // Animate cart badge when updated
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' || mutation.type === 'characterData') {
          this.animateCartBadge();
        }
      });
    });

    observer.observe(this.cartBadge, {
      childList: true,
      characterData: true,
      subtree: true
    });

    // Cart link hover effect
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
      cartLink.addEventListener('mouseenter', () => {
        if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
          cartLink.style.transform = 'translateY(-2px)';
          const icon = cartLink.querySelector('i');
          if (icon) {
            icon.style.transform = 'scale(1.15)';
          }
        }
      });

      cartLink.addEventListener('mouseleave', () => {
        cartLink.style.transform = 'translateY(0)';
        const icon = cartLink.querySelector('i');
        if (icon) {
          icon.style.transform = 'scale(1)';
        }
      });
    }
  }

  /**
   * Animate cart badge when updated
   */
  animateCartBadge() {
    if (!this.cartBadge || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

    this.cartBadge.classList.remove('updated');
    // Force reflow
    this.cartBadge.offsetHeight;
    this.cartBadge.classList.add('updated');

    // Remove class after animation
    setTimeout(() => {
      this.cartBadge.classList.remove('updated');
    }, 600);
  }

  /**
   * Set active navigation links based on current page
   */
  setupActiveNavLinks() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');

    navLinks.forEach(link => {
      const href = link.getAttribute('href');
      if (href === currentPath || (href !== '/' && currentPath.startsWith(href))) {
        link.classList.add('active');
        link.setAttribute('aria-current', 'page');
      } else {
        link.classList.remove('active');
        link.removeAttribute('aria-current');
      }
    });
  }

  /**
   * Enhanced keyboard navigation
   */
  setupKeyboardNavigation() {
    // Escape key closes mobile menu and dropdowns
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        // Close mobile menu
        if (this.navbarCollapse && this.navbarCollapse.classList.contains('show')) {
          const bsCollapse = new bootstrap.Collapse(this.navbarCollapse, {
            toggle: false
          });
          bsCollapse.hide();
        }

        // Close dropdowns
        const openDropdowns = document.querySelectorAll('.dropdown-menu.show');
        openDropdowns.forEach(dropdown => {
          const toggle = dropdown.previousElementSibling;
          if (toggle) {
            const bsDropdown = new bootstrap.Dropdown(toggle);
            bsDropdown.hide();
          }
        });
      }
    });

    // Arrow key navigation in dropdowns
    this.dropdownToggles.forEach(toggle => {
      const dropdown = toggle.nextElementSibling;
      if (!dropdown) return;

      dropdown.addEventListener('keydown', (e) => {
        const items = dropdown.querySelectorAll('.dropdown-item:not(.disabled)');
        const currentIndex = Array.from(items).indexOf(document.activeElement);

        switch (e.key) {
          case 'ArrowDown':
            e.preventDefault();
            const nextIndex = currentIndex < items.length - 1 ? currentIndex + 1 : 0;
            items[nextIndex].focus();
            break;
          case 'ArrowUp':
            e.preventDefault();
            const prevIndex = currentIndex > 0 ? currentIndex - 1 : items.length - 1;
            items[prevIndex].focus();
            break;
          case 'Home':
            e.preventDefault();
            items[0].focus();
            break;
          case 'End':
            e.preventDefault();
            items[items.length - 1].focus();
            break;
        }
      });
    });
  }

  /**
   * Respect user's motion preferences
   */
  setupReducedMotion() {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
    
    const handleMotionPreference = (e) => {
      if (e.matches) {
        // Disable animations
        document.documentElement.style.setProperty('--transition-fast', '0ms');
        document.documentElement.style.setProperty('--transition-base', '0ms');
        document.documentElement.style.setProperty('--transition-slow', '0ms');
      } else {
        // Re-enable animations
        document.documentElement.style.removeProperty('--transition-fast');
        document.documentElement.style.removeProperty('--transition-base');
        document.documentElement.style.removeProperty('--transition-slow');
      }
    };

    prefersReducedMotion.addEventListener('change', handleMotionPreference);
    handleMotionPreference(prefersReducedMotion);
  }

  /**
   * Public method to update cart badge
   */
  updateCartBadge(count) {
    if (!this.cartBadge) return;

    this.cartBadge.textContent = count;
    
    // Show/hide badge based on count
    if (count > 0) {
      this.cartBadge.style.display = 'flex';
      this.cartBadge.parentElement.classList.add('has-items');
    } else {
      this.cartBadge.style.display = 'none';
      this.cartBadge.parentElement.classList.remove('has-items');
    }
    
    this.animateCartBadge();

    // Update aria-label for accessibility
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
      const label = count > 0 ? `سبد خرید - ${count} آیتم` : 'سبد خرید';
      cartLink.setAttribute('aria-label', label);
    }
  }

  /**
   * Public method to show loading state
   */
  showLoading() {
    if (this.navbar) {
      this.navbar.classList.add('nav-loading');
    }
  }

  /**
   * Setup cart event listeners
   */
  setupCartEventListeners() {
    // Listen for cart update events
    window.addEventListener('cartUpdated', (event) => {
      const count = event.detail.count;
      this.updateCartBadge(count);
    });
    
    // Listen for cart loading state changes
    window.addEventListener('cartLoading', (event) => {
      const isLoading = event.detail.loading;
      const cartLink = document.querySelector('.cart-link');
      if (cartLink) {
        if (isLoading) {
          cartLink.classList.add('loading');
        } else {
          cartLink.classList.remove('loading');
        }
      }
    });
  }

  /**
   * Public method to hide loading state
   */
  hideLoading() {
    if (this.navbar) {
      this.navbar.classList.remove('nav-loading');
    }
  }
}

// Initialize navigation when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  window.modernNavigation = new ModernNavigation();
});

// Language switching functionality
function setLanguage(language) {
  // Get current URL
  const currentUrl = window.location.href;
  
  // Get CSRF token
  const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]');
  if (!csrfToken) {
    console.error('CSRF token not found');
    alert('خطا: توکن امنیتی یافت نشد. لطفاً صفحه را رفرش کنید.');
    return;
  }
  
  // Show loading state
  const buttons = document.querySelectorAll('[onclick*="setLanguage"]');
  buttons.forEach(btn => {
    btn.disabled = true;
    btn.classList.add('loading');
  });
  
  // Create form and submit it (Django i18n expects form submission)
  const form = document.createElement('form');
  form.method = 'POST';
  form.action = '/i18n/setlang/';
  form.style.display = 'none';
  
  // Add CSRF token
  const csrfInput = document.createElement('input');
  csrfInput.type = 'hidden';
  csrfInput.name = 'csrfmiddlewaretoken';
  csrfInput.value = csrfToken.value;
  form.appendChild(csrfInput);
  
  // Add language
  const languageInput = document.createElement('input');
  languageInput.type = 'hidden';
  languageInput.name = 'language';
  languageInput.value = language;
  form.appendChild(languageInput);
  
  // Add next URL
  const nextInput = document.createElement('input');
  nextInput.type = 'hidden';
  nextInput.name = 'next';
  nextInput.value = currentUrl;
  form.appendChild(nextInput);
  
  // Submit form
  document.body.appendChild(form);
  form.submit();
}

// Make setLanguage globally available
window.setLanguage = setLanguage;

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernNavigation;
}
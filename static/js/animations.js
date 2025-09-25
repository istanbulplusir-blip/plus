/**
 * Micro-interactions and Animations Manager
 * Handles scroll-triggered animations, hover effects, and interactive states
 */

class AnimationManager {
    constructor() {
        this.observers = new Map();
        this.isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        this.init();
    }

    init() {
        // Initialize scroll animations
        this.initScrollAnimations();
        
        // Initialize hover effects
        this.initHoverEffects();
        
        // Initialize loading states
        this.initLoadingStates();
        
        // Initialize form animations
        this.initFormAnimations();
        
        // Listen for reduced motion changes
        this.setupReducedMotionListener();
        
        console.log('Animation Manager initialized');
    }

    /**
     * Initialize scroll-triggered animations using Intersection Observer
     */
    initScrollAnimations() {
        if (this.isReducedMotion) return;

        // Create intersection observer for scroll animations
        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-in');
                    
                    // Handle staggered animations
                    if (entry.target.classList.contains('scroll-stagger')) {
                        this.handleStaggeredAnimation(entry.target);
                    }
                }
            });
        }, {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        });

        // Observe all scroll animation elements
        const scrollElements = document.querySelectorAll([
            '.scroll-animate',
            '.scroll-fade-up',
            '.scroll-fade-down',
            '.scroll-fade-left',
            '.scroll-fade-right',
            '.scroll-scale',
            '.scroll-stagger'
        ].join(', '));

        scrollElements.forEach(el => {
            scrollObserver.observe(el);
        });

        this.observers.set('scroll', scrollObserver);
    }

    /**
     * Handle staggered animations for lists and grids
     */
    handleStaggeredAnimation(container) {
        const children = container.children;
        Array.from(children).forEach((child, index) => {
            setTimeout(() => {
                child.classList.add('animate-in');
            }, index * 100); // 100ms delay between each item
        });
    }

    /**
     * Initialize enhanced hover effects
     */
    initHoverEffects() {
        if (this.isReducedMotion) return;

        // Add hover classes to interactive elements
        this.addHoverEffects('.btn', 'hover-lift-sm');
        this.addHoverEffects('.card', 'hover-lift');
        this.addHoverEffects('.product-card', 'hover-lift-lg');
        this.addHoverEffects('.category-card', 'hover-scale-sm');
        
        // Add shimmer effect to buttons
        document.querySelectorAll('.btn-modern, .btn-auth').forEach(btn => {
            if (!btn.classList.contains('shimmer')) {
                btn.classList.add('shimmer');
            }
        });

        // Add glow effects to primary buttons
        document.querySelectorAll('.btn-primary, .btn-auth').forEach(btn => {
            if (!btn.classList.contains('hover-glow')) {
                btn.classList.add('hover-glow');
            }
        });
    }

    /**
     * Add hover effect classes to elements
     */
    addHoverEffects(selector, hoverClass) {
        document.querySelectorAll(selector).forEach(el => {
            if (!el.classList.contains(hoverClass)) {
                el.classList.add(hoverClass);
            }
        });
    }

    /**
     * Initialize loading state animations
     */
    initLoadingStates() {
        // Handle button loading states
        this.initButtonLoadingStates();
        
        // Handle form submission states
        this.initFormLoadingStates();
        
        // Handle image loading states
        this.initImageLoadingStates();
    }

    /**
     * Initialize button loading states with modern animations
     */
    initButtonLoadingStates() {
        document.addEventListener('click', (e) => {
            const btn = e.target.closest('.btn');
            if (!btn) return;

            // Add loading state for form submissions
            if (btn.type === 'submit' || btn.classList.contains('submit-btn')) {
                this.setButtonLoading(btn, true);
                
                // Auto-remove loading state after 3 seconds (fallback)
                setTimeout(() => {
                    this.setButtonLoading(btn, false);
                }, 3000);
            }
        });
    }

    /**
     * Set button loading state
     */
    setButtonLoading(btn, isLoading) {
        if (isLoading) {
            btn.classList.add('btn-loading');
            btn.disabled = true;
            
            // Store original text
            if (!btn.dataset.originalText) {
                btn.dataset.originalText = btn.textContent;
            }
            
            // Add loading spinner
            const spinner = document.createElement('span');
            spinner.className = 'loading-spinner loading-spinner-sm';
            spinner.style.marginRight = '8px';
            
            btn.innerHTML = '';
            btn.appendChild(spinner);
            btn.appendChild(document.createTextNode('در حال پردازش...'));
        } else {
            btn.classList.remove('btn-loading');
            btn.disabled = false;
            
            // Restore original text
            if (btn.dataset.originalText) {
                btn.textContent = btn.dataset.originalText;
            }
        }
    }

    /**
     * Initialize form loading states
     */
    initFormLoadingStates() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (!form.classList.contains('no-loading')) {
                this.setFormLoading(form, true);
            }
        });
    }

    /**
     * Set form loading state
     */
    setFormLoading(form, isLoading) {
        if (isLoading) {
            form.classList.add('form-submitting');
            
            // Disable all form inputs
            const inputs = form.querySelectorAll('input, select, textarea, button');
            inputs.forEach(input => {
                input.disabled = true;
            });
        } else {
            form.classList.remove('form-submitting');
            
            // Re-enable form inputs
            const inputs = form.querySelectorAll('input, select, textarea, button');
            inputs.forEach(input => {
                input.disabled = false;
            });
        }
    }

    /**
     * Initialize image loading animations
     */
    initImageLoadingStates() {
        const images = document.querySelectorAll('img[data-src], img[loading="lazy"]');
        
        images.forEach(img => {
            // Add loading class initially
            img.classList.add('card-img-loading');
            
            // Remove loading class when image loads
            img.addEventListener('load', () => {
                img.classList.remove('card-img-loading');
                img.classList.add('animate-fade-in');
            });
            
            // Handle error state
            img.addEventListener('error', () => {
                img.classList.remove('card-img-loading');
                img.classList.add('image-error');
            });
        });
    }

    /**
     * Initialize form field animations
     */
    initFormAnimations() {
        if (this.isReducedMotion) return;

        // Add animation classes to form fields
        document.querySelectorAll('.form-control, .form-select').forEach(field => {
            field.classList.add('form-field-animate');
        });

        // Handle floating label animations
        this.initFloatingLabelAnimations();
        
        // Handle validation animations
        this.initValidationAnimations();
    }

    /**
     * Initialize floating label animations
     */
    initFloatingLabelAnimations() {
        document.querySelectorAll('.form-floating input, .form-floating select').forEach(field => {
            // Add focus animation
            field.addEventListener('focus', () => {
                field.parentElement.classList.add('focused');
            });
            
            field.addEventListener('blur', () => {
                if (!field.value) {
                    field.parentElement.classList.remove('focused');
                }
            });
            
            // Check initial state
            if (field.value) {
                field.parentElement.classList.add('focused');
            }
        });
    }

    /**
     * Initialize validation animations
     */
    initValidationAnimations() {
        document.addEventListener('invalid', (e) => {
            const field = e.target;
            if (field.classList.contains('form-control') || field.classList.contains('form-select')) {
                // Add shake animation for invalid fields
                field.classList.add('animate-shake');
                
                // Remove shake class after animation
                setTimeout(() => {
                    field.classList.remove('animate-shake');
                }, 820);
            }
        }, true);
    }

    /**
     * Setup reduced motion preference listener
     */
    setupReducedMotionListener() {
        const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
        
        mediaQuery.addEventListener('change', (e) => {
            this.isReducedMotion = e.matches;
            
            if (this.isReducedMotion) {
                this.disableAnimations();
            } else {
                this.enableAnimations();
            }
        });
    }

    /**
     * Disable all animations for reduced motion
     */
    disableAnimations() {
        // Disconnect all observers
        this.observers.forEach(observer => observer.disconnect());
        
        // Add reduced motion class to body
        document.body.classList.add('reduced-motion');
        
        // Remove animation classes
        document.querySelectorAll('[class*="animate-"], [class*="hover-"], [class*="scroll-"]').forEach(el => {
            const classes = Array.from(el.classList);
            classes.forEach(cls => {
                if (cls.includes('animate-') || cls.includes('hover-') || cls.includes('scroll-')) {
                    el.classList.remove(cls);
                }
            });
        });
    }

    /**
     * Enable animations when reduced motion is turned off
     */
    enableAnimations() {
        document.body.classList.remove('reduced-motion');
        this.init(); // Re-initialize animations
    }

    /**
     * Add scroll animation to element
     */
    addScrollAnimation(element, animationType = 'scroll-fade-up') {
        if (this.isReducedMotion) return;
        
        element.classList.add(animationType);
        
        if (this.observers.has('scroll')) {
            this.observers.get('scroll').observe(element);
        }
    }

    /**
     * Trigger animation on element
     */
    triggerAnimation(element, animationType) {
        if (this.isReducedMotion) return;
        
        element.classList.add(animationType);
        
        // Remove animation class after completion
        element.addEventListener('animationend', () => {
            element.classList.remove(animationType);
        }, { once: true });
    }

    /**
     * Create staggered animation for children
     */
    staggerChildren(container, delay = 100) {
        if (this.isReducedMotion) return;
        
        const children = Array.from(container.children);
        children.forEach((child, index) => {
            child.style.animationDelay = `${index * delay}ms`;
            child.classList.add('scroll-stagger');
        });
    }

    /**
     * Cleanup method
     */
    destroy() {
        this.observers.forEach(observer => observer.disconnect());
        this.observers.clear();
    }
}

// Utility functions for manual animation control
window.AnimationUtils = {
    /**
     * Add loading state to button
     */
    setButtonLoading: (btn, isLoading) => {
        if (window.animationManager) {
            window.animationManager.setButtonLoading(btn, isLoading);
        }
    },

    /**
     * Add scroll animation to element
     */
    addScrollAnimation: (element, type) => {
        if (window.animationManager) {
            window.animationManager.addScrollAnimation(element, type);
        }
    },

    /**
     * Trigger animation on element
     */
    animate: (element, type) => {
        if (window.animationManager) {
            window.animationManager.triggerAnimation(element, type);
        }
    },

    /**
     * Create staggered animation
     */
    stagger: (container, delay) => {
        if (window.animationManager) {
            window.animationManager.staggerChildren(container, delay);
        }
    }
};

// Initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    window.animationManager = new AnimationManager();
});

// Handle page visibility changes
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        // Pause animations when page is hidden
        document.body.classList.add('animations-paused');
    } else {
        // Resume animations when page is visible
        document.body.classList.remove('animations-paused');
    }
});

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = AnimationManager;
}
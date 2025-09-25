/**
 * Cross-Browser Support and Feature Detection
 * Task 15: Implement cross-browser compatibility and testing
 */

(function() {
    'use strict';

    // Feature Detection Object
    const FeatureDetection = {
        // Test for CSS Custom Properties support
        cssCustomProperties: function() {
            return window.CSS && CSS.supports && CSS.supports('--css', 'variables');
        },

        // Test for CSS Grid support
        cssGrid: function() {
            return CSS.supports && CSS.supports('display', 'grid');
        },

        // Test for CSS Flexbox support
        flexbox: function() {
            return CSS.supports && CSS.supports('display', 'flex');
        },

        // Test for CSS Gap support
        cssGap: function() {
            return CSS.supports && CSS.supports('gap', '1rem');
        },

        // Test for Backdrop Filter support
        backdropFilter: function() {
            return CSS.supports && (
                CSS.supports('backdrop-filter', 'blur(1px)') ||
                CSS.supports('-webkit-backdrop-filter', 'blur(1px)')
            );
        },

        // Test for CSS Aspect Ratio support
        aspectRatio: function() {
            return CSS.supports && CSS.supports('aspect-ratio', '1/1');
        },

        // Test for CSS Container Queries support
        containerQueries: function() {
            return CSS.supports && CSS.supports('container-type', 'inline-size');
        },

        // Test for CSS Logical Properties support
        logicalProperties: function() {
            return CSS.supports && CSS.supports('margin-inline-start', '1rem');
        },

        // Test for Intersection Observer support
        intersectionObserver: function() {
            return 'IntersectionObserver' in window;
        },

        // Test for Web Animations API support
        webAnimations: function() {
            return 'animate' in document.createElement('div');
        },

        // Test for WebP support
        webp: function() {
            return new Promise((resolve) => {
                const webP = new Image();
                webP.onload = webP.onerror = function () {
                    resolve(webP.height === 2);
                };
                webP.src = 'data:image/webp;base64,UklGRjoAAABXRUJQVlA4IC4AAACyAgCdASoCAAIALmk0mk0iIiIiIgBoSygABc6WWgAA/veff/0PP8bA//LwYAAA';
            });
        },

        // Test for AVIF support
        avif: function() {
            return new Promise((resolve) => {
                const avif = new Image();
                avif.onload = avif.onerror = function () {
                    resolve(avif.height === 2);
                };
                avif.src = 'data:image/avif;base64,AAAAIGZ0eXBhdmlmAAAAAGF2aWZtaWYxbWlhZk1BMUIAAADybWV0YQAAAAAAAAAoaGRscgAAAAAAAAAAcGljdAAAAAAAAAAAAAAAAGxpYmF2aWYAAAAADnBpdG0AAAAAAAEAAAAeaWxvYwAAAABEAAABAAEAAAABAAABGgAAAB0AAAAoaWluZgAAAAAAAQAAABppbmZlAgAAAAABAABhdjAxQ29sb3IAAAAAamlwcnAAAABLaXBjbwAAABRpc3BlAAAAAAAAAAIAAAACAAAAEHBpeGkAAAAAAwgICAAAAAxhdjFDgQ0MAAAAABNjb2xybmNseAACAAIAAYAAAAAXaXBtYQAAAAAAAAABAAEEAQKDBAAAACVtZGF0EgAKCBgABogQEAwgMg8f8D///8WfhwB8+ErK42A=';
            });
        },

        // Test for smooth scroll support
        smoothScroll: function() {
            return CSS.supports && CSS.supports('scroll-behavior', 'smooth');
        },

        // Test for prefers-reduced-motion support
        prefersReducedMotion: function() {
            return window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        },

        // Test for prefers-color-scheme support
        prefersColorScheme: function() {
            return window.matchMedia && (
                window.matchMedia('(prefers-color-scheme: dark)').matches ||
                window.matchMedia('(prefers-color-scheme: light)').matches
            );
        },

        // Test for touch support
        touch: function() {
            return 'ontouchstart' in window || navigator.maxTouchPoints > 0;
        },

        // Test for passive event listeners support
        passiveEvents: function() {
            let supportsPassive = false;
            try {
                const opts = Object.defineProperty({}, 'passive', {
                    get: function() {
                        supportsPassive = true;
                        return true;
                    }
                });
                window.addEventListener('testPassive', null, opts);
                window.removeEventListener('testPassive', null, opts);
            } catch (e) {}
            return supportsPassive;
        }
    };

    // Browser Detection
    const BrowserDetection = {
        isIE: function() {
            return navigator.userAgent.indexOf('MSIE') !== -1 || navigator.appVersion.indexOf('Trident/') > -1;
        },

        isEdge: function() {
            return navigator.userAgent.indexOf('Edge') !== -1;
        },

        isChrome: function() {
            return navigator.userAgent.indexOf('Chrome') !== -1 && !this.isEdge();
        },

        isFirefox: function() {
            return navigator.userAgent.indexOf('Firefox') !== -1;
        },

        isSafari: function() {
            return navigator.userAgent.indexOf('Safari') !== -1 && !this.isChrome() && !this.isEdge();
        },

        isOpera: function() {
            return navigator.userAgent.indexOf('Opera') !== -1 || navigator.userAgent.indexOf('OPR') !== -1;
        },

        isMobile: function() {
            return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        },

        getVersion: function() {
            const ua = navigator.userAgent;
            let version = 'unknown';

            if (this.isChrome()) {
                const match = ua.match(/Chrome\/(\d+)/);
                version = match ? match[1] : 'unknown';
            } else if (this.isFirefox()) {
                const match = ua.match(/Firefox\/(\d+)/);
                version = match ? match[1] : 'unknown';
            } else if (this.isSafari()) {
                const match = ua.match(/Version\/(\d+)/);
                version = match ? match[1] : 'unknown';
            } else if (this.isEdge()) {
                const match = ua.match(/Edge\/(\d+)/);
                version = match ? match[1] : 'unknown';
            } else if (this.isIE()) {
                const match = ua.match(/(?:MSIE |Trident\/.*; rv:)(\d+)/);
                version = match ? match[1] : 'unknown';
            }

            return version;
        }
    };

    // Polyfill Manager
    const PolyfillManager = {
        // Load polyfills based on feature detection
        loadPolyfills: function() {
            const polyfills = [];

            // CSS Custom Properties polyfill for IE11
            if (!FeatureDetection.cssCustomProperties() && BrowserDetection.isIE()) {
                polyfills.push('https://cdn.jsdelivr.net/npm/css-vars-ponyfill@2.4.8/dist/css-vars-ponyfill.min.js');
            }

            // Intersection Observer polyfill
            if (!FeatureDetection.intersectionObserver()) {
                polyfills.push('https://cdn.jsdelivr.net/npm/intersection-observer@0.12.2/intersection-observer.js');
            }

            // Web Animations API polyfill
            if (!FeatureDetection.webAnimations()) {
                polyfills.push('https://cdn.jsdelivr.net/npm/web-animations-js@2.3.2/web-animations.min.js');
            }

            // Load polyfills
            polyfills.forEach(src => {
                const script = document.createElement('script');
                script.src = src;
                script.async = true;
                document.head.appendChild(script);
            });

            return polyfills.length > 0;
        },

        // Initialize CSS Variables polyfill
        initCSSVarsPolyfill: function() {
            if (window.cssVars) {
                cssVars({
                    include: 'style,link[rel="stylesheet"]',
                    preserve: false,
                    variables: {
                        // Fallback variables for IE11
                        '--color-primary': '#667eea',
                        '--color-secondary': '#764ba2',
                        '--radius-xl': '12px',
                        '--space-3': '12px',
                        '--space-6': '24px',
                        '--transition-base': '0.2s ease-in-out'
                    }
                });
            }
        }
    };

    // Progressive Enhancement Manager
    const ProgressiveEnhancement = {
        // Add feature classes to document
        addFeatureClasses: function() {
            const html = document.documentElement;
            const classes = [];

            // JavaScript detection
            html.classList.remove('no-js');
            html.classList.add('js');

            // CSS feature classes
            classes.push(FeatureDetection.cssCustomProperties() ? 'css-custom-properties' : 'no-css-custom-properties');
            classes.push(FeatureDetection.cssGrid() ? 'css-grid' : 'no-css-grid');
            classes.push(FeatureDetection.flexbox() ? 'flexbox' : 'no-flexbox');
            classes.push(FeatureDetection.cssGap() ? 'css-gap' : 'no-css-gap');
            classes.push(FeatureDetection.backdropFilter() ? 'backdrop-filter' : 'no-backdrop-filter');
            classes.push(FeatureDetection.aspectRatio() ? 'aspect-ratio' : 'no-aspect-ratio');
            classes.push(FeatureDetection.containerQueries() ? 'container-queries' : 'no-container-queries');
            classes.push(FeatureDetection.logicalProperties() ? 'logical-properties' : 'no-logical-properties');

            // API feature classes
            classes.push(FeatureDetection.intersectionObserver() ? 'intersection-observer' : 'no-intersection-observer');
            classes.push(FeatureDetection.webAnimations() ? 'web-animations' : 'no-web-animations');
            classes.push(FeatureDetection.smoothScroll() ? 'smooth-scroll' : 'no-smooth-scroll');

            // User preference classes
            classes.push(FeatureDetection.prefersReducedMotion() ? 'prefers-reduced-motion' : 'no-prefers-reduced-motion');
            classes.push(FeatureDetection.touch() ? 'touch' : 'no-touch');

            // Browser classes
            if (BrowserDetection.isIE()) classes.push('ie', `ie-${BrowserDetection.getVersion()}`);
            if (BrowserDetection.isEdge()) classes.push('edge', `edge-${BrowserDetection.getVersion()}`);
            if (BrowserDetection.isChrome()) classes.push('chrome', `chrome-${BrowserDetection.getVersion()}`);
            if (BrowserDetection.isFirefox()) classes.push('firefox', `firefox-${BrowserDetection.getVersion()}`);
            if (BrowserDetection.isSafari()) classes.push('safari', `safari-${BrowserDetection.getVersion()}`);
            if (BrowserDetection.isOpera()) classes.push('opera');
            if (BrowserDetection.isMobile()) classes.push('mobile');

            // Add all classes
            html.classList.add(...classes);
        },

        // Add image format support classes
        addImageFormatClasses: async function() {
            const html = document.documentElement;

            try {
                const webpSupported = await FeatureDetection.webp();
                html.classList.add(webpSupported ? 'webp' : 'no-webp');

                const avifSupported = await FeatureDetection.avif();
                html.classList.add(avifSupported ? 'avif' : 'no-avif');
            } catch (error) {
                console.warn('Image format detection failed:', error);
                html.classList.add('no-webp', 'no-avif');
            }
        },

        // Enhance cards with modern features
        enhanceCards: function() {
            if (!FeatureDetection.backdropFilter()) {
                // Add fallback class for cards without backdrop-filter support
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => {
                    card.classList.add('card-fallback');
                });
            } else {
                // Add enhanced class for modern browsers
                const cards = document.querySelectorAll('.card');
                cards.forEach(card => {
                    card.classList.add('enhanced');
                });
            }
        },

        // Enhance buttons with modern features
        enhanceButtons: function() {
            const buttons = document.querySelectorAll('.btn-modern');
            
            buttons.forEach(button => {
                // Add ripple effect for modern browsers
                if (FeatureDetection.webAnimations()) {
                    button.addEventListener('click', this.createRippleEffect.bind(this));
                }

                // Add focus-visible polyfill behavior
                if (!CSS.supports && !CSS.supports('selector(:focus-visible)')) {
                    this.addFocusVisiblePolyfill(button);
                }
            });
        },

        // Create ripple effect for buttons
        createRippleEffect: function(event) {
            const button = event.currentTarget;
            const rect = button.getBoundingClientRect();
            const size = Math.max(rect.width, rect.height);
            const x = event.clientX - rect.left - size / 2;
            const y = event.clientY - rect.top - size / 2;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: ${size}px;
                height: ${size}px;
                left: ${x}px;
                top: ${y}px;
                background: rgba(255, 255, 255, 0.3);
                border-radius: 50%;
                pointer-events: none;
                transform: scale(0);
            `;

            button.appendChild(ripple);

            ripple.animate([
                { transform: 'scale(0)', opacity: 1 },
                { transform: 'scale(1)', opacity: 0 }
            ], {
                duration: 600,
                easing: 'ease-out'
            }).onfinish = () => {
                ripple.remove();
            };
        },

        // Add focus-visible polyfill behavior
        addFocusVisiblePolyfill: function(element) {
            let hadKeyboardEvent = false;

            const onKeyDown = () => {
                hadKeyboardEvent = true;
            };

            const onFocus = () => {
                if (hadKeyboardEvent) {
                    element.classList.add('focus-visible');
                }
            };

            const onBlur = () => {
                element.classList.remove('focus-visible');
                hadKeyboardEvent = false;
            };

            document.addEventListener('keydown', onKeyDown, true);
            element.addEventListener('focus', onFocus);
            element.addEventListener('blur', onBlur);
        }
    };

    // Smooth Scroll Polyfill
    const SmoothScrollPolyfill = {
        init: function() {
            if (!FeatureDetection.smoothScroll()) {
                this.polyfillSmoothScroll();
            }
        },

        polyfillSmoothScroll: function() {
            // Simple smooth scroll polyfill
            const links = document.querySelectorAll('a[href^="#"]');
            
            links.forEach(link => {
                link.addEventListener('click', (e) => {
                    const targetId = link.getAttribute('href').substring(1);
                    const targetElement = document.getElementById(targetId);
                    
                    if (targetElement) {
                        e.preventDefault();
                        this.smoothScrollTo(targetElement);
                    }
                });
            });
        },

        smoothScrollTo: function(element) {
            const targetPosition = element.offsetTop;
            const startPosition = window.pageYOffset;
            const distance = targetPosition - startPosition;
            const duration = 800;
            let start = null;

            const step = (timestamp) => {
                if (!start) start = timestamp;
                const progress = timestamp - start;
                const percentage = Math.min(progress / duration, 1);
                
                // Easing function
                const ease = this.easeInOutCubic(percentage);
                
                window.scrollTo(0, startPosition + distance * ease);
                
                if (progress < duration) {
                    window.requestAnimationFrame(step);
                }
            };

            window.requestAnimationFrame(step);
        },

        easeInOutCubic: function(t) {
            return t < 0.5 ? 4 * t * t * t : (t - 1) * (2 * t - 2) * (2 * t - 2) + 1;
        }
    };

    // Accessibility Enhancements
    const AccessibilityEnhancements = {
        init: function() {
            this.addSkipLinks();
            this.enhanceFocusManagement();
            this.addARIALabels();
            this.handleReducedMotion();
        },

        addSkipLinks: function() {
            // Skip links disabled - no longer needed
            // if (!document.querySelector('.skip-link')) {
            //     const skipLink = document.createElement('a');
            //     skipLink.href = '#main-content';
            //     skipLink.className = 'skip-link';
            //     skipLink.textContent = 'Skip to main content';
            //     document.body.insertBefore(skipLink, document.body.firstChild);
            // }
        },

        enhanceFocusManagement: function() {
            // Trap focus in modals
            const modals = document.querySelectorAll('.modal');
            modals.forEach(modal => {
                this.trapFocus(modal);
            });
        },

        trapFocus: function(element) {
            const focusableElements = element.querySelectorAll(
                'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            
            if (focusableElements.length === 0) return;
            
            const firstElement = focusableElements[0];
            const lastElement = focusableElements[focusableElements.length - 1];

            element.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    if (e.shiftKey) {
                        if (document.activeElement === firstElement) {
                            lastElement.focus();
                            e.preventDefault();
                        }
                    } else {
                        if (document.activeElement === lastElement) {
                            firstElement.focus();
                            e.preventDefault();
                        }
                    }
                }
            });
        },

        addARIALabels: function() {
            // Add ARIA labels to buttons without text
            const iconButtons = document.querySelectorAll('button:not([aria-label]):empty, .btn-icon-only:not([aria-label])');
            iconButtons.forEach(button => {
                const icon = button.querySelector('i, svg');
                if (icon) {
                    const className = icon.className || '';
                    let label = 'Button';
                    
                    if (className.includes('cart')) label = 'Add to cart';
                    else if (className.includes('heart') || className.includes('favorite')) label = 'Add to favorites';
                    else if (className.includes('share')) label = 'Share';
                    else if (className.includes('close')) label = 'Close';
                    else if (className.includes('menu')) label = 'Menu';
                    
                    button.setAttribute('aria-label', label);
                }
            });
        },

        handleReducedMotion: function() {
            if (FeatureDetection.prefersReducedMotion()) {
                // Disable autoplay videos
                const videos = document.querySelectorAll('video[autoplay]');
                videos.forEach(video => {
                    video.removeAttribute('autoplay');
                });

                // Add reduced motion class
                document.documentElement.classList.add('reduce-motion');
            }
        }
    };

    // Performance Optimizations
    const PerformanceOptimizations = {
        init: function() {
            this.lazyLoadImages();
            this.optimizeAnimations();
            this.deferNonCriticalCSS();
        },

        lazyLoadImages: function() {
            if ('IntersectionObserver' in window) {
                const images = document.querySelectorAll('img[data-src]');
                const imageObserver = new IntersectionObserver((entries) => {
                    entries.forEach(entry => {
                        if (entry.isIntersecting) {
                            const img = entry.target;
                            img.src = img.dataset.src;
                            img.classList.remove('lazy');
                            imageObserver.unobserve(img);
                        }
                    });
                });

                images.forEach(img => imageObserver.observe(img));
            } else {
                // Fallback: load all images immediately
                const images = document.querySelectorAll('img[data-src]');
                images.forEach(img => {
                    img.src = img.dataset.src;
                    img.classList.remove('lazy');
                });
            }
        },

        optimizeAnimations: function() {
            // Use will-change property sparingly
            const animatedElements = document.querySelectorAll('.card, .btn-modern');
            
            animatedElements.forEach(element => {
                element.addEventListener('mouseenter', () => {
                    element.style.willChange = 'transform, box-shadow';
                });
                
                element.addEventListener('mouseleave', () => {
                    element.style.willChange = 'auto';
                });
            });
        },

        deferNonCriticalCSS: function() {
            // Convert non-critical CSS to load asynchronously
            const nonCriticalCSS = document.querySelectorAll('link[rel="stylesheet"][data-defer]');
            
            nonCriticalCSS.forEach(link => {
                link.media = 'print';
                link.onload = function() {
                    this.media = 'all';
                };
            });
        }
    };

    // Error Handling
    const ErrorHandling = {
        init: function() {
            this.handleCSSErrors();
            this.handleJSErrors();
        },

        handleCSSErrors: function() {
            // Check if critical CSS loaded
            const testElement = document.createElement('div');
            testElement.className = 'css-test';
            testElement.style.cssText = 'position: absolute; left: -9999px;';
            document.body.appendChild(testElement);

            const computedStyle = window.getComputedStyle(testElement);
            if (computedStyle.position !== 'absolute') {
                console.warn('Critical CSS may not have loaded properly');
                // Load fallback CSS
                this.loadFallbackCSS();
            }

            document.body.removeChild(testElement);
        },

        loadFallbackCSS: function() {
            const fallbackCSS = document.createElement('link');
            fallbackCSS.rel = 'stylesheet';
            fallbackCSS.href = '/static/css/fallback.css';
            document.head.appendChild(fallbackCSS);
        },

        handleJSErrors: function() {
            window.addEventListener('error', (event) => {
                console.error('JavaScript error:', event.error);
                // Gracefully degrade functionality
                document.documentElement.classList.add('js-error');
            });
        }
    };

    // Main Initialization
    const CrossBrowserSupport = {
        init: function() {
            // Wait for DOM to be ready
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', () => this.initializeFeatures());
            } else {
                this.initializeFeatures();
            }
        },

        initializeFeatures: function() {
            try {
                // Core feature detection and enhancement
                ProgressiveEnhancement.addFeatureClasses();
                ProgressiveEnhancement.addImageFormatClasses();
                
                // Load polyfills if needed
                const polyfillsLoaded = PolyfillManager.loadPolyfills();
                
                // Initialize features after polyfills load
                const initFeatures = () => {
                    ProgressiveEnhancement.enhanceCards();
                    ProgressiveEnhancement.enhanceButtons();
                    SmoothScrollPolyfill.init();
                    AccessibilityEnhancements.init();
                    PerformanceOptimizations.init();
                    ErrorHandling.init();
                    
                    // Initialize CSS Variables polyfill if loaded
                    if (window.cssVars) {
                        PolyfillManager.initCSSVarsPolyfill();
                    }
                };

                if (polyfillsLoaded) {
                    // Wait a bit for polyfills to load
                    setTimeout(initFeatures, 100);
                } else {
                    initFeatures();
                }

            } catch (error) {
                console.error('Cross-browser support initialization failed:', error);
                // Ensure basic functionality works
                document.documentElement.classList.add('js-error', 'fallback-mode');
            }
        }
    };

    // Initialize when script loads
    CrossBrowserSupport.init();

    // Expose utilities globally for debugging
    window.CrossBrowserSupport = {
        FeatureDetection,
        BrowserDetection,
        PolyfillManager,
        ProgressiveEnhancement
    };

})();
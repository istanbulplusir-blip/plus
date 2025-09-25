/**
 * Font Loading Optimization
 * Handles web font loading with fallbacks and performance optimization
 */

(function() {
  'use strict';

  // Font loading configuration
  const FONTS_CONFIG = {
    'Inter': {
      weights: [300, 400, 500, 600, 700, 800],
      display: 'swap',
      fallback: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    },
    'Poppins': {
      weights: [400, 500, 600, 700, 800],
      display: 'swap',
      fallback: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
    },
    'Vazir': {
      weights: [300, 400, 500, 700],
      display: 'swap',
      fallback: 'Tahoma, Arial, sans-serif'
    },
    'JetBrains Mono': {
      weights: [400, 500, 700],
      display: 'swap',
      fallback: 'Consolas, "Liberation Mono", Menlo, Courier, monospace'
    }
  };

  // Check if Font Loading API is supported
  const supportsFontLoading = 'fonts' in document;

  /**
   * Load fonts using Font Loading API
   */
  function loadFontsWithAPI() {
    const fontPromises = [];

    Object.entries(FONTS_CONFIG).forEach(([family, config]) => {
      config.weights.forEach(weight => {
        const fontFace = new FontFace(family, `url(https://fonts.googleapis.com/css2?family=${family.replace(' ', '+')}:wght@${weight}&display=swap)`, {
          weight: weight.toString(),
          display: config.display
        });

        fontPromises.push(
          fontFace.load().then(loadedFont => {
            document.fonts.add(loadedFont);
            return loadedFont;
          }).catch(error => {
            console.warn(`Failed to load font ${family} weight ${weight}:`, error);
          })
        );
      });
    });

    return Promise.allSettled(fontPromises);
  }

  /**
   * Fallback font loading using CSS
   */
  function loadFontsWithCSS() {
    // Create link elements for Google Fonts
    const googleFontsUrl = 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap';
    
    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = googleFontsUrl;
    link.crossOrigin = 'anonymous';
    
    // Add to head
    document.head.appendChild(link);

    // Load Vazir font separately
    const vazirLink = document.createElement('link');
    vazirLink.rel = 'stylesheet';
    vazirLink.href = 'https://cdn.jsdelivr.net/gh/rastikerdar/vazir-font@v30.1.0/dist/font-face.css';
    vazirLink.crossOrigin = 'anonymous';
    
    document.head.appendChild(vazirLink);

    return new Promise((resolve) => {
      link.onload = () => resolve();
      link.onerror = () => resolve(); // Still resolve to continue
    });
  }

  /**
   * Add font loading class to document
   */
  function addFontLoadingClass() {
    document.documentElement.classList.add('font-loading');
  }

  /**
   * Remove font loading class and add fonts loaded class
   */
  function addFontsLoadedClass() {
    document.documentElement.classList.remove('font-loading');
    document.documentElement.classList.add('fonts-loaded');
  }

  /**
   * Check if fonts are already cached
   */
  function areFontsCached() {
    try {
      return localStorage.getItem('fonts-loaded') === 'true';
    } catch (e) {
      return false;
    }
  }

  /**
   * Mark fonts as cached
   */
  function markFontsAsCached() {
    try {
      localStorage.setItem('fonts-loaded', 'true');
    } catch (e) {
      // Ignore localStorage errors
    }
  }

  /**
   * Initialize font loading
   */
  function initFontLoading() {
    // Add loading class immediately
    addFontLoadingClass();

    // If fonts are cached, remove loading class quickly
    if (areFontsCached()) {
      setTimeout(addFontsLoadedClass, 100);
      return;
    }

    // Load fonts
    const loadFonts = supportsFontLoading ? loadFontsWithAPI() : loadFontsWithCSS();

    loadFonts.then(() => {
      addFontsLoadedClass();
      markFontsAsCached();
    }).catch(() => {
      // Even if loading fails, remove loading class
      addFontsLoadedClass();
    });

    // Fallback timeout to prevent indefinite loading state
    setTimeout(() => {
      if (document.documentElement.classList.contains('font-loading')) {
        addFontsLoadedClass();
      }
    }, 3000);
  }

  /**
   * Preconnect to font domains for better performance
   */
  function addPreconnectLinks() {
    const domains = [
      'https://fonts.googleapis.com',
      'https://fonts.gstatic.com',
      'https://cdn.jsdelivr.net'
    ];

    domains.forEach(domain => {
      const link = document.createElement('link');
      link.rel = 'preconnect';
      link.href = domain;
      link.crossOrigin = 'anonymous';
      document.head.appendChild(link);
    });
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
      addPreconnectLinks();
      initFontLoading();
    });
  } else {
    addPreconnectLinks();
    initFontLoading();
  }

  // Handle page visibility changes to optimize font loading
  if ('visibilityState' in document) {
    document.addEventListener('visibilitychange', () => {
      if (document.visibilityState === 'visible' && !areFontsCached()) {
        initFontLoading();
      }
    });
  }

})();
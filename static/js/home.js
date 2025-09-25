/* Modern Home Page JavaScript */
/* Task 8: Add smooth scrolling effects and progressive content loading animations */

document.addEventListener('DOMContentLoaded', function() {
  // Initialize all home page functionality
  initSmoothScrolling();
  initProgressiveLoading();
  initParallaxEffects();
  initWishlistFunctionality();
  initHeroAnimations();
  initPerformanceOptimizations();
});

/**
 * Initialize smooth scrolling for navigation links
 */
function initSmoothScrolling() {
  // Smooth scrolling for hero scroll indicator
  const scrollIndicator = document.querySelector('.hero-scroll-indicator');
  if (scrollIndicator) {
    scrollIndicator.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector('#featured-categories');
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  }

  // Smooth scrolling for anchor links
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
      e.preventDefault();
      const target = document.querySelector(this.getAttribute('href'));
      if (target) {
        target.scrollIntoView({
          behavior: 'smooth',
          block: 'start'
        });
      }
    });
  });
}

/**
 * Initialize progressive content loading animations
 */
function initProgressiveLoading() {
  // Intersection Observer for progressive animations
  const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
  };

  const progressiveObserver = new IntersectionObserver(function(entries) {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Add animation class with delay based on element index
        const delay = Array.from(entry.target.parentNode.children).indexOf(entry.target) * 100;
        setTimeout(() => {
          entry.target.classList.add('animate-in');
        }, delay);
        
        // Stop observing once animated
        progressiveObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);

  // Observe all animatable elements
  const animatableElements = document.querySelectorAll(
    '.category-item, .product-item, .section-header, .cta-content'
  );
  
  animatableElements.forEach(el => {
    progressiveObserver.observe(el);
  });

  // Staggered animation for cards in the same row
  const cardRows = document.querySelectorAll('.categories-grid, .products-grid');
  cardRows.forEach(row => {
    const cards = row.querySelectorAll('.category-item, .product-item');
    cards.forEach((card, index) => {
      card.style.transitionDelay = `${index * 150}ms`;
    });
  });
}

/**
 * Initialize parallax effects
 */
function initParallaxEffects() {
  let ticking = false;

  function updateParallax() {
    const scrolled = window.pageYOffset;
    const heroBackground = document.querySelector('.hero-background');
    const heroParticles = document.querySelector('.hero-particles');
    
    if (heroBackground) {
      // Slower parallax for background
      heroBackground.style.transform = `translateY(${scrolled * 0.3}px)`;
    }
    
    if (heroParticles) {
      // Faster parallax for particles
      heroParticles.style.transform = `translateY(${scrolled * 0.5}px) rotate(${scrolled * 0.1}deg)`;
    }

    // Update scroll indicator opacity
    const scrollIndicator = document.querySelector('.hero-scroll-indicator');
    if (scrollIndicator) {
      const opacity = Math.max(0, 1 - (scrolled / window.innerHeight));
      scrollIndicator.style.opacity = opacity;
    }

    ticking = false;
  }

  function requestParallaxUpdate() {
    if (!ticking) {
      requestAnimationFrame(updateParallax);
      ticking = true;
    }
  }

  // Only enable parallax on devices that can handle it
  if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
    window.addEventListener('scroll', requestParallaxUpdate, { passive: true });
  }
}

/**
 * Initialize wishlist functionality
 */
function initWishlistFunctionality() {
  document.querySelectorAll('.btn-wishlist').forEach(btn => {
    btn.addEventListener('click', function(e) {
      e.preventDefault();
      e.stopPropagation();
      
      this.classList.toggle('active');
      const icon = this.querySelector('i');
      
      if (this.classList.contains('active')) {
        icon.classList.remove('bi-heart');
        icon.classList.add('bi-heart-fill');
        this.setAttribute('title', 'حذف از علاقه‌مندی‌ها');
        
        // Add to wishlist animation
        this.style.transform = 'scale(1.2)';
        setTimeout(() => {
          this.style.transform = '';
        }, 200);
      } else {
        icon.classList.remove('bi-heart-fill');
        icon.classList.add('bi-heart');
        this.setAttribute('title', 'افزودن به علاقه‌مندی‌ها');
      }

      // Store wishlist state in localStorage
      const productId = this.closest('.product-card').dataset.productId;
      if (productId) {
        updateWishlistStorage(productId, this.classList.contains('active'));
      }
    });
  });

  // Load wishlist state from localStorage
  loadWishlistState();
}

/**
 * Update wishlist storage
 */
function updateWishlistStorage(productId, isWishlisted) {
  let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
  
  if (isWishlisted && !wishlist.includes(productId)) {
    wishlist.push(productId);
  } else if (!isWishlisted) {
    wishlist = wishlist.filter(id => id !== productId);
  }
  
  localStorage.setItem('wishlist', JSON.stringify(wishlist));
}

/**
 * Load wishlist state from storage
 */
function loadWishlistState() {
  const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
  
  document.querySelectorAll('.product-card').forEach(card => {
    const productId = card.dataset.productId;
    const wishlistBtn = card.querySelector('.btn-wishlist');
    
    if (productId && wishlist.includes(productId) && wishlistBtn) {
      wishlistBtn.classList.add('active');
      const icon = wishlistBtn.querySelector('i');
      icon.classList.remove('bi-heart');
      icon.classList.add('bi-heart-fill');
      wishlistBtn.setAttribute('title', 'حذف از علاقه‌مندی‌ها');
    }
  });
}

/**
 * Initialize hero animations
 */
function initHeroAnimations() {
  const heroTitle = document.querySelector('.hero-title');
  const heroDescription = document.querySelector('.hero-description');
  const heroActions = document.querySelector('.hero-actions');
  const showcaseCards = document.querySelectorAll('.showcase-card');

  // Animate hero content on load
  if (heroTitle) {
    setTimeout(() => {
      heroTitle.style.opacity = '1';
      heroTitle.style.transform = 'translateY(0)';
    }, 300);
  }

  if (heroDescription) {
    setTimeout(() => {
      heroDescription.style.opacity = '1';
      heroDescription.style.transform = 'translateY(0)';
    }, 600);
  }

  if (heroActions) {
    setTimeout(() => {
      heroActions.style.opacity = '1';
      heroActions.style.transform = 'translateY(0)';
    }, 900);
  }

  // Animate showcase cards
  showcaseCards.forEach((card, index) => {
    setTimeout(() => {
      card.style.opacity = '1';
      card.style.transform = 'translateY(0) rotate(0deg)';
    }, 1200 + (index * 200));
  });

  // Set initial states
  [heroTitle, heroDescription, heroActions].forEach(el => {
    if (el) {
      el.style.opacity = '0';
      el.style.transform = 'translateY(30px)';
      el.style.transition = 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)';
    }
  });

  showcaseCards.forEach(card => {
    card.style.opacity = '0';
    card.style.transform = 'translateY(50px) rotate(-10deg)';
    card.style.transition = 'all 1s cubic-bezier(0.4, 0, 0.2, 1)';
  });
}

/**
 * Initialize performance optimizations
 */
function initPerformanceOptimizations() {
  // Lazy load images
  if ('IntersectionObserver' in window) {
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.classList.remove('lazy');
          observer.unobserve(img);
        }
      });
    });

    document.querySelectorAll('img[data-src]').forEach(img => {
      imageObserver.observe(img);
    });
  }

  // Smart preloading: only preload images that are actually visible and needed
  const smartPreload = () => {
    // Only preload hero section images if they're visible
    const heroImages = document.querySelectorAll('.hero-section img');
    heroImages.forEach(img => {
      if (img.src && img.offsetParent !== null && !img.hasAttribute('data-preloaded')) {
        const link = document.createElement('link');
        link.rel = 'preload';
        link.as = 'image';
        link.href = img.src;
        link.setAttribute('data-preloaded', 'true');
        document.head.appendChild(link);
        img.setAttribute('data-preloaded', 'true');
      }
    });
  };

  // Run smart preload after DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', smartPreload);
  } else {
    smartPreload();
  }

  // Optimize scroll performance
  let scrollTimeout;
  window.addEventListener('scroll', () => {
    document.body.classList.add('scrolling');
    
    clearTimeout(scrollTimeout);
    scrollTimeout = setTimeout(() => {
      document.body.classList.remove('scrolling');
    }, 100);
  }, { passive: true });
}

/**
 * Handle card hover effects
 */
function initCardHoverEffects() {
  const cards = document.querySelectorAll('.card');
  
  cards.forEach(card => {
    card.addEventListener('mouseenter', function() {
      this.classList.add('card-hovering');
    });
    
    card.addEventListener('mouseleave', function() {
      this.classList.remove('card-hovering');
    });
  });
}

/**
 * Initialize responsive behavior
 */
function initResponsiveBehavior() {
  const mediaQuery = window.matchMedia('(max-width: 768px)');
  
  function handleResponsiveChange(e) {
    const heroActions = document.querySelector('.hero-actions');
    const ctaContent = document.querySelector('.cta-content');
    
    if (e.matches) {
      // Mobile optimizations
      if (heroActions) {
        heroActions.style.justifyContent = 'center';
      }
      if (ctaContent) {
        ctaContent.style.textAlign = 'center';
      }
    } else {
      // Desktop optimizations
      if (heroActions) {
        heroActions.style.justifyContent = 'flex-start';
      }
      if (ctaContent) {
        ctaContent.style.textAlign = 'left';
      }
    }
  }
  
  mediaQuery.addListener(handleResponsiveChange);
  handleResponsiveChange(mediaQuery);
}

/**
 * Initialize accessibility enhancements
 */
function initAccessibilityEnhancements() {
  // Add focus management for keyboard navigation
  const focusableElements = document.querySelectorAll(
    'a, button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
  );
  
  focusableElements.forEach(element => {
    element.addEventListener('focus', function() {
      this.classList.add('keyboard-focused');
    });
    
    element.addEventListener('blur', function() {
      this.classList.remove('keyboard-focused');
    });
  });

  // Announce dynamic content changes to screen readers
  const announcer = document.createElement('div');
  announcer.setAttribute('aria-live', 'polite');
  announcer.setAttribute('aria-atomic', 'true');
  announcer.className = 'sr-only';
  document.body.appendChild(announcer);

  // Announce when sections come into view
  const sectionObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const sectionTitle = entry.target.querySelector('.section-title');
        if (sectionTitle) {
          announcer.textContent = `بخش ${sectionTitle.textContent} نمایش داده شد`;
        }
      }
    });
  }, { threshold: 0.5 });

  document.querySelectorAll('section').forEach(section => {
    sectionObserver.observe(section);
  });
}

// Initialize all functionality when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  initCardHoverEffects();
  initResponsiveBehavior();
  initAccessibilityEnhancements();
});

// Handle page visibility changes for performance
document.addEventListener('visibilitychange', function() {
  if (document.hidden) {
    // Pause animations when page is not visible
    document.body.classList.add('page-hidden');
  } else {
    // Resume animations when page becomes visible
    document.body.classList.remove('page-hidden');
  }
});

// Export functions for potential external use
window.HomePageJS = {
  initSmoothScrolling,
  initProgressiveLoading,
  initParallaxEffects,
  initWishlistFunctionality,
  updateWishlistStorage,
  loadWishlistState
};
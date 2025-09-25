/**
 * Modern Card Components JavaScript
 * Handles enhanced interactions, loading states, and animations
 */

class ModernCards {
  constructor() {
    this.init();
  }

  init() {
    this.setupImageLoading();
    this.setupHoverEffects();
    this.setupAccessibility();
    this.setupIntersectionObserver();
  }

  /**
   * Setup image loading states and error handling
   */
  setupImageLoading() {
    const images = document.querySelectorAll('.card-img-top');
    
    images.forEach(img => {
      // Add loading class initially
      img.classList.add('card-img-loading');
      
      // Handle successful load
      img.addEventListener('load', () => {
        img.classList.remove('card-img-loading');
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.3s ease-in-out';
        
        // Fade in the image
        requestAnimationFrame(() => {
          img.style.opacity = '1';
        });
      });
      
      // Handle load error
      img.addEventListener('error', () => {
        img.classList.remove('card-img-loading');
        img.src = '/static/img/no-image.png';
        img.alt = 'تصویر موجود نیست';
      });
    });
  }

  /**
   * Setup enhanced hover effects
   */
  setupHoverEffects() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
      // Add mouse enter effect
      card.addEventListener('mouseenter', (e) => {
        this.handleCardHover(e.target, true);
      });
      
      // Add mouse leave effect
      card.addEventListener('mouseleave', (e) => {
        this.handleCardHover(e.target, false);
      });
      
      // Add focus effects for keyboard navigation
      card.addEventListener('focusin', (e) => {
        this.handleCardHover(e.currentTarget, true);
      });
      
      card.addEventListener('focusout', (e) => {
        // Only remove hover if focus is leaving the card entirely
        if (!e.currentTarget.contains(e.relatedTarget)) {
          this.handleCardHover(e.currentTarget, false);
        }
      });
    });
  }

  /**
   * Handle card hover effects
   */
  handleCardHover(card, isHovering) {
    const image = card.querySelector('.card-img-top');
    const priceDisplay = card.querySelector('.price-display');
    
    if (isHovering) {
      // Add hover class for CSS animations
      card.classList.add('card-hovering');
      
      // Animate price display
      if (priceDisplay) {
        priceDisplay.style.transform = 'scale(1.05)';
      }
      
      // Add subtle parallax effect to image
      if (image) {
        image.style.transform = 'scale(1.05) translateZ(0)';
      }
    } else {
      // Remove hover effects
      card.classList.remove('card-hovering');
      
      if (priceDisplay) {
        priceDisplay.style.transform = 'scale(1)';
      }
      
      if (image) {
        image.style.transform = 'scale(1) translateZ(0)';
      }
    }
  }

  /**
   * Setup accessibility improvements
   */
  setupAccessibility() {
    const cards = document.querySelectorAll('.card');
    
    cards.forEach(card => {
      // Add ARIA labels for better screen reader support
      const title = card.querySelector('.card-title');
      const price = card.querySelector('.price-display');
      const link = card.querySelector('.btn');
      
      if (title && link) {
        const productName = title.textContent.trim();
        const priceText = price ? price.textContent.trim() : '';
        
        link.setAttribute('aria-label', 
          `${productName}${priceText ? ' - ' + priceText : ''} - مشاهده جزئیات`
        );
      }
      
      // Add keyboard navigation support
      card.setAttribute('tabindex', '0');
      card.setAttribute('role', 'article');
      
      // Handle keyboard activation
      card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          const link = card.querySelector('.btn');
          if (link) {
            link.click();
          }
        }
      });
    });
  }

  /**
   * Setup Intersection Observer for scroll animations
   */
  setupIntersectionObserver() {
    // Check if user prefers reduced motion
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    
    if (prefersReducedMotion) {
      return; // Skip animations if user prefers reduced motion
    }

    const cards = document.querySelectorAll('.card');
    
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('card-animate-in');
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);
    
    cards.forEach((card, index) => {
      // Add initial animation state
      card.style.opacity = '0';
      card.style.transform = 'translateY(30px)';
      card.style.transition = `opacity 0.6s ease-out ${index * 0.1}s, transform 0.6s ease-out ${index * 0.1}s`;
      
      observer.observe(card);
    });
  }

  /**
   * Handle price formatting for better display
   */
  formatPrices() {
    const priceElements = document.querySelectorAll('.price-display');
    
    priceElements.forEach(element => {
      const priceText = element.textContent.trim();
      const priceNumber = priceText.replace(/[^\d]/g, '');
      
      if (priceNumber) {
        const formattedPrice = new Intl.NumberFormat('fa-IR').format(priceNumber);
        element.textContent = formattedPrice + ' تومان';
      }
    });
  }

  /**
   * Add loading skeleton for dynamic content
   */
  addLoadingSkeleton(container) {
    const skeleton = document.createElement('div');
    skeleton.className = 'card card-skeleton';
    skeleton.innerHTML = `
      <div class="card-img-top card-img-loading"></div>
      <div class="card-body">
        <div class="skeleton-line skeleton-title"></div>
        <div class="skeleton-line skeleton-text"></div>
        <div class="skeleton-line skeleton-text short"></div>
        <div class="skeleton-line skeleton-price"></div>
      </div>
    `;
    
    container.appendChild(skeleton);
    return skeleton;
  }

  /**
   * Remove loading skeleton
   */
  removeLoadingSkeleton(skeleton) {
    if (skeleton && skeleton.parentNode) {
      skeleton.style.opacity = '0';
      skeleton.style.transform = 'scale(0.95)';
      
      setTimeout(() => {
        skeleton.remove();
      }, 300);
    }
  }
}

// CSS for scroll animations
const animationCSS = `
  .card-animate-in {
    opacity: 1 !important;
    transform: translateY(0) !important;
  }
  
  .card-skeleton {
    pointer-events: none;
    background: rgba(255, 255, 255, 0.05);
  }
  
  .skeleton-line {
    height: 1rem;
    background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
    background-size: 200px 100%;
    animation: shimmer 1.5s infinite;
    border-radius: 4px;
    margin-bottom: 0.5rem;
  }
  
  .skeleton-title {
    height: 1.5rem;
    width: 80%;
  }
  
  .skeleton-text {
    width: 100%;
  }
  
  .skeleton-text.short {
    width: 60%;
  }
  
  .skeleton-price {
    height: 1.25rem;
    width: 40%;
    background: linear-gradient(90deg, #667eea 25%, #764ba2 50%, #667eea 75%);
    background-size: 200px 100%;
  }
`;

// Add animation CSS to document
const style = document.createElement('style');
style.textContent = animationCSS;
document.head.appendChild(style);

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  new ModernCards();
});

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
  module.exports = ModernCards;
}
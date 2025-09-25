/**
 * Product Detail Page JavaScript
 * Handles interactions and functionality for the product detail page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize product detail functionality
    initProductDetail();
});

function initProductDetail() {
    // Initialize image gallery
    initImageGallery();
    
    // Initialize add to cart functionality
    initAddToCart();
    
    // Initialize related products
    initRelatedProducts();
    
    // Initialize animations
    initScrollAnimations();
    
    // Initialize quantity controls
    initQuantityControls();
}

/**
 * Initialize image gallery functionality
 */
function initImageGallery() {
    const mainImage = document.querySelector('.product-main-image');
    const thumbnails = document.querySelectorAll('.product-thumbnail');
    const modal = createImageModal();
    
    if (mainImage && thumbnails.length > 0) {
        // Add click event to main image
        mainImage.addEventListener('click', function() {
            openImageModal(this.src, this.alt);
        });
        
        // Add click events to thumbnails
        thumbnails.forEach((thumbnail, index) => {
            thumbnail.addEventListener('click', function() {
                // Update main image
                mainImage.src = this.src;
                mainImage.alt = this.alt;
                
                // Update active thumbnail
                thumbnails.forEach(t => t.classList.remove('active'));
                this.classList.add('active');
                
                // Add smooth transition
                mainImage.style.opacity = '0';
                setTimeout(() => {
                    mainImage.style.opacity = '1';
                }, 150);
            });
            
            // Set first thumbnail as active
            if (index === 0) {
                thumbnail.classList.add('active');
            }
        });
    }
}

/**
 * Create image modal for full-size viewing
 */
function createImageModal() {
    const modal = document.createElement('div');
    modal.className = 'image-modal';
    modal.innerHTML = `
        <span class="image-modal-close">&times;</span>
        <img class="image-modal-content" id="modal-image">
    `;
    
    document.body.appendChild(modal);
    
    // Close modal events
    const closeBtn = modal.querySelector('.image-modal-close');
    closeBtn.addEventListener('click', closeImageModal);
    
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeImageModal();
        }
    });
    
    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && modal.style.display === 'block') {
            closeImageModal();
        }
    });
    
    return modal;
}

/**
 * Open image modal
 */
function openImageModal(src, alt) {
    const modal = document.querySelector('.image-modal');
    const modalImg = document.getElementById('modal-image');
    
    modal.style.display = 'block';
    modalImg.src = src;
    modalImg.alt = alt;
    
    // Prevent body scroll
    document.body.style.overflow = 'hidden';
}

/**
 * Close image modal
 */
function closeImageModal() {
    const modal = document.querySelector('.image-modal');
    modal.style.display = 'none';
    
    // Restore body scroll
    document.body.style.overflow = 'auto';
}

/**
 * Initialize add to cart functionality
 */
function initAddToCart() {
    const addToCartForm = document.querySelector('form[action*="cart_item_create"]');
    const addToCartButton = document.querySelector('.add-to-cart-button');
    
    if (addToCartForm && addToCartButton) {
        addToCartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Show loading state
            const originalText = addToCartButton.innerHTML;
            addToCartButton.innerHTML = '<i class="bi bi-hourglass-split"></i> در حال افزودن...';
            addToCartButton.disabled = true;
            
            // Get form data
            const formData = new FormData(this);
            
            // Submit form
            fetch(this.action, {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken')
                }
            })
            .then(response => {
                if (response.ok) {
                    // Show success message using enhanced cart notification
                    if (typeof showCartNotification === 'function') {
                        showCartNotification('محصول با موفقیت به سبد خرید اضافه شد!', 'success');
                    } else {
                        showNotification('محصول با موفقیت به سبد خرید اضافه شد!', 'success');
                    }
                    
                    // Update cart count with enhanced animation
                    updateCartCount();
                    
                    // Trigger cart bounce animation
                    if (typeof triggerCartBounceAnimation === 'function') {
                        triggerCartBounceAnimation();
                    }
                    
                    // Reset form
                    this.reset();
                    const quantityInput = document.querySelector('input[name="quantity"]');
                    if (quantityInput) {
                        quantityInput.value = '1';
                    }
                } else {
                    throw new Error('خطا در افزودن محصول به سبد خرید');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showNotification('خطا در افزودن محصول به سبد خرید', 'error');
            })
            .finally(() => {
                // Restore button state
                addToCartButton.innerHTML = originalText;
                addToCartButton.disabled = false;
            });
        });
    }
}

/**
 * Initialize related products interactions
 */
function initRelatedProducts() {
    const relatedProductCards = document.querySelectorAll('.related-product-card');
    
    relatedProductCards.forEach(card => {
        // Add hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
        
        // Add click tracking
        const productLink = card.querySelector('.related-product-button');
        if (productLink) {
            productLink.addEventListener('click', function(e) {
                const productTitle = card.querySelector('.related-product-title')?.textContent;
                if (productTitle) {
                    console.log('Related product clicked:', productTitle);
                }
            });
        }
    });
}

/**
 * Initialize scroll animations
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Observe elements
    document.querySelectorAll('.product-main-section, .related-products-section').forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(element);
    });
}

/**
 * Initialize quantity controls
 */
function initQuantityControls() {
    const quantityInput = document.querySelector('input[name="quantity"]');
    
    if (quantityInput) {
        // Add increment/decrement buttons
        const quantityContainer = document.createElement('div');
        quantityContainer.className = 'quantity-controls';
        quantityContainer.innerHTML = `
            <button type="button" class="quantity-btn quantity-decrease">-</button>
            <input type="number" name="quantity" value="1" min="1" max="${quantityInput.max || 999}" class="quantity-input">
            <button type="button" class="quantity-btn quantity-increase">+</button>
        `;
        
        quantityInput.parentNode.replaceChild(quantityContainer, quantityInput);
        
        // Add event listeners
        const decreaseBtn = quantityContainer.querySelector('.quantity-decrease');
        const increaseBtn = quantityContainer.querySelector('.quantity-increase');
        const newQuantityInput = quantityContainer.querySelector('.quantity-input');
        
        decreaseBtn.addEventListener('click', function() {
            const currentValue = parseInt(newQuantityInput.value);
            if (currentValue > 1) {
                newQuantityInput.value = currentValue - 1;
            }
        });
        
        increaseBtn.addEventListener('click', function() {
            const currentValue = parseInt(newQuantityInput.value);
            const maxValue = parseInt(newQuantityInput.max);
            if (currentValue < maxValue) {
                newQuantityInput.value = currentValue + 1;
            }
        });
        
        // Validate input
        newQuantityInput.addEventListener('input', function() {
            const value = parseInt(this.value);
            const min = parseInt(this.min);
            const max = parseInt(this.max);
            
            if (value < min) {
                this.value = min;
            } else if (value > max) {
                this.value = max;
            }
        });
    }
}

/**
 * Show notification message
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--success-color)' : 'var(--danger-color)'};
        color: white;
        padding: 15px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
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

/**
 * Update cart count in navigation
 */
function updateCartCount() {
    // This would typically make an AJAX call to get updated cart count
    // For now, we'll just show a visual feedback
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
        cartLink.style.animation = 'pulse 0.5s ease-in-out';
        setTimeout(() => {
            cartLink.style.animation = '';
        }, 500);
    }
}

/**
 * Share product functionality
 */
function shareProduct() {
    if (navigator.share) {
        navigator.share({
            title: document.querySelector('.product-title')?.textContent || 'محصول',
            text: document.querySelector('.product-description')?.textContent || '',
            url: window.location.href
        });
    } else {
        // Fallback: copy to clipboard
        navigator.clipboard.writeText(window.location.href).then(() => {
            showNotification('لینک محصول کپی شد!', 'success');
        });
    }
}

/**
 * Add to wishlist functionality
 */
function addToWishlist() {
    // This would typically make an AJAX call to add/remove from wishlist
    showNotification('محصول به لیست علاقه‌مندی‌ها اضافه شد!', 'success');
}

// Add CSS for animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideInRight {
        from { transform: translateX(100%); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    
    @keyframes slideOutRight {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(100%); opacity: 0; }
    }
    
    @keyframes pulse {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    
    .quantity-controls {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 15px;
    }
    
    .quantity-btn {
        width: 40px;
        height: 40px;
        border: 1px solid var(--border-color);
        background: var(--background-primary);
        color: var(--text-primary);
        border-radius: 6px;
        cursor: pointer;
        font-weight: bold;
        transition: all 0.2s ease;
    }
    
    .quantity-btn:hover {
        background: var(--primary-color);
        color: var(--text-on-primary);
        border-color: var(--primary-color);
    }
    
    .quantity-input {
        width: 80px;
        text-align: center;
        border: 1px solid var(--border-color);
        border-radius: 6px;
        padding: 8px;
        font-weight: 600;
    }
`;
document.head.appendChild(style);

// Export functions for global access
window.ProductDetail = {
    shareProduct,
    addToWishlist,
    openImageModal,
    closeImageModal
};

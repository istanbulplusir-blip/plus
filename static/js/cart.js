function updateCartCount() {
    fetch('/api/cart/count/', {
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        const count = data.count || 0;
        
        // Update cart badge in navbar
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            cartBadge.textContent = count;
            
            // Show/hide badge based on count
            if (count > 0) {
                cartBadge.style.display = 'flex';
                cartBadge.parentElement.classList.add('has-items');
            } else {
                cartBadge.style.display = 'none';
                cartBadge.parentElement.classList.remove('has-items');
            }
            
            // Trigger animation
            cartBadge.classList.remove('updated');
            setTimeout(() => {
                cartBadge.classList.add('updated');
            }, 10);
        }
        
        // Update cart count element if exists
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = count;
        }
        
        // Update ModernNavigation if available
        if (window.modernNavigation && typeof window.modernNavigation.updateCartBadge === 'function') {
            window.modernNavigation.updateCartBadge(count);
        }
        
        // Update aria-label for accessibility
        const cartLink = document.querySelector('.cart-link');
        if (cartLink) {
            const label = count > 0 ? `سبد خرید - ${count} آیتم` : 'سبد خرید';
            cartLink.setAttribute('aria-label', label);
        }
        
        // Trigger custom event for other components
        window.dispatchEvent(new CustomEvent('cartUpdated', { 
            detail: { count: count } 
        }));
    })
    .catch(error => {
        console.error('Error updating cart count:', error);
        
        // Fallback: set count to 0
        const cartBadge = document.querySelector('.cart-badge');
        if (cartBadge) {
            cartBadge.textContent = '0';
            cartBadge.style.display = 'none';
            cartBadge.parentElement.classList.remove('has-items');
        }
        
        const cartCountElement = document.getElementById('cart-count');
        if (cartCountElement) {
            cartCountElement.textContent = '0';
        }
    });
}

// Update cart count when page loads
document.addEventListener('DOMContentLoaded', updateCartCount);

// Function to add product to cart with enhanced feedback
function addToCart(productId, quantity = 1, showNotification = true) {
    // Show loading state on cart icon
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
        cartLink.classList.add('loading');
    }
    
    // Dispatch cart loading event
    window.dispatchEvent(new CustomEvent('cartLoading', { 
        detail: { loading: true } 
    }));
    
    return fetch('/api/cart/items/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update cart count with animation
            updateCartCount();
            
            // Show success notification
            if (showNotification) {
                showCartNotification('محصول با موفقیت به سبد خرید اضافه شد!', 'success');
            }
            
            // Trigger cart icon bounce animation
            triggerCartBounceAnimation();
            
            return data;
        } else {
            throw new Error(data.error || 'خطا در افزودن محصول به سبد خرید.');
        }
    })
    .catch(error => {
        console.error('Error adding to cart:', error);
        
        if (showNotification) {
            showCartNotification('خطا در افزودن محصول به سبد خرید.', 'error');
        }
        
        throw error;
    })
    .finally(() => {
        // Remove loading state
        if (cartLink) {
            cartLink.classList.remove('loading');
        }
        
        // Dispatch cart loading event
        window.dispatchEvent(new CustomEvent('cartLoading', { 
            detail: { loading: false } 
        }));
    });
}

// Enhanced notification system for cart operations
function showCartNotification(message, type = 'info') {
    // Use ModernAlerts if available
    if (window.ModernAlerts) {
        window.ModernAlerts[type](message, type === 'success' ? 'موفقیت' : 'خطا');
        return;
    }
    
    // Fallback to custom notification
    const notification = document.createElement('div');
    notification.className = `cart-notification cart-notification-${type}`;
    notification.innerHTML = `
        <div class="cart-notification-content">
            <i class="bi bi-${type === 'success' ? 'check-circle' : 'exclamation-circle'}"></i>
            <span>${message}</span>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Show notification
    setTimeout(() => {
        notification.classList.add('show');
    }, 10);
    
    // Hide notification after 3 seconds
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => {
            document.body.removeChild(notification);
        }, 300);
    }, 3000);
}

// Trigger bounce animation on cart icon
function triggerCartBounceAnimation() {
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
        cartLink.classList.add('bounce');
        setTimeout(() => {
            cartLink.classList.remove('bounce');
        }, 600);
    }
}

// Enhanced cart icon loading state
function setCartLoadingState(isLoading) {
    const cartLink = document.querySelector('.cart-link');
    if (cartLink) {
        if (isLoading) {
            cartLink.classList.add('loading');
        } else {
            cartLink.classList.remove('loading');
        }
    }
}

// Helper function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
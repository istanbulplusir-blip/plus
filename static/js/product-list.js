/**
 * Modern Product List Page JavaScript
 * Enhanced functionality aligned with product detail page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize modern product list functionality
    initModernProductList();
});

function initModernProductList() {
    // Initialize scroll animations
    initScrollAnimations();
    
    // Initialize category filters
    initCategoryFilters();
    
    // Initialize product cards
    initProductCards();
    
    // Initialize pagination
    initPagination();
    
    // Initialize wishlist functionality
    initWishlistFunctionality();
    
    // Initialize search functionality
    initSearchFunctionality();
    
    // Initialize sort functionality
    initSortFunctionality();
    
    // Initialize performance optimizations
    initPerformanceOptimizations();
}

/**
 * Initialize scroll animations for modern design
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
                entry.target.classList.add('animate-in');
            }
        });
    }, observerOptions);

    // Observe all animatable elements
    const animatableElements = document.querySelectorAll(
        '.scroll-fade-up, .product-item, .filter-sidebar, .products-content'
    );
    
    animatableElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
        observer.observe(element);
    });

    // Staggered animation for product cards
    const productItems = document.querySelectorAll('.product-item');
    productItems.forEach((item, index) => {
        item.style.transitionDelay = `${index * 0.1}s`;
    });
}

/**
 * Initialize category filter interactions with modern effects
 */
function initCategoryFilters() {
    const categoryLinks = document.querySelectorAll('.category-link');
    
    categoryLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add loading state with modern animation
            const container = document.querySelector('.products-grid');
            if (container) {
                container.style.opacity = '0.5';
                container.style.pointerEvents = 'none';
                container.style.transform = 'scale(0.98)';
            }
            
            // Remove active class from all links
            categoryLinks.forEach(l => l.classList.remove('active'));
            
            // Add active class to clicked link with animation
            this.classList.add('active');
            this.style.transform = 'scale(1.05)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 200);
            
            // Reset container state after navigation
            setTimeout(() => {
                if (container) {
                    container.style.opacity = '1';
                    container.style.pointerEvents = 'auto';
                    container.style.transform = 'scale(1)';
                }
            }, 500);
        });
    });
}

/**
 * Initialize product card interactions with modern effects
 */
function initProductCards() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        // Enhanced hover effects
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
            this.style.zIndex = '10';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
            this.style.zIndex = '1';
        });
        
        // Add click tracking with modern analytics
        const productLink = card.querySelector('a[href*="product_detail"]');
        if (productLink) {
            productLink.addEventListener('click', function(e) {
                const productTitle = card.querySelector('.card-title')?.textContent;
                const productPrice = card.querySelector('.price-display')?.textContent;
                
                if (productTitle) {
                    // Enhanced product view tracking
                    console.log('Product viewed:', {
                        title: productTitle,
                        price: productPrice,
                        timestamp: new Date().toISOString()
                    });
                }
            });
        }
        
        // Add keyboard navigation support
        card.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                const link = this.querySelector('a[href*="product_detail"]');
                if (link) {
                    link.click();
                }
            }
        });
        
        // Make cards focusable
        card.setAttribute('tabindex', '0');
    });
}

/**
 * Initialize pagination with modern interactions
 */
function initPagination() {
    const paginationLinks = document.querySelectorAll('.pagination .page-link');
    
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            // Add loading state with modern animation
            const container = document.querySelector('.products-grid');
            if (container) {
                container.style.opacity = '0.5';
                container.style.pointerEvents = 'none';
                container.style.transform = 'scale(0.98)';
            }
            
            // Show loading indicator
            showLoadingIndicator();
            
            // Add click animation
            this.style.transform = 'scale(0.95)';
            setTimeout(() => {
                this.style.transform = 'scale(1)';
            }, 150);
        });
    });
}

/**
 * Initialize wishlist functionality
 */
function initWishlistFunctionality() {
    const wishlistBtns = document.querySelectorAll('.btn-wishlist');
    
    wishlistBtns.forEach(btn => {
        btn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const icon = this.querySelector('i');
            const isActive = this.classList.contains('active');
            
            if (isActive) {
                this.classList.remove('active');
                icon.classList.remove('bi-heart-fill');
                icon.classList.add('bi-heart');
                this.setAttribute('title', 'افزودن به علاقه‌مندی‌ها');
                
                // Remove animation
                this.style.transform = 'scale(0.9)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            } else {
                this.classList.add('active');
                icon.classList.remove('bi-heart');
                icon.classList.add('bi-heart-fill');
                this.setAttribute('title', 'حذف از علاقه‌مندی‌ها');
                
                // Add animation
                this.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 200);
                
                // Show notification
                showNotification('محصول به لیست علاقه‌مندی‌ها اضافه شد!', 'success');
            }
            
            // Store wishlist state
            const productCard = this.closest('.product-card');
            const productTitle = productCard?.querySelector('.card-title')?.textContent;
            if (productTitle) {
                updateWishlistStorage(productTitle, !isActive);
            }
        });
    });
    
    // Load wishlist state from localStorage
    loadWishlistState();
}

/**
 * Initialize search functionality
 */
function initSearchFunctionality() {
    // Create search input if it doesn't exist
    const filterSidebar = document.querySelector('.filter-sidebar');
    if (filterSidebar && !document.querySelector('.search-input')) {
        const searchSection = document.createElement('div');
        searchSection.className = 'filter-section';
        searchSection.innerHTML = `
            <h4 class="filter-section-title">جستجو</h4>
            <div class="search-container">
                <input type="text" class="search-input" placeholder="جستجو در محصولات..." />
                <button class="search-btn" type="button">
                    <i class="bi bi-search"></i>
                </button>
            </div>
        `;
        
        filterSidebar.insertBefore(searchSection, filterSidebar.firstChild);
        
        // Add search functionality
        const searchInput = searchSection.querySelector('.search-input');
        const searchBtn = searchSection.querySelector('.search-btn');
        
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length > 0) {
                searchProducts(query);
            } else {
                showAllProducts();
            }
        });
        
        searchBtn.addEventListener('click', function() {
            const query = searchInput.value.trim();
            if (query.length > 0) {
                searchProducts(query);
            }
        });
    }
}

/**
 * Initialize sort functionality
 */
function initSortFunctionality() {
    // Create sort dropdown if it doesn't exist
    const productsContent = document.querySelector('.products-content');
    if (productsContent && !document.querySelector('.sort-dropdown')) {
        const sortContainer = document.createElement('div');
        sortContainer.className = 'sort-container';
        sortContainer.innerHTML = `
            <div class="sort-dropdown">
                <label for="sort-select">مرتب‌سازی:</label>
                <select id="sort-select" class="sort-select">
                    <option value="default">پیش‌فرض</option>
                    <option value="name">نام (الف-ی)</option>
                    <option value="price-low">قیمت (کم به زیاد)</option>
                    <option value="price-high">قیمت (زیاد به کم)</option>
                </select>
            </div>
        `;
        
        productsContent.insertBefore(sortContainer, productsContent.firstChild);
        
        // Add sort functionality
        const sortSelect = sortContainer.querySelector('.sort-select');
        sortSelect.addEventListener('change', function() {
            const sortBy = this.value;
            if (sortBy !== 'default') {
                sortProducts(sortBy);
            }
        });
    }
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
                    if (img.dataset.src) {
                        img.src = img.dataset.src;
                        img.classList.remove('lazy');
                        observer.unobserve(img);
                    }
                }
            });
        });

        document.querySelectorAll('img[data-src]').forEach(img => {
            imageObserver.observe(img);
        });
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
 * Show loading indicator with modern design
 */
function showLoadingIndicator() {
    const container = document.querySelector('.products-grid');
    if (container) {
        const loader = document.createElement('div');
        loader.className = 'loading-indicator';
        loader.innerHTML = `
            <div class="loading-spinner">
                <div class="spinner"></div>
                <span>در حال بارگذاری...</span>
            </div>
        `;
        loader.style.cssText = `
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            z-index: 1000;
            background: var(--surface-glass);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--border-glass);
            border-radius: var(--radius-xl);
            padding: var(--space-6);
            box-shadow: var(--shadow-glass);
        `;
        
        container.style.position = 'relative';
        container.appendChild(loader);
    }
}

/**
 * Hide loading indicator
 */
function hideLoadingIndicator() {
    const loader = document.querySelector('.loading-indicator');
    if (loader) {
        loader.style.opacity = '0';
        loader.style.transform = 'translate(-50%, -50%) scale(0.8)';
        setTimeout(() => {
            loader.remove();
        }, 300);
    }
}

/**
 * Show notification with modern design
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
    
    // Add modern styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        background: ${type === 'success' ? 'var(--color-success)' : 'var(--color-error)'};
        color: white;
        padding: 15px 20px;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-lg);
        z-index: 1000;
        animation: slideInRight 0.3s ease-out;
        backdrop-filter: var(--backdrop-blur);
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
 * Update wishlist storage
 */
function updateWishlistStorage(productTitle, isWishlisted) {
    let wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    
    if (isWishlisted && !wishlist.includes(productTitle)) {
        wishlist.push(productTitle);
    } else if (!isWishlisted) {
        wishlist = wishlist.filter(title => title !== productTitle);
    }
    
    localStorage.setItem('wishlist', JSON.stringify(wishlist));
}

/**
 * Load wishlist state from storage
 */
function loadWishlistState() {
    const wishlist = JSON.parse(localStorage.getItem('wishlist') || '[]');
    
    document.querySelectorAll('.product-card').forEach(card => {
        const productTitle = card.querySelector('.card-title')?.textContent;
        const wishlistBtn = card.querySelector('.btn-wishlist');
        
        if (productTitle && wishlist.includes(productTitle) && wishlistBtn) {
            wishlistBtn.classList.add('active');
            const icon = wishlistBtn.querySelector('i');
            icon.classList.remove('bi-heart');
            icon.classList.add('bi-heart-fill');
            wishlistBtn.setAttribute('title', 'حذف از علاقه‌مندی‌ها');
        }
    });
}

/**
 * Search products with modern filtering
 */
function searchProducts(query) {
    const productCards = document.querySelectorAll('.product-card');
    const searchTerm = query.toLowerCase();
    let visibleCount = 0;
    
    productCards.forEach((card, index) => {
        const title = card.querySelector('.card-title')?.textContent.toLowerCase();
        const description = card.querySelector('.card-text')?.textContent.toLowerCase();
        const categories = Array.from(card.querySelectorAll('.product-category-tag'))
            .map(tag => tag.textContent.toLowerCase());
        
        const isMatch = title?.includes(searchTerm) || 
                       description?.includes(searchTerm) ||
                       categories.some(cat => cat.includes(searchTerm));
        
        if (isMatch) {
            card.style.display = 'block';
            card.style.animation = `fadeInUp 0.3s ease-out ${index * 0.05}s both`;
            visibleCount++;
        } else {
            card.style.display = 'none';
        }
    });
    
    // Show search results count
    showSearchResults(visibleCount, query);
}

/**
 * Show all products
 */
function showAllProducts() {
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach((card, index) => {
        card.style.display = 'block';
        card.style.animation = `fadeInUp 0.3s ease-out ${index * 0.05}s both`;
    });
    
    // Hide search results
    hideSearchResults();
}

/**
 * Show search results count
 */
function showSearchResults(count, query) {
    let resultsDiv = document.querySelector('.search-results');
    if (!resultsDiv) {
        resultsDiv = document.createElement('div');
        resultsDiv.className = 'search-results';
        document.querySelector('.products-content').insertBefore(
            resultsDiv, 
            document.querySelector('.products-grid')
        );
    }
    
    resultsDiv.innerHTML = `
        <div class="search-results-content">
            <i class="bi bi-search"></i>
            <span>${count} نتیجه برای "${query}" یافت شد</span>
            <button class="clear-search-btn" onclick="clearSearch()">
                <i class="bi bi-x"></i>
                پاک کردن
            </button>
        </div>
    `;
    resultsDiv.style.display = 'block';
}

/**
 * Hide search results
 */
function hideSearchResults() {
    const resultsDiv = document.querySelector('.search-results');
    if (resultsDiv) {
        resultsDiv.style.display = 'none';
    }
}

/**
 * Clear search
 */
function clearSearch() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        searchInput.value = '';
        showAllProducts();
    }
}

/**
 * Sort products with modern animation
 */
function sortProducts(criteria) {
    const productGrid = document.querySelector('.products-grid');
    const productItems = Array.from(productGrid.querySelectorAll('.product-item'));
    
    productItems.sort((a, b) => {
        switch (criteria) {
            case 'name':
                const nameA = a.querySelector('.card-title')?.textContent || '';
                const nameB = b.querySelector('.card-title')?.textContent || '';
                return nameA.localeCompare(nameB, 'fa');
                
            case 'price-low':
                const priceA = parseFloat(a.querySelector('.price-display')?.textContent.replace(/[^\d]/g, '') || '0');
                const priceB = parseFloat(b.querySelector('.price-display')?.textContent.replace(/[^\d]/g, '') || '0');
                return priceA - priceB;
                
            case 'price-high':
                const priceAHigh = parseFloat(a.querySelector('.price-display')?.textContent.replace(/[^\d]/g, '') || '0');
                const priceBHigh = parseFloat(b.querySelector('.price-display')?.textContent.replace(/[^\d]/g, '') || '0');
                return priceBHigh - priceAHigh;
                
            default:
                return 0;
        }
    });
    
    // Re-append sorted items with animation
    productItems.forEach((item, index) => {
        item.style.animation = `fadeInUp 0.3s ease-out ${index * 0.05}s both`;
        productGrid.appendChild(item);
    });
}

/**
 * Smooth scroll to product grid
 */
function scrollToProductGrid() {
    const productGrid = document.querySelector('.products-grid');
    if (productGrid) {
        productGrid.scrollIntoView({
            behavior: 'smooth',
            block: 'start'
        });
    }
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
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .loading-spinner {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: var(--space-3);
    }
    
    .spinner {
        width: 32px;
        height: 32px;
        border: 3px solid rgba(102, 126, 234, 0.3);
        border-top: 3px solid var(--color-primary);
        border-radius: 50%;
        animation: spin 1s linear infinite;
    }
    
    @keyframes spin {
        0% { transform: rotate(0deg); }
        100% { transform: rotate(360deg); }
    }
    
    .search-container {
        display: flex;
        gap: var(--space-2);
        margin-bottom: var(--space-4);
    }
    
    .search-input {
        flex: 1;
        padding: var(--space-3);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        background: var(--color-background);
        color: var(--color-text-primary);
        transition: all var(--transition-base);
    }
    
    .search-input:focus {
        outline: none;
        border-color: var(--color-primary);
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    .search-btn {
        padding: var(--space-3);
        background: var(--color-primary);
        color: white;
        border: none;
        border-radius: var(--radius-lg);
        cursor: pointer;
        transition: all var(--transition-base);
    }
    
    .search-btn:hover {
        background: var(--color-primary-dark);
        transform: scale(1.05);
    }
    
    .sort-container {
        margin-bottom: var(--space-6);
        display: flex;
        justify-content: flex-end;
    }
    
    .sort-dropdown {
        display: flex;
        align-items: center;
        gap: var(--space-3);
    }
    
    .sort-select {
        padding: var(--space-2) var(--space-3);
        border: 1px solid var(--border-color);
        border-radius: var(--radius-lg);
        background: var(--color-background);
        color: var(--color-text-primary);
        cursor: pointer;
    }
    
    .search-results {
        background: var(--surface-glass);
        backdrop-filter: var(--backdrop-blur);
        border: 1px solid var(--border-glass);
        border-radius: var(--radius-lg);
        padding: var(--space-4);
        margin-bottom: var(--space-6);
    }
    
    .search-results-content {
        display: flex;
        align-items: center;
        gap: var(--space-3);
        color: var(--color-text-primary);
    }
    
    .clear-search-btn {
        background: var(--color-error);
        color: white;
        border: none;
        border-radius: var(--radius-sm);
        padding: var(--space-1) var(--space-2);
        cursor: pointer;
        font-size: var(--font-size-xs);
        transition: all var(--transition-base);
    }
    
    .clear-search-btn:hover {
        background: var(--color-error-dark);
        transform: scale(1.05);
    }
`;
document.head.appendChild(style);

// Export functions for global access
window.ProductList = {
    searchProducts,
    sortProducts,
    scrollToProductGrid,
    showLoadingIndicator,
    hideLoadingIndicator,
    clearSearch,
    showAllProducts
};
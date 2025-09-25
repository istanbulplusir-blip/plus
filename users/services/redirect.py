from django.http import HttpRequest
from django.urls import reverse
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SmartRedirectService:
    """
    Service for intelligent redirect logic after login/registration
    """
    
    # Pages that should redirect to profile after login
    PROFILE_REQUIRED_PAGES = [
        '/users/profile/',
        '/users/verification/',
        '/users/settings/',
        '/users/security/',
        '/users/orders/',
        '/users/addresses/',
    ]
    
    # Pages that should redirect back to themselves
    SELF_REDIRECT_PAGES = [
        '/cart/',
        '/products/',
        '/orders/checkout/',
        '/payments/',
    ]
    
    # Default fallback pages for different scenarios
    DEFAULT_PAGES = {
        'has_cart': '/cart/',  # If user has items in cart
        'no_cart': '/',        # If no cart items
        'first_login': '/',    # First time login
        'returning': '/',      # Returning user
    }
    
    @staticmethod
    def get_smart_redirect_url(request: HttpRequest, user=None, is_registration=False):
        """
        Determine the best redirect URL after login/registration
        
        Args:
            request: HTTP request object
            user: User instance (if available)
            is_registration: Whether this is a registration flow
            
        Returns:
            str: Best redirect URL
        """
        try:
            # Get next URL from request parameters
            next_url = request.GET.get('next') or request.POST.get('next')
            if hasattr(request, 'data'):
                next_url = next_url or request.data.get('next', '')
            
            # Clean and validate next URL
            if next_url:
                next_url = SmartRedirectService._clean_url(next_url)
                if SmartRedirectService._is_safe_url(next_url, request):
                    logger.info(f"Using requested next URL: {next_url}")
                    return next_url
            
            # For registration, always go to home or profile setup
            if is_registration:
                return SmartRedirectService._get_registration_redirect(request, user)
            
            # For login, use smart logic
            return SmartRedirectService._get_login_redirect(request, user)
            
        except Exception as e:
            logger.error(f"Error in smart redirect: {str(e)}")
            return '/'  # Safe fallback
    
    @staticmethod
    def _get_registration_redirect(request, user):
        """Get redirect URL for new user registration"""
        # New users should go to home or profile setup
        if user and hasattr(user, 'email_verified') and not user.email_verified:
            return '/users/verification/'  # Need to verify email
        return '/'  # Go to home page
    
    @staticmethod
    def _get_login_redirect(request, user):
        """Get redirect URL for user login"""
        # Debug logging
        logger.info(f"Getting login redirect for user: {user}")
        logger.info(f"Request has cart: {hasattr(request, 'cart')}")
        if hasattr(request, 'cart'):
            logger.info(f"Cart exists: {request.cart is not None}")
            if request.cart:
                logger.info(f"Cart has items: {request.cart.items.exists()}")
        
        # Check if user has items in cart - PRIORITY 1
        if hasattr(request, 'cart') and request.cart and request.cart.items.exists():
            logger.info("User has cart items, redirecting to cart")
            return '/cart/'
        
        # Check if coming from cart or product pages - PRIORITY 2
        referer = request.META.get('HTTP_REFERER', '')
        if referer:
            referer_path = SmartRedirectService._extract_path_from_referer(referer)
            logger.info(f"User came from: {referer_path}")
            
            # Check if referer contains 'next' parameter (from login page)
            if 'next=' in referer:
                from urllib.parse import urlparse, parse_qs
                parsed_url = urlparse(referer)
                query_params = parse_qs(parsed_url.query)
                if 'next' in query_params:
                    next_url = query_params['next'][0]
                    logger.info(f"Found next parameter in referer: {next_url}")
                    
                    # If next is a product detail page, go to cart
                    if SmartRedirectService._is_product_detail_page(next_url):
                        logger.info("Next is product detail page, redirecting to cart")
                        return '/cart/'
                    
                    # If next is cart page, go to cart
                    if SmartRedirectService._is_cart_page(next_url):
                        logger.info("Next is cart page, redirecting to cart")
                        return '/cart/'
                    
                    # Otherwise, use the next URL
                    logger.info(f"Using next parameter: {next_url}")
                    return next_url
            
            # If coming from cart, go back to cart
            if SmartRedirectService._is_cart_page(referer_path):
                logger.info("User came from cart, redirecting back to cart")
                return '/cart/'
            
            # If coming from product detail, go to cart (since they likely added items)
            if SmartRedirectService._is_product_detail_page(referer_path):
                logger.info("User came from product detail page, redirecting to cart")
                return '/cart/'
            
            # If coming from product list page, go to home (not back to list)
            if referer_path == '/products/':
                logger.info("User came from product list, redirecting to home")
                return '/'
            
            # If coming from other specific pages, go back
            if referer_path in SmartRedirectService.SELF_REDIRECT_PAGES:
                logger.info(f"User came from {referer_path}, redirecting back")
                return referer_path
        
        # Default to home page
        return '/'
    
    @staticmethod
    def _clean_url(url):
        """Clean and normalize URL"""
        if not url:
            return ''
        
        # Remove domain if present
        if url.startswith('http'):
            from urllib.parse import urlparse
            parsed = urlparse(url)
            url = parsed.path
        
        # Ensure it starts with /
        if not url.startswith('/'):
            url = '/' + url
        
        return url
    
    @staticmethod
    def _is_safe_url(url, request):
        """Check if URL is safe to redirect to"""
        if not url:
            return False
        
        # Must be relative URL
        if url.startswith('http') and not url.startswith(request.build_absolute_uri('/')):
            return False
        
        # Must start with /
        if not url.startswith('/'):
            return False
        
        # Avoid redirect loops
        if url in ['/users/login/', '/users/register/']:
            return False
        
        return True
    
    @staticmethod
    def _extract_path_from_referer(referer):
        """Extract path from referer URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(referer)
            return parsed.path
        except Exception:
            return ''
    
    @staticmethod
    def _is_product_detail_page(path):
        """Check if path is a product detail page"""
        if not path:
            return False
        # Pattern: /products/product-slug/ (not /products/ or /products/category/)
        # Should have exactly 3 parts: ['', 'products', 'product-slug', '']
        parts = path.split('/')
        return (path.startswith('/products/') and 
                len(parts) == 4 and  # ['', 'products', 'slug', '']
                path.endswith('/') and
                path != '/products/')
    
    @staticmethod
    def _is_cart_page(path):
        """Check if path is cart page"""
        return path == '/cart/'
    
    @staticmethod
    def get_cart_redirect_url(request):
        """Get redirect URL specifically for cart-related operations"""
        if hasattr(request, 'cart') and request.cart and request.cart.items.exists():
            return '/cart/'
        return '/'
    
    @staticmethod
    def get_product_redirect_url(request, product_slug=None):
        """Get redirect URL for product-related operations"""
        if product_slug:
            return f'/products/{product_slug}/'
        return '/products/'

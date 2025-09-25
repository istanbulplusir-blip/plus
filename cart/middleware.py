from cart.models import Cart
import logging

logger = logging.getLogger(__name__)

def cart_middleware(get_response):
    def middleware(request):
        try:
            # Ensure session exists
            if not request.session.session_key:
                request.session.create()
            
            if request.user.is_authenticated:
                # Skip cart creation for admin users
                if request.user.is_staff:
                    request.cart = None
                    logger.debug(f"Admin user {request.user.id} - no cart assigned")
                else:
                    # Regular authenticated user - get or create user cart
                    if not hasattr(request, 'cart'):
                        cart, created = Cart.objects.get_or_create(user=request.user)
                        request.cart = cart
                        logger.debug(f"Authenticated user {request.user.id} - cart {cart.id} {'created' if created else 'retrieved'}")
            else:
                # Guest user - use session-based cart
                session_key = request.session.session_key
                if session_key:
                    if not hasattr(request, 'cart'):
                        cart, created = Cart.objects.get_or_create(
                            session_key=session_key,
                            user=None
                        )
                        request.cart = cart
                        logger.debug(f"Guest user with session {session_key} - cart {cart.id} {'created' if created else 'retrieved'}")
                else:
                    # Create session if it doesn't exist
                    request.session.create()
                    session_key = request.session.session_key
                    if session_key:
                        cart, created = Cart.objects.get_or_create(
                            session_key=session_key,
                            user=None
                        )
                        request.cart = cart
                        logger.debug(f"Guest user with new session {session_key} - cart {cart.id} {'created' if created else 'retrieved'}")
                    else:
                        request.cart = None
                        logger.warning("Failed to create session for guest user")
        except Exception as e:
            logger.error(f"Cart middleware error: {str(e)}")
            request.cart = None
        
        response = get_response(request)
        return response
    
    return middleware
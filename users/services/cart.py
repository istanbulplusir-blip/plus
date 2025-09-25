from django.contrib.auth import get_user_model
from cart.services import CartTransferService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class UserCartService:
    """
    Service for handling cart operations during user authentication
    """
    
    @staticmethod
    def transfer_guest_cart_on_login(user, session_key):
        """
        Transfer guest cart to user after successful login
        
        Args:
            user: Authenticated user instance
            session_key: Session key of the guest cart
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            if session_key:
                success = CartTransferService.transfer_guest_cart_to_user(user, session_key)
                if success:
                    logger.info(f"Guest cart transferred to user {user.id}")
                return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer guest cart on login: {str(e)}")
            return False
    
    @staticmethod
    def transfer_guest_cart_on_registration(user, session_key):
        """
        Transfer guest cart to user after successful registration
        
        Args:
            user: Newly registered user instance
            session_key: Session key of the guest cart
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            if session_key:
                success = CartTransferService.transfer_guest_cart_to_user(user, session_key)
                if success:
                    logger.info(f"Guest cart transferred to new user {user.id}")
                return success
            return True
            
        except Exception as e:
            logger.error(f"Failed to transfer guest cart on registration: {str(e)}")
            return False
    
    @staticmethod
    def get_user_cart_info(user):
        """
        Get cart information for authenticated user
        
        Args:
            user: User instance
            
        Returns:
            dict: Cart information
        """
        try:
            from cart.models import Cart
            
            cart = Cart.objects.filter(user=user).first()
            if cart:
                return {
                    'cart': cart,
                    'item_count': CartTransferService.get_cart_item_count(cart),
                    'total': CartTransferService.get_cart_total(cart),
                    'has_items': cart.items.exists()
                }
            else:
                return {
                    'cart': None,
                    'item_count': 0,
                    'total': 0,
                    'has_items': False
                }
                
        except Exception as e:
            logger.error(f"Failed to get user cart info: {str(e)}")
            return {
                'cart': None,
                'item_count': 0,
                'total': 0,
                'has_items': False
            }

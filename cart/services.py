from cart.models import Cart, CartItem
from django.contrib.auth import get_user_model
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class CartTransferService:
    """
    Service for transferring guest cart to authenticated user
    """
    
    @staticmethod
    def transfer_guest_cart_to_user(user, session_key):
        """
        Transfer guest cart items to user's cart
        
        Args:
            user: Authenticated user instance
            session_key: Session key of the guest cart
            
        Returns:
            bool: True if transfer successful, False otherwise
        """
        try:
            # Find guest cart
            guest_cart = Cart.objects.filter(
                session_key=session_key,
                user=None
            ).first()
            
            if not guest_cart or not guest_cart.items.exists():
                logger.info(f"No guest cart found for session {session_key}")
                return True  # No items to transfer
            
            # Get or create user cart
            user_cart, created = Cart.objects.get_or_create(user=user)
            
            # Transfer items - keep separate items even if same product
            transferred_items = 0
            for cart_item in guest_cart.items.all():
                # Always create new item in user cart to preserve separate entries
                # This ensures that if both guest and user have the same product,
                # they remain as separate items (e.g., 1x Product A + 1x Product A)
                new_cart_item = CartItem.objects.create(
                    cart=user_cart,
                    product=cart_item.product,
                    quantity=cart_item.quantity
                )
                logger.info(f"Transferred {cart_item.product.name} (qty: {cart_item.quantity}) to user cart as separate item")
                transferred_items += 1
            
            # Delete guest cart after successful transfer
            guest_cart.delete()
            logger.info(f"Successfully transferred {transferred_items} items from guest cart to user {user.id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Cart transfer failed for user {user.id}: {str(e)}")
            return False
    
    @staticmethod
    def merge_carts(user_cart, guest_cart):
        """
        Merge guest cart items into user cart
        
        Args:
            user_cart: User's cart instance
            guest_cart: Guest cart instance
            
        Returns:
            int: Number of items merged
        """
        merged_count = 0
        
        try:
            for cart_item in guest_cart.items.all():
                existing_item = user_cart.items.filter(product=cart_item.product).first()
                
                if existing_item:
                    # Merge quantities
                    existing_item.quantity += cart_item.quantity
                    existing_item.save()
                else:
                    # Move item to user cart
                    cart_item.cart = user_cart
                    cart_item.save()
                
                merged_count += 1
            
            logger.info(f"Merged {merged_count} items from guest cart")
            return merged_count
            
        except Exception as e:
            logger.error(f"Cart merge failed: {str(e)}")
            return 0
    
    @staticmethod
    def get_cart_total(cart):
        """
        Calculate total price of cart items
        
        Args:
            cart: Cart instance
            
        Returns:
            int: Total price in Toman
        """
        if not cart or not cart.items.exists():
            return 0
        
        total = 0
        for item in cart.items.all():
            total += item.product.price * item.quantity
        
        return total
    
    @staticmethod
    def get_cart_item_count(cart):
        """
        Get total number of items in cart
        
        Args:
            cart: Cart instance
            
        Returns:
            int: Total item count
        """
        if not cart:
            return 0
        
        return cart.items.count()
    
    @staticmethod
    def clear_cart(cart):
        """
        Clear all items from cart
        
        Args:
            cart: Cart instance
        """
        if cart:
            cart.items.all().delete()
            logger.info(f"Cleared cart {cart.id}")

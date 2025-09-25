from cart.services import CartTransferService

def cart_context(request):
    """
    Add cart to template context for both authenticated and guest users
    """
    context = {
        'cart': None, 
        'cart_item_count': 0,
        'cart_total': 0,
        'is_guest': not request.user.is_authenticated
    }
    
    if hasattr(request, 'cart') and request.cart:
        context['cart'] = request.cart
        context['cart_item_count'] = CartTransferService.get_cart_item_count(request.cart)
        context['cart_total'] = CartTransferService.get_cart_total(request.cart)
    
    return context
from django.views.generic import TemplateView
from django.shortcuts import redirect
from django.contrib import messages
from cart.services import CartTransferService


class CartView(TemplateView):
    """
    Cart view that works for both authenticated and guest users
    """
    template_name = 'cart/cart_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        cart = getattr(self.request, 'cart', None)
        
        if cart:
            context['cart'] = cart
            context['cart_total'] = CartTransferService.get_cart_total(cart)
            context['cart_item_count'] = CartTransferService.get_cart_item_count(cart)
        else:
            context['cart'] = None
            context['cart_total'] = 0
            context['cart_item_count'] = 0
        
        context['is_guest'] = not self.request.user.is_authenticated
        return context
    
    def get(self, request, *args, **kwargs):
        # Redirect to login if user is not authenticated and cart is empty
        if not request.user.is_authenticated:
            cart = getattr(request, 'cart', None)
            if not cart or not cart.items.exists():
                messages.info(request, 'برای مشاهده سبد خرید، ابتدا وارد حساب کاربری خود شوید')
                return redirect('users:login')
        
        return super().get(request, *args, **kwargs)
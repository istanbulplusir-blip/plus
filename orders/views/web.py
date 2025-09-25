from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView, View
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.http import JsonResponse
from orders.models import Order, OrderItem
from cart.services import CartTransferService
import logging

logger = logging.getLogger(__name__)


class OrderListView(LoginRequiredMixin, ListView):
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class OrderDetailView(LoginRequiredMixin, DetailView):
    model = Order
    template_name = 'orders/order_detail.html'
    context_object_name = 'order'

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user)


class CheckoutView(LoginRequiredMixin, View):
    """
    Checkout view to display cart and create order
    """
    template_name = 'orders/checkout.html'
    
    def get(self, request):
        cart = request.cart
        
        # Check if cart exists and has items
        if not cart or not cart.items.exists():
            messages.warning(request, 'سبد خرید خالی است')
            return redirect('cart:cart_detail')
        
        context = {
            'cart': cart,
            'cart_total': CartTransferService.get_cart_total(cart),
            'cart_item_count': CartTransferService.get_cart_item_count(cart)
        }
        
        return render(request, self.template_name, context)
    
    def post(self, request):
        # This will be handled by CreateOrderView
        return redirect('orders:create_order')


class CreateOrderView(LoginRequiredMixin, View):
    """
    Create order from cart items with comprehensive validation
    """
    
    def post(self, request):
        try:
            cart = request.cart
            
            # Check if cart exists and has items
            if not cart or not cart.items.exists():
                messages.error(request, 'سبد خرید خالی است')
                return redirect('cart:cart_detail')
            
            # Validate required fields
            validation_result = self._validate_order_data(request.POST)
            if not validation_result['valid']:
                for error in validation_result['errors']:
                    messages.error(request, error)
                return redirect('orders:checkout')
            
            # Check product availability
            availability_result = self._check_product_availability(cart)
            if not availability_result['available']:
                messages.error(request, availability_result['message'])
                return redirect('cart:cart_detail')
            
            # Create order with transaction
            from django.db import transaction
            
            with transaction.atomic():
                # Create order
                order = Order.objects.create(
                    user=request.user,
                    billing_name=validation_result['data']['billing_name'],
                    billing_phone=validation_result['data']['billing_phone'],
                    billing_address=validation_result['data']['billing_address'],
                    billing_city=validation_result['data']['billing_city']
                )
                
                # Create order items from cart
                total_amount = 0
                for cart_item in cart.items.all():
                    item_price = cart_item.product.price
                    item_total = item_price * cart_item.quantity
                    total_amount += item_total
                    
                    OrderItem.objects.create(
                        order=order,
                        product=cart_item.product,
                        quantity=cart_item.quantity,
                        price=item_price
                    )
                    
                    # Update product stock for physical products
                    if cart_item.product.type == 'physical':
                        cart_item.product.stock -= cart_item.quantity
                        cart_item.product.save()
                
                # Clear cart after successful order creation
                CartTransferService.clear_cart(cart)
            
            # Send order confirmation email
            from core.services import NotificationService
            NotificationService.send_order_confirmation_email(request.user, order)
            
            messages.success(request, f'سفارش شما با موفقیت ثبت شد. شماره سفارش: {order.id}')
            logger.info(f"Order {order.id} created for user {request.user.id} with total {total_amount}")
            
            return redirect('orders:order_detail', pk=order.id)
            
        except Exception as e:
            logger.error(f"Order creation failed: {str(e)}")
            messages.error(request, 'خطا در ایجاد سفارش. لطفاً دوباره تلاش کنید.')
            return redirect('cart:cart_detail')
    
    def _validate_order_data(self, post_data):
        """
        Validate order form data
        
        Args:
            post_data: POST data dictionary
            
        Returns:
            dict: Validation result with 'valid' boolean and 'data' or 'errors'
        """
        errors = []
        data = {}
        
        # Validate billing name
        billing_name = post_data.get('full_name', '').strip()
        if not billing_name:
            errors.append('نام و نام خانوادگی الزامی است')
        elif len(billing_name) < 2:
            errors.append('نام و نام خانوادگی باید حداقل 2 کاراکتر باشد')
        elif len(billing_name) > 100:
            errors.append('نام و نام خانوادگی نباید بیش از 100 کاراکتر باشد')
        else:
            data['billing_name'] = billing_name
        
        # Validate phone number
        billing_phone = post_data.get('phone', '').strip()
        if not billing_phone:
            errors.append('شماره تلفن الزامی است')
        elif not self._is_valid_phone(billing_phone):
            errors.append('شماره تلفن نامعتبر است')
        else:
            data['billing_phone'] = billing_phone
        
        # Validate address
        billing_address = post_data.get('address', '').strip()
        if not billing_address:
            errors.append('آدرس الزامی است')
        elif len(billing_address) < 10:
            errors.append('آدرس باید حداقل 10 کاراکتر باشد')
        elif len(billing_address) > 500:
            errors.append('آدرس نباید بیش از 500 کاراکتر باشد')
        else:
            data['billing_address'] = billing_address
        
        # Validate city
        billing_city = post_data.get('city', 'تهران').strip()
        if not billing_city:
            billing_city = 'تهران'
        elif len(billing_city) > 50:
            errors.append('نام شهر نباید بیش از 50 کاراکتر باشد')
        else:
            data['billing_city'] = billing_city
        
        return {
            'valid': len(errors) == 0,
            'data': data if len(errors) == 0 else None,
            'errors': errors
        }
    
    def _is_valid_phone(self, phone):
        """
        Validate Iranian phone number
        
        Args:
            phone: Phone number string
            
        Returns:
            bool: True if valid
        """
        import re
        # Iranian phone number patterns
        patterns = [
            r'^09\d{9}$',  # Mobile: 09xxxxxxxxx
            r'^\+989\d{9}$',  # Mobile with country code: +989xxxxxxxxx
            r'^0\d{10}$',  # Landline: 0xxxxxxxxxx
        ]
        
        for pattern in patterns:
            if re.match(pattern, phone):
                return True
        return False
    
    def _check_product_availability(self, cart):
        """
        Check if all products in cart are available
        
        Args:
            cart: Cart instance
            
        Returns:
            dict: Availability result
        """
        unavailable_products = []
        
        for cart_item in cart.items.all():
            product = cart_item.product
            
            # Check if product is active/available
            if not hasattr(product, 'is_active') or not product.is_active:
                unavailable_products.append(f"{product.name} (غیرفعال)")
                continue
            
            # Check stock for physical products
            if product.type == 'physical':
                if product.stock < cart_item.quantity:
                    unavailable_products.append(f"{product.name} (موجودی ناکافی)")
        
        if unavailable_products:
            return {
                'available': False,
                'message': f'محصولات زیر در دسترس نیستند: {", ".join(unavailable_products)}'
            }
        
        return {'available': True}
    
    def get(self, request):
        # Redirect to cart if trying to access via GET
        return redirect('cart:cart_detail')
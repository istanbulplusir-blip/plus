from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from cart.models import Cart, CartItem
from cart.serializers import CartSerializer, CartItemSerializer
from cart.services import CartTransferService
from products.models import Product
import logging

logger = logging.getLogger(__name__)


class CartDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CartSerializer
    permission_classes = [AllowAny]  # Allow both authenticated and guest users

    def get_object(self):
        return self.request.cart


class CartItemCreateAPIView(APIView):
    permission_classes = [AllowAny]  # Allow both authenticated and guest users

    def post(self, request, *args, **kwargs):
        # Check if user is admin - deny cart operations
        if request.user.is_authenticated and request.user.is_staff:
            return Response({
                'success': False,
                'message': 'Admin users cannot use shopping cart'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Ensure cart exists
        if not hasattr(request, 'cart') or request.cart is None:
            if request.user.is_authenticated:
                # Authenticated user
                request.cart, created = Cart.objects.get_or_create(user=request.user)
            else:
                # Guest user
                session_key = request.session.session_key
                if not session_key:
                    request.session.create()
                    session_key = request.session.session_key
                
                request.cart, created = Cart.objects.get_or_create(
                    session_key=session_key,
                    user=None
                )
        
        # Get product and quantity from request
        product_id = request.data.get('product_id')
        quantity = request.data.get('quantity', 1)
        
        if not product_id:
            return Response({
                'success': False,
                'message': 'Product ID is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Product not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check if item already exists in cart
        existing_item = CartItem.objects.filter(
            cart=request.cart,
            product=product
        ).first()
        
        if existing_item:
            # Update quantity
            existing_item.quantity += int(quantity)
            existing_item.save()
            cart_item = existing_item
        else:
            # Create new item
            cart_item = CartItem.objects.create(
                cart=request.cart,
                product=product,
                quantity=int(quantity)
            )
        
        # Serialize the response
        serializer = CartItemSerializer(cart_item)
        
        return Response({
            'success': True,
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class CartItemUpdateAPIView(generics.UpdateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # Allow both authenticated and guest users
    queryset = CartItem.objects.all()

    def get_queryset(self):
        if hasattr(self.request, 'cart') and self.request.cart:
            return super().get_queryset().filter(cart=self.request.cart)
        return CartItem.objects.none()


class CartItemDeleteAPIView(generics.DestroyAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [AllowAny]  # Allow both authenticated and guest users
    queryset = CartItem.objects.all()

    def get_queryset(self):
        if hasattr(self.request, 'cart') and self.request.cart:
            return super().get_queryset().filter(cart=self.request.cart)
        return CartItem.objects.none()
    
    def delete(self, request, *args, **kwargs):
        logger.info(f"Delete request for cart item {kwargs.get('pk')}")
        logger.info(f"Request cart: {getattr(request, 'cart', None)}")
        logger.info(f"User: {request.user}")
        logger.info(f"Session key: {request.session.session_key}")
        
        try:
            response = super().delete(request, *args, **kwargs)
            logger.info(f"Delete response: {response.status_code}")
            return response
        except Exception as e:
            logger.error(f"Delete error: {str(e)}")
            return Response({
                'success': False,
                'message': f'Error deleting item: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CartCountAPIView(APIView):
    permission_classes = [AllowAny]  # Allow both authenticated and guest users
    
    def get(self, request, *args, **kwargs):
        if hasattr(request, 'cart') and request.cart:
            count = CartTransferService.get_cart_item_count(request.cart)
            return Response({'count': count})
        return Response({'count': 0})


class CartTotalAPIView(APIView):
    permission_classes = [AllowAny]  # Allow both authenticated and guest users
    
    def get(self, request, *args, **kwargs):
        if hasattr(request, 'cart') and request.cart:
            total = CartTransferService.get_cart_total(request.cart)
            return Response({'total': total})
        return Response({'total': 0})


class CartTransferAPIView(APIView):
    """
    API endpoint to transfer guest cart to authenticated user
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        session_key = request.data.get('session_key')
        if not session_key:
            return Response({
                'success': False,
                'message': 'Session key is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        success = CartTransferService.transfer_guest_cart_to_user(
            request.user, 
            session_key
        )
        
        if success:
            return Response({
                'success': True,
                'message': 'Cart transferred successfully'
            })
        else:
            return Response({
                'success': False,
                'message': 'Cart transfer failed'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
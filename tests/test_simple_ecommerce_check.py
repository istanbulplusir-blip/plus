"""
Simple E-commerce System Check
Basic test to verify core functionality
"""
import json
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from products.models import Product, Category
from cart.models import Cart, CartItem
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()


class SimpleEcommerceCheck(TestCase):
    """
    Simple check of e-commerce components
    """
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        
        # Create test category
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category"
        )
        
        # Create test product
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            description="Test Description",
            price=100000,  # 100,000 Toman
            stock=10,
            type='physical',
            is_active=True
        )
        self.product.categories.add(self.category)
        
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            phone='09123456789'
        )
    
    def test_models_work(self):
        """Test that models work correctly"""
        print("🧪 Testing Models...")
        
        # Test Product model
        self.assertEqual(self.product.name, "Test Product")
        self.assertEqual(self.product.price, 100000)
        self.assertTrue(self.product.is_active)
        print("✅ Product model works")
        
        # Test Category model
        self.assertEqual(self.category.name, "Test Category")
        print("✅ Category model works")
        
        # Test User model
        self.assertEqual(self.user.username, "testuser")
        print("✅ User model works")
    
    def test_cart_functionality(self):
        """Test cart functionality"""
        print("🧪 Testing Cart Functionality...")
        
        # Test guest cart
        session_key = 'test_session'
        guest_cart = Cart.objects.create(session_key=session_key, user=None)
        
        # Add item to cart
        cart_item = CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=2
        )
        
        # Test cart calculations
        self.assertEqual(guest_cart.total_price, 200000)
        self.assertEqual(guest_cart.final_price, 200000)
        self.assertEqual(guest_cart.item_count, 2)
        print("✅ Cart calculations work")
        
        # Test cart transfer
        user_cart = Cart.objects.create(user=self.user)
        from cart.services import CartTransferService
        success = CartTransferService.transfer_guest_cart_to_user(self.user, session_key)
        self.assertTrue(success)
        print("✅ Cart transfer works")
    
    def test_order_creation(self):
        """Test order creation"""
        print("🧪 Testing Order Creation...")
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            billing_name='Test User',
            billing_phone='09123456789',
            billing_address='Test Address',
            billing_city='تهران'
        )
        
        # Add order item
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=1,
            price=self.product.price
        )
        
        self.assertEqual(order.status, 'pending')
        self.assertEqual(order.items.count(), 1)
        print("✅ Order creation works")
    
    def test_payment_creation(self):
        """Test payment creation"""
        print("🧪 Testing Payment Creation...")
        
        # Create order
        order = Order.objects.create(
            user=self.user,
            billing_name='Test User',
            billing_phone='09123456789',
            billing_address='Test Address',
            billing_city='تهران'
        )
        
        # Create payment
        payment = Payment.objects.create(
            order=order,
            amount=100000,
            status='initiated',
            tracking_code='TEST123'
        )
        
        self.assertEqual(payment.status, 'initiated')
        self.assertEqual(payment.amount, 100000)
        print("✅ Payment creation works")
    
    def test_services_import(self):
        """Test that all services can be imported"""
        print("🧪 Testing Services Import...")
        
        # Test cart services
        try:
            from cart.services import CartTransferService
            self.assertTrue(hasattr(CartTransferService, 'transfer_guest_cart_to_user'))
            print("✅ CartTransferService works")
        except ImportError:
            self.fail("CartTransferService not found")
        
        # Test user services
        try:
            from users.services import UserCartService
            self.assertTrue(hasattr(UserCartService, 'transfer_guest_cart_on_login'))
            print("✅ UserCartService works")
        except ImportError:
            self.fail("UserCartService not found")
        
        # Test payment services
        try:
            from payments.services import PaymentService
            self.assertTrue(hasattr(PaymentService, 'initiate_payment'))
            print("✅ PaymentService works")
        except ImportError:
            self.fail("PaymentService not found")
        
        # Test notification services
        try:
            from core.services import NotificationService
            self.assertTrue(hasattr(NotificationService, 'send_order_confirmation_email'))
            print("✅ NotificationService works")
        except ImportError:
            self.fail("NotificationService not found")
    
    def test_basic_urls(self):
        """Test basic URLs"""
        print("🧪 Testing Basic URLs...")
        
        # Test main URLs
        urls_to_test = [
            '/',
            '/users/login/',
            '/users/register/',
            '/products/',
            '/cart/',
            '/orders/',
            '/payments/',
        ]
        
        for url in urls_to_test:
            response = self.client.get(url)
            # Should not return 404
            self.assertNotEqual(response.status_code, 404, f"URL {url} returned 404")
        
        print("✅ All main URLs exist")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("🧪 Testing API Endpoints...")
        
        # Test cart API
        response = self.client.get('/api/cart/')
        self.assertIn(response.status_code, [200, 401])  # 401 for unauthenticated is OK
        print("✅ Cart API endpoint exists")
        
        # Test products API
        response = self.client.get('/api/products/')
        self.assertIn(response.status_code, [200, 401])
        print("✅ Products API endpoint exists")
        
        # Test orders API
        response = self.client.get('/api/orders/')
        self.assertIn(response.status_code, [200, 401])
        print("✅ Orders API endpoint exists")
    
    def test_guest_cart_api(self):
        """Test guest cart API functionality"""
        print("🧪 Testing Guest Cart API...")
        
        # Test adding item to cart
        cart_data = {
            'product_id': self.product.id,
            'quantity': 2
        }
        response = self.client.post('/api/cart/items/', cart_data)
        self.assertEqual(response.status_code, 201)
        print("✅ Guest can add product to cart via API")
        
        # Check cart was created
        session_key = self.client.session.session_key
        guest_cart = Cart.objects.filter(session_key=session_key, user=None).first()
        self.assertIsNotNone(guest_cart)
        self.assertEqual(guest_cart.items.count(), 1)
        print("✅ Guest cart created with session")
    
    def test_cart_calculations(self):
        """Test cart calculation methods"""
        print("🧪 Testing Cart Calculations...")
        
        # Create cart
        cart = Cart.objects.create(user=self.user)
        
        # Add items
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        # Test calculations
        expected_total = self.product.price * 2
        self.assertEqual(cart.total_price, expected_total)
        print(f"✅ Total price calculated correctly: {cart.total_price}")
        
        self.assertEqual(cart.final_price, expected_total)
        print(f"✅ Final price calculated correctly: {cart.final_price}")
        
        self.assertEqual(cart.item_count, 2)
        print(f"✅ Item count calculated correctly: {cart.item_count}")
        
        self.assertEqual(cart.discount_amount, 0)
        print("✅ Discount amount calculated correctly")
    
    def run_simple_check(self):
        """Run the simple check"""
        print("\n🚀 Running Simple E-commerce Check...")
        print("=" * 50)
        
        try:
            self.test_models_work()
            self.test_cart_functionality()
            self.test_order_creation()
            self.test_payment_creation()
            self.test_services_import()
            self.test_basic_urls()
            self.test_api_endpoints()
            self.test_guest_cart_api()
            self.test_cart_calculations()
            
            print("\n" + "=" * 50)
            print("🎉 SIMPLE CHECK PASSED! Core components are working!")
            print("=" * 50)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Simple check failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def run_simple_ecommerce_check():
    """Run the simple e-commerce check"""
    print("🧪 Starting Simple E-commerce System Check")
    print("=" * 50)
    
    test_instance = SimpleEcommerceCheck()
    test_instance.setUp()
    
    success = test_instance.run_simple_check()
    
    if success:
        print("\n✅ Simple Check Summary:")
        print("- Models: ✅")
        print("- Cart functionality: ✅")
        print("- Order creation: ✅")
        print("- Payment creation: ✅")
        print("- Services: ✅")
        print("- URLs: ✅")
        print("- API endpoints: ✅")
        print("- Guest cart API: ✅")
        print("- Cart calculations: ✅")
        print("\n🎊 Core system is working!")
    else:
        print("\n❌ Simple check failed. Please check the issues above.")
    
    return success


if __name__ == "__main__":
    run_simple_ecommerce_check()

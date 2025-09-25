#!/usr/bin/env python
"""
Test cart transfer fix after login
"""
import os
import sys
import django

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'settings.dev')
django.setup()

from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from cart.models import Cart, CartItem
from products.models import Product
from users.services import UserCartService
import json

User = get_user_model()

class CartTransferFixTest(TestCase):
    def setUp(self):
        """Set up test data"""
        # Create test user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        # Create test product
        self.product = Product.objects.create(
            name='Test Product',
            price=100000,
            stock=10,
            type='physical',
            is_active=True
        )
        
        # Create client
        self.client = Client()
    
    def test_cart_transfer_after_login(self):
        """Test that guest cart is transferred to user after login"""
        print("\n🧪 Testing cart transfer after login...")
        
        # Step 1: Add item to guest cart
        print("1️⃣ Adding item to guest cart...")
        
        # Ensure session exists
        session = self.client.session
        session.save()
        session_key = session.session_key
        print(f"   Session key: {session_key}")
        
        # Add item to guest cart via API
        response = self.client.post('/api/cart/items/', {
            'product_id': self.product.id,
            'quantity': 2
        }, content_type='application/json')
        
        self.assertEqual(response.status_code, 201)
        print("   ✅ Item added to guest cart")
        
        # Verify guest cart has items
        guest_cart = Cart.objects.filter(session_key=session_key, user=None).first()
        self.assertIsNotNone(guest_cart)
        self.assertEqual(guest_cart.items.count(), 1)
        print(f"   ✅ Guest cart has {guest_cart.items.count()} items")
        
        # Step 2: Login user
        print("2️⃣ Logging in user...")
        
        # Store session key before login
        original_session_key = session_key
        print(f"   Original session key: {original_session_key}")
        
        # Login via API
        login_response = self.client.post('/api/users/login/', {
            'username': 'test@example.com',
            'password': 'testpass123'
        }, content_type='application/json')
        
        self.assertEqual(login_response.status_code, 200)
        print("   ✅ User logged in successfully")
        
        # Step 3: Check if cart was transferred
        print("3️⃣ Checking cart transfer...")
        
        # Get user cart
        user_cart = Cart.objects.filter(user=self.user).first()
        self.assertIsNotNone(user_cart)
        print(f"   User cart ID: {user_cart.id}")
        
        # Check if items were transferred
        user_cart_items = user_cart.items.all()
        print(f"   User cart has {user_cart_items.count()} items")
        
        if user_cart_items.count() > 0:
            print("   ✅ Cart transfer successful!")
            for item in user_cart_items:
                print(f"      - {item.product.name}: {item.quantity}")
        else:
            print("   ❌ Cart transfer failed!")
            
            # Debug: Check if guest cart still exists
            guest_cart_after = Cart.objects.filter(session_key=original_session_key, user=None).first()
            if guest_cart_after:
                print(f"   Guest cart still exists with {guest_cart_after.items.count()} items")
            else:
                print("   Guest cart was deleted but items not transferred")
        
        # Step 4: Verify cart via web interface
        print("4️⃣ Testing cart view...")
        
        cart_response = self.client.get('/cart/')
        self.assertEqual(cart_response.status_code, 200)
        print("   ✅ Cart page accessible")
        
        # Check if cart context has items
        if hasattr(cart_response, 'context'):
            cart = cart_response.context.get('cart')
            if cart and cart.items.exists():
                print(f"   ✅ Cart context shows {cart.items.count()} items")
            else:
                print("   ❌ Cart context is empty")
        
        print("\n🎉 Cart transfer test completed!")
    
    def test_manual_cart_transfer(self):
        """Test manual cart transfer service"""
        print("\n🧪 Testing manual cart transfer service...")
        
        # Create guest cart with items
        session_key = 'test-session-123'
        guest_cart = Cart.objects.create(session_key=session_key, user=None)
        CartItem.objects.create(
            cart=guest_cart,
            product=self.product,
            quantity=3
        )
        
        print(f"   Created guest cart with {guest_cart.items.count()} items")
        
        # Test transfer service
        success = UserCartService.transfer_guest_cart_on_login(
            self.user, 
            session_key
        )
        
        self.assertTrue(success)
        print("   ✅ Transfer service returned success")
        
        # Check user cart
        user_cart = Cart.objects.filter(user=self.user).first()
        if user_cart:
            print(f"   User cart has {user_cart.items.count()} items")
            if user_cart.items.count() > 0:
                print("   ✅ Manual transfer successful!")
            else:
                print("   ❌ Manual transfer failed!")
        else:
            print("   ❌ User cart not found!")

if __name__ == '__main__':
    # Run the test
    test = CartTransferFixTest()
    test.setUp()
    test.test_cart_transfer_after_login()
    test.test_manual_cart_transfer()
    print("\n🎊 All tests completed!")

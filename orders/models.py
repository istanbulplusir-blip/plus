from django.db import models
from django.conf import settings
from products.models import Product, ProductFile

class Order(models.Model):
    STATUS_CHOICES = [
        ('pending', 'در انتظار پرداخت'),
        ('paid', 'پرداخت شده'),
        ('shipped', 'ارسال شده'),
        ('completed', 'تکمیل شده'),
        ('cancelled', 'لغو شده'),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    billing_name = models.CharField(max_length=100)
    billing_phone = models.CharField(max_length=15)
    billing_address = models.TextField()
    billing_city = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Order {self.pk} - {self.user}"

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.IntegerField()
    product_file = models.ForeignKey(ProductFile, null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
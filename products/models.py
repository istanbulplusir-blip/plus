from django.db import models
from django.utils import timezone
from mptt.models import MPTTModel, TreeForeignKey


class Category(MPTTModel):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class MPTTMeta:
        order_insertion_by = ['name']

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Categories'


class Product(models.Model):
    PHYSICAL = 'physical'
    DIGITAL = 'digital'
    PRODUCT_TYPE_CHOICES = [
        (PHYSICAL, 'Physical'),
        (DIGITAL, 'Digital'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price = models.IntegerField()  # Toman
    stock = models.IntegerField(default=0)  # Not used for digital
    type = models.CharField(max_length=10, choices=PRODUCT_TYPE_CHOICES, default=PHYSICAL)
    image = models.ImageField(upload_to='products/', blank=True)
    categories = models.ManyToManyField(Category, related_name='products')
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/images/')
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductFile(models.Model):
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name='file')
    file = models.FileField(upload_to='products/files/', blank=True)
    download_limit = models.IntegerField(default=10)

    def __str__(self):
        return f"File for {self.product.name}"

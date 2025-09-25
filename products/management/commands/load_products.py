from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Category, Product

class Command(BaseCommand):
    help = 'Load initial product data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Loading products data...')
        
        with transaction.atomic():
            # Create categories
            cat_digital = Category.objects.create(
                name="کتاب دیجیتال",
                slug="digital-books"
            )
            cat_accessories = Category.objects.create(
                name="لوازم جانبی",
                slug="accessories"
            )

            # Create products
            django_book = Product.objects.create(
                name="کتاب PDF آموزش Django",
                slug="django-pdf",
                description="کتاب دیجیتال آموزش جنگو.",
                price=120000,
                stock=100,
                type=Product.DIGITAL
            )
            django_book.categories.add(cat_digital)

            react_book = Product.objects.create(
                name="کتاب PDF آموزش React",
                slug="react-pdf",
                description="کتاب دیجیتال آموزش ری‌اکت.",
                price=110000,
                stock=100,
                type=Product.DIGITAL
            )
            react_book.categories.add(cat_digital)

            mouse = Product.objects.create(
                name="ماوس بی‌سیم",
                slug="wireless-mouse",
                description="ماوس بی‌سیم با کیفیت.",
                price=250000,
                stock=50,
                type=Product.PHYSICAL
            )
            mouse.categories.add(cat_accessories)

            keyboard = Product.objects.create(
                name="کیبورد مکانیکی",
                slug="mechanical-keyboard",
                description="کیبورد مکانیکی حرفه‌ای.",
                price=600000,
                stock=30,
                type=Product.PHYSICAL
            )
            keyboard.categories.add(cat_accessories)

            headphone = Product.objects.create(
                name="هدفون بلوتوث",
                slug="bluetooth-headphone",
                description="هدفون بلوتوث با صدای عالی.",
                price=400000,
                stock=40,
                type=Product.PHYSICAL
            )
            headphone.categories.add(cat_accessories)

        self.stdout.write(self.style.SUCCESS('Successfully loaded products data'))
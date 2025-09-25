from django.core.management.base import BaseCommand
from products.models import Category, Product, ProductImage, ProductFile

class Command(BaseCommand):
    help = 'Initialize sample categories and products'

    def handle(self, *args, **kwargs):
        # Create categories with MPTT structure
        digital_books = Category.objects.create(
            name='کتاب دیجیتال',
            slug='digital-books'
        )
        accessories = Category.objects.create(
            name='لوازم جانبی',
            slug='accessories'
        )

        self.stdout.write('Categories created successfully!')

        # Create products
        django_book = Product.objects.create(
            name='کتاب PDF آموزش Django',
            slug='django-pdf',
            description='کتاب دیجیتال آموزش جنگو.',
            price=120000,
            stock=100,
            type=Product.DIGITAL
        )
        django_book.categories.add(digital_books)

        react_book = Product.objects.create(
            name='کتاب PDF آموزش React',
            slug='react-pdf',
            description='کتاب دیجیتال آموزش ری‌اکت.',
            price=110000,
            stock=100,
            type=Product.DIGITAL
        )
        react_book.categories.add(digital_books)

        mouse = Product.objects.create(
            name='ماوس بی‌سیم',
            slug='wireless-mouse',
            description='ماوس بی‌سیم با کیفیت.',
            price=250000,
            stock=50,
            type=Product.PHYSICAL
        )
        mouse.categories.add(accessories)

        keyboard = Product.objects.create(
            name='کیبورد مکانیکی',
            slug='mechanical-keyboard',
            description='کیبورد مکانیکی حرفه‌ای.',
            price=600000,
            stock=30,
            type=Product.PHYSICAL
        )
        keyboard.categories.add(accessories)

        headphone = Product.objects.create(
            name='هدفون بلوتوث',
            slug='bluetooth-headphone',
            description='هدفون بلوتوث با صدای عالی.',
            price=400000,
            stock=40,
            type=Product.PHYSICAL
        )
        headphone.categories.add(accessories)

        # Create digital files for books
        ProductFile.objects.create(
            product=django_book,
            file='products/files/django_tutorial.pdf'
        )

        ProductFile.objects.create(
            product=react_book,
            file='products/files/react_tutorial.pdf'
        )

        self.stdout.write('Products and files created successfully!')
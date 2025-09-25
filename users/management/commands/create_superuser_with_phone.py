from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a superuser with phone field support'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Username')
        parser.add_argument('--email', type=str, help='Email')
        parser.add_argument('--phone', type=str, help='Phone number')
        parser.add_argument('--password', type=str, help='Password')

    def handle(self, *args, **options):
        username = options.get('username')
        email = options.get('email')
        phone = options.get('phone')
        password = options.get('password')

        if not all([username, email, phone, password]):
            self.stdout.write(
                self.style.ERROR('All fields (username, email, phone, password) are required')
            )
            return

        try:
            user = User.objects.create_superuser(
                username=username,
                email=email,
                phone=phone,
                password=password
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully created superuser: {username}')
            )
        except IntegrityError as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating superuser: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Unexpected error: {e}')
            )

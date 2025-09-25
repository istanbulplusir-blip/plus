"""
Management command to demonstrate the EmailService and OTPService functionality.
"""
from django.core.management.base import BaseCommand
from users.services.demo import main


class Command(BaseCommand):
    help = 'Demonstrate EmailService and OTPService functionality'
    
    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting Email and OTP Services Demo...')
        )
        
        main()
        
        self.stdout.write(
            self.style.SUCCESS('Demo completed!')
        )
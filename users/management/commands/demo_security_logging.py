"""
Management command to demonstrate security logging functionality.
"""
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from users.services.security import SecurityService
from users.models import SecurityLog

User = get_user_model()


class Command(BaseCommand):
    help = 'Demonstrate security logging functionality'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Security Logging System Demo ==='))
        
        # Create a test user if it doesn't exist
        user, created = User.objects.get_or_create(
            username='demo_user',
            defaults={
                'email': 'demo@example.com',
                'phone': '+989123456789'
            }
        )
        
        if created:
            self.stdout.write(f'Created demo user: {user.username}')
        else:
            self.stdout.write(f'Using existing demo user: {user.username}')
        
        # Demonstrate various security logging events
        ip_address = '192.168.1.100'
        
        self.stdout.write('\n1. Logging successful login...')
        SecurityService.log_security_event(
            event_type='login_success',
            ip_address=ip_address,
            user=user,
            severity='low',
            user_agent='Demo Browser',
            details={'login_method': 'password'}
        )
        
        self.stdout.write('2. Logging failed login attempt...')
        SecurityService.log_security_event(
            event_type='login_failed',
            ip_address=ip_address,
            user=user,
            severity='medium',
            user_agent='Demo Browser',
            details={'reason': 'Invalid password', 'failed_attempts': 1}
        )
        
        self.stdout.write('3. Logging suspicious activity...')
        SecurityService.log_security_event(
            event_type='suspicious_activity',
            ip_address=ip_address,
            user=user,
            severity='high',
            user_agent='Suspicious Bot/1.0',
            details={'reason': 'Bot user agent detected'}
        )
        
        self.stdout.write('4. Logging rate limit exceeded...')
        SecurityService.log_security_event(
            event_type='rate_limit_exceeded',
            ip_address=ip_address,
            severity='medium',
            user_agent='Demo Browser',
            details={'action': 'login_attempts', 'limit_exceeded': True}
        )
        
        self.stdout.write('5. Testing account lock functionality...')
        success = SecurityService.lock_user_account(
            user=user,
            duration_minutes=1,  # Short duration for demo
            reason='Demo account lock',
            ip_address=ip_address
        )
        
        if success:
            self.stdout.write(f'   Account locked: {user.is_locked()}')
            
            # Unlock immediately for demo
            SecurityService.unlock_user_account(
                user=user,
                ip_address=ip_address,
                reason='Demo unlock'
            )
            self.stdout.write(f'   Account unlocked: {not user.is_locked()}')
        
        self.stdout.write('6. Testing IP blocking functionality...')
        SecurityService.block_ip(
            ip_address='192.168.1.200',
            duration_minutes=1,  # Short duration for demo
            reason='Demo IP block'
        )
        
        blocked = SecurityService.is_ip_blocked('192.168.1.200')
        self.stdout.write(f'   IP blocked: {blocked}')
        
        # Show security summary
        self.stdout.write('\n7. Generating security summary...')
        summary = SecurityService.get_security_summary(user, days=1)
        
        self.stdout.write(f'   Total events: {summary["total_events"]}')
        self.stdout.write(f'   Failed logins: {summary["failed_logins"]}')
        self.stdout.write(f'   Successful logins: {summary["successful_logins"]}')
        self.stdout.write(f'   High severity events: {summary["high_severity_events"]}')
        
        # Show recent logs
        self.stdout.write('\n8. Recent security logs:')
        recent_logs = SecurityLog.objects.filter(user=user).order_by('-created_at')[:5]
        
        for log in recent_logs:
            self.stdout.write(
                f'   [{log.created_at.strftime("%H:%M:%S")}] '
                f'{log.get_event_type_display()} - '
                f'{log.get_severity_display()} - '
                f'{log.ip_address}'
            )
        
        # Test rate limiting
        self.stdout.write('\n9. Testing rate limiting...')
        for i in range(3):
            is_allowed, info = SecurityService.check_rate_limit(
                identifier=ip_address,
                action='login_attempts'
            )
            self.stdout.write(f'   Attempt {i+1}: Allowed={is_allowed}, Count={info.get("current_count", 0)}')
            
            if is_allowed:
                SecurityService.increment_rate_limit(ip_address, 'login_attempts')
        
        self.stdout.write('\n=== Demo Complete ===')
        self.stdout.write(
            self.style.SUCCESS(
                f'Created {SecurityLog.objects.count()} security log entries. '
                'Check the admin panel at /admin/users/securitylog/ to view them.'
            )
        )
"""
Security service for handling security-related operations including rate limiting,
suspicious activity detection, and account locking.
"""
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import timedelta
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from django.contrib.gis.geoip2 import GeoIP2
from django.core.exceptions import ValidationError
from users.models import User, SecurityLog

logger = logging.getLogger(__name__)


class SecurityService:
    """Service class for handling security operations"""
    
    # Rate limiting keys and limits
    RATE_LIMIT_KEYS = {
        'login_attempts': 'security_login_attempts_{ip}',
        'otp_requests': 'security_otp_requests_{contact}',
        'password_reset': 'security_password_reset_{ip}',
        'registration': 'security_registration_{ip}',
        'api_requests': 'security_api_requests_{ip}',
        'email_verification': 'security_email_verification_{ip}',
        'phone_verification': 'security_phone_verification_{ip}',
    }
    
    DEFAULT_LIMITS = {
        'login_attempts': {'count': 5, 'window': 900},  # 5 attempts per 15 minutes
        'otp_requests': {'count': 5, 'window': 3600},   # 5 requests per hour
        'password_reset': {'count': 3, 'window': 3600}, # 3 requests per hour
        'registration': {'count': 3, 'window': 3600},   # 3 registrations per hour
        'api_requests': {'count': 100, 'window': 3600}, # 100 API requests per hour
        'email_verification': {'count': 5, 'window': 3600}, # 5 email verifications per hour
        'phone_verification': {'count': 5, 'window': 3600}, # 5 phone verifications per hour
    }
    
    @staticmethod
    def check_rate_limit(
        identifier: str,
        action: str,
        custom_limit: Optional[Dict[str, int]] = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if rate limit is exceeded for a specific action.
        
        Args:
            identifier: IP address, email, or phone number
            action: Type of action (login_attempts, otp_requests, etc.)
            custom_limit: Custom limit override {'count': int, 'window': int}
            
        Returns:
            Tuple[bool, Dict]: (is_allowed, info_dict)
        """
        try:
            if action not in SecurityService.RATE_LIMIT_KEYS:
                logger.warning(f"Unknown rate limit action: {action}")
                return True, {}
            
            # Get limit configuration
            limit_config = custom_limit or SecurityService.DEFAULT_LIMITS.get(action, {})
            max_count = limit_config.get('count', 10)
            window_seconds = limit_config.get('window', 3600)
            
            # Generate cache key
            cache_key = SecurityService.RATE_LIMIT_KEYS[action].format(
                ip=identifier,
                contact=identifier
            )
            
            # Get current count
            current_count = cache.get(cache_key, 0)
            
            # Check if limit exceeded
            if current_count >= max_count:
                logger.warning(f"Rate limit exceeded for {identifier} on action {action}")
                return False, {
                    'current_count': current_count,
                    'max_count': max_count,
                    'window_seconds': window_seconds,
                    'retry_after': window_seconds
                }
            
            return True, {
                'current_count': current_count,
                'max_count': max_count,
                'window_seconds': window_seconds,
                'remaining': max_count - current_count
            }
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {str(e)}")
            # In case of error, allow the request but log it
            return True, {'error': str(e)}
    
    @staticmethod
    def increment_rate_limit(
        identifier: str,
        action: str,
        custom_limit: Optional[Dict[str, int]] = None
    ) -> int:
        """
        Increment rate limit counter for a specific action.
        
        Args:
            identifier: IP address, email, or phone number
            action: Type of action
            custom_limit: Custom limit override
            
        Returns:
            int: New count value
        """
        try:
            if action not in SecurityService.RATE_LIMIT_KEYS:
                logger.warning(f"Unknown rate limit action: {action}")
                return 0
            
            # Get limit configuration
            limit_config = custom_limit or SecurityService.DEFAULT_LIMITS.get(action, {})
            window_seconds = limit_config.get('window', 3600)
            
            # Generate cache key
            cache_key = SecurityService.RATE_LIMIT_KEYS[action].format(
                ip=identifier,
                contact=identifier
            )
            
            # Increment counter with expiry
            try:
                new_count = cache.get(cache_key, 0) + 1
                cache.set(cache_key, new_count, window_seconds)
                return new_count
            except Exception:
                # Fallback: set to 1 if increment fails
                cache.set(cache_key, 1, window_seconds)
                return 1
                
        except Exception as e:
            logger.error(f"Error incrementing rate limit: {str(e)}")
            return 0
    
    @staticmethod
    def reset_rate_limit(identifier: str, action: str) -> bool:
        """
        Reset rate limit counter for a specific action.
        
        Args:
            identifier: IP address, email, or phone number
            action: Type of action
            
        Returns:
            bool: True if reset successfully
        """
        try:
            if action not in SecurityService.RATE_LIMIT_KEYS:
                return False
            
            cache_key = SecurityService.RATE_LIMIT_KEYS[action].format(
                ip=identifier,
                contact=identifier
            )
            
            cache.delete(cache_key)
            return True
            
        except Exception as e:
            logger.error(f"Error resetting rate limit: {str(e)}")
            return False
    
    @staticmethod
    def check_suspicious_activity(
        user: Optional[User],
        ip_address: str,
        user_agent: str = '',
        action: str = 'login'
    ) -> Tuple[bool, str]:
        """
        Check for suspicious activity patterns.
        
        Args:
            user: User instance (can be None for anonymous actions)
            ip_address: IP address of the request
            user_agent: User agent string
            action: Type of action being performed
            
        Returns:
            Tuple[bool, str]: (is_suspicious, reason)
        """
        try:
            suspicious_reasons = []
            
            # Check 1: Multiple failed attempts from same IP
            if action == 'login':
                failed_attempts_key = f"security_failed_attempts_{ip_address}"
                failed_count = cache.get(failed_attempts_key, 0)
                
                if failed_count >= 10:  # 10 failed attempts from same IP
                    suspicious_reasons.append("Multiple failed login attempts from IP")
            
            # Check 2: Rapid requests from same IP
            rapid_requests_key = f"security_rapid_requests_{ip_address}"
            request_count = cache.get(rapid_requests_key, 0)
            
            if request_count >= 50:  # 50 requests in last 5 minutes
                suspicious_reasons.append("Rapid requests from IP")
            
            # Increment rapid request counter
            cache.set(rapid_requests_key, request_count + 1, 300)  # 5 minutes
            
            # Check 3: User login from new location (if user exists)
            if user and user.last_login_ip and user.last_login_ip != ip_address:
                try:
                    # Try to get location info (requires GeoIP2 database)
                    g = GeoIP2()
                    current_country = g.country(ip_address).get('country_code', '')
                    last_country = g.country(user.last_login_ip).get('country_code', '')
                    
                    if current_country and last_country and current_country != last_country:
                        suspicious_reasons.append("Login from different country")
                        
                except Exception:
                    # GeoIP2 not available or IP not found, skip this check
                    pass
            
            # Check 4: Unusual user agent patterns
            if user_agent:
                suspicious_agents = ['bot', 'crawler', 'spider', 'scraper']
                if any(agent in user_agent.lower() for agent in suspicious_agents):
                    suspicious_reasons.append("Suspicious user agent")
            
            # Check 5: Account locked recently
            if user and user.locked_until:
                if timezone.now() < user.locked_until + timedelta(hours=1):
                    suspicious_reasons.append("Recent account lock")
            
            is_suspicious = len(suspicious_reasons) > 0
            reason = "; ".join(suspicious_reasons) if suspicious_reasons else ""
            
            return is_suspicious, reason
            
        except Exception as e:
            logger.error(f"Error checking suspicious activity: {str(e)}")
            return False, ""
    
    @staticmethod
    def lock_user_account(
        user: User,
        duration_minutes: int = 30,
        reason: str = "Security violation",
        ip_address: str = '127.0.0.1'
    ) -> bool:
        """
        Lock user account temporarily.
        
        Args:
            user: User instance to lock
            duration_minutes: Lock duration in minutes
            reason: Reason for locking
            ip_address: IP address that triggered the lock
            
        Returns:
            bool: True if locked successfully
        """
        try:
            # Lock the account
            user.lock_account(duration_minutes)
            
            # Log the security event
            SecurityService.log_security_event(
                user=user,
                event_type='login_locked',
                severity='high',
                ip_address=ip_address,
                details={
                    'reason': reason,
                    'duration_minutes': duration_minutes,
                    'locked_until': user.locked_until.isoformat() if user.locked_until else None
                }
            )
            
            # Send security alert email
            try:
                from users.services.email import EmailService
                EmailService.send_security_alert(
                    user=user,
                    event='account_locked',
                    ip_address=ip_address,
                    details={'reason': reason, 'duration_minutes': duration_minutes}
                )
            except Exception as e:
                logger.error(f"Failed to send security alert email: {str(e)}")
            
            logger.warning(f"User account {user.username} locked for {duration_minutes} minutes. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error locking user account: {str(e)}")
            return False
    
    @staticmethod
    def unlock_user_account(
        user: User,
        ip_address: str = '127.0.0.1',
        reason: str = "Manual unlock"
    ) -> bool:
        """
        Unlock user account.
        
        Args:
            user: User instance to unlock
            ip_address: IP address of the unlock request
            reason: Reason for unlocking
            
        Returns:
            bool: True if unlocked successfully
        """
        try:
            # Unlock the account
            user.unlock_account()
            
            # Log the security event
            SecurityService.log_security_event(
                user=user,
                event_type='account_unlocked',
                severity='medium',
                ip_address=ip_address,
                details={'reason': reason}
            )
            
            logger.info(f"User account {user.username} unlocked. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error unlocking user account: {str(e)}")
            return False
    
    @staticmethod
    def log_security_event(
        event_type: str,
        ip_address: str,
        user: Optional[User] = None,
        severity: str = 'low',
        user_agent: str = '',
        details: Optional[Dict[str, Any]] = None
    ) -> Optional[SecurityLog]:
        """
        Log a security event.
        
        Args:
            event_type: Type of security event
            ip_address: IP address of the event
            user: User instance (optional)
            severity: Severity level (low, medium, high, critical)
            user_agent: User agent string
            details: Additional event details
            
        Returns:
            SecurityLog instance or None if failed
        """
        try:
            security_log = SecurityLog.objects.create(
                user=user,
                event_type=event_type,
                severity=severity,
                ip_address=ip_address,
                user_agent=user_agent,
                details=details or {}
            )
            
            # Log critical events immediately
            if severity == 'critical':
                logger.critical(f"CRITICAL SECURITY EVENT: {event_type} from {ip_address}")
            elif severity == 'high':
                logger.warning(f"HIGH SECURITY EVENT: {event_type} from {ip_address}")
            
            return security_log
            
        except Exception as e:
            logger.error(f"Error logging security event: {str(e)}")
            return None
    
    @staticmethod
    def get_client_ip(request) -> str:
        """
        Get client IP address from request.
        
        Args:
            request: Django request object
            
        Returns:
            str: Client IP address
        """
        try:
            # Check for forwarded IP (behind proxy/load balancer)
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip = x_forwarded_for.split(',')[0].strip()
                return ip
            
            # Check for real IP header
            x_real_ip = request.META.get('HTTP_X_REAL_IP')
            if x_real_ip:
                return x_real_ip.strip()
            
            # Fallback to remote address
            return request.META.get('REMOTE_ADDR', '127.0.0.1')
            
        except Exception as e:
            logger.error(f"Error getting client IP: {str(e)}")
            return '127.0.0.1'
    
    @staticmethod
    def is_ip_blocked(ip_address: str) -> bool:
        """
        Check if IP address is blocked.
        
        Args:
            ip_address: IP address to check
            
        Returns:
            bool: True if IP is blocked
        """
        try:
            blocked_key = f"security_blocked_ip_{ip_address}"
            return cache.get(blocked_key, False)
            
        except Exception as e:
            logger.error(f"Error checking blocked IP: {str(e)}")
            return False
    
    @staticmethod
    def block_ip(ip_address: str, duration_minutes: int = 60, reason: str = "Security violation") -> bool:
        """
        Block IP address temporarily.
        
        Args:
            ip_address: IP address to block
            duration_minutes: Block duration in minutes
            reason: Reason for blocking
            
        Returns:
            bool: True if blocked successfully
        """
        try:
            blocked_key = f"security_blocked_ip_{ip_address}"
            cache.set(blocked_key, True, duration_minutes * 60)
            
            # Log the event
            SecurityService.log_security_event(
                event_type='ip_blocked',
                ip_address=ip_address,
                severity='high',
                details={
                    'reason': reason,
                    'duration_minutes': duration_minutes
                }
            )
            
            logger.warning(f"IP {ip_address} blocked for {duration_minutes} minutes. Reason: {reason}")
            return True
            
        except Exception as e:
            logger.error(f"Error blocking IP: {str(e)}")
            return False
    
    @staticmethod
    def cleanup_security_logs(days_to_keep: int = 90) -> int:
        """
        Clean up old security logs.
        
        Args:
            days_to_keep: Number of days to keep logs
            
        Returns:
            int: Number of logs deleted
        """
        try:
            cutoff_date = timezone.now() - timedelta(days=days_to_keep)
            deleted_count = SecurityLog.objects.filter(
                created_at__lt=cutoff_date
            ).delete()[0]
            
            logger.info(f"Cleaned up {deleted_count} old security logs")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error cleaning up security logs: {str(e)}")
            return 0
    
    @staticmethod
    def get_security_summary(user: User, days: int = 30) -> Dict[str, Any]:
        """
        Get security summary for a user.
        
        Args:
            user: User instance
            days: Number of days to analyze
            
        Returns:
            Dict: Security summary
        """
        try:
            since_date = timezone.now() - timedelta(days=days)
            
            logs = SecurityLog.objects.filter(
                user=user,
                created_at__gte=since_date
            )
            
            summary = {
                'total_events': logs.count(),
                'failed_logins': logs.filter(event_type='login_failed').count(),
                'successful_logins': logs.filter(event_type='login_success').count(),
                'otp_failures': logs.filter(event_type='otp_failed').count(),
                'account_locks': logs.filter(event_type='login_locked').count(),
                'unique_ips': logs.values('ip_address').distinct().count(),
                'high_severity_events': logs.filter(severity__in=['high', 'critical']).count(),
                'recent_events': list(logs.order_by('-created_at')[:10].values(
                    'event_type', 'severity', 'ip_address', 'created_at'
                ))
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting security summary: {str(e)}")
            return {}
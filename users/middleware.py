"""
Middleware for security-related functionality including rate limiting and suspicious activity detection.
"""
import logging
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from users.services.security import SecurityService

logger = logging.getLogger(__name__)


class SecurityMiddleware(MiddlewareMixin):
    """
    Middleware for handling security checks including rate limiting and IP blocking.
    """
    
    # Paths that should be rate limited
    RATE_LIMITED_PATHS = {
        '/api/auth/login/': {'action': 'login_attempts', 'limit': {'count': 5, 'window': 900}},
        '/api/auth/register/': {'action': 'registration', 'limit': {'count': 3, 'window': 3600}},
        '/api/auth/send-otp/': {'action': 'otp_requests', 'limit': {'count': 5, 'window': 3600}},
        '/api/auth/password-reset/request/': {'action': 'password_reset', 'limit': {'count': 3, 'window': 3600}},
        '/api/auth/send-email-verification/': {'action': 'email_verification', 'limit': {'count': 5, 'window': 3600}},
        '/api/auth/send-phone-verification/': {'action': 'phone_verification', 'limit': {'count': 5, 'window': 3600}},
        '/users/login/': {'action': 'login_attempts', 'limit': {'count': 5, 'window': 900}},
        '/users/register/': {'action': 'registration', 'limit': {'count': 3, 'window': 3600}},
    }
    
    def process_request(self, request):
        """
        Process incoming request for security checks.
        """
        try:
            # Skip security checks for certain paths
            if self._should_skip_security_check(request):
                return None
            
            # Get client IP
            ip_address = SecurityService.get_client_ip(request)
            
            # Check if IP is blocked
            if SecurityService.is_ip_blocked(ip_address):
                logger.warning(f"Blocked IP {ip_address} attempted to access {request.path}")
                return self._handle_blocked_ip(request)
            
            # Check rate limiting for specific paths
            if request.path in self.RATE_LIMITED_PATHS:
                rate_limit_config = self.RATE_LIMITED_PATHS[request.path]
                action = rate_limit_config['action']
                custom_limit = rate_limit_config.get('limit')
                
                is_allowed, info = SecurityService.check_rate_limit(
                    identifier=ip_address,
                    action=action,
                    custom_limit=custom_limit
                )
                
                if not is_allowed:
                    # Increment rate limit counter
                    SecurityService.increment_rate_limit(ip_address, action, custom_limit)
                    
                    # Log rate limit violation
                    SecurityService.log_security_event(
                        event_type='rate_limit_exceeded',
                        ip_address=ip_address,
                        severity='medium',
                        user_agent=request.META.get('HTTP_USER_AGENT', ''),
                        details={
                            'path': request.path,
                            'action': action,
                            'limit_info': info
                        }
                    )
                    
                    return self._handle_rate_limit_exceeded(request, info)
            
            # Store IP in request for later use
            request.client_ip = ip_address
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SecurityMiddleware: {str(e)}")
            # Don't block requests if middleware fails
            return None
    
    def process_response(self, request, response):
        """
        Process response to increment rate limit counters for successful requests.
        """
        try:
            # Only increment for POST requests to rate-limited paths
            if (request.method == 'POST' and 
                hasattr(request, 'client_ip') and 
                request.path in self.RATE_LIMITED_PATHS):
                
                rate_limit_config = self.RATE_LIMITED_PATHS[request.path]
                action = rate_limit_config['action']
                custom_limit = rate_limit_config.get('limit')
                
                # Increment counter for processed requests
                SecurityService.increment_rate_limit(
                    identifier=request.client_ip,
                    action=action,
                    custom_limit=custom_limit
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Error in SecurityMiddleware process_response: {str(e)}")
            return response
    
    def _should_skip_security_check(self, request):
        """
        Determine if security check should be skipped for this request.
        """
        # Skip for static files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return True
        
        # Skip for admin (has its own protection)
        if request.path.startswith('/admin/'):
            return True
        
        # Skip for health checks
        if request.path in ['/health/', '/ping/', '/status/']:
            return True
        
        # Skip for GET requests to most paths (except sensitive ones)
        if request.method == 'GET' and not any(
            sensitive in request.path for sensitive in ['/auth/', '/api/auth/']
        ):
            return True
        
        return False
    
    def _handle_blocked_ip(self, request):
        """
        Handle requests from blocked IPs.
        """
        if request.path.startswith('/api/'):
            return JsonResponse({
                'error': 'Access denied',
                'message': 'Your IP address has been temporarily blocked due to suspicious activity.'
            }, status=403)
        else:
            return render(request, 'errors/403.html', {
                'message': 'Your IP address has been temporarily blocked due to suspicious activity.'
            }, status=403)
    
    def _handle_rate_limit_exceeded(self, request, limit_info):
        """
        Handle rate limit exceeded responses.
        """
        retry_after = limit_info.get('retry_after', 3600)
        
        if request.path.startswith('/api/'):
            response = JsonResponse({
                'error': 'Rate limit exceeded',
                'message': 'Too many requests. Please try again later.',
                'retry_after': retry_after,
                'limit_info': {
                    'current_count': limit_info.get('current_count', 0),
                    'max_count': limit_info.get('max_count', 0)
                }
            }, status=429)
        else:
            response = render(request, 'errors/429.html', {
                'message': 'Too many requests. Please try again later.',
                'retry_after': retry_after
            }, status=429)
        
        # Add Retry-After header
        response['Retry-After'] = str(retry_after)
        return response


class SessionTrackingMiddleware(MiddlewareMixin):
    """
    Middleware for tracking user sessions and updating session activity.
    """
    
    def process_request(self, request):
        """
        Track user session activity.
        """
        try:
            # Only track authenticated users
            if not hasattr(request, 'user') or not request.user.is_authenticated:
                return None
            
            # Get session information
            session_key = request.session.session_key
            if not session_key:
                # Create session if it doesn't exist
                request.session.create()
                session_key = request.session.session_key
            
            ip_address = SecurityService.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Update or create user session record
            self._update_user_session(
                user=request.user,
                session_key=session_key,
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SessionTrackingMiddleware: {str(e)}")
            return None
    
    def _update_user_session(self, user, session_key, ip_address, user_agent):
        """
        Update or create user session record.
        """
        try:
            from users.models import UserSession
            
            # Try to get location from IP
            location = ''
            try:
                from django.contrib.gis.geoip2 import GeoIP2
                g = GeoIP2()
                location_data = g.city(ip_address)
                if location_data:
                    city = location_data.get('city', '')
                    country = location_data.get('country_name', '')
                    location = f"{city}, {country}" if city and country else country
            except Exception:
                pass
            
            # Update existing session or create new one
            session, created = UserSession.objects.update_or_create(
                user=user,
                session_key=session_key,
                defaults={
                    'ip_address': ip_address,
                    'user_agent': user_agent,
                    'location': location,
                    'is_active': True
                }
            )
            
            if created:
                # Log new session creation
                SecurityService.log_security_event(
                    event_type='session_created',
                    ip_address=ip_address,
                    user=user,
                    severity='low',
                    user_agent=user_agent,
                    details={
                        'session_id': session.id,
                        'location': location
                    }
                )
                
        except Exception as e:
            logger.error(f"Failed to update user session: {str(e)}")


class SecurityLoggingMiddleware(MiddlewareMixin):
    """
    Middleware for logging security-related events.
    """
    
    def process_request(self, request):
        """
        Log security-relevant requests.
        """
        try:
            # Only log sensitive paths
            if not self._should_log_request(request):
                return None
            
            ip_address = SecurityService.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Check for suspicious activity
            user = getattr(request, 'user', None) if hasattr(request, 'user') else None
            if user and user.is_authenticated:
                is_suspicious, reason = SecurityService.check_suspicious_activity(
                    user=user,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    action='request'
                )
                
                if is_suspicious:
                    SecurityService.log_security_event(
                        event_type='suspicious_activity',
                        ip_address=ip_address,
                        user=user,
                        severity='medium',
                        user_agent=user_agent,
                        details={
                            'path': request.path,
                            'method': request.method,
                            'reason': reason
                        }
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error in SecurityLoggingMiddleware: {str(e)}")
            return None
    
    def _should_log_request(self, request):
        """
        Determine if request should be logged.
        """
        # Log authentication-related requests
        if '/auth/' in request.path or '/api/auth/' in request.path:
            return True
        
        # Log admin access
        if request.path.startswith('/admin/'):
            return True
        
        # Log API requests
        if request.path.startswith('/api/') and request.method in ['POST', 'PUT', 'DELETE']:
            return True
        
        return False
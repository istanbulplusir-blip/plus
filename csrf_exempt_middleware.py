from django.utils.deprecation import MiddlewareMixin

class CSRFExemptAdminMiddleware(MiddlewareMixin):
    """
    Middleware to disable CSRF for admin URLs completely
    """
    def process_request(self, request):
        # Disable CSRF for admin URLs
        if request.path.startswith('/admin/'):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
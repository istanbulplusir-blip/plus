from django.contrib import admin
from django.urls import path, include
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin.views.decorators import staff_member_required

# Custom admin login view without CSRF
class CSRFExemptAdminSite(admin.AdminSite):
    def login(self, request, extra_context=None):
        # Temporarily disable CSRF for login
        view = csrf_exempt(super().login)
        return view(request, extra_context)

# Create custom admin site
admin_site = CSRFExemptAdminSite(name='admin')

# Register all models from default admin
admin_site._registry = admin.site._registry
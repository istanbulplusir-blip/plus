from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.views.i18n import set_language
from rest_framework_simplejwt.views import (TokenObtainPairView,
                                            TokenRefreshView, TokenVerifyView,
                                            TokenBlacklistView)
from drf_spectacular.views import (SpectacularAPIView, SpectacularRedocView,
                                   SpectacularSwaggerView)
from core.views import health_check, metrics, system_info

# Internationalization URL patterns
urlpatterns = i18n_patterns(
    # Frontend URLs
    path('users/', include(('users.urls.web', 'users'), namespace='users')),
    path('products/',
         include(('products.urls.web', 'products'), namespace='products')),
    path('cart/', include(('cart.urls.web', 'cart'), namespace='cart')),
    path('orders/', include(('orders.urls.web', 'orders'),
                            namespace='orders')),
    path('payments/',
         include(('payments.urls.web', 'payments'), namespace='payments')),
    path('', include('core.urls')),
    prefix_default_language=False)

# Non-internationalized URLs (API, admin, etc.)
urlpatterns += [
    path('admin/', admin.site.urls),
    # Internationalization URL
    path('i18n/setlang/', set_language, name='set_language'),
    # JWT Authentication URLs
    path(
        'api/token/',
        include([
            # Token URLs
            path('', TokenObtainPairView.as_view(), name='token_obtain_pair'),
            path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
            path('verify/', TokenVerifyView.as_view(), name='token_verify'),
            path('blacklist/',
                 TokenBlacklistView.as_view(),
                 name='token_blacklist'),
        ])),
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/',
         SpectacularSwaggerView.as_view(url_name='schema'),
         name='swagger-ui'),
    path('api/redoc/',
         SpectacularRedocView.as_view(url_name='schema'),
         name='redoc'),

    # API URLs
    path(
        'api/',
        include([
            # Health check and monitoring endpoints (must be before other API routes)
            path('health/', health_check, name='health_check'),
            path('metrics/', metrics, name='metrics'),
            path('system/', system_info, name='system_info'),
            path('auth/',
                 include(('users.urls.api', 'users'), namespace='api_auth')),
            path('users/',
                 include(('users.urls.api', 'users'), namespace='api_users')),
            path(
                'products/',
                include(('products.urls.api', 'products'),
                        namespace='api_products')),
            path('cart/',
                 include(('cart.urls.api', 'cart'), namespace='api_cart')),
            path(
                'orders/',
                include(('orders.urls.api', 'orders'),
                        namespace='api_orders')),
            path(
                'payments/',
                include(('payments.urls.api', 'payments'),
                        namespace='api_payments')),
        ])),
]

# Add media files serving in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    # Static files are automatically served by django.contrib.staticfiles in DEBUG mode

# Add media files serving in production (for WhiteNoise)
if not settings.DEBUG:
    from django.conf.urls.static import static
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)

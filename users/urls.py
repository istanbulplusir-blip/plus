from django.urls import include, path

urlpatterns = [
    path('', include('users.urls.web')),
    path('api/auth/', include('users.urls.api')),
    path('admin/security/', include('users.urls.monitoring')),
]

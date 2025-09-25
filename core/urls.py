from django.urls import path
from .views import HomePageView, about, contact

app_name = 'core'

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
    path('about/', about, name='about'),
    path('contact/', contact, name='contact'),
]

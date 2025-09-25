from django.urls import path
from products.views import (
    ProductListAPIView, ProductDetailAPIView,
    CategoryListAPIView, CategoryDetailAPIView,
    ProductSearchAPIView
)

app_name = 'api_products'

urlpatterns = [
    path('', ProductListAPIView.as_view(), name='product_list'),
    path('<int:pk>/', ProductDetailAPIView.as_view(), name='product_detail'),
    path('search/', ProductSearchAPIView.as_view(), name='product_search'),
    path('categories/', CategoryListAPIView.as_view(), name='category_list'),
    path('categories/<int:pk>/', CategoryDetailAPIView.as_view(), name='category_detail'),
]
from django.urls import path
from .views import CategoryListView, CategoryDetailView, ProductListView, ProductDetailView, ProductByCategoryView

app_name = 'products'

urlpatterns = [
    path('api/categories/', CategoryListView.as_view(), name='category-list'),
    path('api/categories/<int:pk>/', CategoryDetailView.as_view(), name='category-detail'),
    path('api/products/', ProductListView.as_view(), name='product-list'),
    path('api/products/<slug:slug>/', ProductDetailView.as_view(), name='product-detail'),
    path('api/categories/<slug:category_slug>/products/', ProductByCategoryView.as_view(), name='products-by-category'),
]

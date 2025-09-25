from django.urls import path
from products.views.web import (
    ProductListViewWeb as ProductListView,
    ProductDetailViewWeb as ProductDetailView,
    CategoryListViewWeb as CategoryListView,
    CategoryDetailViewWeb as CategoryDetailView
)

app_name = 'products'

urlpatterns = [
    path('', ProductListView.as_view(), name='product_list'),
    path('<slug:slug>/', ProductDetailView.as_view(), name='product_detail'),
    path('categories/', CategoryListView.as_view(), name='category_list'),
    path('categories/<slug:slug>/', CategoryDetailView.as_view(), name='category_detail'),
]

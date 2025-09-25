from typing import Any, Dict, cast
from django.views.generic import ListView, DetailView
from django.db.models.query import QuerySet
from django.http import HttpRequest
from products.models import Category, Product


class CategoryListViewWeb(ListView):
    model = Category
    template_name = 'products/category_list.html'
    context_object_name = 'categories'
    request: HttpRequest
    object: Category | None
    object_list: QuerySet[Category]

    def get_queryset(self) -> QuerySet[Category]:
        return cast(QuerySet[Category], Category.objects.filter(parent__isnull=True))


class CategoryDetailViewWeb(DetailView):
    model = Category
    template_name = 'products/category_detail.html'
    context_object_name = 'category'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    request: HttpRequest
    object: Category | None

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.object is not None:
            context['products'] = cast(QuerySet[Product], self.object.products.all())
        return context


class ProductListViewWeb(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    request: HttpRequest
    object: Product | None
    object_list: QuerySet[Product]

    def get_queryset(self) -> QuerySet[Product]:
        queryset = cast(QuerySet[Product], super().get_queryset())
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(categories__id=category_id)
        return queryset

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['categories'] = cast(QuerySet[Category], 
            Category.objects.filter(parent__isnull=True))
        return context


class ProductDetailViewWeb(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_field = 'slug'
    slug_url_kwarg = 'slug'
    query_pk_and_slug = True
    request: HttpRequest
    object: Product | None

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.object is not None:
            context['related_products'] = cast(QuerySet[Product],
                Product.objects.filter(categories__in=self.object.categories.all())
                .exclude(id=self.object.id)
                .distinct()[:4]
            )
        return context


class ProductByCategoryViewWeb(ListView):
    model = Product
    template_name = 'products/product_by_category.html'
    context_object_name = 'products'
    paginate_by = 12
    request: HttpRequest
    object: Product | None
    object_list: QuerySet[Product]
    
    def get_queryset(self) -> QuerySet[Product]:
        category_slug = self.kwargs['category_slug']
        return cast(QuerySet[Product], 
            Product.objects.filter(categories__slug=category_slug))

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['category'] = cast(Category, 
            Category.objects.get(slug=self.kwargs['category_slug']))
        return context

from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from mptt.admin import MPTTModelAdmin
from .models import Category, Product, ProductImage, ProductFile


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'image_preview')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return '-'
    image_preview.short_description = 'پیش‌نمایش'


class ProductFileInline(admin.TabularInline):
    model = ProductFile
    extra = 1
    fields = ('file', 'download_limit', 'file_preview')
    readonly_fields = ('file_preview',)
    
    def file_preview(self, obj):
        if obj.pk and obj.file:
            return format_html(
                '<a href="{}" target="_blank">دانلود فایل</a>',
                obj.file.url
            )
        return '-'
    file_preview.short_description = 'فایل'


@admin.register(Category)
class CategoryAdmin(MPTTModelAdmin):
    list_display = ('name', 'slug', 'parent', 'product_count', 'level')
    list_filter = ('parent',)
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = (
        ('اطلاعات دسته‌بندی', {
            'fields': ('name', 'slug', 'parent', 'description')
        }),
    )
    
    def product_count(self, obj):
        count = obj.products.count()
        if count > 0:
            url = reverse('admin:products_product_changelist') + f'?categories__id__exact={obj.id}'
            return format_html('<a href="{}">{} محصول</a>', url, count)
        return '0 محصول'
    product_count.short_description = 'تعداد محصولات'
    
    def level(self, obj):
        return obj.level
    level.short_description = 'سطح'


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'name', 
        'slug', 
        'price_display', 
        'stock_display', 
        'type_display', 
        'is_active_display',
        'is_featured_display',
        'category_list',
        'created_at'
    )
    list_filter = ('type', 'is_active', 'is_featured', 'categories', 'created_at')
    search_fields = ('name', 'slug', 'description')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    inlines = [ProductImageInline, ProductFileInline]
    
    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': ('name', 'slug', 'description', 'type', 'is_active', 'is_featured')
        }),
        ('قیمت‌گذاری و موجودی', {
            'fields': ('price', 'stock')
        }),
        ('تصویر محصول', {
            'fields': ('image', 'image_preview')
        }),
        ('دسته‌بندی‌ها', {
            'fields': ('categories',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_products', 'deactivate_products', 'mark_as_featured', 'unmark_as_featured']
    
    def price_display(self, obj):
        return f"{obj.price:,} تومان"
    price_display.short_description = 'قیمت'
    price_display.admin_order_field = 'price'
    
    def stock_display(self, obj):
        if obj.type == Product.DIGITAL:
            return 'نامحدود'
        return f"{obj.stock} عدد"
    stock_display.short_description = 'موجودی'
    stock_display.admin_order_field = 'stock'
    
    def type_display(self, obj):
        type_colors = {
            Product.PHYSICAL: '#17a2b8',
            Product.DIGITAL: '#28a745'
        }
        color = type_colors.get(obj.type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_type_display()
        )
    type_display.short_description = 'نوع'
    type_display.admin_order_field = 'type'
    
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color: #28a745;">✓ فعال</span>')
        return format_html('<span style="color: #dc3545;">✗ غیرفعال</span>')
    is_active_display.short_description = 'وضعیت'
    is_active_display.admin_order_field = 'is_active'
    
    def is_featured_display(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: #ffc107;">⭐ ویژه</span>')
        return '-'
    is_featured_display.short_description = 'ویژه'
    is_featured_display.admin_order_field = 'is_featured'
    
    def category_list(self, obj):
        categories = obj.categories.all()[:3]  # Show first 3 categories
        if categories:
            category_links = []
            for category in categories:
                url = reverse('admin:products_category_change', args=[category.pk])
                category_links.append(f'<a href="{url}">{category.name}</a>')
            result = ', '.join(category_links)
            if obj.categories.count() > 3:
                result += f' و {obj.categories.count() - 3} مورد دیگر'
            return format_html(result)
        return '-'
    category_list.short_description = 'دسته‌بندی‌ها'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 200px; max-width: 200px;" />',
                obj.image.url
            )
        return 'تصویری انتخاب نشده'
    image_preview.short_description = 'پیش‌نمایش تصویر'
    
    def activate_products(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} محصول فعال شد.')
    activate_products.short_description = 'فعال کردن محصولات انتخاب شده'
    
    def deactivate_products(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} محصول غیرفعال شد.')
    deactivate_products.short_description = 'غیرفعال کردن محصولات انتخاب شده'
    
    def mark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} محصول به عنوان ویژه علامت‌گذاری شد.')
    mark_as_featured.short_description = 'علامت‌گذاری به عنوان ویژه'
    
    def unmark_as_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} محصول از حالت ویژه خارج شد.')
    unmark_as_featured.short_description = 'خروج از حالت ویژه'
    
    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('categories', 'images', 'file')


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_display', 'alt_text', 'image_preview')
    list_filter = ('product__type', 'product__categories')
    search_fields = ('product__name', 'alt_text')
    readonly_fields = ('image_preview',)
    
    def product_display(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_display.short_description = 'محصول'
    product_display.admin_order_field = 'product__name'
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px;" />',
                obj.image.url
            )
        return 'تصویری وجود ندارد'
    image_preview.short_description = 'پیش‌نمایش'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(ProductFile)
class ProductFileAdmin(admin.ModelAdmin):
    list_display = ('id', 'product_display', 'file_display', 'download_limit', 'file_size')
    list_filter = ('product__type', 'product__categories')
    search_fields = ('product__name',)
    readonly_fields = ('file_display', 'file_size')
    
    def product_display(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_display.short_description = 'محصول'
    product_display.admin_order_field = 'product__name'
    
    def file_display(self, obj):
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">دانلود فایل</a>',
                obj.file.url
            )
        return 'فایلی وجود ندارد'
    file_display.short_description = 'فایل'
    
    def file_size(self, obj):
        if obj.file:
            try:
                size = obj.file.size
                if size < 1024:
                    return f"{size} B"
                elif size < 1024 * 1024:
                    return f"{size / 1024:.1f} KB"
                else:
                    return f"{size / (1024 * 1024):.1f} MB"
            except:
                return 'نامشخص'
        return '-'
    file_size.short_description = 'اندازه فایل'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')

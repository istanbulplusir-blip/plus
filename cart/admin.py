from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at',)
    fields = ('product', 'quantity', 'added_at')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product')


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user_display', 
        'session_key_display', 
        'item_count', 
        'total_price_display', 
        'created_at', 
        'updated_at'
    )
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email', 'session_key')
    readonly_fields = ('created_at', 'updated_at', 'total_price_display', 'item_count_display')
    inlines = [CartItemInline]
    
    fieldsets = (
        ('اطلاعات سبد خرید', {
            'fields': ('user', 'session_key', 'created_at', 'updated_at')
        }),
        ('خلاصه', {
            'fields': ('total_price_display', 'item_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    def user_display(self, obj):
        if obj.user:
            url = reverse('admin:users_user_change', args=[obj.user.pk])
            return format_html('<a href="{}">{}</a>', url, obj.user.username)
        return 'مهمان'
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'
    
    def session_key_display(self, obj):
        if obj.session_key:
            return obj.session_key[:8] + '...' if len(obj.session_key) > 8 else obj.session_key
        return '-'
    session_key_display.short_description = 'کلید جلسه'
    
    def total_price_display(self, obj):
        return f"{obj.total_price:,} تومان"
    total_price_display.short_description = 'مجموع قیمت'
    
    def item_count_display(self, obj):
        return f"{obj.item_count} آیتم"
    item_count_display.short_description = 'تعداد آیتم‌ها'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'cart_display', 
        'product_display', 
        'quantity', 
        'unit_price_display', 
        'total_price_display', 
        'added_at'
    )
    list_filter = ('added_at', 'product__type', 'product__categories')
    search_fields = ('product__name', 'cart__user__username', 'cart__session_key')
    readonly_fields = ('added_at', 'unit_price_display', 'total_price_display')
    
    fieldsets = (
        ('اطلاعات آیتم', {
            'fields': ('cart', 'product', 'quantity', 'added_at')
        }),
        ('قیمت‌گذاری', {
            'fields': ('unit_price_display', 'total_price_display'),
            'classes': ('collapse',)
        }),
    )
    
    def cart_display(self, obj):
        url = reverse('admin:cart_cart_change', args=[obj.cart.pk])
        if obj.cart.user:
            return format_html('<a href="{}">سبد {} ({})</a>', url, obj.cart.pk, obj.cart.user.username)
        else:
            return format_html('<a href="{}">سبد {} (مهمان)</a>', url, obj.cart.pk)
    cart_display.short_description = 'سبد خرید'
    cart_display.admin_order_field = 'cart__id'
    
    def product_display(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_display.short_description = 'محصول'
    product_display.admin_order_field = 'product__name'
    
    def unit_price_display(self, obj):
        return f"{obj.product.price:,} تومان"
    unit_price_display.short_description = 'قیمت واحد'
    
    def total_price_display(self, obj):
        total = obj.product.price * obj.quantity
        return f"{total:,} تومان"
    total_price_display.short_description = 'قیمت کل'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('cart__user', 'product')

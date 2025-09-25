from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product_display', 'unit_price_display', 'total_price_display')
    fields = ('product', 'quantity', 'price', 'product_file', 'product_display', 'unit_price_display', 'total_price_display')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'product_file')
    
    def product_display(self, obj):
        if obj.pk:
            url = reverse('admin:products_product_change', args=[obj.product.pk])
            return format_html('<a href="{}" target="_blank">{}</a>', url, obj.product.name)
        return '-'
    product_display.short_description = 'محصول'
    
    def unit_price_display(self, obj):
        if obj.pk:
            return f"{obj.price:,} تومان"
        return '-'
    unit_price_display.short_description = 'قیمت واحد'
    
    def total_price_display(self, obj):
        if obj.pk:
            total = obj.price * obj.quantity
            return f"{total:,} تومان"
        return '-'
    total_price_display.short_description = 'قیمت کل'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'user_display', 
        'status_display', 
        'total_amount_display', 
        'item_count', 
        'billing_name', 
        'billing_phone', 
        'created_at', 
        'updated_at'
    )
    list_filter = ('status', 'created_at', 'updated_at', 'billing_city')
    search_fields = (
        'user__username', 
        'user__email', 
        'billing_name', 
        'billing_phone', 
        'billing_address',
        'billing_city'
    )
    readonly_fields = ('created_at', 'updated_at', 'total_amount_display', 'item_count_display')
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('اطلاعات سفارش', {
            'fields': ('user', 'status', 'created_at', 'updated_at')
        }),
        ('اطلاعات تحویل گیرنده', {
            'fields': ('billing_name', 'billing_phone', 'billing_address', 'billing_city')
        }),
        ('خلاصه سفارش', {
            'fields': ('total_amount_display', 'item_count_display'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_paid', 'mark_as_shipped', 'mark_as_completed', 'mark_as_cancelled']
    
    def user_display(self, obj):
        url = reverse('admin:users_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_display.short_description = 'کاربر'
    user_display.admin_order_field = 'user__username'
    
    def status_display(self, obj):
        status_colors = {
            'pending': '#ffc107',
            'paid': '#28a745',
            'shipped': '#17a2b8',
            'completed': '#6f42c1',
            'cancelled': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    status_display.admin_order_field = 'status'
    
    def total_amount_display(self, obj):
        total = sum(item.price * item.quantity for item in obj.items.all())
        return f"{total:,} تومان"
    total_amount_display.short_description = 'مجموع مبلغ'
    
    def item_count_display(self, obj):
        count = sum(item.quantity for item in obj.items.all())
        return f"{count} آیتم"
    item_count_display.short_description = 'تعداد آیتم‌ها'
    
    def item_count(self, obj):
        count = sum(item.quantity for item in obj.items.all())
        return count
    item_count.short_description = 'تعداد'
    
    def mark_as_paid(self, request, queryset):
        updated = queryset.filter(status='pending').update(status='paid')
        self.message_user(request, f'{updated} سفارش به وضعیت "پرداخت شده" تغییر یافت.')
    mark_as_paid.short_description = 'تغییر وضعیت به پرداخت شده'
    
    def mark_as_shipped(self, request, queryset):
        updated = queryset.filter(status='paid').update(status='shipped')
        self.message_user(request, f'{updated} سفارش به وضعیت "ارسال شده" تغییر یافت.')
    mark_as_shipped.short_description = 'تغییر وضعیت به ارسال شده'
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.filter(status='shipped').update(status='completed')
        self.message_user(request, f'{updated} سفارش به وضعیت "تکمیل شده" تغییر یافت.')
    mark_as_completed.short_description = 'تغییر وضعیت به تکمیل شده'
    
    def mark_as_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} سفارش لغو شد.')
    mark_as_cancelled.short_description = 'لغو سفارش‌ها'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('items__product')


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order_display', 
        'product_display', 
        'quantity', 
        'unit_price_display', 
        'total_price_display', 
        'product_file_display'
    )
    list_filter = ('order__status', 'product__type', 'product__categories')
    search_fields = ('product__name', 'order__user__username', 'order__billing_name')
    readonly_fields = ('unit_price_display', 'total_price_display')
    
    fieldsets = (
        ('اطلاعات آیتم سفارش', {
            'fields': ('order', 'product', 'quantity', 'price', 'product_file')
        }),
        ('قیمت‌گذاری', {
            'fields': ('unit_price_display', 'total_price_display'),
            'classes': ('collapse',)
        }),
    )
    
    def order_display(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html('<a href="{}">سفارش {} ({})</a>', url, obj.order.pk, obj.order.user.username)
    order_display.short_description = 'سفارش'
    order_display.admin_order_field = 'order__id'
    
    def product_display(self, obj):
        url = reverse('admin:products_product_change', args=[obj.product.pk])
        return format_html('<a href="{}">{}</a>', url, obj.product.name)
    product_display.short_description = 'محصول'
    product_display.admin_order_field = 'product__name'
    
    def unit_price_display(self, obj):
        return f"{obj.price:,} تومان"
    unit_price_display.short_description = 'قیمت واحد'
    
    def total_price_display(self, obj):
        total = obj.price * obj.quantity
        return f"{total:,} تومان"
    total_price_display.short_description = 'قیمت کل'
    
    def product_file_display(self, obj):
        if obj.product_file and obj.product_file.file:
            return format_html(
                '<a href="{}" target="_blank">دانلود فایل</a>',
                obj.product_file.file.url
            )
        return '-'
    product_file_display.short_description = 'فایل محصول'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order__user', 'product', 'product_file')

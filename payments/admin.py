from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'id', 
        'order_display', 
        'amount_display', 
        'status_display', 
        'tracking_code_display', 
        'created_at',
        'gateway_display'
    )
    list_filter = ('status', 'created_at', 'order__status')
    search_fields = (
        'tracking_code', 
        'order__user__username', 
        'order__user__email',
        'order__billing_name',
        'order__billing_phone'
    )
    readonly_fields = ('created_at', 'raw_response_display', 'gateway_display')
    
    fieldsets = (
        ('اطلاعات پرداخت', {
            'fields': ('order', 'amount', 'status', 'tracking_code', 'created_at')
        }),
        ('اطلاعات درگاه', {
            'fields': ('gateway_display',),
            'classes': ('collapse',)
        }),
        ('پاسخ درگاه', {
            'fields': ('raw_response_display',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_success', 'mark_as_failed']
    
    def order_display(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.order.pk])
        return format_html(
            '<a href="{}">سفارش {} ({})</a>',
            url, 
            obj.order.pk, 
            obj.order.user.username
        )
    order_display.short_description = 'سفارش'
    order_display.admin_order_field = 'order__id'
    
    def amount_display(self, obj):
        return f"{obj.amount:,} تومان"
    amount_display.short_description = 'مبلغ'
    amount_display.admin_order_field = 'amount'
    
    def status_display(self, obj):
        status_colors = {
            'initiated': '#ffc107',
            'success': '#28a745',
            'failed': '#dc3545'
        }
        color = status_colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'وضعیت'
    status_display.admin_order_field = 'status'
    
    def tracking_code_display(self, obj):
        if obj.tracking_code:
            return format_html(
                '<code style="background: #f8f9fa; padding: 2px 4px; border-radius: 3px;">{}</code>',
                obj.tracking_code
            )
        return '-'
    tracking_code_display.short_description = 'کد پیگیری'
    
    def gateway_display(self, obj):
        """Extract gateway information from raw_response"""
        if obj.raw_response:
            try:
                import json
                response_data = json.loads(obj.raw_response)
                gateway = response_data.get('gateway', 'نامشخص')
                return format_html(
                    '<span style="background: #e9ecef; padding: 2px 6px; border-radius: 3px;">{}</span>',
                    gateway
                )
            except:
                return 'نامشخص'
        return '-'
    gateway_display.short_description = 'درگاه پرداخت'
    
    def raw_response_display(self, obj):
        if obj.raw_response:
            try:
                import json
                response_data = json.loads(obj.raw_response)
                formatted_json = json.dumps(response_data, indent=2, ensure_ascii=False)
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; max-height: 300px; overflow-y: auto;">{}</pre>',
                    formatted_json
                )
            except:
                return format_html(
                    '<pre style="background: #f8f9fa; padding: 10px; border-radius: 5px;">{}</pre>',
                    obj.raw_response
                )
        return '-'
    raw_response_display.short_description = 'پاسخ کامل درگاه'
    
    def mark_as_success(self, request, queryset):
        updated = queryset.filter(status='initiated').update(status='success')
        self.message_user(request, f'{updated} پرداخت به وضعیت "موفق" تغییر یافت.')
    mark_as_success.short_description = 'تغییر وضعیت به موفق'
    
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} پرداخت به وضعیت "ناموفق" تغییر یافت.')
    mark_as_failed.short_description = 'تغییر وضعیت به ناموفق'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('order__user')
    
    def has_add_permission(self, request):
        """Prevent manual creation of payments"""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of payments"""
        return False

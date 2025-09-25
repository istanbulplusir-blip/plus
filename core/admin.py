from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from .models import (
    SiteConfiguration, ContactInformation, SocialMediaLink, 
    NavigationMenu, SiteContent, SiteAnnouncement, 
    SiteStatistics, HeroCard, HeroSection
)


@admin.register(SiteConfiguration)
class SiteConfigurationAdmin(admin.ModelAdmin):
    """Admin interface for Site Configuration"""
    
    list_display = ('site_name', 'site_domain', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('site_name', 'site_domain', 'site_tagline')
    readonly_fields = ('created_at', 'updated_at', 'logo_preview', 'favicon_preview', 'og_image_preview')
    
    fieldsets = (
        ('اطلاعات برند', {
            'fields': ('site_name', 'site_tagline', 'site_domain', 'is_active')
        }),
        ('لوگوها', {
            'fields': ('logo_high_quality', 'logo_preview', 'logo_low_quality', 'favicon', 'favicon_preview')
        }),
        ('تنظیمات SEO', {
            'fields': ('default_meta_description', 'default_meta_keywords', 'default_og_image', 'og_image_preview')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def logo_preview(self, obj):
        if obj.logo_high_quality:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.logo_high_quality.url
            )
        return 'لوگویی انتخاب نشده'
    logo_preview.short_description = 'پیش‌نمایش لوگو'
    
    def favicon_preview(self, obj):
        if obj.favicon:
            return format_html(
                '<img src="{}" style="max-height: 32px; max-width: 32px;" />',
                obj.favicon.url
            )
        return 'فاویکونی انتخاب نشده'
    favicon_preview.short_description = 'پیش‌نمایش فاویکون'
    
    def og_image_preview(self, obj):
        if obj.default_og_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.default_og_image.url
            )
        return 'تصویری انتخاب نشده'
    og_image_preview.short_description = 'پیش‌نمایش تصویر OG'
    
    def has_add_permission(self, request):
        """Allow only one configuration"""
        return not SiteConfiguration.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the only configuration"""
        return False


@admin.register(ContactInformation)
class ContactInformationAdmin(admin.ModelAdmin):
    """Admin interface for Contact Information"""
    
    list_display = ('title', 'contact_type', 'value', 'display_order', 'is_active', 'is_clickable')
    list_filter = ('contact_type', 'is_active', 'is_clickable')
    search_fields = ('title', 'value')
    list_editable = ('display_order', 'is_active', 'is_clickable')
    ordering = ('display_order', 'contact_type')
    
    fieldsets = (
        ('اطلاعات تماس', {
            'fields': ('contact_type', 'title', 'value', 'icon_class')
        }),
        ('تنظیمات نمایش', {
            'fields': ('display_order', 'is_active', 'is_clickable')
        }),
    )
    
    actions = ['activate_contacts', 'deactivate_contacts']
    
    def activate_contacts(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} اطلاعات تماس فعال شد.')
    activate_contacts.short_description = 'فعال کردن اطلاعات تماس انتخاب شده'
    
    def deactivate_contacts(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} اطلاعات تماس غیرفعال شد.')
    deactivate_contacts.short_description = 'غیرفعال کردن اطلاعات تماس انتخاب شده'


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    """Admin interface for Social Media Links"""
    
    list_display = ('display_name', 'platform', 'url', 'display_order', 'is_active')
    list_filter = ('platform', 'is_active', 'open_in_new_tab')
    search_fields = ('display_name', 'url')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'platform')
    
    fieldsets = (
        ('اطلاعات لینک', {
            'fields': ('platform', 'display_name', 'url', 'icon_class')
        }),
        ('تنظیمات نمایش', {
            'fields': ('display_order', 'is_active', 'open_in_new_tab')
        }),
    )
    
    actions = ['activate_links', 'deactivate_links']
    
    def activate_links(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} لینک شبکه اجتماعی فعال شد.')
    activate_links.short_description = 'فعال کردن لینک‌های انتخاب شده'
    
    def deactivate_links(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} لینک شبکه اجتماعی غیرفعال شد.')
    deactivate_links.short_description = 'غیرفعال کردن لینک‌های انتخاب شده'


@admin.register(NavigationMenu)
class NavigationMenuAdmin(admin.ModelAdmin):
    """Admin interface for Navigation Menu"""
    
    list_display = ('title', 'menu_type', 'url', 'display_order', 'is_active', 'is_external')
    list_filter = ('menu_type', 'is_active', 'is_external', 'open_in_new_tab')
    search_fields = ('title', 'url')
    list_editable = ('display_order', 'is_active')
    ordering = ('menu_type', 'display_order', 'title')
    
    fieldsets = (
        ('اطلاعات منو', {
            'fields': ('menu_type', 'title', 'url', 'icon_class')
        }),
        ('تنظیمات نمایش', {
            'fields': ('display_order', 'is_active', 'is_external', 'open_in_new_tab')
        }),
    )
    
    actions = ['activate_menus', 'deactivate_menus']
    
    def activate_menus(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} آیتم منو فعال شد.')
    activate_menus.short_description = 'فعال کردن آیتم‌های منو انتخاب شده'
    
    def deactivate_menus(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} آیتم منو غیرفعال شد.')
    deactivate_menus.short_description = 'غیرفعال کردن آیتم‌های منو انتخاب شده'


@admin.register(SiteContent)
class SiteContentAdmin(admin.ModelAdmin):
    """Admin interface for Site Content"""
    
    list_display = ('title', 'content_type', 'is_active', 'created_at', 'updated_at')
    list_filter = ('content_type', 'is_active', 'created_at')
    search_fields = ('title', 'content', 'short_description')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات محتوا', {
            'fields': ('content_type', 'title', 'short_description', 'is_active')
        }),
        ('محتوای کامل', {
            'fields': ('content',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_contents', 'deactivate_contents']
    
    def activate_contents(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} محتوا فعال شد.')
    activate_contents.short_description = 'فعال کردن محتوای انتخاب شده'
    
    def deactivate_contents(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} محتوا غیرفعال شد.')
    deactivate_contents.short_description = 'غیرفعال کردن محتوای انتخاب شده'


@admin.register(SiteAnnouncement)
class SiteAnnouncementAdmin(admin.ModelAdmin):
    """Admin interface for Site Announcements"""
    
    list_display = ('title', 'announcement_type', 'is_active', 'show_on_homepage', 'show_in_navbar', 'start_date', 'end_date')
    list_filter = ('announcement_type', 'is_active', 'show_on_homepage', 'show_in_navbar', 'start_date', 'end_date')
    search_fields = ('title', 'message')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('اطلاعات اعلان', {
            'fields': ('announcement_type', 'title', 'message', 'is_active')
        }),
        ('تنظیمات نمایش', {
            'fields': ('show_on_homepage', 'show_in_navbar')
        }),
        ('زمان‌بندی', {
            'fields': ('start_date', 'end_date')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_announcements', 'deactivate_announcements']
    
    def activate_announcements(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} اعلان فعال شد.')
    activate_announcements.short_description = 'فعال کردن اعلانات انتخاب شده'
    
    def deactivate_announcements(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} اعلان غیرفعال شد.')
    deactivate_announcements.short_description = 'غیرفعال کردن اعلانات انتخاب شده'


@admin.register(SiteStatistics)
class SiteStatisticsAdmin(admin.ModelAdmin):
    """Admin interface for Site Statistics"""
    
    list_display = ('total_products', 'total_customers', 'total_orders', 'established_year', 'updated_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('آمار عمومی', {
            'fields': ('total_products', 'total_customers', 'total_orders')
        }),
        ('اطلاعات اعتماد', {
            'fields': ('trust_badges',)
        }),
        ('اطلاعات اضافی', {
            'fields': ('established_year', 'license_number')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        """Allow only one statistics record"""
        return not SiteStatistics.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of statistics"""
        return False


@admin.register(HeroCard)
class HeroCardAdmin(admin.ModelAdmin):
    """Admin interface for Hero Cards"""
    
    list_display = ('title', 'subtitle', 'price', 'display_order', 'is_active', 'image_preview')
    list_filter = ('is_active', 'open_in_new_tab', 'created_at')
    search_fields = ('title', 'subtitle', 'price')
    list_editable = ('display_order', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'image_preview')
    ordering = ('display_order', 'title')
    
    fieldsets = (
        ('اطلاعات کارت', {
            'fields': ('title', 'subtitle', 'price', 'image', 'image_preview')
        }),
        ('لینک و تنظیمات', {
            'fields': ('link_url', 'link_text', 'display_order', 'is_active', 'open_in_new_tab')
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 150px;" />',
                obj.image.url
            )
        return 'تصویری انتخاب نشده'
    image_preview.short_description = 'پیش‌نمایش تصویر'
    
    actions = ['activate_cards', 'deactivate_cards']
    
    def activate_cards(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} کارت Hero فعال شد.')
    activate_cards.short_description = 'فعال کردن کارت‌های انتخاب شده'
    
    def deactivate_cards(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} کارت Hero غیرفعال شد.')
    deactivate_cards.short_description = 'غیرفعال کردن کارت‌های انتخاب شده'


@admin.register(HeroSection)
class HeroSectionAdmin(admin.ModelAdmin):
    """Admin interface for Hero Section Configuration"""
    
    list_display = ('background_type', 'animation_enabled', 'show_cards', 'cards_count', 'is_active')
    list_filter = ('background_type', 'animation_enabled', 'show_particles', 'show_cards', 'is_active')
    readonly_fields = ('created_at', 'updated_at', 'background_preview')
    
    fieldsets = (
        ('تنظیمات پس‌زمینه', {
            'fields': ('background_type', 'background_color', 'background_gradient_start', 'background_gradient_end', 'background_image', 'background_preview')
        }),
        ('تنظیمات انیمیشن', {
            'fields': ('animation_enabled', 'animation_speed', 'show_particles')
        }),
        ('تنظیمات محتوا', {
            'fields': ('show_cards', 'cards_count')
        }),
        ('وضعیت', {
            'fields': ('is_active',)
        }),
        ('تاریخ‌ها', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def background_preview(self, obj):
        if obj.background_image:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 200px;" />',
                obj.background_image.url
            )
        elif obj.background_type == 'gradient':
            return format_html(
                '<div style="width: 200px; height: 50px; background: linear-gradient(45deg, {}, {}); border: 1px solid #ccc;"></div>',
                obj.background_gradient_start,
                obj.background_gradient_end
            )
        elif obj.background_type == 'solid':
            return format_html(
                '<div style="width: 200px; height: 50px; background-color: {}; border: 1px solid #ccc;"></div>',
                obj.background_color
            )
        return 'پیش‌نمایشی در دسترس نیست'
    background_preview.short_description = 'پیش‌نمایش پس‌زمینه'
    
    def has_add_permission(self, request):
        """Allow only one hero configuration"""
        return not HeroSection.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of the only hero configuration"""
        return False
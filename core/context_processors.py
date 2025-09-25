from django.utils.translation import gettext_lazy as _
from .models import (
    SiteConfiguration, ContactInformation, SocialMediaLink,
    NavigationMenu, SiteContent, SiteAnnouncement, SiteStatistics,
    HeroCard, HeroSection
)


def site_context(request):
    """
    Context processor برای اضافه کردن اطلاعات سایت به تمام تمپلیت‌ها
    """
    context = {}
    
    try:
        # تنظیمات اصلی سایت
        site_config = SiteConfiguration.get_active_config()
        if site_config:
            context.update({
                'site_config': site_config,
                'site_name': site_config.site_name,
                'site_tagline': site_config.site_tagline,
                'site_domain': site_config.site_domain,
                'site_logo_high': site_config.logo_high_quality,
                'site_logo_low': site_config.logo_low_quality,
                'site_favicon': site_config.favicon,
                'default_meta_description': site_config.default_meta_description,
                'default_meta_keywords': site_config.default_meta_keywords,
                'default_og_image': site_config.default_og_image,
            })
        
        # اطلاعات تماس
        contact_info = ContactInformation.objects.filter(is_active=True).order_by('display_order')
        context['contact_info'] = contact_info
        
        # لینک‌های شبکه‌های اجتماعی
        social_links = SocialMediaLink.objects.filter(is_active=True).order_by('display_order')
        context['social_links'] = social_links
        
        # منوهای ناوبری
        main_menu = NavigationMenu.objects.filter(
            menu_type='main', is_active=True
        ).order_by('display_order')
        context['main_menu'] = main_menu
        
        footer_menu = NavigationMenu.objects.filter(
            menu_type='footer', is_active=True
        ).order_by('display_order')
        context['footer_menu'] = footer_menu
        
        quick_access_menu = NavigationMenu.objects.filter(
            menu_type='quick_access', is_active=True
        ).order_by('display_order')
        context['quick_access_menu'] = quick_access_menu
        
        customer_service_menu = NavigationMenu.objects.filter(
            menu_type='customer_service', is_active=True
        ).order_by('display_order')
        context['customer_service_menu'] = customer_service_menu
        
        # محتوای سایت
        site_contents = {}
        for content in SiteContent.objects.filter(is_active=True):
            site_contents[content.content_type] = content
        context['site_contents'] = site_contents
        
        # اعلانات فعال
        active_announcements = SiteAnnouncement.objects.filter(
            is_active=True
        ).order_by('-created_at')
        context['active_announcements'] = active_announcements
        
        # آمار سایت
        site_stats = SiteStatistics.get_current_stats()
        context['site_stats'] = site_stats
        
        # کارت‌های Hero
        hero_cards = HeroCard.objects.filter(is_active=True).order_by('display_order')
        context['hero_cards'] = hero_cards
        
        # تنظیمات Hero
        hero_config = HeroSection.get_active_config()
        context['hero_config'] = hero_config
        
    except Exception as e:
        # در صورت بروز خطا، مقادیر پیش‌فرض تنظیم می‌شود
        context.update({
            'site_name': 'Istanbul Plus',
            'site_domain': 'istanbulplus.ir',
            'contact_info': [],
            'social_links': [],
            'main_menu': [],
            'footer_menu': [],
            'quick_access_menu': [],
            'customer_service_menu': [],
            'site_contents': {},
            'active_announcements': [],
            'site_stats': None,
            'hero_cards': [],
            'hero_config': None,
        })
    
    return context


def navigation_context(request):
    """
    Context processor مخصوص ناوبری
    """
    context = {}
    
    try:
        # منوی اصلی
        main_menu = NavigationMenu.objects.filter(
            menu_type='main', is_active=True
        ).order_by('display_order')
        
        # تشخیص صفحه فعلی
        current_path = request.path
        for item in main_menu:
            if item.url == current_path or (item.url != '/' and current_path.startswith(item.url)):
                item.is_current = True
                break
        
        context['navigation_menu'] = main_menu
        
    except Exception:
        context['navigation_menu'] = []
    
    return context


def footer_context(request):
    """
    Context processor مخصوص فوتر
    """
    context = {}
    
    try:
        # اطلاعات تماس برای فوتر
        contact_info = ContactInformation.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        # لینک‌های شبکه‌های اجتماعی
        social_links = SocialMediaLink.objects.filter(
            is_active=True
        ).order_by('display_order')
        
        # محتوای فوتر
        footer_description = SiteContent.objects.filter(
            content_type='footer_description', is_active=True
        ).first()
        
        context.update({
            'footer_contact_info': contact_info,
            'footer_social_links': social_links,
            'footer_description': footer_description,
        })
        
    except Exception:
        context.update({
            'footer_contact_info': [],
            'footer_social_links': [],
            'footer_description': None,
        })
    
    return context


def seo_context(request):
    """
    Context processor مخصوص SEO
    """
    context = {}
    
    try:
        site_config = SiteConfiguration.get_active_config()
        if site_config:
            context.update({
                'seo_title': site_config.site_name,
                'seo_description': site_config.default_meta_description,
                'seo_keywords': site_config.default_meta_keywords,
                'seo_image': site_config.default_og_image,
                'seo_site_name': site_config.site_name,
            })
    except Exception:
        context.update({
            'seo_title': 'Istanbul Plus',
            'seo_description': 'فروشگاه آنلاین Istanbul Plus - محصولات با کیفیت و ارسال سریع',
            'seo_keywords': 'فروشگاه آنلاین, خرید اینترنتی, Istanbul Plus',
            'seo_image': None,
            'seo_site_name': 'Istanbul Plus',
        })
    
    return context

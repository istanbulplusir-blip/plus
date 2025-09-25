from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.db import models
from core.models import SiteConfiguration, ContactInformation, SocialMediaLink, HeroCard, HeroSection

register = template.Library()


@register.simple_tag
def get_site_config():
    """دریافت تنظیمات سایت"""
    return SiteConfiguration.get_active_config()


@register.simple_tag
def get_contact_info(contact_type=None):
    """دریافت اطلاعات تماس"""
    queryset = ContactInformation.objects.filter(is_active=True)
    if contact_type:
        queryset = queryset.filter(contact_type=contact_type)
    return queryset.order_by('display_order')


@register.simple_tag
def get_social_links():
    """دریافت لینک‌های شبکه‌های اجتماعی"""
    return SocialMediaLink.objects.filter(is_active=True).order_by('display_order')


@register.simple_tag
def get_contact_url(contact_info):
    """دریافت URL قابل کلیک برای اطلاعات تماس"""
    if not contact_info.is_clickable:
        return None
    
    if contact_info.contact_type == 'email':
        return f"mailto:{contact_info.value}"
    elif contact_info.contact_type in ['phone', 'mobile']:
        return f"tel:{contact_info.value}"
    elif contact_info.contact_type == 'whatsapp':
        # حذف کاراکترهای غیرعددی و اضافه کردن کد کشور
        clean_number = contact_info.value.replace('+', '').replace('-', '').replace(' ', '')
        if clean_number.startswith('0'):
            clean_number = '98' + clean_number[1:]
        return f"https://wa.me/{clean_number}"
    elif contact_info.contact_type == 'telegram':
        return f"https://t.me/{contact_info.value}"
    
    return None


@register.filter
def get_contact_by_type(queryset, contact_type):
    """فیلتر اطلاعات تماس بر اساس نوع"""
    return queryset.filter(contact_type=contact_type)


@register.simple_tag
def render_logo(size='medium', quality='high', logo_context='', show_text=True, text_class=''):
    """رندر لوگو با پارامترهای مختلف"""
    site_config = SiteConfiguration.get_active_config()
    if not site_config:
        return mark_safe('<span>Istanbul Plus</span>')
    
    # انتخاب فایل لوگو
    if quality == 'low':
        logo_file = site_config.logo_low_quality
    else:
        logo_file = site_config.logo_high_quality
    
    # تعیین ابعاد
    size_map = {
        'small': {'width': 24, 'height': 24, 'class': 'logo-small'},
        'medium': {'width': 32, 'height': 32, 'class': 'logo-medium'},
        'large': {'width': 48, 'height': 48, 'class': 'logo-large'},
        'xlarge': {'width': 64, 'height': 64, 'class': 'logo-xlarge'},
    }
    
    dimensions = size_map.get(size, size_map['medium'])
    
    # بررسی وجود فایل لوگو
    if logo_file and hasattr(logo_file, 'url') and logo_file.url:
        logo_src = logo_file.url
    else:
        # استفاده از لوگوی پیش‌فرض
        logo_src = f"/static/Istanbulplusir-logo-{'lowquality' if quality == 'low' else 'highquality'}.png"
    
    # ساخت HTML
    html = f'''
    <div class="logo-container logo-{logo_context} {dimensions['class']}">
        <img src="{logo_src}" 
             alt="{site_config.site_name} Logo" 
             class="logo logo-{logo_context} {dimensions['class']}" 
             width="{dimensions['width']}" 
             height="{dimensions['height']}" 
             loading="{'eager' if logo_context == 'navbar' else 'lazy'}" 
             decoding="async" />
    '''
    
    if show_text:
        html += f'<span class="logo-text {text_class}">{site_config.site_name}</span>'
    
    html += '</div>'
    
    return mark_safe(html)


@register.simple_tag
def get_site_meta(meta_type='description'):
    """دریافت متا تگ‌های سایت"""
    site_config = SiteConfiguration.get_active_config()
    if not site_config:
        return ''
    
    meta_map = {
        'description': site_config.default_meta_description,
        'keywords': site_config.default_meta_keywords,
        'title': site_config.site_name,
        'site_name': site_config.site_name,
        'domain': site_config.site_domain,
    }
    
    return meta_map.get(meta_type, '')


@register.simple_tag
def get_site_image(image_type='og_image'):
    """دریافت تصاویر سایت"""
    site_config = SiteConfiguration.get_active_config()
    if not site_config:
        return ''
    
    image_map = {
        'og_image': site_config.default_og_image,
        'logo_high': site_config.logo_high_quality,
        'logo_low': site_config.logo_low_quality,
        'favicon': site_config.favicon,
    }
    
    image = image_map.get(image_type)
    return image.url if image else ''


@register.inclusion_tag('core/tags/social_links.html')
def render_social_links(show_icons=True, show_text=False, css_class=''):
    """رندر لینک‌های شبکه‌های اجتماعی"""
    social_links = SocialMediaLink.objects.filter(is_active=True).order_by('display_order')
    return {
        'social_links': social_links,
        'show_icons': show_icons,
        'show_text': show_text,
        'css_class': css_class,
    }


@register.inclusion_tag('core/tags/contact_info.html')
def render_contact_info(contact_type=None, show_icons=True, css_class=''):
    """رندر اطلاعات تماس"""
    queryset = ContactInformation.objects.filter(is_active=True)
    if contact_type:
        queryset = queryset.filter(contact_type=contact_type)
    
    contact_info = queryset.order_by('display_order')
    return {
        'contact_info': contact_info,
        'show_icons': show_icons,
        'css_class': css_class,
    }


@register.simple_tag
def get_current_year():
    """دریافت سال جاری"""
    from django.utils import timezone
    return timezone.now().year


@register.simple_tag
def get_site_statistics():
    """دریافت آمار سایت"""
    from core.models import SiteStatistics
    return SiteStatistics.get_current_stats()


@register.filter
def format_phone(phone_number):
    """فرمت کردن شماره تلفن"""
    if not phone_number:
        return ''
    
    # حذف کاراکترهای غیرعددی
    clean_number = ''.join(filter(str.isdigit, phone_number))
    
    # فرمت کردن شماره ایرانی
    if len(clean_number) == 11 and clean_number.startswith('0'):
        return f"{clean_number[:4]}-{clean_number[4:7]}-{clean_number[7:]}"
    elif len(clean_number) == 10:
        return f"0{clean_number[:3]}-{clean_number[3:6]}-{clean_number[6:]}"
    
    return phone_number


@register.simple_tag
def get_announcements(show_on_homepage=False, show_in_navbar=False):
    """دریافت اعلانات فعال"""
    from core.models import SiteAnnouncement
    from django.utils import timezone
    
    queryset = SiteAnnouncement.objects.filter(is_active=True)
    
    if show_on_homepage:
        queryset = queryset.filter(show_on_homepage=True)
    
    if show_in_navbar:
        queryset = queryset.filter(show_in_navbar=True)
    
    # فیلتر بر اساس تاریخ
    now = timezone.now()
    queryset = queryset.filter(start_date__lte=now)
    queryset = queryset.filter(
        models.Q(end_date__isnull=True) | models.Q(end_date__gte=now)
    )
    
    return queryset.order_by('-created_at')


@register.simple_tag
def get_site_content(content_type):
    """دریافت محتوای سایت بر اساس نوع"""
    from core.models import SiteContent
    try:
        return SiteContent.objects.get(content_type=content_type, is_active=True)
    except SiteContent.DoesNotExist:
        return None


@register.simple_tag
def get_hero_cards(limit=None):
    """دریافت کارت‌های Hero"""
    queryset = HeroCard.objects.filter(is_active=True).order_by('display_order')
    if limit:
        queryset = queryset[:limit]
    return queryset


@register.simple_tag
def get_hero_config():
    """دریافت تنظیمات Hero"""
    return HeroSection.get_active_config()


@register.inclusion_tag('core/tags/hero_cards.html')
def render_hero_cards(limit=None, css_class=''):
    """رندر کارت‌های Hero"""
    cards = HeroCard.objects.filter(is_active=True).order_by('display_order')
    if limit:
        cards = cards[:limit]
    
    # دریافت تنظیمات Hero
    hero_config = HeroSection.get_active_config()
    
    return {
        'hero_cards': cards,
        'css_class': css_class,
        'hero_config': hero_config,
    }

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import URLValidator, EmailValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
import uuid


class SiteConfiguration(models.Model):
    """
    تنظیمات اصلی سایت - Singleton pattern
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # اطلاعات برند
    site_name = models.CharField(
        max_length=100,
        verbose_name=_("نام سایت"),
        help_text=_("نام رسمی سایت")
    )
    site_tagline = models.TextField(
        max_length=200,
        blank=True,
        verbose_name=_("شعار سایت"),
        help_text=_("شعار یا توضیح کوتاه سایت")
    )
    site_domain = models.CharField(
        max_length=100,
        verbose_name=_("دامنه سایت"),
        help_text=_("دامنه اصلی سایت (مثال: istanbulplus.ir)")
    )
    
    # لوگوها
    logo_high_quality = models.ImageField(
        upload_to='logos/',
        verbose_name=_("لوگو کیفیت بالا"),
        help_text=_("لوگو با کیفیت بالا برای نمایش در صفحات اصلی")
    )
    logo_low_quality = models.ImageField(
        upload_to='logos/',
        verbose_name=_("لوگو کیفیت پایین"),
        help_text=_("لوگو با کیفیت پایین برای بارگذاری سریع")
    )
    favicon = models.ImageField(
        upload_to='logos/',
        blank=True,
        verbose_name=_("فاویکون"),
        help_text=_("آیکون کوچک برای تب مرورگر")
    )
    
    # اطلاعات SEO
    default_meta_description = models.TextField(
        max_length=160,
        verbose_name=_("توضیحات پیش‌فرض SEO"),
        help_text=_("توضیحات پیش‌فرض برای متا تگ description")
    )
    default_meta_keywords = models.TextField(
        max_length=200,
        blank=True,
        verbose_name=_("کلمات کلیدی پیش‌فرض"),
        help_text=_("کلمات کلیدی پیش‌فرض برای SEO")
    )
    default_og_image = models.ImageField(
        upload_to='seo/',
        blank=True,
        verbose_name=_("تصویر پیش‌فرض Open Graph"),
        help_text=_("تصویر پیش‌فرض برای اشتراک‌گذاری در شبکه‌های اجتماعی")
    )
    
    # تنظیمات عمومی
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال"),
        help_text=_("آیا این تنظیمات فعال است؟")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("تنظیمات سایت")
        verbose_name_plural = _("تنظیمات سایت")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.site_name} - {self.site_domain}"
    
    def clean(self):
        # اطمینان از اینکه فقط یک تنظیمات فعال وجود دارد
        if self.is_active:
            existing = SiteConfiguration.objects.filter(is_active=True).exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError(_("فقط یک تنظیمات سایت می‌تواند فعال باشد."))
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @classmethod
    def get_active_config(cls):
        """دریافت تنظیمات فعال سایت"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None


class ContactInformation(models.Model):
    """
    اطلاعات تماس سایت
    """
    CONTACT_TYPE_CHOICES = [
        ('phone', _('تلفن')),
        ('mobile', _('موبایل')),
        ('email', _('ایمیل')),
        ('whatsapp', _('واتساپ')),
        ('telegram', _('تلگرام')),
        ('address', _('آدرس')),
        ('working_hours', _('ساعات کاری')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    contact_type = models.CharField(
        max_length=20,
        choices=CONTACT_TYPE_CHOICES,
        verbose_name=_("نوع تماس")
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_("عنوان"),
        help_text=_("عنوان نمایشی (مثال: تلفن تماس)")
    )
    value = models.CharField(
        max_length=200,
        verbose_name=_("مقدار"),
        help_text=_("مقدار واقعی (شماره، ایمیل، آدرس و...)")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتیب نمایش"),
        help_text=_("ترتیب نمایش در فوتر")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    is_clickable = models.BooleanField(
        default=True,
        verbose_name=_("قابل کلیک"),
        help_text=_("آیا این اطلاعات قابل کلیک است؟ (برای تلفن، ایمیل و...)")
    )
    icon_class = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("کلاس آیکون"),
        help_text=_("کلاس آیکون Bootstrap (مثال: bi-telephone)")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("اطلاعات تماس")
        verbose_name_plural = _("اطلاعات تماس")
        ordering = ['display_order', 'contact_type']
        unique_together = ['contact_type', 'value']
    
    def __str__(self):
        return f"{self.title}: {self.value}"
    
    def clean(self):
        # اعتبارسنجی بر اساس نوع تماس
        if self.contact_type == 'email':
            validator = EmailValidator()
            validator(self.value)
        elif self.contact_type in ['phone', 'mobile', 'whatsapp']:
            # اعتبارسنجی شماره تلفن
            if not self.value.replace('+', '').replace('-', '').replace(' ', '').isdigit():
                raise ValidationError(_("شماره تلفن نامعتبر است."))
    
    def get_clickable_url(self):
        """دریافت URL قابل کلیک بر اساس نوع تماس"""
        if not self.is_clickable:
            return None
            
        if self.contact_type == 'email':
            return f"mailto:{self.value}"
        elif self.contact_type in ['phone', 'mobile']:
            return f"tel:{self.value}"
        elif self.contact_type == 'whatsapp':
            # حذف کاراکترهای غیرعددی و اضافه کردن کد کشور
            clean_number = self.value.replace('+', '').replace('-', '').replace(' ', '')
            if clean_number.startswith('0'):
                clean_number = '98' + clean_number[1:]
            return f"https://wa.me/{clean_number}"
        elif self.contact_type == 'telegram':
            return f"https://t.me/{self.value}"
        
        return None


class SocialMediaLink(models.Model):
    """
    لینک‌های شبکه‌های اجتماعی
    """
    PLATFORM_CHOICES = [
        ('instagram', _('اینستاگرام')),
        ('telegram', _('تلگرام')),
        ('whatsapp', _('واتساپ')),
        ('linkedin', _('لینکدین')),
        ('twitter', _('توییتر')),
        ('facebook', _('فیس‌بوک')),
        ('youtube', _('یوتیوب')),
        ('tiktok', _('تیک‌تاک')),
        ('aparat', _('آپارات')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    platform = models.CharField(
        max_length=20,
        choices=PLATFORM_CHOICES,
        unique=True,
        verbose_name=_("پلتفرم")
    )
    url = models.URLField(
        verbose_name=_("لینک"),
        help_text=_("لینک کامل صفحه در شبکه اجتماعی")
    )
    display_name = models.CharField(
        max_length=100,
        verbose_name=_("نام نمایشی"),
        help_text=_("نام نمایشی در فوتر")
    )
    icon_class = models.CharField(
        max_length=50,
        verbose_name=_("کلاس آیکون"),
        help_text=_("کلاس آیکون Bootstrap (مثال: bi-instagram)")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتیب نمایش")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    open_in_new_tab = models.BooleanField(
        default=True,
        verbose_name=_("باز کردن در تب جدید")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("لینک شبکه اجتماعی")
        verbose_name_plural = _("لینک‌های شبکه‌های اجتماعی")
        ordering = ['display_order', 'platform']
    
    def __str__(self):
        return f"{self.display_name} - {self.platform}"
    
    def clean(self):
        # اعتبارسنجی URL
        validator = URLValidator()
        validator(self.url)


class NavigationMenu(models.Model):
    """
    منوی ناوبری سایت
    """
    MENU_TYPE_CHOICES = [
        ('main', _('منوی اصلی')),
        ('footer', _('منوی فوتر')),
        ('quick_access', _('دسترسی سریع')),
        ('customer_service', _('خدمات مشتریان')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    menu_type = models.CharField(
        max_length=20,
        choices=MENU_TYPE_CHOICES,
        verbose_name=_("نوع منو")
    )
    title = models.CharField(
        max_length=100,
        verbose_name=_("عنوان")
    )
    url = models.CharField(
        max_length=200,
        verbose_name=_("لینک"),
        help_text=_("لینک داخلی (مثال: /products/) یا خارجی")
    )
    icon_class = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("کلاس آیکون"),
        help_text=_("کلاس آیکون Bootstrap")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتیب نمایش")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    is_external = models.BooleanField(
        default=False,
        verbose_name=_("لینک خارجی"),
        help_text=_("آیا این لینک خارجی است؟")
    )
    open_in_new_tab = models.BooleanField(
        default=False,
        verbose_name=_("باز کردن در تب جدید")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("آیتم منو")
        verbose_name_plural = _("آیتم‌های منو")
        ordering = ['menu_type', 'display_order', 'title']
    
    def __str__(self):
        return f"{self.title} ({self.get_menu_type_display()})"


class SiteContent(models.Model):
    """
    محتوای متنی سایت (درباره ما، شرایط استفاده و...)
    """
    CONTENT_TYPE_CHOICES = [
        ('about', _('درباره ما')),
        ('terms', _('شرایط استفاده')),
        ('privacy', _('حریم خصوصی')),
        ('shipping', _('شیوه‌های ارسال')),
        ('return', _('مرجوعی کالا')),
        ('guide', _('راهنمای خرید')),
        ('support', _('پشتیبانی')),
        ('footer_description', _('توضیحات فوتر')),
        ('hero_title', _('عنوان اصلی صفحه اول')),
        ('hero_description', _('توضیحات صفحه اول')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content_type = models.CharField(
        max_length=30,
        choices=CONTENT_TYPE_CHOICES,
        unique=True,
        verbose_name=_("نوع محتوا")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان")
    )
    content = models.TextField(
        verbose_name=_("محتوا"),
        help_text=_("محتوای کامل (پشتیبانی از HTML)")
    )
    short_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name=_("توضیح کوتاه"),
        help_text=_("خلاصه محتوا برای نمایش در لیست‌ها")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("محتوای سایت")
        verbose_name_plural = _("محتوای سایت")
        ordering = ['content_type']
    
    def __str__(self):
        return f"{self.title} ({self.get_content_type_display()})"


class SiteAnnouncement(models.Model):
    """
    اعلانات و پیام‌های سایت
    """
    ANNOUNCEMENT_TYPE_CHOICES = [
        ('info', _('اطلاعیه')),
        ('warning', _('هشدار')),
        ('success', _('موفقیت')),
        ('promotion', _('تخفیف')),
        ('maintenance', _('تعمیرات')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    announcement_type = models.CharField(
        max_length=20,
        choices=ANNOUNCEMENT_TYPE_CHOICES,
        verbose_name=_("نوع اعلان")
    )
    title = models.CharField(
        max_length=200,
        verbose_name=_("عنوان")
    )
    message = models.TextField(
        verbose_name=_("پیام")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    show_on_homepage = models.BooleanField(
        default=False,
        verbose_name=_("نمایش در صفحه اصلی")
    )
    show_in_navbar = models.BooleanField(
        default=False,
        verbose_name=_("نمایش در نوار ناوبری")
    )
    start_date = models.DateTimeField(
        default=timezone.now,
        verbose_name=_("تاریخ شروع")
    )
    end_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("تاریخ پایان"),
        help_text=_("اختیاری - اگر مشخص نشود، اعلان تا زمان غیرفعال کردن نمایش داده می‌شود")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("اعلان سایت")
        verbose_name_plural = _("اعلانات سایت")
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_announcement_type_display()})"
    
    def is_currently_active(self):
        """بررسی فعال بودن اعلان در زمان فعلی"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True


class SiteStatistics(models.Model):
    """
    آمار و اطلاعات سایت
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # آمار عمومی
    total_products = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل محصولات")
    )
    total_customers = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل مشتریان")
    )
    total_orders = models.PositiveIntegerField(
        default=0,
        verbose_name=_("تعداد کل سفارشات")
    )
    
    # اطلاعات اعتماد
    trust_badges = models.JSONField(
        default=list,
        verbose_name=_("نشان‌های اعتماد"),
        help_text=_("لیست نشان‌های اعتماد (نماد الکترونیکی، مجوزها و...)")
    )
    
    # اطلاعات اضافی
    established_year = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("سال تأسیس")
    )
    license_number = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("شماره مجوز")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("آمار سایت")
        verbose_name_plural = _("آمار سایت")
    
    def __str__(self):
        return f"آمار سایت - {self.updated_at.strftime('%Y/%m/%d')}"
    
    @classmethod
    def get_current_stats(cls):
        """دریافت آمار فعلی سایت"""
        stats, created = cls.objects.get_or_create(
            defaults={
                'total_products': 0,
                'total_customers': 0,
                'total_orders': 0,
            }
        )
        return stats


class HeroCard(models.Model):
    """
    کارت‌های نمایشی در بخش Hero صفحه اصلی
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    title = models.CharField(
        max_length=100,
        verbose_name=_("عنوان کارت"),
        help_text=_("عنوان اصلی کارت (مثال: تور ویژه VIP)")
    )
    subtitle = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("زیرعنوان"),
        help_text=_("زیرعنوان یا توضیح کوتاه")
    )
    price = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_("قیمت"),
        help_text=_("قیمت یا اطلاعات قیمت (مثال: از 500,000 تومان)")
    )
    image = models.ImageField(
        upload_to='hero_cards/',
        verbose_name=_("تصویر کارت"),
        help_text=_("تصویر نمایشی کارت")
    )
    link_url = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_("لینک"),
        help_text=_("لینک مقصد (مثال: /products/vip-tour/)")
    )
    link_text = models.CharField(
        max_length=50,
        default="مشاهده",
        verbose_name=_("متن لینک"),
        help_text=_("متن دکمه لینک")
    )
    display_order = models.PositiveIntegerField(
        default=0,
        verbose_name=_("ترتیب نمایش"),
        help_text=_("ترتیب نمایش کارت‌ها")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    open_in_new_tab = models.BooleanField(
        default=False,
        verbose_name=_("باز کردن در تب جدید")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("کارت Hero")
        verbose_name_plural = _("کارت‌های Hero")
        ordering = ['display_order', 'title']
    
    def __str__(self):
        return f"{self.title} - {self.subtitle}"


class HeroSection(models.Model):
    """
    تنظیمات بخش Hero صفحه اصلی
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # تنظیمات پس‌زمینه
    background_type = models.CharField(
        max_length=20,
        choices=[
            ('gradient', _('گرادیان')),
            ('solid', _('رنگ یکنواخت')),
            ('image', _('تصویر')),
        ],
        default='gradient',
        verbose_name=_("نوع پس‌زمینه")
    )
    background_color = models.CharField(
        max_length=7,
        default='#667eea',
        verbose_name=_("رنگ پس‌زمینه"),
        help_text=_("کد رنگ hex (مثال: #667eea)")
    )
    background_gradient_start = models.CharField(
        max_length=7,
        default='#667eea',
        verbose_name=_("شروع گرادیان"),
        help_text=_("رنگ شروع گرادیان")
    )
    background_gradient_end = models.CharField(
        max_length=7,
        default='#764ba2',
        verbose_name=_("پایان گرادیان"),
        help_text=_("رنگ پایان گرادیان")
    )
    background_image = models.ImageField(
        upload_to='hero_backgrounds/',
        blank=True,
        verbose_name=_("تصویر پس‌زمینه"),
        help_text=_("تصویر پس‌زمینه (در صورت انتخاب نوع تصویر)")
    )
    
    # تنظیمات انیمیشن
    animation_enabled = models.BooleanField(
        default=True,
        verbose_name=_("فعال‌سازی انیمیشن")
    )
    animation_speed = models.CharField(
        max_length=10,
        choices=[
            ('slow', _('آهسته')),
            ('normal', _('عادی')),
            ('fast', _('سریع')),
        ],
        default='normal',
        verbose_name=_("سرعت انیمیشن")
    )
    
    # تنظیمات محتوا
    show_particles = models.BooleanField(
        default=True,
        verbose_name=_("نمایش ذرات متحرک")
    )
    show_cards = models.BooleanField(
        default=True,
        verbose_name=_("نمایش کارت‌ها")
    )
    cards_count = models.PositiveIntegerField(
        default=3,
        verbose_name=_("تعداد کارت‌ها"),
        help_text=_("تعداد کارت‌های نمایشی (حداکثر 6)")
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("فعال")
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = _("تنظیمات Hero")
        verbose_name_plural = _("تنظیمات Hero")
    
    def __str__(self):
        return f"تنظیمات Hero - {self.background_type}"
    
    def clean(self):
        if self.cards_count > 6:
            raise ValidationError(_("تعداد کارت‌ها نمی‌تواند بیشتر از 6 باشد."))
    
    @classmethod
    def get_active_config(cls):
        """دریافت تنظیمات فعال Hero"""
        try:
            return cls.objects.get(is_active=True)
        except cls.DoesNotExist:
            return None

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils.translation import gettext_lazy as _
from core.models import (
    SiteConfiguration, ContactInformation, SocialMediaLink,
    NavigationMenu, SiteContent, SiteAnnouncement, SiteStatistics,
    HeroCard, HeroSection
)


class Command(BaseCommand):
    help = 'تنظیم داده‌های اولیه سایت'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='حذف داده‌های موجود و ایجاد مجدد',
        )

    def handle(self, *args, **options):
        if options['reset']:
            self.stdout.write('حذف داده‌های موجود...')
            SiteConfiguration.objects.all().delete()
            ContactInformation.objects.all().delete()
            SocialMediaLink.objects.all().delete()
            NavigationMenu.objects.all().delete()
            SiteContent.objects.all().delete()
            SiteAnnouncement.objects.all().delete()
            SiteStatistics.objects.all().delete()

        self.stdout.write('ایجاد تنظیمات سایت...')
        self.create_site_configuration()
        
        self.stdout.write('ایجاد اطلاعات تماس...')
        self.create_contact_information()
        
        self.stdout.write('ایجاد لینک‌های شبکه‌های اجتماعی...')
        self.create_social_media_links()
        
        self.stdout.write('ایجاد منوهای ناوبری...')
        self.create_navigation_menus()
        
        self.stdout.write('ایجاد محتوای سایت...')
        self.create_site_content()
        
        self.stdout.write('ایجاد آمار سایت...')
        self.create_site_statistics()
        
        self.stdout.write('ایجاد کارت‌های Hero...')
        self.create_hero_cards()
        
        self.stdout.write('ایجاد تنظیمات Hero...')
        self.create_hero_section()
        
        self.stdout.write(
            self.style.SUCCESS('داده‌های اولیه سایت با موفقیت ایجاد شد!')
        )

    def create_site_configuration(self):
        """ایجاد تنظیمات اصلی سایت"""
        config, created = SiteConfiguration.objects.get_or_create(
            site_domain='istanbulplus.ir',
            defaults={
                'site_name': 'Istanbul Plus',
                'site_tagline': 'فروشگاه آنلاین محصولات با کیفیت و ارسال سریع در سراسر کشور',
                'default_meta_description': 'فروشگاه آنلاین Istanbul Plus - محصولات با کیفیت و ارسال سریع در سراسر کشور. تجربه خرید مطمئن و آسان با بهترین قیمت‌ها.',
                'default_meta_keywords': 'فروشگاه آنلاین, خرید اینترنتی, Istanbul Plus, محصولات با کیفیت, ارسال سریع',
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ تنظیمات سایت ایجاد شد: {config.site_name}')
        else:
            self.stdout.write(f'  - تنظیمات سایت موجود است: {config.site_name}')

    def create_contact_information(self):
        """ایجاد اطلاعات تماس"""
        contact_data = [
            {
                'contact_type': 'email',
                'title': 'ایمیل',
                'value': 'info@istanbulplus.ir',
                'display_order': 1,
                'icon_class': 'bi-envelope',
            },
            {
                'contact_type': 'phone',
                'title': 'تلفن',
                'value': '۰۲۱-۱۲۳۴۵۶۷۸',
                'display_order': 2,
                'icon_class': 'bi-telephone',
            },
            {
                'contact_type': 'mobile',
                'title': 'واتساپ',
                'value': '۰۹۱۲-۳۴۵۶۷۸۹',
                'display_order': 3,
                'icon_class': 'bi-whatsapp',
            },
            {
                'contact_type': 'address',
                'title': 'آدرس',
                'value': 'تهران، خیابان ولیعصر، نرسیده به پل صدر، پلاک ۱۲۳، طبقه ۲',
                'display_order': 4,
                'icon_class': 'bi-geo-alt',
                'is_clickable': False,
            },
            {
                'contact_type': 'working_hours',
                'title': 'ساعات کاری',
                'value': 'شنبه تا پنج‌شنبه ۹ تا ۱۸',
                'display_order': 5,
                'icon_class': 'bi-clock',
                'is_clickable': False,
            },
        ]
        
        for data in contact_data:
            contact, created = ContactInformation.objects.get_or_create(
                contact_type=data['contact_type'],
                defaults=data
            )
            
            if created:
                self.stdout.write(f'  ✓ اطلاعات تماس ایجاد شد: {contact.title}')
            else:
                self.stdout.write(f'  - اطلاعات تماس موجود است: {contact.title}')

    def create_social_media_links(self):
        """ایجاد لینک‌های شبکه‌های اجتماعی"""
        social_data = [
            {
                'platform': 'instagram',
                'display_name': 'اینستاگرام',
                'url': 'https://instagram.com/istanbulplus',
                'icon_class': 'bi-instagram',
                'display_order': 1,
            },
            {
                'platform': 'telegram',
                'display_name': 'تلگرام',
                'url': 'https://t.me/istanbulplus',
                'icon_class': 'bi-telegram',
                'display_order': 2,
            },
            {
                'platform': 'whatsapp',
                'display_name': 'واتساپ',
                'url': 'https://wa.me/989123456789',
                'icon_class': 'bi-whatsapp',
                'display_order': 3,
            },
            {
                'platform': 'linkedin',
                'display_name': 'لینکدین',
                'url': 'https://linkedin.com/company/istanbulplus',
                'icon_class': 'bi-linkedin',
                'display_order': 4,
            },
        ]
        
        for data in social_data:
            social, created = SocialMediaLink.objects.get_or_create(
                platform=data['platform'],
                defaults=data
            )
            
            if created:
                self.stdout.write(f'  ✓ لینک شبکه اجتماعی ایجاد شد: {social.display_name}')
            else:
                self.stdout.write(f'  - لینک شبکه اجتماعی موجود است: {social.display_name}')

    def create_navigation_menus(self):
        """ایجاد منوهای ناوبری"""
        menu_data = [
            # منوی اصلی
            {
                'menu_type': 'main',
                'title': 'خانه',
                'url': '/',
                'icon_class': 'bi-house-door',
                'display_order': 1,
            },
            {
                'menu_type': 'main',
                'title': 'محصولات',
                'url': '/products/',
                'icon_class': 'bi-grid',
                'display_order': 2,
            },
            
            # منوی فوتر
            {
                'menu_type': 'footer',
                'title': 'درباره ما',
                'url': '/about/',
                'icon_class': 'bi-info-circle',
                'display_order': 1,
            },
            {
                'menu_type': 'footer',
                'title': 'تماس با ما',
                'url': '/contact/',
                'icon_class': 'bi-envelope',
                'display_order': 2,
            },
            
            # دسترسی سریع
            {
                'menu_type': 'quick_access',
                'title': 'خانه',
                'url': '/',
                'icon_class': 'bi-house-door',
                'display_order': 1,
            },
            {
                'menu_type': 'quick_access',
                'title': 'محصولات',
                'url': '/products/',
                'icon_class': 'bi-grid',
                'display_order': 2,
            },
            {
                'menu_type': 'quick_access',
                'title': 'درباره ما',
                'url': '/about/',
                'icon_class': 'bi-info-circle',
                'display_order': 3,
            },
            {
                'menu_type': 'quick_access',
                'title': 'تماس با ما',
                'url': '/contact/',
                'icon_class': 'bi-envelope',
                'display_order': 4,
            },
            {
                'menu_type': 'quick_access',
                'title': 'سبد خرید',
                'url': '/cart/',
                'icon_class': 'bi-cart3',
                'display_order': 5,
            },
            
            # خدمات مشتریان
            {
                'menu_type': 'customer_service',
                'title': 'راهنمای خرید',
                'url': '/guide/',
                'icon_class': 'bi-question-circle',
                'display_order': 1,
            },
            {
                'menu_type': 'customer_service',
                'title': 'شیوه‌های ارسال',
                'url': '/shipping/',
                'icon_class': 'bi-truck',
                'display_order': 2,
            },
            {
                'menu_type': 'customer_service',
                'title': 'مرجوعی کالا',
                'url': '/return/',
                'icon_class': 'bi-arrow-return-left',
                'display_order': 3,
            },
            {
                'menu_type': 'customer_service',
                'title': 'شرایط استفاده',
                'url': '/terms/',
                'icon_class': 'bi-file-text',
                'display_order': 4,
            },
            {
                'menu_type': 'customer_service',
                'title': 'حریم خصوصی',
                'url': '/privacy/',
                'icon_class': 'bi-shield-check',
                'display_order': 5,
            },
            {
                'menu_type': 'customer_service',
                'title': 'پشتیبانی ۲۴/۷',
                'url': '/support/',
                'icon_class': 'bi-headset',
                'display_order': 6,
            },
        ]
        
        for data in menu_data:
            menu, created = NavigationMenu.objects.get_or_create(
                menu_type=data['menu_type'],
                title=data['title'],
                defaults=data
            )
            
            if created:
                self.stdout.write(f'  ✓ منو ایجاد شد: {menu.title} ({menu.get_menu_type_display()})')
            else:
                self.stdout.write(f'  - منو موجود است: {menu.title} ({menu.get_menu_type_display()})')

    def create_site_content(self):
        """ایجاد محتوای سایت"""
        content_data = [
            {
                'content_type': 'footer_description',
                'title': 'توضیحات فوتر',
                'content': 'فروشگاه آنلاین محصولات با کیفیت و ارسال سریع در سراسر کشور. تجربه خرید مطمئن و آسان با بهترین قیمت‌ها.',
                'short_description': 'توضیحات کوتاه فوتر',
            },
            {
                'content_type': 'hero_title',
                'title': 'عنوان اصلی صفحه اول',
                'content': 'به فروشگاه Istanbul Plus خوش آمدید',
                'short_description': 'عنوان اصلی صفحه اول',
            },
            {
                'content_type': 'hero_description',
                'title': 'توضیحات صفحه اول',
                'content': 'تجربه خرید آنلاین منحصر به فرد با بهترین محصولات و خدمات درجه یک',
                'short_description': 'توضیحات صفحه اول',
            },
            {
                'content_type': 'about',
                'title': 'درباره ما',
                'content': '''
                <h2>درباره Istanbul Plus</h2>
                <p>Istanbul Plus یک فروشگاه آنلاین پیشرو در ارائه محصولات با کیفیت و خدمات عالی است. ما با سال‌ها تجربه در زمینه تجارت الکترونیک، متعهد به ارائه بهترین تجربه خرید به مشتریان خود هستیم.</p>
                
                <h3>چرا Istanbul Plus؟</h3>
                <ul>
                    <li>محصولات با کیفیت و اصل</li>
                    <li>ارسال سریع و مطمئن</li>
                    <li>پشتیبانی ۲۴/۷</li>
                    <li>قیمت‌های رقابتی</li>
                    <li>ضمانت کیفیت</li>
                </ul>
                
                <h3>ماموریت ما</h3>
                <p>ماموریت ما ارائه بهترین محصولات و خدمات به مشتریان است تا تجربه خرید آنلاین را به تجربه‌ای لذت‌بخش تبدیل کنیم.</p>
                ''',
                'short_description': 'درباره Istanbul Plus و خدمات ما',
            },
        ]
        
        for data in content_data:
            content, created = SiteContent.objects.get_or_create(
                content_type=data['content_type'],
                defaults=data
            )
            
            if created:
                self.stdout.write(f'  ✓ محتوا ایجاد شد: {content.title}')
            else:
                self.stdout.write(f'  - محتوا موجود است: {content.title}')

    def create_site_statistics(self):
        """ایجاد آمار سایت"""
        stats, created = SiteStatistics.objects.get_or_create(
            defaults={
                'total_products': 0,
                'total_customers': 0,
                'total_orders': 0,
                'established_year': 2024,
                'license_number': '۱۲۳۴۵۶۷۸۹',
                'trust_badges': [
                    'نماد اعتماد الکترونیکی',
                    'مجوز رسمی از وزارت صنعت، معدن و تجارت',
                    'پرداخت امن',
                ],
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ آمار سایت ایجاد شد')
        else:
            self.stdout.write(f'  - آمار سایت موجود است')

    def create_hero_cards(self):
        """ایجاد کارت‌های Hero"""
        hero_cards_data = [
            {
                'title': 'تور ویژه VIP',
                'subtitle': 'تجربه‌ای منحصر به فرد',
                'price': 'از 500,000 تومان',
                'link_url': '/products/vip-tour/',
                'link_text': 'مشاهده تور',
                'display_order': 1,
            },
            {
                'title': 'سفر لوکس',
                'subtitle': 'بهترین خدمات',
                'price': 'از 750,000 تومان',
                'link_url': '/products/luxury-travel/',
                'link_text': 'مشاهده سفر',
                'display_order': 2,
            },
            {
                'title': 'پکیج ویژه',
                'subtitle': 'ارزش واقعی',
                'price': 'از 300,000 تومان',
                'link_url': '/products/special-package/',
                'link_text': 'مشاهده پکیج',
                'display_order': 3,
            },
        ]
        
        for data in hero_cards_data:
            card, created = HeroCard.objects.get_or_create(
                title=data['title'],
                defaults=data
            )
            
            if created:
                self.stdout.write(f'  ✓ کارت Hero ایجاد شد: {card.title}')
            else:
                self.stdout.write(f'  - کارت Hero موجود است: {card.title}')

    def create_hero_section(self):
        """ایجاد تنظیمات Hero"""
        hero_config, created = HeroSection.objects.get_or_create(
            defaults={
                'background_type': 'gradient',
                'background_color': '#667eea',
                'background_gradient_start': '#667eea',
                'background_gradient_end': '#764ba2',
                'animation_enabled': True,
                'animation_speed': 'normal',
                'show_particles': True,
                'show_cards': True,
                'cards_count': 3,
                'is_active': True,
            }
        )
        
        if created:
            self.stdout.write(f'  ✓ تنظیمات Hero ایجاد شد')
        else:
            self.stdout.write(f'  - تنظیمات Hero موجود است')

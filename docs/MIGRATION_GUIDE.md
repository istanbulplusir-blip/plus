# راهنمای مهاجرت سیستم احراز هویت

## مقدمه

این راهنما مراحل به‌روزرسانی سیستم احراز هویت از نسخه قبلی به نسخه جدید را شرح می‌دهد.

## نسخه‌بندی

- **نسخه قبلی**: 0.9.x (سیستم ساده احراز هویت)
- **نسخه جدید**: 1.0.0 (سیستم پیشرفته احراز هویت)

## تغییرات اصلی

### 1. مدل‌های جدید

- `UserSession`: مدیریت جلسات کاربری
- `PasswordResetToken`: توکن‌های بازیابی رمز عبور
- `SecurityLog`: لاگ رویدادهای امنیتی

### 2. فیلدهای جدید مدل User

- `email_verified`: وضعیت تأیید ایمیل
- `phone_verified`: وضعیت تأیید موبایل
- `failed_login_attempts`: تعداد تلاش‌های ناموفق
- `locked_until`: زمان قفل حساب
- `last_login_ip`: آخرین IP ورود
- `two_factor_enabled`: فعال‌سازی 2FA
- `avatar`: عکس پروفایل
- `birth_date`: تاریخ تولد

### 3. بهبود مدل OtpCode

- `delivery_method`: روش ارسال (SMS/Email)
- `purpose`: هدف استفاده
- `ip_address`: IP درخواست‌کننده

## مراحل مهاجرت

### مرحله 1: پشتیبان‌گیری

```bash
# پشتیبان‌گیری از پایگاه داده
python manage.py dumpdata > backup_before_migration.json

# پشتیبان‌گیری از فایل‌های media
cp -r media/ media_backup/

# پشتیبان‌گیری از تنظیمات
cp -r istanbulplusir/settings/ settings_backup/
```

### مرحله 2: به‌روزرسانی کد

```bash
# دریافت آخرین نسخه
git pull origin main

# نصب وابستگی‌های جدید
pip install -r requirements.txt

# بررسی تغییرات تنظیمات
diff istanbulplusir/settings/base.py settings_backup/base.py
```

### مرحله 3: اجرای Migration ها

```bash
# ایجاد migration های جدید
python manage.py makemigrations users
python manage.py makemigrations

# بررسی migration ها
python manage.py showmigrations

# اجرای migration ها
python manage.py migrate
```

### مرحله 4: تنظیمات جدید

#### 4.1 تنظیمات Redis

```python
# settings/base.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# تنظیمات Rate Limiting
RATE_LIMIT_SETTINGS = {
    'OTP_REQUESTS': {
        'LIMIT': 5,
        'WINDOW': 3600,  # 1 hour
    },
    'LOGIN_ATTEMPTS': {
        'LIMIT': 10,
        'WINDOW': 3600,  # 1 hour
    },
    'PASSWORD_RESET': {
        'LIMIT': 3,
        'WINDOW': 3600,  # 1 hour
    }
}
```

#### 4.2 تنظیمات ایمیل

```python
# settings/base.py
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@gmail.com'
EMAIL_HOST_PASSWORD = 'your-app-password'

# تنظیمات ایمیل سیستم
DEFAULT_FROM_EMAIL = 'noreply@istanbulplus.ir'
ADMIN_EMAIL = 'admin@istanbulplus.ir'
```

#### 4.3 تنظیمات SMS

```python
# settings/base.py
SMS_BACKEND = 'your_sms_provider'
SMS_API_KEY = 'your-sms-api-key'
SMS_SENDER_NUMBER = '+98xxxxxxxxxx'
```

#### 4.4 تنظیمات امنیتی

```python
# settings/base.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# تنظیمات JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
}
```

### مرحله 5: مهاجرت داده‌ها

#### 5.1 اسکریپت مهاجرت کاربران

```python
# management/commands/migrate_users.py
from django.core.management.base import BaseCommand
from users.models import User

class Command(BaseCommand):
    help = 'Migrate existing users to new format'

    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            # تنظیم مقادیر پیش‌فرض برای فیلدهای جدید
            if user.email and '@' in user.email:
                user.email_verified = False

            if user.phone and user.phone.startswith('+98'):
                user.phone_verified = False

            user.failed_login_attempts = 0
            user.two_factor_enabled = False
            user.email_notifications = True
            user.sms_notifications = True

            user.save()

        self.stdout.write(
            self.style.SUCCESS(f'Successfully migrated {users.count()} users')
        )
```

#### 5.2 اجرای اسکریپت مهاجرت

```bash
python manage.py migrate_users
```

### مرحله 6: به‌روزرسانی Template ها

#### 6.1 فایل‌های Template جدید

```bash
# کپی کردن template های جدید
cp -r templates/auth/ your_templates/auth/
cp -r templates/emails/ your_templates/emails/
```

#### 6.2 به‌روزرسانی Base Template

```html
<!-- templates/base.html -->
<!-- اضافه کردن CSS و JS جدید -->
<link rel="stylesheet" href="{% static 'css/auth.css' %}" />
<script src="{% static 'js/auth.js' %}"></script>
```

### مرحله 7: تست سیستم

#### 7.1 تست‌های خودکار

```bash
# اجرای تست‌ها
python manage.py test users.tests
python manage.py test --pattern="test_auth*"
```

#### 7.2 تست‌های دستی

1. **ثبت‌نام کاربر جدید**

   - تست فرم ثبت‌نام
   - تست ارسال ایمیل تأیید
   - تست تأیید ایمیل

2. **ورود کاربر**

   - تست ورود با رمز عبور
   - تست ورود با OTP
   - تست قفل حساب

3. **بازیابی رمز عبور**

   - تست درخواست بازیابی
   - تست ارسال ایمیل/SMS
   - تست تنظیم رمز جدید

4. **مدیریت پروفایل**

   - تست ویرایش اطلاعات
   - تست آپلود عکس
   - تست تغییر رمز عبور

5. **مدیریت جلسات**
   - تست مشاهده جلسات فعال
   - تست خروج از جلسه خاص
   - تست خروج از همه دستگاه‌ها

### مرحله 8: تنظیمات Production

#### 8.1 متغیرهای محیطی

```bash
# .env
DEBUG=False
SECRET_KEY=your-secret-key
DATABASE_URL=postgres://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/1
EMAIL_HOST_PASSWORD=your-email-password
SMS_API_KEY=your-sms-api-key
```

#### 8.2 تنظیمات وب سرور

```nginx
# nginx.conf
server {
    listen 443 ssl;
    server_name istanbulplus.ir;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location /static/ {
        alias /path/to/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /path/to/media/;
        expires 1y;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 8.3 تنظیمات Supervisor

```ini
# /etc/supervisor/conf.d/istanbulplus.conf
[program:istanbulplus]
command=/path/to/venv/bin/gunicorn istanbulplusir.wsgi:application
directory=/path/to/project
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/istanbulplus.log
```

## مشکلات رایج و راه‌حل

### 1. خطای Migration

**مشکل**: خطا در اجرای migration ها

**راه‌حل**:

```bash
# بازگشت به migration قبلی
python manage.py migrate users 0001 --fake

# اجرای مجدد
python manage.py migrate users
```

### 2. مشکل Redis

**مشکل**: عدم اتصال به Redis

**راه‌حل**:

```bash
# نصب و راه‌اندازی Redis
sudo apt-get install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# تست اتصال
redis-cli ping
```

### 3. مشکل ارسال ایمیل

**مشکل**: عدم ارسال ایمیل‌ها

**راه‌حل**:

```python
# تست تنظیمات ایمیل
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'Test message', 'from@example.com', ['to@example.com'])
```

### 4. مشکل Static Files

**مشکل**: عدم نمایش فایل‌های استاتیک

**راه‌حل**:

```bash
# جمع‌آوری فایل‌های استاتیک
python manage.py collectstatic --noinput

# بررسی تنظیمات
python manage.py findstatic css/auth.css
```

## بازگشت به نسخه قبل (Rollback)

در صورت بروز مشکل:

### 1. بازگشت کد

```bash
git checkout previous-version-tag
```

### 2. بازگشت پایگاه داده

```bash
# بازیابی از پشتیبان
python manage.py loaddata backup_before_migration.json
```

### 3. بازگشت فایل‌ها

```bash
# بازیابی media files
rm -rf media/
mv media_backup/ media/

# بازیابی تنظیمات
rm -rf istanbulplusir/settings/
mv settings_backup/ istanbulplusir/settings/
```

## تست نهایی

پس از مهاجرت، موارد زیر را تست کنید:

- [ ] ثبت‌نام کاربر جدید
- [ ] ورود با رمز عبور
- [ ] ورود با OTP
- [ ] بازیابی رمز عبور
- [ ] تأیید ایمیل
- [ ] تأیید شماره موبایل
- [ ] ویرایش پروفایل
- [ ] آپلود عکس پروفایل
- [ ] مشاهده جلسات فعال
- [ ] خروج از جلسه
- [ ] تنظیمات امنیتی
- [ ] Rate limiting
- [ ] هشدارهای امنیتی

## پشتیبانی

در صورت بروز مشکل در فرآیند مهاجرت:

- **ایمیل**: tech-support@istanbulplus.ir
- **تلفن**: +98 21 1234 5678
- **مستندات**: https://docs.istanbulplus.ir/migration
- **GitHub Issues**: https://github.com/istanbulplus/issues

## Changelog

### نسخه 1.0.0

- سیستم احراز هویت پیشرفته
- مدیریت جلسات
- احراز هویت دو مرحله‌ای
- تأیید ایمیل و موبایل
- بازیابی رمز عبور
- Rate limiting
- لاگ امنیتی

**تاریخ انتشار**: دی 1403  
**سازگاری**: Django 4.2+, Python 3.8+

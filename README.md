# Istanbul Plus E-commerce

یک پلتفرم فروشگاه آنلاین با جنگو ۵.۲ با قابلیت احراز هویت OTP و پرداخت آنلاین.

## ویژگی‌ها

- **مدیریت کاربران**: مدل سفارشی کاربر با امکان ثبت‌نام/ورود از طریق OTP پیامکی
- **محصولات**: دسته‌بندی درختی، محصولات فیزیکی/دیجیتال با تصاویر/فایل‌ها
- **سبد خرید**: سبد خرید مبتنی بر نشست با به‌روزرسانی Ajax
- **سفارشات**: مدیریت سفارش با رزرو موجودی
- **پرداخت**: درگاه پرداخت آزمایشی زرین‌پال
- **هسته**: رابط کاربری Bootstrap، صفحه اصلی با محصولات ویژه

## نیازمندی‌ها

- Python 3.8+
- Django 5.2.6
- Django REST Framework 3.15.2
- و سایر وابستگی‌ها در `requirements.txt`

## نصب و راه‌اندازی

1. کلون پروژه و نصب وابستگی‌ها:

```bash
git clone <repository-url>
cd istanbulplusir
pip install -r requirements.txt
```

2. اعمال مهاجرت‌ها:

```bash
python manage.py migrate --settings=istanbulplusir.settings.dev
```

3. ساخت کاربر مدیر:

```bash
python manage.py createsuperuser --settings=istanbulplusir.settings.dev
```

4. بارگذاری داده‌های نمونه:

```bash
python manage.py init_sample_data --settings=istanbulplusir.settings.dev
```

5. اجرای سرور توسعه:

```bash
python manage.py runserver --settings=istanbulplusir.settings.dev
```

## تنظیمات

- تنظیمات توسعه: `istanbulplusir/settings/dev.py` (SQLite، ایمیل و پیامک کنسول)
- تنظیمات تولید: یک فایل `prod.py` با PostgreSQL و تنظیمات واقعی ایجاد کنید.

## آدرس‌ها

- API: `/api/users/`, `/api/products/`, ...
- رابط کاربری: `/`, `/products/`, `/cart/`, `/orders/`
- پنل مدیریت: `/admin/`

## ورود به سیستم

- کاربر مدیر پیش‌فرض: testadmin / test123
- یا ثبت‌نام کاربر جدید از طریق `/users/register/`

## توسعه

پروژه از DRF برای API و JWT برای احراز هویت استفاده می‌کند.  
برای تست محصولات دیجیتال، فایل‌های PDF نمونه در `products/files/` قرار دارند.

## چندزبانه

پروژه برای فارسی و انگلیسی آماده است (Django i18n).  
فایل‌های ترجمه در پوشه `locale/` قرار دارند.

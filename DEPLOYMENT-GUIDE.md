# Istanbul Plus - راهنمای استقرار Production

## 🚀 راه‌اندازی سریع (Quick Start)

### برای تست محلی:
```bash
# اجرای اسکریپت استقرار سریع
chmod +x scripts/quick-deploy.sh
./scripts/quick-deploy.sh
```

### برای استقرار Production:
```bash
# اجرای اسکریپت استقرار کامل
chmod +x scripts/production-setup.sh
sudo ./scripts/production-setup.sh
```

## 📋 پیش‌نیازها

### برای استقرار محلی:
- Python 3.9+
- pip
- Git

### برای استقرار Production:
- Ubuntu 20.04+ یا CentOS 8+
- دسترسی root
- دامنه ثبت شده
- حداقل 2GB RAM
- حداقل 20GB فضای دیسک

## 🏗️ مراحل استقرار Production

### 1. آماده‌سازی سرور

```bash
# به‌روزرسانی سیستم
sudo apt update && sudo apt upgrade -y

# نصب پکیج‌های ضروری
sudo apt install -y curl wget git
```

### 2. اجرای اسکریپت استقرار

```bash
# کلون کردن پروژه
git clone https://github.com/istanbulplusir-blip/plus.git
cd plus

# اجرای اسکریپت استقرار
chmod +x scripts/production-setup.sh
sudo ./scripts/production-setup.sh
```

### 3. تنظیم DNS

دامنه خود را به IP سرور متصل کنید:
```
A Record: istanbulplus.ir -> YOUR_SERVER_IP
CNAME: www.istanbulplus.ir -> istanbulplus.ir
```

### 4. تنظیم متغیرهای محیطی

فایل `.env` را ویرایش کنید:
```bash
sudo nano /var/www/istanbulplus/.env
```

تنظیمات مهم:
```env
# ایمیل
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# SMS
OTP_SMS_API_KEY=your_sms_api_key
OTP_SMS_SENDER=your_sms_sender

# پرداخت
PAYMENT_MERCHANT_ID=your_merchant_id
PAYMENT_CALLBACK_URL=https://istanbulplus.ir/payments/callback/
```

### 5. ایجاد Superuser

```bash
sudo -u istanbulplus /var/www/istanbulplus/venv/bin/python manage.py createsuperuser
```

## 🔧 مدیریت سرویس‌ها

### بررسی وضعیت سرویس‌ها:
```bash
systemctl status istanbulplus
systemctl status istanbulplus-celery
systemctl status nginx
systemctl status postgresql
systemctl status redis-server
```

### راه‌اندازی مجدد سرویس‌ها:
```bash
systemctl restart istanbulplus
systemctl restart istanbulplus-celery
systemctl restart nginx
```

### مشاهده لاگ‌ها:
```bash
# لاگ‌های Django
journalctl -u istanbulplus -f

# لاگ‌های Nginx
tail -f /var/log/nginx/error.log
tail -f /var/log/nginx/access.log

# لاگ‌های پروژه
tail -f /var/log/istanbulplus/application.log
```

## 📦 به‌روزرسانی پروژه

### استقرار به‌روزرسانی‌ها:
```bash
chmod +x scripts/production-deploy.sh
sudo ./scripts/production-deploy.sh
```

### به‌روزرسانی دستی:
```bash
cd /var/www/istanbulplus
sudo -u istanbulplus git pull
sudo -u istanbulplus /var/www/istanbulplus/venv/bin/pip install -r requirements/prod.txt
sudo -u istanbulplus /var/www/istanbulplus/venv/bin/python manage.py migrate
sudo -u istanbulplus /var/www/istanbulplus/venv/bin/python manage.py collectstatic --noinput
systemctl restart istanbulplus
```

## 🔒 امنیت

### تنظیمات امنیتی اعمال شده:
- SSL/TLS با Let's Encrypt
- Security Headers
- Rate Limiting
- Fail2Ban
- Firewall (UFW)
- CSRF Protection
- XSS Protection

### بررسی امنیت:
```bash
# اجرای اسکریپت بررسی امنیت
chmod +x scripts/security-audit.sh
sudo ./scripts/security-audit.sh
```

## 📊 مانیتورینگ

### Health Check:
```bash
curl https://istanbulplus.ir/health/
```

### Metrics:
```bash
curl https://istanbulplus.ir/metrics/
```

### System Info:
```bash
curl https://istanbulplus.ir/system-info/
```

## 💾 پشتیبان‌گیری

### پشتیبان‌گیری خودکار:
پشتیبان‌گیری روزانه در ساعت 3 صبح انجام می‌شود.

### پشتیبان‌گیری دستی:
```bash
sudo /usr/local/bin/istanbulplus-backup.sh
```

### بازیابی:
```bash
# بازیابی دیتابیس
sudo -u postgres psql istanbulplus_db < backup_file.sql

# بازیابی فایل‌های رسانه
tar -xzf media_backup.tar.gz -C /var/www/istanbulplus/
```

## 🛠️ عیب‌یابی

### مشکلات رایج:

#### 1. سرویس شروع نمی‌شود:
```bash
systemctl status istanbulplus
journalctl -u istanbulplus -f
```

#### 2. خطای دیتابیس:
```bash
sudo -u postgres psql -c "SELECT * FROM pg_stat_activity;"
```

#### 3. خطای Nginx:
```bash
nginx -t
systemctl status nginx
```

#### 4. خطای SSL:
```bash
certbot certificates
certbot renew --dry-run
```

## 📞 پشتیبانی

### اطلاعات مفید:
- **پروژه**: `/var/www/istanbulplus`
- **لاگ‌ها**: `/var/log/istanbulplus`
- **پشتیبان‌ها**: `/backups/istanbulplus`
- **تنظیمات**: `/var/www/istanbulplus/.env`

### دستورات مفید:
```bash
# بررسی فضای دیسک
df -h

# بررسی استفاده از RAM
free -h

# بررسی پردازش‌ها
htop

# بررسی اتصالات شبکه
netstat -tulpn
```

## 🎯 نتیجه

پس از تکمیل مراحل بالا، سایت Istanbul Plus در آدرس `https://istanbulplus.ir` در دسترس خواهد بود.

**موفق باشید! 🚀**

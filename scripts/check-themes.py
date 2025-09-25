#!/usr/bin/env python3
"""
Theme Status Checker
بررسی وضعیت فایل‌های تم و تنظیمات
"""

import os
import re
from pathlib import Path

def check_file_exists(file_path, description):
    """بررسی وجود فایل"""
    if os.path.exists(file_path):
        print(f"✅ {description}")
        return True
    else:
        print(f"❌ {description} - فایل موجود نیست: {file_path}")
        return False

def check_css_imports():
    """بررسی import های CSS"""
    main_css = "static/css/main.css"
    if not os.path.exists(main_css):
        print("❌ فایل main.css موجود نیست")
        return False
    
    with open(main_css, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_imports = [
        'themes/light.css',
        'themes/dark.css', 
        'utilities/theme-fixes.css'
    ]
    
    print("\n🔗 بررسی import های CSS:")
    all_good = True
    for import_file in required_imports:
        if import_file in content:
            print(f"✅ {import_file} import شده")
        else:
            print(f"❌ {import_file} import نشده")
            all_good = False
    
    return all_good

def check_theme_variables():
    """بررسی متغیرهای تم"""
    files_to_check = {
        "static/css/base/variables.css": [
            "--color-background",
            "--color-text-primary", 
            "--theme-transition"
        ],
        "static/css/themes/light.css": [
            "--color-nav-background",
            "--color-card-background"
        ],
        "static/css/themes/dark.css": [
            "--color-background: #0a0a0a",
            "--color-text-primary: var(--color-gray-100)"
        ]
    }
    
    print("\n🎨 بررسی متغیرهای تم:")
    all_good = True
    
    for file_path, variables in files_to_check.items():
        if not os.path.exists(file_path):
            print(f"❌ فایل موجود نیست: {file_path}")
            all_good = False
            continue
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        for variable in variables:
            if variable in content:
                print(f"✅ {variable} در {os.path.basename(file_path)}")
            else:
                print(f"❌ {variable} در {os.path.basename(file_path)} موجود نیست")
                all_good = False
    
    return all_good

def check_template_integration():
    """بررسی ادغام در template"""
    template_file = "templates/base.html"
    if not os.path.exists(template_file):
        print("❌ فایل base.html موجود نیست")
        return False
    
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('class="no-js"', 'کلاس no-js در HTML'),
        ('data-theme="light"', 'تنظیم تم پیش‌فرض'),
        ('theme-manager.js', 'اسکریپت مدیریت تم'),
        ('theme-debug.js', 'اسکریپت دیباگ تم (در حالت debug)'),
        ('css-template-tags.html', 'فایل CSS template tags')
    ]
    
    print("\n🌐 بررسی ادغام در template:")
    all_good = True
    
    for check, description in checks:
        if check in content:
            print(f"✅ {description}")
        else:
            print(f"❌ {description} موجود نیست")
            all_good = False
    
    return all_good

def check_css_template_tags():
    """بررسی فایل CSS template tags"""
    css_tags_file = "templates/css/css-template-tags.html"
    if not os.path.exists(css_tags_file):
        print("❌ فایل css-template-tags.html موجود نیست")
        return False
    
    with open(css_tags_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("\n📄 بررسی CSS template tags:")
    
    # بررسی که فایل‌های اصلی CSS بارگذاری می‌شوند
    if 'main.css' in content:
        print("✅ main.css بارگذاری می‌شود")
    else:
        print("❌ main.css بارگذاری نمی‌شود")
        return False
    
    # بررسی fallback برای CSS variables
    if 'css-vars-fallback.css' in content:
        print("✅ CSS variables fallback تنظیم شده")
    else:
        print("❌ CSS variables fallback تنظیم نشده")
        return False
    
    return True

def generate_summary():
    """تولید خلاصه وضعیت"""
    print("\n" + "="*60)
    print("📊 خلاصه بررسی تم‌ها")
    print("="*60)
    
    results = {
        "فایل‌های اصلی": check_essential_files(),
        "Import های CSS": check_css_imports(),
        "متغیرهای تم": check_theme_variables(), 
        "ادغام Template": check_template_integration(),
        "CSS Template Tags": check_css_template_tags()
    }
    
    passed = sum(results.values())
    total = len(results)
    
    print(f"\n📋 نتایج:")
    for category, result in results.items():
        status = "✅ موفق" if result else "❌ ناموفق"
        print(f"  {category}: {status}")
    
    print(f"\n🎯 کل: {passed}/{total} بررسی موفق")
    
    if passed == total:
        print("\n🎉 همه بررسی‌ها موفق! تم‌ها آماده استفاده هستند.")
        print("\n🚀 مراحل بعدی:")
        print("  1. سرور Django را اجرا کنید")
        print("  2. صفحه را در مرورگر باز کنید") 
        print("  3. دکمه تغییر تم را تست کنید")
        print("  4. در حالت debug از Ctrl+Shift+T استفاده کنید")
        return True
    else:
        print("\n⚠️ برخی مشکلات وجود دارد. لطفاً موارد بالا را بررسی کنید.")
        return False

def check_essential_files():
    """بررسی فایل‌های ضروری"""
    essential_files = [
        ("static/css/main.css", "فایل CSS اصلی"),
        ("static/css/themes/light.css", "تم روشن"),
        ("static/css/themes/dark.css", "تم تاریک"),
        ("static/css/utilities/theme-fixes.css", "رفع مشکلات تم"),
        ("static/js/theme-manager.js", "مدیریت تم"),
        ("templates/base.html", "Template اصلی"),
        ("templates/css/css-template-tags.html", "CSS Template Tags")
    ]
    
    print("📁 بررسی فایل‌های ضروری:")
    all_good = True
    
    for file_path, description in essential_files:
        if not check_file_exists(file_path, description):
            all_good = False
    
    return all_good

def main():
    """تابع اصلی"""
    print("🎨 بررسی وضعیت تم‌های Istanbul Plus")
    print("="*50)
    
    success = generate_summary()
    
    if success:
        exit(0)
    else:
        exit(1)

if __name__ == "__main__":
    main()
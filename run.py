#!/usr/bin/env python3
"""
🤖 بوت يوكي - نقطة تشغيل بديلة
Alternative startup script for Yuki Bot
"""

import sys
import os
import logging
import subprocess

def check_requirements():
    """التحقق من المتطلبات"""
    print("🔍 فحص المتطلبات...")
    
    # فحص Python version
    if sys.version_info < (3, 8):
        print("❌ يتطلب البوت Python 3.8 أو أحدث")
        return False
    
    # فحص وجود الملفات المطلوبة
    required_files = ['main.py', 'config.py', 'requirements.txt']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ الملف {file} غير موجود")
            return False
    
    print("✅ جميع المتطلبات متوفرة")
    return True

def install_dependencies():
    """تثبيت المكتبات المطلوبة"""
    print("📦 تثبيت المكتبات...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ تم تثبيت جميع المكتبات بنجاح")
        return True
    except subprocess.CalledProcessError:
        print("❌ فشل في تثبيت المكتبات")
        return False

def setup_database():
    """إعداد قاعدة البيانات"""
    print("🗄️ إعداد قاعدة البيانات...")
    try:
        if os.path.exists('database_setup.py'):
            subprocess.check_call([sys.executable, "database_setup.py"])
        print("✅ تم إعداد قاعدة البيانات")
        return True
    except:
        print("⚠️ تحذير: لم يتم العثور على ملف إعداد قاعدة البيانات")
        return True

def main():
    """تشغيل البوت"""
    print("🤖 مرحباً بك في بوت يوكي!")
    print("=" * 50)
    
    if not check_requirements():
        print("❌ لا يمكن تشغيل البوت")
        sys.exit(1)
    
    # السؤال عن تثبيت المكتبات
    install = input("هل تريد تثبيت/تحديث المكتبات؟ (y/n): ").lower()
    if install in ['y', 'yes', 'نعم', 'ن']:
        if not install_dependencies():
            print("❌ لا يمكن المتابعة بدون المكتبات")
            sys.exit(1)
    
    setup_database()
    
    print("\n🚀 تشغيل بوت يوكي...")
    print("=" * 50)
    
    try:
        # تشغيل البوت الرئيسي
        import main
        # سيتم تشغيل البوت تلقائياً من main.py
    except KeyboardInterrupt:
        print("\n⛔ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        print(f"\n❌ خطأ في تشغيل البوت: {e}")
        logging.error(f"خطأ في تشغيل البوت: {e}")

if __name__ == "__main__":
    main()
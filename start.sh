#!/bin/bash

# 🤖 سكريبت تشغيل بوت يوكي لـ Linux/Mac
# Yuki Bot startup script for Linux/Mac

echo "🤖 مرحباً بك في بوت يوكي!"
echo "=============================="

# التحقق من وجود Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 غير مثبت"
    exit 1
fi

# التحقق من إصدار Python
python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 إصدار Python: $python_version"

if (( $(echo "$python_version < 3.8" | bc -l) )); then
    echo "❌ يتطلب Python 3.8 أو أحدث"
    exit 1
fi

# إنشاء بيئة وهمية إذا لم تكن موجودة
if [ ! -d "venv" ]; then
    echo "📦 إنشاء بيئة وهمية..."
    python3 -m venv venv
fi

# تفعيل البيئة الوهمية
echo "🔄 تفعيل البيئة الوهمية..."
source venv/bin/activate

# تحديث pip
echo "⬆️ تحديث pip..."
pip install --upgrade pip

# تثبيت المتطلبات
echo "📋 تثبيت المتطلبات..."
pip install -r requirements.txt

# إعداد قاعدة البيانات
if [ -f "database_setup.py" ]; then
    echo "🗄️ إعداد قاعدة البيانات..."
    python database_setup.py
fi

# التحقق من وجود ملف المفاتيح
if [ ! -f "api.txt" ]; then
    echo "⚠️ تحذير: ملف api.txt غير موجود"
    echo "📝 تأكد من إنشاء ملف api.txt مع مفاتيحك"
fi

# تشغيل البوت
echo "🚀 تشغيل بوت يوكي..."
echo "=============================="
python main.py
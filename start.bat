@echo off
chcp 65001 >nul
echo.
echo 🤖 مرحباً بك في بوت يوكي!
echo ==============================
echo.

:: التحقق من وجود Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python غير مثبت أو غير موجود في PATH
    echo 📥 يرجى تحميل Python من https://python.org
    pause
    exit /b 1
)

:: عرض إصدار Python
echo 🐍 إصدار Python:
python --version

:: إنشاء بيئة وهمية إذا لم تكن موجودة
if not exist "venv\" (
    echo.
    echo 📦 إنشاء بيئة وهمية...
    python -m venv venv
)

:: تفعيل البيئة الوهمية
echo.
echo 🔄 تفعيل البيئة الوهمية...
call venv\Scripts\activate

:: تحديث pip
echo.
echo ⬆️ تحديث pip...
python -m pip install --upgrade pip

:: تثبيت المتطلبات
echo.
echo 📋 تثبيت المتطلبات...
pip install -r requirements.txt

:: إعداد قاعدة البيانات
if exist "database_setup.py" (
    echo.
    echo 🗄️ إعداد قاعدة البيانات...
    python database_setup.py
)

:: التحقق من وجود ملف المفاتيح
if not exist "api.txt" (
    echo.
    echo ⚠️ تحذير: ملف api.txt غير موجود
    echo 📝 تأكد من إنشاء ملف api.txt مع مفاتيحك
    echo.
)

:: تشغيل البوت
echo.
echo 🚀 تشغيل بوت يوكي...
echo ==============================
echo.
python main.py

:: الانتظار قبل الإغلاق
echo.
pause
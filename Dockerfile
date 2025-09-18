# استخدام Python 3.11 كصورة أساسية
FROM python:3.11-slim

# تحديد مجلد العمل
WORKDIR /app

# تثبيت متطلبات النظام
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libcairo2-dev \
    libpango1.0-dev \
    libgdk-pixbuf2.0-dev \
    libgirepository1.0-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المتطلبات أولاً للاستفادة من التخزين المؤقت
COPY requirements.txt .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# إنشاء مستخدم غير root للأمان
RUN useradd -m -u 1000 botuser

# نسخ جميع ملفات البوت
COPY . .

# إنشاء مجلد للقاعدة البيانات والملفات المؤقتة
RUN mkdir -p temp_media && mkdir -p attached_assets

# إعطاء الصلاحيات المناسبة للمستخدم غير root
RUN chown -R botuser:botuser /app
RUN chmod +x main.py

USER botuser

# تشغيل البوت
CMD ["python", "main.py"]
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
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# نسخ ملفات المتطلبات أولاً للاستفادة من التخزين المؤقت
COPY requirements.txt .

# تثبيت المكتبات المطلوبة
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# نسخ جميع ملفات البوت
COPY . .

# إنشاء مجلد للقاعدة البيانات والملفات المؤقتة
RUN mkdir -p temp_media
RUN mkdir -p attached_assets

# إعطاء الصلاحيات المناسبة
RUN chmod +x main.py

# تحديد المنفذ (إذا كان البوت يحتاج لخدمة ويب)
EXPOSE 8080

# تشغيل البوت
CMD ["python", "main.py"]
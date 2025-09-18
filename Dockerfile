# استخدام صورة أساسية خفيفة من Python
FROM python:3.10-slim-bullseye

# تعيين اللغة والتشفير لتجنب مشاكل الأحرف
ENV LANG C.UTF-8
ENV LC_ALL C.UTF-8

# تحديث قائمة الحزم وتثبيت المتطلبات النظامية
RUN apt-get update --fix-missing && \
    apt-get install -y --no-install-recommends \
    gcc \
    g++ \
    python3-dev \
    libffi-dev \
    libssl-dev \
    libcairo2 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf2.0-0 \
    libgirepository-1.0-1 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# إنشاء مجلد للتطبيق وتعيين صلاحيات
WORKDIR /app
RUN chmod 755 /app

# نسخ متطلبات التطبيق أولاً (للاستفادة من طبقات Docker المحسنة)
COPY requirements.txt .

# تثبيت متطلبات Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات التطبيق
COPY . .

# تعيين الأمر الافتراضي لتشغيل البوت
CMD ["python", "main.py"]

# التعليقات التوضيحية:
# 1. استخدام python:3.10-slim-bullseye بدلاً من Ubuntu لتقليل حجم الصورة
# 2. إضافة --no-install-recommends لتجنب تثبيت حزم غير ضرورية
# 3. إضافة --fix-missing لحل مشاكل التبعيات
# 4. استخدام --no-cache-dir مع pip لمنع تخزين ذاكرة التخزين المؤقت
# 5. نسخ requirements.txt أولاً للاستفادة من محاذاة الطبقات في Docker# إعطاء الصلاحيات المناسبة للمستخدم غير root
RUN chown -R botuser:botuser /app
RUN chmod +x main.py

USER botuser

# تشغيل البوت
CMD ["python", "main.py"]

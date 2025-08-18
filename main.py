"""
البوت الرئيسي - نقطة دخول التطبيق مع خادم ويب للحفاظ على التشغيل
Main Bot Entry Point with Web Server for 24/7 Uptime
"""

import asyncio
import logging
import sys
import os
import json
import requests
import traceback
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

# إضافة استيرادات خادم الويب
from flask import Flask
from threading import Thread

from config.settings import BOT_TOKEN
from config.database import init_database
from handlers import commands, callbacks, messages
from utils.helpers import setup_logging

# إنشاء تطبيق Flask
web_app = Flask(__name__)

@web_app.route('/')
def home():
    """صفحة رئيسية لإظهار حالة التشغيل"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Yukibot 6.0.34</title>
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #1a1a2e, #16213e);
                color: #fff;
                height: 100vh;
                margin: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                text-align: center;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                max-width: 600px;
            }
            h1 {
                color: #4ecca3;
                font-size: 2.5rem;
                margin-bottom: 20px;
            }
            .status {
                font-size: 1.5rem;
                margin: 30px 0;
                color: #4ecca3;
                font-weight: bold;
            }
            .details {
                text-align: left;
                background: rgba(0, 0, 0, 0.2);
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            .details p {
                margin: 10px 0;
            }
            .logo {
                width: 120px;
                height: 120px;
                margin: 0 auto 20px;
                background: url('https://i.imgur.com/logo-placeholder.png') center/contain no-repeat;
            }
            .version {
                font-size: 0.9rem;
                opacity: 0.7;
                margin-top: 30px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo"></div>
            <h1>Yukibot 6.0.34</h1>
            <div class="status">✅ البوت يعمل بنجاح 24/7</div>
            
            <div class="details">
                <p><strong>الحالة الحالية:</strong> نشط ومستقر</p>
                <p><strong>وقت التشغيل:</strong> منذ 00:00:00</p>
                <p><strong>النسخة:</strong> 6.0.34</p>
                <p><strong>المطور:</strong> tilajed620</p>
                <p><strong>نظام الحماية:</strong> مفعل</p>
            </div>
            
            <div class="version">
                تم التحديث في: 18 أغسطس 2025 | نظام Uptime Robot
            </div>
        </div>
    </body>
    </html>
    """

def run_web_server():
    """تشغيل خادم الويب في خيط منفصل"""
    web_app.run(host='0.0.0.0', port=8080)

async def check_restart_status(bot):
    """فحص حالة إعادة التشغيل وإرسال رسالة تأكيد"""
    try:
        if os.path.exists('restart_info.json'):
            with open('restart_info.json', 'r', encoding='utf-8') as f:
                restart_info = json.load(f)
            
            # إرسال رسالة تأكيد إعادة التشغيل
            success_message = (
                "✅ **تم إعادة التشغيل بنجاح!**\n\n"
                f"👑 السيد: {restart_info['username']}\n"
                f"🔄 تمت إعادة تشغيل البوت بنجاح\n"
                f"⚡ النظام يعمل الآن بشكل طبيعي\n\n"
                f"📊 **تفاصيل العملية:**\n"
                f"• المعرف: `{restart_info['user_id']}`\n"
                f"• تمت إعادة التشغيل بأمر مطلق\n"
                f"• جميع الأنظمة تعمل بشكل صحيح\n\n"
                f"🎯 **البوت جاهز لاستقبال الأوامر**"
            )
            
            await bot.send_message(restart_info['chat_id'], success_message)
            
            # حذف ملف المعلومات بعد الإرسال
            os.remove('restart_info.json')
            logging.info(f"تم إرسال رسالة تأكيد إعادة التشغيل للسيد: {restart_info['user_id']}")
            
    except Exception as e:
        logging.error(f"خطأ في فحص حالة إعادة التشغيل: {e}")

async def main():
    """دالة تشغيل البوت الرئيسية"""
    # إعداد نظام التسجيل
    setup_logging()
    logging.info("🚀 بدء تهيئة نظام البوت...")
    
    # بدء خادم الويب في خيط منفصل
    try:
        web_thread = Thread(target=run_web_server)
        web_thread.daemon = True
        web_thread.start()
        logging.info("🌐 بدء خادم الويب على المنفذ 8080")
        
        # اختبار الخادم
        try:
            response = requests.get('http://localhost:8080', timeout=3)
            logging.info(f"✅ اختبار خادم الويب ناجح: {response.status_code}")
        except Exception as test_error:
            logging.warning(f"⚠️ تحذير في اختبار خادم الويب: {test_error}")
            
    except Exception as web_error:
        logging.error(f"❌ خطأ في بدء خادم الويب: {web_error}")
    
    # إنشاء كائن البوت مع الإعدادات الافتراضية
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
    
    # إنشاء موزع الأحداث
    dp = Dispatcher()
    
    # تسجيل معالجات الأحداث
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(messages.router)
    
    # تسجيل معالج أحداث المجموعات
    from handlers import group_events
    dp.include_router(group_events.router)
    
    # تهيئة قاعدة البيانات
    await init_database()
    logging.info("💾 تم تهيئة قاعدة البيانات")
    
    # تحميل الرتب من قاعدة البيانات
    from config.hierarchy import load_ranks_from_database
    await load_ranks_from_database()
    logging.info("👑 تم تحميل هيكل الرتب")
    
    # تحميل الأوامر المخصصة
    from modules.custom_commands import load_custom_commands
    await load_custom_commands()
    logging.info("⌨️ تم تحميل الأوامر المخصصة")
    
    # تحميل إعدادات التحميل
    from modules.media_download import load_download_settings
    await load_download_settings()
    logging.info("📥 تم تحميل إعدادات التحميل")
    
    # فحص إعادة التشغيل وإرسال رسالة تأكيد
    await check_restart_status(bot)
    
    try:
        logging.info("🚀 بدء تشغيل البوت...")
        
        # التأكد من إغلاق أي webhooks نشطة
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logging.info("✅ تم حذف جميع الـ webhooks والتحديثات المعلقة")
        except Exception as webhook_error:
            logging.warning(f"⚠️ تحذير في حذف الـ webhooks: {webhook_error}")
        
        # إضافة تأخير قصير للتأكد من تطبيق التغييرات
        await asyncio.sleep(2)
        
        # إرسال إشعار بدء التشغيل للقناة الفرعية
        try:
            from modules.notification_manager import NotificationManager
            notification_manager = NotificationManager(bot)
            await notification_manager.send_startup_notification("6.0.34")
        except Exception as startup_error:
            logging.warning(f"⚠️ تحذير: لم يتم إرسال إشعار بدء التشغيل: {startup_error}")
        
        # بدء التصويت
        logging.info("🔍 بدء استقبال الرسائل...")
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logging.info("🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logging.error(f"❌ خطأ في تشغيل البوت: {e}")
        logging.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
    finally:
        try:
            await bot.session.close()
            logging.info("✅ تم إغلاق جلسة البوت بنجاح")
        except Exception as close_error:
            logging.error(f"خطأ في إغلاق الجلسة: {close_error}")

if __name__ == "__main__":
    if sys.version_info < (3, 8):
        logging.error("❌ يتطلب Python 3.8 أو أحدث")
        sys.exit(1)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.info("🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logging.error(f"❌ خطأ غير متوقع: {e}")
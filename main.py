"""
البوت الرئيسي - نقطة دخول التطبيق
Main Bot Entry Point with Professional Structure
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import BOT_TOKEN
from config.database import init_database
from handlers import commands, callbacks, messages, smart_commands
from utils.helpers import setup_logging

# متغير عام لتتبع وقت بدء التشغيل
BOT_START_TIME = None


async def check_restart_status(bot):
    """فحص حالة إعادة التشغيل وإرسال رسالة تأكيد"""
    try:
        import json
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
    global BOT_START_TIME
    BOT_START_TIME = datetime.now()  # تسجيل وقت بدء التشغيل
    
    # إعداد نظام التسجيل
    setup_logging()
    
    # إنشاء كائن البوت مع الإعدادات الافتراضية
    bot = Bot(token=BOT_TOKEN)
    
    # إنشاء موزع الأحداث
    dp = Dispatcher()
    
    # تسجيل معالجات الأحداث
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(smart_commands.router)
    
    # تسجيل النظام الشامل لكشف المحتوى (قبل معالج الرسائل العام)
    from handlers import comprehensive_content_handler
    dp.include_router(comprehensive_content_handler.router)
    
    dp.include_router(messages.router)
    
    # تسجيل معالج أحداث المجموعات
    from handlers import group_events
    dp.include_router(group_events.router)
    
    # تسجيل معالج تتبع رسائل المجموعة للذاكرة المشتركة
    from handlers import group_message_tracker
    dp.include_router(group_message_tracker.router)
    
    # تسجيل أوامر الذاكرة المشتركة
    from handlers import memory_commands
    dp.include_router(memory_commands.router)
    
    # تسجيل نظام كشف السباب الذكي
    from modules import ai_profanity_commands
    dp.include_router(ai_profanity_commands.router)
    
    # تهيئة قاعدة البيانات
    await init_database()
    
    # تهيئة نظام التصنيف
    try:
        from modules.ranking_system import init_ranking_system
        await init_ranking_system()
    except Exception as e:
        logging.error(f"خطأ في تهيئة نظام التصنيف: {e}")
    
    # تحميل الرتب من قاعدة البيانات
    from config.hierarchy import load_ranks_from_database
    await load_ranks_from_database()
    
    # تحميل الأوامر المخصصة
    from modules.custom_commands import load_custom_commands
    await load_custom_commands()
    
    # تحميل إعدادات التحميل
    from modules.media_download import load_download_settings
    await load_download_settings()
    
    # تهيئة نظام الحماية المتطور من الألفاظ المسيئة
    try:
        from modules.profanity_filter import init_abusive_db, init_ml_model
        init_abusive_db()
        init_success = init_ml_model()
        if init_success:
            logging.info("✅ تم تهيئة نظام الحماية بنجاح")
        else:
            logging.info("⚠️ تم تهيئة قاعدة البيانات بدون نموذج ML")
    except Exception as protection_error:
        logging.error(f"⚠️ خطأ في تهيئة نظام الحماية: {protection_error}")
    
    # تهيئة النظام الذكي لكشف السباب
    try:
        from modules.ai_profanity_detector import ai_detector
        logging.info("🧠 تم تهيئة النظام الذكي لكشف السباب المتطور")
    except Exception as smart_detection_error:
        logging.error(f"❌ خطأ في تهيئة النظام الذكي: {smart_detection_error}")
    
    # تهيئة نظام الذكاء الاصطناعي الحقيقي (Real Yuki AI)
    try:
        from modules.real_ai import setup_real_ai
        await setup_real_ai()
        logging.info("🧠 تم تهيئة نظام يوكي الذكي الحقيقي")
    except Exception as ai_error:
        logging.warning(f"⚠️ تحذير في تهيئة النظام الذكي الحقيقي: {ai_error}")
    
    # تهيئة نظام الذاكرة المشتركة مع NLTK
    try:
        from modules.shared_memory import shared_group_memory
        await shared_group_memory.init_shared_memory_db()
        logging.info("🧠 تم تهيئة نظام الذاكرة المشتركة والمواضيع المترابطة")
    except Exception as shared_error:
        logging.warning(f"⚠️ تحذير في تهيئة الذاكرة المشتركة: {shared_error}")
    
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
            await notification_manager.send_startup_notification("2.0")
        except Exception as startup_error:
            logging.warning(f"⚠️ تحذير: لم يتم إرسال إشعار بدء التشغيل: {startup_error}")
        
        # بدء التصويت
        await dp.start_polling(bot)
        
    except KeyboardInterrupt:
        logging.info("🛑 تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logging.error(f"❌ خطأ في تشغيل البوت: {e}")
        # إضافة تفاصيل أكثر عن الخطأ
        import traceback
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

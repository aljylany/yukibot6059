"""
البوت الرئيسي - نقطة دخول التطبيق
Main Bot Entry Point with Professional Structure
"""

import asyncio
import logging
import sys
import os
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from config.settings import BOT_TOKEN
from config.database import init_database
from handlers import commands, callbacks, messages
from utils.helpers import setup_logging


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
    # إعداد نظام التسجيل
    setup_logging()
    
    # إنشاء كائن البوت مع الإعدادات الافتراضية
    bot = Bot(token=BOT_TOKEN)
    
    # إنشاء موزع الأحداث
    dp = Dispatcher()
    
    # تسجيل معالجات الأحداث
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(messages.router)
    
    # تهيئة قاعدة البيانات
    await init_database()
    
    # تحميل الرتب من قاعدة البيانات
    from config.hierarchy import load_ranks_from_database
    await load_ranks_from_database()
    
    # تحميل الأوامر المخصصة
    from modules.custom_commands import load_custom_commands
    await load_custom_commands()
    
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

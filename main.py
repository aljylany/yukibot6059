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


async def main():
    """دالة تشغيل البوت الرئيسية"""
    # إعداد نظام التسجيل
    setup_logging()
    
    # إنشاء كائن البوت مع الإعدادات الافتراضية
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    # إنشاء موزع الأحداث
    dp = Dispatcher()
    
    # تسجيل معالجات الأحداث
    dp.include_router(commands.router)
    dp.include_router(callbacks.router)
    dp.include_router(messages.router)
    
    # تهيئة قاعدة البيانات
    await init_database()
    
    try:
        logging.info("🚀 بدء تشغيل البوت...")
        # حذف التحديثات المعلقة وبدء التصويت
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    except Exception as e:
        logging.error(f"❌ خطأ في تشغيل البوت: {e}")
    finally:
        await bot.session.close()


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

"""
تكامل نظام XP مع الأنشطة المختلفة
XP System Integration with Various Activities
"""

import logging
from aiogram.types import Message
from modules.xp_system import add_xp_for_activity
from modules.leveling import leveling_system


async def add_xp_for_banking(user_id: int, activity: str = "banking"):
    """إضافة XP للأنشطة المصرفية"""
    try:
        await add_xp_for_activity(user_id, activity)
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للنشاط المصرفي: {e}")


async def add_xp_for_investment(user_id: int):
    """إضافة XP للاستثمار"""
    try:
        await add_xp_for_activity(user_id, "investment")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للاستثمار: {e}")


async def add_xp_for_property(user_id: int):
    """إضافة XP للعقارات"""
    try:
        await add_xp_for_activity(user_id, "property_deal")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للعقارات: {e}")


async def add_xp_for_theft(user_id: int):
    """إضافة XP للسرقة"""
    try:
        await add_xp_for_activity(user_id, "theft")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للسرقة: {e}")


async def add_xp_for_farm(user_id: int):
    """إضافة XP للمزرعة"""
    try:
        await add_xp_for_activity(user_id, "farm_activity")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للمزرعة: {e}")


async def add_xp_for_castle(user_id: int):
    """إضافة XP للقلعة"""
    try:
        await add_xp_for_activity(user_id, "castle_activity")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للقلعة: {e}")


async def add_xp_for_message(user_id: int):
    """إضافة XP للرسائل"""
    try:
        await add_xp_for_activity(user_id, "message")
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للرسائل: {e}")


async def handle_user_level_command(message: Message):
    """معالجة أمر عرض المستوى"""
    try:
        from modules.xp_system import get_user_level_display
        
        level_info = await get_user_level_display(message.from_user.id)
        await message.reply(level_info)
        
    except Exception as e:
        logging.error(f"خطأ في عرض مستوى المستخدم: {e}")
        await message.reply("❌ حدث خطأ في عرض معلومات المستوى")
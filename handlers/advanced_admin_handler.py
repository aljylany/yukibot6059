"""
معالج الأوامر الإدارية المتقدمة
يدمج النظام الجديد للرتب والصلاحيات مع handlers/messages.py
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from modules.advanced_admin import (
    mute_user, kick_user, ban_user, promote_user_command, demote_user_command,
    show_user_rank_info, show_admin_panel, show_administrative_ranks,
    show_entertainment_ranks, handle_rank_selection, handle_promotion_reason,
    RankManagementStates
)
from config.ranks_system import rank_manager


async def handle_advanced_admin_commands(message: Message, state: FSMContext) -> bool:
    """
    معالجة الأوامر الإدارية المتقدمة
    
    Returns:
        True إذا تم التعامل مع الأمر، False إذا لم يكن أمر إداري
    """
    try:
        if not message.text:
            return False
        
        text = message.text.strip()
        
        # التحقق من حالة FSM الحالية
        current_state = await state.get_state()
        
        # معالجة حالات FSM لإدارة الرتب
        if current_state == RankManagementStates.waiting_for_rank_name:
            await handle_rank_selection(message, state)
            return True
        elif current_state == RankManagementStates.waiting_for_reason:
            await handle_promotion_reason(message, state)
            return True
        
        # أوامر إدارة المستخدمين
        if text == 'كتم':
            await mute_user(message)
            return True
        elif text == 'طرد':
            await kick_user(message)
            return True
        elif text == 'حظر':
            await ban_user(message)
            return True
        
        # أوامر إدارة الرتب
        elif text == 'ترقية':
            await promote_user_command(message, state)
            return True
        elif text == 'تخفيض':
            await demote_user_command(message)
            return True
        
        # أوامر عرض المعلومات
        elif text == 'رتبتي':
            await show_user_rank_info(message)
            return True
        elif text == 'رتبته':
            await show_user_rank_info(message)
            return True
        elif text == 'لوحة الإدارة':
            await show_admin_panel(message)
            return True
        elif text == 'الرتب الإدارية':
            await show_administrative_ranks(message)
            return True
        elif text == 'الرتب الترفيهية':
            await show_entertainment_ranks(message)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج الأوامر الإدارية المتقدمة: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الأمر الإداري")
        return True  # نعيد True لمنع معالجة أخرى للرسالة


async def init_advanced_admin_system():
    """تهيئة نظام الإدارة المتقدم"""
    try:
        # تهيئة جداول قاعدة البيانات
        await rank_manager.init_database_tables()
        
        # تحميل الرتب من قاعدة البيانات
        await rank_manager.load_ranks_from_database()
        
        logging.info("✅ تم تهيئة نظام الإدارة المتقدم بنجاح")
        
    except Exception as e:
        logging.error(f"خطأ في تهيئة نظام الإدارة المتقدم: {e}")


# دوال مساعدة للتحقق من الصلاحيات
async def user_can_use_admin_command(user_id: int, chat_id: int) -> bool:
    """التحقق من قدرة المستخدم على استخدام الأوامر الإدارية"""
    try:
        from config.hierarchy import is_master
        
        # فحص إذا كان Master
        if is_master(user_id):
            return True
        
        # فحص إذا كان له رتبة إدارية
        user_rank = rank_manager.get_user_rank(user_id, chat_id)
        if user_rank and user_rank.rank_type.value == "administrative":
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في فحص صلاحية الأوامر الإدارية: {e}")
        return False
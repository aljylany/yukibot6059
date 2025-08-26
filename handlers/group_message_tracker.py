"""
معالج تتبع رسائل المجموعة للذاكرة المشتركة
Group Message Tracker for Shared Memory
"""

from aiogram import Router, F
from aiogram.types import Message
import logging

router = Router()

@router.message(F.chat.type.in_({"group", "supergroup"}))
async def track_group_messages(message: Message):
    """تتبع جميع رسائل المجموعة للذاكرة المشتركة"""
    try:
        if not message.text or not message.from_user:
            return
        
        # تجاهل رسائل البوت نفسه
        if message.from_user.is_bot:
            return
        
        # حفظ الرسالة في الذاكرة المشتركة
        from modules.shared_memory import shared_memory
        
        username = message.from_user.first_name or message.from_user.username or "مجهول"
        
        await shared_memory.save_shared_conversation(
            message.chat.id,
            message.from_user.id,
            username,
            message.text
        )
        
        logging.debug(f"تم تتبع رسالة من {username} في المجموعة {message.chat.id}")
        
    except Exception as e:
        logging.error(f"خطأ في تتبع رسائل المجموعة: {e}")
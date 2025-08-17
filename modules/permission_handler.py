"""
معالج الردود المهينة للصلاحيات
Permission Handler with Insulting Responses
"""

import logging
from aiogram.types import Message
from config.hierarchy import AdminLevel, get_user_admin_level
from modules.permission_responses import (
    is_master_command, is_owner_command, is_moderator_command, 
    get_permission_denial_response
)

async def handle_permission_check(message: Message) -> bool:
    """
    معالج عام للتحقق من الصلاحيات مع الردود المهينة
    
    Returns:
        True إذا تم التعامل مع الرسالة، False إذا لم تكن أمر يحتاج صلاحيات
    """
    if not message.text or not message.from_user:
        return False
    
    user_id = message.from_user.id
    group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
    user_level = get_user_admin_level(user_id, group_id)
    text = message.text
    
    try:
        # فحص أوامر الأسياد
        if is_master_command(text):
            from config.hierarchy import MASTERS
            if user_id not in MASTERS:
                insulting_response = get_permission_denial_response(user_id, group_id, AdminLevel.MASTER)
                if insulting_response:
                    await message.reply(insulting_response)
                return True
        
        # فحص أوامر مالكي المجموعات  
        elif is_owner_command(text):
            if user_level.value < AdminLevel.GROUP_OWNER.value:
                insulting_response = get_permission_denial_response(user_id, group_id, AdminLevel.GROUP_OWNER)
                if insulting_response:
                    await message.reply(insulting_response)
                return True
        
        # فحص أوامر المشرفين
        elif is_moderator_command(text):
            if user_level.value < AdminLevel.MODERATOR.value:
                insulting_response = get_permission_denial_response(user_id, group_id, AdminLevel.MODERATOR)
                if insulting_response:
                    await message.reply(insulting_response)
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج الصلاحيات: {e}")
        return False
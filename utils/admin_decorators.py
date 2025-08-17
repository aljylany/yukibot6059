"""
أدوات التحقق من الصلاحيات الإدارية
Administrative Permission Decorators
"""

import logging
from functools import wraps
from aiogram.types import Message
from config.hierarchy import AdminLevel, has_permission, is_master, get_admin_level_name


def master_only(func):
    """decorator للتحقق من كون المستخدم سيد"""
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if not message.from_user:
            await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
            return
        
        if not is_master(message.from_user.id):
            await message.reply("🔴 هذا الأمر مخصص للأسياد فقط!")
            return
        
        return await func(message, *args, **kwargs)
    return wrapper


def min_level_required(required_level: AdminLevel):
    """decorator للتحقق من المستوى الإداري المطلوب"""
    def decorator(func):
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            if not message.from_user:
                await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
                return
            
            group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
            
            if not has_permission(message.from_user.id, required_level, group_id):
                required_name = get_admin_level_name(required_level)
                await message.reply(f"❌ هذا الأمر يتطلب مستوى {required_name} أو أعلى")
                return
            
            return await func(message, *args, **kwargs)
        return wrapper
    return decorator


def group_owner_or_master(func):
    """decorator للتحقق من كون المستخدم مالك المجموعة أو سيد"""
    return min_level_required(AdminLevel.GROUP_OWNER)(func)


def moderator_or_higher(func):
    """decorator للتحقق من كون المستخدم مشرف أو أعلى"""
    return min_level_required(AdminLevel.MODERATOR)(func)


def admin_command_check(message: Message, required_level: AdminLevel = AdminLevel.MODERATOR) -> tuple[bool, str]:
    """
    التحقق من صلاحية تنفيذ أمر إداري
    
    Returns:
        (has_permission, error_message)
    """
    if not message.from_user:
        return False, "❌ لا يمكن التحقق من هوية المستخدم"
    
    group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
    
    if not has_permission(message.from_user.id, required_level, group_id):
        required_name = get_admin_level_name(required_level)
        return False, f"❌ هذا الأمر يتطلب مستوى {required_name} أو أعلى"
    
    return True, ""


async def check_and_respond_permission(message: Message, required_level: AdminLevel = AdminLevel.MODERATOR) -> bool:
    """
    التحقق من الصلاحية مع الرد التلقائي في حالة عدم وجود صلاحية
    
    Returns:
        True إذا كان لديه صلاحية، False مع رسالة خطأ
    """
    has_perm, error_msg = admin_command_check(message, required_level)
    if not has_perm:
        await message.reply(error_msg)
    return has_perm
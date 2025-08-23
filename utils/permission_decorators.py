"""
نظام الـ Decorators المتقدم للصلاحيات
يدعم النظام الجديد للرتب والصلاحيات
"""

import logging
from functools import wraps
from typing import List, Callable, Any
from aiogram.types import Message

from config.ranks_system import rank_manager, Permission, RankType
from config.hierarchy import is_master


def require_permission(permission: Permission):
    """Decorator للتحقق من صلاحية محددة"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                if not message.from_user:
                    await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
                    return
                
                user_id = message.from_user.id
                chat_id = message.chat.id
                
                # فحص إذا كان المستخدم Master (صلاحيات مطلقة)
                if is_master(user_id):
                    return await func(message, *args, **kwargs)
                
                # فحص الصلاحية من النظام الجديد
                if rank_manager.user_has_permission(user_id, chat_id, permission):
                    return await func(message, *args, **kwargs)
                
                # رسالة خطأ مخصصة حسب الصلاحية
                permission_names = {
                    Permission.MUTE_USERS: "كتم المستخدمين",
                    Permission.KICK_USERS: "طرد المستخدمين", 
                    Permission.BAN_USERS: "حظر المستخدمين",
                    Permission.DELETE_MESSAGES: "حذف الرسائل",
                    Permission.MANAGE_RANKS: "إدارة الرتب",
                    Permission.ACCESS_ADMIN_PANEL: "الوصول للوحة الإدارة"
                }
                
                perm_name = permission_names.get(permission, "تنفيذ هذا الأمر")
                await message.reply(f"❌ تحتاج صلاحية {perm_name} لاستخدام هذا الأمر")
                
            except Exception as e:
                logging.error(f"خطأ في فحص الصلاحية {permission}: {e}")
                await message.reply("❌ حدث خطأ في التحقق من الصلاحية")
        
        return wrapper
    return decorator


def require_admin_rank():
    """Decorator للتحقق من امتلاك رتبة إدارية"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                if not message.from_user:
                    await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
                    return
                
                user_id = message.from_user.id
                chat_id = message.chat.id
                
                # فحص إذا كان المستخدم Master
                if is_master(user_id):
                    return await func(message, *args, **kwargs)
                
                # فحص إذا كان لديه رتبة إدارية
                user_rank = rank_manager.get_user_rank(user_id, chat_id)
                if user_rank and user_rank.rank_type == RankType.ADMINISTRATIVE:
                    return await func(message, *args, **kwargs)
                
                await message.reply("❌ هذا الأمر مخصص للمشرفين والإداريين فقط")
                
            except Exception as e:
                logging.error(f"خطأ في فحص الرتبة الإدارية: {e}")
                await message.reply("❌ حدث خطأ في التحقق من الرتبة")
        
        return wrapper
    return decorator


def require_multiple_permissions(permissions: List[Permission], require_all: bool = False):
    """Decorator للتحقق من عدة صلاحيات"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                if not message.from_user:
                    await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
                    return
                
                user_id = message.from_user.id
                chat_id = message.chat.id
                
                # فحص إذا كان المستخدم Master
                if is_master(user_id):
                    return await func(message, *args, **kwargs)
                
                # فحص الصلاحيات
                has_permissions = []
                for permission in permissions:
                    has_perm = rank_manager.user_has_permission(user_id, chat_id, permission)
                    has_permissions.append(has_perm)
                
                # تحديد إذا كان يحتاج جميع الصلاحيات أو واحدة فقط
                if require_all:
                    if all(has_permissions):
                        return await func(message, *args, **kwargs)
                else:
                    if any(has_permissions):
                        return await func(message, *args, **kwargs)
                
                requirement = "جميع" if require_all else "إحدى"
                await message.reply(f"❌ تحتاج {requirement} الصلاحيات المطلوبة لاستخدام هذا الأمر")
                
            except Exception as e:
                logging.error(f"خطأ في فحص الصلاحيات المتعددة: {e}")
                await message.reply("❌ حدث خطأ في التحقق من الصلاحيات")
        
        return wrapper
    return decorator


def rank_level_required(min_level: int):
    """Decorator للتحقق من مستوى الرتبة الإدارية"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                if not message.from_user:
                    await message.reply("❌ لا يمكن التحقق من هوية المستخدم")
                    return
                
                user_id = message.from_user.id
                chat_id = message.chat.id
                
                # فحص إذا كان المستخدم Master
                if is_master(user_id):
                    return await func(message, *args, **kwargs)
                
                # فحص مستوى الرتبة
                user_rank = rank_manager.get_user_rank(user_id, chat_id)
                if (user_rank and 
                    user_rank.rank_type == RankType.ADMINISTRATIVE and 
                    user_rank.level >= min_level):
                    return await func(message, *args, **kwargs)
                
                level_names = {
                    1: "مشرف مساعد",
                    2: "مشرف", 
                    3: "مشرف أول",
                    4: "نائب المالك",
                    5: "مالك"
                }
                
                required_name = level_names.get(min_level, f"مستوى {min_level}")
                await message.reply(f"❌ تحتاج رتبة {required_name} أو أعلى لاستخدام هذا الأمر")
                
            except Exception as e:
                logging.error(f"خطأ في فحص مستوى الرتبة: {e}")
                await message.reply("❌ حدث خطأ في التحقق من مستوى الرتبة")
        
        return wrapper
    return decorator


# Decorators مباشرة للصلاحيات الشائعة
def can_mute_users(func: Callable) -> Callable:
    """التحقق من صلاحية كتم المستخدمين"""
    return require_permission(Permission.MUTE_USERS)(func)


def can_kick_users(func: Callable) -> Callable:
    """التحقق من صلاحية طرد المستخدمين"""
    return require_permission(Permission.KICK_USERS)(func)


def can_ban_users(func: Callable) -> Callable:
    """التحقق من صلاحية حظر المستخدمين"""
    return require_permission(Permission.BAN_USERS)(func)


def can_delete_messages(func: Callable) -> Callable:
    """التحقق من صلاحية حذف الرسائل"""
    return require_permission(Permission.DELETE_MESSAGES)(func)


def can_manage_ranks(func: Callable) -> Callable:
    """التحقق من صلاحية إدارة الرتب"""
    return require_permission(Permission.MANAGE_RANKS)(func)


def can_access_admin_panel(func: Callable) -> Callable:
    """التحقق من صلاحية الوصول للوحة الإدارة"""
    return require_permission(Permission.ACCESS_ADMIN_PANEL)(func)


# Decorators للمستويات الإدارية
def assistant_moderator_required(func: Callable) -> Callable:
    """مشرف مساعد أو أعلى"""
    return rank_level_required(1)(func)


def moderator_required(func: Callable) -> Callable:
    """مشرف أو أعلى"""
    return rank_level_required(2)(func)


def senior_moderator_required(func: Callable) -> Callable:
    """مشرف أول أو أعلى"""
    return rank_level_required(3)(func)


def deputy_owner_required(func: Callable) -> Callable:
    """نائب المالك أو أعلى"""
    return rank_level_required(4)(func)


def owner_required(func: Callable) -> Callable:
    """مالك فقط"""
    return rank_level_required(5)(func)


async def check_user_permission(user_id: int, chat_id: int, permission: Permission) -> bool:
    """فحص صلاحية المستخدم (مساعد)"""
    try:
        if is_master(user_id):
            return True
        return rank_manager.user_has_permission(user_id, chat_id, permission)
    except Exception as e:
        logging.error(f"خطأ في فحص صلاحية المستخدم: {e}")
        return False


async def get_user_permissions_list(user_id: int, chat_id: int) -> List[str]:
    """الحصول على قائمة صلاحيات المستخدم"""
    try:
        permissions = []
        
        if is_master(user_id):
            permissions.append("🔴 صلاحيات Master مطلقة")
            return permissions
        
        user_rank = rank_manager.get_user_rank(user_id, chat_id)
        if user_rank:
            permissions.append(f"{user_rank.color} {user_rank.display_name}")
            
            if user_rank.rank_type == RankType.ADMINISTRATIVE:
                for permission in user_rank.permissions:
                    if permission == Permission.MUTE_USERS:
                        permissions.append("• كتم المستخدمين")
                    elif permission == Permission.KICK_USERS:
                        permissions.append("• طرد المستخدمين")
                    elif permission == Permission.BAN_USERS:
                        permissions.append("• حظر المستخدمين")
                    elif permission == Permission.DELETE_MESSAGES:
                        permissions.append("• حذف الرسائل")
                    elif permission == Permission.MANAGE_RANKS:
                        permissions.append("• إدارة الرتب")
                    elif permission == Permission.ACCESS_ADMIN_PANEL:
                        permissions.append("• الوصول للوحة الإدارة")
            else:
                permissions.append("• رتبة ترفيهية (بدون صلاحيات إدارية)")
        else:
            permissions.append("• عضو عادي (بدون صلاحيات)")
        
        return permissions
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على قائمة الصلاحيات: {e}")
        return ["❌ خطأ في جلب الصلاحيات"]
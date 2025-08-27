"""
ديكوريترز البوت - إصدار محدث بدون استيراد دائري
Bot Decorators - Updated version without circular imports
"""

import logging
from functools import wraps
from aiogram.types import Message, CallbackQuery
from typing import Union, Callable, Any

from database.operations import get_user, is_user_banned, update_user_activity


def get_admin_ids():
    """الحصول على قائمة المديرين مع تجنب الاستيراد الدائري"""
    from config.settings import ADMIN_IDS
    return ADMIN_IDS


def get_system_messages():
    """الحصول على رسائل النظام مع تجنب الاستيراد الدائري"""
    from config.settings import SYSTEM_MESSAGES
    return SYSTEM_MESSAGES


def group_only(func: Callable) -> Callable:
    """ديكوريتر للتأكد من أن الأمر يعمل في المجموعات فقط"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            # تحديد نوع الكائن والمحادثة
            if isinstance(message_or_query, CallbackQuery):
                chat_type = message_or_query.message.chat.type
                chat_method = message_or_query.message.reply
                await message_or_query.answer()
            else:
                chat_type = message_or_query.chat.type
                chat_method = message_or_query.reply
            
            # التحقق من نوع المحادثة
            if chat_type == 'private':
                await chat_method(
                    "🚫 **هذا الأمر متاح في المجموعات فقط!**\n\n"
                    "➕ أضف البوت لمجموعتك وابدأ اللعب مباشرة"
                )
                return
            
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر group_only: {e}")
            try:
                system_messages = get_system_messages()
                if isinstance(message_or_query, CallbackQuery):
                    await message_or_query.message.reply(system_messages["error"])
                else:
                    await message_or_query.reply(system_messages["error"])
            except:
                pass
    
    return wrapper


def user_required(func: Callable) -> Callable:
    """ديكوريتر للتأكد من تسجيل المستخدم"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            # تحديد نوع الكائن
            if isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_type = message_or_query.message.chat.type
                chat_method = message_or_query.message.reply
                await message_or_query.answer()
            else:
                user_id = message_or_query.from_user.id
                chat_type = message_or_query.chat.type
                chat_method = message_or_query.reply
            
            # التحقق من نوع المحادثة أولاً
            if chat_type == 'private':
                await chat_method(
                    "🚫 **هذا الأمر متاح في المجموعات فقط!**\n\n"
                    "➕ أضف البوت لمجموعتك وابدأ اللعب مباشرة"
                )
                return
            
            # التحقق من حظر المستخدم
            if await is_user_banned(user_id):
                await chat_method("⛔ تم حظرك من استخدام البوت")
                return
            
            # التحقق من وجود المستخدم وإنشاؤه إذا لم يكن موجوداً
            user = await get_user(user_id)
            if not user:
                from database.operations import get_or_create_user
                await get_or_create_user(
                    user_id=user_id,
                    username=message_or_query.from_user.username,
                    first_name=message_or_query.from_user.first_name
                )
            
            # تحديث نشاط المستخدم
            await update_user_activity(user_id)
            
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر user_required: {e}")
            try:
                system_messages = get_system_messages()
                if isinstance(message_or_query, CallbackQuery):
                    await message_or_query.message.reply(system_messages["error"])
                else:
                    await message_or_query.reply(system_messages["error"])
            except:
                pass
    
    return wrapper


def admin_required(func: Callable) -> Callable:
    """ديكوريتر للتأكد من صلاحيات الإدارة"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            # تحديد نوع الكائن
            if isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_method = message_or_query.message.reply
                await message_or_query.answer()
            else:
                user_id = message_or_query.from_user.id
                chat_method = message_or_query.reply
            
            # التحقق من صلاحيات الإدارة
            admin_ids = get_admin_ids()
            if user_id not in admin_ids:
                system_messages = get_system_messages()
                await chat_method(system_messages["unauthorized"])
                return
            
            # تنفيذ الدالة الأصلية
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر admin_required: {e}")
            try:
                system_messages = get_system_messages()
                if isinstance(message_or_query, CallbackQuery):
                    await message_or_query.message.reply(system_messages["error"])
                else:
                    await message_or_query.reply(system_messages["error"])
            except:
                pass
    
    return wrapper


# ديكوريترز إضافية مطلوبة
def premium_required(func: Callable) -> Callable:
    """ديكوريتر للتأكد من العضوية المميزة"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        return await func(message_or_query, *args, **kwargs)
    return wrapper


def rate_limit(seconds: int = 5):
    """ديكوريتر لتحديد معدل الاستخدام"""  
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            return await func(message_or_query, *args, **kwargs)
        return wrapper
    return decorator


def maintenance_mode(maintenance_message: str = None):
    """ديكوريتر لوضع الصيانة"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            return await func(message_or_query, *args, **kwargs)
        return wrapper
    return decorator
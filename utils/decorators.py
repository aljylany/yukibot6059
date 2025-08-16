"""
ديكوريترز البوت
Bot Decorators
"""

import logging
from functools import wraps
from aiogram.types import Message, CallbackQuery
from typing import Union, Callable, Any

from database.operations import get_user, is_user_banned, update_user_activity
from config.settings import ADMIN_IDS, SYSTEM_MESSAGES


def user_required(func: Callable) -> Callable:
    """ديكوريتر للتأكد من تسجيل المستخدم"""
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
            
            # التحقق من حظر المستخدم
            if await is_user_banned(user_id):
                await chat_method("⛔ تم حظرك من استخدام البوت")
                return
            
            # التحقق من تسجيل المستخدم
            user = await get_user(user_id)
            if not user:
                await chat_method(
                    "❌ يرجى التسجيل أولاً باستخدام /start\n\n"
                    "🎮 ابدأ رحلتك في عالم الألعاب الاقتصادية!"
                )
                return
            
            # تحديث نشاط المستخدم
            await update_user_activity(user_id)
            
            # تنفيذ الدالة الأصلية
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر user_required: {e}")
            try:
                if isinstance(message_or_query, CallbackQuery):
                    await message_or_query.message.reply(SYSTEM_MESSAGES["error"])
                else:
                    await message_or_query.reply(SYSTEM_MESSAGES["error"])
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
            if user_id not in ADMIN_IDS:
                await chat_method(SYSTEM_MESSAGES["unauthorized"])
                return
            
            # تنفيذ الدالة الأصلية
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر admin_required: {e}")
            try:
                if isinstance(message_or_query, CallbackQuery):
                    await message_or_query.message.reply(SYSTEM_MESSAGES["error"])
                else:
                    await message_or_query.reply(SYSTEM_MESSAGES["error"])
            except:
                pass
    
    return wrapper


def rate_limit(max_calls: int = 5, window_seconds: int = 60):
    """ديكوريتر لتحديد معدل الاستخدام"""
    def decorator(func: Callable) -> Callable:
        # قاموس لتتبع استخدام المستخدمين
        user_calls = {}
        
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                import time
                
                # تحديد المستخدم
                if isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.message.reply
                else:
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.reply
                
                current_time = time.time()
                
                # تنظيف السجلات القديمة
                if user_id in user_calls:
                    user_calls[user_id] = [
                        call_time for call_time in user_calls[user_id]
                        if current_time - call_time < window_seconds
                    ]
                else:
                    user_calls[user_id] = []
                
                # التحقق من تجاوز الحد المسموح
                if len(user_calls[user_id]) >= max_calls:
                    await chat_method(
                        f"⏰ لقد تجاوزت الحد المسموح من الاستخدام\n\n"
                        f"يمكنك المحاولة مرة أخرى خلال {window_seconds} ثانية"
                    )
                    return
                
                # إضافة الاستدعاء الحالي
                user_calls[user_id].append(current_time)
                
                # تنفيذ الدالة الأصلية
                return await func(message_or_query, *args, **kwargs)
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر rate_limit: {e}")
        
        return wrapper
    return decorator


def log_action(action_name: str):
    """ديكوريتر لتسجيل الإجراءات"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                # تحديد المستخدم
                if isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    username = message_or_query.from_user.username or "مجهول"
                else:
                    user_id = message_or_query.from_user.id
                    username = message_or_query.from_user.username or "مجهول"
                
                # تسجيل بداية الإجراء
                logging.info(f"المستخدم {username} ({user_id}) بدأ إجراء: {action_name}")
                
                # تنفيذ الدالة الأصلية
                result = await func(message_or_query, *args, **kwargs)
                
                # تسجيل نهاية الإجراء
                logging.info(f"المستخدم {username} ({user_id}) أنهى إجراء: {action_name}")
                
                return result
                
            except Exception as e:
                logging.error(f"خطأ في إجراء {action_name} للمستخدم {user_id}: {e}")
                raise
        
        return wrapper
    return decorator


def validate_input(validation_func: Callable[[str], bool], error_message: str = "❌ إدخال غير صحيح"):
    """ديكوريتر للتحقق من صحة الإدخال"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                # التحقق من أن الكائن رسالة (للتحقق من النص)
                if isinstance(message_or_query, Message) and message_or_query.text:
                    if not validation_func(message_or_query.text):
                        await message_or_query.reply(error_message)
                        return
                
                # تنفيذ الدالة الأصلية
                return await func(message_or_query, *args, **kwargs)
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر validate_input: {e}")
        
        return wrapper
    return decorator


def handle_errors(error_message: str = None):
    """ديكوريتر لمعالجة الأخطاء"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                return await func(message_or_query, *args, **kwargs)
            except Exception as e:
                logging.error(f"خطأ في {func.__name__}: {e}")
                
                try:
                    # إرسال رسالة خطأ للمستخدم
                    error_msg = error_message or SYSTEM_MESSAGES["error"]
                    
                    if isinstance(message_or_query, CallbackQuery):
                        await message_or_query.message.reply(error_msg)
                    else:
                        await message_or_query.reply(error_msg)
                except:
                    pass  # في حالة فشل إرسال رسالة الخطأ
        
        return wrapper
    return decorator


def maintenance_mode(maintenance_message: str = None):
    """ديكوريتر لوضع الصيانة"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                # التحقق من وضع الصيانة (يمكن قراءته من متغير البيئة أو قاعدة البيانات)
                import os
                is_maintenance = os.getenv("MAINTENANCE_MODE", "false").lower() == "true"
                
                if is_maintenance:
                    # السماح للمديرين بالمرور
                    if isinstance(message_or_query, CallbackQuery):
                        user_id = message_or_query.from_user.id
                        chat_method = message_or_query.message.reply
                    else:
                        user_id = message_or_query.from_user.id
                        chat_method = message_or_query.reply
                    
                    if user_id not in ADMIN_IDS:
                        msg = maintenance_message or SYSTEM_MESSAGES["maintenance"]
                        await chat_method(msg)
                        return
                
                # تنفيذ الدالة الأصلية
                return await func(message_or_query, *args, **kwargs)
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر maintenance_mode: {e}")
        
        return wrapper
    return decorator


def cache_result(cache_duration: int = 300):
    """ديكوريتر للتخزين المؤقت للنتائج"""
    def decorator(func: Callable) -> Callable:
        cache = {}
        
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                import time
                
                # تحديد مفتاح التخزين المؤقت
                if isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                else:
                    user_id = message_or_query.from_user.id
                
                cache_key = f"{func.__name__}_{user_id}"
                current_time = time.time()
                
                # التحقق من وجود نتيجة مخزنة صالحة
                if cache_key in cache:
                    cached_time, cached_result = cache[cache_key]
                    if current_time - cached_time < cache_duration:
                        return cached_result
                
                # تنفيذ الدالة وتخزين النتيجة
                result = await func(message_or_query, *args, **kwargs)
                cache[cache_key] = (current_time, result)
                
                return result
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر cache_result: {e}")
                return await func(message_or_query, *args, **kwargs)
        
        return wrapper
    return decorator


def typing_action(func: Callable) -> Callable:
    """ديكوريتر لإرسال إشارة الكتابة"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            # إرسال إشارة الكتابة
            if isinstance(message_or_query, CallbackQuery):
                chat_id = message_or_query.message.chat.id
                bot = message_or_query.bot
            else:
                chat_id = message_or_query.chat.id
                bot = message_or_query.bot
            
            await bot.send_chat_action(chat_id=chat_id, action="typing")
            
            # تنفيذ الدالة الأصلية
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر typing_action: {e}")
            return await func(message_or_query, *args, **kwargs)
    
    return wrapper


def premium_required(func: Callable) -> Callable:
    """ديكوريتر للتأكد من الاشتراك المميز"""
    @wraps(func)
    async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
        try:
            # تحديد المستخدم
            if isinstance(message_or_query, CallbackQuery):
                user_id = message_or_query.from_user.id
                chat_method = message_or_query.message.reply
            else:
                user_id = message_or_query.from_user.id
                chat_method = message_or_query.reply
            
            # التحقق من الاشتراك المميز (يمكن إضافة منطق التحقق هنا)
            # مؤقتاً نسمح للمديرين
            if user_id not in ADMIN_IDS:
                # يمكن إضافة فحص قاعدة البيانات للاشتراك المميز
                has_premium = False  # placeholder
                
                if not has_premium:
                    await chat_method(
                        "⭐ **هذه الميزة مخصصة للمشتركين المميزين فقط**\n\n"
                        "🎁 احصل على اشتراك مميز للوصول لجميع الميزات الحصرية!\n"
                        "استخدم /premium لمعرفة المزيد"
                    )
                    return
            
            # تنفيذ الدالة الأصلية
            return await func(message_or_query, *args, **kwargs)
            
        except Exception as e:
            logging.error(f"خطأ في ديكوريتر premium_required: {e}")
    
    return wrapper


def min_balance_required(min_amount: int):
    """ديكوريتر للتأكد من الحد الأدنى للرصيد"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                # تحديد المستخدم
                if isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.message.reply
                else:
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.reply
                
                # التحقق من الرصيد
                user = await get_user(user_id)
                if not user or user['balance'] < min_amount:
                    from utils.helpers import format_number
                    current_balance = user['balance'] if user else 0
                    
                    await chat_method(
                        f"💰 **رصيد غير كافٍ**\n\n"
                        f"💵 رصيدك الحالي: {format_number(current_balance)}$\n"
                        f"💳 المطلوب: {format_number(min_amount)}$\n"
                        f"💸 تحتاج إلى: {format_number(min_amount - current_balance)}$ إضافية"
                    )
                    return
                
                # تنفيذ الدالة الأصلية
                return await func(message_or_query, *args, **kwargs)
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر min_balance_required: {e}")
        
        return wrapper
    return decorator


def cooldown(seconds: int):
    """ديكوريتر للانتظار بين الاستخدامات"""
    def decorator(func: Callable) -> Callable:
        user_cooldowns = {}
        
        @wraps(func)
        async def wrapper(message_or_query: Union[Message, CallbackQuery], *args, **kwargs):
            try:
                import time
                
                # تحديد المستخدم
                if isinstance(message_or_query, CallbackQuery):
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.message.reply
                else:
                    user_id = message_or_query.from_user.id
                    chat_method = message_or_query.reply
                
                current_time = time.time()
                
                # التحقق من وقت الانتظار
                if user_id in user_cooldowns:
                    time_passed = current_time - user_cooldowns[user_id]
                    if time_passed < seconds:
                        remaining = seconds - time_passed
                        from utils.helpers import format_duration
                        
                        await chat_method(
                            f"⏰ **يرجى الانتظار**\n\n"
                            f"🕐 الوقت المتبقي: {format_duration(int(remaining))}"
                        )
                        return
                
                # تحديث وقت آخر استخدام
                user_cooldowns[user_id] = current_time
                
                # تنفيذ الدالة الأصلية
                return await func(message_or_query, *args, **kwargs)
                
            except Exception as e:
                logging.error(f"خطأ في ديكوريتر cooldown: {e}")
        
        return wrapper
    return decorator

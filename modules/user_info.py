"""
وحدة معلومات المستخدم
User Information Module
"""

import logging
from aiogram.types import Message
from database.operations import execute_query, get_user
from utils.helpers import format_number
from config.hierarchy import MASTERS


async def show_my_rank(message: Message):
    """عرض رتبة المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من رتبة السيد
        if user_id in MASTERS:
            await message.reply(
                "👑 **رتبتك:**\n\n"
                "🔥 السيد - صلاحيات مطلقة\n"
                "⚡ أعلى رتبة في النظام"
            )
            return
        
        # البحث عن الرتبة في قاعدة البيانات
        rank_info = await execute_query(
            "SELECT rank_type, promoted_at FROM group_ranks WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        if rank_info:
            rank_type = rank_info[0] if isinstance(rank_info, tuple) else rank_info.get('rank_type', '')
            promoted_at = rank_info[1] if isinstance(rank_info, tuple) else rank_info.get('promoted_at', '')
            
            # تحديد الرمز والوصف حسب الرتبة
            rank_emoji = {
                'مالك': '👑',
                'مالك اساسي': '👑',
                'مشرف': '🛡️',
                'ادمن': '⚡',
                'مميز': '⭐'
            }
            
            rank_description = {
                'مالك': 'مالك المجموعة - صلاحيات كاملة',
                'مالك اساسي': 'مالك أساسي - صلاحيات كاملة',
                'مشرف': 'مشرف - صلاحيات إدارية',
                'ادمن': 'أدمن - صلاحيات متوسطة',
                'مميز': 'عضو مميز - صلاحيات محدودة'
            }
            
            emoji = rank_emoji.get(rank_type, '🎖️')
            description = rank_description.get(rank_type, 'رتبة خاصة')
            date_str = promoted_at[:10] if promoted_at else 'غير محدد'
            
            await message.reply(
                f"{emoji} **رتبتك:**\n\n"
                f"📋 الرتبة: {rank_type}\n"
                f"📝 الوصف: {description}\n"
                f"📅 تاريخ الترقية: {date_str}"
            )
        else:
            await message.reply(
                "👤 **رتبتك:**\n\n"
                "📋 الرتبة: عضو عادي\n"
                "📝 الوصف: عضو في المجموعة\n"
                "💡 يمكن للمشرفين رفع رتبتك"
            )
    
    except Exception as e:
        logging.error(f"خطأ في عرض الرتبة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتبة")


async def show_my_balance(message: Message):
    """عرض رصيد المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        user = await get_user(user_id)
        
        if not user:
            await message.reply(
                "❌ **لم يتم العثور على حسابك**\n\n"
                "💡 استخدم الأوامر التالية لإنشاء حساب:\n"
                "• `حساب بنكي`\n"
                "• `انشاء حساب`"
            )
            return
        
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        total_earned = user.get('total_earned', 0) if isinstance(user, dict) else 0
        total_spent = user.get('total_spent', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        
        await message.reply(
            f"💰 **رصيدك المالي:**\n\n"
            f"💵 النقد: {format_number(balance)}$\n"
            f"🏦 البنك ({bank_type}): {format_number(bank_balance)}$\n"
            f"💎 المجموع: {format_number(balance + bank_balance)}$\n\n"
            f"📊 **الإحصائيات:**\n"
            f"📈 إجمالي الكسب: {format_number(total_earned)}$\n"
            f"📉 إجمالي الإنفاق: {format_number(total_spent)}$"
        )
    
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرصيد")


async def show_user_balance(message: Message):
    """عرض رصيد مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `فلوسه`\n\n"
                "💡 أو استخدم `فلوسي` لمعرفة رصيدك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        user = await get_user(target_user.id)
        
        if not user:
            target_name = target_user.first_name or "المستخدم"
            await message.reply(
                f"❌ **{target_name} ليس مسجل في النظام**\n\n"
                "💡 يحتاج لإنشاء حساب بنكي أولاً"
            )
            return
        
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        target_name = target_user.first_name or "المستخدم"
        
        await message.reply(
            f"💰 **رصيد {target_name}:**\n\n"
            f"💵 النقد: {format_number(balance)}$\n"
            f"🏦 البنك ({bank_type}): {format_number(bank_balance)}$\n"
            f"💎 المجموع: {format_number(balance + bank_balance)}$"
        )
    
    except Exception as e:
        logging.error(f"خطأ في عرض رصيد المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرصيد")


async def show_user_rank(message: Message):
    """عرض رتبة مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `رتبته`\n\n"
                "💡 أو استخدم `رتبتي` لمعرفة رتبتك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        user_id = target_user.id
        chat_id = message.chat.id
        target_name = target_user.first_name or "المستخدم"
        
        # التحقق من رتبة السيد
        if user_id in MASTERS:
            await message.reply(
                f"👑 **رتبة {target_name}:**\n\n"
                "🔥 السيد - صلاحيات مطلقة\n"
                "⚡ أعلى رتبة في النظام"
            )
            return
        
        # البحث عن الرتبة في قاعدة البيانات
        rank_info = await execute_query(
            "SELECT rank_type, promoted_at FROM group_ranks WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        if rank_info:
            rank_type = rank_info[0] if isinstance(rank_info, tuple) else rank_info.get('rank_type', '')
            promoted_at = rank_info[1] if isinstance(rank_info, tuple) else rank_info.get('promoted_at', '')
            
            # تحديد الرمز والوصف حسب الرتبة
            rank_emoji = {
                'مالك': '👑',
                'مالك اساسي': '👑',
                'مشرف': '🛡️',
                'ادمن': '⚡',
                'مميز': '⭐'
            }
            
            rank_description = {
                'مالك': 'مالك المجموعة - صلاحيات كاملة',
                'مالك اساسي': 'مالك أساسي - صلاحيات كاملة',
                'مشرف': 'مشرف - صلاحيات إدارية',
                'ادمن': 'أدمن - صلاحيات متوسطة',
                'مميز': 'عضو مميز - صلاحيات محدودة'
            }
            
            emoji = rank_emoji.get(rank_type, '🎖️')
            description = rank_description.get(rank_type, 'رتبة خاصة')
            date_str = promoted_at[:10] if promoted_at else 'غير محدد'
            
            await message.reply(
                f"{emoji} **رتبة {target_name}:**\n\n"
                f"📋 الرتبة: {rank_type}\n"
                f"📝 الوصف: {description}\n"
                f"📅 تاريخ الترقية: {date_str}"
            )
        else:
            await message.reply(
                f"👤 **رتبة {target_name}:**\n\n"
                "📋 الرتبة: عضو عادي\n"
                "📝 الوصف: عضو في المجموعة"
            )
    
    except Exception as e:
        logging.error(f"خطأ في عرض رتبة المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتبة")


async def show_user_level(message: Message):
    """عرض مستوى مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `مستواه`\n\n"
                "💡 أو استخدم `مستواي` لمعرفة مستواك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        target_name = target_user.first_name or "المستخدم"
        
        # استخدام نظام المستويات الجديد
        from modules.simple_level_display import get_user_level_info
        level_info = await get_user_level_info(target_user.id)
        
        if not level_info:
            await message.reply(
                f"❌ **{target_name} ليس مسجل في النظام**\n\n"
                "💡 يحتاج لإرسال رسالة أولاً لإنشاء حساب"
            )
            return
        
        await message.reply(level_info.replace("**مستواك:**", f"**مستوى {target_name}:**"))
    
    except Exception as e:
        logging.error(f"خطأ في عرض مستوى المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المستوى")


async def show_my_level(message: Message):
    """عرض مستوى المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        
        # استخدام نظام المستويات الجديد  
        from modules.simple_level_display import get_user_level_info
        level_info = await get_user_level_info(user_id)
        
        if not level_info:
            await message.reply(
                "❌ **لم يتم العثور على حسابك**\n\n"
                "💡 ارسل أي رسالة لإنشاء حساب جديد"
            )
            return
        
        await message.reply(level_info)
    
    except Exception as e:
        logging.error(f"خطأ في عرض المستوى: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المستوى")
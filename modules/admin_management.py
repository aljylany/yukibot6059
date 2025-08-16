"""
وحدة إدارة البوت المتكاملة
Comprehensive Bot Administration Module
"""

import logging
from datetime import datetime, timedelta
from aiogram.types import Message, ChatMember
from aiogram.fsm.context import FSMContext
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest

from database.operations import execute_query, get_user
from utils.decorators import admin_required, group_only
from utils.helpers import format_number, format_user_mention
from config.settings import ADMINS

# رتب الإدارة
ADMIN_RANKS = {
    "مالك اساسي": 9,
    "مالك": 8,
    "منشئ": 7,
    "مدير": 6,
    "ادمن": 5,
    "مشرف": 4,
    "مميز": 3
}

# أوامر الرفع والتنزيل
RANK_COMMANDS = {
    "رفع مالك اساسي": "مالك اساسي",
    "تنزيل مالك اساسي": "مالك اساسي",
    "رفع مالك": "مالك",
    "تنزيل مالك": "مالك",
    "رفع منشئ": "منشئ",
    "تنزيل منشئ": "منشئ",
    "رفع مدير": "مدير",
    "تنزيل مدير": "مدير",
    "رفع ادمن": "ادمن",
    "تنزيل ادمن": "ادمن",
    "رفع مشرف": "مشرف",
    "تنزيل مشرف": "مشرف",
    "رفع مميز": "مميز",
    "تنزيل مميز": "مميز"
}


async def handle_rank_promotion(message: Message, rank_type: str, action: str):
    """معالج رفع وتنزيل الرتب"""
    try:
        # التحقق من الصلاحيات
        if not await has_permission(message.from_user.id, message.chat.id, rank_type):
            await message.reply("❌ ليس لديك صلاحية لهذا الأمر")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        else:
            # استخراج المعرف من النص
            text_parts = message.text.split()
            if len(text_parts) > 2:
                username = text_parts[2].replace("@", "")
                # البحث عن المستخدم في قاعدة البيانات
                target_user = await get_user_by_username(username)

        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص أو كتابة معرفه")
            return

        if action == "رفع":
            success = await promote_user(target_user.id, rank_type, message.chat.id)
            if success:
                await message.reply(f"✅ تم رفع {format_user_mention(target_user)} إلى رتبة {rank_type}")
            else:
                await message.reply("❌ فشل في رفع المستخدم")
        else:
            success = await demote_user(target_user.id, rank_type, message.chat.id)
            if success:
                await message.reply(f"✅ تم تنزيل {format_user_mention(target_user)} من رتبة {rank_type}")
            else:
                await message.reply("❌ فشل في تنزيل المستخدم")

    except Exception as e:
        logging.error(f"خطأ في معالجة الرتب: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def handle_clear_ranks(message: Message, rank_type: str = None):
    """معالج مسح الرتب"""
    try:
        if not await has_permission(message.from_user.id, message.chat.id, "مالك"):
            await message.reply("❌ هذا الأمر للمالكين فقط")
            return

        if rank_type == "الكل":
            # مسح جميع الرتب
            await execute_query(
                "DELETE FROM group_ranks WHERE chat_id = ?",
                (message.chat.id,)
            )
            await message.reply("✅ تم مسح جميع الرتب من المجموعة")
        elif rank_type:
            # مسح رتبة محددة
            await execute_query(
                "DELETE FROM group_ranks WHERE chat_id = ? AND rank_type = ?",
                (message.chat.id, rank_type)
            )
            await message.reply(f"✅ تم مسح جميع {rank_type} من المجموعة")

    except Exception as e:
        logging.error(f"خطأ في مسح الرتب: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح الرتب")


async def handle_ban_user(message: Message):
    """معالج حظر المستخدم"""
    try:
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ ليس لديك صلاحية الحظر")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        else:
            text_parts = message.text.split()
            if len(text_parts) > 1:
                username = text_parts[1].replace("@", "")
                target_user = await get_user_by_username(username)

        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص أو كتابة معرفه")
            return

        # حظر المستخدم
        try:
            await message.bot.ban_chat_member(message.chat.id, target_user.id)
            
            # إضافة إلى قائمة المحظورين
            await execute_query(
                "INSERT OR REPLACE INTO banned_users (user_id, chat_id, banned_by, banned_at) VALUES (?, ?, ?, ?)",
                (target_user.id, message.chat.id, message.from_user.id, datetime.now().isoformat())
            )
            
            await message.reply(f"✅ تم حظر {format_user_mention(target_user)} من المجموعة")
            
        except TelegramBadRequest as e:
            await message.reply(f"❌ فشل في حظر المستخدم: {e}")

    except Exception as e:
        logging.error(f"خطأ في حظر المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء الحظر")


async def handle_kick_user(message: Message):
    """معالج طرد المستخدم"""
    try:
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ ليس لديك صلاحية الطرد")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        else:
            text_parts = message.text.split()
            if len(text_parts) > 1:
                username = text_parts[1].replace("@", "")
                target_user = await get_user_by_username(username)

        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص أو كتابة معرفه")
            return

        try:
            # طرد المستخدم
            await message.bot.ban_chat_member(message.chat.id, target_user.id)
            await message.bot.unban_chat_member(message.chat.id, target_user.id)
            
            await message.reply(f"✅ تم طرد {format_user_mention(target_user)} من المجموعة")
            
        except TelegramBadRequest as e:
            await message.reply(f"❌ فشل في طرد المستخدم: {e}")

    except Exception as e:
        logging.error(f"خطأ في طرد المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء الطرد")


async def handle_mute_user(message: Message):
    """معالج كتم المستخدم"""
    try:
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ ليس لديك صلاحية الكتم")
            return

        target_user = None
        duration = None
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            text_parts = message.text.split()
            if len(text_parts) > 1:
                duration = parse_duration(text_parts[1])
        else:
            text_parts = message.text.split()
            if len(text_parts) > 1:
                username = text_parts[1].replace("@", "")
                target_user = await get_user_by_username(username)
                if len(text_parts) > 2:
                    duration = parse_duration(text_parts[2])

        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص أو كتابة معرفه")
            return

        try:
            # كتم المستخدم
            until_date = None
            if duration:
                until_date = datetime.now() + timedelta(seconds=duration)
            
            await message.bot.restrict_chat_member(
                message.chat.id,
                target_user.id,
                permissions=message.chat.permissions,
                until_date=until_date
            )
            
            # إضافة إلى قائمة المكتومين
            await execute_query(
                "INSERT OR REPLACE INTO muted_users (user_id, chat_id, muted_by, muted_at, until_date) VALUES (?, ?, ?, ?, ?)",
                (target_user.id, message.chat.id, message.from_user.id, 
                 datetime.now().isoformat(), until_date.isoformat() if until_date else None)
            )
            
            duration_text = f" لمدة {format_duration(duration)}" if duration else " بشكل دائم"
            await message.reply(f"✅ تم كتم {format_user_mention(target_user)}{duration_text}")
            
        except TelegramBadRequest as e:
            await message.reply(f"❌ فشل في كتم المستخدم: {e}")

    except Exception as e:
        logging.error(f"خطأ في كتم المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء الكتم")


async def handle_warn_user(message: Message):
    """معالج تحذير المستخدم"""
    try:
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ ليس لديك صلاحية التحذير")
            return

        target_user = None
        warn_level = "اول"
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
            text_parts = message.text.split()
            if len(text_parts) > 1:
                warn_level = text_parts[1]
        
        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص")
            return

        # إضافة التحذير
        await execute_query(
            "INSERT INTO user_warnings (user_id, chat_id, warned_by, warn_level, warned_at) VALUES (?, ?, ?, ?, ?)",
            (target_user.id, message.chat.id, message.from_user.id, warn_level, datetime.now().isoformat())
        )
        
        # عد التحذيرات
        warnings_count = await execute_query(
            "SELECT COUNT(*) FROM user_warnings WHERE user_id = ? AND chat_id = ?",
            (target_user.id, message.chat.id),
            fetch_one=True
        )
        
        count = warnings_count[0] if warnings_count else 0
        
        await message.reply(
            f"⚠️ تحذير {warn_level} لـ {format_user_mention(target_user)}\n"
            f"📊 إجمالي التحذيرات: {count}/5\n"
            f"⚡ عند الوصول لـ 5 تحذيرات سيتم تقييده"
        )
        
        # تقييد تلقائي عند 5 تحذيرات
        if count >= 5:
            await handle_restrict_user_auto(message, target_user)

    except Exception as e:
        logging.error(f"خطأ في تحذير المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء التحذير")


async def show_group_ranks(message: Message, rank_type: str = None):
    """عرض قوائم الرتب"""
    try:
        if rank_type:
            # عرض رتبة محددة
            ranks = await execute_query(
                "SELECT user_id FROM group_ranks WHERE chat_id = ? AND rank_type = ?",
                (message.chat.id, rank_type),
                fetch_all=True
            )
        else:
            # عرض جميع الرتب
            ranks = await execute_query(
                "SELECT user_id, rank_type FROM group_ranks WHERE chat_id = ?",
                (message.chat.id,),
                fetch_all=True
            )

        if not ranks:
            await message.reply(f"📝 لا يوجد {rank_type if rank_type else 'رتب'} في المجموعة")
            return

        # تنسيق القائمة
        rank_text = f"👥 **قائمة {rank_type if rank_type else 'الرتب'}:**\n\n"
        
        for i, rank in enumerate(ranks, 1):
            user_id = rank['user_id'] if isinstance(rank, dict) else rank[0]
            user = await get_user(user_id)
            if user:
                user_mention = f"@{user['username']}" if user.get('username') else f"#{user_id}"
                if rank_type:
                    rank_text += f"{i}. {user_mention}\n"
                else:
                    rank_type_display = rank['rank_type'] if isinstance(rank, dict) else rank[1]
                    rank_text += f"{i}. {user_mention} - {rank_type_display}\n"

        await message.reply(rank_text)

    except Exception as e:
        logging.error(f"خطأ في عرض الرتب: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتب")


# دوال مساعدة
async def has_permission(user_id: int, chat_id: int, required_rank: str) -> bool:
    """التحقق من صلاحيات المستخدم"""
    try:
        # التحقق من الأدمن العام
        if user_id in ADMINS:
            return True
            
        # التحقق من رتبة المستخدم في المجموعة
        user_rank = await execute_query(
            "SELECT rank_type FROM group_ranks WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        if user_rank:
            user_rank_level = ADMIN_RANKS.get(user_rank[0], 0)
            required_rank_level = ADMIN_RANKS.get(required_rank, 0)
            return user_rank_level >= required_rank_level
            
        return False
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من الصلاحيات: {e}")
        return False


async def promote_user(user_id: int, rank_type: str, chat_id: int) -> bool:
    """رفع رتبة المستخدم"""
    try:
        await execute_query(
            "INSERT OR REPLACE INTO group_ranks (user_id, chat_id, rank_type, promoted_at) VALUES (?, ?, ?, ?)",
            (user_id, chat_id, rank_type, datetime.now().isoformat())
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في رفع الرتبة: {e}")
        return False


async def demote_user(user_id: int, rank_type: str, chat_id: int) -> bool:
    """تنزيل رتبة المستخدم"""
    try:
        await execute_query(
            "DELETE FROM group_ranks WHERE user_id = ? AND chat_id = ? AND rank_type = ?",
            (user_id, chat_id, rank_type)
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في تنزيل الرتبة: {e}")
        return False


async def get_user_by_username(username: str):
    """البحث عن مستخدم بالمعرف"""
    try:
        user = await execute_query(
            "SELECT * FROM users WHERE username = ?",
            (username,),
            fetch_one=True
        )
        return user
    except Exception as e:
        logging.error(f"خطأ في البحث عن المستخدم: {e}")
        return None


def parse_duration(duration_str: str) -> int:
    """تحليل مدة الوقت"""
    try:
        if duration_str.endswith('د'):
            return int(duration_str[:-1]) * 60
        elif duration_str.endswith('س'):
            return int(duration_str[:-1]) * 3600
        elif duration_str.endswith('ي'):
            return int(duration_str[:-1]) * 86400
        else:
            return int(duration_str) * 60  # افتراضي: دقائق
    except:
        return 300  # افتراضي: 5 دقائق


def format_duration(seconds: int) -> str:
    """تنسيق مدة الوقت"""
    if seconds < 60:
        return f"{seconds} ثانية"
    elif seconds < 3600:
        return f"{seconds // 60} دقيقة"
    elif seconds < 86400:
        return f"{seconds // 3600} ساعة"
    else:
        return f"{seconds // 86400} يوم"


async def handle_restrict_user_auto(message: Message, target_user):
    """تقييد تلقائي للمستخدم عند 5 تحذيرات"""
    try:
        await message.bot.restrict_chat_member(
            message.chat.id,
            target_user.id,
            permissions=message.chat.permissions
        )
        
        await message.reply(
            f"🔒 تم تقييد {format_user_mention(target_user)} تلقائياً\n"
            f"السبب: الوصول لـ 5 تحذيرات"
        )
        
    except Exception as e:
        logging.error(f"خطأ في التقييد التلقائي: {e}")
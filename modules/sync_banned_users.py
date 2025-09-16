"""
نظام مزامنة المحظورين
Banned Users Synchronization System
"""

import logging
import aiosqlite
from aiogram.types import Message, ChatMemberStatus
from aiogram.exceptions import TelegramBadRequest
from config.database import DATABASE_URL
from database.operations import execute_query
from utils.decorators import admin_required
from datetime import datetime


@admin_required
async def sync_banned_users(message: Message):
    """مزامنة قائمة المحظورين مع تليجرام"""
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.reply("❌ البوت يحتاج صلاحيات إدارية للمزامنة")
            return
        
        if not bot_member.can_restrict_members:
            await message.reply("❌ البوت لا يملك صلاحية إدارة الأعضاء")
            return

        # إرسال رسالة تحميل
        loading_msg = await message.reply("🔄 **جاري مزامنة قائمة المحظورين...**\n\n⏳ قد تستغرق هذه العملية بعض الوقت")
        
        # الحصول على قائمة المحظورين من قاعدة البيانات
        banned_users_db = await execute_query(
            "SELECT user_id, banned_at FROM banned_users WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not banned_users_db:
            await loading_msg.edit_text("📝 لا يوجد أعضاء محظورين في قاعدة البيانات للمزامنة")
            return
        
        # متغيرات الإحصائيات
        total_checked = 0
        removed_from_db = 0
        sync_errors = 0
        still_banned = 0
        
        # فحص كل مستخدم محظور في قاعدة البيانات
        for user_data in banned_users_db:
            user_id = user_data['user_id']
            total_checked += 1
            
            try:
                # فحص حالة المستخدم في تليجرام
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                
                # إذا كان المستخدم موجود وغير محظور في تليجرام
                if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    # إزالته من قاعدة بيانات البوت
                    await execute_query(
                        "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                        (user_id, message.chat.id)
                    )
                    removed_from_db += 1
                    logging.info(f"🔄 تم إزالة المستخدم {user_id} من قائمة المحظورين (مزامنة)")
                
                elif member.status == ChatMemberStatus.KICKED:
                    # لا يزال محظور في تليجرام، لا نحتاج لفعل شيء
                    still_banned += 1
                    
            except TelegramBadRequest as e:
                if "User not found" in str(e) or "user not found" in str(e).lower():
                    # المستخدم حذف حسابه أو غير موجود، إزالته من قاعدة البيانات
                    await execute_query(
                        "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                        (user_id, message.chat.id)
                    )
                    removed_from_db += 1
                    logging.info(f"🔄 تم إزالة المستخدم {user_id} من قائمة المحظورين (حساب محذوف)")
                else:
                    sync_errors += 1
                    logging.error(f"خطأ في فحص المستخدم {user_id}: {e}")
                    
            except Exception as e:
                sync_errors += 1
                logging.error(f"خطأ غير متوقع في فحص المستخدم {user_id}: {e}")
        
        # تحديث رسالة النتائج
        sync_report = f"""
✅ **تمت مزامنة قائمة المحظورين بنجاح!**

📊 **إحصائيات المزامنة:**
• إجمالي الفحوصات: {total_checked}
• تم إزالتهم من القائمة: {removed_from_db}
• لا يزالون محظورين: {still_banned}
• أخطاء الفحص: {sync_errors}

🔄 **تم في:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

💡 **ملاحظة:** المستخدمون الذين تم إزالتهم يدوياً من المجموعة أثناء إيقاف البوت تم تنظيفهم من القائمة تلقائياً.
        """
        
        await loading_msg.edit_text(sync_report)
        
        # إضافة سجل للعملية
        logging.info(f"تمت مزامنة قائمة المحظورين للمجموعة {message.chat.id}: فحص {total_checked}, أزال {removed_from_db}, أخطاء {sync_errors}")
        
    except Exception as e:
        logging.error(f"خطأ في مزامنة المحظورين: {e}")
        await message.reply("❌ حدث خطأ أثناء مزامنة قائمة المحظورين")


async def auto_check_user_ban_status(user_id: int, chat_id: int, bot) -> bool:
    """فحص تلقائي لحالة حظر المستخدم (للاستخدام الداخلي)"""
    try:
        # فحص حالة المستخدم في تليجرام
        member = await bot.get_chat_member(chat_id, user_id)
        
        # إذا كان غير محظور في تليجرام
        if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            # التحقق من وجوده في قاعدة بيانات المحظورين
            banned_in_db = await execute_query(
                "SELECT user_id FROM banned_users WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
                fetch_one=True
            )
            
            if banned_in_db:
                # إزالته من قاعدة البيانات
                await execute_query(
                    "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                    (user_id, chat_id)
                )
                logging.info(f"🔄 تم إزالة المستخدم {user_id} من قائمة المحظورين تلقائياً (مزامنة)")
                return False  # غير محظور
        
        elif member.status == ChatMemberStatus.KICKED:
            return True  # محظور
            
    except TelegramBadRequest as e:
        if "User not found" in str(e):
            # المستخدم حذف حسابه، إزالته من قاعدة البيانات
            await execute_query(
                "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            )
            logging.info(f"🔄 تم إزالة المستخدم {user_id} من قائمة المحظورين (حساب محذوف)")
            return False
    except Exception as e:
        logging.error(f"خطأ في الفحص التلقائي للمستخدم {user_id}: {e}")
    
    return False


@admin_required
async def force_sync_with_telegram(message: Message):
    """مزامنة قوية - فحص جميع المحظورين وتصحيح الاختلافات"""
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in [ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
            await message.reply("❌ البوت يحتاج صلاحيات إدارية للمزامنة القوية")
            return
        
        if not bot_member.can_restrict_members:
            await message.reply("❌ البوت لا يملك صلاحية إدارة الأعضاء")
            return

        loading_msg = await message.reply("🔧 **جاري المزامنة القوية...**\n\n⚠️ هذه العملية ستتحقق من جميع المحظورين وتصحح أي اختلافات")
        
        # الحصول على قائمة المحظورين من قاعدة البيانات
        banned_users_db = await execute_query(
            "SELECT user_id, banned_at, banned_by FROM banned_users WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not banned_users_db:
            await loading_msg.edit_text("📝 لا يوجد أعضاء محظورين في قاعدة البيانات")
            return
        
        corrected_bans = 0
        removed_entries = 0
        confirmed_bans = 0
        errors = 0
        
        for user_data in banned_users_db:
            user_id = user_data['user_id']
            
            try:
                # فحص حالة المستخدم الفعلية في تليجرام
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                
                if member.status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.CREATOR]:
                    # المستخدم غير محظور في تليجرام لكن موجود في قاعدة البيانات
                    # خيار 1: حظره في تليجرام (إذا كان البوت يريد فرض قاعدة بياناته)
                    # خيار 2: إزالته من قاعدة البيانات (إذا كان تليجرام هو المرجع)
                    
                    # سنختار الخيار 2 - إزالة من قاعدة البيانات لأن المشرف أزاله يدوياً
                    await execute_query(
                        "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                        (user_id, message.chat.id)
                    )
                    removed_entries += 1
                    logging.info(f"🔄 تم إزالة {user_id} من قاعدة البيانات (غير محظور في تليجرام)")
                    
                elif member.status == ChatMemberStatus.KICKED:
                    # محظور في كلا المكانين - لا حاجة لفعل شيء
                    confirmed_bans += 1
                    
            except TelegramBadRequest as e:
                if "User not found" in str(e):
                    # المستخدم حذف حسابه
                    await execute_query(
                        "DELETE FROM banned_users WHERE user_id = ? AND chat_id = ?",
                        (user_id, message.chat.id)
                    )
                    removed_entries += 1
                    logging.info(f"🔄 تم إزالة {user_id} من قاعدة البيانات (حساب محذوف)")
                else:
                    errors += 1
                    logging.error(f"خطأ TelegramBadRequest مع المستخدم {user_id}: {e}")
                    
            except Exception as e:
                errors += 1
                logging.error(f"خطأ في المزامنة القوية للمستخدم {user_id}: {e}")
        
        # تقرير النتائج
        sync_report = f"""
🔧 **تمت المزامنة القوية بنجاح!**

📊 **النتائج:**
• إجمالي الفحوصات: {len(banned_users_db)}
• تم تأكيد حظرهم: {confirmed_bans}
• تم إزالتهم من القائمة: {removed_entries}
• عمليات تصحيح: {corrected_bans}
• أخطاء: {errors}

✅ **الآن قائمة المحظورين متزامنة تماماً مع تليجرام**

🕐 **تمت في:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
        """
        
        await loading_msg.edit_text(sync_report)
        
    except Exception as e:
        logging.error(f"خطأ في المزامنة القوية: {e}")
        await message.reply("❌ حدث خطأ أثناء المزامنة القوية")


async def periodic_sync_check(chat_id: int, bot):
    """فحص دوري للمزامنة (يمكن استدعاؤه تلقائياً)"""
    try:
        # الحصول على عينة من المحظورين للفحص السريع
        banned_sample = await execute_query(
            "SELECT user_id FROM banned_users WHERE chat_id = ? LIMIT 10",
            (chat_id,),
            fetch_all=True
        )
        
        if not banned_sample:
            return
        
        for user_data in banned_sample:
            user_id = user_data['user_id']
            await auto_check_user_ban_status(user_id, chat_id, bot)
            
    except Exception as e:
        logging.error(f"خطأ في الفحص الدوري للمزامنة: {e}")
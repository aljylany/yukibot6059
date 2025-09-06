"""
وحدة إعدادات المجموعة
Group Settings Module
"""

import logging
from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import execute_query
from utils.decorators import admin_required, group_only
from config.settings import SYSTEM_MESSAGES
from config.hierarchy import has_telegram_permission, AdminLevel

# إعدادات القفل والفتح
LOCK_SETTINGS = {
    "الكتابه": "writing",
    "التعديل": "edit",
    "الفيديو": "video",
    "الصور": "photos",
    "الصوت": "audio",
    "الملصقات": "stickers",
    "الملصقات المميزه": "premium_stickers",
    "المتحركه": "gifs",
    "الدردشه": "chat",
    "الروابط": "links",
    "التاك": "hashtags",
    "البوتات": "bots",
    "المعرفات": "mentions",
    "الكاليش": "long_messages",
    "التوجيه": "forwarding",
    "الانلاين": "inline",
    "الجهات": "contacts"
}

# إعدادات التفعيل والتعطيل
TOGGLE_SETTINGS = {
    "ضافني": "who_added_me",
    "الاذكار": "azkar",
    "الثنائي": "daily_quote",
    "افتاري": "avatar_command",
    "التسليه": "entertainment",
    "الكت": "quote_tweets",
    "الترحيب": "welcome",
    "الردود": "replies",
    "الايدي": "id_command",
    "الرابط": "link_command",
    "اطردني": "kick_me",
    "الحظر": "ban_command",
    "الرفع": "promote_command",
    "التنزيل": "demote_command",
    "التحويل": "transfer_command",
    "المنشن": "mention_all",
    "وضع الاقتباسات": "quotes_mode",
    "الايدي بالصوره": "id_with_photo",
    "التحقق": "verification",
    "التحميل": "download"
}


async def handle_lock_command(message: Message, setting: str, action: str):
    """معالج أوامر القفل والفتح"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        setting_key = LOCK_SETTINGS.get(setting)
        if not setting_key:
            # لا نرد بإعداد غير صحيح هنا، نترك الأمر يمر للمعالجات الأخرى
            return

        # تطبيق الإعداد
        is_locked = action == "قفل"
        
        await execute_query(
            "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
            (message.chat.id, f"lock_{setting_key}", str(is_locked), datetime.now().isoformat())
        )

        action_text = "قفل" if is_locked else "فتح"
        await message.reply(f"✅ تم {action_text} {setting} في المجموعة")

        # إضافة سجل للعملية
        await execute_query(
            "INSERT INTO admin_actions (user_id, chat_id, action_type, target, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (message.from_user.id, message.chat.id, f"{action_text}_setting", setting, 
             f"{action_text} إعداد {setting}", datetime.now().isoformat())
        )

    except Exception as e:
        logging.error(f"خطأ في {action} الإعداد: {e}")
        await message.reply("❌ حدث خطأ أثناء تطبيق الإعداد")


async def handle_toggle_command(message: Message, setting: str, action: str):
    """معالج أوامر التفعيل والتعطيل"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        setting_key = TOGGLE_SETTINGS.get(setting)
        if not setting_key:
            # لا نرد بإعداد غير صحيح هنا، نترك الأمر يمر للمعالجات الأخرى
            return

        # معالجة خاصة لإعداد التحميل
        if setting_key == "download":
            from modules.media_download import toggle_download
            await toggle_download(message, action == "تفعيل")
            return

        # تطبيق الإعداد العام
        is_enabled = action == "تفعيل"
        
        await execute_query(
            "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
            (message.chat.id, f"enable_{setting_key}", str(is_enabled), datetime.now().isoformat())
        )

        action_text = "تفعيل" if is_enabled else "تعطيل"
        await message.reply(f"✅ تم {action_text} {setting} في المجموعة")

        # إضافة سجل للعملية
        await execute_query(
            "INSERT INTO admin_actions (user_id, chat_id, action_type, target, details, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            (message.from_user.id, message.chat.id, f"{action_text}_feature", setting, 
             f"{action_text} ميزة {setting}", datetime.now().isoformat())
        )

    except Exception as e:
        logging.error(f"خطأ في {action} الميزة: {e}")
        await message.reply("❌ حدث خطأ أثناء تطبيق الإعداد")


async def show_group_settings(message: Message):
    """عرض إعدادات المجموعة"""
    try:
        settings = await execute_query(
            "SELECT setting_key, setting_value FROM group_settings WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )

        if not settings:
            await message.reply("📋 لا توجد إعدادات مخصصة للمجموعة")
            return

        settings_text = "⚙️ **إعدادات المجموعة:**\n\n"
        
        # تجميع الإعدادات حسب النوع
        lock_settings = []
        enable_settings = []
        
        for setting in settings:
            key = setting['setting_key'] if isinstance(setting, dict) else setting[0]
            value = setting['setting_value'] if isinstance(setting, dict) else setting[1]
            
            if key.startswith('lock_'):
                setting_name = key.replace('lock_', '')
                status = "🔒 مقفل" if value == "True" else "🔓 مفتوح"
                lock_settings.append(f"• {setting_name}: {status}")
            elif key.startswith('enable_'):
                setting_name = key.replace('enable_', '')
                status = "✅ مفعل" if value == "True" else "❌ معطل"
                enable_settings.append(f"• {setting_name}: {status}")

        if lock_settings:
            settings_text += "🔐 **إعدادات القفل:**\n"
            settings_text += "\n".join(lock_settings) + "\n\n"
        
        if enable_settings:
            settings_text += "🎛 **إعدادات التفعيل:**\n"
            settings_text += "\n".join(enable_settings)

        await message.reply(settings_text)

    except Exception as e:
        logging.error(f"خطأ في عرض الإعدادات: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الإعدادات")


async def handle_delete_messages(message: Message, count: int = 1):
    """معالج حذف الرسائل"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        if count > 100:
            await message.reply("❌ لا يمكن حذف أكثر من 100 رسالة في المرة الواحدة")
            return

        deleted_count = 0
        current_message_id = message.message_id

        # حذف الرسائل
        if message.bot:
            for i in range(count):
                try:
                    await message.bot.delete_message(message.chat.id, current_message_id - i)
                    deleted_count += 1
                except:
                    continue

        # حذف رسالة الأمر نفسها
        try:
            await message.delete()
        except:
            pass

        # إرسال تأكيد مؤقت
        confirm_msg = await message.answer(f"✅ تم حذف {deleted_count} رسالة")
        
        # حذف رسالة التأكيد بعد 3 ثواني
        import asyncio
        await asyncio.sleep(3)
        try:
            await confirm_msg.delete()
        except:
            pass

    except Exception as e:
        logging.error(f"خطأ في حذف الرسائل: {e}")
        await message.reply("❌ حدث خطأ أثناء حذف الرسائل")


async def set_group_welcome(message: Message, welcome_text: str):
    """تعيين رسالة الترحيب"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        await execute_query(
            "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
            (message.chat.id, "welcome_message", welcome_text, datetime.now().isoformat())
        )

        await message.reply("✅ تم تعيين رسالة الترحيب بنجاح")

    except Exception as e:
        logging.error(f"خطأ في تعيين الترحيب: {e}")
        await message.reply("❌ حدث خطأ أثناء تعيين الترحيب")


async def set_group_rules(message: Message, rules_text: str):
    """تعيين قوانين المجموعة"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        await execute_query(
            "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
            (message.chat.id, "group_rules", rules_text, datetime.now().isoformat())
        )

        await message.reply("✅ تم تعيين قوانين المجموعة بنجاح")

    except Exception as e:
        logging.error(f"خطأ في تعيين القوانين: {e}")
        await message.reply("❌ حدث خطأ أثناء تعيين القوانين")


async def show_group_rules(message: Message):
    """عرض قوانين المجموعة"""
    try:
        rules = await execute_query(
            "SELECT setting_value FROM group_settings WHERE chat_id = ? AND setting_key = 'group_rules'",
            (message.chat.id,),
            fetch_one=True
        )

        if not rules:
            await message.reply("📜 لم يتم تعيين قوانين للمجموعة بعد")
            return

        if isinstance(rules, tuple):
            rules_text = rules[0]
        elif isinstance(rules, dict):
            rules_text = rules.get('setting_value', '')
        else:
            rules_text = str(rules)
        await message.reply(f"📜 **قوانين المجموعة:**\n\n{rules_text}")

    except Exception as e:
        logging.error(f"خطأ في عرض القوانين: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض القوانين")


async def handle_forbidden_word(message: Message, word: str, action: str):
    """معالج إضافة/إزالة الكلمات المحظورة"""
    try:
        if not message.bot or not await has_telegram_permission(message.bot, message.from_user.id, AdminLevel.MODERATOR, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        if action == "منع":
            # إضافة كلمة محظورة
            await execute_query(
                "INSERT INTO forbidden_words (chat_id, word, added_by, added_at) VALUES (?, ?, ?, ?)",
                (message.chat.id, word.lower(), message.from_user.id, datetime.now().isoformat())
            )
            await message.reply(f"✅ تم منع كلمة '{word}' في المجموعة")
        
        elif action == "الغاء منع":
            # إزالة كلمة محظورة
            await execute_query(
                "DELETE FROM forbidden_words WHERE chat_id = ? AND word = ?",
                (message.chat.id, word.lower())
            )
            await message.reply(f"✅ تم إلغاء منع كلمة '{word}' في المجموعة")

    except Exception as e:
        logging.error(f"خطأ في معالجة الكلمة المحظورة: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الكلمة")


async def show_group_info(message: Message):
    """عرض معلومات المجموعة"""
    try:
        chat = message.chat
        
        # إحصائيات المجموعة
        members_count = 0
        if message.bot:
            try:
                members_count = await message.bot.get_chat_member_count(chat.id)
            except Exception:
                members_count = 0
        
        # عدد الإدارة
        admins_count = await execute_query(
            "SELECT COUNT(*) FROM group_ranks WHERE chat_id = ?",
            (chat.id,),
            fetch_one=True
        )
        
        if isinstance(admins_count, tuple):
            admin_count = admins_count[0] if admins_count else 0
        elif isinstance(admins_count, dict):
            admin_count = admins_count.get('COUNT(*)', 0)
        else:
            admin_count = admins_count or 0
        
        # معلومات أساسية
        info_text = f"""
🏷 **معلومات المجموعة:**

📝 الاسم: {chat.title}
🆔 المعرف: {chat.id}
👥 عدد الأعضاء: {members_count}
👨‍💼 عدد الإدارة: {admin_count}
🔗 نوع المجموعة: {"خاصة" if chat.type == "supergroup" else "عامة"}
📅 تاريخ الإنشاء: {datetime.now().strftime("%Y-%m-%d")}

⚙️ لعرض الإعدادات: /الاعدادات
📋 لعرض القوانين: /القوانين
"""
        
        await message.reply(info_text)

    except Exception as e:
        logging.error(f"خطأ في عرض معلومات المجموعة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المعلومات")


# دوال مساعدة
# استيراد has_admin_permission من entertainment module
from modules.entertainment import has_admin_permission


async def get_setting_value(chat_id: int, setting_key: str, default_value: str = "False") -> str:
    """الحصول على قيمة إعداد معين"""
    try:
        setting = await execute_query(
            "SELECT setting_value FROM group_settings WHERE chat_id = ? AND setting_key = ?",
            (chat_id, setting_key),
            fetch_one=True
        )
        
        if setting:
            if isinstance(setting, tuple):
                return setting[0]
            elif isinstance(setting, dict):
                return setting.get('setting_value', default_value)
            else:
                return str(setting)
        return default_value
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على الإعداد: {e}")
        return default_value


async def is_setting_enabled(chat_id: int, setting_key: str) -> bool:
    """التحقق من تفعيل إعداد معين"""
    try:
        value = await get_setting_value(chat_id, setting_key, "False")
        return value.lower() == "true"
    except:
        return False
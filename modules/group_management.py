"""
وحدة إدارة المجموعة - أوامر الرؤية والحماية
Group Management Module - Viewing and Protection Commands
"""

import logging
from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram import html

from database.operations import execute_query, get_user
from utils.helpers import format_number, format_user_mention, format_user_id
from utils.decorators import group_only, admin_required
from config.hierarchy import get_user_rank, HIERARCHY_LEVELS
from config.settings import GROUP_SETTINGS


# أوامر رؤية الأعضاء والإعدادات
@group_only
async def show_group_link(message: Message):
    """عرض رابط المجموعة"""
    try:
        chat = message.chat
        
        if chat.type == "supergroup" and chat.username:
            link = f"https://t.me/{chat.username}"
            await message.reply(f"🔗 **رابط المجموعة:**\n{link}")
        elif chat.type == "supergroup":
            # محاولة الحصول على رابط دعوة
            try:
                bot = message.bot
                invite_link = await bot.export_chat_invite_link(chat.id)
                await message.reply(f"🔗 **رابط دعوة المجموعة:**\n{invite_link}")
            except Exception:
                await message.reply("❌ لا يمكن الحصول على رابط المجموعة. تأكد من أن البوت لديه صلاحيات الإدارة.")
        else:
            await message.reply("❌ هذا الأمر يعمل فقط في المجموعات الفائقة")
            
    except Exception as e:
        logging.error(f"خطأ في عرض رابط المجموعة: {e}")
        await message.reply("❌ حدث خطأ في عرض رابط المجموعة")


@group_only
async def show_owners(message: Message):
    """عرض قائمة المالكين الأساسيين"""
    try:
        from config.hierarchy import hierarchy_data
        
        owners = hierarchy_data.get(message.chat.id, {}).get('basic_owners', [])
        
        if not owners:
            await message.reply("📋 **المالكين الأساسيين:**\nلا يوجد مالكين أساسيين حالياً")
            return
        
        owners_list = []
        for user_id in owners:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                owners_list.append(f"👑 {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                owners_list.append(f"👑 مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **المالكين الأساسيين:** ({len(owners)})\n\n" + "\n".join(owners_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المالكين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المالكين")


@group_only
async def show_group_owners(message: Message):
    """عرض قائمة المالكين"""
    try:
        from config.hierarchy import hierarchy_data
        
        owners = hierarchy_data.get(message.chat.id, {}).get('owners', [])
        
        if not owners:
            await message.reply("📋 **المالكين:**\nلا يوجد مالكين حالياً")
            return
        
        owners_list = []
        for user_id in owners:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                owners_list.append(f"👑 {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                owners_list.append(f"👑 مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **المالكين:** ({len(owners)})\n\n" + "\n".join(owners_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المالكين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المالكين")


@group_only
async def show_creators(message: Message):
    """عرض قائمة المنشئين"""
    try:
        from config.hierarchy import hierarchy_data
        
        creators = hierarchy_data.get(message.chat.id, {}).get('creators', [])
        
        if not creators:
            await message.reply("📋 **المنشئين:**\nلا يوجد منشئين حالياً")
            return
        
        creators_list = []
        for user_id in creators:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                creators_list.append(f"⭐ {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                creators_list.append(f"⭐ مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **المنشئين:** ({len(creators)})\n\n" + "\n".join(creators_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المنشئين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المنشئين")


@group_only
async def show_managers(message: Message):
    """عرض قائمة المدراء"""
    try:
        from config.hierarchy import hierarchy_data
        
        managers = hierarchy_data.get(message.chat.id, {}).get('managers', [])
        
        if not managers:
            await message.reply("📋 **المدراء:**\nلا يوجد مدراء حالياً")
            return
        
        managers_list = []
        for user_id in managers:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                managers_list.append(f"🔰 {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                managers_list.append(f"🔰 مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **المدراء:** ({len(managers)})\n\n" + "\n".join(managers_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المدراء: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المدراء")


@group_only
async def show_admins(message: Message):
    """عرض قائمة الإدمنية"""
    try:
        from config.hierarchy import hierarchy_data
        
        admins = hierarchy_data.get(message.chat.id, {}).get('admins', [])
        
        if not admins:
            await message.reply("📋 **الإدمنية:**\nلا يوجد إدمنية حالياً")
            return
        
        admins_list = []
        for user_id in admins:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                admins_list.append(f"🛡 {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                admins_list.append(f"🛡 مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **الإدمنية:** ({len(admins)})\n\n" + "\n".join(admins_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الإدمنية: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الإدمنية")


@group_only
async def show_vips(message: Message):
    """عرض قائمة المميزين"""
    try:
        from config.hierarchy import hierarchy_data
        
        vips = hierarchy_data.get(message.chat.id, {}).get('vips', [])
        
        if not vips:
            await message.reply("📋 **المميزين:**\nلا يوجد مميزين حالياً")
            return
        
        vips_list = []
        for user_id in vips:
            try:
                member = await message.bot.get_chat_member(message.chat.id, user_id)
                user_info = member.user
                vips_list.append(f"💎 {format_user_mention(user_info)} - {format_user_id(user_id)}")
            except Exception:
                vips_list.append(f"💎 مستخدم محذوف - {format_user_id(user_id)}")
        
        text = f"📋 **المميزين:** ({len(vips)})\n\n" + "\n".join(vips_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المميزين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المميزين")


@group_only
async def show_banned_users(message: Message):
    """عرض قائمة المحظورين"""
    try:
        query = """
        SELECT user_id, username, first_name, banned_at, reason 
        FROM banned_users 
        WHERE chat_id = ? AND is_active = 1
        ORDER BY banned_at DESC
        """
        
        banned_users = await execute_query(query, (message.chat.id,), fetch_all=True)
        
        if not banned_users:
            await message.reply("📋 **المحظورين:**\nلا يوجد أعضاء محظورين حالياً")
            return
        
        banned_list = []
        for user in banned_users:
            username = f"@{user['username']}" if user['username'] else "بدون معرف"
            name = user['first_name'] or "مجهول"
            reason = user['reason'] or "غير محدد"
            banned_list.append(f"🚫 {name} ({username}) - {format_user_id(user['user_id'])}\n   السبب: {reason}")
        
        text = f"📋 **المحظورين:** ({len(banned_users)})\n\n" + "\n\n".join(banned_list)
        await message.reply(text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المحظورين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المحظورين")


@group_only
async def show_muted_users(message: Message):
    """عرض قائمة المكتومين"""
    try:
        # يمكن إضافة جدول للمكتومين أو استخدام الحالة من Telegram
        await message.reply("📋 **المكتومين:**\nهذه الميزة قيد التطوير")
        
    except Exception as e:
        logging.error(f"خطأ في عرض المكتومين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المكتومين")


@group_only
async def show_my_info(message: Message):
    """عرض معلومات المستخدم"""
    try:
        user = message.from_user
        member = await message.bot.get_chat_member(message.chat.id, user.id)
        user_rank = get_user_rank(user.id, message.chat.id)
        
        # الحصول على بيانات البوت
        bot_user = await get_user(user.id)
        
        info_text = f"""
🆔 **معلوماتي:**

👤 **المعلومات الأساسية:**
• الاسم: {html.escape(user.first_name or 'غير محدد')}
• المعرف: @{user.username or 'غير متوفر'}
• الآيدي: `{user.id}`

🏆 **في المجموعة:**
• الرتبة: {user_rank}
• حالة العضوية: {member.status}

💰 **المعلومات المالية:**
• الرصيد النقدي: {format_number(bot_user['balance']) if bot_user else '0'}$
• رصيد البنك: {format_number(bot_user['bank_balance']) if bot_user else '0'}$

🛡 **الأمان:**
• مستوى الأمان: {bot_user['security_level'] if bot_user else 1}
        """
        
        await message.reply(info_text.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات المستخدم: {e}")
        await message.reply("❌ حدث خطأ في عرض معلوماتك")


@group_only
async def show_group_protection(message: Message):
    """عرض حالة حماية المجموعة"""
    try:
        text = """
🛡 **حماية المجموعة:**

🔐 **أوامر القفل المتاحة:**
• قفل/فتح الصور - منع إرسال الصور
• قفل/فتح الفيديو - منع إرسال الفيديوهات
• قفل/فتح الصوت - منع إرسال التسجيلات الصوتية
• قفل/فتح الملصقات - منع إرسال الملصقات
• قفل/فتح المتحركه - منع إرسال GIF
• قفل/فتح الروابط - منع إرسال الروابط
• قفل/فتح التوجيه - منع إعادة توجيه الرسائل
• قفل/فتح الكتابه - منع الكتابة نهائياً
• قفل/فتح الكل - قفل جميع أنواع الرسائل

⚙️ **أوامر التفعيل/التعطيل:**
• تفعيل/تعطيل الترحيب
• تفعيل/تعطيل الردود
• تفعيل/تعطيل التسليه
• تفعيل/تعطيل الحماية

📝 **ملاحظة:** استخدم الأوامر بالكتابة المباشرة
مثال: "قفل الصور" أو "فتح الفيديو"
        """
        
        await message.reply(text.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض حماية المجموعة: {e}")
        await message.reply("❌ حدث خطأ في عرض حماية المجموعة")


@group_only
async def show_group_settings(message: Message):
    """عرض إعدادات المجموعة"""
    try:
        chat = message.chat
        
        settings_text = f"""
⚙️ **إعدادات المجموعة:**

📋 **معلومات المجموعة:**
• الاسم: {html.escape(chat.title or 'غير محدد')}
• النوع: {chat.type}
• العدد التقريبي: {getattr(chat, 'member_count', 'غير معروف')}

🔗 **الروابط:**
• المعرف: @{chat.username or 'غير متوفر'}

🛡 **الحماية:**
• حالة البوت: نشط ✅
• نظام الرتب: مفعل ✅
• النظام المصرفي: مفعل ✅

📊 **الإحصائيات:**
• تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d')}
• حالة التسجيل: مفعل

💡 **ملاحظة:** لعرض تفاصيل أكثر استخدم الأوامر المتخصصة
        """
        
        await message.reply(settings_text.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض إعدادات المجموعة: {e}")
        await message.reply("❌ حدث خطأ في عرض إعدادات المجموعة")


@group_only
async def show_group_info(message: Message):
    """عرض معلومات المجموعة التفصيلية"""
    try:
        chat = message.chat
        member_count = await message.bot.get_chat_member_count(chat.id)
        
        # إحصائيات الرتب
        from config.hierarchy import hierarchy_data
        group_hierarchy = hierarchy_data.get(chat.id, {})
        
        total_ranks = (
            len(group_hierarchy.get('basic_owners', [])) +
            len(group_hierarchy.get('owners', [])) +
            len(group_hierarchy.get('creators', [])) +
            len(group_hierarchy.get('managers', [])) +
            len(group_hierarchy.get('admins', [])) +
            len(group_hierarchy.get('vips', []))
        )
        
        info_text = f"""
📊 **معلومات المجموعة الكاملة:**

📋 **التفاصيل الأساسية:**
• الاسم: {html.escape(chat.title or 'غير محدد')}
• المعرف: @{chat.username or 'غير متوفر'}
• النوع: {chat.type}
• الآيدي: `{chat.id}`

👥 **الأعضاء:**
• العدد الإجمالي: {member_count}
• أصحاب الرتب: {total_ranks}
• الأعضاء العاديين: {member_count - total_ranks}

🏆 **الرتب الإدارية:**
• المالكين الأساسيين: {len(group_hierarchy.get('basic_owners', []))}
• المالكين: {len(group_hierarchy.get('owners', []))}
• المنشئين: {len(group_hierarchy.get('creators', []))}
• المدراء: {len(group_hierarchy.get('managers', []))}
• الإدمنية: {len(group_hierarchy.get('admins', []))}
• المميزين: {len(group_hierarchy.get('vips', []))}

⚙️ **حالة النظام:**
• البوت: نشط ✅
• قاعدة البيانات: متصلة ✅
• نظام الرتب: مفعل ✅
• النظام الاقتصادي: مفعل ✅
        """
        
        await message.reply(info_text.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات المجموعة: {e}")
        await message.reply("❌ حدث خطأ في عرض معلومات المجموعة")
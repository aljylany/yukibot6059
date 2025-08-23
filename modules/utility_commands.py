"""
أوامر مساعدة وأدوات عامة
Utility Commands and General Tools
"""

import logging
from aiogram.types import Message
from config.hierarchy import get_user_admin_level, get_admin_level_name, MASTERS


async def check_bot_permissions(message: Message):
    """فحص صلاحيات البوت في المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        bot_id = message.bot.id
        chat_id = message.chat.id
        
        # الحصول على معلومات البوت في المجموعة
        bot_member = await message.bot.get_chat_member(chat_id, bot_id)
        
        permissions_text = "🤖 **صلاحيات البوت في المجموعة**\n\n"
        permissions_text += f"📊 **النوع:** {bot_member.status}\n\n"
        
        if bot_member.status == 'administrator':
            permissions_text += "✅ **البوت مدير في المجموعة**\n\n"
            permissions_text += "🔑 **الصلاحيات المتاحة:**\n"
            
            # فحص الصلاحيات المختلفة
            permissions = [
                ("can_be_edited", "تعديل صلاحيات أخرى"),
                ("can_manage_chat", "إدارة المجموعة"),
                ("can_delete_messages", "حذف الرسائل"),
                ("can_manage_video_chats", "إدارة المكالمات المرئية"),
                ("can_restrict_members", "تقييد الأعضاء"),
                ("can_promote_members", "ترقية الأعضاء"),
                ("can_change_info", "تغيير معلومات المجموعة"),
                ("can_invite_users", "دعوة مستخدمين"),
                ("can_pin_messages", "تثبيت الرسائل"),
                ("can_manage_topics", "إدارة المواضيع")
            ]
            
            available_permissions = 0
            for perm_attr, perm_name in permissions:
                if hasattr(bot_member, perm_attr):
                    has_perm = getattr(bot_member, perm_attr)
                    status = "✅" if has_perm else "❌"
                    permissions_text += f"{status} {perm_name}\n"
                    if has_perm:
                        available_permissions += 1
            
            permissions_text += f"\n📈 **إجمالي الصلاحيات:** {available_permissions}/{len(permissions)}"
            
            if available_permissions < 5:
                permissions_text += "\n\n⚠️ **تحذير:** البوت يحتاج صلاحيات أكثر لتنفيذ جميع الأوامر بفعالية"
            
        else:
            permissions_text += "❌ **البوت ليس مديراً**\n"
            permissions_text += "💡 اجعل البوت مديراً لاستخدام الأوامر المتقدمة\n\n"
            permissions_text += "🔧 **الصلاحيات المطلوبة للأوامر المطلقة:**\n"
            permissions_text += "• حظر المستخدمين\n"
            permissions_text += "• حذف الرسائل\n"
            permissions_text += "• إدارة المجموعة\n"
            permissions_text += "• تقييد الأعضاء"
        
        await message.reply(permissions_text)
        
    except Exception as e:
        logging.error(f"خطأ في check_bot_permissions: {e}")
        await message.reply(f"❌ حدث خطأ أثناء فحص الصلاحيات: {str(e)[:100]}")


async def show_user_info(message: Message):
    """عرض معلومات المستخدم والمجموعة"""
    try:
        user = message.from_user
        chat = message.chat
        
        if not user:
            return
        
        # معلومات المستخدم
        info_text = f"👤 **معلومات المستخدم**\n\n"
        info_text += f"🏷️ **الاسم:** {user.first_name}"
        if user.last_name:
            info_text += f" {user.last_name}"
        info_text += f"\n🆔 **المعرف:** `{user.id}`"
        if user.username:
            info_text += f"\n📧 **اليوزر:** @{user.username}"
        
        # مستوى الإدارة
        if chat.type in ['group', 'supergroup']:
            admin_level = get_user_admin_level(user.id, chat.id)
            level_name = get_admin_level_name(admin_level)
            info_text += f"\n⭐ **المستوى الإداري:** {level_name}"
            
            # إضافة تمييز خاص للأسياد
            if user.id in MASTERS:
                info_text += " 👑"
        
        # معلومات المجموعة (إذا كانت مجموعة)
        if chat.type in ['group', 'supergroup']:
            info_text += f"\n\n🏠 **معلومات المجموعة**\n"
            info_text += f"📛 **الاسم:** {chat.title}\n"
            info_text += f"🆔 **المعرف:** `{chat.id}`\n"
            info_text += f"📊 **النوع:** {chat.type}"
            
            # عدد الأعضاء
            try:
                member_count = await message.bot.get_chat_member_count(chat.id)
                info_text += f"\n👥 **الأعضاء:** {member_count}"
            except:
                pass
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_user_info: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المعلومات")


async def show_target_user_info(message: Message):
    """عرض معلومات المستخدم المراد كشفه بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("❌ يرجى الرد على رسالة المستخدم المراد كشفه")
            return
        
        target_user = message.reply_to_message.from_user
        chat = message.chat
        
        # العنوان الرئيسي
        info_text = f"📋 **كشف معلومات المستخدم**\n\n"
        
        # معلومات المستخدم الأساسية
        info_text += f"👤 **الاسم:** {target_user.first_name}"
        if target_user.last_name:
            info_text += f" {target_user.last_name}"
        info_text += f"\n🆔 **معرف المستخدم:** `{target_user.id}`"
        if target_user.username:
            info_text += f"\n📧 **اليوزرنيم:** @{target_user.username}"
        
        # إذا كانت مجموعة، عرض الرتبة والمستوى الإداري
        if chat.type in ['group', 'supergroup']:
            admin_level = get_user_admin_level(target_user.id, chat.id)
            level_name = get_admin_level_name(admin_level)
            info_text += f"\n⭐ **الرتبة:** {level_name}"
            
            # إضافة تمييز خاص للأسياد
            if target_user.id in MASTERS:
                info_text += "\n\n👑 **مستخدم مميز: السيد**"
        
        # عدد الرسائل (افتراضي للآن)
        info_text += f"\n📊 **عدد الرسائل:** غير متوفر"
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_target_user_info: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات المستخدم")


async def show_help_command(message: Message):
    """عرض مساعدة أوامر النظام الإداري"""
    try:
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
        
        admin_level = get_user_admin_level(user_id, chat_id)
        
        help_text = "📚 **دليل أوامر النظام الإداري**\n\n"
        
        # أوامر عامة للجميع
        help_text += "🔰 **أوامر عامة (للجميع):**\n"
        help_text += "• `معلوماتي` - عرض معلوماتك الشخصية\n"
        help_text += "• `صلاحيات البوت` - فحص صلاحيات البوت\n"
        help_text += "• `قائمة المديرين` - عرض مديرين المجموعة\n"
        help_text += "• `المساعدة الإدارية` - عرض هذه المساعدة\n\n"
        
        # أوامر المشرفين
        if admin_level.value >= 1:  # MODERATOR
            help_text += "👮‍♂️ **أوامر المشرفين:**\n"
            help_text += "• أوامر الإشراف الأساسية\n"
            help_text += "• كتم وإلغاء كتم الأعضاء\n"
            help_text += "• تحذير الأعضاء\n\n"
        
        # أوامر مالكي المجموعات
        if admin_level.value >= 2:  # GROUP_OWNER
            help_text += "🏆 **أوامر مالكي المجموعات:**\n"
            help_text += "• `ترقية مشرف` (رد على رسالة)\n"
            help_text += "• `تنزيل مشرف` (رد على رسالة)\n"
            help_text += "• حظر وإلغاء حظر الأعضاء\n"
            help_text += "• إعدادات المجموعة المتقدمة\n\n"
        
        # أوامر الأسياد
        if admin_level.value >= 3:  # MASTER
            help_text += "👑 **أوامر الأسياد المطلقة:**\n"
            help_text += "• `يوكي قم بإعادة التشغيل`\n"
            help_text += "• `يوكي قم بالتدمير الذاتي`\n"
            help_text += "• `يوكي قم بمغادرة المجموعة`\n"
            help_text += "• `يوكي رقي مالك مجموعة` (رد على رسالة)\n"
            help_text += "• `يوكي نزل مالك المجموعة` (رد على رسالة)\n"
            help_text += "• `الهيكل الإداري` - عرض التنظيم الكامل\n"
            help_text += "• `إلغاء` - إيقاف أي أمر مطلق أثناء العد التنازلي\n\n"
            help_text += "⚠️ **ملاحظة:** جميع الأوامر المطلقة لها عد تنازلي 15 ثانية\n"
        
        help_text += f"📊 **مستواك الحالي:** {get_admin_level_name(admin_level)}"
        if user_id in MASTERS:
            help_text += " 👑"
        
        await message.reply(help_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_help_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المساعدة")


async def handle_utility_commands(message: Message) -> bool:
    """معالج الأوامر المساعدة"""
    if not message.text or not message.from_user:
        return False
    
    text = message.text.lower().strip()
    
    # أوامر الفحص والمعلومات
    if text in ['صلاحيات البوت', 'فحص البوت', 'bot permissions']:
        await check_bot_permissions(message)
        return True
    
    elif text in ['معلوماتي', 'my info', 'user info']:
        await show_user_info(message)
        return True
    
    elif text in ['المساعدة الإدارية', 'مساعدة النظام', 'admin help']:
        await show_help_command(message)
        return True
    
    return False
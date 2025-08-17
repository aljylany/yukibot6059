"""
معالج أحداث المجموعات
Group Events Handler
"""

import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import ChatMemberUpdated, ChatMember, Message
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config.settings import NOTIFICATION_CHANNEL, ADMINS
from database.operations import get_or_create_user
from modules.notification_manager import NotificationManager

router = Router()



async def get_group_admins_info(bot: Bot, chat_id: int):
    """جلب معلومات مشرفي المجموعة"""
    try:
        admins = await bot.get_chat_administrators(chat_id)
        admin_list = []
        
        for admin in admins:
            user = admin.user
            status_emoji = "👑" if admin.status == ChatMemberStatus.CREATOR else "🔧"
            
            # تجميع معلومات المشرف
            admin_info = f"{status_emoji} "
            if user.first_name:
                admin_info += user.first_name
            if user.last_name:
                admin_info += f" {user.last_name}"
            if user.username:
                admin_info += f" (@{user.username})"
            admin_info += f" - ID: <code>{user.id}</code>"
            
            admin_list.append(admin_info)
        
        return admin_list
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المشرفين: {e}")
        return ["❌ لا يمكن جلب معلومات المشرفين"]


async def get_group_info(bot: Bot, chat_id: int):
    """جلب معلومات المجموعة"""
    try:
        chat = await bot.get_chat(chat_id)
        
        # تحديد نوع المجموعة
        group_type = "مجموعة عادية" if chat.type == ChatType.GROUP else "مجموعة عملاقة"
        
        # جلب عدد الأعضاء
        try:
            members_count = await bot.get_chat_member_count(chat_id)
        except:
            members_count = "غير معروف"
        
        # تجميع معلومات المجموعة
        group_info = {
            "title": chat.title or "بدون عنوان",
            "type": group_type,
            "id": chat_id,
            "username": f"@{chat.username}" if chat.username else "لا يوجد",
            "members_count": members_count,
            "description": chat.description[:100] + "..." if chat.description and len(chat.description) > 100 else chat.description or "لا يوجد وصف"
        }
        
        return group_info
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المجموعة: {e}")
        return None


@router.my_chat_member()
async def handle_my_chat_member_update(update: ChatMemberUpdated, bot: Bot):
    """معالج تحديثات عضوية البوت في المجموعات"""
    try:
        # التحقق من أن التحديث خاص بإضافة البوت كعضو جديد أو ترقيته كمشرف
        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status
        
        # تجاهل التحديثات في المحادثات الخاصة
        if update.chat.type == ChatType.PRIVATE:
            return
        
        # التحقق من إضافة البوت للمجموعة لأول مرة
        if (old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and 
            new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]):
            
            logging.info(f"🎉 تم إضافة البوت إلى مجموعة جديدة: {update.chat.title} ({update.chat.id})")
            
            # جلب معلومات المجموعة والمشرفين
            group_info = await get_group_info(bot, update.chat.id)
            admins_info = await get_group_admins_info(bot, update.chat.id)
            
            if group_info:
                # إرسال الإشعار للقناة الفرعية باستخدام مدير الإشعارات
                notification_manager = NotificationManager(bot)
                await notification_manager.send_new_group_notification(group_info, admins_info)
                
        # التحقق من ترقية البوت لمشرف
        elif (old_status == ChatMemberStatus.MEMBER and 
              new_status == ChatMemberStatus.ADMINISTRATOR):
            
            logging.info(f"⬆️ تم ترقية البوت لمشرف في: {update.chat.title}")
            
            # إرسال إشعار الترقية
            group_info = {"title": update.chat.title, "id": update.chat.id}
            notification_manager = NotificationManager(bot)
            await notification_manager.send_bot_promotion_notification(group_info)
                
        # التحقق من إزالة البوت من المجموعة
        elif (old_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] and 
              new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]):
            
            logging.info(f"😢 تم إزالة البوت من: {update.chat.title}")
            
            # إرسال إشعار الإزالة
            group_info = {"title": update.chat.title, "id": update.chat.id}
            notification_manager = NotificationManager(bot)
            await notification_manager.send_bot_removal_notification(group_info)
                
    except Exception as e:
        logging.error(f"خطأ في معالج أحداث المجموعات: {e}")


@router.message(F.content_type.in_({"new_chat_members"}))
async def handle_new_members(message: Message, bot: Bot):
    """معالج إضافة أعضاء جدد للمجموعة"""
    try:
        # التحقق من وجود أعضاء جدد
        if not message.new_chat_members:
            return
            
        # التحقق من إضافة البوت كعضو جديد
        for new_member in message.new_chat_members:
            if new_member and new_member.id == bot.id:
                # البوت تم إضافته كعضو جديد
                logging.info(f"🎉 تم إضافة البوت كعضو جديد في: {message.chat.title}")
                
                # إرسال رسالة ترحيب في المجموعة
                welcome_message = """
🎉 <b>أهلاً وسهلاً! تم تفعيل البوت بنجاح</b>

🤖 أنا <b>Yuki</b>، بوت الألعاب الاقتصادية التفاعلية!

🚀 <b>للبدء:</b>
• اكتب <code>انشاء حساب بنكي</code> لبدء رحلتك
• اكتب <code>المساعدة</code> لمعرفة جميع الأوامر

💡 <b>نصيحة:</b> لأفضل تجربة، اجعلني مشرفاً في المجموعة!

🎮 <b>استعد للمتعة والتشويق في عالم الاقتصاد الافتراضي!</b>
                """
                
                await message.reply(welcome_message, parse_mode="HTML")
                
    except Exception as e:
        logging.error(f"خطأ في معالج الأعضاء الجدد: {e}")


@router.message(F.content_type.in_({"left_chat_member"}))
async def handle_left_member(message: Message, bot: Bot):
    """معالج مغادرة الأعضاء للمجموعة"""
    try:
        # التحقق من وجود عضو مغادر
        if not message.left_chat_member:
            return
            
        # التحقق من مغادرة البوت
        if message.left_chat_member.id == bot.id:
            logging.info(f"😢 البوت غادر المجموعة: {message.chat.title}")
            
    except Exception as e:
        logging.error(f"خطأ في معالج مغادرة الأعضاء: {e}")
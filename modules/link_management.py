"""
وحدة إدارة الروابط
Link Management Module
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.decorators import group_only, admin_required
from database.operations import execute_query


# تخزين روابط المجموعات
group_links = {}


@group_only
@admin_required
async def set_group_link(message: Message):
    """وضع رابط للمجموعة"""
    try:
        # استخراج الرابط من النص
        text = message.text or ""
        if text.startswith('ضع رابط '):
            link = text[9:].strip()
        else:
            await message.reply("❌ الاستخدام الصحيح: ضع رابط [الرابط]")
            return
        
        if not link:
            await message.reply("❌ يرجى إدخال رابط صحيح")
            return
        
        # التحقق من صحة الرابط (أساسي)
        if not (link.startswith('http://') or link.startswith('https://') or link.startswith('t.me/')):
            await message.reply("❌ يرجى إدخال رابط صحيح يبدأ بـ http:// أو https:// أو t.me/")
            return
        
        chat_id = message.chat.id
        group_links[chat_id] = link
        
        # حفظ في قاعدة البيانات
        query = """
        INSERT OR REPLACE INTO group_settings (chat_id, setting_name, setting_value) 
        VALUES (?, ?, ?)
        """
        await execute_query(query, (chat_id, 'group_link', link))
        
        await message.reply(f"✅ **تم حفظ رابط المجموعة بنجاح**\n🔗 الرابط: {link}")
        
    except Exception as e:
        logging.error(f"خطأ في وضع رابط المجموعة: {e}")
        await message.reply("❌ حدث خطأ في حفظ الرابط")


@group_only
@admin_required
async def delete_group_link(message: Message):
    """مسح رابط المجموعة"""
    try:
        chat_id = message.chat.id
        
        # حذف من الذاكرة
        if chat_id in group_links:
            del group_links[chat_id]
        
        # حذف من قاعدة البيانات
        query = """
        DELETE FROM group_settings 
        WHERE chat_id = ? AND setting_name = 'group_link'
        """
        await execute_query(query, (chat_id,))
        
        await message.reply("✅ **تم مسح رابط المجموعة بنجاح**")
        
    except Exception as e:
        logging.error(f"خطأ في مسح رابط المجموعة: {e}")
        await message.reply("❌ حدث خطأ في مسح الرابط")


@group_only
async def show_group_link(message: Message):
    """عرض رابط المجموعة"""
    try:
        chat_id = message.chat.id
        
        # البحث في الذاكرة أولاً
        link = group_links.get(chat_id)
        
        # إذا لم يوجد، البحث في قاعدة البيانات
        if not link:
            query = """
            SELECT setting_value FROM group_settings 
            WHERE chat_id = ? AND setting_name = 'group_link'
            """
            result = await execute_query(query, (chat_id,), fetch_one=True)
            if result:
                link = result['setting_value']
                group_links[chat_id] = link
        
        if link:
            await message.reply(f"🔗 **رابط المجموعة:**\n{link}")
        else:
            # محاولة الحصول على رابط تلقائي من تليجرام
            chat = message.chat
            if chat.username:
                auto_link = f"https://t.me/{chat.username}"
                await message.reply(f"🔗 **رابط المجموعة:**\n{auto_link}")
            else:
                await message.reply("❌ لا يوجد رابط محفوظ للمجموعة\nاستخدم 'ضع رابط [الرابط]' لإضافة رابط")
        
    except Exception as e:
        logging.error(f"خطأ في عرض رابط المجموعة: {e}")
        await message.reply("❌ حدث خطأ في عرض الرابط")


@group_only
@admin_required
async def create_invite_link(message: Message):
    """إنشاء رابط دعوة جديد"""
    try:
        chat_id = message.chat.id
        
        # محاولة إنشاء رابط دعوة جديد
        try:
            bot = message.bot
            invite_link = await bot.create_chat_invite_link(chat_id)
            
            await message.reply(
                f"✅ **تم إنشاء رابط دعوة جديد**\n\n"
                f"🔗 الرابط: {invite_link.invite_link}\n"
                f"👥 عدد الاستخدامات: غير محدود\n"
                f"⏰ صالح: دائماً"
            )
            
        except Exception as e:
            await message.reply(
                "❌ لا يمكن إنشاء رابط دعوة\n"
                "تأكد من أن البوت لديه صلاحيات الإدارة"
            )
            
    except Exception as e:
        logging.error(f"خطأ في إنشاء رابط الدعوة: {e}")
        await message.reply("❌ حدث خطأ في إنشاء رابط الدعوة")


async def load_group_links():
    """تحميل روابط المجموعات من قاعدة البيانات عند بدء التشغيل"""
    try:
        query = """
        SELECT chat_id, setting_value FROM group_settings 
        WHERE setting_name = 'group_link'
        """
        results = await execute_query(query, fetch_all=True)
        
        for result in results:
            group_links[result['chat_id']] = result['setting_value']
        
        logging.info(f"تم تحميل {len(results)} رابط مجموعة")
        
    except Exception as e:
        logging.error(f"خطأ في تحميل روابط المجموعات: {e}")


def get_group_link(chat_id: int) -> str:
    """الحصول على رابط المجموعة"""
    return group_links.get(chat_id, "")
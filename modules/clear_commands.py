"""
أوامر المسح والتنظيف
Clear and Cleanup Commands Module
"""

import logging
from aiogram.types import Message
from config.database import get_database_connection
from utils.decorators import admin_required


@admin_required
async def clear_banned(message: Message):
    """مسح قائمة المحظورين"""
    try:
        async with get_database_connection() as db:
            # مسح المحظورين من المجموعة
            result = await db.execute("""
                DELETE FROM banned_users WHERE chat_id = ?
            """, (message.chat.id,))
            
            count = result.rowcount
            await db.commit()
            
        await message.reply(f"✅ تم مسح {count} محظور من قائمة المحظورين")
        
    except Exception as e:
        logging.error(f"خطأ في مسح المحظورين: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح قائمة المحظورين")


@admin_required
async def clear_muted(message: Message):
    """مسح قائمة المكتومين"""
    try:
        async with get_database_connection() as db:
            # مسح المكتومين من المجموعة
            result = await db.execute("""
                DELETE FROM muted_users WHERE chat_id = ?
            """, (message.chat.id,))
            
            count = result.rowcount
            await db.commit()
            
        await message.reply(f"✅ تم مسح {count} مكتوم من قائمة المكتومين")
        
    except Exception as e:
        logging.error(f"خطأ في مسح المكتومين: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح قائمة المكتومين")


@admin_required
async def clear_ban_words(message: Message):
    """مسح قائمة الكلمات المحظورة"""
    try:
        async with get_database_connection() as db:
            # مسح الكلمات المحظورة من المجموعة
            result = await db.execute("""
                DELETE FROM banned_words WHERE chat_id = ?
            """, (message.chat.id,))
            
            count = result.rowcount
            await db.commit()
            
        await message.reply(f"✅ تم مسح {count} كلمة من قائمة المنع")
        
    except Exception as e:
        logging.error(f"خطأ في مسح قائمة المنع: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح قائمة المنع")


@admin_required
async def clear_replies(message: Message):
    """مسح الردود المخصصة"""
    try:
        async with get_database_connection() as db:
            # مسح الردود المخصصة من المجموعة
            result = await db.execute("""
                DELETE FROM custom_replies WHERE chat_id = ?
            """, (message.chat.id,))
            
            count = result.rowcount
            await db.commit()
            
        await message.reply(f"✅ تم مسح {count} رد مخصص")
        
    except Exception as e:
        logging.error(f"خطأ في مسح الردود: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح الردود المخصصة")


@admin_required
async def clear_custom_commands(message: Message):
    """مسح الأوامر المضافة"""
    try:
        async with get_database_connection() as db:
            # مسح الأوامر المخصصة من المجموعة
            result = await db.execute("""
                DELETE FROM custom_commands WHERE chat_id = ?
            """, (message.chat.id,))
            
            count = result.rowcount
            await db.commit()
            
        await message.reply(f"✅ تم مسح {count} أمر مخصص")
        
    except Exception as e:
        logging.error(f"خطأ في مسح الأوامر المضافة: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح الأوامر المضافة")


@admin_required
async def clear_id_template(message: Message):
    """مسح قالب الايدي"""
    try:
        async with get_database_connection() as db:
            # مسح قالب الايدي المخصص
            await db.execute("""
                DELETE FROM group_settings 
                WHERE chat_id = ? AND setting_key = 'id_template'
            """, (message.chat.id,))
            
            await db.commit()
            
        await message.reply("✅ تم مسح قالب الايدي، سيتم استخدام القالب الافتراضي")
        
    except Exception as e:
        logging.error(f"خطأ في مسح قالب الايدي: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح قالب الايدي")


@admin_required
async def clear_welcome(message: Message):
    """مسح رسالة الترحيب"""
    try:
        async with get_database_connection() as db:
            # مسح رسالة الترحيب المخصصة
            await db.execute("""
                DELETE FROM group_settings 
                WHERE chat_id = ? AND setting_key = 'welcome_message'
            """, (message.chat.id,))
            
            await db.commit()
            
        await message.reply("✅ تم مسح رسالة الترحيب المخصصة")
        
    except Exception as e:
        logging.error(f"خطأ في مسح الترحيب: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح رسالة الترحيب")


@admin_required
async def clear_link(message: Message):
    """مسح رابط المجموعة المحفوظ"""
    try:
        async with get_database_connection() as db:
            # مسح رابط المجموعة المحفوظ
            await db.execute("""
                DELETE FROM group_settings 
                WHERE chat_id = ? AND setting_key = 'group_link'
            """, (message.chat.id,))
            
            await db.commit()
            
        await message.reply("✅ تم مسح رابط المجموعة المحفوظ")
        
    except Exception as e:
        logging.error(f"خطأ في مسح الرابط: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح رابط المجموعة")


@admin_required
async def clear_all_data(message: Message):
    """مسح جميع بيانات المجموعة"""
    try:
        async with get_database_connection() as db:
            # مسح جميع البيانات المتعلقة بالمجموعة
            tables_to_clear = [
                'banned_users',
                'muted_users', 
                'banned_words',
                'custom_replies',
                'custom_commands',
                'group_settings',
                'group_ranks',
                'entertainment_ranks',
                'entertainment_marriages'
            ]
            
            total_cleared = 0
            for table in tables_to_clear:
                result = await db.execute(f"""
                    DELETE FROM {table} WHERE chat_id = ?
                """, (message.chat.id,))
                total_cleared += result.rowcount
            
            await db.commit()
            
        await message.reply(f"""
🗑️ **تم مسح جميع البيانات!**

📊 **إحصائيات المسح:**
• عدد السجلات المحذوفة: {total_cleared}
• تم إعادة تعيين جميع الإعدادات للوضع الافتراضي

⚠️ **تنبيه:** هذا الإجراء لا يمكن التراجع عنه
        """)
        
    except Exception as e:
        logging.error(f"خطأ في مسح جميع البيانات: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح البيانات")


async def clear_messages(message: Message, count: int = 1):
    """مسح عدد من الرسائل"""
    try:
        if count <= 0 or count > 100:
            await message.reply("❌ يجب أن يكون العدد بين 1 و 100")
            return
            
        # في البوتات العادية، لا يمكن مسح رسائل المستخدمين
        # لكن يمكن توضيح كيفية المسح للإدارة
        await message.reply(f"""
🗑️ **طلب مسح {count} رسالة**

⚠️ **ملاحظة:** البوتات العادية لا تستطيع مسح رسائل المستخدمين

🔧 **للإدارة:**
• اختر الرسائل المراد مسحها يدوياً
• أو استخدم الأدوات الإدارية في تيليجرام

💡 **نصيحة:** يمكن للبوت مسح رسائله الخاصة فقط
        """)
        
    except Exception as e:
        logging.error(f"خطأ في مسح الرسائل: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة طلب المسح")
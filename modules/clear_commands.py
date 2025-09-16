"""
أوامر المسح والتنظيف
Clear and Cleanup Commands Module
"""

import logging
import aiosqlite
from aiogram.types import Message
from config.database import DATABASE_URL
from database.operations import execute_query
from utils.decorators import admin_required


@admin_required
async def clear_banned(message: Message):
    """مسح قائمة المحظورين"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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
        async with aiosqlite.connect(DATABASE_URL) as db:
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


@admin_required
async def handle_clear_command(message: Message, text: str):
    """معالج أوامر المسح الرئيسي"""
    try:
        text = text.strip()
        logging.info(f"تم استلام أمر المسح: '{text}' - يوجد رد: {message.reply_to_message is not None}")
        
        # مسح بالرد - حذف الرسالة المردود عليها
        if (text == "مسح بالرد" or text == "مسح") and message.reply_to_message:
            logging.info("بدء معالجة أمر مسح بالرد")
            await delete_replied_message(message)
            return
        
        # مسح عدد معين من الرسائل
        if text.startswith("مسح ") and len(text.split()) == 2:
            try:
                count = int(text.split()[1])
                await delete_multiple_messages(message, count)
                return
            except ValueError:
                pass
        
        # أوامر مسح البيانات المختلفة
        if text == "مسح المحظورين":
            await clear_banned(message)
        elif text == "مسح المكتومين":
            await clear_muted(message)
        elif text == "مسح قائمة المنع" or text == "مسح قائمه المنع":
            await clear_ban_words(message)
        elif text == "مسح الردود":
            await clear_replies(message)
        elif text == "مسح الاوامر المضافه" or text == "مسح الأوامر المضافة":
            await clear_custom_commands(message)
        elif text == "مسح الايدي" or text == "مسح الأيدي":
            await clear_id_template(message)
        elif text == "مسح الترحيب":
            await clear_welcome(message)
        elif text == "مسح الرابط":
            await clear_link(message)
        elif text == "مسح الكل":
            await clear_all_data(message)
        else:
            await message.reply("""
❓ **أوامر المسح المتاحة:**

🗑️ **مسح الرسائل:**
• `مسح بالرد` - حذف الرسالة المردود عليها
• `مسح [العدد]` - حذف عدد معين من الرسائل (1-100)

📋 **مسح البيانات:**
• `مسح المحظورين` - مسح قائمة المحظورين
• `مسح المكتومين` - مسح قائمة المكتومين
• `مسح قائمة المنع` - مسح الكلمات المحظورة
• `مسح الردود` - مسح الردود المخصصة
• `مسح الاوامر المضافه` - مسح الأوامر المخصصة
• `مسح الايدي` - مسح قالب الهوية
• `مسح الترحيب` - مسح رسالة الترحيب
• `مسح الرابط` - مسح رابط المجموعة
• `مسح الكل` - مسح جميع البيانات

📝 **مثال:** للرد على رسالة واكتب `مسح بالرد`
            """)
            
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر المسح: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ أمر المسح")


@admin_required
async def delete_replied_message(message: Message):
    """حذف الرسالة المردود عليها"""
    try:
        logging.info("بدء دالة حذف الرسالة المردود عليها")
        
        if not message.reply_to_message:
            logging.warning("لا يوجد رد على رسالة")
            await message.reply("❌ يجب الرد على رسالة لحذفها")
            return
        
        logging.info(f"معرف الرسالة المراد حذفها: {message.reply_to_message.message_id}")
        
        # التحقق من صلاحيات البوت
        try:
            bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
            logging.info(f"حالة البوت في المجموعة: {bot_member.status}")
            
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply("❌ البوت يحتاج صلاحيات إدارية لحذف الرسائل")
                return
            
            # فحص صلاحية حذف الرسائل للمشرفين فقط
            if bot_member.status == 'administrator' and hasattr(bot_member, 'can_delete_messages') and not bot_member.can_delete_messages:
                await message.reply("❌ البوت لا يملك صلاحية حذف الرسائل")
                return
        
        except Exception as perm_error:
            logging.error(f"خطأ في فحص الصلاحيات: {perm_error}")
            await message.reply("❌ لا يمكن فحص صلاحيات البوت")
            return
        
        # حذف الرسالة المردود عليها
        try:
            logging.info("محاولة حذف الرسالة المردود عليها")
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id
            )
            logging.info("تم حذف الرسالة المردود عليها بنجاح")
            
            # حذف رسالة الأمر أيضاً
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=message.message_id
                )
                logging.info("تم حذف رسالة الأمر أيضاً")
            except Exception as cmd_error:
                logging.warning(f"لم نتمكن من حذف رسالة الأمر: {cmd_error}")
                
            # إرسال تأكيد مؤقت
            confirmation = await message.reply("✅ تم حذف الرسالة بنجاح")
            
            # حذف رسالة التأكيد بعد 3 ثوان
            import asyncio
            await asyncio.sleep(3)
            try:
                await confirmation.delete()
            except:
                pass
                
        except Exception as delete_error:
            if "Bad Request: message to delete not found" in str(delete_error):
                await message.reply("❌ الرسالة محذوفة مسبقاً أو لا يمكن العثور عليها")
            elif "Bad Request: not enough rights" in str(delete_error):
                await message.reply("❌ البوت لا يملك صلاحيات كافية لحذف هذه الرسالة")
            else:
                await message.reply("❌ فشل في حذف الرسالة")
                logging.error(f"خطأ في حذف الرسالة: {delete_error}")
        
    except Exception as e:
        logging.error(f"خطأ في حذف الرسالة المردود عليها: {e}")
        await message.reply("❌ حدث خطأ أثناء حذف الرسالة")


@admin_required
async def delete_multiple_messages(message: Message, count: int):
    """حذف عدد معين من الرسائل"""
    try:
        if count <= 0 or count > 100:
            await message.reply("❌ يجب أن يكون العدد بين 1 و 100")
            return
        
        # التحقق من صلاحيات البوت
        try:
            bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
            if bot_member.status not in ['administrator', 'creator']:
                await message.reply("❌ البوت يحتاج صلاحيات إدارية لحذف الرسائل")
                return
            
            if not bot_member.can_delete_messages:
                await message.reply("❌ البوت لا يملك صلاحية حذف الرسائل")
                return
        
        except Exception as perm_error:
            logging.error(f"خطأ في فحص الصلاحيات: {perm_error}")
            await message.reply("❌ لا يمكن فحص صلاحيات البوت")
            return
        
        # حذف الرسائل
        current_message_id = message.message_id
        deleted_count = 0
        
        # حذف الرسائل من الأحدث للأقدم
        for i in range(count + 1):  # +1 لتضمين رسالة الأمر
            try:
                await message.bot.delete_message(
                    chat_id=message.chat.id,
                    message_id=current_message_id - i
                )
                deleted_count += 1
            except Exception as delete_error:
                if "message to delete not found" not in str(delete_error):
                    logging.error(f"خطأ في حذف الرسالة {current_message_id - i}: {delete_error}")
                continue
        
        # إرسال تأكيد مؤقت
        confirmation = await message.reply(f"✅ تم حذف {deleted_count} رسالة بنجاح")
        
        # حذف رسالة التأكيد بعد 5 ثوان
        import asyncio
        await asyncio.sleep(5)
        try:
            await confirmation.delete()
        except:
            pass
        
    except Exception as e:
        logging.error(f"خطأ في حذف الرسائل المتعددة: {e}")
        await message.reply("❌ حدث خطأ أثناء حذف الرسائل")


async def clear_messages(message: Message, count: int = 1):
    """مسح عدد من الرسائل - وظيفة مساعدة للتوافق مع الأنظمة الأخرى"""
    await delete_multiple_messages(message, count)
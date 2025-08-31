"""
نظام إصمات المشرفين الخاص بالسيد الأعلى
Supreme Silence Commands System
"""

import logging
import re
import sqlite3
from datetime import datetime, timedelta
from typing import Optional
from aiogram.types import Message
from config.hierarchy import is_supreme_master, get_user_admin_level, AdminLevel

# استيراد دالة الاتصال بقاعدة البيانات من الملف الصحيح
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# الحصول على دالة الاتصال بقاعدة البيانات
def get_db():
    import sqlite3
    return sqlite3.connect('yukibot.db')


async def parse_time_duration(time_text: str) -> Optional[datetime]:
    """
    تحليل مدة الإصمات من النص
    يدعم الصيغ: 5د (دقائق)، 5ث (ثواني)، 1س (ساعات)
    """
    try:
        if not time_text:
            return None
            
        # البحث عن الأرقام والوحدات
        pattern = r'(\d+)([دثس])'
        match = re.search(pattern, time_text)
        
        if not match:
            return None
            
        amount = int(match.group(1))
        unit = match.group(2)
        
        now = datetime.now()
        
        if unit == 'ث':  # ثواني
            return now + timedelta(seconds=amount)
        elif unit == 'د':  # دقائق
            return now + timedelta(minutes=amount)
        elif unit == 'س':  # ساعات
            return now + timedelta(hours=amount)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في تحليل مدة الإصمات: {e}")
        return None


async def is_target_moderator(user_id: int, chat_id: int) -> bool:
    """التحقق من أن المستخدم المستهدف مشرف فعلي وليس عضو عادي"""
    try:
        user_level = get_user_admin_level(user_id, chat_id)
        # الأمر يعمل فقط على المشرفين ومالكي المجموعات، وليس الأعضاء العاديين
        return user_level in [AdminLevel.MODERATOR, AdminLevel.GROUP_OWNER]
    except Exception as e:
        logging.error(f"خطأ في فحص مستوى المستخدم: {e}")
        return False


async def silence_moderator(user_id: int, chat_id: int, silenced_by: int, duration: Optional[datetime] = None) -> bool:
    """إصمات مشرف في قاعدة البيانات"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        # حذف أي إصمات سابق للمستخدم في نفس المجموعة
        cursor.execute("""
            DELETE FROM silenced_moderators 
            WHERE user_id = ? AND chat_id = ?
        """, (user_id, chat_id))
        
        # إضافة الإصمات الجديد
        cursor.execute("""
            INSERT INTO silenced_moderators 
            (user_id, chat_id, silenced_by, silenced_until, is_active)
            VALUES (?, ?, ?, ?, 1)
        """, (user_id, chat_id, silenced_by, duration.isoformat() if duration else None))
        
        conn.commit()
        conn.close()
        
        logging.info(f"تم إصمات المشرف {user_id} في المجموعة {chat_id} بواسطة {silenced_by}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إصمات المشرف: {e}")
        return False


async def unsilence_moderator(user_id: int, chat_id: int) -> bool:
    """إلغاء إصمات مشرف"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            DELETE FROM silenced_moderators 
            WHERE user_id = ? AND chat_id = ?
        """, (user_id, chat_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"تم إلغاء إصمات المشرف {user_id} في المجموعة {chat_id}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إلغاء إصمات المشرف: {e}")
        return False


async def is_moderator_silenced(user_id: int, chat_id: int) -> bool:
    """فحص إذا كان المشرف مصمت حالياً"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT silenced_until FROM silenced_moderators 
            WHERE user_id = ? AND chat_id = ? AND is_active = 1
        """, (user_id, chat_id))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return False
            
        # إذا لم يكن هناك تاريخ انتهاء، فهو إصمات دائم
        if not result[0]:
            return True
            
        # فحص إذا انتهت مدة الإصمات
        until_date = datetime.fromisoformat(result[0])
        if datetime.now() >= until_date:
            # انتهت المدة، حذف الإصمات
            await unsilence_moderator(user_id, chat_id)
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"خطأ في فحص إصمات المشرف: {e}")
        return False


async def handle_silence_command(message: Message) -> bool:
    """
    معالج أمر الإصمات الخاص بالسيد الأعلى
    يدعم: اصمت (رد على رسالة)، اصمت 5د، اصمت 5ث، اصمت 1س
    """
    try:
        # التحقق من أن المرسل هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            return False
            
        # التحقق من أن الأمر في مجموعة
        if message.chat.type == 'private':
            await message.reply("❌ هذا الأمر يعمل فقط في المجموعات")
            return True
            
        text = message.text.strip()
        
        # تحليل الأمر
        if text == "اصمت":
            # إصمات دائم (رد على رسالة)
            if not message.reply_to_message:
                await message.reply("❌ يرجى الرد على رسالة المشرف المراد إصماته")
                return True
                
            target_user_id = message.reply_to_message.from_user.id
            target_user_name = message.reply_to_message.from_user.first_name or "المستخدم"
            duration = None
            duration_text = "دائم"
            
        elif text.startswith("اصمت "):
            # إصمات مؤقت مع مدة زمنية
            if not message.reply_to_message:
                await message.reply("❌ يرجى الرد على رسالة المشرف المراد إصماته")
                return True
                
            time_part = text[5:].strip()  # إزالة "اصمت "
            target_user_id = message.reply_to_message.from_user.id
            target_user_name = message.reply_to_message.from_user.first_name or "المستخدم"
            
            duration = await parse_time_duration(time_part)
            if not duration:
                await message.reply("❌ صيغة الوقت غير صحيحة. استخدم: 5د (دقائق)، 5ث (ثواني)، 1س (ساعات)")
                return True
                
            duration_text = time_part
            
        else:
            return False  # ليس أمر إصمات
            
        # التحقق من أن المستهدف مشرف فعلي
        if not await is_target_moderator(target_user_id, message.chat.id):
            await message.reply("❌ هذا الأمر يعمل فقط على المشرفين الفعليين، وليس الأعضاء العاديين")
            return True
            
        # التحقق من عدم إصمات السيد الأعلى نفسه
        if is_supreme_master(target_user_id):
            await message.reply("⛔ لا يمكن إصمات السيد الأعلى!")
            return True
            
        # تطبيق الإصمات
        success = await silence_moderator(
            target_user_id, 
            message.chat.id, 
            message.from_user.id, 
            duration
        )
        
        if success:
            reply_text = f"""
🔇 **تم إصمات المشرف**

👤 **المشرف:** {target_user_name}
🆔 **المعرف:** `{target_user_id}`
⏰ **المدة:** {duration_text}
👑 **بواسطة:** السيد الأعلى

⚠️ سيتم حذف جميع رسائل هذا المشرف تلقائياً حتى انتهاء الإصمات
            """
            await message.reply(reply_text.strip())
        else:
            await message.reply("❌ فشل في تطبيق الإصمات، يرجى المحاولة مرة أخرى")
            
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج أمر الإصمات: {e}")
        await message.reply("❌ حدث خطأ أثناء تطبيق الإصمات")
        return True


async def handle_unsilence_command(message: Message) -> bool:
    """
    معالج أمر إلغاء الإصمات (فك الإصمات)
    """
    try:
        # التحقق من أن المرسل هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            return False
            
        text = message.text.strip()
        
        if text != "فك الاصمات" and text != "الغاء الاصمات":
            return False
            
        # التحقق من أن الأمر في مجموعة
        if message.chat.type == 'private':
            await message.reply("❌ هذا الأمر يعمل فقط في المجموعات")
            return True
            
        # التحقق من الرد على رسالة
        if not message.reply_to_message:
            await message.reply("❌ يرجى الرد على رسالة المشرف المراد فك إصماته")
            return True
            
        target_user_id = message.reply_to_message.from_user.id
        target_user_name = message.reply_to_message.from_user.first_name or "المستخدم"
        
        # فحص إذا كان مصمت أصلاً
        if not await is_moderator_silenced(target_user_id, message.chat.id):
            await message.reply("❌ هذا المشرف ليس مصمت حالياً")
            return True
            
        # إلغاء الإصمات
        success = await unsilence_moderator(target_user_id, message.chat.id)
        
        if success:
            reply_text = f"""
🔊 **تم فك إصمات المشرف**

👤 **المشرف:** {target_user_name}
🆔 **المعرف:** `{target_user_id}`
👑 **بواسطة:** السيد الأعلى

✅ يمكن للمشرف الآن إرسال الرسائل مرة أخرى
            """
            await message.reply(reply_text.strip())
        else:
            await message.reply("❌ فشل في إلغاء الإصمات، يرجى المحاولة مرة أخرى")
            
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج إلغاء الإصمات: {e}")
        await message.reply("❌ حدث خطأ أثناء إلغاء الإصمات")
        return True


async def handle_silenced_list_command(message: Message) -> bool:
    """
    معالج أمر عرض قائمة المشرفين المصمتين
    """
    try:
        # التحقق من أن المرسل هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            return False
            
        text = message.text.strip()
        
        if text != "المصمتين" and text != "قائمة المصمتين":
            return False
            
        # التحقق من أن الأمر في مجموعة
        if message.chat.type == 'private':
            await message.reply("❌ هذا الأمر يعمل فقط في المجموعات")
            return True
            
        # جلب قائمة المصمتين
        conn = get_db()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT user_id, silenced_at, silenced_until 
            FROM silenced_moderators 
            WHERE chat_id = ? AND is_active = 1
            ORDER BY silenced_at DESC
        """, (message.chat.id,))
        
        silenced_users = cursor.fetchall()
        conn.close()
        
        if not silenced_users:
            await message.reply("📋 **قائمة المشرفين المصمتين:**\n\n❌ لا يوجد مشرفين مصمتين حالياً")
            return True
            
        # تنسيق القائمة
        users_list = []
        for user_id, silenced_at, silenced_until in silenced_users:
            try:
                # محاولة جلب معلومات المستخدم
                user_info = await message.bot.get_chat_member(message.chat.id, user_id)
                user_name = user_info.user.first_name or f"المستخدم {user_id}"
                username = f"@{user_info.user.username}" if user_info.user.username else "بدون معرف"
                
                user_text = f"🔇 {user_name} ({username})\n   🆔 {user_id}"
                
                if silenced_until:
                    user_text += f"\n   ⏰ حتى: {silenced_until[:16]}"
                else:
                    user_text += f"\n   ⏰ إصمات دائم"
                    
                users_list.append(user_text)
                
            except Exception:
                # في حالة عدم العثور على معلومات المستخدم
                user_text = f"🔇 المستخدم {user_id}"
                if silenced_until:
                    user_text += f"\n   ⏰ حتى: {silenced_until[:16]}"
                else:
                    user_text += f"\n   ⏰ إصمات دائم"
                users_list.append(user_text)
                
        reply_text = f"📋 **قائمة المشرفين المصمتين:** ({len(silenced_users)})\n\n" + "\n\n".join(users_list)
        reply_text += f"\n\n💡 **ملاحظة:** استخدم 'فك الاصمات' بالرد على رسالة المشرف لإلغاء إصماته"
        
        await message.reply(reply_text)
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج قائمة المصمتين: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض قائمة المصمتين")
        return True
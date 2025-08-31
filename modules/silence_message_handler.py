"""
معالج حذف رسائل المشرفين المصمتين
Silenced Moderators Message Deletion Handler
"""

import logging
from aiogram.types import Message
from modules.supreme_silence_commands import is_moderator_silenced


async def handle_silenced_moderator_message(message: Message) -> bool:
    """
    فحص وحذف رسائل المشرفين المصمتين
    
    Returns:
        True إذا تم حذف الرسالة (المستخدم مصمت)
        False إذا لم يتم حذف الرسالة (المستخدم غير مصمت)
    """
    try:
        # فحص إذا كان في مجموعة
        if message.chat.type == 'private':
            return False
            
        # فحص إذا كان المرسل مصمت
        if await is_moderator_silenced(message.from_user.id, message.chat.id):
            # حذف الرسالة
            try:
                await message.delete()
                
                # تسجيل الحدث
                user_name = message.from_user.first_name or "مستخدم"
                logging.info(f"تم حذف رسالة من المشرف المصمت {user_name} ({message.from_user.id}) في المجموعة {message.chat.id}")
                
                return True
                
            except Exception as delete_error:
                # في حالة فشل الحذف (قد يكون البوت لا يملك صلاحيات)
                logging.warning(f"فشل في حذف رسالة المشرف المصمت {message.from_user.id}: {delete_error}")
                
                # إرسال تنبيه للسيد الأعلى (اختياري)
                try:
                    await message.reply(
                        f"⚠️ **تحذير للسيد الأعلى**\n\n"
                        f"🔇 المشرف المصمت {user_name} أرسل رسالة\n"
                        f"❌ فشل في حذف الرسالة تلقائياً\n"
                        f"🔧 تحقق من صلاحيات البوت"
                    )
                except Exception:
                    pass  # تجاهل فشل إرسال التنبيه
                    
                return True  # اعتبار أنه تم التعامل مع الرسالة
                
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل المصمتين: {e}")
        return False
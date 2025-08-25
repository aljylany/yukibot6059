"""
معالج النظام الجديد للحماية من الألفاظ المسيئة
نظام متطور بدرجات الخطورة والذكاء الاصطناعي
"""

import logging
from aiogram.types import Message
from modules.profanity_filter import check_message_advanced, mute_user_for_profanity

async def handle_new_profanity_system(message: Message) -> bool:
    """
    معالج النظام الجديد مع درجات الخطورة والرسائل المتطورة
    """
    try:
        # التأكد من أن الرسالة في مجموعة وليس خاص
        if message.chat.type == 'private':
            return False
        
        # استثناء أوامر المسح من فحص السباب
        if message.text:
            text = message.text.strip()
            if text.startswith('مسح ') or text == 'مسح بالرد' or text == 'مسح':
                return False
        
        # الفحص المتطور بالذكاء الاصطناعي
        result = await check_message_advanced(message.text, message.from_user.id, message.chat.id)
        
        if not result['is_abusive']:
            return False
        
        # حذف الرسالة المسيئة أولاً
        try:
            await message.delete()
            logging.info("تم حذف الرسالة المسيئة")
        except Exception as delete_error:
            logging.warning(f"لم يتمكن من حذف الرسالة المسيئة: {delete_error}")
        
        # معالجة العقوبة حسب درجة الخطورة
        severity = result.get('severity', 1)
        warnings_count = result.get('warnings', 0)
        
        # محاولة كتم المستخدم
        mute_success = await mute_user_for_profanity(message)
        
        # فحص نوع المستخدم للرسالة المناسبة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        user_name = message.from_user.first_name or "المستخدم"
        
        # رسائل النظام الجديد حسب درجة الخطورة
        if severity == 1:  # خفيف
            if mute_success:
                warning_message = await message.answer(
                    f"⚠️ **تحذير لـ {user_name}**\n\n"
                    f"🛡️ **نظام الحماية المتطور كشف لغة غير مناسبة**\n"
                    f"📊 **مستوى الخطورة:** خفيف\n"
                    f"⏰ **مدة الكتم:** 30 دقيقة\n"
                    f"🔢 **التحذيرات:** {warnings_count}\n\n"
                    f"💡 **نصيحة:** استخدم لغة مهذبة في المحادثات"
                )
        elif severity == 2:  # متوسط
            if mute_success:
                warning_message = await message.answer(
                    f"🔥 **إنذار قوي لـ {user_name}!**\n\n"
                    f"🤖 **الذكاء الاصطناعي كشف لغة مسيئة**\n"
                    f"📊 **مستوى الخطورة:** متوسط\n"
                    f"⏰ **مدة الكتم:** ساعة كاملة\n"
                    f"🔢 **التحذيرات:** {warnings_count}\n\n"
                    f"⚡️ **تحذير:** تكرار هذا السلوك سيؤدي لعقوبة أشد!"
                )
        else:  # شديد (3 أو أكثر)
            if mute_success:
                warning_message = await message.answer(
                    f"🚨 **طرد فوري لـ {user_name}!**\n\n"
                    f"🤖 **نظام الذكاء الاصطناعي المتطور كشف محتوى شديد الإساءة**\n"
                    f"📊 **مستوى الخطورة:** عالي جداً\n"
                    f"⏰ **العقوبة:** كتم 24 ساعة\n"
                    f"🔢 **التحذيرات:** {warnings_count}\n\n"
                    f"💀 **لا تساهل مع هذا المستوى من الإساءة!**"
                )
        
        # رسائل خاصة للمشرفين والمالكين
        if user_member.status == 'administrator':
            warning_message = await message.answer(
                f"🔥 **تحذير للمشرف {user_name}**\n\n"
                f"🤖 **نظام الحماية المتطور لا يستثني أحد**\n"
                f"📊 **درجة الخطورة:** {severity}\n"
                f"👑 **الأدب مطلوب من الجميع**\n\n"
                f"⚖️ **تذكر: أنت قدوة للأعضاء!**"
            )
        elif user_member.status == 'creator':
            warning_message = await message.answer(
                f"🙏 **ملاحظة محترمة لمالك المجموعة {user_name}**\n\n"
                f"🤖 **نظام الذكاء الاصطناعي كشف محتوى غير مناسب**\n"
                f"📊 **درجة الخطورة:** {severity}\n"
                f"🌟 **نأمل أن تكون قدوة في الأدب**\n\n"
                f"👑 **احترامك لقوانين الأدب يُلهم الآخرين**"
            )
        
        # حذف رسالة التحذير بعد 30 ثانية
        if 'warning_message' in locals():
            import asyncio
            async def delete_warning():
                await asyncio.sleep(30)
                try:
                    await warning_message.delete()
                except:
                    pass
            asyncio.create_task(delete_warning())
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج النظام الجديد للحماية: {e}")
        return False
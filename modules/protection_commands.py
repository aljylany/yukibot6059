"""
معالج الأوامر العربية لنظام الحماية المتطور
"""

import logging
from aiogram.types import Message
from aiogram import F
from config.hierarchy import MASTERS

async def handle_protection_toggle_command(message: Message) -> bool:
    """
    معالج أوامر تفعيل وتعطيل الحماية
    للمالكين والأسياد فقط
    """
    try:
        if not message.text:
            return False
            
        text = message.text.strip()
        
        # التحقق من أن الأمر هو تفعيل أو تعطيل الحماية
        is_enable_command = text in ["تفعيل الحماية", "تشغيل الحماية", "فعل الحماية"]
        is_disable_command = text in ["تعطيل الحماية", "إيقاف الحماية", "عطل الحماية"]
        
        if not (is_enable_command or is_disable_command):
            return False
        
        # التحقق من أن الرسالة في مجموعة وليس في الخاص
        if message.chat.type == 'private':
            await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**")
            return True
        
        # التحقق من صلاحية المستخدم (مالك مجموعة أو سيد)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من كون المستخدم سيد
        is_master = user_id in MASTERS
        
        # الحصول على قائمة المالكين من قاعدة البيانات
        is_owner = False
        try:
            from config.hierarchy import GROUP_OWNERS
            if chat_id in GROUP_OWNERS and user_id in GROUP_OWNERS[chat_id]:
                is_owner = True
        except (ImportError, NameError):
            pass
        
        # التحقق من كون المستخدم مالك المجموعة من تليجرام
        try:
            member = await message.bot.get_chat_member(chat_id, user_id)
            is_telegram_owner = member.status == 'creator'
        except:
            is_telegram_owner = False
        
        # إذا لم يكن المستخدم مؤهل
        if not (is_master or is_owner or is_telegram_owner):
            await message.reply(
                "⛔️ **ليس لديك صلاحية لاستخدام هذا الأمر!**\n\n"
                "🔐 **هذا الأمر مخصص للمالكين والأسياد فقط**\n"
                "👑 **رتبتك الحالية لا تسمح بالتحكم في نظام الحماية**"
            )
            return True
        
        # تنفيذ الأمر
        from modules.profanity_filter import toggle_protection, init_abusive_db, init_ml_model
        
        # التأكد من تهيئة النظام
        try:
            init_abusive_db()
            init_ml_model()
        except Exception as init_error:
            logging.warning(f"تحذير في تهيئة نظام الحماية: {init_error}")
        
        # تطبيق التغيير
        success = await toggle_protection(chat_id, is_enable_command, user_id)
        
        if success:
            if is_enable_command:
                await message.reply(
                    "✅ **تم تفعيل نظام الحماية المتطور بنجاح!**\n\n"
                    f"👑 **بواسطة:** {message.from_user.first_name}\n"
                    f"🛡️ **الحالة:** مفعل ونشط\n\n"
                    "🔍 **المزايا المفعلة:**\n"
                    "• كشف الألفاظ المسيئة من قاعدة البيانات\n"
                    "• نموذج الذكاء الاصطناعي للكشف المتطور\n"
                    "• نظام التحذيرات التدريجي\n"
                    "• الكتم التلقائي للمخالفين\n\n"
                    "⚡️ **يوكي الآن يحمي المجموعة بأقوى نظام حماية!**"
                )
            else:
                await message.reply(
                    "⏸️ **تم تعطيل نظام الحماية المتطور**\n\n"
                    f"👑 **بواسطة:** {message.from_user.first_name}\n"
                    f"🛡️ **الحالة:** معطل مؤقتاً\n\n"
                    "⚠️ **تحذير:** المجموعة الآن بدون حماية من الألفاظ المسيئة\n\n"
                    "💡 **لإعادة التفعيل:** اكتب `تفعيل الحماية`"
                )
        else:
            await message.reply(
                "❌ **حدث خطأ أثناء تنفيذ الأمر!**\n\n"
                "🔧 يرجى المحاولة مرة أخرى أو التواصل مع المطور"
            )
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر الحماية: {e}")
        await message.reply("❌ حدث خطأ غير متوقع!")
        return True

async def handle_protection_status_command(message: Message) -> bool:
    """
    معالج أمر عرض حالة الحماية
    """
    try:
        if not message.text:
            return False
            
        text = message.text.strip()
        
        if text not in ["حالة الحماية", "وضع الحماية", "إعدادات الحماية"]:
            return False
        
        # التحقق من أن الرسالة في مجموعة
        if message.chat.type == 'private':
            await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**")
            return True
        
        from modules.profanity_filter import is_protection_enabled
        
        chat_id = message.chat.id
        is_enabled = is_protection_enabled(chat_id)
        
        status_text = "🟢 **مفعل**" if is_enabled else "🔴 **معطل**"
        status_emoji = "🛡️" if is_enabled else "⚠️"
        
        response = f"{status_emoji} **حالة نظام الحماية المتطور**\n\n"
        response += f"📊 **الحالة الحالية:** {status_text}\n"
        response += f"🏠 **المجموعة:** {message.chat.title or 'غير محدد'}\n\n"
        
        if is_enabled:
            response += "✅ **المزايا النشطة:**\n"
            response += "• كشف الألفاظ المسيئة من قاعدة البيانات\n"
            response += "• نموذج الذكاء الاصطناعي للكشف المتطور\n"
            response += "• نظام التحذيرات التدريجي (حسب الخطورة)\n"
            response += "• الكتم التلقائي للمخالفين\n"
            response += "• حماية شاملة للمجموعة\n\n"
            response += "💡 **لإيقاف الحماية:** `تعطيل الحماية` (للمالكين فقط)"
        else:
            response += "❌ **التحذير:** النظام معطل حالياً\n"
            response += "🚨 المجموعة بدون حماية من الألفاظ المسيئة\n\n"
            response += "💡 **لتفعيل الحماية:** `تفعيل الحماية` (للمالكين فقط)"
        
        await message.reply(response)
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج حالة الحماية: {e}")
        await message.reply("❌ حدث خطأ في عرض حالة الحماية!")
        return True

async def handle_protection_commands(message: Message) -> bool:
    """المعالج الرئيسي المُبسط لأوامر الحماية"""
    logging.info(f"🔍 تم استلام أمر حماية: {message.text}")
    try:
        # معالجة أوامر التفعيل/التعطيل
        if await handle_protection_toggle_command(message):
            return True
            
        # معالجة أمر عرض الحالة
        if await handle_protection_status_command(message):
            return True
            
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر الحماية: {e}")
        await message.reply("❌ حدث خطأ في معالج الحماية!")
        return False
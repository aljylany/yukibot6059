"""
أوامر إدارة فلتر الألفاظ المسيئة
Profanity Filter Management Commands
"""

import logging
from aiogram.types import Message
from aiogram.filters import Command

from config.hierarchy import has_permission, AdminLevel, get_user_admin_level
from modules.profanity_filter import profanity_filter
from utils.decorators import group_only


@group_only
async def enable_profanity_filter(message: Message):
    """تفعيل فلتر الألفاظ المسيئة - أمر: فعل الفلتر"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من الصلاحيات - مالكين ومشرفين وأسياد فقط
        user_level = get_user_admin_level(user_id, chat_id)
        if user_level.value < AdminLevel.MODERATOR.value:
            await message.reply("❌ هذا الأمر متاح فقط للمشرفين ومالكي المجموعة والأسياد")
            return
        
        # التحقق من حالة التفعيل الحالية
        if profanity_filter.is_enabled(chat_id):
            await message.reply("✅ فلتر الألفاظ المسيئة مفعل بالفعل في هذه المجموعة")
            return
        
        # تفعيل الفلتر
        success = await profanity_filter.enable_filter(chat_id)
        
        if success:
            response = """
✅ **تم تفعيل فلتر الألفاظ المسيئة بنجاح!**

🔍 **ما سيحدث الآن:**
• سيتم حذف الرسائل التي تحتوي على ألفاظ مسيئة تلقائياً
• سيحصل المخالفون على تحذيرات (الحد الأقصى: 3 تحذيرات)
• بعد 3 تحذيرات سيتم كتم المستخدم لمدة ساعة واحدة
• العقوبة تنتهي تلقائياً بعد انتهاء المدة

⚡ **أوامر الإدارة:**
• `عطل الفلتر` - لتعطيل النظام
• `احصائيات الفلتر` - لعرض الإحصائيات
• `امسح تحذيرات @username` - لمسح تحذيرات عضو

🛡️ **ملاحظة:** المشرفين والمالكين محصنون من الفلتر
"""
            await message.reply(response)
            logging.info(f"تم تفعيل فلتر الألفاظ في المجموعة {chat_id} بواسطة {user_id}")
        else:
            await message.reply("❌ حدث خطأ أثناء تفعيل فلتر الألفاظ المسيئة")
            
    except Exception as e:
        logging.error(f"خطأ في تفعيل فلتر الألفاظ: {e}")
        await message.reply("❌ حدث خطأ أثناء تفعيل الفلتر")


@group_only
async def disable_profanity_filter(message: Message):
    """تعطيل فلتر الألفاظ المسيئة - أمر: عطل الفلتر"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من الصلاحيات - مالكين ومشرفين وأسياد فقط
        user_level = get_user_admin_level(user_id, chat_id)
        if user_level.value < AdminLevel.MODERATOR.value:
            await message.reply("❌ هذا الأمر متاح فقط للمشرفين ومالكي المجموعة والأسياد")
            return
        
        # التحقق من حالة التفعيل الحالية
        if not profanity_filter.is_enabled(chat_id):
            await message.reply("⚠️ فلتر الألفاظ المسيئة معطل بالفعل في هذه المجموعة")
            return
        
        # تعطيل الفلتر
        success = await profanity_filter.disable_filter(chat_id)
        
        if success:
            response = """
⚠️ **تم تعطيل فلتر الألفاظ المسيئة**

📝 **ما تم إيقافه:**
• لن يتم حذف الرسائل المسيئة تلقائياً
• لن يتم إعطاء تحذيرات للمخالفين
• تم إيقاف نظام العقوبات التلقائي

🔄 **للتفعيل مرة أخرى:** استخدم الأمر `فعل الفلتر`

ℹ️ **ملاحظة:** التحذيرات والعقوبات السابقة محفوظة ولن تُحذف
"""
            await message.reply(response)
            logging.info(f"تم تعطيل فلتر الألفاظ في المجموعة {chat_id} بواسطة {user_id}")
        else:
            await message.reply("❌ حدث خطأ أثناء تعطيل فلتر الألفاظ المسيئة")
            
    except Exception as e:
        logging.error(f"خطأ في تعطيل فلتر الألفاظ: {e}")
        await message.reply("❌ حدث خطأ أثناء تعطيل الفلتر")


@group_only
async def profanity_filter_stats(message: Message):
    """عرض إحصائيات فلتر الألفاظ المسيئة - أمر: احصائيات الفلتر"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من الصلاحيات - مالكين ومشرفين وأسياد فقط
        user_level = get_user_admin_level(user_id, chat_id)
        if user_level.value < AdminLevel.MODERATOR.value:
            await message.reply("❌ هذا الأمر متاح فقط للمشرفين ومالكي المجموعة والأسياد")
            return
        
        # جلب الإحصائيات
        stats = await profanity_filter.get_filter_stats(chat_id)
        
        status_emoji = "✅" if stats['enabled'] else "❌"
        status_text = "مفعل" if stats['enabled'] else "معطل"
        
        response = f"""
📊 **إحصائيات فلتر الألفاظ المسيئة**

🔄 **الحالة:** {status_emoji} {status_text}

📈 **الإحصائيات:**
• 👥 المستخدمين مع تحذيرات: {stats['users_with_warnings']}
• ⛔ المستخدمين المعاقبين حالياً: {stats['punished_users']}
• 📋 إجمالي التحذيرات: {stats['total_warnings']}

⚡ **أوامر الإدارة:**
• `فعل الفلتر` / `عطل الفلتر` - تفعيل/تعطيل النظام
• `امسح تحذيرات @username` - مسح تحذيرات عضو

🛡️ **ملاحظة:** النظام يحمي المشرفين والمالكين تلقائياً
"""
        
        await message.reply(response)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات الفلتر: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب الإحصائيات")


@group_only
async def clear_user_warnings(message: Message):
    """مسح تحذيرات مستخدم معين - أمر: امسح تحذيرات"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # التحقق من الصلاحيات - مالكين ومشرفين وأسياد فقط
        user_level = get_user_admin_level(user_id, chat_id)
        if user_level.value < AdminLevel.MODERATOR.value:
            await message.reply("❌ هذا الأمر متاح فقط للمشرفين ومالكي المجموعة والأسياد")
            return
        
        # التحقق من وجود رد على رسالة أو منشن
        target_user = None
        target_user_id = None
        
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            target_user_id = target_user.id
        else:
            # البحث عن منشن في النص
            if message.entities:
                for entity in message.entities:
                    if entity.type == "mention":
                        # استخراج اليوزرنيم من النص
                        username = message.text[entity.offset:entity.offset + entity.length].replace('@', '')
                        await message.reply("❌ لا يمكن العثور على المستخدم بهذه الطريقة. يرجى الرد على رسالة المستخدم أو استخدام معرفه الرقمي")
                        return
                    elif entity.type == "text_mention":
                        target_user = entity.user
                        target_user_id = target_user.id
                        break
        
        if not target_user_id:
            await message.reply("""
❌ **طريقة الاستخدام غير صحيحة**

✅ **الطرق الصحيحة:**
• الرد على رسالة المستخدم مع الأمر `امسح تحذيرات`
• استخدام المعرف الرقمي: `امسح تحذيرات 123456789`

💡 **مثال:** ارد على رسالة العضو واكتب `امسح تحذيرات`
""")
            return
        
        # التحقق من التحذيرات الحالية
        current_warnings = await profanity_filter.get_user_warnings(target_user_id, chat_id)
        
        if current_warnings['warning_count'] == 0 and not current_warnings['is_punished']:
            user_name = target_user.first_name if target_user else f"المستخدم {target_user_id}"
            await message.reply(f"ℹ️ المستخدم {user_name} ليس لديه تحذيرات أو عقوبات")
            return
        
        # مسح التحذيرات
        success = await profanity_filter.reset_user_warnings(target_user_id, chat_id)
        
        if success:
            user_name = target_user.first_name if target_user else f"المستخدم {target_user_id}"
            response = f"""
✅ **تم مسح التحذيرات بنجاح**

👤 **المستخدم:** {user_name}
🔄 **ما تم مسحه:**
• التحذيرات: {current_warnings['warning_count']} ← 0
• العقوبات النشطة: {'نعم' if current_warnings['is_punished'] else 'لا'} ← لا

🎯 **النتيجة:** المستخدم أصبح نظيفاً من أي تحذيرات أو عقوبات
"""
            await message.reply(response)
            
            logging.info(f"تم مسح تحذيرات المستخدم {target_user_id} في المجموعة {chat_id} بواسطة {user_id}")
        else:
            await message.reply("❌ حدث خطأ أثناء مسح التحذيرات")
    
    except Exception as e:
        logging.error(f"خطأ في مسح تحذيرات المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح التحذيرات")


# قاموس الأوامر لسهولة التكامل
PROFANITY_COMMANDS = {
    "فعل الفلتر": enable_profanity_filter,
    "عطل الفلتر": disable_profanity_filter,
    "احصائيات الفلتر": profanity_filter_stats,
    "امسح تحذيرات": clear_user_warnings,
    
    # أوامر بديلة
    "تفعيل الفلتر": enable_profanity_filter,
    "تعطيل الفلتر": disable_profanity_filter,
    "فلتر الكلمات": profanity_filter_stats,
    "مسح التحذيرات": clear_user_warnings,
}


def get_profanity_help() -> str:
    """الحصول على نص المساعدة لأوامر الفلتر"""
    return """
🔍 **أوامر فلتر الألفاظ المسيئة**

🔧 **أوامر الإدارة:**
• `فعل الفلتر` - تفعيل فلتر الألفاظ المسيئة
• `عطل الفلتر` - تعطيل فلتر الألفاظ المسيئة
• `احصائيات الفلتر` - عرض إحصائيات النظام

🛠️ **أوامر التحكم:**
• `امسح تحذيرات` (بالرد على رسالة) - مسح تحذيرات عضو

⚡ **ميزات النظام:**
• حذف تلقائي للرسائل المسيئة
• نظام تحذيرات ذكي (3 تحذيرات حد أقصى)
• كتم تلقائي لمدة ساعة بعد التحذير الثالث
• حماية المشرفين والمالكين
• إنهاء العقوبات تلقائياً

🔒 **الصلاحيات:** المشرفين والمالكين والأسياد فقط
"""
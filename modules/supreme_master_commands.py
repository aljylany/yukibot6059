"""
أوامر السيد الأعلى الخاصة
Supreme Master Special Commands
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from config.hierarchy import is_supreme_master

# Router للأوامر الخاصة
router = Router()

# متغير عام لحالة تفعيل العقوبات على الأسياد
MASTERS_PUNISHMENT_ENABLED = False

def get_masters_punishment_status() -> bool:
    """الحصول على حالة تفعيل العقوبات على الأسياد"""
    return MASTERS_PUNISHMENT_ENABLED

def set_masters_punishment_status(enabled: bool) -> None:
    """تعيين حالة تفعيل العقوبات على الأسياد"""
    global MASTERS_PUNISHMENT_ENABLED
    MASTERS_PUNISHMENT_ENABLED = enabled
    logging.info(f"🔧 تم {'تفعيل' if enabled else 'تعطيل'} نظام العقوبات على الأسياد")

@router.message(F.text.in_(["تفعيل عقوبات الاسياد", "تفعيل العقوبات", "تفعيل العقوبة", "تفعيل العقود", "تفعيل_عقوبات_الاسياد", "تفعيل العقوبه", "تفعيل عقوبة الاسياد"]))
async def enable_masters_punishment(message: Message):
    """تفعيل نظام العقوبات على الأسياد الآخرين"""
    try:
        # التحقق من أن المرسل هو السيد الأعلى فقط
        if not message.from_user or not is_supreme_master(message.from_user.id):
            await message.reply("⛔ هذا الأمر متاح للسيد الأعلى فقط")
            return
        
        # تفعيل نظام العقوبات
        set_masters_punishment_status(True)
        
        response = (
            "🔥 **تم تفعيل نظام العقوبات على الأسياد**\n\n"
            "⚠️ **تحذير هام:**\n"
            "• الأسياد الآخرين سيُعاملون كأعضاء عاديين\n"
            "• سيتم تطبيق العقوبات الكاملة عليهم (كتم، بان، إلخ)\n"
            "• أنت (السيد الأعلى) محمي دائماً\n\n"
            "🛠️ **للإلغاء:** استخدم الأمر `الغاء العقوبات`\n\n"
            "👑 **السيد الأعلى:** أنت الوحيد المحمي من جميع الأنظمة"
        )
        
        await message.reply(response, parse_mode="Markdown")
        logging.warning(f"👑 السيد الأعلى {message.from_user.id} فعل نظام العقوبات على الأسياد")
        
    except Exception as e:
        logging.error(f"خطأ في تفعيل عقوبات الأسياد: {e}")
        await message.reply("❌ حدث خطأ في تفعيل النظام")

@router.message(F.text.in_(["الغاء عقوبات الاسياد", "الغاء العقوبات", "تعطيل العقوبات", "الغاء_عقوبات_الاسياد"]))
async def disable_masters_punishment(message: Message):
    """إلغاء تفعيل نظام العقوبات على الأسياد"""
    try:
        # التحقق من أن المرسل هو السيد الأعلى فقط
        if not message.from_user or not is_supreme_master(message.from_user.id):
            await message.reply("⛔ هذا الأمر متاح للسيد الأعلى فقط")
            return
        
        # إلغاء تفعيل نظام العقوبات
        set_masters_punishment_status(False)
        
        response = (
            "✅ **تم إلغاء نظام العقوبات على الأسياد**\n\n"
            "🛡️ **الوضع الحالي:**\n"
            "• الأسياد عادوا للحماية الكاملة\n"
            "• لا توجد عقوبات على الأسياد الآخرين\n"
            "• النظام يعمل في الوضع العادي\n\n"
            "👑 **أنت محمي دائماً** كالسيد الأعلى"
        )
        
        await message.reply(response, parse_mode="Markdown")
        logging.warning(f"👑 السيد الأعلى {message.from_user.id} ألغى نظام العقوبات على الأسياد")
        
    except Exception as e:
        logging.error(f"خطأ في إلغاء عقوبات الأسياد: {e}")
        await message.reply("❌ حدث خطأ في إلغاء النظام")

@router.message(F.text.in_(["حالة الاسياد", "حالة العقوبات", "وضع الاسياد", "حالة_الاسياد"]))
async def check_masters_status(message: Message):
    """فحص حالة نظام العقوبات على الأسياد"""
    try:
        # التحقق من أن المرسل هو السيد الأعلى فقط
        if not message.from_user or not is_supreme_master(message.from_user.id):
            await message.reply("⛔ هذا الأمر متاح للسيد الأعلى فقط")
            return
        
        current_status = get_masters_punishment_status()
        
        if current_status:
            response = (
                "🔥 **نظام العقوبات مُفعل**\n\n"
                "⚠️ **الوضع الحالي:**\n"
                "• الأسياد الآخرين يُعاملون كأعضاء عاديين\n"
                "• العقوبات مُفعلة عليهم (كتم، بان، إلخ)\n"
                "• السيد الأعلى محمي دائماً\n\n"
                "🛑 للإلغاء: `الغاء العقوبات`"
            )
        else:
            response = (
                "🛡️ **نظام العقوبات غير مُفعل**\n\n"
                "✅ **الوضع الحالي:**\n"
                "• الأسياد محميين من جميع العقوبات\n"
                "🔥 للتفعيل: `تفعيل العقوبات`"
            )
        
        await message.reply(response, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"خطأ في فحص حالة الأسياد: {e}")
        await message.reply("❌ حدث خطأ في فحص الحالة")

# إضافة أمر لقراءة ملف الأوامر
@router.message(F.text.in_(["اوامر النظام الجديد", "أوامر النظام الجديد", "الاوامر الجديدة", "الأوامر الجديدة"]))
async def show_new_system_commands(message: Message):
    """عرض أوامر النظام الجديد للسيد الأعلى"""
    try:
        if not message.from_user or not is_supreme_master(message.from_user.id):
            await message.reply("⛔ هذا الأمر متاح للسيد الأعلى فقط")
            return
        
        new_commands_info = (
            "👑 **أوامر النظام الجديد - السيد الأعلى فقط**\n\n"
            "🔧 **التحكم في عقوبات الأسياد:**\n"
            "• `تفعيل العقوبات` - تفعيل العقوبات على الأسياد الآخرين\n"
            "• `الغاء العقوبات` - إلغاء العقوبات وإرجاع الحماية\n"
            "• `حالة العقوبات` - فحص الحالة الحالية\n"
            "• `وضع الاسياد` - عرض وضع الأسياد\n\n"
            "📋 **الأوامر البديلة:**\n"
            "• `تفعيل عقوبات الاسياد`\n"
            "• `الغاء عقوبات الاسياد`\n"
            "• `تعطيل العقوبات`\n"
            "• `حالة الاسياد`\n\n"
            "⚠️ **تحذير:** عند تفعيل العقوبات، الأسياد الآخرين سيُعاملون كأعضاء عاديين!\n"
            "👑 **أنت محمي دائماً** كالسيد الأعلى من جميع الأنظمة"
        )
        
        await message.reply(new_commands_info, parse_mode="Markdown")
        
    except Exception as e:
        logging.error(f"خطأ في عرض أوامر النظام الجديد: {e}")
        await message.reply("❌ حدث خطأ في عرض الأوامر")
"""
معالج المحتوى الشامل والمتقدم
Comprehensive Content Handler
"""

import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from modules.comprehensive_content_filter import (
    comprehensive_filter, 
    ViolationType, 
    SeverityLevel, 
    PunishmentAction
)
from modules.admin_reports_system import admin_reports
from config.hierarchy import is_master, is_supreme_master
from utils.decorators import group_only

router = Router()

class ComprehensiveContentHandler:
    """معالج المحتوى الشامل"""
    
    def __init__(self):
        self.filter = comprehensive_filter
        self.reports_system = admin_reports
        self.processing_lock = {}  # لمنع المعالجة المتكررة
    
    async def process_message_content(self, message: Message) -> bool:
        """
        معالجة شاملة لمحتوى الرسالة
        Returns True إذا تم العثور على مخالفات وتمت معالجتها
        """
        try:
            # منع المعالجة المتكررة للرسالة نفسها
            message_key = f"{message.chat.id}:{message.message_id}"
            if message_key in self.processing_lock:
                return False
            
            self.processing_lock[message_key] = True
            
            try:
                # التحقق من أن الرسالة في مجموعة
                if message.chat.type not in ['group', 'supergroup']:
                    return False
                
                # استثناء الأسياد من الفحص
                if is_supreme_master(message.from_user.id) or is_master(message.from_user.id):
                    return False
                
                # الفحص الشامل للمحتوى
                logging.info(f"🔍 بدء الفحص الشامل للمحتوى من المستخدم {message.from_user.id}")
                
                # تسجيل تفاصيل المحتوى
                content_details = []
                if message.text:
                    content_details.append(f"نص: '{message.text[:50]}{'...' if len(message.text) > 50 else ''}'")
                if message.photo:
                    content_details.append("صورة")
                if message.video:
                    content_details.append("فيديو")
                if message.sticker:
                    content_details.append(f"ملصق: {message.sticker.emoji or 'غير محدد'}")
                if message.animation:
                    content_details.append("رسم متحرك")
                if message.document:
                    content_details.append(f"ملف: {message.document.file_name or 'غير محدد'}")
                
                if content_details:
                    logging.info(f"📋 المحتوى المراد فحصه: {' | '.join(content_details)}")
                
                check_result = await self.filter.comprehensive_content_check(message)
                
                if not check_result['has_violations']:
                    logging.info(f"✅ المحتوى نظيف - لا توجد مخالفات")
                    return False
                
                logging.warning(
                    f"🚨 تم اكتشاف مخالفات من المستخدم {message.from_user.id} "
                    f"في المجموعة {message.chat.id}: {len(check_result['violations'])} مخالفة"
                )
                
                # تسجيل تفاصيل كل مخالفة
                for i, violation in enumerate(check_result['violations'], 1):
                    logging.warning(
                        f"📝 مخالفة {i}: {violation['violation_type']} "
                        f"(خطورة: {violation['severity']}) - {violation.get('content_summary', 'غير محدد')}"
                    )
                
                # تطبيق العقوبة
                punishment_result = await self.filter.apply_punishment(
                    message, 
                    check_result['recommended_action'],
                    check_result['violations']
                )
                
                # إنشاء تقرير للمشرفين
                if check_result['admin_notification_required']:
                    report_id = await self.reports_system.generate_violation_report(
                        message,
                        check_result['violations'],
                        check_result['recommended_action'].value,
                        ai_data={
                            'total_severity': check_result['total_severity'],
                            'violations_count': len(check_result['violations'])
                        }
                    )
                    
                    # إرسال تنبيه فوري للمشرفين
                    await self.reports_system.send_instant_admin_alert(
                        message.bot, 
                        message.chat.id, 
                        report_id
                    )
                
                # تسجيل النتيجة
                if punishment_result['success']:
                    logging.info(f"✅ تم تطبيق العقوبة بنجاح: {punishment_result['action_taken']}")
                else:
                    logging.warning(f"⚠️ فشل في تطبيق العقوبة: {punishment_result.get('message_sent', 'خطأ غير محدد')}")
                
                return True
                
            finally:
                # إزالة القفل
                self.processing_lock.pop(message_key, None)
                
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة المحتوى الشامل: {e}")
            return False
    
    async def get_user_status(self, user_id: int, chat_id: int) -> dict:
        """الحصول على حالة المستخدم ومخالفاته"""
        try:
            return await self.filter.get_user_violations_summary(user_id, chat_id)
        except Exception as e:
            logging.error(f"❌ خطأ في جلب حالة المستخدم: {e}")
            return {}
    
    async def handle_admin_report_callback(self, callback_query: CallbackQuery):
        """معالجة ردود المشرفين على التقارير"""
        try:
            await self.reports_system.handle_report_callback(callback_query, callback_query.bot)
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة رد المشرف: {e}")
            await callback_query.answer("❌ حدث خطأ في معالجة الطلب")

# إنشاء معالج المحتوى الشامل
comprehensive_handler = ComprehensiveContentHandler()

# معالجات الرسائل المختلفة
@router.message(F.photo)
@group_only
async def handle_photo_content(message: Message):
    """معالج الصور"""
    await comprehensive_handler.process_message_content(message)

@router.message(F.video)
@group_only
async def handle_video_content(message: Message):
    """معالج الفيديوهات"""
    await comprehensive_handler.process_message_content(message)

@router.message(F.sticker)
@group_only
async def handle_sticker_content(message: Message):
    """معالج الملصقات"""
    await comprehensive_handler.process_message_content(message)

@router.message(F.animation)
@group_only
async def handle_animation_content(message: Message):
    """معالج الرسوم المتحركة"""
    await comprehensive_handler.process_message_content(message)

@router.message(F.document)
@group_only
async def handle_document_content(message: Message):
    """معالج الملفات"""
    await comprehensive_handler.process_message_content(message)

# معالج الاستجابات للتقارير
@router.callback_query(F.data.startswith('report_'))
async def handle_report_callbacks(callback_query: CallbackQuery):
    """معالج ردود المشرفين على التقارير"""
    await comprehensive_handler.handle_admin_report_callback(callback_query)

# معالج الرسائل النصية المحسن (يتكامل مع النظام الموجود)
async def enhanced_text_content_check(message: Message) -> bool:
    """
    فحص محسن للمحتوى النصي - يعمل مع النظام الموجود
    """
    try:
        # استخدام النظام الشامل للفحص النصي المحسن
        result = await comprehensive_handler.process_message_content(message)
        return result
        
    except Exception as e:
        logging.error(f"❌ خطأ في الفحص النصي المحسن: {e}")
        return False

# دالة مساعدة للتكامل مع المعالجات الموجودة
async def integrate_with_existing_handlers(message: Message) -> bool:
    """
    دمج النظام الشامل مع المعالجات الموجودة
    """
    try:
        # فحص شامل لكل أنواع المحتوى
        has_violations = await comprehensive_handler.process_message_content(message)
        
        if has_violations:
            # إذا وُجدت مخالفات، إنهاء المعالجة هنا
            return True
        
        # إذا لم توجد مخالفات، السماح للمعالجات الأخرى بالاستمرار
        return False
        
    except Exception as e:
        logging.error(f"❌ خطأ في التكامل مع المعالجات: {e}")
        return False

# دوال مساعدة للأوامر الإدارية
async def get_comprehensive_group_stats(chat_id: int) -> str:
    """الحصول على إحصائيات شاملة للمجموعة"""
    try:
        # إنشاء ملخص شامل للمجموعة
        daily_summary = await admin_reports.generate_daily_summary(chat_id)
        return daily_summary
        
    except Exception as e:
        logging.error(f"❌ خطأ في جلب إحصائيات المجموعة: {e}")
        return "❌ حدث خطأ في جلب الإحصائيات"

async def get_user_comprehensive_report(user_id: int, chat_id: int) -> str:
    """الحصول على تقرير شامل للمستخدم"""
    try:
        user_summary = await comprehensive_filter.get_user_violations_summary(user_id, chat_id)
        
        if not user_summary or user_summary['total_violations'] == 0:
            return "👤 المستخدم ليس له سجل مخالفات"
        
        report = f"👤 **تقرير المستخدم الشامل**\n\n"
        report += f"📊 **إجمالي المخالفات:** {user_summary['total_violations']}\n"
        report += f"📈 **إجمالي درجات الخطورة:** {user_summary['total_severity']}\n"
        report += f"🎯 **النقاط التراكمية:** {user_summary['current_points']}\n"
        report += f"⚖️ **مستوى العقوبة:** {user_summary['punishment_level']}\n"
        
        if user_summary['is_permanently_banned']:
            report += f"🚫 **الحالة:** محظور نهائياً\n"
        
        if user_summary['recent_violations']:
            report += f"\n📋 **آخر المخالفات:**\n"
            for violation in user_summary['recent_violations'][:3]:
                report += f"• {violation['type']} (خطورة: {violation['severity']})\n"
        
        return report
        
    except Exception as e:
        logging.error(f"❌ خطأ في إنشاء تقرير المستخدم: {e}")
        return "❌ حدث خطأ في إنشاء التقرير"

# دالة لتفعيل/تعطيل النظام الشامل
async def toggle_comprehensive_system(chat_id: int, enabled: bool) -> str:
    """تفعيل أو تعطيل النظام الشامل"""
    try:
        comprehensive_filter.enabled = enabled
        
        status = "مفعل" if enabled else "معطل"
        return f"✅ تم {status} النظام الشامل لكشف المحتوى"
        
    except Exception as e:
        logging.error(f"❌ خطأ في تغيير حالة النظام: {e}")
        return "❌ حدث خطأ في تغيير حالة النظام"

# دالة لاشتراك المشرف في التقارير
async def subscribe_admin_to_comprehensive_reports(admin_id: int, chat_id: int, 
                                                 report_types: list = None) -> str:
    """اشتراك المشرف في التقارير الشاملة"""
    try:
        if report_types is None:
            report_types = ['instant_alerts', 'daily_summary']
        
        await admin_reports.subscribe_admin_to_reports(admin_id, chat_id, report_types)
        
        return f"✅ تم اشتراكك في تقارير النظام الشامل: {', '.join(report_types)}"
        
    except Exception as e:
        logging.error(f"❌ خطأ في اشتراك المشرف: {e}")
        return "❌ حدث خطأ في عملية الاشتراك"

# دالة للحصول على تقرير حالة النظام
async def get_system_status() -> str:
    """الحصول على حالة النظام الشامل"""
    try:
        status_report = f"🔍 **حالة النظام الشامل**\n\n"
        
        # حالة التفعيل
        if comprehensive_filter.enabled:
            status_report += f"✅ **النظام:** مفعل ويعمل\n"
        else:
            status_report += f"❌ **النظام:** معطل\n"
        
        # حالة الذكاء الاصطناعي
        if comprehensive_filter.model:
            status_report += f"🧠 **الذكاء الاصطناعي:** متصل\n"
        else:
            status_report += f"⚠️ **الذكاء الاصطناعي:** غير متوفر\n"
        
        # عدد مفاتيح API
        status_report += f"🔑 **مفاتيح API:** {len(comprehensive_filter.api_keys)}\n"
        
        # أنواع الفحص المتاحة
        status_report += f"\n🔍 **أنواع الفحص المتاحة:**\n"
        status_report += f"• فحص النصوص والسباب ✅\n"
        status_report += f"• فحص السياق الجنسي ✅\n"
        status_report += f"• فحص الصور بالذكاء الاصطناعي {'✅' if comprehensive_filter.model else '❌'}\n"
        status_report += f"• فحص الملصقات ✅\n"
        status_report += f"• فحص الفيديوهات {'✅' if comprehensive_filter.model else '⚠️'}\n"
        status_report += f"• فحص الملفات ✅\n"
        
        status_report += f"\n⚖️ **نظام العقوبات:** متدرج من التحذير إلى الطرد النهائي\n"
        status_report += f"📊 **نظام التقارير:** مفعل للمشرفين\n"
        
        return status_report
        
    except Exception as e:
        logging.error(f"❌ خطأ في جلب حالة النظام: {e}")
        return "❌ حدث خطأ في جلب حالة النظام"

# تصدير الوظائف المهمة
__all__ = [
    'comprehensive_handler',
    'enhanced_text_content_check',
    'integrate_with_existing_handlers',
    'get_comprehensive_group_stats',
    'get_user_comprehensive_report',
    'toggle_comprehensive_system',
    'subscribe_admin_to_comprehensive_reports',
    'get_system_status'
]
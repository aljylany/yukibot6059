"""
معالج الرسائل الموحد - Unified Message Processor
نظام موحد لمعالجة جميع أنواع الرسائل مع ضمان مرور كل شيء عبر نظام الكشف
"""

import logging
import asyncio
from aiogram import Router, F
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import TelegramBadRequest
from datetime import datetime, timedelta

from config.hierarchy import is_master, is_supreme_master
from modules.supreme_master_commands import get_masters_punishment_status
from utils.decorators import group_only
from modules.comprehensive_content_filter import comprehensive_filter, ViolationType, SeverityLevel
from modules.admin_reports_system import admin_reports

router = Router()

class UnifiedMessageProcessor:
    """معالج الرسائل الموحد - يضمن معالجة كل رسالة"""
    
    def __init__(self):
        self.filter = comprehensive_filter
        self.reports = admin_reports
        self.processing_lock = {}  # لمنع المعالجة المتكررة
        
    async def process_any_message(self, message: Message) -> bool:
        """
        معالج موحد لجميع أنواع الرسائل
        Returns True إذا تم العثور على مخالفات
        """
        try:
            # منع المعالجة المتكررة
            message_key = f"{message.chat.id}:{message.message_id}"
            if message_key in self.processing_lock:
                return False
            
            self.processing_lock[message_key] = True
            
            try:
                # التحقق من أن الرسالة في مجموعة
                if message.chat.type not in ['group', 'supergroup']:
                    return False
                
                # التحقق من وجود معلومات المستخدم
                if not message.from_user:
                    return False
                
                # التحقق من حالة الكتم الفعلية للمستخدم في التيليجرام أولاً
                from modules.profanity_filter import is_user_actually_muted
                user_is_muted = await is_user_actually_muted(message.bot, message.chat.id, message.from_user.id)
                
                # إذا كان المستخدم غير مكتوم ولم يرسل سباب، لا نحذف رسائله
                if not user_is_muted:
                    # للمستخدمين غير المكتومين، نفحص السباب فقط
                    logging.info(f"✅ المستخدم {message.from_user.id} غير مكتوم - سيتم فحص السباب فقط")
                else:
                    logging.info(f"🔇 المستخدم {message.from_user.id} مكتوم فعلياً في التيليجرام")
                
                # السيد الأعلى محمي دائماً من جميع أنواع الفحص
                if is_supreme_master(message.from_user.id):
                    logging.info(f"👑 تم استثناء السيد الأعلى {message.from_user.id} من الفحص (حماية مطلقة)")
                    return False
                
                # فحص حالة تفعيل العقوبات على الأسياد من النظام الجديد
                masters_punishment_enabled = get_masters_punishment_status()
                
                # فحص خاص: إذا كانت الرسالة تحتوي على "اختبار النظام" فالأسياد الآخرين يتم فحصهم
                is_testing = message.text and "اختبار النظام" in message.text
                
                # استثناء الأسياد الآخرين من الفحص (إلا في حالة الاختبار أو إذا كان نظام العقوبات مفعل)
                if not is_testing and not masters_punishment_enabled and is_master(message.from_user.id):
                    logging.info(f"🔓 تم استثناء السيد {message.from_user.id} من الفحص (العقوبات معطلة)")
                    return False
                
                # إذا كان نظام العقوبات مفعل على الأسياد، سجل ذلك
                if (masters_punishment_enabled or is_testing) and is_master(message.from_user.id):
                    status_msg = "نظام العقوبات مفعل" if masters_punishment_enabled else "وضع اختبار"
                    logging.warning(f"🔥 {status_msg} - سيتم فحص السيد {message.from_user.id} كعضو عادي")
                
                # تسجيل تفاصيل الرسالة
                content_type = self._get_content_type(message)
                user_name = message.from_user.first_name or "مجهول"
                
                logging.info(f"🔍 فحص {content_type} من {user_name} (ID: {message.from_user.id})")
                
                # للمستخدمين غير المكتومين: فحص السباب فقط
                if not user_is_muted:
                    if message.text:
                        from modules.profanity_filter import handle_profanity_detection
                        profanity_detected = await handle_profanity_detection(message)
                        if profanity_detected:
                            logging.info("✅ تم التعامل مع السباب من مستخدم غير مكتوم")
                            return True
                        else:
                            # رسالة عادية من مستخدم غير مكتوم - لا نحذفها
                            return False
                    else:
                        # محتوى غير نصي من مستخدم غير مكتوم - نفحصه للمحتوى المسيء فقط
                        check_result = await self.filter.comprehensive_content_check(message)
                        if check_result['has_violations']:
                            # حذف المحتوى المسيء من مستخدم غير مكتوم
                            logging.warning(f"🚨 محتوى مسيء من مستخدم غير مكتوم - سيتم التعامل معه")
                            # نكمل المعالجة أدناه
                        else:
                            return False
                else:
                    # المستخدم مكتوم - نطبق جميع الفحوصات
                    if message.text:
                        from modules.profanity_filter import handle_profanity_detection
                        profanity_detected = await handle_profanity_detection(message)
                        if profanity_detected:
                            logging.info("✅ تم التعامل مع السباب من مستخدم مكتوم")
                            return True
                    
                    # الفحص الشامل للمحتويات الأخرى
                    check_result = await self.filter.comprehensive_content_check(message)
                    
                    if not check_result['has_violations']:
                        # حتى لو لم يكن هناك مخالفات، المستخدم مكتوم - لا يجب أن يرسل رسائل
                        logging.info(f"🔇 رسالة من مستخدم مكتوم - سيتم حذفها")
                        try:
                            await message.delete()
                            logging.info("🗑️ تم حذف رسالة من مستخدم مكتوم")
                        except Exception as delete_error:
                            logging.warning(f"⚠️ لم يتمكن من حذف رسالة من مستخدم مكتوم: {delete_error}")
                        return True
                
                # إذا وصلنا هنا، فهناك مخالفات تحتاج للمعالجة
                if not hasattr(locals(), 'check_result') or not check_result.get('has_violations'):
                    return False
                
                violations_count = len(check_result['violations'])
                logging.warning(
                    f"🚨 اكتشاف {violations_count} مخالفة من {user_name} "
                    f"في المجموعة {message.chat.title or message.chat.id}"
                )
                
                # تسجيل تفاصيل المخالفات
                for i, violation in enumerate(check_result['violations'], 1):
                    logging.warning(
                        f"📝 مخالفة {i}: {violation['violation_type']} "
                        f"(خطورة: {violation['severity']}) - {violation.get('content_summary', 'غير محدد')}"
                    )
                
                # حذف الرسالة المخالفة فوراً
                try:
                    await message.delete()
                    logging.info("🗑️ تم حذف الرسالة المخالفة")
                except Exception as delete_error:
                    logging.warning(f"⚠️ لم يتمكن من حذف الرسالة: {delete_error}")
                
                # تطبيق العقوبة
                punishment_result = await self.filter.apply_punishment(
                    message, 
                    check_result['recommended_action'],
                    check_result['violations']
                )
                
                # إرسال رسالة تحذيرية
                await self._send_warning_message(
                    message, 
                    check_result, 
                    punishment_result
                )
                
                # إنشاء تقرير للمشرفين إذا لزم الأمر
                if check_result['admin_notification_required']:
                    await self._create_admin_report(message, check_result)
                
                return True
                
            finally:
                # إزالة القفل
                self.processing_lock.pop(message_key, None)
                
        except Exception as e:
            logging.error(f"❌ خطأ في المعالج الموحد: {e}")
            return False
    
    def _get_content_type(self, message: Message) -> str:
        """تحديد نوع المحتوى"""
        if message.text:
            return "نص"
        elif message.photo:
            return "صورة"
        elif message.video:
            return "فيديو"
        elif message.sticker:
            return "ملصق"
        elif message.animation:
            return "رسم متحرك"
        elif message.document:
            return "ملف"
        elif message.voice:
            return "رسالة صوتية"
        elif message.video_note:
            return "فيديو دائري"
        else:
            return "محتوى غير معروف"
    
    async def _send_warning_message(self, message: Message, check_result: dict, punishment_result: dict):
        """إرسال رسالة تحذيرية"""
        try:
            user_name = (message.from_user.first_name if message.from_user else None) or "المستخدم"
            violations_count = len(check_result['violations'])
            total_severity = check_result['total_severity']
            
            # تحديد مستوى التحذير
            if total_severity <= 2:
                warning_level = "⚠️ تحذير خفيف"
                emoji = "🟡"
            elif total_severity <= 4:
                warning_level = "🔴 تحذير متوسط"
                emoji = "🔴"
            elif total_severity <= 6:
                warning_level = "🚨 تحذير شديد"
                emoji = "🚨"
            else:
                warning_level = "💀 تحذير خطير"
                emoji = "💀"
            
            warning_message = (
                f"{emoji} **{warning_level}**\n\n"
                f"👤 **المستخدم:** {user_name}\n"
                f"🔢 **عدد المخالفات:** {violations_count}\n"
                f"📊 **مستوى الخطورة:** {total_severity}\n"
                f"⚡ **الإجراء:** {punishment_result.get('action_taken', 'غير محدد')}\n\n"
                f"🛡️ **نظام الحماية المتطور**\n"
                f"💡 يرجى الالتزام بقوانين المجموعة"
            )
            
            await message.answer(warning_message, parse_mode="Markdown")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال رسالة التحذير: {e}")
    
    async def _create_admin_report(self, message: Message, check_result: dict):
        """إنشاء تقرير للمشرفين"""
        try:
            report_id = await self.reports.generate_violation_report(
                message,
                check_result['violations'],
                check_result['recommended_action'].value,
                ai_data={
                    'total_severity': check_result['total_severity'],
                    'violations_count': len(check_result['violations'])
                }
            )
            
            # إرسال تنبيه فوري للمشرفين
            if message.bot:
                await self.reports.send_instant_admin_alert(
                    message.bot, 
                    message.chat.id, 
                    report_id
                )
            
            logging.info(f"📊 تم إنشاء تقرير للمشرفين: {report_id}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء تقرير المشرفين: {e}")

# إنشاء المعالج الموحد
unified_processor = UnifiedMessageProcessor()

# معالجات لجميع أنواع الرسائل
@router.message(F.text)
@group_only
async def handle_text_messages(message: Message):
    """معالج الرسائل النصية"""
    # تحقق من رسائل يوكي الذكي - لا تعالجها هنا
    if message.text:
        yuki_triggers = ['يوكي', 'yuki', 'يوكى']
        if any(trigger in message.text.lower() for trigger in yuki_triggers):
            # اترك رسائل يوكي للمعالج المخصص في messages.py
            return
    
    await unified_processor.process_any_message(message)

@router.message(F.photo)
@group_only
async def handle_photo_messages(message: Message):
    """معالج الصور"""
    await unified_processor.process_any_message(message)

@router.message(F.video)
@group_only
async def handle_video_messages(message: Message):
    """معالج الفيديوهات"""
    await unified_processor.process_any_message(message)

@router.message(F.sticker)
@group_only
async def handle_sticker_messages(message: Message):
    """معالج الملصقات"""
    await unified_processor.process_any_message(message)

@router.message(F.animation)
@group_only
async def handle_animation_messages(message: Message):
    """معالج الرسوم المتحركة"""
    await unified_processor.process_any_message(message)

@router.message(F.document)
@group_only
async def handle_document_messages(message: Message):
    """معالج الملفات"""
    await unified_processor.process_any_message(message)

@router.message(F.voice)
@group_only
async def handle_voice_messages(message: Message):
    """معالج الرسائل الصوتية"""
    await unified_processor.process_any_message(message)

@router.message(F.video_note)
@group_only
async def handle_video_note_messages(message: Message):
    """معالج الفيديوهات الدائرية"""
    await unified_processor.process_any_message(message)

# معالج شامل لأي رسالة لم تتم معالجتها
@router.message()
@group_only
async def handle_any_other_message(message: Message):
    """معالج شامل لأي نوع رسالة أخرى"""
    await unified_processor.process_any_message(message)

# دالة للتكامل مع الأنظمة الأخرى
async def check_message_unified(message: Message) -> bool:
    """
    دالة موحدة لفحص الرسائل - للاستخدام من الأنظمة الأخرى
    Returns True إذا تم اكتشاف مخالفات
    """
    return await unified_processor.process_any_message(message)
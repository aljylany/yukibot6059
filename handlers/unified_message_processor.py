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
                
                # استثناء الأسياد من الفحص
                if is_supreme_master(message.from_user.id) or is_master(message.from_user.id):
                    logging.info(f"🔓 تم استثناء السيد {message.from_user.id} من الفحص")
                    return False
                
                # تسجيل تفاصيل الرسالة
                content_type = self._get_content_type(message)
                user_name = message.from_user.first_name or "مجهول"
                
                logging.info(f"🔍 فحص {content_type} من {user_name} (ID: {message.from_user.id})")
                
                # فحص سريع للكلمات المسيئة في النص
                if message.text:
                    banned_words = [
                        "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
                        "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
                        "ابن الشرموطة", "بنت الشرموطة", "خرا", "خراء", "يلعن", "اللعنة",
                        "منيوك", "ايري", "انيك", "نيكك", "منيوكة", "ايرك", "ايرها",
                        "انيكك", "انيكها", "منيوكو", "ايرو", "نيكو", "كسمك", "كسك",
                        "عرص", "عرصة", "قحبة", "قحبه", "بغي", "بغيه", "متناك", "متناكة"
                    ]
                    
                    text_lower = message.text.lower()
                    found_violations = []
                    
                    for word in banned_words:
                        if word in text_lower:
                            found_violations.append({
                                'violation_type': 'text_profanity',
                                'severity': 3,
                                'content_summary': f'كلمة مسيئة: {word}'
                            })
                            logging.warning(f"🚨 تم اكتشاف كلمة مسيئة: {word}")
                    
                    if found_violations:
                        # حذف الرسالة فوراً
                        try:
                            await message.delete()
                            logging.info("🗑️ تم حذف الرسالة المخالفة")
                        except Exception as delete_error:
                            logging.warning(f"⚠️ لم يتمكن من حذف الرسالة: {delete_error}")
                        
                        # إرسال رسالة تحذيرية
                        warning_message = (
                            f"🚨 **تحذير شديد**\n\n"
                            f"👤 **المستخدم:** {user_name}\n"
                            f"🔢 **عدد المخالفات:** {len(found_violations)}\n"
                            f"⚡ **الإجراء:** تم حذف الرسالة\n\n"
                            f"🛡️ **نظام الحماية المتطور**\n"
                            f"💡 يرجى الالتزام بقوانين المجموعة واستخدام لغة مهذبة"
                        )
                        
                        await message.answer(warning_message, parse_mode="Markdown")
                        return True
                
                # الفحص الشامل للمحتويات الأخرى
                check_result = await self.filter.comprehensive_content_check(message)
                
                if not check_result['has_violations']:
                    logging.info(f"✅ المحتوى نظيف - لا توجد مخالفات")
                    return False
                
                # تم اكتشاف مخالفات
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
            user_name = message.from_user.first_name or "المستخدم"
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
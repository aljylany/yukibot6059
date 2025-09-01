"""
معالج الرسائل الموحد - Unified Message Processor
نظام موحد لمعالجة جميع أنواع الرسائل
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from utils.decorators import group_only
from modules.media_analyzer import media_analyzer
from modules.content_moderation import ContentModerator

router = Router()

class UnifiedMessageProcessor:
    """معالج الرسائل الموحد - معالجة بسيطة للرسائل"""
    
    def __init__(self):
        self.processing_lock = {}  # لمنع المعالجة المتكررة
        self.content_moderator = ContentModerator()
        
    async def process_any_message(self, message: Message) -> bool:
        """
        معالج موحد لجميع أنواع الرسائل
        Returns False - لا يوجد فحص حاليا
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
                
                # تسجيل تفاصيل الرسالة
                content_type = self._get_content_type(message)
                user_name = message.from_user.first_name or "مجهول"
                
                logging.info(f"📝 رسالة {content_type} من {user_name} (ID: {message.from_user.id})")
                
                # تحليل المحتوى إذا كان صورة أو فيديو
                if message.photo or message.video or message.document:
                    return await self._analyze_media_content(message)
                
                # لباقي الرسائل - السماح بجميع الرسائل
                return False
                
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
    
    async def _analyze_media_content(self, message: Message) -> bool:
        """تحليل محتوى الوسائط"""
        try:
            # إرسال رسالة انتظار
            loading_message = await message.reply("🔍 **جاري تحليل الملف...**")
            
            # تحديد نوع الملف وتحميله
            file_id = None
            file_name = "unknown"
            media_type = None
            
            if message.photo:
                file_id = message.photo[-1].file_id
                file_name = f"photo_{message.message_id}.jpg"
                media_type = "photo"
            elif message.video:
                file_id = message.video.file_id
                file_name = f"video_{message.message_id}.mp4"
                media_type = "video"
            elif message.document:
                file_id = message.document.file_id
                file_name = message.document.file_name or f"document_{message.message_id}"
                media_type = "document"
            
            if not file_id:
                await loading_message.delete()
                return False
            
            # تحميل الملف
            file_path = await media_analyzer.download_media_file(
                message.bot, file_id, file_name
            )
            
            if not file_path:
                await loading_message.edit_text("❌ فشل في تحميل الملف")
                return False
            
            # تحليل المحتوى
            analysis_result = None
            
            if media_type == "photo":
                analysis_result = await media_analyzer.analyze_image_content(file_path)
            elif media_type == "video":
                analysis_result = await media_analyzer.analyze_video_content(file_path)
            elif media_type == "document":
                analysis_result = await media_analyzer.analyze_document_content(file_path)
            
            # حذف الملف المؤقت
            await media_analyzer.cleanup_temp_file(file_path)
            
            # معالجة نتيجة التحليل
            if analysis_result and not analysis_result.get("error"):
                is_safe = analysis_result.get("is_safe", True)
                
                if not is_safe:
                    # محتوى مخالف - حذف الملف وإرسال تحذير
                    violations = analysis_result.get("violations", [])
                    severity = analysis_result.get("severity", "medium")
                    
                    # حذف الرسالة المخالفة
                    try:
                        await message.delete()
                    except:
                        pass
                    
                    # رسالة تحذير
                    warning_msg = f"⚠️ **تم اكتشاف محتوى مخالف!**\n\n"
                    warning_msg += f"👤 **المستخدم:** {message.from_user.first_name}\n"
                    warning_msg += f"📋 **نوع المخالفة:** {', '.join(violations)}\n"
                    warning_msg += f"⚖️ **درجة الخطورة:** {severity}\n"
                    warning_msg += f"🗑️ **تم حذف الملف تلقائياً**"
                    
                    await loading_message.edit_text(warning_msg)
                    
                    # إشعار المشرفين
                    await self.content_moderator.notify_authorities(message, analysis_result)
                    
                    # تسجيل المخالفة
                    await self.content_moderator.log_violation(message, analysis_result)
                    
                    return True  # تم حذف المحتوى
                else:
                    # محتوى آمن - عرض الوصف
                    description = analysis_result.get("description", "محتوى آمن")
                    confidence = analysis_result.get("confidence", 0.8)
                    gesture_analysis = analysis_result.get("gesture_analysis", "")
                    
                    safe_msg = f"✅ **تحليل المحتوى:**\n\n"
                    safe_msg += f"📝 **الوصف:** {description}\n"
                    if gesture_analysis:
                        safe_msg += f"🤲 **تحليل الإيماءات:** {gesture_analysis}\n"
                    safe_msg += f"🎯 **درجة الثقة:** {confidence:.0%}\n"
                    safe_msg += f"✅ **النتيجة:** محتوى آمن"
                    
                    await loading_message.edit_text(safe_msg)
                    
                    return False  # محتوى آمن
            else:
                await loading_message.edit_text("❌ فشل في تحليل المحتوى")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل المحتوى: {e}")
            try:
                await loading_message.edit_text("❌ حدث خطأ أثناء تحليل المحتوى")
            except:
                pass
            return False

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
    Returns False - لا يوجد فحص حاليا
    """
    return await unified_processor.process_any_message(message)
"""
معالج الرسائل الموحد - Unified Message Processor
نظام موحد لمعالجة جميع أنواع الرسائل
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from utils.decorators import group_only

router = Router()

class UnifiedMessageProcessor:
    """معالج الرسائل الموحد - معالجة بسيطة للرسائل"""
    
    def __init__(self):
        self.processing_lock = {}  # لمنع المعالجة المتكررة
        
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
                
                # لا يوجد فحص - السماح بجميع الرسائل
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
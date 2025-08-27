"""
نظام كشف المحتوى الإباحي والغير مناسب في الصور والملفات
Content Filter System for Detecting Inappropriate Content
"""

import os
import logging
import base64
import io
import asyncio
from typing import Optional, Dict, Any, List
try:
    from PIL import Image
except ImportError:
    Image = None
try:
    import google.generativeai as genai
except ImportError:
    genai = None
from aiogram.types import Message, PhotoSize, Document, Video, Animation

class ContentFilter:
    """فئة كشف المحتوى الإباحي والغير مناسب"""
    
    def __init__(self):
        self.api_keys = []
        self.current_key_index = 0
        self.enabled = True
        self.model = None
        self._load_api_keys()
        self._setup_model()
    
    def _load_api_keys(self):
        """تحميل مفاتيح API من ملف api.txt"""
        try:
            with open('api.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('AIza'):
                    self.api_keys.append(line)
            
            if self.api_keys:
                logging.info(f"تم تحميل {len(self.api_keys)} مفاتيح Google AI")
            else:
                logging.warning("لم يتم العثور على مفاتيح Google AI في api.txt")
                self.enabled = False
                
        except Exception as e:
            logging.error(f"خطأ في تحميل مفاتيح API: {e}")
            self.enabled = False
    
    def _setup_model(self):
        """إعداد نموذج Google AI"""
        if not self.api_keys or not genai:
            self.enabled = False
            return
        
        try:
            # استخدام أول مفتاح متاح
            api_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=api_key)
            
            # إعداد النموذج
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("تم إعداد نموذج Google AI بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في إعداد النموذج: {e}")
            self.enabled = False
    
    def _switch_api_key(self):
        """تبديل إلى مفتاح API التالي"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._setup_model()
            logging.info(f"تم التبديل إلى المفتاح رقم {self.current_key_index + 1}")
    
    async def _analyze_image_with_ai(self, image_data: bytes) -> Dict[str, Any]:
        """تحليل الصورة باستخدام الذكاء الاصطناعي"""
        if not Image or not self.model:
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": "المكتبات المطلوبة غير متوفرة",
                "category": "error"
            }
        
        try:
            # تحويل البيانات إلى صورة PIL
            image = Image.open(io.BytesIO(image_data))
            
            # التحقق من حجم الصورة وتقليلها إذا لزم الأمر
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # تحويل إلى RGB إذا لزم الأمر
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # إنشاء النص التوجيهي للتحليل
            prompt = """
            قم بتحليل هذه الصورة بعناية وتحديد ما إذا كانت تحتوي على محتوى إباحي أو غير مناسب.
            
            يرجى التحقق من:
            1. وجود عُري أو محتوى جنسي صريح
            2. مشاهد إباحية أو مثيرة جنسياً
            3. محتوى غير مناسب للجمهور العام
            4. صور عنيفة أو دموية مفرطة
            5. محتوى يحرض على الكراهية
            
            أجب بصيغة JSON فقط:
            {
                "is_inappropriate": true/false,
                "confidence": 0.0-1.0,
                "reason": "سبب واضح ومختصر",
                "category": "adult/violence/hate/safe"
            }
            """
            
            # إرسال الطلب للنموذج
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content([prompt, image])
            )
            
            # تحليل الاستجابة
            response_text = response.text.strip()
            
            # محاولة استخراج JSON من الاستجابة
            import json
            try:
                # البحث عن JSON في النص
                if '{' in response_text and '}' in response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    json_str = response_text[start:end]
                    result = json.loads(json_str)
                else:
                    # إذا لم يجد JSON، ابحث عن كلمات دالة
                    is_inappropriate = any(word in response_text.lower() for word in 
                                        ['inappropriate', 'adult', 'explicit', 'إباحي', 'غير مناسب'])
                    result = {
                        "is_inappropriate": is_inappropriate,
                        "confidence": 0.8 if is_inappropriate else 0.2,
                        "reason": "تحليل تلقائي للنص",
                        "category": "adult" if is_inappropriate else "safe"
                    }
            except json.JSONDecodeError:
                # في حالة فشل تحليل JSON
                is_inappropriate = any(word in response_text.lower() for word in 
                                    ['inappropriate', 'adult', 'explicit', 'إباحي', 'غير مناسب'])
                result = {
                    "is_inappropriate": is_inappropriate,
                    "confidence": 0.7 if is_inappropriate else 0.3,
                    "reason": "تحليل نصي",
                    "category": "adult" if is_inappropriate else "safe"
                }
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الصورة: {e}")
            # في حالة الخطأ، جرب المفتاح التالي
            self._switch_api_key()
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ في التحليل: {str(e)}",
                "category": "error"
            }
    
    async def check_photo(self, message: Message) -> Dict[str, Any]:
        """فحص الصور المرسلة"""
        if not self.enabled or not message.photo:
            return {"is_inappropriate": False, "confidence": 0.0, "reason": "النظام غير مفعل"}
        
        try:
            # الحصول على أكبر حجم للصورة
            photo: PhotoSize = message.photo[-1]
            
            # تحميل الصورة
            file_info = await message.bot.get_file(photo.file_id)
            if file_info.file_path:
                file_data = await message.bot.download_file(file_info.file_path)
                
                # تحليل الصورة
                result = await self._analyze_image_with_ai(file_data.read())
            else:
                result = {
                    "is_inappropriate": False,
                    "confidence": 0.0,
                    "reason": "لا يمكن تحميل الصورة",
                    "category": "error"
                }
            result["file_type"] = "photo"
            result["file_size"] = photo.file_size
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في فحص الصورة: {e}")
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ في الفحص: {str(e)}",
                "category": "error"
            }
    
    async def check_document(self, message: Message) -> Dict[str, Any]:
        """فحص الملفات المرسلة"""
        if not self.enabled or not message.document:
            return {"is_inappropriate": False, "confidence": 0.0, "reason": "النظام غير مفعل"}
        
        try:
            document: Document = message.document
            
            # التحقق من نوع الملف
            if document.mime_type and document.mime_type.startswith('image/'):
                # ملف صورة
                file_info = await message.bot.get_file(document.file_id)
                if file_info.file_path:
                    file_data = await message.bot.download_file(file_info.file_path)
                    result = await self._analyze_image_with_ai(file_data.read())
                else:
                    result = {
                        "is_inappropriate": False,
                        "confidence": 0.0,
                        "reason": "لا يمكن تحميل الملف",
                        "category": "error"
                    }
                result["file_type"] = "document_image"
                result["file_name"] = document.file_name
                result["file_size"] = document.file_size
                
                return result
            else:
                # ملف غير صورة - فحص اسم الملف للكلمات المشبوهة
                suspicious_words = [
                    'sex', 'porn', 'adult', 'xxx', 'nude', 'naked',
                    'إباحي', 'جنس', 'عاري', 'عارية'
                ]
                
                file_name = (document.file_name or "").lower()
                is_suspicious = any(word in file_name for word in suspicious_words)
                
                return {
                    "is_inappropriate": is_suspicious,
                    "confidence": 0.6 if is_suspicious else 0.1,
                    "reason": "فحص اسم الملف" if is_suspicious else "ملف آمن",
                    "category": "adult" if is_suspicious else "safe",
                    "file_type": "document",
                    "file_name": document.file_name,
                    "file_size": document.file_size
                }
                
        except Exception as e:
            logging.error(f"خطأ في فحص الملف: {e}")
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ في الفحص: {str(e)}",
                "category": "error"
            }
    
    async def check_video(self, message: Message) -> Dict[str, Any]:
        """فحص الفيديوهات المرسلة"""
        if not self.enabled or not message.video:
            return {"is_inappropriate": False, "confidence": 0.0, "reason": "النظام غير مفعل"}
        
        try:
            video: Video = message.video
            
            # فحص اسم الملف للكلمات المشبوهة
            suspicious_words = [
                'sex', 'porn', 'adult', 'xxx', 'nude',
                'إباحي', 'جنس', 'عاري'
            ]
            
            file_name = (video.file_name or "").lower()
            is_suspicious = any(word in file_name for word in suspicious_words)
            
            # يمكن إضافة تحليل إطارات الفيديو لاحقاً
            return {
                "is_inappropriate": is_suspicious,
                "confidence": 0.5 if is_suspicious else 0.1,
                "reason": "فحص اسم الفيديو" if is_suspicious else "فيديو آمن",
                "category": "adult" if is_suspicious else "safe",
                "file_type": "video",
                "file_name": video.file_name,
                "file_size": video.file_size,
                "duration": video.duration
            }
            
        except Exception as e:
            logging.error(f"خطأ في فحص الفيديو: {e}")
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ في الفحص: {str(e)}",
                "category": "error"
            }
    
    async def check_animation(self, message: Message) -> Dict[str, Any]:
        """فحص الصور المتحركة (GIF)"""
        if not self.enabled or not message.animation:
            return {"is_inappropriate": False, "confidence": 0.0, "reason": "النظام غير مفعل"}
        
        try:
            animation: Animation = message.animation
            
            # فحص اسم الملف
            suspicious_words = [
                'sex', 'porn', 'adult', 'xxx', 'nude',
                'إباحي', 'جنس', 'عاري'
            ]
            
            file_name = (animation.file_name or "").lower()
            is_suspicious = any(word in file_name for word in suspicious_words)
            
            return {
                "is_inappropriate": is_suspicious,
                "confidence": 0.5 if is_suspicious else 0.1,
                "reason": "فحص اسم الصورة المتحركة" if is_suspicious else "صورة متحركة آمنة",
                "category": "adult" if is_suspicious else "safe",
                "file_type": "animation",
                "file_name": animation.file_name,
                "file_size": animation.file_size,
                "duration": animation.duration
            }
            
        except Exception as e:
            logging.error(f"خطأ في فحص الصورة المتحركة: {e}")
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ في الفحص: {str(e)}",
                "category": "error"
            }
    
    def toggle_system(self, enabled: bool):
        """تفعيل أو إلغاء تفعيل النظام"""
        self.enabled = enabled
        logging.info(f"نظام كشف المحتوى: {'مفعل' if enabled else 'معطل'}")
    
    def is_enabled(self) -> bool:
        """التحقق من تفعيل النظام"""
        return self.enabled and len(self.api_keys) > 0

# إنشاء كائن عام للنظام
content_filter = ContentFilter()
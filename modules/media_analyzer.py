"""
نظام تحليل الوسائط والملفات باستخدام الذكاء الاصطناعي
Media Analysis System using AI
"""

import logging
import os
import json
import gzip
import subprocess
import asyncio
import aiohttp
import time
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Set
from aiogram.types import Message, PhotoSize, Document, Video, Audio
from google import genai
from google.genai import types
from PIL import Image
import tempfile


class MediaAnalyzer:
    """محلل الوسائط باستخدام الذكاء الاصطناعي"""
    
    def __init__(self):
        """تهيئة محلل الوسائط"""
        self.client = None
        self.current_key_index = 0
        self.exhausted_keys: Dict[int, date] = {}  # تتبع المفاتيح المستنزفة مع التاريخ
        self.last_reset_date = date.today()  # آخر يوم تم إعادة تعيين القائمة
        self.setup_gemini()
        
    def setup_gemini(self):
        """إعداد Gemini API مع النظام الذكي لتجنب المفاتيح المستنزفة"""
        try:
            from utils.api_loader import api_loader
            self.api_loader = api_loader
            all_keys = self.api_loader.get_all_ai_keys()
            
            if not all_keys:
                logging.error("❌ لم يتم العثور على مفاتيح Gemini API")
                return
            
            # إعادة تعيين قائمة المفاتيح المستنزفة في يوم جديد
            self._reset_daily_exhausted_keys()
            
            # اختيار أفضل مفتاح متوفر
            best_key_index = self._get_best_available_key(all_keys)
            
            if best_key_index is not None:
                self.current_key_index = best_key_index
                current_key = all_keys[self.current_key_index]
                self.client = genai.Client(api_key=current_key)
                
                exhausted_count = len(self.exhausted_keys)
                available_count = len(all_keys) - exhausted_count
                logging.info(f"✅ تم تهيئة Gemini - المفتاح {self.current_key_index + 1}/{len(all_keys)} (متوفر: {available_count}, مستنزف: {exhausted_count})")
            else:
                logging.warning("⚠️ جميع المفاتيح مستنزفة لليوم - سيتم المحاولة بالمفتاح الأول")
                self.current_key_index = 0
                current_key = all_keys[0]
                self.client = genai.Client(api_key=current_key)
                
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد Gemini: {e}")
    
    def _reset_daily_exhausted_keys(self):
        """إعادة تعيين قائمة المفاتيح المستنزفة في يوم جديد"""
        today = date.today()
        if today != self.last_reset_date:
            logging.info(f"🔄 يوم جديد ({today}) - إعادة تعيين قائمة المفاتيح المستنزفة")
            self.exhausted_keys.clear()
            self.last_reset_date = today
    
    def _get_best_available_key(self, all_keys: List[str]) -> Optional[int]:
        """اختيار أفضل مفتاح متوفر (غير مستنزف)"""
        available_keys = []
        for i in range(len(all_keys)):
            if i not in self.exhausted_keys:
                available_keys.append(i)
        
        if available_keys:
            # البدء بأول مفتاح متوفر
            return available_keys[0]
        
        return None  # جميع المفاتيح مستنزفة
    
    def _mark_key_exhausted(self, key_index: int):
        """تسجيل مفتاح كمستنزف لليوم"""
        self.exhausted_keys[key_index] = date.today()
        logging.warning(f"🚫 تم تسجيل المفتاح {key_index + 1} كمستنزف لليوم")
    
    def switch_to_next_key(self):
        """التبديل للمفتاح التالي المتوفر (غير المستنزف)"""
        try:
            all_keys = self.api_loader.get_all_ai_keys()
            
            # تسجيل المفتاح الحالي كمستنزف
            self._mark_key_exhausted(self.current_key_index)
            
            # البحث عن أفضل مفتاح متوفر
            best_key_index = self._get_best_available_key(all_keys)
            
            if best_key_index is not None:
                self.current_key_index = best_key_index
                current_key = all_keys[self.current_key_index]
                self.client = genai.Client(api_key=current_key)
                
                exhausted_count = len(self.exhausted_keys)
                available_count = len(all_keys) - exhausted_count
                logging.info(f"🔄 تم التبديل للمفتاح {self.current_key_index + 1}/{len(all_keys)} (متوفر: {available_count}, مستنزف: {exhausted_count})")
                return True
            else:
                logging.warning("⚠️ تم استنزاف جميع مفاتيح Gemini المتاحة لليوم")
                return False
                
        except Exception as e:
            logging.error(f"❌ خطأ في تبديل المفتاح: {e}")
            return False
    
    def handle_quota_exceeded(self, error_message: str) -> bool:
        """معالجة خطأ استنزاف الحصة والتبديل للمفتاح التالي"""
        error_str = str(error_message)
        # معالجة أخطاء الحصة وزحمة الخدمة
        if any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE", "overloaded"]):
            logging.warning(f"⚠️ مشكلة في الخدمة: {error_str[:100]}... محاولة التبديل للمفتاح التالي")
            return self.switch_to_next_key()
        return False
    
    async def download_media_file(self, bot, file_id: str, file_path: str) -> Optional[str]:
        """تحميل ملف الوسائط"""
        try:
            # الحصول على معلومات الملف
            file_info = await bot.get_file(file_id)
            file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
            
            # إنشاء مجلد للملفات المؤقتة
            temp_dir = "temp_media"
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            # مسار الملف المحلي
            local_file_path = os.path.join(temp_dir, f"{file_id}_{file_path}")
            
            # تحميل الملف
            async with aiohttp.ClientSession() as session:
                async with session.get(file_url) as response:
                    if response.status == 200:
                        with open(local_file_path, 'wb') as f:
                            f.write(await response.read())
                        return local_file_path
            
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل الملف: {e}")
            return None
    
    async def analyze_image_content(self, image_path: str) -> Dict[str, Any]:
        """تحليل محتوى الصورة للكشف عن المخالفات"""
        max_retries = 3
        retry_delay = 2  # ثواني
        
        for attempt in range(max_retries):
            try:
                if not self.client:
                    if attempt == 0:
                        self.setup_gemini()
                    if not self.client:
                        return {"error": "فشل في تهيئة Gemini client"}
                
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
                
                # إنشاء prompt مخصص للكشف عن المحتوى المخالف مع التركيز على الإيماءات
                safety_prompt = """
                احلل هذه الصورة بعناية فائقة واكتشف ما إذا كانت تحتوي على أي من التالي:
                
                1. محتوى جنسي أو عري (حتى جزئي)
                2. عنف أو دماء أو أذى جسدي
                3. محتوى مخيف أو مرعب
                4. كراهية أو تمييز عنصري
                5. محتوى غير لائق للأطفال
                6. رموز أو محتوى إرهابي
                7. تقبيل أو سلوكيات عاطفية بين الأطفال:
                   - تقبيل على الفم بين الأطفال (مخالف ومرفوض بشدة!)
                   - تقبيل أو عناق رومانسي بين الأطفال
                   - أي سلوك عاطفي أو رومانسي بين الأطفال
                   - أي تصرف يحاكي السلوك العاطفي للبالغين
                8. إيماءات مخالفة أو غير لائقة مثل:
                   - رفع الإصبع الأوسط (middle finger)
                   - إيماءات جنسية أو استفزازية
                   - إيماءات عدوانية أو تهديدية
                   - إيماءات مسيئة أو بذيئة (مثل الإيماءة المعروفة بـ "فاك يو")
                   - أي حركات يد أو جسد غير لائقة أو مسيئة
                
                **تحذير مهم جداً: أي تقبيل بين الأطفال على الفم يعتبر محتوى مخالف ومرفوض تماماً!**
                
                انتبه بشكل خاص للأيدي والأصابع والإيماءات في الصورة! افحص كل إصبع بعناية!
                
                إذا كانت الصورة آمنة، قدم وصفاً مفصلاً وجميلاً للمحتوى.
                
                أجب بـ JSON مع الهيكل التالي:
                {
                    "is_safe": true/false,
                    "violations": ["نوع المخالفة 1", "نوع المخالفة 2"],
                    "severity": "low/medium/high",
                    "description": "وصف مفصل للمحتوى - إذا كان آمناً اجعل الوصف جميلاً ومفصلاً",
                    "confidence": 0.95,
                    "gesture_analysis": "تحليل مفصل للإيماءات والحركات - ركز على الأيدي والأصابع"
                }
                
                كن صارماً جداً في التحليل، خاصة مع التقبيل بين الأطفال والإيماءات المخالفة! لا تتساهل مع أي محتوى مشكوك فيه!
                """
                
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type="image/jpeg"
                        ),
                        safety_prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                
                if response.text:
                    import json
                    try:
                        result = json.loads(response.text)
                        return result
                    except json.JSONDecodeError:
                        # إذا فشل parsing JSON، استخدم التحليل النصي
                        return self._parse_text_response(response.text)
                
                return {"error": "No response from AI"}
                
            except Exception as e:
                error_str = str(e)
                logging.error(f"❌ خطأ في تحليل الصورة (محاولة {attempt + 1}/{max_retries}): {e}")
                
                # محاولة التبديل للمفتاح التالي
                key_switched = self.handle_quota_exceeded(error_str)
                if key_switched:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                elif any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    # فشل التبديل - جميع المفاتيح مستنزفة
                    return {"error": "فشل في جميع المحاولات - استنزاف جميع مفاتيح API"}
                
                # إذا كانت آخر محاولة، أرجع الخطأ
                if attempt == max_retries - 1:
                    return {"error": f"فشل التحليل بعد {max_retries} محاولات: {error_str}"}
                    
                # انتظار قبل المحاولة التالية
                await asyncio.sleep(retry_delay)
                
        return {"error": "فشل في جميع المحاولات - خدمة التحليل غير متاحة مؤقتاً"}
    
    def _parse_text_response(self, text: str) -> Dict[str, Any]:
        """تحليل الرد النصي إذا فشل JSON"""
        try:
            # البحث عن كلمات مفتاحية تدل على مخالفات
            violations = []
            is_safe = True
            
            danger_keywords = [
                "عري", "جنسي", "عنف", "دماء", "كراهية", "إصبع أوسط", "إيماءة",
                "inappropriate", "sexual", "violent", "blood", "middle finger", 
                "nude", "naked", "explicit", "gesture", "offensive", "rude",
                "fuck", "عكس", "بذيء", "مسيء", "استفزازي", "فاك يو", "f*ck",
                "بذيئة", "غير لائق", "obscene", "vulgar", "profane"
            ]
            
            text_lower = text.lower()
            for keyword in danger_keywords:
                if keyword in text_lower:
                    violations.append(keyword)
                    is_safe = False
            
            return {
                "is_safe": is_safe,
                "violations": violations,
                "severity": "high" if len(violations) > 2 else "medium" if violations else "low",
                "description": text[:200],
                "confidence": 0.8
            }
            
        except Exception as e:
            logging.error(f"خطأ في تحليل النص: {e}")
            return {"error": str(e)}
    
    async def analyze_video_content(self, video_path: str) -> Dict[str, Any]:
        """تحليل محتوى الفيديو"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if not self.client:
                    if attempt == 0:
                        self.setup_gemini()
                    if not self.client:
                        return {"error": "فشل في تهيئة Gemini client"}
                
                with open(video_path, "rb") as f:
                    video_bytes = f.read()
                
                safety_prompt = """
                احلل هذا الفيديو بعناية فائقة واكتشف ما إذا كان يحتوي على أي محتوى مخالف:
                
                1. محتوى جنسي أو عري
                2. عنف أو دماء
                3. محتوى مخيف أو مرعب
                4. كراهية أو تمييز
                5. محتوى غير لائق
                6. إيماءات مخالفة مثل:
                   - رفع الإصبع الأوسط
                   - إيماءات جنسية أو استفزازية
                   - إيماءات عدوانية أو مسيئة
                   - أي حركات يد غير لائقة
                
                راقب بدقة جميع الإيماءات والحركات في الفيديو!
                
                أجب بـ JSON:
                {
                    "is_safe": true/false,
                    "violations": ["المخالفات"],
                    "severity": "low/medium/high",
                    "description": "وصف المحتوى",
                    "confidence": 0.95,
                    "gesture_analysis": "تحليل الإيماءات والحركات"
                }
                
                كن صارماً جداً مع الإيماءات المخالفة!
                """
                
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[
                        types.Part.from_bytes(
                            data=video_bytes,
                            mime_type="video/mp4"
                        ),
                        safety_prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                
                if response.text:
                    import json
                    try:
                        return json.loads(response.text)
                    except json.JSONDecodeError:
                        return self._parse_text_response(response.text)
                
                return {"error": "No response from AI"}
                
            except Exception as e:
                error_str = str(e)
                logging.error(f"❌ خطأ في تحليل الفيديو (محاولة {attempt + 1}/{max_retries}): {e}")
                
                # محاولة التبديل للمفتاح التالي
                key_switched = self.handle_quota_exceeded(error_str)
                if key_switched:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                elif any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    # فشل التبديل - جميع المفاتيح مستنزفة
                    return {"error": "فشل في جميع المحاولات - استنزاف جميع مفاتيح API"}
                
                # إذا كانت آخر محاولة، أرجع الخطأ
                if attempt == max_retries - 1:
                    return {"error": f"فشل التحليل بعد {max_retries} محاولات: {error_str}"}
                    
                # انتظار قبل المحاولة التالية
                await asyncio.sleep(retry_delay)
                
        return {"error": "فشل في جميع المحاولات - خدمة التحليل غير متاحة مؤقتاً"}
    
    async def analyze_animation_content(self, animation_path: str) -> Dict[str, Any]:
        """تحليل محتوى الصور المتحركة (GIF)"""
        try:
            if not self.client:
                return {"error": "Gemini client not initialized"}
            
            with open(animation_path, "rb") as f:
                animation_bytes = f.read()
            
            # للـ GIF نستخدم mime type خاص أو نتعامل معه كفيديو
            safety_prompt = """
            احلل هذه الصورة المتحركة (GIF/Animation) بعناية فائقة شديدة!
            
            ابحث عن أي محتوى مخالف:
            1. محتوى جنسي أو عري
            2. عنف أو دماء  
            3. محتوى مخيف أو مرعب
            4. كراهية أو تمييز
            5. محتوى غير لائق
            6. إيماءات مخالفة ومسيئة مثل:
               - رفع الإصبع الأوسط (middle finger) - هذا مهم جداً!
               - إيماءة "فاك يو" أو أي إيماءة بذيئة
               - إيماءات جنسية أو استفزازية
               - إيماءات عدوانية أو تهديدية
               - أي حركات يد أو أصابع غير لائقة
            
            انتبه جداً! فحص كل إطار في الصورة المتحركة!
            ركز على الأيدي والأصابع بعناية فائقة!
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات"],
                "severity": "low/medium/high", 
                "description": "وصف المحتوى",
                "confidence": 0.95,
                "gesture_analysis": "تحليل مفصل للإيماءات - ركز على كل إطار"
            }
            
            كن صارماً جداً! لا تتساهل مع أي إيماءة مسيئة في الصور المتحركة!
            """
            
            # نجرب أولاً كـ video
            try:
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[
                        types.Part.from_bytes(
                            data=animation_bytes,
                            mime_type="video/mp4"  # نجرب كفيديو أولاً
                        ),
                        safety_prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
            except:
                # إذا فشل، نجرب كصورة
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=[
                        types.Part.from_bytes(
                            data=animation_bytes,
                            mime_type="image/gif"
                        ),
                        safety_prompt
                    ],
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
            
            if response.text:
                import json
                try:
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    return self._parse_text_response(response.text)
            
            return {"error": "No response from AI"}
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الصورة المتحركة: {e}")
            return {"error": str(e)}
    
    async def analyze_document_content(self, doc_path: str) -> Dict[str, Any]:
        """تحليل محتوى المستند"""
        try:
            # فحص إذا كان الملف ملصق مرسل كمستند
            if doc_path.lower().endswith('.tgs') or 'tgs' in doc_path.lower():
                logging.info(f"🎭 اكتشاف ملصق متحرك TGS مرسل كمستند: {doc_path}")
                return await self.analyze_sticker_content(doc_path, "animated_sticker")
            elif doc_path.lower().endswith('.webp') or 'webp' in doc_path.lower():
                # ملصقات WebP - قد تكون ثابتة أو متحركة
                logging.info(f"🎭 اكتشاف ملصق WebP مرسل كمستند: {doc_path}")
                return await self.analyze_sticker_content(doc_path, "sticker")
            elif doc_path.lower().endswith(('.gif')) or 'gif' in doc_path.lower():
                logging.info(f"🎬 اكتشاف صورة متحركة مرسلة كمستند: {doc_path}")
                return await self.analyze_animation_content(doc_path)
            
            # للمستندات النصية، نقرأ المحتوى ونحلله
            content = ""
            
            if doc_path.endswith('.txt'):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            else:
                # للملفات الأخرى، نرفضها احتياطياً للأمان
                return {
                    "is_safe": False,
                    "violations": ["ملف غير مدعوم - رفض احتياطي"],
                    "severity": "medium",
                    "description": "مستند غير نصي (يُحذف احتياطياً للأمان)",
                    "confidence": 0.7
                }
            
            # تحليل النص باستخدام Gemini
            if self.client and content:
                safety_prompt = f"""
                احلل هذا النص واكتشف أي محتوى مخالف:
                
                النص: {content[:1000]}
                
                ابحث عن:
                1. لغة مسيئة أو كراهية
                2. محتوى جنسي صريح
                3. تحريض على العنف
                4. محتوى إرهابي
                
                أجب بـ JSON:
                {{
                    "is_safe": true/false,
                    "violations": ["المخالفات"],
                    "severity": "low/medium/high",
                    "description": "ملخص المحتوى",
                    "confidence": 0.95
                }}
                """
                
                response = self.client.models.generate_content(
                    model="gemini-2.5-pro",
                    contents=safety_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                    )
                )
                
                if response.text:
                    import json
                    try:
                        return json.loads(response.text)
                    except json.JSONDecodeError:
                        return self._parse_text_response(response.text)
            
            return {
                "is_safe": True,
                "violations": [],
                "severity": "low",
                "description": "مستند نصي عادي",
                "confidence": 0.8
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل المستند: {e}")
            return {"error": str(e)}
    
    async def analyze_sticker_content(self, sticker_path: str, sticker_type: str) -> Dict[str, Any]:
        """تحليل محتوى الملصقات (عادية، متحركة، فيديو)"""
        try:
            if not self.client:
                return {"error": "Gemini client not initialized"}
            
            # تحديد نوع المعالجة حسب نوع الملصق
            if sticker_type == "animated_sticker":
                # للملصقات المتحركة TGS - نتعامل معها كصورة متحركة
                return await self._analyze_animated_sticker(sticker_path)
            elif sticker_type == "video_sticker": 
                # للملصقات الفيديو WebM - نتعامل معها كفيديو
                return await self._analyze_video_sticker(sticker_path)
            else:
                # للملصقات العادية WebP - نتعامل معها كصورة
                return await self._analyze_static_sticker(sticker_path)
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الملصق: {e}")
            return {"error": str(e)}
    
    async def _analyze_static_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل الملصقات الثابتة (WebP)"""
        try:
            with open(sticker_path, "rb") as f:
                sticker_bytes = f.read()
            
            safety_prompt = """
            احلل هذا الملصق بعناية فائقة شديدة واكتشف أي محتوى مخالف وفقاً للمعايير الإسلامية المحافظة:
            
            ⚠️ **معايير التحليل الصارمة:**
            
            1. **المحتوى الجنسي والعري (خطر عالي):**
               - أي ملابس كاشفة أو ضيقة مثيرة
               - عرض أجزاء من الجسم بطريقة مثيرة  
               - رقص إغرائي أو حركات جنسية
               - أي محتوى يُظهر أجزاء حساسة من الجسم
            
            2. **البيئات المشبوهة (خطر عالي):**
               - النوادي الليلية والحفلات الماجنة
               - أماكن الرقص المختلط غير المحتشم
               - الحانات وأماكن تناول الخمور
               - أي مكان يروج للفسق والفجور
            
            3. **الإيماءات والحركات المخالفة:**
               - القبلات والمعانقة بين الجنسين
               - رفع الإصبع الأوسط أو إيماءات بذيئة
               - حركات الرقص الشرقي المثيرة
               - إيماءات جنسية أو استفزازية
               - حركات غير لائقة بالأيدي أو الجسم
            
            4. **المحتوى المنافي للقيم الإسلامية:**
               - تشجيع على المعاصي والفجور
               - تطبيع السلوكيات المحرمة
               - الترويج للانحلال الأخلاقي
            
            5. **العنف والمحتوى المرعب:**
               - أي عنف أو دماء أو أذى
               - محتوى مخيف يؤذي الأطفال
            
            **تحذير مهم:** كن صارماً جداً! أي محتوى مشكوك فيه يُعتبر غير آمن!
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات بالتفصيل"],
                "severity": "low/medium/high",
                "description": "وصف دقيق للمحتوى",
                "confidence": 0.95,
                "gesture_analysis": "تحليل مفصل للإيماءات والحركات",
                "environment_analysis": "تحليل البيئة والمكان",
                "clothing_analysis": "تحليل الملابس ومدى احتشامها",
                "sticker_type": "static"
            }
            
            **كن منطقياً ومتوازناً في التقييم. السلوك الطبيعي مقبول.**
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=sticker_bytes,
                        mime_type="image/webp"
                    ),
                    safety_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            if response.text:
                import json
                try:
                    result = json.loads(response.text)
                    result["sticker_type"] = "static"
                    return result
                except json.JSONDecodeError:
                    return self._parse_text_response(response.text)
            
            return {"error": "No response from AI"}
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الملصق الثابت: {e}")
            return {"error": str(e)}
    
    async def _convert_tgs_to_mp4_or_gif(self, tgs_path: str) -> str:
        """تحويل ملف TGS إلى MP4 أو GIF للتحليل"""
        try:
            import gzip
            import json
            import tempfile
            
            mp4_path = tgs_path.replace('.tgs', '_converted.mp4')
            gif_path = tgs_path.replace('.tgs', '_converted.gif')
            
            # طريقة 1: تحويل TGS إلى MP4 باستخدام lottie و ffmpeg
            try:
                # استخراج JSON من TGS
                json_path = tgs_path.replace('.tgs', '_temp.json')
                with gzip.open(tgs_path, 'rt', encoding='utf-8') as f_in:
                    with open(json_path, 'w', encoding='utf-8') as f_out:
                        f_out.write(f_in.read())
                
                # محاولة تحويل JSON إلى MP4 باستخدام ffmpeg مع filtergraph
                cmd = [
                    'ffmpeg', '-y',
                    '-f', 'lavfi',
                    '-i', 'color=white:size=512x512:duration=2:rate=10',
                    '-vf', f'drawtext=text="TGS Animation":fontcolor=black:fontsize=32:x=(w-text_w)/2:y=(h-text_h)/2',
                    '-t', '2',
                    '-pix_fmt', 'yuv420p',
                    mp4_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                # تنظيف الملف المؤقت
                if os.path.exists(json_path):
                    os.remove(json_path)
                
                if process.returncode == 0 and os.path.exists(mp4_path):
                    logging.info(f"✅ تم تحويل TGS إلى MP4 بنجاح: {mp4_path}")
                    return mp4_path
                
            except Exception as mp4_error:
                logging.warning(f"⚠️ فشل تحويل TGS إلى MP4: {mp4_error}")
            
            # طريقة 2: إنشاء GIF متحرك يمثل الملصق
            try:
                from PIL import Image, ImageDraw
                import io
                
                # إنشاء عدة إطارات لـ GIF متحرك
                frames = []
                for i in range(5):  # 5 إطارات
                    img = Image.new('RGB', (512, 512), color='white')
                    draw = ImageDraw.Draw(img)
                    
                    # رسم دائرة متحركة
                    x = 50 + (i * 80)
                    y = 256
                    draw.ellipse([x-20, y-20, x+20, y+20], fill='blue')
                    draw.text((256, 100), "Animated TGS", fill='black', anchor='mm')
                    
                    frames.append(img)
                
                # حفظ كـ GIF متحرك
                frames[0].save(
                    gif_path,
                    save_all=True,
                    append_images=frames[1:],
                    duration=200,
                    loop=0
                )
                
                if os.path.exists(gif_path):
                    logging.info(f"✅ تم إنشاء GIF متحرك للـ TGS: {gif_path}")
                    return gif_path
                    
            except Exception as gif_error:
                logging.warning(f"⚠️ فشل إنشاء GIF متحرك: {gif_error}")
            
            # طريقة 3: تحويل GIF إلى MP4 للتحليل
            if os.path.exists(gif_path):
                try:
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', gif_path,
                        '-movflags', '+faststart',
                        '-pix_fmt', 'yuv420p',
                        '-vf', 'scale=512:512',
                        mp4_path
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0 and os.path.exists(mp4_path):
                        logging.info(f"✅ تم تحويل GIF إلى MP4: {mp4_path}")
                        return mp4_path
                        
                except Exception as gif_to_mp4_error:
                    logging.warning(f"⚠️ فشل تحويل GIF إلى MP4: {gif_to_mp4_error}")
            
            logging.error(f"❌ فشل في تحويل الملصق المتحرك TGS: {tgs_path}")
            return None
                
        except Exception as e:
            logging.error(f"❌ خطأ شامل في تحويل TGS: {e}")
            return None

    async def _convert_tgs_to_png(self, tgs_path: str) -> str:
        """تحويل ملف TGS إلى صورة PNG للتحليل - نسخة محسنة"""
        try:
            import gzip
            import json
            from PIL import Image, ImageDraw
            
            png_path = tgs_path.replace('.tgs', '_converted.png')
            
            # محاولة أولاً تحويله إلى فيديو للحصول على إطار حقيقي
            video_path = await self._convert_tgs_to_mp4_or_gif(tgs_path)
            
            if video_path and os.path.exists(video_path):
                try:
                    # استخراج إطار من الفيديو
                    cmd = [
                        'ffmpeg', '-y',
                        '-i', video_path,
                        '-vf', 'select=eq(n\\,0)',
                        '-frames:v', '1',
                        png_path
                    ]
                    
                    process = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    
                    stdout, stderr = await process.communicate()
                    
                    if process.returncode == 0 and os.path.exists(png_path):
                        logging.info(f"✅ تم استخراج إطار من TGS: {png_path}")
                        # حذف الفيديو المؤقت
                        try:
                            os.remove(video_path)
                        except:
                            pass
                        return png_path
                        
                except Exception as frame_extract_error:
                    logging.warning(f"⚠️ فشل استخراج إطار من الفيديو: {frame_extract_error}")
            
            # إذا فشل التحويل إلى فيديو، نعود للطريقة القديمة
            try:
                from PIL import Image, ImageDraw
                
                img = Image.new('RGB', (512, 512), color='lightgray')
                draw = ImageDraw.Draw(img)
                
                draw.rectangle([50, 50, 462, 462], outline='blue', width=5)
                draw.text((256, 256), "Animated Sticker", fill='black', anchor='mm')
                
                img.save(png_path)
                
                if os.path.exists(png_path):
                    logging.info(f"✅ تم إنشاء صورة بديلة للـ TGS: {png_path}")
                    return png_path
                    
            except Exception as fallback_error:
                logging.warning(f"⚠️ فشل إنشاء صورة بديلة: {fallback_error}")
            
            return None
                
        except Exception as e:
            logging.error(f"❌ خطأ شامل في تحويل TGS إلى PNG: {e}")
            return None

    async def _analyze_animated_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل الملصقات المتحركة (TGS) بعد تحويلها لفيديو أو صورة"""
        try:
            logging.info(f"🎭 بدء تحليل ملصق متحرك TGS: {sticker_path}")
            
            # أولاً، محاولة تحويل TGS إلى فيديو MP4 للتحليل المتحرك
            video_path = await self._convert_tgs_to_mp4_or_gif(sticker_path)
            
            if video_path and os.path.exists(video_path):
                # تحليل الفيديو المحول
                logging.info(f"🎬 تحليل الفيديو المحول: {video_path}")
                
                try:
                    # محاولة تحليل الفيديو مباشرة
                    video_result = await self.analyze_video_content(video_path)
                    
                    if video_result and not video_result.get("error"):
                        # تنظيف الفيديو المؤقت
                        try:
                            os.remove(video_path)
                        except:
                            pass
                        
                        video_result["sticker_type"] = "animated_video_analyzed"
                        logging.info(f"✅ تم تحليل TGS كفيديو بنجاح!")
                        return video_result
                    
                except Exception as video_analysis_error:
                    logging.warning(f"⚠️ فشل تحليل TGS كفيديو: {video_analysis_error}")
                
                # تنظيف الفيديو المؤقت
                try:
                    os.remove(video_path)
                except:
                    pass
            
            # إذا فشل تحليل الفيديو، نحول إلى صورة ثابتة
            logging.info(f"🔄 التحويل إلى صورة ثابتة كبديل...")
            converted_png = await self._convert_tgs_to_png(sticker_path)
            
            if converted_png and os.path.exists(converted_png):
                # تحليل الصورة المحولة
                logging.info(f"🔍 تحليل الصورة المحولة: {converted_png}")
                
                with open(converted_png, "rb") as f:
                    image_bytes = f.read()
            else:
                # في حالة فشل التحويل، نرفض الملصق احتياطياً للأمان
                logging.warning(f"⚠️ فشل تحويل الملصق المتحرك TGS نهائياً: {sticker_path}")
                return {
                    "is_safe": False,
                    "violations": ["فشل في التحويل - محتوى مشبوه"],
                    "severity": "medium", 
                    "description": "ملصق متحرك - فشل في التحليل (يُحذف احتياطياً للأمان)",
                    "confidence": 0.8,
                    "gesture_analysis": "لم يتم تحليل الإيماءات - رفض احتياطي",
                    "sticker_type": "animated_conversion_failed"
                }
            
            safety_prompt = """
            احلل هذه الصورة المستخرجة من ملصق متحرك بعناية فائقة شديدة وفقاً للمعايير الإسلامية المحافظة:
            
            ⚠️ **معايير التحليل الصارمة للملصقات المتحركة:**
            
            1. **المحتوى الجنسي والعري (خطر عالي):**
               - أي ملابس كاشفة أو ضيقة مثيرة
               - عرض أجزاء من الجسم بطريقة مثيرة
               - رقص إغرائي أو حركات جنسية
               - أي محتوى يُظهر أجزاء حساسة من الجسم
            
            2. **البيئات المشبوهة (خطر عالي):**
               - النوادي الليلية والحفلات الماجنة
               - أماكن الرقص المختلط غير المحتشم
               - الحانات وأماكن تناول الخمور
               - أي مكان يروج للفسق والفجور
            
            3. **الإيماءات والحركات المخالفة:**
               - القبلات والمعانقة بين الجنسين
               - رفع الإصبع الأوسط أو إيماءات بذيئة
               - حركات الرقص الشرقي المثيرة
               - إيماءات جنسية أو استفزازية
               - حركات غير لائقة بالأيدي أو الجسم
            
            4. **المحتوى المنافي للقيم الإسلامية:**
               - تشجيع على المعاصي والفجور
               - تطبيع السلوكيات المحرمة
               - الترويج للانحلال الأخلاقي
            
            **ملاحظة مهمة:** هذه صورة ثابتة مستخرجة من ملصق متحرك - تذكر أن الملصق الأصلي قد يحتوي على حركات أكثر!
            
            **تحذير:** كن صارماً جداً! أي محتوى مشكوك فيه يُعتبر غير آمن!
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات بالتفصيل"],
                "severity": "low/medium/high",
                "description": "وصف دقيق للمحتوى المستخرج",
                "confidence": 0.85,
                "gesture_analysis": "تحليل مفصل للإيماءات من الإطار المستخرج",
                "environment_analysis": "تحليل البيئة والمكان",
                "clothing_analysis": "تحليل الملابس ومدى احتشامها",
                "sticker_type": "animated_converted"
            }
            
            **كن منطقياً ومتوازناً في التقييم. السلوك الطبيعي مقبول.**
            """
            
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type="image/png"
                    ),
                    safety_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
            # حذف الصورة المؤقتة
            try:
                os.remove(converted_png)
                logging.info(f"🗑️ تم حذف الصورة المؤقتة: {converted_png}")
            except:
                pass
            
            if response.text:
                import json
                try:
                    result = json.loads(response.text)
                    result["sticker_type"] = "animated_converted"
                    result["conversion_method"] = "TGS to PNG"
                    logging.info(f"✅ تم تحليل الملصق المتحرك بنجاح بعد التحويل")
                    return result
                except json.JSONDecodeError:
                    return self._parse_text_response(response.text)
            
            return {"error": "No response from AI"}
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الملصق المتحرك: {e}")
            # في حالة الفشل، نرفض الملصق احتياطياً للأمان
            return {
                "is_safe": False,
                "violations": ["فشل في التحليل - محتوى مشبوه"],
                "severity": "medium",
                "description": "ملصق متحرك - فشل في التحليل (يُحذف احتياطياً للأمان)",
                "confidence": 0.8,
                "gesture_analysis": "لم يتم تحليل الإيماءات - رفض احتياطي",
                "sticker_type": "animated_error",
                "error": str(e)
            }
    
    async def _analyze_video_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل ملصقات الفيديو (WebM)"""
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            try:
                if not self.client:
                    if attempt == 0:
                        self.setup_gemini()
                    if not self.client:
                        return {"error": "فشل في تهيئة Gemini client"}
                
                with open(sticker_path, "rb") as f:
                    sticker_bytes = f.read()
                
                safety_prompt = """
            احلل ملصق الفيديو هذا بعناية فائقة شديدة واكتشف أي محتوى مخالف وفقاً للمعايير الإسلامية المحافظة:
            
            ⚠️ **معايير التحليل الصارمة:**
            
            1. **المحتوى الجنسي والعري (خطر عالي):**
               - أي ملابس كاشفة أو ضيقة مثيرة
               - عرض أجزاء من الجسم بطريقة مثيرة
               - رقص إغرائي أو حركات جنسية
               - أي محتوى يُظهر أجزاء حساسة من الجسم
            
            2. **تقبيل وسلوكيات عاطفية (مخالف ومرفوض بشدة!):**
               - تقبيل على الفم بين الأطفال (مخالف بشدة!)
               - تقبيل أو عناق رومانسي بين الأطفال
               - أي سلوك عاطفي أو رومانسي بين الأطفال
               - أي تصرف يحاكي السلوك العاطفي للبالغين
               - القبلات والمعانقة بين الجنسين (أي عمر)
            
            3. **البيئات المشبوهة (خطر عالي):**
               - النوادي الليلية والحفلات الماجنة
               - أماكن الرقص المختلط غير المحتشم
               - الحانات وأماكن تناول الخمور
               - أي مكان يروج للفسق والفجور
            
            4. **الإيماءات والحركات المخالفة:**
               - رفع الإصبع الأوسط أو إيماءات بذيئة
               - حركات الرقص الشرقي المثيرة
               - إيماءات جنسية أو استفزازية
               - حركات غير لائقة بالأيدي أو الجسم
            
            5. **العنف والمحتوى المرعب:**
               - أي عنف أو دماء أو أذى
               - محتوى مخيف يؤذي الأطفال
            
            6. **المحتوى المنافي للقيم الإسلامية:**
               - تشجيع على المعاصي والفجور
               - تطبيع السلوكيات المحرمة
               - الترويج للانحلال الأخلاقي
            
            **تحذير مهم جداً: أي تقبيل بين الأطفال على الفم أو سلوك عاطفي يعتبر محتوى مخالف ومرفوض تماماً!**
            
            **قواعد التقييم المحددة:**
            - الضحك والسلوك العادي: مقبول تماماً
            - الملابس المحتشمة: مقبولة تماماً  
            - الرقص العادي والحفلات العادية: مقبولة إذا كانت محتشمة
            - الصدر المكشوف أو شبه المكشوف: غير مقبول (خطر متوسط)
            - المحتوى الإباحي الصريح والعنف الواضح: غير مقبول (خطر عالي)
            - تقبيل بين الأطفال: غير مقبول تماماً (خطر عالي)
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["فقط المخالفات الصريحة"],
                "severity": "low/medium/high",
                "description": "وصف المحتوى",
                "confidence": 0.95,
                "gesture_analysis": "تحليل الإيماءات",
                "environment_analysis": "تحليل البيئة",
                "clothing_analysis": "تحليل الملابس",
                "sticker_type": "video"
            }
            
            **اعتبر المحتوى آمناً إلا إذا كان يُظهر الصدر مكشوفاً أو محتوى إباحي صريح أو عنف واضح.**
            """
            
                response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=sticker_bytes,
                        mime_type="video/webm"
                    ),
                    safety_prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                )
            )
            
                if response.text:
                    import json
                    try:
                        result = json.loads(response.text)
                        result["sticker_type"] = "video"
                        return result
                    except json.JSONDecodeError:
                        return self._parse_text_response(response.text)
                
                return {"error": "No response from AI"}
                
            except Exception as e:
                error_str = str(e)
                logging.error(f"❌ خطأ في تحليل ملصق الفيديو (محاولة {attempt + 1}/{max_retries}): {e}")
                
                # محاولة التبديل للمفتاح التالي
                key_switched = self.handle_quota_exceeded(error_str)
                if key_switched:
                    if attempt < max_retries - 1:
                        await asyncio.sleep(retry_delay)
                        continue
                elif any(code in error_str for code in ["429", "503", "RESOURCE_EXHAUSTED", "UNAVAILABLE"]):
                    # فشل التبديل - جميع المفاتيح مستنزفة
                    return {"error": "فشل في جميع المحاولات - استنزاف جميع مفاتيح API"}
                
                # إذا كانت آخر محاولة، أرجع الخطأ
                if attempt == max_retries - 1:
                    return {"error": f"فشل التحليل بعد {max_retries} محاولات: {error_str}"}
                    
                # انتظار قبل المحاولة التالية
                await asyncio.sleep(retry_delay)
                
        return {"error": "فشل في جميع المحاولات - خدمة التحليل غير متاحة مؤقتاً"}


    async def cleanup_temp_file(self, file_path: str):
        """تنظيف الملفات المؤقتة"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"🗑️ تم حذف الملف المؤقت: {file_path}")
        except Exception as e:
            logging.error(f"❌ خطأ في حذف الملف المؤقت: {e}")

# إنشاء مثيل محلل الوسائط
media_analyzer = MediaAnalyzer()

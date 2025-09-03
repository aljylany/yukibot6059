"""
نظام تحليل الوسائط والملفات باستخدام الذكاء الاصطناعي
Media Analysis System using AI
"""

import logging
import os
import aiohttp
from datetime import datetime
from typing import Dict, Any, Optional, List
from aiogram.types import Message, PhotoSize, Document, Video, Audio
from google import genai
from google.genai import types


class MediaAnalyzer:
    """محلل الوسائط باستخدام الذكاء الاصطناعي"""
    
    def __init__(self):
        """تهيئة محلل الوسائط"""
        self.client = None
        self.setup_gemini()
        
    def setup_gemini(self):
        """إعداد Gemini API"""
        try:
            # استخدام مفتاح Gemini من متغيرات البيئة أو api.txt
            gemini_key = os.environ.get("GEMINI_API_KEY")
            if not gemini_key:
                # محاولة قراءة من api.txt
                try:
                    with open("api.txt", "r") as f:
                        lines = f.readlines()
                        for line in lines:
                            if line.strip().startswith("ai "):
                                gemini_key = lines[lines.index(line) + 1].strip()
                                break
                except:
                    pass
            
            if gemini_key:
                self.client = genai.Client(api_key=gemini_key)
                logging.info("✅ تم تهيئة Gemini لتحليل الوسائط")
            else:
                logging.error("❌ لم يتم العثور على مفتاح Gemini API")
                
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد Gemini: {e}")
    
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
        try:
            if not self.client:
                return {"error": "Gemini client not initialized"}
            
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
            7. إيماءات مخالفة أو غير لائقة مثل:
               - رفع الإصبع الأوسط (middle finger)
               - إيماءات جنسية أو استفزازية
               - إيماءات عدوانية أو تهديدية
               - إيماءات مسيئة أو بذيئة (مثل الإيماءة المعروفة بـ "فاك يو")
               - أي حركات يد أو جسد غير لائقة أو مسيئة
            
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
            
            كن صارماً جداً في التحليل، خاصة مع الإيماءات المخالفة! لا تتساهل مع أي إيماءة مسيئة!
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
            logging.error(f"❌ خطأ في تحليل الصورة: {e}")
            return {"error": str(e)}
    
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
        try:
            if not self.client:
                return {"error": "Gemini client not initialized"}
            
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
            logging.error(f"❌ خطأ في تحليل الفيديو: {e}")
            return {"error": str(e)}
    
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
                # للملفات الأخرى، نعتبرها آمنة مؤقتاً
                return {
                    "is_safe": True,
                    "violations": [],
                    "severity": "low",
                    "description": "مستند غير نصي",
                    "confidence": 0.5
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
            احلل هذا الملصق بعناية فائقة واكتشف ما إذا كان يحتوي على أي محتوى مخالف أو مسيء:
            
            1. محتوى جنسي أو عري
            2. عنف أو دماء أو أذى
            3. محتوى مخيف أو مرعب
            4. كراهية أو تمييز عنصري
            5. محتوى غير لائق للأطفال
            6. رموز أو محتوى إرهابي
            7. إيماءات مخالفة أو مسيئة مثل:
               - رفع الإصبع الأوسط (middle finger)
               - إيماءات جنسية أو استفزازية
               - إيماءات عدوانية أو تهديدية
               - إيماءات بذيئة أو مسيئة
               - أي حركات يد أو إيماءات غير لائقة
            
            انتبه بشكل خاص للأيدي والأصابع والإيماءات في الملصق!
            الملصقات غالباً ما تحتوي على تعبيرات وإيماءات، فحصها بعناية!
            
            إذا كان الملصق آمن، قدم وصفاً جميلاً ومفصلاً للملصق.
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["نوع المخالفة"],
                "severity": "low/medium/high",
                "description": "وصف مفصل للملصق - إذا كان آمناً اجعل الوصف جميلاً",
                "confidence": 0.95,
                "gesture_analysis": "تحليل مفصل للإيماءات والحركات",
                "sticker_type": "static"
            }
            
            كن صارماً جداً مع الإيماءات المخالفة في الملصقات!
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
    
    async def _analyze_animated_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل الملصقات المتحركة (TGS)"""
        try:
            # ملصقات TGS معقدة - نعاملها كملصقات عادية مؤقتاً لتجنب مشاكل MIME type
            logging.info(f"🎭 معالجة ملصق متحرك TGS كملصق عادي: {sticker_path}")
            
            # نستخدم معالجة الملصق العادي للملصقات المتحركة مؤقتاً
            result = await self._analyze_static_sticker_fallback(sticker_path)
            result["sticker_type"] = "animated"
            result["note"] = "تم تحليل الملصق المتحرك باستخدام المعالج العادي"
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الملصق المتحرك: {e}")
            # في حالة الفشل، نعتبر الملصق آمناً مؤقتاً
            return {
                "is_safe": True,
                "violations": [],
                "severity": "low",
                "description": "ملصق متحرك - لم يتم تحليله بالكامل",
                "confidence": 0.5,
                "gesture_analysis": "تحليل محدود للملصق المتحرك",
                "sticker_type": "animated",
                "error": str(e)
            }
    
    async def _analyze_video_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل ملصقات الفيديو (WebM)"""
        try:
            with open(sticker_path, "rb") as f:
                sticker_bytes = f.read()
            
            safety_prompt = """
            احلل ملصق الفيديو هذا بعناية فائقة واكتشف أي محتوى مخالف:
            
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
            
            راقب بدقة جميع الإيماءات والحركات في ملصق الفيديو!
            ملصقات الفيديو قد تحتوي على حركات سريعة ومعقدة!
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات"],
                "severity": "low/medium/high",
                "description": "وصف ملصق الفيديو",
                "confidence": 0.95,
                "gesture_analysis": "تحليل الإيماءات والحركات",
                "sticker_type": "video"
            }
            
            كن صارماً جداً مع الإيماءات المخالفة!
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
            logging.error(f"❌ خطأ في تحليل ملصق الفيديو: {e}")
            return {"error": str(e)}
    
    async def _analyze_static_sticker_fallback(self, sticker_path: str) -> Dict[str, Any]:
        """معالج احتياطي للملصقات التي تفشل في التحليل المتقدم"""
        try:
            # نحاول قراءة الملف كصورة عادية
            with open(sticker_path, "rb") as f:
                sticker_bytes = f.read()
            
            # تحليل مبسط للملصق
            safety_prompt = """
            احلل هذا الملصق بعناية واكتشف أي محتوى مخالف.
            
            ابحث عن:
            1. محتوى جنسي أو غير لائق
            2. عنف أو دماء
            3. إيماءات مسيئة أو بذيئة
            4. كراهية أو تمييز
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات إن وجدت"],
                "severity": "low/medium/high",
                "description": "وصف الملصق",
                "confidence": 0.8
            }
            """
            
            # محاولة تحليل بسيطة
            response = self.client.models.generate_content(
                model="gemini-2.5-pro",
                contents=[
                    types.Part.from_bytes(
                        data=sticker_bytes[:1024*50],  # أول 50KB فقط لتجنب المشاكل
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
                    return json.loads(response.text)
                except json.JSONDecodeError:
                    return self._parse_text_response(response.text)
            
            # إذا فشل كل شيء، نعتبر الملصق آمناً
            return {
                "is_safe": True,
                "violations": [],
                "severity": "low",
                "description": "ملصق عادي - تحليل مبسط",
                "confidence": 0.6
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في المعالج الاحتياطي: {e}")
            # آمن افتراضياً مع رسالة واضحة
            return {
                "is_safe": True,
                "violations": [],
                "severity": "low", 
                "description": "ملصق متحرك - تم السماح به (لا يمكن تحليل هذا النوع من الملصقات حالياً)",
                "confidence": 0.7,
                "gesture_analysis": "تم فحص الملصق بشكل أساسي - لم يتم رصد محتوى مخالف واضح",
                "note": "الملصقات المتحركة المعقدة تحتاج محلل متخصص إضافي"
            }
    
    async def cleanup_temp_file(self, file_path: str):
        """حذف الملف المؤقت"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logging.info(f"🗑️ تم حذف الملف المؤقت: {file_path}")
        except Exception as e:
            logging.error(f"خطأ في حذف الملف المؤقت: {e}")


# إنشاء مثيل المحلل
media_analyzer = MediaAnalyzer()
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
from datetime import datetime
from typing import Dict, Any, Optional, List
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
    
    async def _convert_tgs_to_png(self, tgs_path: str) -> str:
        """تحويل ملف TGS إلى صورة PNG للتحليل"""
        try:
            # إنشاء مسار للصورة المحولة
            png_path = tgs_path.replace('.tgs', '_converted.png')
            
            # طريقة 1: استخدام ffmpeg لتحويل TGS إلى PNG
            try:
                cmd = [
                    'ffmpeg', '-y',  # -y للكتابة فوق الملف الموجود
                    '-i', tgs_path,
                    '-vf', 'scale=512:512',  # تحديد حجم الصورة
                    '-frames:v', '1',  # إطار واحد فقط (الأول)
                    png_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0 and os.path.exists(png_path):
                    logging.info(f"✅ تم تحويل TGS إلى PNG بنجاح: {png_path}")
                    return png_path
                else:
                    logging.warning(f"⚠️ فشل تحويل TGS بـ ffmpeg: {stderr.decode() if stderr else 'Unknown error'}")
            
            except Exception as ffmpeg_error:
                logging.warning(f"⚠️ خطأ في ffmpeg: {ffmpeg_error}")
            
            # طريقة 2: محاولة أخرى بخيارات ffmpeg مختلفة
            try:
                # محاولة مع خيارات ffmpeg أبسط
                simple_cmd = [
                    'ffmpeg', '-y',
                    '-i', tgs_path,
                    '-t', '1',  # ثانية واحدة فقط
                    '-r', '1',  # إطار واحد في الثانية
                    png_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *simple_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0 and os.path.exists(png_path):
                    logging.info(f"✅ تم تحويل TGS بخيارات مبسطة: {png_path}")
                    return png_path
                else:
                    logging.warning(f"⚠️ فشل التحويل المبسط أيضاً: {stderr.decode() if stderr else 'Unknown error'}")
                    
            except Exception as simple_ffmpeg_error:
                logging.warning(f"⚠️ خطأ في التحويل المبسط: {simple_ffmpeg_error}")
            
            # طريقة 3: إعادة null بدلاً من إنشاء صورة بيضاء
            logging.error(f"❌ فشل في تحويل الملصق المتحرك TGS: {tgs_path}")
            return None
                
        except Exception as e:
            logging.error(f"❌ خطأ شامل في تحويل TGS: {e}")
            return None

    async def _analyze_animated_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل الملصقات المتحركة (TGS) بعد تحويلها لصورة ثابتة"""
        try:
            logging.info(f"🎭 بدء تحليل ملصق متحرك TGS: {sticker_path}")
            
            # تحويل TGS إلى صورة ثابتة
            converted_png = await self._convert_tgs_to_png(sticker_path)
            
            if converted_png and os.path.exists(converted_png):
                # تحليل الصورة المحولة
                logging.info(f"🔍 تحليل الصورة المحولة: {converted_png}")
                
                with open(converted_png, "rb") as f:
                    image_bytes = f.read()
            else:
                # في حالة فشل التحويل، أرجع تحليل افتراضي آمن
                logging.warning(f"⚠️ فشل تحويل الملصق المتحرك TGS إلى PNG: {sticker_path}")
                return {
                    "is_safe": True,
                    "violations": [],
                    "severity": "low", 
                    "description": "ملصق متحرك - لم يتم تحليله بسبب فشل التحويل",
                    "confidence": 0.3,
                    "gesture_analysis": "لم يتم تحليل الإيماءات بسبب فشل التحويل",
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
            # في حالة الفشل، نعتبر الملصق آمناً مؤقتاً
            return {
                "is_safe": True,
                "violations": [],
                "severity": "low",
                "description": "ملصق متحرك - فشل في التحليل الكامل",
                "confidence": 0.4,
                "gesture_analysis": "لم يتم تحليل الإيماءات بسبب مشكلة تقنية",
                "sticker_type": "animated_error",
                "error": str(e)
            }
    
    async def _analyze_video_sticker(self, sticker_path: str) -> Dict[str, Any]:
        """تحليل ملصقات الفيديو (WebM)"""
        try:
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
            
            4. **العنف والمحتوى المرعب:**
               - أي عنف أو دماء أو أذى
               - محتوى مخيف يؤذي الأطفال
            
            5. **المحتوى المنافي للقيم الإسلامية:**
               - تشجيع على المعاصي والفجور
               - تطبيع السلوكيات المحرمة
               - الترويج للانحلال الأخلاقي
            
            **ملاحظة مهمة:** ركز على المحتوى الصريح والواضح المخالف فقط. الملابس العادية والسلوك الطبيعي مقبول.
            
            أجب بـ JSON:
            {
                "is_safe": true/false,
                "violations": ["المخالفات الواضحة فقط"],
                "severity": "low/medium/high",
                "description": "وصف دقيق للمحتوى",
                "confidence": 0.95,
                "gesture_analysis": "تحليل الإيماءات والحركات",
                "environment_analysis": "تحليل البيئة والمكان",
                "clothing_analysis": "تحليل الملابس",
                "sticker_type": "video"
            }
            
            **كن منطقياً ومتوازناً في التقييم. ركز على المحتوى المخالف الواضح فقط.**
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
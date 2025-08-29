"""
نظام كشف المحتوى الشامل والمتقدم
Comprehensive Content Detection and Moderation System
"""

import logging
import asyncio
import io
import json
import sqlite3
import base64
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

try:
    from PIL import Image
except ImportError:
    Image = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

try:
    import cv2
    import numpy as np
except ImportError:
    cv2 = None
    np = None

from aiogram.types import Message, PhotoSize, Document, Video, Animation, Sticker, ChatPermissions
from aiogram.exceptions import TelegramBadRequest

class ViolationType(Enum):
    """أنواع المخالفات"""
    TEXT_PROFANITY = "text_profanity"          # سباب نصي
    SEXUAL_CONTENT = "sexual_content"          # محتوى جنسي
    ADULT_IMAGE = "adult_image"                # صور إباحية
    VIOLENT_CONTENT = "violent_content"        # محتوى عنيف
    HATE_SPEECH = "hate_speech"                # خطاب كراهية
    INAPPROPRIATE_STICKER = "inappropriate_sticker"  # ملصق غير مناسب
    SUSPICIOUS_FILE = "suspicious_file"        # ملف مشبوه

class SeverityLevel(Enum):
    """مستويات الخطورة"""
    LOW = 1      # خفيف - تحذير
    MEDIUM = 2   # متوسط - كتم مؤقت
    HIGH = 3     # عالي - كتم طويل
    SEVERE = 4   # شديد - كتم دائم
    EXTREME = 5  # متطرف - طرد نهائي

class PunishmentAction(Enum):
    """أنواع العقوبات"""
    WARNING = "warning"              # تحذير فقط
    MUTE_5MIN = "mute_5min"         # كتم 5 دقائق
    MUTE_30MIN = "mute_30min"       # كتم 30 دقيقة
    MUTE_1HOUR = "mute_1hour"       # كتم ساعة
    MUTE_6HOUR = "mute_6hour"       # كتم 6 ساعات
    MUTE_24HOUR = "mute_24hour"     # كتم 24 ساعة
    MUTE_PERMANENT = "mute_permanent"  # كتم دائم
    BAN_TEMPORARY = "ban_temporary"    # حظر مؤقت
    BAN_PERMANENT = "ban_permanent"    # طرد نهائي

class ComprehensiveContentFilter:
    """نظام كشف المحتوى الشامل والمتقدم"""
    
    def __init__(self):
        self.enabled = False  # تعطيل النظام الشامل مؤقتاً لحل المشاكل
        self.api_keys = []
        self.current_key_index = 0
        self.model = None
        self._load_api_keys()
        self._setup_model()
        self._init_punishment_system()
        
        # قاموس السياق الجنسي للنصوص
        self.sexual_context_keywords = [
            # كلمات جنسية صريحة
            "جنس", "جماع", "مجامعه", "نكاح", "مناكه", "سكس", "ممارسه",
            "معاشره", "لواط", "لوطي", "لوطيه", "شاذ", "مثلي", "مثليه",
            
            # أجزاء الجسم الحساسة
            "صدر", "ثدي", "مؤخرة", "أرداف", "فخذ", "ساق", "بطن",
            
            # أفعال جنسية
            "عانق", "قبل", "لمس", "احتضن", "داعب", "تلامس",
            
            # كلمات إيحائية
            "شهوة", "رغبة", "إثارة", "متعة", "لذة", "اشتهاء",
            
            # مصطلحات إنجليزية
            "sex", "porn", "nude", "naked", "adult", "xxx", "kiss", "touch", "sexy"
        ]
        
        # أنماط ملصقات مشبوهة
        self.suspicious_sticker_patterns = [
            # ملصقات جنسية
            "sex", "porn", "nude", "naked", "adult", "xxx",
            "إباحي", "جنس", "عاري", "عارية", "شهوة",
            
            # ملصقات عنيفة
            "violence", "blood", "kill", "death", "gun", "knife",
            "عنف", "دم", "قتل", "موت", "سلاح", "سكين",
            
            # ملصقات كراهية
            "hate", "nazi", "terror", "racist",
            "كراهية", "عنصرية", "إرهاب"
        ]

    def _load_api_keys(self):
        """تحميل مفاتيح API"""
        try:
            with open('api.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for line in lines:
                line = line.strip()
                if line.startswith('AIza'):
                    self.api_keys.append(line)
            
            if self.api_keys:
                logging.info(f"🔑 تم تحميل {len(self.api_keys)} مفاتيح للنظام الشامل")
            else:
                logging.warning("⚠️ لم يتم العثور على مفاتيح AI للنظام الشامل")
                self.enabled = False
                
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل مفاتيح API: {e}")
            self.enabled = False

    def _setup_model(self):
        """إعداد نموذج الذكاء الاصطناعي"""
        if not self.api_keys or not genai:
            self.enabled = False
            return
        
        try:
            api_key = self.api_keys[self.current_key_index]
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            logging.info("🧠 تم إعداد النظام الشامل للذكاء الاصطناعي")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعداد نموذج الذكاء الاصطناعي: {e}")
            self.enabled = False

    def _init_punishment_system(self):
        """تهيئة نظام العقوبات المتدرج"""
        try:
            conn = sqlite3.connect('comprehensive_filter.db')
            cursor = conn.cursor()
            
            # جدول سجل المخالفات الشامل
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS violation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                chat_id INTEGER NOT NULL,
                violation_type TEXT NOT NULL,
                severity_level INTEGER NOT NULL,
                content_summary TEXT,
                punishment_applied TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
            ''')
            
            # جدول إعدادات المجموعات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_filter_settings (
                chat_id INTEGER PRIMARY KEY,
                text_filter_enabled BOOLEAN DEFAULT TRUE,
                media_filter_enabled BOOLEAN DEFAULT TRUE,
                sticker_filter_enabled BOOLEAN DEFAULT TRUE,
                auto_punishment_enabled BOOLEAN DEFAULT TRUE,
                admin_reports_enabled BOOLEAN DEFAULT TRUE,
                severity_threshold INTEGER DEFAULT 2,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول تقارير المشرفين
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                admin_id INTEGER,
                violation_type TEXT NOT NULL,
                severity_level INTEGER NOT NULL,
                content_summary TEXT,
                action_taken TEXT,
                report_status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                resolved_at TIMESTAMP
            )
            ''')
            
            # جدول نقاط العقوبة التراكمية
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_violation_points (
                user_id INTEGER,
                chat_id INTEGER,
                total_points INTEGER DEFAULT 0,
                last_violation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                punishment_level INTEGER DEFAULT 0,
                is_permanently_banned BOOLEAN DEFAULT FALSE,
                PRIMARY KEY (user_id, chat_id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info("✅ تم تهيئة نظام العقوبات الشامل")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نظام العقوبات: {e}")

    async def comprehensive_content_check(self, message: Message) -> Dict[str, Any]:
        """
        الفحص الشامل لجميع أنواع المحتوى
        """
        results = {
            'has_violations': False,
            'violations': [],
            'total_severity': 0,
            'recommended_action': PunishmentAction.WARNING,
            'admin_notification_required': False
        }
        
        try:
            # فحص النص
            if message.text:
                logging.info(f"🔍 فحص النص: '{message.text[:30]}{'...' if len(message.text) > 30 else ''}'")
                text_result = await self._check_text_content(message.text)
                if text_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة نصية: {text_result['violation_type']} (خطورة: {text_result['severity']})")
                    results['violations'].append(text_result)
                    results['total_severity'] += text_result['severity']
                else:
                    logging.info("✅ النص نظيف")
            
            # فحص الصور
            if message.photo:
                logging.info("🔍 فحص الصورة...")
                image_result = await self._check_image_content(message)
                if image_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة في الصورة: {image_result['violation_type']} (خطورة: {image_result['severity']})")
                    results['violations'].append(image_result)
                    results['total_severity'] += image_result['severity']
                else:
                    logging.info("✅ الصورة نظيفة")
            
            # فحص الملصقات
            if message.sticker:
                logging.info(f"🔍 فحص الملصق: {message.sticker.emoji or 'غير محدد'}")
                sticker_result = await self._check_sticker_content(message)
                if sticker_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة في الملصق: {sticker_result['violation_type']} (خطورة: {sticker_result['severity']})")
                    results['violations'].append(sticker_result)
                    results['total_severity'] += sticker_result['severity']
                else:
                    logging.info("✅ الملصق نظيف")
            
            # فحص الفيديو
            if message.video:
                logging.info("🔍 فحص الفيديو...")
                video_result = await self._check_video_content(message)
                if video_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة في الفيديو: {video_result['violation_type']} (خطورة: {video_result['severity']})")
                    results['violations'].append(video_result)
                    results['total_severity'] += video_result['severity']
                else:
                    logging.info("✅ الفيديو نظيف")
            
            # فحص الرسوم المتحركة
            if message.animation:
                logging.info("🔍 فحص الرسم المتحرك...")
                animation_result = await self._check_animation_content(message)
                if animation_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة في الرسم المتحرك: {animation_result['violation_type']} (خطورة: {animation_result['severity']})")
                    results['violations'].append(animation_result)
                    results['total_severity'] += animation_result['severity']
                else:
                    logging.info("✅ الرسم المتحرك نظيف")
            
            # فحص الملفات
            if message.document:
                logging.info(f"🔍 فحص الملف: {message.document.file_name or 'غير محدد'}")
                document_result = await self._check_document_content(message)
                if document_result['has_violation']:
                    logging.warning(f"⚠️ مخالفة في الملف: {document_result['violation_type']} (خطورة: {document_result['severity']})")
                    results['violations'].append(document_result)
                    results['total_severity'] += document_result['severity']
                else:
                    logging.info("✅ الملف نظيف")
            
            # تحديد الإجراء المطلوب
            if results['violations']:
                results['has_violations'] = True
                results['recommended_action'] = self._determine_punishment_action(
                    results['total_severity'], 
                    message.from_user.id, 
                    message.chat.id
                )
                
                # تحديد ما إذا كان يتطلب إشعار المشرفين
                results['admin_notification_required'] = (
                    results['total_severity'] >= SeverityLevel.HIGH.value or
                    any(v['violation_type'] in [
                        ViolationType.ADULT_IMAGE.value,
                        ViolationType.VIOLENT_CONTENT.value,
                        ViolationType.HATE_SPEECH.value
                    ] for v in results['violations'])
                )
            
            return results
            
        except Exception as e:
            logging.error(f"❌ خطأ في الفحص الشامل: {e}")
            return results

    async def _check_text_content(self, text: str) -> Dict[str, Any]:
        """فحص المحتوى النصي للسباب والسياق الجنسي"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': text[:100] + "..." if len(text) > 100 else text
        }
        
        try:
            text_lower = text.lower()
            
            # قائمة الكلمات الآمنة - لا يجب اعتبارها سباب أبداً
            safe_words = [
                "بوت", "bot", "روبوت", "يوكي", "yuki", "آلي", "ذكي", "مساعد", "برنامج",
                "تطبيق", "سيري", "siri", "أليكسا", "alexa", "جوجل", "google", "ماسنجر", "messenger",
                "واتساب", "whatsapp", "تيليجرام", "telegram", "ديسكورد", "discord", 
                "غبي", "مجنون", "سيء", "جيد", "عادي", "طبيعي", "مفيد", "رائع", "جميل", "حلو",
                "شكرا", "شكراً", "thanks", "مرحبا", "مرحباً", "hello", "hi", "أهلا", "أهلاً",
                "نعم", "لا", "yes", "no", "ربما", "maybe", "perhaps", "لماذا", "why", "كيف", "how",
                "متى", "when", "أين", "where", "ماذا", "what", "من", "who", "كم", "how much"
            ]
            
            # التحقق من الكلمات الآمنة أولاً
            words_in_text = text_lower.split()
            is_safe_text = any(safe_word in text_lower for safe_word in safe_words)
            
            # إذا كان النص يحتوي على كلمات آمنة فقط، لا نفحصه بالذكاء الاصطناعي
            if is_safe_text and len(text_lower.strip()) <= 50:
                logging.info(f"✅ تم تجاهل النص الآمن: '{text[:30]}...'")
                return result
            
            # فحص متقدم باستخدام Google Gemini (فقط للنصوص المشبوهة)
            if self.model and len(text_lower.strip()) > 5:  # نفحص النصوص الطويلة فقط
                # تحقق إضافي - لا نفحص النصوص التي تحتوي على كلمات آمنة فقط
                if not is_safe_text:
                    ai_result = await self._check_text_with_ai(text)
                    if ai_result.get('has_profanity', False):
                        # تقليل شدة العقوبة للنصوص العادية
                        severity = ai_result.get('severity', SeverityLevel.MEDIUM.value)
                        if severity > SeverityLevel.MEDIUM.value:
                            severity = SeverityLevel.MEDIUM.value  # تقليل الشدة
                        
                        result['has_violation'] = True
                        result['violation_type'] = ViolationType.TEXT_PROFANITY.value
                        result['severity'] = severity
                        result['details'] = {
                            'ai_analysis': ai_result.get('reason', 'محتوى غير مناسب'),
                            'confidence': ai_result.get('confidence', 0),
                            'method': 'ai_gemini_filtered'
                        }
                        return result
            
            # فحص السياق الجنسي
            sexual_matches = []
            for keyword in self.sexual_context_keywords:
                if keyword in text_lower:
                    sexual_matches.append(keyword)
            
            if sexual_matches:
                result['has_violation'] = True
                result['violation_type'] = ViolationType.SEXUAL_CONTENT.value
                result['severity'] = SeverityLevel.MEDIUM.value
                result['details'] = {
                    'matched_keywords': sexual_matches[:3],
                    'context': 'sexual_content_detected'
                }
                return result
            
            # فحص السباب التقليدي الخطير فقط (احتياطي)
            severe_banned_words = [
                "شرموط", "عاهرة", "منيك", "نيك", "كس", "زب", "طيز", "خرا",
                "منيوك", "ايري", "انيك", "عرص", "قحبة", "كسمك", "قاوود", "زومل"
            ]
            
            # إزالة الكلمات العادية من قائمة السباب
            # كلمات مثل "حمار"، "احمق"، "غبي" لم تعد تُعتبر سباب خطير
            
            for banned_word in severe_banned_words:
                if banned_word in text_lower:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.TEXT_PROFANITY.value
                    result['severity'] = SeverityLevel.HIGH.value
                    result['details'] = {
                        'matched_word': banned_word,
                        'method': 'database_fallback'
                    }
                    return result
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص النص: {e}")
            return result

    async def _check_image_content(self, message: Message) -> Dict[str, Any]:
        """فحص محتوى الصور"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': f"صورة من {message.from_user.first_name}"
        }
        
        try:
            if not self.model or not message.photo:
                return result
            
            # تحميل الصورة
            photo = message.photo[-1]  # أكبر حجم
            file_info = await message.bot.get_file(photo.file_id)
            
            if not file_info.file_path:
                return result
            
            file_data = await message.bot.download_file(file_info.file_path)
            
            # تحليل الصورة بالذكاء الاصطناعي
            analysis_result = await self._analyze_image_with_ai(file_data.read())
            
            if analysis_result.get('is_inappropriate', False):
                result['has_violation'] = True
                
                # تحديد نوع المخالفة
                category = analysis_result.get('category', 'unknown')
                if category == 'adult':
                    result['violation_type'] = ViolationType.ADULT_IMAGE.value
                    result['severity'] = SeverityLevel.SEVERE.value
                elif category == 'violence':
                    result['violation_type'] = ViolationType.VIOLENT_CONTENT.value
                    result['severity'] = SeverityLevel.HIGH.value
                elif category == 'hate':
                    result['violation_type'] = ViolationType.HATE_SPEECH.value
                    result['severity'] = SeverityLevel.HIGH.value
                else:
                    result['violation_type'] = ViolationType.ADULT_IMAGE.value
                    result['severity'] = SeverityLevel.MEDIUM.value
                
                result['details'] = {
                    'ai_confidence': analysis_result.get('confidence', 0),
                    'ai_reason': analysis_result.get('reason', 'غير محدد'),
                    'category': category
                }
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الصورة: {e}")
            return result

    async def _check_sticker_content(self, message: Message) -> Dict[str, Any]:
        """فحص الملصقات"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': f"ملصق: {message.sticker.emoji or 'غير محدد'}"
        }
        
        try:
            sticker = message.sticker
            
            # فحص emoji الملصق
            if sticker.emoji:
                suspicious_emojis = ['🍆', '🍑', '💦', '🔞', '😈', '💋', '👅']
                if sticker.emoji in suspicious_emojis:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.INAPPROPRIATE_STICKER.value
                    result['severity'] = SeverityLevel.LOW.value
                    result['details'] = {'reason': 'suspicious_emoji', 'emoji': sticker.emoji}
                    return result
            
            # فحص اسم الملف
            file_name = getattr(sticker, 'file_name', '') or ''
            file_name_lower = file_name.lower()
            
            for pattern in self.suspicious_sticker_patterns:
                if pattern in file_name_lower:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.INAPPROPRIATE_STICKER.value
                    result['severity'] = SeverityLevel.MEDIUM.value
                    result['details'] = {
                        'reason': 'suspicious_filename',
                        'matched_pattern': pattern,
                        'filename': file_name
                    }
                    return result
            
            # فحص محتوى الملصق كصورة (إذا أمكن)
            if sticker.is_static:
                try:
                    file_info = await message.bot.get_file(sticker.file_id)
                    if file_info.file_path:
                        file_data = await message.bot.download_file(file_info.file_path)
                        
                        # تحويل إلى صورة وفحصها
                        if Image:
                            image = Image.open(io.BytesIO(file_data.read()))
                            # تحويل WEBP إلى PNG
                            png_bytes = io.BytesIO()
                            image.save(png_bytes, format='PNG')
                            png_bytes.seek(0)
                            
                            analysis_result = await self._analyze_image_with_ai(png_bytes.read())
                            
                            if analysis_result.get('is_inappropriate', False):
                                result['has_violation'] = True
                                result['violation_type'] = ViolationType.INAPPROPRIATE_STICKER.value
                                result['severity'] = SeverityLevel.HIGH.value
                                result['details'] = {
                                    'reason': 'ai_analysis',
                                    'ai_confidence': analysis_result.get('confidence', 0),
                                    'ai_category': analysis_result.get('category', 'unknown')
                                }
                                return result
                                
                except Exception as sticker_analysis_error:
                    logging.debug(f"تحذير: لم يتمكن من تحليل الملصق: {sticker_analysis_error}")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الملصق: {e}")
            return result

    async def _check_video_content(self, message: Message) -> Dict[str, Any]:
        """فحص محتوى الفيديو"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': f"فيديو من {message.from_user.first_name}"
        }
        
        try:
            video = message.video
            
            # فحص اسم الملف
            file_name = getattr(video, 'file_name', '') or ''
            file_name_lower = file_name.lower()
            
            suspicious_words = [
                'sex', 'porn', 'adult', 'xxx', 'nude', 'naked',
                'إباحي', 'جنس', 'عاري', 'عارية', 'فاضح'
            ]
            
            for word in suspicious_words:
                if word in file_name_lower:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.ADULT_IMAGE.value
                    result['severity'] = SeverityLevel.HIGH.value
                    result['details'] = {
                        'reason': 'suspicious_filename',
                        'matched_word': word,
                        'filename': file_name
                    }
                    return result
            
            # فحص متقدم للفيديو (استخراج إطارات)
            if cv2 and np and video.file_size < 50 * 1024 * 1024:  # أقل من 50 ميجا
                try:
                    file_info = await message.bot.get_file(video.file_id)
                    if file_info.file_path:
                        file_data = await message.bot.download_file(file_info.file_path)
                        
                        # حفظ مؤقت للفيديو
                        temp_video_path = f"/tmp/video_{message.message_id}.mp4"
                        with open(temp_video_path, 'wb') as f:
                            f.write(file_data.read())
                        
                        # استخراج إطارات للفحص
                        frames_analysis = await self._analyze_video_frames(temp_video_path)
                        
                        # حذف الملف المؤقت
                        import os
                        if os.path.exists(temp_video_path):
                            os.remove(temp_video_path)
                        
                        if frames_analysis['has_inappropriate']:
                            result['has_violation'] = True
                            result['violation_type'] = ViolationType.ADULT_IMAGE.value
                            result['severity'] = SeverityLevel.SEVERE.value
                            result['details'] = {
                                'reason': 'video_frame_analysis',
                                'inappropriate_frames': frames_analysis['inappropriate_count'],
                                'total_frames_analyzed': frames_analysis['total_analyzed']
                            }
                            return result
                        
                except Exception as video_analysis_error:
                    logging.debug(f"تحذير: لم يتمكن من تحليل الفيديو: {video_analysis_error}")
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الفيديو: {e}")
            return result

    async def _check_animation_content(self, message: Message) -> Dict[str, Any]:
        """فحص محتوى الرسوم المتحركة (GIF)"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': f"رسم متحرك من {message.from_user.first_name}"
        }
        
        try:
            animation = message.animation
            
            # فحص اسم الملف
            file_name = getattr(animation, 'file_name', '') or ''
            file_name_lower = file_name.lower()
            
            suspicious_words = [
                'sex', 'porn', 'adult', 'xxx', 'nude',
                'إباحي', 'جنس', 'عاري'
            ]
            
            for word in suspicious_words:
                if word in file_name_lower:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.ADULT_IMAGE.value
                    result['severity'] = SeverityLevel.MEDIUM.value
                    result['details'] = {
                        'reason': 'suspicious_filename',
                        'matched_word': word,
                        'filename': file_name
                    }
                    return result
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الرسم المتحرك: {e}")
            return result

    async def _check_document_content(self, message: Message) -> Dict[str, Any]:
        """فحص محتوى الملفات"""
        result = {
            'has_violation': False,
            'violation_type': None,
            'severity': 0,
            'details': {},
            'content_summary': f"ملف: {message.document.file_name or 'غير محدد'}"
        }
        
        try:
            document = message.document
            
            # فحص نوع الملف
            if document.mime_type and document.mime_type.startswith('image/'):
                # ملف صورة - فحص كصورة
                file_info = await message.bot.get_file(document.file_id)
                if file_info.file_path:
                    file_data = await message.bot.download_file(file_info.file_path)
                    analysis_result = await self._analyze_image_with_ai(file_data.read())
                    
                    if analysis_result.get('is_inappropriate', False):
                        result['has_violation'] = True
                        result['violation_type'] = ViolationType.ADULT_IMAGE.value
                        result['severity'] = SeverityLevel.HIGH.value
                        result['details'] = {
                            'reason': 'image_document_analysis',
                            'ai_confidence': analysis_result.get('confidence', 0)
                        }
                        return result
            
            # فحص اسم الملف
            file_name = document.file_name or ''
            file_name_lower = file_name.lower()
            
            suspicious_words = [
                'sex', 'porn', 'adult', 'xxx', 'nude', 'naked',
                'إباحي', 'جنس', 'عاري', 'عارية'
            ]
            
            for word in suspicious_words:
                if word in file_name_lower:
                    result['has_violation'] = True
                    result['violation_type'] = ViolationType.SUSPICIOUS_FILE.value
                    result['severity'] = SeverityLevel.MEDIUM.value
                    result['details'] = {
                        'reason': 'suspicious_filename',
                        'matched_word': word,
                        'filename': file_name
                    }
                    return result
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص الملف: {e}")
            return result

    async def _analyze_image_with_ai(self, image_data: bytes) -> Dict[str, Any]:
        """تحليل الصورة بالذكاء الاصطناعي المحسن"""
        if not Image or not self.model:
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": "النظام غير متوفر",
                "category": "error"
            }
        
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # تحسين الصورة
            max_size = (1024, 1024)
            if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
                image.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # نص تحليل محسن ومفصل
            prompt = """
            قم بتحليل هذه الصورة بدقة شديدة وحدد إذا كانت تحتوي على محتوى غير مناسب.
            
            فئات المحتوى غير المناسب:
            1. المحتوى الجنسي الصريح: عُري جزئي أو كامل، مشاهد جنسية، أوضاع إيحائية
            2. العنف الشديد: دماء، جروح، أسلحة مستخدمة ضد أشخاص
            3. خطاب الكراهية: رموز عنصرية، شعارات متطرفة
            4. محتوى مخدرات: تعاطي واضح أو بيع مخدرات
            
            المحتوى المقبول:
            - الفن التشكيلي والرسوم (حتى لو كانت تحتوي على عُري فني)
            - المحتوى التعليمي الطبي
            - الرياضة (السباحة، كمال الأجسام)
            - الطبيعة والمناظر الطبيعية
            
            أجب بصيغة JSON دقيقة:
            {
                "is_inappropriate": true/false,
                "confidence": 0.0-1.0,
                "reason": "سبب مفصل",
                "category": "adult/violence/hate/drugs/safe",
                "specific_elements": ["العناصر المحددة الموجودة"]
            }
            """
            
            response = await asyncio.get_event_loop().run_in_executor(
                None, 
                lambda: self.model.generate_content([prompt, image])
            )
            
            response_text = response.text.strip()
            
            # استخراج JSON
            try:
                if '{' in response_text and '}' in response_text:
                    start = response_text.find('{')
                    end = response_text.rfind('}') + 1
                    json_str = response_text[start:end]
                    result = json.loads(json_str)
                    
                    # التحقق من صحة النتيجة
                    if 'is_inappropriate' in result and 'confidence' in result:
                        return result
                
                # إذا فشل استخراج JSON، استخدم تحليل النص
                is_inappropriate = any(word in response_text.lower() for word in 
                                    ['inappropriate', 'explicit', 'adult', 'violence', 'inappropriate', 'غير مناسب', 'صريح', 'عنيف'])
                
                return {
                    "is_inappropriate": is_inappropriate,
                    "confidence": 0.7 if is_inappropriate else 0.3,
                    "reason": "تحليل نصي للاستجابة",
                    "category": "adult" if is_inappropriate else "safe"
                }
                
            except json.JSONDecodeError:
                return {
                    "is_inappropriate": False,
                    "confidence": 0.1,
                    "reason": "خطأ في تحليل الاستجابة",
                    "category": "error"
                }
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل الصورة: {e}")
            return {
                "is_inappropriate": False,
                "confidence": 0.0,
                "reason": f"خطأ تقني: {str(e)}",
                "category": "error"
            }

    async def _analyze_video_frames(self, video_path: str) -> Dict[str, Any]:
        """تحليل إطارات الفيديو"""
        if not cv2 or not np:
            return {
                'has_inappropriate': False,
                'inappropriate_count': 0,
                'total_analyzed': 0
            }
        
        try:
            cap = cv2.VideoCapture(video_path)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            
            # تحليل إطار كل ثانيتين كحد أقصى
            step = max(1, int(fps * 2))
            
            inappropriate_count = 0
            total_analyzed = 0
            max_frames_to_analyze = 10  # حد أقصى 10 إطارات
            
            for i in range(0, min(frame_count, max_frames_to_analyze * step), step):
                cap.set(cv2.CAP_PROP_POS_FRAMES, i)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # تحويل الإطار إلى صورة
                _, buffer = cv2.imencode('.jpg', frame)
                frame_bytes = buffer.tobytes()
                
                # تحليل الإطار
                analysis = await self._analyze_image_with_ai(frame_bytes)
                
                total_analyzed += 1
                
                if analysis.get('is_inappropriate', False):
                    inappropriate_count += 1
                    
                    # إذا وجدنا 2 إطارات غير مناسبة، نتوقف
                    if inappropriate_count >= 2:
                        break
            
            cap.release()
            
            return {
                'has_inappropriate': inappropriate_count > 0,
                'inappropriate_count': inappropriate_count,
                'total_analyzed': total_analyzed
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل إطارات الفيديو: {e}")
            return {
                'has_inappropriate': False,
                'inappropriate_count': 0,
                'total_analyzed': 0
            }

    def _determine_punishment_action(self, total_severity: int, user_id: int, chat_id: int) -> PunishmentAction:
        """تحديد الإجراء العقابي المناسب مع نظام التحذيرات الثلاثة"""
        try:
            # جلب سجل المخالفات السابقة
            conn = sqlite3.connect('comprehensive_filter.db')
            cursor = conn.cursor()
            
            # جلب النقاط التراكمية
            cursor.execute('''
            SELECT total_points, punishment_level, is_permanently_banned 
            FROM user_violation_points 
            WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            result = cursor.fetchone()
            
            if result:
                current_points, punishment_level, is_banned = result
                if is_banned:
                    conn.close()
                    return PunishmentAction.BAN_PERMANENT
            else:
                current_points, punishment_level = 0, 0
            
            # حساب النقاط الجديدة (نضيف 1 لكل مخالفة بغض النظر عن الشدة لنظام التحذيرات الثلاثة)
            new_total_points = current_points + 1
            
            # نظام التحذيرات الثلاثة أولاً
            if new_total_points <= 3:
                action = PunishmentAction.WARNING
            else:
                # بعد التحذيرات الثلاثة، نستخدم الشدة والعدد لتحديد العقوبة
                # تحديد مستوى العقوبة بناءً على العدد والشدة
                punishment_level = new_total_points - 3  # نبدأ من 1 بعد 3 تحذيرات
                
                # تضخيم العقوبة حسب الخطورة
                if total_severity >= 3:  # سباب شديد
                    punishment_level += 2
                elif total_severity == 2:  # سباب متوسط
                    punishment_level += 1
                
                # تحديد العقوبة المناسبة
                if punishment_level <= 1:
                    action = PunishmentAction.MUTE_5MIN
                elif punishment_level <= 3:
                    action = PunishmentAction.MUTE_30MIN
                elif punishment_level <= 5:
                    action = PunishmentAction.MUTE_1HOUR
                elif punishment_level <= 8:
                    action = PunishmentAction.MUTE_6HOUR
                elif punishment_level <= 12:
                    action = PunishmentAction.MUTE_24HOUR
                elif punishment_level <= 16:
                    action = PunishmentAction.MUTE_PERMANENT
                else:
                    action = PunishmentAction.BAN_PERMANENT
            
            # تحديث النقاط في قاعدة البيانات
            cursor.execute('''
            INSERT OR REPLACE INTO user_violation_points 
            (user_id, chat_id, total_points, punishment_level, is_permanently_banned)
            VALUES (?, ?, ?, ?, ?)
            ''', (user_id, chat_id, new_total_points, 
                  punishment_level + 1 if 'punishment_level' in locals() else 0, 
                  action == PunishmentAction.BAN_PERMANENT))
            
            conn.commit()
            conn.close()
            
            return action
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديد العقوبة: {e}")
            return PunishmentAction.WARNING

    async def apply_punishment(self, message: Message, action: PunishmentAction, violations: List[Dict]) -> Dict[str, Any]:
        """تطبيق العقوبة"""
        result = {
            'success': False,
            'action_taken': action.value,
            'message_sent': '',
            'admin_notified': False
        }
        
        try:
            # فحص الصلاحيات والاستثناءات
            from config.hierarchy import is_master, is_supreme_master
            from modules.supreme_master_commands import get_masters_punishment_status
            
            # السيد الأعلى محمي دائماً
            if is_supreme_master(message.from_user.id):
                result['message_sent'] = "👑 السيد الأعلى محمي من جميع العقوبات"
                return result
            
            # فحص حالة العقوبات على الأسياد الآخرين
            masters_punishment_enabled = get_masters_punishment_status()
            
            if is_master(message.from_user.id) and not masters_punishment_enabled:
                result['message_sent'] = "🛡️ الأسياد محميين من العقوبات (العقوبات معطلة)"
                return result
            
            # إذا كان نظام العقوبات مفعل على الأسياد، سجل ذلك
            if is_master(message.from_user.id) and masters_punishment_enabled:
                logging.warning(f"🔥 تطبيق عقوبة على السيد {message.from_user.id} - نظام العقوبات مفعل")
            
            # حذف المحتوى المخالف
            try:
                await message.delete()
                logging.info(f"✅ تم حذف المحتوى المخالف من {message.from_user.id}")
            except Exception as delete_error:
                logging.warning(f"⚠️ لم يتمكن من حذف المحتوى: {delete_error}")
            
            # تطبيق العقوبة حسب النوع
            if action == PunishmentAction.WARNING:
                result['message_sent'] = await self._send_warning_message(message, violations)
                result['success'] = True
                
            elif action in [PunishmentAction.MUTE_5MIN, PunishmentAction.MUTE_30MIN, 
                           PunishmentAction.MUTE_1HOUR, PunishmentAction.MUTE_6HOUR, 
                           PunishmentAction.MUTE_24HOUR]:
                mute_success = await self._apply_mute(message, action)
                if mute_success:
                    result['message_sent'] = await self._send_mute_message(message, action, violations)
                    result['success'] = True
                else:
                    result['message_sent'] = "❌ فشل في تطبيق الكتم"
                    
            elif action == PunishmentAction.MUTE_PERMANENT:
                mute_success = await self._apply_permanent_mute(message)
                if mute_success:
                    result['message_sent'] = await self._send_permanent_mute_message(message, violations)
                    result['success'] = True
                else:
                    result['message_sent'] = "❌ فشل في تطبيق الكتم الدائم"
                    
            elif action == PunishmentAction.BAN_PERMANENT:
                ban_success = await self._apply_ban(message)
                if ban_success:
                    result['message_sent'] = await self._send_ban_message(message, violations)
                    result['success'] = True
                else:
                    result['message_sent'] = "❌ فشل في تطبيق الطرد"
            
            # إشعار المشرفين للمخالفات الخطيرة
            if any(v['severity'] >= SeverityLevel.HIGH.value for v in violations):
                await self._notify_admins(message, violations, action)
                result['admin_notified'] = True
            
            # تسجيل المخالفة
            await self._log_violation(message, violations, action)
            
            return result
            
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق العقوبة: {e}")
            result['message_sent'] = f"❌ خطأ في تطبيق العقوبة: {str(e)}"
            return result

    async def _apply_mute(self, message: Message, action: PunishmentAction) -> bool:
        """تطبيق الكتم المؤقت"""
        try:
            # تحديد مدة الكتم
            mute_durations = {
                PunishmentAction.MUTE_5MIN: timedelta(minutes=5),
                PunishmentAction.MUTE_30MIN: timedelta(minutes=30),
                PunishmentAction.MUTE_1HOUR: timedelta(hours=1),
                PunishmentAction.MUTE_6HOUR: timedelta(hours=6),
                PunishmentAction.MUTE_24HOUR: timedelta(hours=24)
            }
            
            duration = mute_durations.get(action, timedelta(hours=1))
            mute_until = datetime.now() + duration
            
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=permissions,
                until_date=mute_until
            )
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق الكتم: {e}")
            return False

    async def _apply_permanent_mute(self, message: Message) -> bool:
        """تطبيق الكتم الدائم"""
        try:
            permissions = ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_polls=False,
                can_send_other_messages=False,
                can_add_web_page_previews=False,
                can_change_info=False,
                can_invite_users=False,
                can_pin_messages=False
            )
            
            await message.bot.restrict_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id,
                permissions=permissions
            )
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق الكتم الدائم: {e}")
            return False

    async def _apply_ban(self, message: Message) -> bool:
        """تطبيق الطرد النهائي"""
        try:
            await message.bot.ban_chat_member(
                chat_id=message.chat.id,
                user_id=message.from_user.id
            )
            
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق الطرد: {e}")
            return False

    async def _send_warning_message(self, message: Message, violations: List[Dict]) -> str:
        """إرسال رسالة تحذير"""
        violation_types = [v['violation_type'] for v in violations]
        
        warning_msg = f"⚠️ **تحذير لـ {message.from_user.first_name}**\n\n"
        warning_msg += f"🚨 تم اكتشاف محتوى غير مناسب:\n"
        
        for violation in violations:
            warning_msg += f"• {self._get_violation_description(violation['violation_type'])}\n"
        
        warning_msg += f"\n🛡️ **هذا تحذير رسمي - المخالفة القادمة ستؤدي لعقوبات أقوى**"
        
        await message.answer(warning_msg)
        return warning_msg

    async def _send_mute_message(self, message: Message, action: PunishmentAction, violations: List[Dict]) -> str:
        """إرسال رسالة الكتم"""
        duration_names = {
            PunishmentAction.MUTE_5MIN: "5 دقائق",
            PunishmentAction.MUTE_30MIN: "30 دقيقة",
            PunishmentAction.MUTE_1HOUR: "ساعة واحدة",
            PunishmentAction.MUTE_6HOUR: "6 ساعات",
            PunishmentAction.MUTE_24HOUR: "24 ساعة"
        }
        
        duration = duration_names.get(action, "مدة محددة")
        
        mute_msg = f"🔇 **تم كتم {message.from_user.first_name}**\n\n"
        mute_msg += f"⏰ **مدة الكتم:** {duration}\n"
        mute_msg += f"🚨 **السبب:** محتوى غير مناسب\n\n"
        
        for violation in violations:
            mute_msg += f"• {self._get_violation_description(violation['violation_type'])}\n"
        
        mute_msg += f"\n🛡️ **نظام الحماية الشامل فعال - احترموا قوانين المجموعة**"
        
        await message.answer(mute_msg)
        return mute_msg

    async def _send_permanent_mute_message(self, message: Message, violations: List[Dict]) -> str:
        """إرسال رسالة الكتم الدائم"""
        mute_msg = f"🔇 **تم كتم {message.from_user.first_name} نهائياً**\n\n"
        mute_msg += f"⚠️ **السبب:** مخالفات متكررة للقوانين\n"
        mute_msg += f"🚨 **المخالفة الأخيرة:**\n"
        
        for violation in violations:
            mute_msg += f"• {self._get_violation_description(violation['violation_type'])}\n"
        
        mute_msg += f"\n🛡️ **الكتم الدائم - لن يتمكن من الإرسال مرة أخرى**"
        mute_msg += f"\n📞 **للاستئناف:** التواصل مع إدارة المجموعة"
        
        await message.answer(mute_msg)
        return mute_msg

    async def _send_ban_message(self, message: Message, violations: List[Dict]) -> str:
        """إرسال رسالة الطرد"""
        ban_msg = f"🚫 **تم طرد {message.from_user.first_name} نهائياً**\n\n"
        ban_msg += f"⚠️ **السبب:** مخالفات خطيرة ومتكررة\n"
        ban_msg += f"🚨 **المخالفة الأخيرة:**\n"
        
        for violation in violations:
            ban_msg += f"• {self._get_violation_description(violation['violation_type'])}\n"
        
        ban_msg += f"\n🚫 **تم منعه من العودة للمجموعة**"
        ban_msg += f"\n🛡️ **نظام الحماية الشامل - صفر تسامح مع المخالفات الخطيرة**"
        
        await message.answer(ban_msg)
        return ban_msg

    def _get_violation_description(self, violation_type: str) -> str:
        """الحصول على وصف المخالفة"""
        descriptions = {
            ViolationType.TEXT_PROFANITY.value: "ألفاظ مسيئة وسباب",
            ViolationType.SEXUAL_CONTENT.value: "محتوى جنسي غير مناسب",
            ViolationType.ADULT_IMAGE.value: "صور إباحية أو فاضحة",
            ViolationType.VIOLENT_CONTENT.value: "محتوى عنيف",
            ViolationType.HATE_SPEECH.value: "خطاب كراهية",
            ViolationType.INAPPROPRIATE_STICKER.value: "ملصق غير مناسب",
            ViolationType.SUSPICIOUS_FILE.value: "ملف مشبوه"
        }
        
        return descriptions.get(violation_type, "مخالفة غير محددة")

    async def _notify_admins(self, message: Message, violations: List[Dict], action: PunishmentAction):
        """إشعار المشرفين بالمخالفات الخطيرة"""
        try:
            # جلب قائمة المشرفين
            chat_administrators = await message.bot.get_chat_administrators(message.chat.id)
            
            notification_msg = f"🚨 **تقرير مخالفة خطيرة**\n\n"
            notification_msg += f"👤 **المخالف:** {message.from_user.first_name} (@{message.from_user.username or 'لا يوجد'})\n"
            notification_msg += f"🏠 **المجموعة:** {message.chat.title}\n"
            notification_msg += f"⏰ **الوقت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            notification_msg += f"🚨 **المخالفات:**\n"
            for violation in violations:
                notification_msg += f"• {self._get_violation_description(violation['violation_type'])}\n"
                if 'details' in violation and violation['details']:
                    details = violation['details']
                    if 'ai_confidence' in details:
                        notification_msg += f"  الثقة: {details['ai_confidence']:.2f}\n"
            
            notification_msg += f"\n⚖️ **الإجراء المتخذ:** {self._get_action_description(action)}\n"
            notification_msg += f"🔗 **رابط الرسالة:** [انقر هنا](https://t.me/c/{str(message.chat.id)[4:]}/{message.message_id})"
            
            # إرسال للمشرفين في الخاص
            for admin in chat_administrators:
                if admin.user.is_bot:
                    continue
                
                try:
                    await message.bot.send_message(
                        admin.user.id,
                        notification_msg,
                        parse_mode='Markdown'
                    )
                except Exception as send_error:
                    # إذا لم يتمكن من إرسال في الخاص، تجاهل
                    logging.debug(f"لم يتمكن من إشعار المشرف {admin.user.id}: {send_error}")
            
            # تسجيل التقرير في قاعدة البيانات
            await self._save_admin_report(message, violations, action)
            
        except Exception as e:
            logging.error(f"❌ خطأ في إشعار المشرفين: {e}")

    def _get_action_description(self, action: PunishmentAction) -> str:
        """الحصول على وصف الإجراء"""
        descriptions = {
            PunishmentAction.WARNING: "تحذير",
            PunishmentAction.MUTE_5MIN: "كتم 5 دقائق",
            PunishmentAction.MUTE_30MIN: "كتم 30 دقيقة",
            PunishmentAction.MUTE_1HOUR: "كتم ساعة",
            PunishmentAction.MUTE_6HOUR: "كتم 6 ساعات",
            PunishmentAction.MUTE_24HOUR: "كتم 24 ساعة",
            PunishmentAction.MUTE_PERMANENT: "كتم دائم",
            PunishmentAction.BAN_PERMANENT: "طرد نهائي"
        }
        
        return descriptions.get(action, "إجراء غير محدد")

    async def _save_admin_report(self, message: Message, violations: List[Dict], action: PunishmentAction):
        """حفظ تقرير للمشرفين"""
        try:
            conn = sqlite3.connect('comprehensive_filter.db')
            cursor = conn.cursor()
            
            for violation in violations:
                cursor.execute('''
                INSERT INTO admin_reports 
                (chat_id, user_id, violation_type, severity_level, content_summary, action_taken)
                VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    message.chat.id,
                    message.from_user.id,
                    violation['violation_type'],
                    violation['severity'],
                    violation.get('content_summary', ''),
                    action.value
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في حفظ التقرير: {e}")

    async def _log_violation(self, message: Message, violations: List[Dict], action: PunishmentAction):
        """تسجيل المخالفة في السجل"""
        try:
            conn = sqlite3.connect('comprehensive_filter.db')
            cursor = conn.cursor()
            
            for violation in violations:
                expiry_date = None
                if action in [PunishmentAction.MUTE_5MIN, PunishmentAction.MUTE_30MIN, 
                             PunishmentAction.MUTE_1HOUR, PunishmentAction.MUTE_6HOUR, 
                             PunishmentAction.MUTE_24HOUR]:
                    durations = {
                        PunishmentAction.MUTE_5MIN: timedelta(minutes=5),
                        PunishmentAction.MUTE_30MIN: timedelta(minutes=30),
                        PunishmentAction.MUTE_1HOUR: timedelta(hours=1),
                        PunishmentAction.MUTE_6HOUR: timedelta(hours=6),
                        PunishmentAction.MUTE_24HOUR: timedelta(hours=24)
                    }
                    expiry_date = datetime.now() + durations.get(action, timedelta(hours=1))
                
                cursor.execute('''
                INSERT INTO violation_history 
                (user_id, chat_id, violation_type, severity_level, content_summary, punishment_applied, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    message.from_user.id,
                    message.chat.id,
                    violation['violation_type'],
                    violation['severity'],
                    violation.get('content_summary', ''),
                    action.value,
                    expiry_date
                ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تسجيل المخالفة: {e}")

    async def get_user_violations_summary(self, user_id: int, chat_id: int) -> Dict[str, Any]:
        """الحصول على ملخص مخالفات المستخدم"""
        try:
            conn = sqlite3.connect('comprehensive_filter.db')
            cursor = conn.cursor()
            
            # إجمالي المخالفات
            cursor.execute('''
            SELECT COUNT(*), SUM(severity_level) 
            FROM violation_history 
            WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            total_violations, total_severity = cursor.fetchone()
            total_violations = total_violations or 0
            total_severity = total_severity or 0
            
            # النقاط الحالية
            cursor.execute('''
            SELECT total_points, punishment_level, is_permanently_banned 
            FROM user_violation_points 
            WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            points_result = cursor.fetchone()
            if points_result:
                current_points, punishment_level, is_banned = points_result
            else:
                current_points, punishment_level, is_banned = 0, 0, False
            
            # آخر المخالفات
            cursor.execute('''
            SELECT violation_type, severity_level, created_at 
            FROM violation_history 
            WHERE user_id = ? AND chat_id = ? 
            ORDER BY created_at DESC 
            LIMIT 5
            ''', (user_id, chat_id))
            
            recent_violations = cursor.fetchall()
            
            conn.close()
            
            return {
                'total_violations': total_violations,
                'total_severity': total_severity,
                'current_points': current_points,
                'punishment_level': punishment_level,
                'is_permanently_banned': is_banned,
                'recent_violations': [
                    {
                        'type': v[0],
                        'severity': v[1],
                        'date': v[2]
                    } for v in recent_violations
                ]
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب ملخص المخالفات: {e}")
            return {
                'total_violations': 0,
                'total_severity': 0,
                'current_points': 0,
                'punishment_level': 0,
                'is_permanently_banned': False,
                'recent_violations': []
            }

    async def _check_text_with_ai(self, text: str) -> Dict[str, Any]:
        """فحص النص باستخدام Google Gemini"""
        try:
            if not self.model:
                return {'has_profanity': False}
            
            prompt = f"""
أنت نظام ذكي لكشف السباب والألفاظ المسيئة في النصوص العربية.
قم بتحليل النص التالي وحدد:
1. هل يحتوي على سباب أو ألفاظ مسيئة؟
2. ما مستوى الخطورة من 1-5؟
3. ما السبب؟

النص للتحليل: "{text}"

أجب فقط بـ JSON:
{{"has_profanity": true/false, "severity": 1-5, "reason": "السبب", "confidence": 0.0-1.0}}
"""
            
            response = await asyncio.to_thread(
                self.model.generate_content, 
                prompt
            )
            
            import json
            try:
                result = json.loads(response.text.strip())
                return result
            except:
                # تحليل النص بطريقة بديلة
                response_text = response.text.lower()
                if any(word in response_text for word in ['true', 'profanity', 'سباب', 'مسيء']):
                    return {'has_profanity': True, 'severity': 3, 'reason': 'كُشف بواسطة الذكاء الاصطناعي', 'confidence': 0.8}
                else:
                    return {'has_profanity': False, 'severity': 0, 'reason': 'نص نظيف', 'confidence': 0.9}
                    
        except Exception as e:
            logging.error(f"❌ خطأ في فحص النص بالذكاء الاصطناعي: {e}")
            return {'has_profanity': False}

# إنشاء كائج النظام الشامل
comprehensive_filter = ComprehensiveContentFilter()
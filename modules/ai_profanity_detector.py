"""
نظام الكشف الذكي عن السباب باستخدام الذكاء الاصطناعي
يستخدم Google Gemini للفهم المتقدم للسياق وكشف التمويه
"""

import logging
import sqlite3
import json
import re
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import google.generativeai as genai
import os
from dataclasses import dataclass

@dataclass
class ProfanityResult:
    """نتيجة فحص السباب"""
    is_profane: bool
    confidence: float
    detected_patterns: List[str]
    obfuscation_methods: List[str]
    severity_level: int  # 1=خفيف، 2=متوسط، 3=شديد
    context_analysis: str
    learning_data: Dict

class AIProfanityDetector:
    """كاشف السباب الذكي المتطور"""
    
    def __init__(self):
        self.model = None
        self.learning_cache = {}
        self.pattern_history = {}
        self.initialize_ai()
        self.initialize_db()
        
    def initialize_ai(self):
        """تهيئة نموذج الذكاء الاصطناعي"""
        try:
            # استخدام Google Gemini المتوفر
            api_key = os.environ.get('GOOGLE_API_KEY') or os.environ.get('GEMINI_API_KEY')
            if api_key:
                genai.configure(api_key=api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                logging.info("✅ تم تهيئة نظام الكشف الذكي باستخدام Google Gemini")
            else:
                logging.error("❌ لم يتم العثور على مفتاح Google AI")
        except Exception as e:
            logging.error(f"خطأ في تهيئة AI: {e}")
    
    def initialize_db(self):
        """تهيئة قاعدة بيانات التعلم الذكي"""
        try:
            conn = sqlite3.connect('ai_profanity_learning.db')
            cursor = conn.cursor()
            
            # جدول أنماط السباب المكتشفة
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS detected_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_hash TEXT UNIQUE,
                original_text TEXT,
                cleaned_text TEXT,
                obfuscation_method TEXT,
                severity_level INTEGER,
                confidence_score REAL,
                context_info TEXT,
                detection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                usage_count INTEGER DEFAULT 1
            )
            ''')
            
            # جدول تعلم السياق
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS context_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                text_context TEXT,
                is_profane BOOLEAN,
                confidence_score REAL,
                user_feedback BOOLEAN,
                chat_id INTEGER,
                learning_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول أساليب التمويه المكتشفة
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS obfuscation_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method_name TEXT,
                pattern_regex TEXT,
                effectiveness_score REAL,
                detection_count INTEGER DEFAULT 1,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            conn.commit()
            conn.close()
            logging.info("✅ تم تهيئة قاعدة بيانات التعلم الذكي")
            
        except Exception as e:
            logging.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

    async def analyze_with_ai(self, text: str, chat_context: str = "") -> Dict:
        """تحليل النص باستخدام الذكاء الاصطناعي"""
        if not self.model:
            return {"error": "AI model not available"}
            
        try:
            prompt = f"""
            قم بتحليل النص التالي للكشف عن أي سباب أو ألفاظ مسيئة بما في ذلك الأساليب المموهة:

            النص: "{text}"
            السياق: "{chat_context}"

            احلل النص من ناحية:
            1. هل يحتوي على سباب أو ألفاظ مسيئة؟
            2. ما مستوى الثقة في الكشف (0-1)؟
            3. ما الأنماط المكتشفة؟
            4. ما أساليب التمويه المستخدمة؟
            5. ما مستوى الخطورة (1-3)؟
            6. تحليل السياق والقصد

            ملاحظات مهمة:
            - انتبه للأرقام المستخدمة كبديل للحروف (0=و، 3=ع، 5=ه، 7=ح، 8=ث)
            - انتبه للرموز والمسافات المستخدمة للتمويه (*، _، -، مسافات)
            - انتبه للكلمات المقلوبة أو المعكوسة
            - انتبه للهجات المختلفة وطرق النطق
            - انتبه للإيحاءات والتلميحات غير المباشرة

            أجب بصيغة JSON فقط:
            {{
                "is_profane": boolean,
                "confidence": float,
                "detected_patterns": [strings],
                "obfuscation_methods": [strings], 
                "severity_level": int,
                "context_analysis": "string",
                "reasoning": "string"
            }}
            """
            
            response = self.model.generate_content(prompt)
            
            # استخراج JSON من الرد
            response_text = response.text.strip()
            
            # محاولة استخراج JSON من الرد
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start != -1 and json_end != -1:
                json_text = response_text[json_start:json_end]
                return json.loads(json_text)
            else:
                # fallback إذا لم يكن الرد JSON صحيح
                return {
                    "is_profane": "سباب" in response_text or "مسيء" in response_text,
                    "confidence": 0.7,
                    "detected_patterns": [],
                    "obfuscation_methods": [],
                    "severity_level": 2,
                    "context_analysis": response_text[:200],
                    "reasoning": "تحليل تلقائي"
                }
                
        except Exception as e:
            logging.error(f"خطأ في تحليل AI: {e}")
            return {"error": str(e)}

    def detect_obfuscation_patterns(self, text: str) -> List[Dict]:
        """كشف أنماط التمويه المختلفة"""
        patterns = []
        
        # تمويه بالأرقام
        number_replacements = {
            '0': ['و', 'ص'], '1': ['ل', 'ا'], '2': ['ن'], '3': ['ع'], 
            '4': ['ر'], '5': ['ه', 'س'], '6': ['و'], '7': ['ح'], 
            '8': ['ث', 'ب'], '9': ['ق']
        }
        
        if re.search(r'[0-9]', text):
            patterns.append({
                "type": "number_substitution",
                "description": "استبدال الأرقام بالحروف",
                "confidence": 0.8
            })
        
        # تمويه بالرموز
        if re.search(r'[\*\_\-\+\=\|\\\/\.\,\!\@\#\$\%\^\&]', text):
            patterns.append({
                "type": "symbol_obfuscation", 
                "description": "استخدام الرموز للتمويه",
                "confidence": 0.9
            })
        
        # مسافات بين الحروف
        if re.search(r'[أ-ي]\s+[أ-ي]\s+[أ-ي]', text):
            patterns.append({
                "type": "letter_spacing",
                "description": "مسافات بين حروف الكلمة",
                "confidence": 0.95
            })
        
        # تكرار زائد للحروف
        if re.search(r'(.)\1{3,}', text):
            patterns.append({
                "type": "letter_repetition",
                "description": "تكرار زائد للحروف",
                "confidence": 0.7
            })
        
        # خليط عربي/إنجليزي
        if re.search(r'[a-zA-Z].*[أ-ي]|[أ-ي].*[a-zA-Z]', text):
            patterns.append({
                "type": "mixed_languages",
                "description": "خليط من اللغات",
                "confidence": 0.8
            })
        
        # كلمات معكوسة
        reversed_text = text[::-1]
        if len(text) > 3:
            patterns.append({
                "type": "potential_reversal",
                "description": "احتمالية كلمات معكوسة", 
                "confidence": 0.5,
                "reversed": reversed_text
            })
        
        return patterns

    def clean_and_normalize_text(self, text: str) -> List[str]:
        """تنظيف النص وإنتاج أشكال مختلفة للفحص"""
        variations = []
        
        # النص الأصلي
        variations.append(text)
        
        # إزالة الرموز والمسافات الزائدة
        cleaned = re.sub(r'[\*\_\-\+\=\|\\\/\.\,\!\@\#\$\%\^\&\(\)\[\]\{\}\<\>\?\~\`\"\']+', '', text)
        cleaned = re.sub(r'\s+', '', cleaned)
        if cleaned != text:
            variations.append(cleaned)
        
        # تحويل الأرقام إلى حروف
        number_replacements = {
            '0': 'و', '1': 'ل', '2': 'ن', '3': 'ع', '4': 'ر', 
            '5': 'ه', '6': 'و', '7': 'ح', '8': 'ث', '9': 'ق'
        }
        
        number_replaced = text
        for num, letter in number_replacements.items():
            number_replaced = number_replaced.replace(num, letter)
        if number_replaced != text:
            variations.append(number_replaced)
        
        # إزالة التكرارات المفرطة
        no_repeats = re.sub(r'(.)\1{2,}', r'\1', text)
        if no_repeats != text:
            variations.append(no_repeats)
        
        # تطبيق جميع التنظيفات معاً
        fully_cleaned = text.lower()
        for num, letter in number_replacements.items():
            fully_cleaned = fully_cleaned.replace(num, letter)
        fully_cleaned = re.sub(r'[\*\_\-\+\=\|\\\/\.\,\!\@\#\$\%\^\&\(\)\[\]\{\}\<\>\?\~\`\"\'\s]+', '', fully_cleaned)
        fully_cleaned = re.sub(r'(.)\1{2,}', r'\1', fully_cleaned)
        
        if fully_cleaned and fully_cleaned != text.lower():
            variations.append(fully_cleaned)
        
        # إزالة التكرارات وإرجاع القائمة
        return list(set(variations))

    def learn_from_detection(self, text: str, result: ProfanityResult, user_feedback: Optional[bool] = None):
        """التعلم من الكشوفات الجديدة"""
        try:
            # إنشاء hash للنمط
            pattern_hash = hashlib.md5(text.lower().encode()).hexdigest()
            
            conn = sqlite3.connect('ai_profanity_learning.db')
            cursor = conn.cursor()
            
            # حفظ النمط المكتشف
            cursor.execute('''
            INSERT OR REPLACE INTO detected_patterns 
            (pattern_hash, original_text, cleaned_text, severity_level, confidence_score, context_info, usage_count)
            VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT usage_count FROM detected_patterns WHERE pattern_hash = ?) + 1, 1))
            ''', (pattern_hash, text, str(result.detected_patterns), result.severity_level, 
                  result.confidence, result.context_analysis, pattern_hash))
            
            # حفظ أساليب التمويه
            for method in result.obfuscation_methods:
                cursor.execute('''
                INSERT OR IGNORE INTO obfuscation_methods (method_name, effectiveness_score)
                VALUES (?, ?)
                ''', (method, result.confidence))
            
            # حفظ تعليق السياق
            cursor.execute('''
            INSERT INTO context_learning (text_context, is_profane, confidence_score, user_feedback)
            VALUES (?, ?, ?, ?)
            ''', (text, result.is_profane, result.confidence, user_feedback))
            
            conn.commit()
            conn.close()
            
            logging.info(f"تم حفظ نمط جديد للتعلم: {pattern_hash}")
            
        except Exception as e:
            logging.error(f"خطأ في حفظ التعلم: {e}")

    async def check_message_smart(self, text: str, chat_context: str = "", chat_id: int = None) -> ProfanityResult:
        """الفحص الذكي الشامل للرسالة"""
        
        # الفحص السريع للأنماط المعروفة أولاً
        text_variations = self.clean_and_normalize_text(text)
        obfuscation_patterns = self.detect_obfuscation_patterns(text)
        
        # فحص قاعدة البيانات للأنماط المحفوظة
        known_result = await self.check_known_patterns(text_variations)
        if known_result and known_result.confidence > 0.8:
            return known_result
        
        # التحليل بالذكاء الاصطناعي
        ai_analysis = await self.analyze_with_ai(text, chat_context)
        
        if "error" in ai_analysis:
            # fallback للطريقة التقليدية
            return await self.fallback_detection(text, obfuscation_patterns)
        
        # إنشاء النتيجة النهائية
        result = ProfanityResult(
            is_profane=ai_analysis.get("is_profane", False),
            confidence=ai_analysis.get("confidence", 0.5),
            detected_patterns=ai_analysis.get("detected_patterns", []),
            obfuscation_methods=[p["type"] for p in obfuscation_patterns],
            severity_level=ai_analysis.get("severity_level", 1),
            context_analysis=ai_analysis.get("context_analysis", ""),
            learning_data={
                "original_text": text,
                "variations": text_variations,
                "ai_reasoning": ai_analysis.get("reasoning", ""),
                "obfuscation_details": obfuscation_patterns
            }
        )
        
        # التعلم من النتيجة
        if result.is_profane and result.confidence > 0.6:
            self.learn_from_detection(text, result)
        
        return result

    async def check_known_patterns(self, text_variations: List[str]) -> Optional[ProfanityResult]:
        """فحص الأنماط المحفوظة مسبقاً"""
        try:
            conn = sqlite3.connect('ai_profanity_learning.db')
            cursor = conn.cursor()
            
            for variation in text_variations:
                pattern_hash = hashlib.md5(variation.lower().encode()).hexdigest()
                cursor.execute('''
                SELECT severity_level, confidence_score, context_info, usage_count 
                FROM detected_patterns WHERE pattern_hash = ?
                ''', (pattern_hash,))
                
                result = cursor.fetchone()
                if result:
                    severity, confidence, context, usage_count = result
                    
                    # زيادة عدد الاستخدام
                    cursor.execute('''
                    UPDATE detected_patterns SET usage_count = usage_count + 1 
                    WHERE pattern_hash = ?
                    ''', (pattern_hash,))
                    
                    conn.commit()
                    conn.close()
                    
                    return ProfanityResult(
                        is_profane=True,
                        confidence=min(confidence + (usage_count * 0.1), 1.0),
                        detected_patterns=[variation],
                        obfuscation_methods=["known_pattern"],
                        severity_level=severity,
                        context_analysis=f"نمط محفوظ: {context}",
                        learning_data={"source": "database", "usage_count": usage_count}
                    )
            
            conn.close()
            return None
            
        except Exception as e:
            logging.error(f"خطأ في فحص الأنماط المحفوظة: {e}")
            return None

    async def fallback_detection(self, text: str, obfuscation_patterns: List[Dict]) -> ProfanityResult:
        """نظام الكشف الاحتياطي"""
        # قائمة كلمات أساسية للطوارئ
        basic_profanity = [
            "شرموط", "عاهرة", "منيك", "نيك", "كس", "زب", "خرا", 
            "قحبة", "عرص", "حمار", "احمق", "غبي"
        ]
        
        is_profane = False
        detected = []
        confidence = 0.3
        
        text_lower = text.lower()
        for word in basic_profanity:
            if word in text_lower:
                is_profane = True
                detected.append(word)
                confidence += 0.2
        
        # إضافة نقاط للتمويه المكتشف
        if obfuscation_patterns:
            confidence += 0.3
        
        return ProfanityResult(
            is_profane=is_profane,
            confidence=min(confidence, 1.0),
            detected_patterns=detected,
            obfuscation_methods=[p["type"] for p in obfuscation_patterns],
            severity_level=2 if is_profane else 0,
            context_analysis="فحص احتياطي أساسي",
            learning_data={"source": "fallback"}
        )

    async def get_detection_stats(self) -> Dict:
        """إحصائيات النظام"""
        try:
            conn = sqlite3.connect('ai_profanity_learning.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM detected_patterns')
            patterns_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(*) FROM context_learning')  
            learning_count = cursor.fetchone()[0]
            
            cursor.execute('SELECT COUNT(DISTINCT method_name) FROM obfuscation_methods')
            methods_count = cursor.fetchone()[0]
            
            cursor.execute('''
            SELECT method_name, detection_count FROM obfuscation_methods 
            ORDER BY detection_count DESC LIMIT 5
            ''')
            top_methods = cursor.fetchall()
            
            conn.close()
            
            return {
                "total_patterns": patterns_count,
                "learning_entries": learning_count,
                "obfuscation_methods": methods_count,
                "top_methods": top_methods,
                "system_status": "active" if self.model else "fallback_mode"
            }
            
        except Exception as e:
            logging.error(f"خطأ في الإحصائيات: {e}")
            return {"error": str(e)}

# إنشاء المثيل العام
ai_detector = AIProfanityDetector()
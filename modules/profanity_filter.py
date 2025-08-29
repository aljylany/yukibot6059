"""
نظام كشف السباب المتطور والكتم التلقائي
يستخدم قاعدة بيانات ونموذج ذكاء اصطناعي للكشف عن الألفاظ المسيئة
يقوم بكتم المستخدمين الذين يسبون ويرسل رسالة من السيدة رهف
"""

import logging
import sqlite3
import pandas as pd
import numpy as np
from aiogram.types import Message, ChatPermissions, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
# from utils.decorators import ensure_group_only  # مُعطل مؤقتاً
from datetime import datetime, timedelta
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk
import re
import os

# استيراد النظام الذكي الجديد
from .ai_profanity_detector import ai_detector, ProfanityResult

# كلمات السباب الخطيرة (درجة خطورة عالية)
SEVERE_PROFANITY = [
    # سباب جنسي بذيء وكلمات فاحشة خطيرة
    "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
    "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
    "ابن الشرموطة", "بنت الشرموطة",
    "خرا", "خراء", "يلعن", "اللعنة",
    
    # كلمات إضافية خطيرة
    "منيوك", "ايري", "انيك", "نيكك", "منيوكة", "ايرك", "ايرها",
    "انيكك", "انيكها", "منيوكو", "ايرو", "نيكو", "كسمك", "كسك",
    "كسها", "كسهم", "كسكم", "كسكن", "زبك", "زبها", "زبهم", "زبكم",
    
    # سباب خطير
    "عرص", "عرصة", "عرصه", "عرصين", "عارص", "عارصة", "عارصه",
    "قحبة", "قحبه", "قحاب", "بغي", "بغيه", "متناك", "متناكة", "متناكين",
    
    # سباب يمني بذيء خطير
    "قاوود", "قواد", "زومل", "زومله",
    "ملعون", "ملعونه",
    
    # تركيبات يمنية بذيئة خطيرة
    "يا قاوود", "يا قواد", "اخنث", "يا مخنوث",
    "ابن القاوود", "بنت القواد", "ابن الكلب", "بنت الكلب",
    
    # كلمات بذيئة إضافية خطيرة
    "انيكك", "يلعن ابوك", "يلعن ابوكي", "كول خرا", "اكل خرا",
    
    # كلمات جنسية صريحة
    "جنس", "جماع", "مجامعه", "نكاح", "مناكه", "سكس", "ممارسه",
    "معاشره", "لواط", "لوطي", "لوطيه", "شاذ انت", "شاذه انتي", "مثلي انت", "انتي مثليه"
]

# كلمات مؤذية متوسطة (لا نعتبرها سباب حقيقي)
MILD_PROFANITY = [
    "حمار", "حمارة", "حمارين", "احمق", "احمقه", "احمقين",
    "جحش", "بهيمة", "غشيم"
]

# كلمات عادية لا تُعتبر سباب (مُعطلة من الفحص)
NORMAL_WORDS = [
    "غبي", "غبيه", "غبيين", "سيء", "سيئه", "سيئين", "مجنون", "مجنونه"
]

# دمج جميع الكلمات المحظورة للتوافق مع الكود القديم
BANNED_WORDS = SEVERE_PROFANITY + MILD_PROFANITY

# صيغ مختلفة للكلمات البذيئة
BANNED_VARIATIONS = [
    # صيغ مختلفة بالأرقام والرموز للكلمات البذيئة
    "شرم0ط", "3اهرة", "من1ك", "ن1ك", "ك5", "ز8", "ط1ز",
    "من10ك", "@يري", "انن1ك", "من10وك", "@يرك", "ان1كك",
    "ق@وود", "ق0اد", "ز0مل",
    
    # صيغ بديلة للكلمات البذيئة
    "قوووود", "قااااد", "زوووومل",
    
    # بديلات إنجليزية بذيئة
    "fuck", "shit", "bitch", "asshole", "bastard", "whore", "slut",
    "motherfucker", "dickhead", "pussy", "cock", "penis", "vagina",
    
    # صيغ مختلطة بذيئة
    "كs", "nيك", "fuck you", "مخنوث", "مخنوثه", "مخنوثة", "انيكك", "kس", "zب", "tيز",
    "qاوود"
]

# دمج جميع الكلمات المحظورة
ALL_BANNED_WORDS = BANNED_WORDS + BANNED_VARIATIONS

# متغيرات النموذج العالمية
vectorizer = None
ml_model = None
protection_enabled = {}

# قاموس التحذيرات في الذاكرة
user_warnings = {}

# تحميل بيانات NLTK إذا لم تكن موجودة
try:
    import nltk
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
except Exception as e:
    logging.warning(f"تحذير: لم يتمكن من تحميل بيانات NLTK: {e}")

def init_abusive_db():
    """
    تهيئة قاعدة بيانات الألفاظ المسيئة والتحذيرات
    """
    try:
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        # جدول الكلمات المسيئة مع درجة الخطورة
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS abusive_words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT UNIQUE,
            severity INTEGER DEFAULT 1,
            added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        # جدول تحذيرات المستخدمين
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_warnings (
            user_id INTEGER,
            chat_id INTEGER,
            warnings INTEGER DEFAULT 0,
            last_warning TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, chat_id)
        )
        ''')
        
        # جدول إعدادات الحماية للمجموعات
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS group_protection_settings (
            chat_id INTEGER PRIMARY KEY,
            protection_enabled BOOLEAN DEFAULT TRUE,
            ml_threshold REAL DEFAULT 0.7,
            max_warnings INTEGER DEFAULT 3,
            mute_duration INTEGER DEFAULT 3600,
            updated_by INTEGER,
            updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        
        conn.commit()
        conn.close()
        
        # إضافة الكلمات الافتراضية
        add_default_abusive_words()
        
        logging.info("✅ تم تهيئة قاعدة بيانات الألفاظ المسيئة بنجاح")
        
    except Exception as e:
        logging.error(f"خطأ في تهيئة قاعدة البيانات: {e}")

def add_default_abusive_words():
    """
    إضافة الكلمات المسيئة الافتراضية مع درجات خطورة
    """
    try:
        # تحديد درجة الخطورة لكل كلمة (1=خفيف، 2=متوسط، 3=شديد)
        default_words_with_severity = []
        
        # كلمات شديدة الخطورة (3)
        severe_words = [
            "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
            "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
            "ابن الشرموطة", "بنت الشرموطة", "خرا", "خراء"
        ]
        for word in severe_words:
            default_words_with_severity.append((word, 3))
            
        # كلمات متوسطة الخطورة (2)
        medium_words = [
            "منيوك", "ايري", "انيك", "نيكك", "منيوكة", "ايرك", "ايرها",
            "قاوود", "قواد", "زومل", "زومله", "ملعون", "ملعونه",
            "عرص", "عرصة", "عرصه", "عرصين", "عارص", "عارصة", "عارصه",
            "حمار", "حمارة", "حمارين", "احمق", "احمقه", "احمقين", "غبي", "غبيه", "غبيين",
            "قحبة", "قحبه", "قحاب", "بغي", "بغيه", "متناك", "متناكة", "متناكين", "كسمك"
        ]
        for word in medium_words:
            default_words_with_severity.append((word, 2))
            
        # كلمات خفيفة الخطورة (1)
        light_words = ["يلعن", "اللعنة"]
        for word in light_words:
            default_words_with_severity.append((word, 1))
            
        # إضافة الكلمات لقاعدة البيانات
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        for word, severity in default_words_with_severity:
            try:
                cursor.execute('INSERT OR IGNORE INTO abusive_words (word, severity) VALUES (?, ?)', (word, severity))
            except Exception as e:
                logging.debug(f"تحذير: لم يتم إضافة '{word}': {e}")
                
        conn.commit()
        conn.close()
        
    except Exception as e:
        logging.error(f"خطأ في إضافة الكلمات الافتراضية: {e}")

def init_ml_model():
    """
    تهيئة نموذج تعلم الآلة للكشف عن الألفاظ المسيئة
    """
    global vectorizer, ml_model
    
    try:
        # بيانات تدريب عينة محسنة
        training_data = {
            'text': [
                "أنت شخص لطيف ومحترم",
                "أحب التحدث معك دائماً",
                "شكراً لك على مساعدتك الرائعة",
                "هذا عمل ممتاز ومتقن",
                "أتمنى لك يوماً سعيداً",
                "بارك الله فيك على جهودك",
                "أنت إنسان رائع حقاً",
                "أحترم وجهة نظرك تماماً",
                
                "أنت غبي جداً ولا تفهم شيء",
                "اخرس يا أحمق ولا تتكلم",
                "أنت عديم الفائدة تماماً",
                "أنت فاشل في حياتك كلها",
                "لا تفتح فمك مرة أخرى",
                "أنت مزعج ومقرف جداً",
                "اتركني في حالي أيها الغبي",
                "كلامك سخيف ولا معنى له"
            ],
            'label': [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1]
        }
        
        df = pd.DataFrame(training_data)
        
        # تنظيف النص للنموذج
        try:
            stop_words = set(stopwords.words('arabic'))
        except:
            stop_words = set()  # إذا لم تكن متوفرة، استخدم مجموعة فارغة
        
        def clean_text_for_ml(text):
            # إزالة العلامات والرموز
            text = re.sub(r'[^\w\s]', '', text)
            try:
                tokens = word_tokenize(text)
                tokens = [word for word in tokens if word not in stop_words and len(word) > 1]
            except:
                tokens = text.split()  # fallback إذا فشل tokenize
            return ' '.join(tokens)
        
        df['cleaned_text'] = df['text'].apply(clean_text_for_ml)
        
        # تدريب النموذج
        vectorizer = TfidfVectorizer(max_features=1000, ngram_range=(1, 2))
        X = vectorizer.fit_transform(df['cleaned_text'])
        y = df['label']
        
        ml_model = LogisticRegression(random_state=42)
        ml_model.fit(X, y)
        
        logging.info("✅ تم تدريب نموذج تعلم الآلة بنجاح")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في تدريب النموذج: {e}")
        return False

def is_protection_enabled(chat_id: int) -> bool:
    """
    التحقق من تفعيل الحماية في المجموعة
    """
    try:
        # التحقق من الذاكرة أولاً
        if chat_id in protection_enabled:
            return protection_enabled[chat_id]
            
        # التحقق من قاعدة البيانات
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        cursor.execute('SELECT protection_enabled FROM group_protection_settings WHERE chat_id = ?', (chat_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            enabled = bool(result[0])
            protection_enabled[chat_id] = enabled
            return enabled
        else:
            # إعداد افتراضي: تفعيل الحماية
            protection_enabled[chat_id] = True
            return True
            
    except Exception as e:
        logging.error(f"خطأ في فحص حالة الحماية: {e}")
        return True  # افتراضي مفعل

async def toggle_protection(chat_id: int, enabled: bool, user_id: int) -> bool:
    """
    تفعيل/تعطيل الحماية في المجموعة
    """
    try:
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT OR REPLACE INTO group_protection_settings 
        (chat_id, protection_enabled, updated_by, updated_date)
        VALUES (?, ?, ?, ?)
        ''', (chat_id, enabled, user_id, datetime.now()))
        
        conn.commit()
        conn.close()
        
        # تحديث الذاكرة
        protection_enabled[chat_id] = enabled
        
        status = "مفعل" if enabled else "معطل"
        logging.info(f"تم {status} نظام الحماية في المجموعة {chat_id} بواسطة {user_id}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في تغيير حالة الحماية: {e}")
        return False

def create_arabic_pattern(word: str) -> str:
    """
    إنشاء نمط تعبير منتظم للكلمة العربية مع اختلافات الكتابة المحسنة
    مستوحى من الملف الجديد مع تحسينات إضافية
    """
    replacements = {
        'ا': '[اٲإأٱآ]',
        'ب': '[ب٨]',
        'ت': '[ت٥]',
        'ث': '[ث٨]',
        'ج': '[جچ]',
        'ح': '[ح٨]',
        'خ': '[خ٨]',
        'د': '[د]',
        'ذ': '[ذ٨]',
        'ر': '[ر٤]',
        'ز': '[ز]',
        'س': '[س٥]',
        'ش': '[ش]',
        'ص': '[ص]',
        'ض': '[ض]',
        'ط': '[ط٥]',
        'ظ': '[ظ]',
        'ع': '[ع٥]',
        'غ': '[غ]',
        'ف': '[ف]',
        'ق': '[ق٥]',
        'ك': '[كک]',
        'ل': '[ل]',
        'م': '[م]',
        'ن': '[ن٥]',
        'ه': '[هة]',
        'و': '[و٦]',
        'ي': '[ي٨ئى]'
    }
    
    pattern = r'(?i)\b('
    for char in word:
        if char in replacements:
            pattern += replacements[char]
        else:
            pattern += re.escape(char)
    pattern += r')\b'
    
    return pattern

def clean_text_for_profanity_check(text: str) -> str:
    """
    تنظيف النص لإزالة التشفير والتمويه - محسن مع الأنماط الجديدة
    """
    if not text:
        return ""
    
    # تحويل لأحرف صغيرة
    cleaned = text.lower().strip()
    
    # إزالة المسافات الزائدة
    cleaned = ' '.join(cleaned.split())
    
    # إزالة الرموز الشائعة المستخدمة للتمويه
    symbols_to_remove = ['*', '_', '-', '+', '=', '|', '\\', '/', '.', ',', '!', '@', '#', '$', '%', '^', '&', '(', ')', '[', ']', '{', '}', '<', '>', '?', '~', '`', '"', "'"]
    for symbol in symbols_to_remove:
        cleaned = cleaned.replace(symbol, '')
    
    # إزالة المسافات التي قد تكون بين الحروف
    cleaned = cleaned.replace(' ', '')
    
    # تحويل الأرقام الشائعة إلى حروف - محسن مع اختلافات عربية
    number_replacements = {
        '0': 'و',  # شكل مشابه للواو
        '1': 'ل',  # شكل مشابه للام  
        '2': 'ن',  # شكل مشابه للنون
        '3': 'ع',  # شكل مشابه للعين
        '4': 'ر',  # شكل مشابه للراء
        '5': 'ه',  # شكل مشابه للهاء
        '6': 'و',  # شكل مشابه للواو
        '7': 'ح',  # شكل مشابه للحاء
        '8': 'ث',  # شكل مشابه للثاء
        '9': 'ق'   # شكل مشابه للقاف
    }
    
    for number, letter in number_replacements.items():
        cleaned = cleaned.replace(number, letter)
    
    # إزالة التكرارات الزائدة للحروف (مثل كككك -> كك)
    import re
    cleaned = re.sub(r'(.)\1{2,}', r'\1\1', cleaned)
    
    return cleaned

def generate_text_variations(text: str) -> list:
    """
    توليد تنويعات مختلفة للنص للفحص
    """
    variations = [text]
    
    # إضافة النص المنظف
    cleaned = clean_text_for_profanity_check(text)
    if cleaned and cleaned != text:
        variations.append(cleaned)
    
    # إزالة المسافات فقط
    no_spaces = text.replace(' ', '')
    if no_spaces != text:
        variations.append(no_spaces)
    
    # إزالة الرموز الأساسية فقط
    basic_clean = text
    for symbol in ['*', '_', '-', '.']:
        basic_clean = basic_clean.replace(symbol, '')
    if basic_clean != text:
        variations.append(basic_clean)
    
    return list(set(variations))  # إزالة التكرارات

async def check_message_ai_powered(text: str, user_id: int, chat_id: int, chat_context: str = "") -> dict:
    """
    فحص ذكي للرسالة باستخدام الذكاء الاصطناعي ونظام التعلم المتطور
    """
    try:
        # فحص قاعدة البيانات أولاً
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT word, severity FROM abusive_words')
        db_words = cursor.fetchall()
        conn.close()
        
        found_words = []
        text_lower = text.lower()
        
        # فحص الكلمات المعروفة
        for word, severity in db_words:
            if word.lower() in text_lower:
                # فحص أدق للتأكد من أن الكلمة منفصلة
                pattern = r'\b' + re.escape(word.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_words.append((word, severity))
        
        # إذا وُجدت كلمات معروفة
        if found_words:
            max_severity = max(severity for _, severity in found_words)
            return {
                'is_abusive': True,
                'method': 'database',
                'words': found_words,
                'severity': max_severity,
                'ml_score': None
            }
        
        # إذا لم توجد كلمات معروفة، استخدم النموذج
        if vectorizer and ml_model:
            try:
                cleaned_text = re.sub(r'[^\w\s]', '', text_lower)
                X = vectorizer.transform([cleaned_text])
                probability = ml_model.predict_proba(X)[0][1]
                
                threshold = 0.7  # يمكن تعديله من قاعدة البيانات
                if probability > threshold:
                    return {
                        'is_abusive': True,
                        'method': 'ml_model',
                        'words': [],
                        'severity': 2,  # متوسط للنموذج
                        'ml_score': probability
                    }
                else:
                    return {
                        'is_abusive': False,
                        'method': 'ml_model',
                        'words': [],
                        'severity': 0,
                        'ml_score': probability
                    }
            except Exception as ml_error:
                logging.warning(f"خطأ في نموذج ML: {ml_error}")
        
        return {
            'is_abusive': False,
            'method': 'clean',
            'words': [],
            'severity': 0,
            'ml_score': None
        }
        
    except Exception as e:
        logging.error(f"خطأ في الفحص المتقدم: {e}")
        return {
            'is_abusive': False,
            'method': 'error',
            'words': [],
            'severity': 0,
            'ml_score': None
        }

async def update_user_warnings(user_id: int, chat_id: int, severity: int) -> int:
    """
    تحديث تحذيرات المستخدم وإرجاع العدد الجديد
    """
    try:
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        # إضافة أو تحديث التحذيرات
        cursor.execute('''
        INSERT OR IGNORE INTO user_warnings (user_id, chat_id, warnings)
        VALUES (?, ?, 0)
        ''', (user_id, chat_id))
        
        # زيادة التحذيرات حسب درجة الخطورة
        warning_increment = severity  # كلما زادت الخطورة، زادت التحذيرات
        
        cursor.execute('''
        UPDATE user_warnings 
        SET warnings = warnings + ?, last_warning = CURRENT_TIMESTAMP
        WHERE user_id = ? AND chat_id = ?
        ''', (warning_increment, user_id, chat_id))
        
        cursor.execute('SELECT warnings FROM user_warnings WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        warnings_count = cursor.fetchone()[0]
        
        conn.commit()
        conn.close()
        
        return warnings_count
        
    except Exception as e:
        logging.error(f"خطأ في تحديث التحذيرات: {e}")
        return 0

async def calculate_punishment_duration(user_warnings: int, severity: int) -> tuple:
    """
    حساب مدة ونوع العقوبة حسب عدد التحذيرات ودرجة خطورة السب
    Returns: (duration_seconds, punishment_type, description)
    """
    # نظام العقوبات المتدرج:
    # التحذيرات 1-3: تحذيرات فقط
    # التحذيرات 4+: عقوبات فعلية متدرجة
    
    if user_warnings <= 3:
        return (0, "warning", "تحذير")
    
    # حساب مستوى العقوبة بناءً على التحذيرات والخطورة
    punishment_level = user_warnings - 3  # نبدأ من 1 بعد 3 تحذيرات
    
    # تضخيم العقوبة حسب الخطورة
    if severity >= 3:  # سباب شديد
        punishment_level += 2
    elif severity == 2:  # سباب متوسط
        punishment_level += 1
    
    # نظام العقوبات المتدرج
    if punishment_level == 1:
        return (60, "mute", "دقيقة واحدة")
    elif punishment_level == 2:
        return (120, "mute", "دقيقتان")
    elif punishment_level == 3:
        return (180, "mute", "3 دقائق")
    elif punishment_level == 4:
        return (240, "mute", "4 دقائق")
    elif punishment_level == 5:
        return (300, "mute", "5 دقائق")
    elif punishment_level == 6:
        return (600, "mute", "10 دقائق")
    elif punishment_level == 7:
        return (1800, "mute", "30 دقيقة")
    elif punishment_level == 8:
        return (3600, "mute", "ساعة واحدة")
    elif punishment_level == 9:
        return (7200, "mute", "ساعتان")
    elif punishment_level == 10:
        return (10800, "mute", "3 ساعات")
    elif punishment_level == 11:
        return (14400, "mute", "4 ساعات")
    elif punishment_level == 12:
        return (86400, "mute", "يوم كامل")
    elif punishment_level == 13:
        return (172800, "mute", "يومان")
    elif punishment_level == 14:
        return (259200, "mute", "3 أيام")
    elif punishment_level == 15:
        return (604800, "mute", "أسبوع")
    elif punishment_level == 16:
        return (2592000, "mute", "شهر كامل")
    elif punishment_level >= 17:
        return (0, "ban", "طرد نهائي")
    
    # احتياطي
    return (3600, "mute", "ساعة واحدة")

async def reset_user_warnings(user_id: int, chat_id: int) -> bool:
    """
    إعادة تعيين تحذيرات المستخدم (مثلاً عند إلغاء الكتم من قبل مشرف)
    Returns True إذا تم الحذف بنجاح
    """
    try:
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        # حذف جميع التحذيرات والعقوبات للمستخدم
        cursor.execute('''
            DELETE FROM user_warnings 
            WHERE user_id = ? AND chat_id = ?
        ''', (user_id, chat_id))
        
        conn.commit()
        conn.close()
        
        logging.info(f"تم إعادة تعيين تحذيرات المستخدم {user_id} في المجموعة {chat_id}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إعادة تعيين التحذيرات: {e}")
        return False

async def get_user_warnings(user_id: int, chat_id: int) -> int:
    """
    الحصول على عدد تحذيرات المستخدم الحالية
    """
    try:
        conn = sqlite3.connect('abusive_words.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT warnings FROM user_warnings WHERE user_id = ? AND chat_id = ?', (user_id, chat_id))
        result = cursor.fetchone()
        
        conn.close()
        
        return result[0] if result else 0
        
    except Exception as e:
        logging.error(f"خطأ في جلب تحذيرات المستخدم: {e}")
        return 0

async def is_user_actually_muted(bot, chat_id: int, user_id: int) -> bool:
    """
    التحقق من حالة المستخدم الفعلية في التيليجرام - هل هو مكتوم أم لا؟
    Returns True إذا كان المستخدم مكتوماً فعلاً في التيليجرام
    """
    try:
        user_member = await bot.get_chat_member(chat_id, user_id)
        
        # إذا كان المستخدم مطروداً أو غادر المجموعة، فهو ليس مكتوماً
        if user_member.status in ['left', 'kicked']:
            return False
            
        # إذا كان المستخدم مالك أو مشرف، فهو غير مكتوم
        if user_member.status in ['creator', 'administrator']:
            return False
            
        # إذا كان المستخدم عضو عادي، نتحقق من صلاحياته
        if user_member.status == 'restricted':
            # المستخدم مكتوم إذا لم يستطع إرسال الرسائل
            if hasattr(user_member, 'can_send_messages'):
                return not user_member.can_send_messages
            # إذا لم تكن الصلاحية متوفرة، فهو مكتوم
            return True
        
        # إذا كان العضو "member" عادي، فهو غير مكتوم
        return False
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من حالة المستخدم {user_id} في المجموعة {chat_id}: {e}")
        # في حالة الخطأ، نفترض أنه غير مكتوم لتجنب حذف الرسائل بدون مبرر
        return False

async def check_for_profanity(message: Message) -> dict:
    """
    فحص الرسالة للكشف عن السباب مع تحديد درجة الخطورة
    Returns dict مع is_profane, severity, detected_word
    """
    if not message.text:
        return {'is_profane': False, 'severity': 0, 'detected_word': None}
    
    # الحصول على تنويعات النص للفحص
    text_variations = generate_text_variations(message.text.lower().strip())
    
    # فحص السباب الخطير أولاً
    import re
    for text_variant in text_variations:
        # فحص السباب الخطير
        for banned_word in SEVERE_PROFANITY:
            # استخدام النمط المحسن للكلمات العربية
            arabic_pattern = create_arabic_pattern(banned_word.lower())
            if re.search(arabic_pattern, text_variant):
                logging.warning(f"⚠️ مخالفة خطيرة: '{banned_word}' في النص: '{message.text[:30]}...'")
                return {'is_profane': True, 'severity': 3, 'detected_word': banned_word}
            
            # النمط القديم كاحتياط
            simple_pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
            if re.search(simple_pattern, text_variant):
                logging.warning(f"⚠️ مخالفة خطيرة: '{banned_word}' في النص: '{message.text[:30]}...'")
                return {'is_profane': True, 'severity': 3, 'detected_word': banned_word}
        
        # فحص السباب البسيط (كلمات مثل "غبي")
        for mild_word in MILD_PROFANITY:
            arabic_pattern = create_arabic_pattern(mild_word.lower())
            if re.search(arabic_pattern, text_variant):
                logging.info(f"📝 كلمة غير لائقة: '{mild_word}' في النص: '{message.text[:30]}...'")
                return {'is_profane': True, 'severity': 1, 'detected_word': mild_word}
            
            simple_pattern = r'\b' + re.escape(mild_word.lower()) + r'\b'
            if re.search(simple_pattern, text_variant):
                logging.info(f"📝 كلمة غير لائقة: '{mild_word}' في النص: '{message.text[:30]}...'")
                return {'is_profane': True, 'severity': 1, 'detected_word': mild_word}
    
    # فحص إضافي للكلمات المشفرة (السباب الخطير فقط)
    original_text = message.text.lower()
    for banned_word in SEVERE_PROFANITY:
        # تحويل الكلمة المحظورة إلى نمط regex للبحث مع رموز التمويه
        word_pattern = r'\b'
        for char in banned_word.lower():
            word_pattern += re.escape(char) + r"[\*\_\-\.\s\+\=\|\\\/\,\!\@\#\$\%\^\&\(\)\[\]\{\}\<\>\?\~\`\"\'0-9]*"
        word_pattern += r'\b'
        
        # البحث عن النمط في النص الأصلي
        if re.search(word_pattern, original_text):
            logging.warning(f"⚠️ سباب مُشفر خطير: '{banned_word}' في النص: '{message.text[:30]}...'")
            return {'is_profane': True, 'severity': 3, 'detected_word': banned_word}
    
    # لا توجد مخالفات
    return {'is_profane': False, 'severity': 0, 'detected_word': None}

async def mute_user_with_duration(message: Message, duration_seconds: int, description: str) -> bool:
    """
    كتم المستخدم لمدة محددة
    """
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("البوت ليس مشرف - لا يمكن كتم المستخدمين")
            return False
        
        if not hasattr(bot_member, 'can_restrict_members') or not bot_member.can_restrict_members:
            logging.warning("البوت لا يملك صلاحية كتم المستخدمين")
            return False
        
        # فحص إذا كان المستخدم من الأسياد
        from config.hierarchy import is_master, is_supreme_master
        from modules.supreme_master_commands import get_masters_punishment_status
        
        if is_supreme_master(message.from_user.id):
            logging.info("المستخدم هو السيد الأعلى - محمي مطلقاً من جميع العقوبات")
            return False
        elif is_master(message.from_user.id):
            masters_punishment_enabled = get_masters_punishment_status()
            if not masters_punishment_enabled:
                logging.info("المستخدم من الأسياد - محمي من العقوبات التلقائية (العقوبات معطلة)")
                return False
        
        # التحقق من أن المستخدم ليس مالك المجموعة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_member.status == 'creator':
            logging.info(f"المستخدم {message.from_user.id} هو مالك المجموعة - لا يمكن كتمه")
            return False
        
        # إعداد صلاحيات الكتم
        mute_until = datetime.now() + timedelta(seconds=duration_seconds)
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
        
        logging.info(f"تم كتم المستخدم {message.from_user.id} لمدة {description} بسبب السباب")
        return True
        
    except TelegramBadRequest as e:
        logging.error(f"خطأ في كتم المستخدم: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع في كتم المستخدم: {e}")
        return False

async def ban_user_permanently(message: Message) -> bool:
    """
    طرد المستخدم نهائياً
    """
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("البوت ليس مشرف - لا يمكن طرد المستخدمين")
            return False
        
        if not hasattr(bot_member, 'can_restrict_members') or not bot_member.can_restrict_members:
            logging.warning("البوت لا يملك صلاحية طرد المستخدمين")
            return False
        
        # فحص إذا كان المستخدم من الأسياد
        from config.hierarchy import is_master, is_supreme_master
        from modules.supreme_master_commands import get_masters_punishment_status
        
        if is_supreme_master(message.from_user.id):
            logging.info("المستخدم هو السيد الأعلى - محمي مطلقاً من جميع العقوبات")
            return False
        elif is_master(message.from_user.id):
            masters_punishment_enabled = get_masters_punishment_status()
            if not masters_punishment_enabled:
                logging.info("المستخدم من الأسياد - محمي من العقوبات التلقائية (العقوبات معطلة)")
                return False
        
        # التحقق من أن المستخدم ليس مالك المجموعة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_member.status == 'creator':
            logging.info(f"المستخدم {message.from_user.id} هو مالك المجموعة - لا يمكن طرده")
            return False
        
        # طرد المستخدم
        await message.bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id
        )
        
        logging.info(f"تم طرد المستخدم {message.from_user.id} نهائياً بسبب تكرار السباب")
        return True
        
    except TelegramBadRequest as e:
        logging.error(f"خطأ في طرد المستخدم: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع في طرد المستخدم: {e}")
        return False

async def mute_user_for_profanity(message: Message) -> bool:
    """
    كتم المستخدم بسبب السباب
    Returns True إذا تم الكتم بنجاح
    """
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("البوت ليس مشرف - لا يمكن كتم المستخدمين")
            return False
        
        if not hasattr(bot_member, 'can_restrict_members') or not bot_member.can_restrict_members:
            logging.warning("البوت لا يملك صلاحية كتم المستخدمين")
            return False
        
        # فحص إذا كان المستخدم من الأسياد (السيد الأعلى محمي مطلقاً، والأسياد الآخرين حسب الحالة)
        from config.hierarchy import is_master, is_supreme_master
        from modules.supreme_master_commands import get_masters_punishment_status
        
        if is_supreme_master(message.from_user.id):
            logging.info("المستخدم هو السيد الأعلى - محمي مطلقاً من جميع العقوبات")
            return False
        elif is_master(message.from_user.id):
            # فحص حالة العقوبات على الأسياد
            masters_punishment_enabled = get_masters_punishment_status()
            if not masters_punishment_enabled:
                logging.info("المستخدم من الأسياد - محمي من العقوبات التلقائية (العقوبات معطلة)")
                return False
            else:
                logging.warning(f"🔥 نظام العقوبات مفعل - سيتم معاقبة السيد {message.from_user.id}")
                # نكمل العملية لتطبيق العقوبات
        
        # التحقق من أن المستخدم ليس مالك المجموعة (المالك لا يُكتم أبداً)
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_member.status == 'creator':
            logging.info("المستخدم مالك المجموعة - لن يتم كتمه")
            return False
        
        # المشرفين أيضاً يخضعون للقانون - لا استثناءات
        if user_member.status == 'administrator':
            logging.info("المستخدم مشرف ولكن سيتم كتمه بسبب السباب")
        
        # كتم المستخدم لمدة ساعة
        mute_until = datetime.now() + timedelta(hours=1)
        
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
        
        logging.info(f"تم كتم المستخدم {message.from_user.id} لمدة ساعة بسبب السباب")
        return True
        
    except TelegramBadRequest as e:
        logging.error(f"خطأ في كتم المستخدم: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع في كتم المستخدم: {e}")
        return False

async def handle_profanity_detection(message: Message) -> bool:
    """
    معالج كشف السباب الرئيسي
    Returns True إذا تم العثور على سباب وتمت معالجته
    """
    try:
        # التأكد من أن الرسالة في مجموعة وليس خاص
        if message.chat.type == 'private':
            return False
        
        # استثناء أوامر المسح من فحص السباب
        if message.text:
            text = message.text.strip()
            if text.startswith('مسح ') or text == 'مسح بالرد' or text == 'مسح':
                return False
        
        # التحقق من حالة المستخدم الفعلية في التيليجرام
        user_is_muted = await is_user_actually_muted(message.bot, message.chat.id, message.from_user.id)
        
        # فحص وجود سباب مع تحديد درجة الخطورة
        profanity_result = await check_for_profanity(message)
        
        if not profanity_result['is_profane']:
            # لا يوجد سباب - نتحقق من حالة المستخدم
            if not user_is_muted:
                # المستخدم غير مكتوم ولا يوجد سباب - رسالة عادية
                logging.debug(f"✅ رسالة عادية من مستخدم غير مكتوم {message.from_user.id}")
                return False
            else:
                # المستخدم مكتوم - يجب حذف جميع رسائله حتى لو لم تكن سباب
                logging.info(f"🔇 المستخدم {message.from_user.id} مكتوم ويحاول إرسال رسالة")
                try:
                    await message.delete()
                    logging.info("🗑️ تم حذف رسالة من مستخدم مكتوم")
                    # إرسال تذكير للمستخدم المكتوم
                    reminder_msg = await message.answer(
                        f"🔇 **{message.from_user.first_name}** أنت مكتوم حالياً\n"
                        f"⚠️ لا يمكنك إرسال الرسائل حتى ينتهي الكتم أو يتم إلغاؤه من قبل المشرفين"
                    )
                    # حذف الرسالة التذكيرية بعد 8 ثواني
                    import asyncio
                    await asyncio.sleep(8)
                    try:
                        await reminder_msg.delete()
                    except:
                        pass
                except Exception as delete_error:
                    logging.warning(f"لم يتمكن من حذف رسالة المستخدم المكتوم: {delete_error}")
                return True
        
        # الحصول على درجة الخطورة والكلمة المكتشفة
        severity = profanity_result['severity']
        detected_word = profanity_result['detected_word']
        
        # التعامل المتدرج حسب درجة الخطورة
        if severity == 1:
            # كلمات متوسطة - نظام التحذيرات الثلاث
            current_warnings = await get_user_warnings(message.from_user.id, message.chat.id)
            new_warnings_count = await update_user_warnings(message.from_user.id, message.chat.id, 1)  # تحذير واحد للكلمات المتوسطة
            
            # حذف الرسالة
            try:
                await message.delete()
                logging.info(f"📝 تم حذف كلمة غير لائقة متوسطة: {detected_word}")
            except Exception as delete_error:
                logging.warning(f"لم يتمكن من حذف الرسالة: {delete_error}")
            
            # تطبيق نظام التحذيرات
            if new_warnings_count <= 3:
                # تحذير فقط
                if new_warnings_count == 1:
                    warning_msg = await message.answer(
                        f"⚠️ **تحذير أول لـ {message.from_user.first_name}**\n\n"
                        f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n"
                        f"💡 **الكلمة:** {detected_word}\n"
                        f"🤝 **تجنب الكلمات غير اللائقة**"
                    )
                elif new_warnings_count == 2:
                    warning_msg = await message.answer(
                        f"🔥 **تحذير ثاني لـ {message.from_user.first_name}**\n\n"
                        f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n"
                        f"💡 **الكلمة:** {detected_word}\n"
                        f"⚠️ **تحذير أخير قبل العقوبة!**"
                    )
                elif new_warnings_count == 3:
                    warning_msg = await message.answer(
                        f"💥 **تحذير أخير لـ {message.from_user.first_name}**\n\n"
                        f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n"
                        f"💡 **الكلمة:** {detected_word}\n"
                        f"🚨 **المخالفة القادمة = عقوبة فورية!**"
                    )
                
                # حذف رسالة التحذير بعد 10 ثوان
                import asyncio
                await asyncio.sleep(10)
                try:
                    await warning_msg.delete()
                except:
                    pass
            else:
                # عقوبة فعلية
                duration_seconds, punishment_type, description = await calculate_punishment_duration(new_warnings_count, severity)
                
                if punishment_type == "mute" and duration_seconds > 0:
                    punishment_success = await mute_user_with_duration(message, duration_seconds, description)
                    if punishment_success:
                        punishment_msg = await message.answer(
                            f"⛔️ **تم كتم {message.from_user.first_name}!**\n\n"
                            f"📊 **التحذيرات: {new_warnings_count}**\n"
                            f"🔇 **مدة الكتم: {description}**\n"
                            f"💡 **السبب:** {detected_word}\n\n"
                            f"🛡️ **نظام التحذيرات الثلاث مُطبق!**"
                        )
            return True
        
        # للسباب الخطير (severity >= 2) - نظام التحذيرات والعقوبات العادي
        current_warnings = await get_user_warnings(message.from_user.id, message.chat.id)
        
        # زيادة التحذيرات حسب درجة الخطورة (تحذيرواحد للسباب الخطير)
        new_warnings_count = await update_user_warnings(message.from_user.id, message.chat.id, severity)
        
        # حذف الرسالة المسيئة فوراً
        try:
            await message.delete()
            logging.warning(f"🗑️ تم حذف سباب خطير: {detected_word}")
        except Exception as delete_error:
            logging.warning(f"لم يتمكن من حذف الرسالة المسيئة: {delete_error}")
        
        # تحديد نوع الرد
        if new_warnings_count <= 3:
            # تحذيرات فقط
            warning_level = new_warnings_count
            punishment_success = False
        else:
            # عقوبة فعلية
            warning_level = 4
            duration_seconds, punishment_type, description = await calculate_punishment_duration(new_warnings_count, severity)
            
            punishment_success = False
            if punishment_type == "mute" and duration_seconds > 0:
                punishment_success = await mute_user_with_duration(message, duration_seconds, description)
            elif punishment_type == "ban":
                punishment_success = await ban_user_permanently(message)
        
        # فحص نوع المستخدم للرسالة المناسبة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        
        # استيراد دوال الهياكل
        from config.hierarchy import is_master, is_supreme_master
        from modules.supreme_master_commands import get_masters_punishment_status
        
        # إرسال رسالة السيدة رهف حسب عدد التحذيرات ونجاح الكتم
        if warning_level <= 3:
            # رسائل التحذير (1-2)
            if warning_level == 1:
                warning_message = await message.answer(
                    f"⚠️ **تحذير أول لـ {message.from_user.first_name}**\n\n"
                    f"🚫 **تم حذف رسالتك المسيئة**\n"
                    f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n\n"
                    f"💡 **هذا تحذير مجاني - احترم آداب المحادثة**\n"
                    f"⚡️ **بعد 3 تحذيرات ستتم معاقبتك!**\n\n"
                    f"🛡️ **قوانين السيدة رهف واضحة ومحترمة**"
                )
            elif warning_level == 2:
                warning_message = await message.answer(
                    f"🔥 **تحذير ثاني لـ {message.from_user.first_name}**\n\n"
                    f"🚫 **تم حذف رسالتك المسيئة مرة أخرى**\n"
                    f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n\n"
                    f"⚠️ **هذا تحذيرك الأخير!**\n"
                    f"💣 **مخالفة واحدة أخرى وستُعاقب!**\n\n"
                    f"🗡️ **لا تختبر صبر السيدة رهف!**"
                )
            elif warning_level == 3:
                warning_message = await message.answer(
                    f"💥 **تحذير أخير لـ {message.from_user.first_name}**\n\n"
                    f"🚫 **تم حذف رسالتك المسيئة للمرة الثالثة!**\n"
                    f"📝 **عدد التحذيرات: {new_warnings_count}/3**\n\n"
                    f"🚨 **انتهى عهد التحذيرات المجانية!**\n"
                    f"💣 **المخالفة القادمة = عقوبة فورية!**\n\n"
                    f"🔥 **أصبحت على حافة الهاوية!**"
                )
        elif warning_level == 4 and punishment_success:
            # تم تطبيق عقوبة فعلية (كتم أو طرد)
            if punishment_type == "ban":
                if is_master(message.from_user.id):
                    warning_message = await message.answer(
                        f"💀 **تم طرد السيد {message.from_user.first_name} نهائياً!**\n\n"
                        f"👑 **نظام العقوبات الجديد لا يرحم - حتى الأسياد!**\n"
                        f"📊 **التحذيرات: {new_warnings_count} - تجاوز جميع الحدود**\n"
                        f"🚫 **العقوبة: طرد نهائي من المجموعة**\n\n"
                        f"⚡️ **رسالة للجميع:** لا أحد فوق القانون!\n"
                        f"🛡️ **السيدة رهف لا تتسامح مع المتمردين**"
                    )
                else:
                    warning_message = await message.answer(
                        f"💀 **تم طرد {message.from_user.first_name} نهائياً!**\n\n"
                        f"👑 **السيد يوكي نفد صبره تماماً**\n"
                        f"📊 **التحذيرات: {new_warnings_count} - تجاوز جميع الحدود**\n"
                        f"🚫 **العقوبة: طرد نهائي من المجموعة**\n\n"
                        f"⚡️ **تحذير للجميع:** هذا مصير كل من يتمرد!\n"
                        f"🛡️ **قوانين السيدة رهف مطلقة ونهائية**"
                    )
            else:  # punishment_type == "mute"
                if is_master(message.from_user.id):
                    warning_message = await message.answer(
                        f"🔥 **تم إسكات السيد {message.from_user.first_name}!**\n\n"
                        f"👑 **نظام العقوبات المتدرج مفعل - لا استثناءات!**\n"
                        f"📊 **التحذيرات: {new_warnings_count}**\n"
                        f"🔇 **مدة الكتم: {description}**\n\n"
                        f"⚡️ **رسالة للجميع:** العقوبات تطال الجميع عند التفعيل!\n"
                        f"🛡️ **قوانين السيدة رهف أقوى من أي رتبة!**"
                    )
                else:
                    warning_message = await message.answer(
                        f"⛔️ **تم إسكات {message.from_user.first_name}!**\n\n"
                        f"👑 **السيد يوكي يطبق نظام العقوبات المتدرج**\n"
                        f"📊 **التحذيرات: {new_warnings_count}**\n"
                        f"🔇 **مدة الكتم: {description}**\n\n"
                        f"⚡️ **تحذير للجميع:** العقوبات تزيد مع التكرار!\n"
                        f"🛡️ **قوانين السيدة رهف مطلقة وغير قابلة للنقاش**"
                    )
        elif warning_level == 4 and not punishment_success and is_master(message.from_user.id):
            # رسالة خاصة للأسياد المحميين من العقوبات بعد 3 تحذيرات
            masters_punishment_enabled = get_masters_punishment_status()
            if not masters_punishment_enabled:
                warning_message = await message.answer(
                    f"👑 **إنذار نهائي للسيد {message.from_user.first_name}**\n\n"
                    f"🛡️ **أنت محمي من العقوبات لكن...**\n"
                    f"📊 **حصلت على {new_warnings_count} تحذيرات!**\n"
                    f"📚 **يُفضل الحفاظ على الأدب كقدوة للأعضاء**\n\n"
                    f"🌟 **كن المثال الجيد الذي يحتذى به**\n"
                    f"⚠️ **تذكر: يمكن تفعيل العقوبات عليك في أي وقت!**"
                )
            else:
                warning_message = await message.answer(
                    f"🔥 **إنذار نهائي للسيد {message.from_user.first_name}!**\n\n"
                    f"👑 **نظام العقوبات مفعل عليك الآن!**\n"
                    f"📊 **التحذيرات: {new_warnings_count} - تجاوزت الحد المسموح**\n"
                    f"⚠️ **حتى الأسياد يخضعون للقوانين عند التفعيل**\n\n"
                    f"💣 **سلوك آخر وستتم معاقبتك كعضو عادي!**\n"
                    f"🗡️ **لا أحد فوق قوانين السيدة رهف!**"
                )
        elif warning_level == 4 and not punishment_success and user_member.status == 'administrator':
            # المستخدم مشرف - رسالة تحذير قوية خاصة بعد 3 تحذيرات
            warning_message = await message.answer(
                f"🔥 **إنذار نهائي للمشرف {message.from_user.first_name}!**\n\n"
                f"👑 **السيدة رهف غاضبة جداً من سلوكك!**\n"
                f"📊 **التحذيرات: {new_warnings_count} - تجاوزت الحد المسموح**\n"
                f"⚠️ **حتى المشرفين يخضعون لقوانين الأدب**\n\n"
                f"💣 **التحذير الأخير:** سلوك آخر وسيتم تنزيل رتبتك!\n"
                f"🗡️ **لا أحد فوق القانون في مملكة السيدة رهف!**"
            )
        elif warning_level == 4 and not punishment_success and user_member.status == 'creator':
            # مالك المجموعة - رسالة دبلوماسية لكن قوية بعد 3 تحذيرات
            warning_message = await message.answer(
                f"🙏 **ملاحظة محترمة لمالك المجموعة {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تقدر دورك ولكن...**\n"
                f"📊 **حصلت على {new_warnings_count} تحذيرات**\n"
                f"📚 **الأدب مطلوب من الجميع بما فيهم أصحاب المجموعات**\n\n"
                f"🌟 **نرجو أن تكون قدوة للأعضاء في الكلام المهذب**"
            )
        elif warning_level == 4 and not punishment_success:
            # عضو عادي - يجب إرسال رسالة حتى لو فشل الكتم بعد 3 تحذيرات
            warning_message = await message.answer(
                f"🔥 **تم حذف رسالة مسيئة من {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تحكم هنا بيد من حديد!**\n"
                f"📊 **التحذيرات: {new_warnings_count} - تجاوزت الحد المسموح**\n"
                f"🔇 **لم يتمكن من كتمك لكن الرسالة محذوفة**\n\n"
                f"⚠️ **التحذير الأخير:** من يكرر السب سيتم طرده!\n"
                f"💀 **لا مجال للتساهل مع قلة الأدب**\n\n"
                f"📝 **ملاحظة:** تأكد من أن البوت لديه صلاحيات كافية لفرض العقوبات"
            )
        
        # حذف رسالة التحذير بعد 20 ثانية
        try:
            import asyncio
            await asyncio.sleep(20)
            await warning_message.delete()
        except:
            pass  # لا نفشل إذا لم نتمكن من حذف رسالة التحذير
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج كشف السباب: {e}")
        return False

# دالة للتوافق مع الكود القديم
async def check_message_advanced(text: str, user_id: int, chat_id: int) -> dict:
    """دالة للتوافق مع الكود القديم - تحويل إلى النظام الجديد"""
    try:
        chat_context = f"مجموعة {chat_id}"
        return await check_message_ai_powered(text, user_id, chat_id, chat_context)
    except Exception as e:
        logging.error(f"خطأ في دالة التوافق: {e}")
        # استخدام الكشف الأساسي في حالة فشل النظام المتقدم
        from .ai_profanity_detector import check_message_advanced_fallback
        return await check_message_advanced_fallback(text, user_id, chat_id)
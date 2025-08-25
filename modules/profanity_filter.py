"""
نظام كشف السباب المتطور والكتم التلقائي
يستخدم قاعدة بيانات ونموذج ذكاء اصطناعي للكشف عن الألفاظ المسيئة
يقوم بكتم المستخدمين الذين يسبون ويرسل رسالة من السيدة رهف
"""

import logging
import sqlite3
import pandas as pd
import numpy as np
from aiogram.types import Message, ChatPermissions
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

# قائمة الكلمات المحظورة (السباب الشديد فقط)
BANNED_WORDS = [
    # سباب جنسي بذيء وكلمات فاحشة فقط
    "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
    "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
    "ابن الشرموطة", "بنت الشرموطة",
    "خرا", "خراء", "يلعن", "اللعنة",
    
    # كلمات إضافية مطلوبة
    "منيوك", "ايري", "انيك", "نيكك", "منيوكة", "ايرك", "ايرها",
    "انيكك", "انيكها", "منيوكو", "ايرو", "نيكو", "كسمك", "كسك",
    "كسها", "كسهم", "كسكم", "كسكن", "زبك", "زبها", "زبهم", "زبكم",
    
    # سباب يمني بذيء فقط
    "قاوود", "قواد", "زومل", "زومله",
    "ملعون", "ملعونه",
    
    # تركيبات يمنية بذيئة
    "يا قاوود", "يا قواد", "اخنث", "يا مخنوث",
    "ابن القاوود", "بنت القواد", "ابن الكلب", "بنت الكلب" ,
    
    # كلمات بذيئة إضافية
    "انيكك", "يلعن ابوك", "يلعن ابوكي", "كول خرا", "اكل خرا",
    
    # كلمات جنسية صريحة
    "جنس", "جماع", "مجامعه", "نكاح", "مناكه", "سكس", "ممارسه",
    "معاشره", "لواط", "لوطي", "لوطيه", "شاذ انت", "شاذه انتي", "مثلي انت", "انتي مثليه"
]

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
            "قاوود", "قواد", "زومل", "زومله", "ملعون", "ملعونه"
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

def clean_text_for_profanity_check(text: str) -> str:
    """
    تنظيف النص لإزالة التشفير والتمويه
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
    
    # تحويل الأرقام الشائعة إلى حروف
    number_replacements = {
        '0': 'o',
        '1': 'i',
        '2': 'z',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '6': 'g',
        '7': 't',
        '8': 'b',
        '9': 'g'
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

async def check_message_advanced(text: str, user_id: int, chat_id: int) -> dict:
    """
    فحص متقدم للرسالة باستخدام قاعدة البيانات ونموذج تعلم الآلة
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

async def check_for_profanity(message: Message) -> bool:
    """
    فحص الرسالة للكشف عن السباب مع كشف التشفير والتمويه
    Returns True إذا وُجد سباب
    """
    if not message.text:
        return False
    
    # الحصول على تنويعات النص للفحص
    text_variations = generate_text_variations(message.text.lower().strip())
    
    # فحص كل تنويعة مع كل كلمة محظورة
    import re
    for text_variant in text_variations:
        for banned_word in ALL_BANNED_WORDS:
            # استخدام regex للتأكد من أن الكلمة المحظورة منفصلة وليست جزء من كلمة أخرى
            pattern = r'\b' + re.escape(banned_word.lower()) + r'\b'
            if re.search(pattern, text_variant):
                logging.info(f"تم كشف سباب: '{banned_word}' في النص المنظف: '{text_variant}' (النص الأصلي: '{message.text[:50]}...')")
                return True
    
    # فحص إضافي للكلمات المقسمة بمسافات أو رموز
    original_text = message.text.lower()
    for banned_word in ALL_BANNED_WORDS:
        # تحويل الكلمة المحظورة إلى نمط regex للبحث مع رموز التمويه
        import re
        word_pattern = r'\b'
        for char in banned_word.lower():
            word_pattern += re.escape(char) + r"[\*\_\-\.\s\+\=\|\\\/\,\!\@\#\$\%\^\&\(\)\[\]\{\}\<\>\?\~\`\"\'0-9]*"
        word_pattern += r'\b'
        
        # البحث عن النمط في النص الأصلي
        if re.search(word_pattern, original_text):
            logging.info(f"تم كشف سباب مُشفر: '{banned_word}' في النص: '{message.text[:50]}...'")
            return True
    
    # استخدام الفحص المتقدم إذا فشل الفحص التقليدي
    if not is_protection_enabled(message.chat.id):
        return False
    
    result = await check_message_advanced(message.text, message.from_user.id, message.chat.id)
    return result['is_abusive']

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
        
        # فحص وجود سباب
        if not await check_for_profanity(message):
            return False
        
        # محاولة كتم المستخدم أولاً
        mute_success = await mute_user_for_profanity(message)
        
        # حذف الرسالة المسيئة بعد الكتم
        try:
            await message.delete()
            logging.info("تم حذف الرسالة المسيئة")
        except Exception as delete_error:
            logging.warning(f"لم يتمكن من حذف الرسالة المسيئة: {delete_error}")
        
        # فحص نوع المستخدم للرسالة المناسبة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        
        # إرسال رسالة السيدة رهف حسب نجاح الكتم
        if mute_success:
            # تم الكتم بنجاح (عضو عادي)
            warning_message = await message.answer(
                f"⛔️ **تم إسكات {message.from_user.first_name} فوراً!**\n\n"
                f"👑 **السيد يوكي لا تتساهل مع السب والكلام القذر**\n"
                f"🔇 **مدة الكتم:** ساعة كاملة - تعلم الأدب!\n\n"
                f"⚡️ **تحذير للجميع:** من يسب يُكتم بلا استثناءات!\n"
                f"🛡️ **قوانين السيدة رهف مطلقة وغير قابلة للنقاش**"
            )
        elif user_member.status == 'administrator':
            # المستخدم مشرف - رسالة تحذير قوية خاصة
            warning_message = await message.answer(
                f"🔥 **إنذار نهائي للمشرف {message.from_user.first_name}!**\n\n"
                f"👑 **السيدة رهف غاضبة جداً من سلوكك!**\n"
                f"⚠️ **حتى المشرفين يخضعون لقوانين الأدب**\n\n"
                f"💣 **التحذير الأخير:** سلوك آخر وسيتم تنزيل رتبتك!\n"
                f"🗡️ **لا أحد فوق القانون في مملكة السيدة رهف!**"
            )
        elif user_member.status == 'creator':
            # مالك المجموعة - رسالة دبلوماسية لكن قوية
            warning_message = await message.answer(
                f"🙏 **ملاحظة محترمة لمالك المجموعة {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تقدر دورك ولكن...**\n"
                f"📚 **الأدب مطلوب من الجميع بما فيهم أصحاب المجموعات**\n\n"
                f"🌟 **نرجو أن تكون قدوة للأعضاء في الكلام المهذب**"
            )
        else:
            # عضو عادي لكن فشل الكتم لسبب آخر
            warning_message = await message.answer(
                f"🔥 **تم حذف رسالة مسيئة من {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تحكم هنا بيد من حديد!**\n"
                f"⚠️ **التحذير الأخير:** من يكرر السب سيتم طرده!\n\n"
                f"💀 **لا مجال للتساهل مع قلة الأدب**"
            )
        
        # حذف رسالة التحذير بعد 30 ثانية
        try:
            import asyncio
            await asyncio.sleep(30)
            await warning_message.delete()
        except:
            pass  # لا نفشل إذا لم نتمكن من حذف رسالة التحذير
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج كشف السباب: {e}")
        return False
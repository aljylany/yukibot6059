"""
نظام كشف الألفاظ المسيئة المتطور
Advanced Abusive Language Detection System for Yuki Bot
"""

import logging
import re
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords

from database.operations import execute_query, get_user
from config.hierarchy import MASTERS
from utils.decorators import user_required
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

# تحميل بيانات NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

class AbusiveDetector:
    """كلاس رئيسي لكشف الألفاظ المسيئة"""
    
    def __init__(self):
        self.vectorizer = None
        self.model = None
        self.is_initialized = False
        
    async def initialize(self):
        """تهيئة النظام وإعداد قاعدة البيانات والنموذج"""
        try:
            await self._setup_database()
            await self._add_default_words()
            await self._init_ml_model()
            self.is_initialized = True
            logging.info("✅ تم تهيئة نظام كشف الألفاظ المسيئة بنجاح")
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نظام كشف الألفاظ المسيئة: {e}")
    
    async def _setup_database(self):
        """إعداد جداول قاعدة البيانات"""
        
        # جدول الكلمات المسيئة
        await execute_query("""
            CREATE TABLE IF NOT EXISTS abusive_words (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT UNIQUE,
                severity INTEGER DEFAULT 1,
                added_by INTEGER,
                added_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # جدول تحذيرات المستخدمين
        await execute_query("""
            CREATE TABLE IF NOT EXISTS user_warnings (
                user_id INTEGER,
                chat_id INTEGER,
                warnings INTEGER DEFAULT 0,
                last_warning TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_violations INTEGER DEFAULT 0,
                PRIMARY KEY (user_id, chat_id)
            )
        """)
        
        # جدول سجل الرسائل المحذوفة
        await execute_query("""
            CREATE TABLE IF NOT EXISTS deleted_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                message_text TEXT,
                detection_method TEXT,
                severity INTEGER,
                deleted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def _add_default_words(self):
        """إضافة الكلمات المسيئة الافتراضية"""
        default_words = [
            ('كلب', 2), ('حيوان', 2), ('عاهة', 3), ('قذر', 1),
            ('خنزير', 3), ('سافل', 2), ('حقير', 2), ('وضيع', 1),
            ('ساقط', 2), ('منحط', 2), ('عاهر', 3), ('زاني', 3),
            ('لعين', 2), ('نذل', 2), ('أحمق', 1), ('غبي', 1),
            ('ابن كلب', 3), ('ولد حرام', 3), ('يا كلب', 2),
            ('حمار', 1), ('بهيمة', 2), ('جاهل', 1)
        ]
        
        for word, severity in default_words:
            await execute_query(
                "INSERT OR IGNORE INTO abusive_words (word, severity, added_by) VALUES (?, ?, ?)",
                (word, severity, 0)
            )
    
    async def _init_ml_model(self):
        """تهيئة نموذج تعلم الآلة"""
        try:
            # بيانات التدريب العربية
            training_data = {
                'text': [
                    "أنت شخص لطيف ومهذب",
                    "أحب التحدث معك دائماً",
                    "شكراً لك على المساعدة",
                    "هذا عمل رائع ومتقن",
                    "بارك الله فيك",
                    "جزاك الله خيراً",
                    "أنت غبي جداً ولا تفهم شيء",
                    "اخرس يا أحمق ولا تتكلم",
                    "أنت عديم الفائدة تماماً",
                    "أنت فاشل في كل شيء",
                    "لا أحد يحبك أبداً",
                    "أنت أسوأ شخص قابلته",
                    "اذهب وامت",
                    "أتمنى لك الموت",
                    "يا كلب انت ومن خلفك",
                    "ابن حرام وولد زنا"
                ],
                'label': [0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
            }
            
            df = pd.DataFrame(training_data)
            
            # تنظيف النص العربي
            def clean_arabic_text(text):
                # إزالة علامات الترقيم والأرقام
                text = re.sub(r'[^\u0600-\u06FF\s]', '', text)
                # تطبيع الحروف العربية
                text = re.sub(r'[إأآا]', 'ا', text)
                text = re.sub(r'[ىي]', 'ي', text)
                text = re.sub(r'ة', 'ه', text)
                # إزالة المسافات الزائدة
                text = re.sub(r'\s+', ' ', text.strip())
                return text
            
            df['cleaned_text'] = df['text'].apply(clean_arabic_text)
            
            # تحويل النص إلى متجهات
            self.vectorizer = TfidfVectorizer(
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1
            )
            X = self.vectorizer.fit_transform(df['cleaned_text'])
            y = df['label']
            
            # تدريب النموذج
            self.model = LogisticRegression(random_state=42)
            self.model.fit(X, y)
            
            logging.info("✅ تم تدريب نموذج تعلم الآلة بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نموذج تعلم الآلة: {e}")
    
    async def check_message(self, text: str, user_id: int, chat_id: int) -> Dict:
        """فحص الرسالة للكشف عن الألفاظ المسيئة"""
        if not self.is_initialized:
            await self.initialize()
        
        result = {
            'is_abusive': False,
            'words': [],
            'ml_score': 0.0,
            'reason': 'clean',
            'severity': 0
        }
        
        try:
            # 1. فحص قاعدة البيانات أولاً
            db_result = await self._check_database_words(text.lower())
            if db_result['found']:
                result.update({
                    'is_abusive': True,
                    'words': db_result['words'],
                    'reason': 'known_words',
                    'severity': max([w[1] for w in db_result['words']])
                })
                return result
            
            # 2. فحص نموذج تعلم الآلة
            if self.model and self.vectorizer:
                ml_result = await self._check_ml_model(text)
                if ml_result['is_abusive']:
                    result.update(ml_result)
                    result['reason'] = 'ml_model'
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في فحص الرسالة: {e}")
            return result
    
    async def _check_database_words(self, text: str) -> Dict:
        """فحص الكلمات المحفوظة في قاعدة البيانات"""
        try:
            words_data = await execute_query(
                "SELECT word, severity FROM abusive_words",
                fetch_all=True
            )
            
            found_words = []
            for row in words_data:
                word, severity = row['word'], row['severity']
                if word in text:
                    found_words.append((word, severity))
            
            return {
                'found': len(found_words) > 0,
                'words': found_words
            }
            
        except Exception as e:
            logging.error(f"خطأ في فحص قاعدة البيانات: {e}")
            return {'found': False, 'words': []}
    
    async def _check_ml_model(self, text: str) -> Dict:
        """فحص النص باستخدام نموذج تعلم الآلة"""
        try:
            # تنظيف النص
            cleaned_text = re.sub(r'[^\u0600-\u06FF\s]', '', text.lower())
            cleaned_text = re.sub(r'[إأآا]', 'ا', cleaned_text)
            cleaned_text = re.sub(r'[ىي]', 'ي', cleaned_text)
            cleaned_text = re.sub(r'ة', 'ه', cleaned_text)
            cleaned_text = re.sub(r'\s+', ' ', cleaned_text.strip())
            
            if not cleaned_text:
                return {'is_abusive': False, 'ml_score': 0.0}
            
            # تحويل إلى متجه والتنبؤ
            X = self.vectorizer.transform([cleaned_text])
            proba = self.model.predict_proba(X)[0][1]
            
            # حد الثقة لاعتبار النص مسيء
            confidence_threshold = 0.7
            
            return {
                'is_abusive': proba > confidence_threshold,
                'ml_score': float(proba),
                'severity': 2 if proba > 0.9 else 1
            }
            
        except Exception as e:
            logging.error(f"خطأ في نموذج تعلم الآلة: {e}")
            return {'is_abusive': False, 'ml_score': 0.0}
    
    async def handle_abusive_message(self, message: Message, result: Dict) -> str:
        """معالجة الرسالة المسيئة"""
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        try:
            # تحديث تحذيرات المستخدم
            warnings_count = await self._update_user_warnings(user_id, chat_id)
            
            # تسجيل الرسالة المحذوفة
            await self._log_deleted_message(
                user_id, chat_id, message.text, result
            )
            
            # بناء رسالة التحذير
            warning_msg = await self._build_warning_message(result, warnings_count)
            
            # حذف الرسالة الأصلية
            try:
                await message.delete()
            except Exception as e:
                logging.error(f"خطأ في حذف الرسالة: {e}")
            
            # معالجة العقوبات
            if warnings_count >= 3:
                await self._apply_punishment(message, warnings_count)
                warning_msg += "\n\n🚫 **تم تطبيق عقوبة لتجاوز الحد المسموح**"
            
            return warning_msg
            
        except Exception as e:
            logging.error(f"خطأ في معالجة الرسالة المسيئة: {e}")
            return "⚠️ تم اكتشاف محتوى مسيء وتم حذف الرسالة"
    
    async def _update_user_warnings(self, user_id: int, chat_id: int) -> int:
        """تحديث عدد تحذيرات المستخدم"""
        try:
            # إدراج أو تحديث التحذيرات
            await execute_query("""
                INSERT OR IGNORE INTO user_warnings (user_id, chat_id, warnings, total_violations)
                VALUES (?, ?, 0, 0)
            """, (user_id, chat_id))
            
            await execute_query("""
                UPDATE user_warnings 
                SET warnings = warnings + 1, 
                    total_violations = total_violations + 1,
                    last_warning = CURRENT_TIMESTAMP
                WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            
            # جلب عدد التحذيرات الحالي
            result = await execute_query(
                "SELECT warnings FROM user_warnings WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
                fetch_one=True
            )
            
            return result['warnings'] if result else 1
            
        except Exception as e:
            logging.error(f"خطأ في تحديث التحذيرات: {e}")
            return 1
    
    async def _log_deleted_message(self, user_id: int, chat_id: int, text: str, result: Dict):
        """تسجيل الرسالة المحذوفة في السجل"""
        try:
            await execute_query("""
                INSERT INTO deleted_messages 
                (user_id, chat_id, message_text, detection_method, severity)
                VALUES (?, ?, ?, ?, ?)
            """, (
                user_id, chat_id, (text or "")[:500],  # حد أقصى 500 حرف
                result['reason'], result.get('severity', 1)
            ))
            
        except Exception as e:
            logging.error(f"خطأ في تسجيل الرسالة المحذوفة: {e}")
    
    async def _build_warning_message(self, result: Dict, warnings_count: int) -> str:
        """بناء رسالة التحذير"""
        warning_msg = "🚨 **تحذير - محتوى مسيء**\n\n"
        
        if result['reason'] == 'known_words':
            words_list = []
            for word, severity in result['words']:
                severity_emoji = "🔴" if severity == 3 else "🟡" if severity == 2 else "🟢"
                words_list.append(f"{severity_emoji} {word}")
            
            warning_msg += "📝 **تم اكتشاف كلمات محظورة:**\n"
            warning_msg += "\n".join(words_list)
        
        elif result['reason'] == 'ml_model':
            confidence = result['ml_score'] * 100
            warning_msg += f"🤖 **تم اكتشاف محتوى مسيء بالذكاء الاصطناعي**\n"
            warning_msg += f"🎯 نسبة الثقة: {confidence:.1f}%"
        
        warning_msg += f"\n\n⚠️ **عدد تحذيراتك:** {warnings_count}/3"
        
        if warnings_count == 1:
            warning_msg += "\n💡 هذا تحذيرك الأول، يرجى الانتباه لآدابك"
        elif warnings_count == 2:
            warning_msg += "\n⚡ هذا تحذيرك الثاني، التحذير القادم سيؤدي لعقوبة"
        elif warnings_count >= 3:
            warning_msg += "\n💀 لقد تجاوزت الحد المسموح من التحذيرات"
        
        return warning_msg
    
    async def _apply_punishment(self, message: Message, warnings_count: int):
        """تطبيق العقوبة على المستخدم"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            if warnings_count == 3:
                # كتم لمدة ساعة
                until_date = datetime.now() + timedelta(hours=1)
                try:
                    from aiogram.types import ChatPermissions
                    await message.bot.restrict_chat_member(
                        chat_id=chat_id,
                        user_id=user_id,
                        until_date=until_date,
                        permissions=ChatPermissions(can_send_messages=False)
                    )
                    logging.info(f"تم كتم المستخدم {user_id} لمدة ساعة")
                except Exception as e:
                    logging.error(f"خطأ في كتم المستخدم: {e}")
            
            elif warnings_count >= 5:
                # طرد من المجموعة
                try:
                    await message.bot.ban_chat_member(chat_id, user_id)
                    logging.info(f"تم طرد المستخدم {user_id} من المجموعة")
                except Exception as e:
                    logging.error(f"خطأ في طرد المستخدم: {e}")
        
        except Exception as e:
            logging.error(f"خطأ في تطبيق العقوبة: {e}")

# إنشاء مثيل واحد من الكلاس
detector = AbusiveDetector()

async def add_abusive_word(word: str, severity: int, added_by: int) -> bool:
    """إضافة كلمة مسيئة جديدة"""
    try:
        await execute_query(
            "INSERT OR REPLACE INTO abusive_words (word, severity, added_by) VALUES (?, ?, ?)",
            (word.lower(), severity, added_by)
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في إضافة الكلمة المسيئة: {e}")
        return False

async def remove_abusive_word(word: str) -> bool:
    """حذف كلمة مسيئة"""
    try:
        await execute_query(
            "DELETE FROM abusive_words WHERE word = ?",
            (word.lower(),)
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في حذف الكلمة المسيئة: {e}")
        return False

async def get_user_warnings(user_id: int, chat_id: int) -> Dict:
    """جلب تحذيرات المستخدم"""
    try:
        result = await execute_query(
            "SELECT warnings, total_violations, last_warning FROM user_warnings WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        if result:
            return {
                'warnings': result['warnings'],
                'total_violations': result['total_violations'],
                'last_warning': result['last_warning']
            }
        else:
            return {'warnings': 0, 'total_violations': 0, 'last_warning': None}
            
    except Exception as e:
        logging.error(f"خطأ في جلب التحذيرات: {e}")
        return {'warnings': 0, 'total_violations': 0, 'last_warning': None}

async def reset_user_warnings(user_id: int, chat_id: int) -> bool:
    """إعادة تعيين تحذيرات المستخدم"""
    try:
        await execute_query(
            "UPDATE user_warnings SET warnings = 0 WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id)
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في إعادة تعيين التحذيرات: {e}")
        return False

async def get_abusive_words_list() -> List[Dict]:
    """جلب قائمة الكلمات المسيئة"""
    try:
        result = await execute_query(
            "SELECT word, severity FROM abusive_words ORDER BY severity DESC, word ASC",
            fetch_all=True
        )
        return result if result else []
    except Exception as e:
        logging.error(f"خطأ في جلب قائمة الكلمات المسيئة: {e}")
        return []

# أوامر البوت
async def add_word_command(message: Message):
    """إضافة كلمة مسيئة جديدة"""
    # التحقق من الصلاحيات (الأسياد والمطورين فقط)
    if message.from_user.id not in MASTERS:
        await message.reply("⚠️ هذا الأمر مخصص للأسياد فقط")
        return
    try:
        if not message.text:
            await message.reply("❌ لم يتم العثور على نص الرسالة")
            return
            
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("""
📝 **إضافة كلمة محظورة**

🔸 الاستخدام: `اضافة كلمة محظورة [الكلمة] [درجة الخطورة]`

🔸 درجات الخطورة:
🟢 **1** - خفيفة (تحذير بسيط)
🟡 **2** - متوسطة (تحذير قوي)  
🔴 **3** - شديدة (عقوبة فورية)

🔸 مثال: `اضافة كلمة محظورة احمق 2`
            """)
            return
        
        word = parts[3]
        try:
            severity = int(parts[4])
            if not 1 <= severity <= 3:
                raise ValueError
        except (ValueError, IndexError):
            await message.reply("❌ درجة الخطورة يجب أن تكون رقم بين 1 و 3")
            return
        
        success = await add_abusive_word(word, severity, message.from_user.id)
        
        if success:
            severity_text = "خفيفة 🟢" if severity == 1 else "متوسطة 🟡" if severity == 2 else "شديدة 🔴"
            await message.reply(f"✅ تمت إضافة الكلمة **{word}** بدرجة خطورة {severity_text}")
        else:
            await message.reply("❌ حدث خطأ أثناء إضافة الكلمة")
            
    except Exception as e:
        logging.error(f"خطأ في أمر إضافة الكلمة: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")

async def remove_word_command(message: Message):
    """حذف كلمة مسيئة"""
    # التحقق من الصلاحيات (الأسياد والمطورين فقط)
    if message.from_user.id not in MASTERS:
        await message.reply("⚠️ هذا الأمر مخصص للأسياد فقط")
        return
    try:
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply("""
🗑️ **حذف كلمة محظورة**

🔸 الاستخدام: `حذف كلمة محظورة [الكلمة]`
🔸 مثال: `حذف كلمة محظورة احمق`
            """)
            return
        
        word = parts[3]
        success = await remove_abusive_word(word)
        
        if success:
            await message.reply(f"✅ تم حذف الكلمة **{word}** من قائمة الكلمات المحظورة")
        else:
            await message.reply("❌ حدث خطأ أثناء حذف الكلمة")
            
    except Exception as e:
        logging.error(f"خطأ في أمر حذف الكلمة: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")

async def list_words_command(message: Message):
    """عرض قائمة الكلمات المحظورة"""
    # التحقق من الصلاحيات (الأسياد والمطورين فقط)
    if message.from_user.id not in MASTERS:
        await message.reply("⚠️ هذا الأمر مخصص للأسياد فقط")
        return
    try:
        words = await get_abusive_words_list()
        
        if not words:
            await message.reply("📝 لا توجد كلمات محظورة في القائمة")
            return
        
        # تجميع الكلمات حسب درجة الخطورة
        words_by_severity = {1: [], 2: [], 3: []}
        for word_data in words:
            severity = word_data['severity']
            words_by_severity[severity].append(word_data['word'])
        
        reply_text = "📋 **قائمة الكلمات المحظورة**\n\n"
        
        severity_names = {1: "🟢 خفيفة", 2: "🟡 متوسطة", 3: "🔴 شديدة"}
        
        for severity in [3, 2, 1]:  # من الأشد للأخف
            if words_by_severity[severity]:
                reply_text += f"**{severity_names[severity]}:**\n"
                words_list = ", ".join(words_by_severity[severity][:20])  # أول 20 كلمة
                reply_text += f"{words_list}\n\n"
        
        reply_text += f"📊 **إجمالي الكلمات:** {len(words)}"
        
        await message.reply(reply_text)
        
    except Exception as e:
        logging.error(f"خطأ في أمر عرض الكلمات: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب قائمة الكلمات")

async def user_warnings_command(message: Message):
    """عرض تحذيرات مستخدم معين"""
    # التحقق من الصلاحيات (الأسياد والمطورين فقط)
    if message.from_user.id not in MASTERS:
        await message.reply("⚠️ هذا الأمر مخصص للأسياد فقط")
        return
    try:
        if not message.reply_to_message:
            await message.reply("""
👤 **فحص تحذيرات المستخدم**

🔸 رد على رسالة المستخدم واكتب: `تحذيرات المستخدم`
            """)
            return
        
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        chat_id = message.chat.id
        
        warnings_data = await get_user_warnings(target_user_id, chat_id)
        
        reply_text = f"👤 **تحذيرات المستخدم:** {target_name}\n\n"
        reply_text += f"⚠️ **التحذيرات الحالية:** {warnings_data['warnings']}/3\n"
        reply_text += f"📊 **إجمالي المخالفات:** {warnings_data['total_violations']}\n"
        
        if warnings_data['last_warning']:
            reply_text += f"🕒 **آخر تحذير:** {warnings_data['last_warning']}"
        else:
            reply_text += "✅ لم يحصل على أي تحذيرات"
        
        await message.reply(reply_text)
        
    except Exception as e:
        logging.error(f"خطأ في أمر فحص التحذيرات: {e}")
        await message.reply("❌ حدث خطأ أثناء فحص التحذيرات")

async def reset_warnings_command(message: Message):
    """إعادة تعيين تحذيرات مستخدم"""
    # التحقق من الصلاحيات (الأسياد والمطورين فقط)
    if message.from_user.id not in MASTERS:
        await message.reply("⚠️ هذا الأمر مخصص للأسياد فقط")
        return
    try:
        if not message.reply_to_message:
            await message.reply("""
🔄 **إعادة تعيين تحذيرات المستخدم**

🔸 رد على رسالة المستخدم واكتب: `اعادة تعيين التحذيرات`
            """)
            return
        
        target_user_id = message.reply_to_message.from_user.id
        target_name = message.reply_to_message.from_user.first_name
        chat_id = message.chat.id
        
        success = await reset_user_warnings(target_user_id, chat_id)
        
        if success:
            await message.reply(f"✅ تم إعادة تعيين تحذيرات المستخدم **{target_name}**")
        else:
            await message.reply("❌ حدث خطأ أثناء إعادة تعيين التحذيرات")
            
    except Exception as e:
        logging.error(f"خطأ في أمر إعادة تعيين التحذيرات: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")

async def show_detection_menu(message: Message):
    """عرض قائمة نظام كشف الألفاظ المسيئة"""
    menu_text = """
🤖 **نظام كشف الألفاظ المسيئة المتطور**

🔍 **الميزات:**
• كشف ذكي بالذكاء الاصطناعي
• قاعدة بيانات شاملة للكلمات المحظورة  
• نظام تحذيرات متدرج
• حذف تلقائي للرسائل المسيئة
• عقوبات تصاعدية (كتم → طرد)

⚙️ **أوامر الإدارة:**
• `اضافة كلمة محظورة [كلمة] [1-3]` - إضافة كلمة
• `حذف كلمة محظورة [كلمة]` - حذف كلمة
• `قائمة الكلمات المحظورة` - عرض القائمة
• `تحذيرات المستخدم` - فحص التحذيرات (رد على الرسالة)
• `اعادة تعيين التحذيرات` - مسح التحذيرات (رد على الرسالة)

💡 **درجات الخطورة:**
🟢 **1** - خفيفة | 🟡 **2** - متوسطة | 🔴 **3** - شديدة

🛡️ النظام نشط ويراقب جميع الرسائل تلقائياً
    """
    
    await message.reply(menu_text)

# تهيئة النظام عند استيراد الوحدة
async def initialize_detector():
    """تهيئة كاشف الألفاظ المسيئة"""
    if not detector.is_initialized:
        await detector.initialize()
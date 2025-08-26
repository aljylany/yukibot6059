"""
نظام الذاكرة المشتركة والمواضيع المترابطة
Shared Memory and Topic Linking System with NLTK
"""

import aiosqlite
import logging
import nltk
import re
from typing import List, Dict, Optional, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict
from config.settings import DATABASE_URL

# تحميل مكتبات NLTK المطلوبة
try:
    nltk.download('punkt', quiet=True)
    nltk.download('stopwords', quiet=True)
    nltk.download('punkt_tab', quiet=True)
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize
    NLTK_AVAILABLE = True
except:
    NLTK_AVAILABLE = False
    logging.warning("NLTK not fully available, using basic text processing")

class SharedGroupMemory:
    """نظام الذاكرة المشتركة للمجموعة مع ربط المواضيع والمستخدمين"""
    
    def __init__(self):
        self.arabic_stopwords = {
            'في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'ذلك', 'تلك',
            'هو', 'هي', 'أن', 'أنا', 'أنت', 'نحن', 'هم', 'هن', 'كان', 'كانت',
            'يكون', 'تكون', 'ما', 'لا', 'نعم', 'كيف', 'متى', 'أين', 'ماذا',
            'لماذا', 'كل', 'بعض', 'قد', 'لقد', 'سوف', 'يجب', 'يمكن', 'لكن',
            'لكن', 'إذا', 'عندما', 'بعد', 'قبل', 'حتى', 'منذ', 'خلال', 'بين'
        }
        
        # المستخدمون المميزون
        self.special_users = {
            6629947448: {  # غيو
                'name': 'غيو',
                'title': 'الأسطورة',
                'special_traits': ['محترف الألعاب', 'خبير التقنية', 'صاحب الحماس'],
                'greeting_style': 'حماسي'
            },
            # الشيخ حلال المشاكل - 7155814194
            7155814194: {  # الشيخ
                'name': 'الشيخ',
                'title': 'حلال المشاكل وكاتب العقود',
                'special_traits': ['يحل مشاكل المجموعة', 'يكتب عقود الزواج', 'الحكيم'],
                'greeting_style': 'محترم'
            }
        }
    
    async def init_shared_memory_db(self):
        """تهيئة قاعدة بيانات الذاكرة المشتركة"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # جدول المحادثات المشتركة
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS shared_conversations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        user_id INTEGER,
                        username TEXT,
                        message_text TEXT,
                        ai_response TEXT,
                        mentioned_users TEXT,  -- JSON list of mentioned user IDs
                        topics TEXT,           -- JSON list of extracted topics
                        sentiment TEXT,        -- positive, negative, neutral
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # جدول ربط المواضيع بين المستخدمين
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS topic_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        chat_id INTEGER,
                        topic TEXT,
                        user1_id INTEGER,
                        user2_id INTEGER,
                        relation_type TEXT,  -- 'mentioned', 'discussed', 'asked_about'
                        conversation_id INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (conversation_id) REFERENCES shared_conversations(id)
                    )
                ''')
                
                # جدول معلومات المستخدمين المُجمعة
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS user_profiles (
                        user_id INTEGER PRIMARY KEY,
                        chat_id INTEGER,
                        username TEXT,
                        display_name TEXT,
                        personality_traits TEXT,  -- JSON list
                        interests TEXT,           -- JSON list
                        mentioned_by TEXT,        -- JSON dict of {user_id: count}
                        last_active DATETIME,
                        conversation_style TEXT,
                        UNIQUE(user_id, chat_id)
                    )
                ''')
                
                await db.commit()
                logging.info("✅ تم تهيئة قاعدة بيانات الذاكرة المشتركة")
                
        except Exception as e:
            logging.error(f"خطأ في تهيئة قاعدة بيانات الذاكرة المشتركة: {e}")
    
    def extract_topics_and_mentions(self, text: str) -> Tuple[List[str], List[str]]:
        """استخراج المواضيع والإشارات من النص"""
        topics = []
        mentions = []
        
        # تنظيف النص
        text = re.sub(r'[^\w\s@]', ' ', text)
        
        # استخراج الإشارات (@username)
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text)
        
        if NLTK_AVAILABLE:
            try:
                # توكينز النص
                from nltk.tokenize import word_tokenize
                tokens = word_tokenize(text.lower())
                
                # إزالة الكلمات الشائعة
                filtered_tokens = [token for token in tokens 
                                 if token not in self.arabic_stopwords 
                                 and len(token) > 2 
                                 and token.isalpha()]
                
                # استخراج المواضيع (الكلمات الأساسية)
                topics = list(set(filtered_tokens))[:10]  # أهم 10 مواضيع
                
            except Exception as e:
                logging.warning(f"خطأ في معالجة NLTK: {e}")
        
        # استخراج أساسي إذا فشل NLTK
        if not topics:
            words = text.split()
            topics = [word.lower().strip('.,!?') for word in words 
                     if len(word) > 3 and word.lower() not in self.arabic_stopwords][:10]
        
        return topics, mentions
    
    def analyze_sentiment(self, text: str) -> str:
        """تحليل بسيط للمشاعر"""
        positive_words = ['حبيبي', 'رائع', 'ممتاز', 'جميل', 'شكرا', 'أحبك', 'عظيم', 'مبروك']
        negative_words = ['سيء', 'مشكلة', 'خطأ', 'زعلان', 'متضايق', 'مش حلو']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    async def save_shared_conversation(self, chat_id: int, user_id: int, username: str, 
                                     message_text: str, ai_response: str = ""):
        """حفظ المحادثة في الذاكرة المشتركة مع تحليل المواضيع"""
        try:
            topics, mentions = self.extract_topics_and_mentions(message_text)
            sentiment = self.analyze_sentiment(message_text)
            
            async with aiosqlite.connect(DATABASE_URL) as db:
                # حفظ المحادثة
                cursor = await db.execute('''
                    INSERT INTO shared_conversations 
                    (chat_id, user_id, username, message_text, ai_response, mentioned_users, topics, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (chat_id, user_id, username, message_text, ai_response, 
                      str(mentions), str(topics), sentiment))
                
                conversation_id = cursor.lastrowid
                
                # ربط المواضيع مع المستخدمين المذكورين
                for mention in mentions:
                    for topic in topics:
                        await db.execute('''
                            INSERT INTO topic_links 
                            (chat_id, topic, user1_id, user2_id, relation_type, conversation_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (chat_id, topic, user_id, 0, 'mentioned', conversation_id))
                
                # تحديث ملف المستخدم
                await self.update_user_profile(db, chat_id, user_id, username, topics, mentions)
                
                await db.commit()
                logging.info(f"✅ تم حفظ المحادثة المشتركة للمستخدم {user_id}")
                
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة المشتركة: {e}")
    
    async def update_user_profile(self, db, chat_id: int, user_id: int, username: str, 
                                topics: List[str], mentions: List[str]):
        """تحديث ملف المستخدم بناءً على نشاطه"""
        try:
            # جلب الملف الحالي
            cursor = await db.execute('''
                SELECT personality_traits, interests, mentioned_by FROM user_profiles 
                WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            row = await cursor.fetchone()
            
            if row:
                # تحديث البيانات الموجودة
                current_traits = eval(row[0]) if row[0] else []
                current_interests = eval(row[1]) if row[1] else []
                mentioned_by = eval(row[2]) if row[2] else {}
                
                # إضافة مواضيع جديدة كاهتمامات
                current_interests.extend(topics)
                current_interests = list(set(current_interests))[:20]  # الحد الأقصى 20
                
                await db.execute('''
                    UPDATE user_profiles 
                    SET interests = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND chat_id = ?
                ''', (str(current_interests), user_id, chat_id))
            else:
                # إنشاء ملف جديد
                await db.execute('''
                    INSERT INTO user_profiles 
                    (user_id, chat_id, username, display_name, interests, last_active)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, chat_id, username, username, str(topics)))
                
        except Exception as e:
            logging.error(f"خطأ في تحديث ملف المستخدم: {e}")
    
    async def get_shared_context_about_user(self, chat_id: int, target_user_id: int, 
                                          asking_user_id: int, limit: int = 5) -> str:
        """جلب السياق المشترك حول مستخدم معين"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # البحث عن المحادثات التي تذكر المستخدم المطلوب
                cursor = await db.execute('''
                    SELECT sc.user_id, sc.username, sc.message_text, sc.ai_response, sc.topics, sc.timestamp
                    FROM shared_conversations sc
                    WHERE sc.chat_id = ? 
                    AND (sc.mentioned_users LIKE ? OR sc.user_id = ?)
                    ORDER BY sc.timestamp DESC
                    LIMIT ?
                ''', (chat_id, f'%{target_user_id}%', target_user_id, limit))
                
                conversations = await cursor.fetchall()
                
                if not conversations:
                    return ""
                
                context = f"ما أعرفه عن هذا المستخدم من المحادثات السابقة:\n"
                
                for conv in conversations:
                    user_id, username, message, ai_response, topics, timestamp = conv
                    topics_list = eval(topics) if topics else []
                    
                    if user_id == target_user_id:
                        context += f"• {username} تحدث عن: {', '.join(topics_list[:3])}\n"
                    else:
                        context += f"• {username} ذكر/تحدث عنه بموضوع: {', '.join(topics_list[:3])}\n"
                
                return context
                
        except Exception as e:
            logging.error(f"خطأ في جلب السياق المشترك: {e}")
            return ""
    
    async def get_topic_connections(self, chat_id: int, topic: str, limit: int = 3) -> str:
        """جلب الروابط بين المستخدمين حول موضوع معين"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute('''
                    SELECT sc.user_id, sc.username, sc.message_text, sc.timestamp
                    FROM shared_conversations sc
                    WHERE sc.chat_id = ? 
                    AND sc.topics LIKE ?
                    ORDER BY sc.timestamp DESC
                    LIMIT ?
                ''', (chat_id, f'%{topic}%', limit))
                
                conversations = await cursor.fetchall()
                
                if not conversations:
                    return ""
                
                context = f"المحادثات حول موضوع '{topic}':\n"
                for conv in conversations:
                    user_id, username, message, timestamp = conv
                    context += f"• {username}: {message[:50]}...\n"
                
                return context
                
        except Exception as e:
            logging.error(f"خطأ في جلب روابط المواضيع: {e}")
            return ""
    
    def get_special_user_context(self, user_id: int) -> str:
        """جلب السياق الخاص للمستخدمين المميزين"""
        if user_id in self.special_users:
            user_data = self.special_users[user_id]
            return f"أنت تتحدث مع {user_data['title']} {user_data['name']}. سماته: {', '.join(user_data['special_traits'])}. "
        return ""
    
    async def find_conversations_between_users(self, chat_id: int, user1_id: int, 
                                             user2_id: int, limit: int = 3) -> str:
        """البحث عن المحادثات بين مستخدمين محددين"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute('''
                    SELECT user_id, username, message_text, topics, timestamp
                    FROM shared_conversations 
                    WHERE chat_id = ? 
                    AND (user_id = ? OR user_id = ? OR mentioned_users LIKE ? OR mentioned_users LIKE ?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (chat_id, user1_id, user2_id, f'%{user1_id}%', f'%{user2_id}%', limit))
                
                conversations = await cursor.fetchall()
                
                if not conversations:
                    return ""
                
                context = "المحادثات ذات الصلة:\n"
                for conv in conversations:
                    user_id, username, message, topics, timestamp = conv
                    topics_list = eval(topics) if topics else []
                    context += f"• {username}: تحدث عن {', '.join(topics_list[:2])}\n"
                
                return context
                
        except Exception as e:
            logging.error(f"خطأ في البحث عن المحادثات بين المستخدمين: {e}")
            return ""

# إنشاء نسخة واحدة من نظام الذاكرة المشتركة
shared_group_memory = SharedGroupMemory()
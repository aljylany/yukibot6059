"""
نظام الذاكرة المشتركة والمواضيع المترابطة - نسخة PostgreSQL
Shared Memory and Topic Linking System for PostgreSQL
"""

import asyncpg
import logging
import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

class SharedGroupMemoryPG:
    """نظام الذاكرة المشتركة للمجموعة مع ربط المواضيع والمستخدمين - PostgreSQL"""
    
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
            },
            # رهف - المستخدمة المميزة - 8278493069
            8278493069: {  # رهف
                'name': 'رهف',
                'title': 'الحبيبة المميزة',
                'special_traits': ['محبوبة من الجميع', 'شخصية جميلة', 'مميزة جداً'],
                'greeting_style': 'رومانسي'
            },
            # يوكي براندون - المطور - 6524680126
            6524680126: {  # يوكي براندون
                'name': 'يوكي براندون',
                'age': 7,
                'title': 'المطور الصغير',
                'special_traits': ['مطور البوت', 'عبقري صغير', 'مبدع'],
                'greeting_style': 'ودود'
            }
        }
    
    async def get_db_connection(self):
        """الحصول على اتصال PostgreSQL"""
        try:
            # استخدام متغيرات البيئة لـ PostgreSQL
            database_url = os.environ.get('DATABASE_URL')
            if database_url:
                return await asyncpg.connect(database_url)
            else:
                # إعدادات افتراضية للتطوير
                return await asyncpg.connect(
                    host='localhost',
                    port=5432,
                    user='postgres',
                    password='password',
                    database='bot_database'
                )
        except Exception as e:
            logging.error(f"خطأ في الاتصال بـ PostgreSQL: {e}")
            return None

    def extract_topics_and_mentions(self, text: str) -> Tuple[List[str], List[str]]:
        """استخراج المواضيع والإشارات من النص"""
        topics = []
        mentions = []
        
        # تنظيف النص
        import re
        text = re.sub(r'[^\w\s@]', ' ', text)
        
        # استخراج الإشارات (@username)
        mention_pattern = r'@(\w+)'
        mentions = re.findall(mention_pattern, text)
        
        # استخراج المواضيع (الكلمات الأساسية)
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
            
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات")
                return
                
            try:
                # حفظ المحادثة
                conversation_id = await conn.fetchval('''
                    INSERT INTO shared_conversations 
                    (chat_id, user_id, username, message_text, ai_response, mentioned_users, topics, sentiment)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    RETURNING id
                ''', chat_id, user_id, username, message_text, ai_response, 
                     json.dumps(mentions), json.dumps(topics), sentiment)
                
                # ربط المواضيع مع المستخدمين المذكورين
                for mention in mentions:
                    for topic in topics:
                        await conn.execute('''
                            INSERT INTO topic_links 
                            (chat_id, topic, user1_id, user2_id, relation_type, conversation_id)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        ''', chat_id, topic, user_id, 0, 'mentioned', conversation_id)
                
                # تحديث ملف المستخدم
                await self.update_user_profile(conn, chat_id, user_id, username, topics, mentions)
                
                logging.info(f"✅ تم حفظ المحادثة المشتركة للمستخدم {user_id}")
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة المشتركة: {e}")
    
    async def update_user_profile(self, conn, chat_id: int, user_id: int, username: str, 
                                topics: List[str], mentions: List[str]):
        """تحديث ملف المستخدم بناءً على نشاطه"""
        try:
            # جلب الملف الحالي
            row = await conn.fetchrow('''
                SELECT personality_traits, interests, mentioned_by FROM user_profiles 
                WHERE user_id = $1 AND chat_id = $2
            ''', user_id, chat_id)
            
            if row:
                # تحديث البيانات الموجودة
                current_traits = json.loads(row['personality_traits']) if row['personality_traits'] else []
                current_interests = json.loads(row['interests']) if row['interests'] else []
                mentioned_by = json.loads(row['mentioned_by']) if row['mentioned_by'] else {}
                
                # إضافة مواضيع جديدة كاهتمامات
                current_interests.extend(topics)
                current_interests = list(set(current_interests))[:20]  # الحد الأقصى 20
                
                await conn.execute('''
                    UPDATE user_profiles 
                    SET interests = $1, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = $2 AND chat_id = $3
                ''', json.dumps(current_interests), user_id, chat_id)
            else:
                # إنشاء ملف جديد
                await conn.execute('''
                    INSERT INTO user_profiles 
                    (user_id, chat_id, username, display_name, interests, last_active)
                    VALUES ($1, $2, $3, $4, $5, CURRENT_TIMESTAMP)
                ''', user_id, chat_id, username, username, json.dumps(topics))
                
        except Exception as e:
            logging.error(f"خطأ في تحديث ملف المستخدم: {e}")
    
    async def get_shared_context_about_user(self, chat_id: int, target_user_id: int, 
                                          asking_user_id: int, limit: int = 5) -> str:
        """جلب السياق المشترك حول مستخدم معين"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                return ""
                
            try:
                # البحث عن المحادثات التي تذكر المستخدم المطلوب أو التي كتبها
                rows = await conn.fetch('''
                    SELECT user_id, username, message_text, ai_response, topics, timestamp
                    FROM shared_conversations
                    WHERE chat_id = $1 
                    AND (mentioned_users LIKE $2 OR user_id = $3 OR message_text ILIKE $4)
                    ORDER BY timestamp DESC
                    LIMIT $5
                ''', chat_id, f'%{target_user_id}%', target_user_id, f'%{target_user_id}%', limit)
                
                if not rows:
                    # البحث في أسماء المستخدمين المعروفين
                    user_names = {
                        8278493069: 'رهف',
                        7155814194: 'الشيخ',
                        6629947448: 'غيو'
                    }
                    user_name = user_names.get(target_user_id, 'هذا المستخدم')
                    return f"لم أجد محادثات حديثة مع {user_name} في الذاكرة المشتركة."
                
                # الحصول على اسم المستخدم المستهدف
                target_username = None
                user_names = {
                    8278493069: 'رهف',
                    7155814194: 'الشيخ', 
                    6629947448: 'غيو'
                }
                
                context = f"ما أعرفه عن {user_names.get(target_user_id, 'هذا المستخدم')} من المحادثات:\n"
                
                for row in rows:
                    user_id, username, message, ai_response, topics, timestamp = row
                    topics_list = json.loads(topics) if topics else []
                    
                    if user_id == target_user_id:
                        # المستخدم المستهدف نفسه كتب الرسالة
                        context += f"• {username} قال: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                        if ai_response:
                            context += f"  → ورديت عليه: {ai_response[:80]}{'...' if len(ai_response) > 80 else ''}\n"
                    else:
                        # شخص آخر تحدث عنه
                        context += f"• {username} ذكره وتحدث عن: {', '.join(topics_list[:3])}\n"
                
                return context
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب السياق المشترك: {e}")
            return ""
    
    def get_special_user_context(self, user_id: int) -> str:
        """جلب السياق الخاص للمستخدمين المميزين"""
        if user_id in self.special_users:
            user_data = self.special_users[user_id]
            context = f"أنت تتحدث مع {user_data['title']} {user_data['name']}. سماته: {', '.join(user_data['special_traits'])}. "
            if 'age' in user_data:
                context += f"العمر: {user_data['age']} سنوات. "
            return context
        return ""
    
    async def get_brandon_info(self) -> Dict:
        """جلب معلومات يوكي براندون المحفوظة"""
        try:
            if 6524680126 in self.special_users:
                return self.special_users[6524680126]
            
            # البحث في قاعدة البيانات
            conn = await self.get_db_connection()
            if not conn:
                return {}
                
            try:
                row = await conn.fetchrow('''
                    SELECT message_text, ai_response FROM shared_conversations 
                    WHERE user_id = 6524680126 AND (message_text LIKE '%عمري%' OR message_text LIKE '%براندون%')
                    ORDER BY timestamp DESC LIMIT 1
                ''')
                
                if row:
                    return {
                        'name': 'يوكي براندون',
                        'age': 7,
                        'title': 'المطور الصغير',
                        'message': row['message_text'],
                        'response': row['ai_response']
                    }
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب معلومات براندون: {e}")
        
        return {}

# إنشاء نسخة واحدة من نظام الذاكرة المشتركة
shared_group_memory_pg = SharedGroupMemoryPG()
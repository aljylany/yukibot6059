"""
نظام الذاكرة المشتركة والمواضيع المترابطة - نسخة SQLite محسنة
Enhanced Shared Memory and Topic Linking System for SQLite
"""

import aiosqlite
import logging
import json
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

class SharedGroupMemorySQLite:
    """نظام الذاكرة المشتركة للمجموعة مع ربط المواضيع والمستخدمين - SQLite"""
    
    def __init__(self):
        self.db_path = "bot_database.db"
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
            7155814194: {  # الشيخ حلال المشاكل
                'name': 'الشيخ',
                'title': 'حلال المشاكل وكاتب العقود',
                'special_traits': ['يحل مشاكل المجموعة', 'يكتب عقود الزواج', 'الحكيم'],
                'greeting_style': 'محترم'
            },
            8278493069: {  # رهف - المستخدمة المميزة
                'name': 'رهف',
                'title': 'الحبيبة المميزة',
                'special_traits': ['محبوبة من الجميع', 'شخصية جميلة', 'مميزة جداً'],
                'greeting_style': 'رومانسي'
            },
            6524680126: {  # يوكي براندون - المطور
                'name': 'يوكي براندون',
                'age': 7,
                'title': 'المطور الصغير',
                'special_traits': ['مطور البوت', 'عبقري صغير', 'مبدع'],
                'greeting_style': 'ودود'
            }
        }
    
    async def get_db_connection(self):
        """الحصول على اتصال SQLite"""
        try:
            return await aiosqlite.connect(self.db_path)
        except Exception as e:
            logging.error(f"خطأ في الاتصال بـ SQLite: {e}")
            return None
    
    def extract_topics_and_mentions(self, text: str) -> Tuple[List[str], List[str]]:
        """استخراج المواضيع والإشارات من النص"""
        import re
        
        # استخراج الإشارات (@username)
        mentions = re.findall(r'@(\w+)', text)
        
        # استخراج المواضيع (الكلمات المهمة)
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
                                     message_text: str, ai_response: str = None):
        """حفظ محادثة في الذاكرة المشتركة"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات")
                return
                
            try:
                # استخراج المواضيع والإشارات
                topics, mentions = self.extract_topics_and_mentions(message_text)
                sentiment = self.analyze_sentiment(message_text)
                
                # حفظ المحادثة
                await conn.execute('''
                    INSERT INTO shared_conversations 
                    (chat_id, user_id, username, message_text, ai_response, mentioned_users, topics, sentiment)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    chat_id, user_id, username, message_text, ai_response,
                    json.dumps(mentions), json.dumps(topics), sentiment
                ))
                
                # حفظ روابط المواضيع
                for topic in topics:
                    await conn.execute('''
                        INSERT INTO topic_links (chat_id, topic, user_ids, relation_type)
                        VALUES (?, ?, ?, ?)
                    ''', (chat_id, topic, json.dumps([user_id]), 'discussion'))
                
                # تحديث ملف المستخدم
                await self.update_user_profile(conn, chat_id, user_id, username, topics, mentions)
                
                await conn.commit()
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
            cursor = await conn.execute('''
                SELECT personality_traits, interests, mentioned_by FROM user_profiles 
                WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            row = await cursor.fetchone()
            
            if row:
                # تحديث البيانات الموجودة
                current_traits = json.loads(row[0]) if row[0] else []
                current_interests = json.loads(row[1]) if row[1] else []
                mentioned_by = json.loads(row[2]) if row[2] else {}
                
                # إضافة مواضيع جديدة كاهتمامات
                current_interests.extend(topics)
                current_interests = list(set(current_interests))[:20]  # الحد الأقصى 20
                
                await conn.execute('''
                    UPDATE user_profiles 
                    SET interests = ?, last_active = CURRENT_TIMESTAMP
                    WHERE user_id = ? AND chat_id = ?
                ''', (json.dumps(current_interests), user_id, chat_id))
            else:
                # إنشاء ملف جديد
                await conn.execute('''
                    INSERT INTO user_profiles 
                    (user_id, chat_id, username, display_name, interests, last_active)
                    VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ''', (user_id, chat_id, username, username, json.dumps(topics)))
                
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
                cursor = await conn.execute('''
                    SELECT user_id, username, message_text, ai_response, topics, timestamp
                    FROM shared_conversations
                    WHERE chat_id = ? 
                    AND (mentioned_users LIKE ? OR user_id = ?)
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (chat_id, f'%{target_user_id}%', target_user_id, limit))
                
                rows = await cursor.fetchall()
                
                if not rows:
                    return ""
                
                context_parts = []
                for row in rows:
                    user_id, username, message_text, ai_response, topics, timestamp = row
                    # تحويل JSON strings إلى lists
                    try:
                        topics_list = json.loads(topics) if topics else []
                    except:
                        topics_list = []
                    
                    context_parts.append(f"[{timestamp}] {username}: {message_text[:100]}")
                    if topics_list:
                        context_parts.append(f"المواضيع: {', '.join(topics_list[:3])}")
                
                return "\n".join(context_parts)
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب السياق المشترك: {e}")
            return ""
    
    async def get_group_conversation_context(self, chat_id: int, limit: int = 10) -> str:
        """جلب سياق المحادثة العامة للمجموعة"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                return ""
                
            try:
                cursor = await conn.execute('''
                    SELECT username, message_text, sentiment, timestamp
                    FROM shared_conversations
                    WHERE chat_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (chat_id, limit))
                
                rows = await cursor.fetchall()
                
                if not rows:
                    return ""
                
                context_parts = []
                for row in rows:
                    username, message_text, sentiment, timestamp = row
                    emoji = {'positive': '😊', 'negative': '😔', 'neutral': '😐'}.get(sentiment, '😐')
                    context_parts.append(f"{emoji} {username}: {message_text[:80]}")
                
                return "\n".join(reversed(context_parts[-5:]))  # آخر 5 رسائل
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب سياق المجموعة: {e}")
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
                cursor = await conn.execute('''
                    SELECT message_text, ai_response FROM shared_conversations 
                    WHERE user_id = 6524680126 AND (message_text LIKE '%عمري%' OR message_text LIKE '%براندون%')
                    ORDER BY timestamp DESC LIMIT 1
                ''')
                row = await cursor.fetchone()
                
                if row:
                    return {
                        'name': 'يوكي براندون',
                        'age': 7,
                        'title': 'المطور الصغير',
                        'message': row[0],
                        'response': row[1]
                    }
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب معلومات براندون: {e}")
        
        return {}

# إنشاء نسخة عالمية من النظام
shared_group_memory_sqlite = SharedGroupMemorySQLite()
"""
نظام البحث في المواضيع والذاكرة المشتركة
Topic Search and Shared Memory Query System
"""

import logging
from typing import List, Dict, Optional
from modules.shared_memory_pg import shared_group_memory_pg

class TopicSearchEngine:
    """محرك البحث في المواضيع والذاكرة المشتركة"""
    
    def __init__(self):
        self.search_phrases = {
            'user_info': ['ماذا تعرف عن', 'معلومات عن', 'قل لي عن'],
            'conversation_history': ['ماذا كنتم تتحدثون', 'ماذا قال', 'تحدثتم عني', 'قال عني'],
            'topic_search': ['من تحدث عن', 'من ذكر', 'محادثات حول'],
            'user_connections': ['العلاقة بين', 'ماذا يعرف', 'تحدثوا مع بعض']
        }
    
    async def process_query(self, query: str, user_id: int, chat_id: int) -> Optional[str]:
        """معالجة استعلام البحث وإرجاع النتائج"""
        query_lower = query.lower().strip()
        
        try:
            # البحث عن معلومات مستخدم معين
            if any(phrase in query_lower for phrase in self.search_phrases['user_info']):
                return await self._search_user_info(query, user_id, chat_id)
            
            # البحث في تاريخ المحادثات
            elif any(phrase in query_lower for phrase in self.search_phrases['conversation_history']):
                return await self._search_conversation_history(query, user_id, chat_id)
            
            # البحث عن موضوع معين
            elif any(phrase in query_lower for phrase in self.search_phrases['topic_search']):
                return await self._search_topic(query, user_id, chat_id)
            
            # البحث عن الروابط بين المستخدمين
            elif any(phrase in query_lower for phrase in self.search_phrases['user_connections']):
                return await self._search_user_connections(query, user_id, chat_id)
            
        except Exception as e:
            logging.error(f"خطأ في معالجة الاستعلام: {e}")
        
        return None
    
    async def _search_user_info(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث عن معلومات مستخدم معين"""
        # استخراج اسم المستخدم من الاستعلام
        words = query.split()
        target_username = None
        
        for word in words:
            if word.startswith('@'):
                target_username = word[1:]
                break
            elif len(word) > 2 and word not in ['ماذا', 'تعرف', 'عن', 'معلومات']:
                target_username = word
                break
        
        if not target_username:
            return "لم أتمكن من تحديد المستخدم المطلوب البحث عنه."
        
        # البحث في الذاكرة المشتركة
        # البحث عن المستخدم بالاسم في قاعدة البيانات
        try:
            conn = await shared_group_memory_pg.get_db_connection()
            if not conn:
                return f"لم أتمكن من الاتصال بقاعدة البيانات للبحث عن {target_username}."
            
            try:
                # البحث عن المحادثات التي تحتوي على الاسم المطلوب
                rows = await conn.fetch('''
                    SELECT user_id, username, message_text, ai_response, topics, timestamp
                    FROM shared_conversations
                    WHERE chat_id = $1 
                    AND (message_text ILIKE $2 OR username ILIKE $3 OR topics ILIKE $4)
                    ORDER BY timestamp DESC
                    LIMIT 10
                ''', chat_id, f'%{target_username}%', f'%{target_username}%', f'%{target_username}%')
                
                if rows:
                    context = f"معلومات عن {target_username}:\n"
                    for row in rows:
                        user_id_found, username, message, ai_response, topics, timestamp = row
                        # استخراج المعلومات المهمة من الرسالة
                        if 'عمري' in message or 'عمر' in message:
                            context += f"• العمر: {message}\n"
                        if 'اسمي' in message:
                            context += f"• الاسم: {message}\n"
                        if 'احب' in message or 'أحب' in message:
                            context += f"• الاهتمامات: {message}\n"
                        
                        # إضافة جزء من الرسالة
                        context += f"• قال: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                        if ai_response:
                            context += f"  → ورد يوكي: {ai_response[:80]}{'...' if len(ai_response) > 80 else ''}\n"
                        context += "\n"
                    
                    return context
                else:
                    return f"لم أجد معلومات مسجلة عن {target_username} في ذاكرتي المشتركة."
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في البحث عن المستخدم: {e}")
            return f"حدث خطأ أثناء البحث عن {target_username}."
        
    
    async def _search_conversation_history(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث في تاريخ المحادثات"""
        context = await shared_group_memory_pg.get_shared_context_about_user(chat_id, user_id, user_id, limit=8)
        
        if context:
            return f"🗣️ **المحادثات التي تخصك:**\n\n{context}"
        else:
            return "لم أجد محادثات مسجلة عنك في الذاكرة المشتركة."
    
    async def _search_topic(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث عن موضوع معين"""
        # استخراج الموضوع من الاستعلام
        words = query.split()
        topic = None
        
        for i, word in enumerate(words):
            if word in ['عن', 'حول']:
                if i + 1 < len(words):
                    topic = words[i + 1]
                    break
        
        if not topic:
            return "لم أتمكن من تحديد الموضوع المطلوب البحث عنه."
        
        # البحث عن المحادثات المتعلقة بالموضوع
        try:
            conn = await shared_group_memory_pg.get_db_connection()
            if not conn:
                return f"لم أتمكن من الاتصال بقاعدة البيانات للبحث عن الموضوع {topic}."
            
            try:
                rows = await conn.fetch('''
                    SELECT user_id, username, message_text, ai_response, timestamp
                    FROM shared_conversations
                    WHERE chat_id = $1 AND (message_text ILIKE $2 OR topics ILIKE $3)
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''', chat_id, f'%{topic}%', f'%{topic}%')
                
                if rows:
                    context = f"المحادثات حول موضوع '{topic}':\n"
                    for row in rows:
                        user_id_found, username, message, ai_response, timestamp = row
                        context += f"• {username}: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                        if ai_response:
                            context += f"  → يوكي رد: {ai_response[:80]}{'...' if len(ai_response) > 80 else ''}\n"
                        context += "\n"
                    return context
                else:
                    return f"لم أجد محادثات مسجلة حول موضوع '{topic}'."
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في البحث عن الموضوع: {e}")
            return f"حدث خطأ أثناء البحث عن الموضوع {topic}."
        
    
    async def _search_user_connections(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث عن الروابط بين المستخدمين"""
        try:
            conn = await shared_group_memory_pg.get_db_connection()
            if not conn:
                return "لم أتمكن من الاتصال بقاعدة البيانات."
            
            try:
                rows = await conn.fetch('''
                    SELECT user_id, username, message_text, mentioned_users, timestamp
                    FROM shared_conversations
                    WHERE chat_id = $1 AND (user_id = $2 OR mentioned_users LIKE $3)
                    ORDER BY timestamp DESC
                    LIMIT 5
                ''', chat_id, user_id, f'%{user_id}%')
                
                if rows:
                    context = "الروابط والمحادثات:\n"
                    for row in rows:
                        user_id_found, username, message, mentioned_users, timestamp = row
                        context += f"• {username}: {message[:100]}{'...' if len(message) > 100 else ''}\n"
                    return context
                else:
                    return "لم أجد روابط محادثات مسجلة."
                    
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في البحث عن الروابط: {e}")
            return "حدث خطأ أثناء البحث عن الروابط."

# إنشاء نسخة واحدة من محرك البحث
topic_search_engine = TopicSearchEngine()
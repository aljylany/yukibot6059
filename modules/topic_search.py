"""
نظام البحث في المواضيع والذاكرة المشتركة
Topic Search and Shared Memory Query System
"""

import logging
from typing import List, Dict, Optional
from modules.shared_memory import shared_group_memory

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
        context = await shared_group_memory.get_shared_context_about_user(chat_id, 0, user_id, limit=10)
        
        if context:
            return f"🔍 **معلومات عن {target_username}:**\n\n{context}"
        else:
            return f"لم أجد معلومات مسجلة عن {target_username} في ذاكرتي المشتركة."
    
    async def _search_conversation_history(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث في تاريخ المحادثات"""
        context = await shared_group_memory.get_shared_context_about_user(chat_id, user_id, user_id, limit=8)
        
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
        
        context = await shared_group_memory.get_topic_connections(chat_id, topic, limit=5)
        
        if context:
            return f"📝 **المحادثات حول موضوع '{topic}':**\n\n{context}"
        else:
            return f"لم أجد محادثات مسجلة حول موضوع '{topic}'."
    
    async def _search_user_connections(self, query: str, user_id: int, chat_id: int) -> str:
        """البحث عن الروابط بين المستخدمين"""
        context = await shared_group_memory.find_conversations_between_users(chat_id, user_id, 0, limit=5)
        
        if context:
            return f"🔗 **الروابط والمحادثات:**\n\n{context}"
        else:
            return "لم أجد روابط محادثات مسجلة."

# إنشاء نسخة واحدة من محرك البحث
topic_search_engine = TopicSearchEngine()
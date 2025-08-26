"""
نظام ذاكرة المحادثات - نسخة PostgreSQL
Conversation Memory System for PostgreSQL
"""

import asyncpg
import logging
import os
from typing import List, Dict, Optional

class ConversationMemoryPG:
    """نظام ذاكرة المحادثات لحفظ آخر 50 رسالة لكل مستخدم - PostgreSQL"""
    
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
    
    async def save_conversation(self, user_id: int, user_message: str, ai_response: str):
        """حفظ محادثة جديدة وإدارة الحد الأقصى لعدد المحادثات"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات لحفظ المحادثة")
                return
                
            try:
                # حفظ المحادثة الجديدة
                await conn.execute('''
                    INSERT INTO conversation_history (user_id, user_message, ai_response)
                    VALUES ($1, $2, $3)
                ''', user_id, user_message, ai_response)
                
                # حذف المحادثات القديمة (أكثر من 50)
                await conn.execute('''
                    DELETE FROM conversation_history 
                    WHERE user_id = $1 AND id NOT IN (
                        SELECT id FROM conversation_history 
                        WHERE user_id = $1 
                        ORDER BY timestamp DESC 
                        LIMIT 50
                    )
                ''', user_id)
                
                logging.info(f"✅ تم حفظ المحادثة للمستخدم {user_id}")
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة: {e}")

    async def get_conversation_history(self, user_id: int, limit: int = 15) -> List[Dict]:
        """جلب آخر محادثات للمستخدم (افتراضياً آخر 15)"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات لجلب المحادثات")
                return []
                
            try:
                rows = await conn.fetch('''
                    SELECT user_message, ai_response, timestamp 
                    FROM conversation_history 
                    WHERE user_id = $1 
                    ORDER BY timestamp DESC 
                    LIMIT $2
                ''', user_id, limit)
                
                # ترتيب المحادثات من الأقدم للأحدث للسياق المنطقي
                conversations = []
                for row in reversed(list(rows)):
                    conversations.append({
                        'user_message': row['user_message'],
                        'ai_response': row['ai_response'],
                        'timestamp': row['timestamp']
                    })
                
                return conversations
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب المحادثات: {e}")
            return []

    async def clear_conversation_history(self, user_id: int):
        """مسح تاريخ المحادثات للمستخدم"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات لمسح المحادثات")
                return
                
            try:
                await conn.execute('''
                    DELETE FROM conversation_history WHERE user_id = $1
                ''', user_id)
                
                logging.info(f"✅ تم مسح تاريخ المحادثات للمستخدم {user_id}")
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في مسح المحادثات: {e}")

    def format_conversation_context(self, conversations: List[Dict]) -> str:
        """تنسيق المحادثات للاستخدام كسياق"""
        if not conversations:
            return ""
        
        context = "المحادثات السابقة:\n"
        for conv in conversations:
            context += f"المستخدم: {conv['user_message']}\n"
            context += f"يوكي: {conv['ai_response']}\n"
        
        context += "\nالآن استكمل المحادثة بطريقة طبيعية:"
        return context

# إنشاء نسخة واحدة من نظام الذاكرة
conversation_memory_pg = ConversationMemoryPG()
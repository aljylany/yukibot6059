"""
نظام ذاكرة المحادثات - نسخة SQLite محسنة
Enhanced Conversation Memory System for SQLite
"""

import aiosqlite
import logging
from typing import List, Dict, Optional

class ConversationMemorySQLite:
    """نظام ذاكرة المحادثات لحفظ آخر 50 رسالة لكل مستخدم - SQLite"""
    
    def __init__(self):
        self.db_path = "bot_database.db"
    
    async def get_db_connection(self):
        """الحصول على اتصال SQLite"""
        try:
            return await aiosqlite.connect(self.db_path)
        except Exception as e:
            logging.error(f"خطأ في الاتصال بـ SQLite: {e}")
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
                    VALUES (?, ?, ?)
                ''', (user_id, user_message, ai_response))
                
                # حذف المحادثات القديمة (أكثر من 50)
                await conn.execute('''
                    DELETE FROM conversation_history 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM conversation_history 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 50
                    )
                ''', (user_id, user_id))
                
                await conn.commit()
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
                cursor = await conn.execute('''
                    SELECT user_message, ai_response, timestamp
                    FROM conversation_history
                    WHERE user_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = await cursor.fetchall()
                
                conversations = []
                for row in rows:
                    conversations.append({
                        'user_message': row[0],
                        'ai_response': row[1],
                        'timestamp': row[2]
                    })
                
                return list(reversed(conversations))  # الأقدم أولاً
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في جلب المحادثات: {e}")
            return []

    async def clear_conversation_history(self, user_id: int) -> bool:
        """مسح تاريخ المحادثات لمستخدم معين"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                return False
                
            try:
                await conn.execute('''
                    DELETE FROM conversation_history WHERE user_id = ?
                ''', (user_id,))
                
                await conn.commit()
                logging.info(f"✅ تم مسح تاريخ المحادثات للمستخدم {user_id}")
                return True
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في مسح المحادثات: {e}")
            return False

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

# إنشاء نسخة عالمية من النظام
conversation_memory_sqlite = ConversationMemorySQLite()
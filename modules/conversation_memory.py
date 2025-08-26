"""
نظام ذاكرة المحادثات
Conversation Memory System
"""

import aiosqlite
import logging
from typing import List, Dict, Optional
from config.settings import DATABASE_URL

class ConversationMemory:
    """نظام ذاكرة المحادثات لحفظ آخر 10 رسائل لكل مستخدم"""
    
    async def save_conversation(self, user_id: int, user_message: str, ai_response: str):
        """حفظ محادثة جديدة وإدارة الحد الأقصى لعدد المحادثات"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # حفظ المحادثة الجديدة
                await db.execute('''
                    INSERT INTO conversation_history (user_id, user_message, ai_response)
                    VALUES (?, ?, ?)
                ''', (user_id, user_message, ai_response))
                
                # حذف المحادثات القديمة (أكثر من 10)
                await db.execute('''
                    DELETE FROM conversation_history 
                    WHERE user_id = ? AND id NOT IN (
                        SELECT id FROM conversation_history 
                        WHERE user_id = ? 
                        ORDER BY timestamp DESC 
                        LIMIT 10
                    )
                ''', (user_id, user_id))
                
                await db.commit()
                logging.info(f"✅ تم حفظ المحادثة للمستخدم {user_id}")
                
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة: {e}")

    async def get_conversation_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """جلب آخر محادثات للمستخدم (افتراضياً آخر 5)"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute('''
                    SELECT user_message, ai_response, timestamp 
                    FROM conversation_history 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (user_id, limit))
                
                rows = await cursor.fetchall()
                
                # ترتيب المحادثات من الأقدم للأحدث للسياق المنطقي
                conversations = []
                for row in reversed(rows):
                    conversations.append({
                        'user_message': row[0],
                        'ai_response': row[1],
                        'timestamp': row[2]
                    })
                
                return conversations
                
        except Exception as e:
            logging.error(f"خطأ في جلب المحادثات: {e}")
            return []

    async def clear_conversation_history(self, user_id: int):
        """مسح تاريخ المحادثات للمستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute('''
                    DELETE FROM conversation_history WHERE user_id = ?
                ''', (user_id,))
                
                await db.commit()
                logging.info(f"✅ تم مسح تاريخ المحادثات للمستخدم {user_id}")
                
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
conversation_memory = ConversationMemory()
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
        self._column_checked = False  # فلاج للتأكد من فحص العمود مرة واحدة فقط
    
    async def _ensure_chat_id_column(self, conn):
        """التأكد من وجود عمود chat_id في جدول conversation_history"""
        if self._column_checked:
            return
        
        try:
            # التحقق من وجود العمود
            cursor = await conn.execute("PRAGMA table_info(conversation_history)")
            columns = await cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            if 'chat_id' not in column_names:
                # إضافة العمود الجديد
                await conn.execute("ALTER TABLE conversation_history ADD COLUMN chat_id INTEGER")
                await conn.commit()
                logging.info("✅ تم إضافة عمود chat_id إلى جدول conversation_history")
            
            self._column_checked = True
                
        except Exception as e:
            logging.error(f"خطأ في التحقق من عمود chat_id: {e}")
    
    
    async def get_db_connection(self):
        """الحصول على اتصال SQLite مع التأكد من وجود العمود المطلوب"""
        try:
            conn = await aiosqlite.connect(self.db_path)
            # فحص وإضافة عمود chat_id إذا لم يكن موجوداً
            await self._ensure_chat_id_column(conn)
            return conn
        except Exception as e:
            logging.error(f"خطأ في الاتصال بـ SQLite: {e}")
            return None
    
    async def save_conversation(self, user_id: int, user_message: str, ai_response: str, chat_id: Optional[int] = None):
        """حفظ محادثة جديدة وإدارة الحد الأقصى لعدد المحادثات"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات لحفظ المحادثة")
                return
                
            try:
                # حفظ المحادثة الجديدة
                await conn.execute('''
                    INSERT INTO conversation_history (user_id, chat_id, user_message, ai_response)
                    VALUES (?, ?, ?, ?)
                ''', (user_id, chat_id, user_message, ai_response))
                
                # حذف المحادثات القديمة (أكثر من 50) - مع مراعاة السياق
                where_clause = "user_id = ?"
                params = [user_id]
                if chat_id is not None:
                    where_clause += " AND chat_id = ?"
                    params.append(chat_id)
                
                # إنشاء قائمة المعاملات الصحيحة للاستعلام المضاعف
                query_params = params + params  # نحتاج المعاملات للجزء الخارجي والداخلي من الاستعلام
                
                await conn.execute(f'''
                    DELETE FROM conversation_history 
                    WHERE {where_clause} AND id NOT IN (
                        SELECT id FROM conversation_history 
                        WHERE {where_clause}
                        ORDER BY timestamp DESC 
                        LIMIT 50
                    )
                ''', query_params)
                
                await conn.commit()
                context_info = f" في المجموعة {chat_id}" if chat_id else " في المحادثة الخاصة"
                logging.info(f"✅ تم حفظ المحادثة للمستخدم {user_id}{context_info}")
                
            finally:
                await conn.close()
                
        except Exception as e:
            logging.error(f"خطأ في حفظ المحادثة: {e}")

    async def get_conversation_history(self, user_id: int, limit: int = 15, chat_id: Optional[int] = None) -> List[Dict]:
        """جلب آخر محادثات للمستخدم (افتراضياً آخر 15)"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                logging.error("لا يمكن الاتصال بقاعدة البيانات لجلب المحادثات")
                return []
                
            try:
                # بناء الاستعلام حسب السياق (مجموعة أو محادثة خاصة)
                if chat_id is not None:
                    # جلب المحادثات الخاصة بهذه المجموعة
                    cursor = await conn.execute('''
                        SELECT user_message, ai_response, timestamp
                        FROM conversation_history
                        WHERE user_id = ? AND chat_id = ?
                        ORDER BY timestamp DESC
                        LIMIT ?
                    ''', (user_id, chat_id, limit))
                else:
                    # جلب المحادثات الخاصة أو العامة (بدون تحديد مجموعة)
                    cursor = await conn.execute('''
                        SELECT user_message, ai_response, timestamp
                        FROM conversation_history
                        WHERE user_id = ? AND (chat_id IS NULL OR chat_id = 0)
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

    async def clear_conversation_history(self, user_id: int, chat_id: Optional[int] = None) -> bool:
        """مسح تاريخ المحادثات لمستخدم معين"""
        try:
            conn = await self.get_db_connection()
            if not conn:
                return False
                
            try:
                # حذف بناءً على السياق
                if chat_id is not None:
                    # حذف محادثات مجموعة محددة
                    await conn.execute('''
                        DELETE FROM conversation_history WHERE user_id = ? AND chat_id = ?
                    ''', (user_id, chat_id))
                else:
                    # حذف جميع المحادثات
                    await conn.execute('''
                        DELETE FROM conversation_history WHERE user_id = ?
                    ''', (user_id,))
                
                await conn.commit()
                context_info = f" في المجموعة {chat_id}" if chat_id else " (جميع المحادثات)"
                logging.info(f"✅ تم مسح تاريخ المحادثات للمستخدم {user_id}{context_info}")
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
"""
عمليات قاعدة البيانات المبسطة
Simplified Database Operations
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
import aiosqlite

from config.database import DATABASE_URL


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """الحصول على بيانات المستخدم"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على المستخدم {user_id}: {e}")
        return None


async def create_user(user_id: int, username: str = "", first_name: str = "") -> bool:
    """إنشاء مستخدم جديد"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, first_name, balance, bank_balance, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username or "", first_name or "", 1000, 0, 
                 datetime.now().isoformat(), datetime.now().isoformat())
            )
            await db.commit()
            
            logging.info(f"تم إنشاء مستخدم جديد: {user_id} - {username}")
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إنشاء المستخدم {user_id}: {e}")
        return False


async def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> Optional[Dict[str, Any]]:
    """الحصول على المستخدم أو إنشاؤه إذا لم يكن موجوداً"""
    try:
        # محاولة الحصول على المستخدم
        user = await get_user(user_id)
        
        if user:
            # تحديث آخر نشاط
            await update_user_activity(user_id)
            return user
        
        # إنشاء مستخدم جديد إذا لم يكن موجوداً
        if await create_user(user_id, username or "", first_name or ""):
            return await get_user(user_id)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في get_or_create_user: {e}")
        return None


async def update_user_activity(user_id: int) -> bool:
    """تحديث آخر نشاط للمستخدم"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                "UPDATE users SET updated_at = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث نشاط المستخدم {user_id}: {e}")
        return False


async def update_user_balance(user_id: int, new_balance: float) -> bool:
    """تحديث رصيد المستخدم مع فحص الحد الأقصى"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                "UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?",
                (new_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            
            # فحص الحد الأقصى للأموال
            try:
                from modules.ranking_system import check_money_limit_and_convert
                await check_money_limit_and_convert(user_id)
            except Exception as ranking_error:
                logging.error(f"خطأ في فحص نظام التصنيف: {ranking_error}")
                
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد المستخدم {user_id}: {e}")
        return False


async def update_user_bank_balance(user_id: int, new_bank_balance: float) -> bool:
    """تحديث رصيد البنك للمستخدم مع فحص الحد الأقصى"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                "UPDATE users SET bank_balance = ?, updated_at = ? WHERE user_id = ?",
                (new_bank_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            
            # فحص الحد الأقصى للأموال
            try:
                from modules.ranking_system import check_money_limit_and_convert
                await check_money_limit_and_convert(user_id)
            except Exception as ranking_error:
                logging.error(f"خطأ في فحص نظام التصنيف: {ranking_error}")
            
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد البنك للمستخدم {user_id}: {e}")
        return False


async def add_transaction(user_id: int = None, transaction_type: str = "general", amount: float = 0, 
                         description: str = "", from_user_id: Optional[int] = None, 
                         to_user_id: Optional[int] = None) -> bool:
    """إضافة معاملة جديدة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                INSERT INTO transactions (user_id, transaction_type, amount, description, 
                                        from_user_id, to_user_id, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, transaction_type, amount, description or "", 
                 from_user_id, to_user_id, datetime.now().isoformat())
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إضافة المعاملة: {e}")
        return False


async def is_user_banned(user_id: int) -> bool:
    """التحقق من حظر المستخدم"""
    try:
        user = await get_user(user_id)
        return user.get('is_banned', False) if user else False
    except Exception as e:
        logging.error(f"خطأ في التحقق من حظر المستخدم {user_id}: {e}")
        return False


async def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
    """تنفيذ استعلام قاعدة البيانات"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute(query, params) as cursor:
                if fetch_one:
                    result = await cursor.fetchone()
                    await db.commit()
                    return dict(result) if result else None
                elif fetch_all:
                    results = await cursor.fetchall()
                    await db.commit()
                    return [dict(row) for row in results]
                else:
                    await db.commit()
                    return cursor.rowcount
                    
    except Exception as e:
        logging.error(f"خطأ في تنفيذ الاستعلام: {e}")
        return None if (fetch_one or fetch_all) else False


async def get_user_message_count(user_id: int, chat_id: int) -> int:
    """الحصول على عدد رسائل المستخدم الحقيقي في المجموعة"""
    try:
        result = await execute_query(
            """
            SELECT message_count 
            FROM user_message_count 
            WHERE user_id = ? AND chat_id = ?
            """,
            (user_id, chat_id),
            fetch_one=True
        )
        
        if result:
            return result.get('message_count', 0)
        
        return 0
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على عدد رسائل المستخدم {user_id} في المجموعة {chat_id}: {e}")
        return 0


async def increment_user_message_count(user_id: int, chat_id: int) -> bool:
    """زيادة عدد رسائل المستخدم في المجموعة"""
    try:
        from datetime import datetime
        current_time = datetime.now().isoformat()
        
        # محاولة التحديث أولاً
        result = await execute_query(
            """
            UPDATE user_message_count 
            SET message_count = message_count + 1, last_message_date = ?
            WHERE user_id = ? AND chat_id = ?
            """,
            (current_time, user_id, chat_id)
        )
        
        # إذا لم يتم التحديث (السجل غير موجود)، أنشئ سجل جديد
        if result == 0:
            await execute_query(
                """
                INSERT OR IGNORE INTO user_message_count 
                (user_id, chat_id, message_count, first_message_date, last_message_date)
                VALUES (?, ?, 1, ?, ?)
                """,
                (user_id, chat_id, current_time, current_time)
            )
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في زيادة عدد رسائل المستخدم {user_id} في المجموعة {chat_id}: {e}")
        return False


async def get_group_message_ranking(chat_id: int, limit: int = 10) -> list:
    """الحصول على ترتيب المستخدمين حسب عدد الرسائل في المجموعة"""
    try:
        result = await execute_query(
            """
            SELECT umc.user_id, umc.message_count, u.first_name, u.username
            FROM user_message_count umc
            LEFT JOIN users u ON umc.user_id = u.user_id
            WHERE umc.chat_id = ? AND umc.message_count > 0
            ORDER BY umc.message_count DESC
            LIMIT ?
            """,
            (chat_id, limit),
            fetch_all=True
        )
        
        return result if result else []
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على ترتيب الرسائل للمجموعة {chat_id}: {e}")
        return []


async def get_user_message_rank(user_id: int, chat_id: int) -> tuple:
    """الحصول على ترتيب المستخدم وعدد رسائله في المجموعة"""
    try:
        # الحصول على عدد رسائل المستخدم
        user_count = await get_user_message_count(user_id, chat_id)
        
        # الحصول على ترتيب المستخدم
        rank_result = await execute_query(
            """
            SELECT COUNT(*) + 1 as user_rank
            FROM user_message_count 
            WHERE chat_id = ? AND message_count > (
                SELECT COALESCE(message_count, 0)
                FROM user_message_count 
                WHERE user_id = ? AND chat_id = ?
            )
            """,
            (chat_id, user_id, chat_id),
            fetch_one=True
        )
        
        user_rank = rank_result.get('user_rank', 0) if rank_result else 0
        
        # إذا كان عدد الرسائل 0، الترتيب يكون 0 أيضاً
        if user_count == 0:
            user_rank = 0
            
        return user_count, user_rank
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على ترتيب المستخدم {user_id} في المجموعة {chat_id}: {e}")
        return 0, 0


async def get_all_group_members(group_id: int) -> list:
    """الحصول على جميع الأعضاء المسجلين في المجموعة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            cursor = await db.execute(
                """
                SELECT DISTINCT user_id FROM users 
                WHERE user_id IS NOT NULL
                AND user_id NOT IN (SELECT user_id FROM users WHERE is_banned = 1)
                ORDER BY updated_at DESC
                LIMIT 500
                """,
            )
            results = await cursor.fetchall()
            
            # استخراج معرفات المستخدمين من النتائج
            member_ids = [row[0] for row in results if row[0] is not None]
            
            logging.info(f"تم العثور على {len(member_ids)} عضو مسجل للمجموعة {group_id}")
            return member_ids
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على أعضاء المجموعة {group_id}: {e}")
        return []
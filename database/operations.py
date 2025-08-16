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
    """تحديث رصيد المستخدم"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                "UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?",
                (new_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد المستخدم {user_id}: {e}")
        return False


async def update_user_bank_balance(user_id: int, new_bank_balance: float) -> bool:
    """تحديث رصيد البنك للمستخدم"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                "UPDATE users SET bank_balance = ?, updated_at = ? WHERE user_id = ?",
                (new_bank_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد البنك للمستخدم {user_id}: {e}")
        return False


async def add_transaction(user_id: int, transaction_type: str, amount: float, 
                         description: str = "", from_user_id: int = None, 
                         to_user_id: int = None) -> bool:
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
            if fetch_one or fetch_all:
                db.row_factory = aiosqlite.Row
            
            async with db.execute(query, params) as cursor:
                if fetch_one:
                    result = await cursor.fetchone()
                    return dict(result) if result else None
                elif fetch_all:
                    results = await cursor.fetchall()
                    return [dict(row) for row in results]
                else:
                    await db.commit()
                    return cursor.rowcount
                    
    except Exception as e:
        logging.error(f"خطأ في تنفيذ الاستعلام: {e}")
        return None
"""
عمليات قاعدة البيانات
Database Operations
"""

import logging
from datetime import datetime, date
from typing import Optional, Dict, List, Any, Union
import aiosqlite
from contextlib import asynccontextmanager

from config.database import get_db_connection, execute_query, DB_PATH
from .models import User, create_user_from_telegram


async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """الحصول على بيانات المستخدم"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            
            if result:
                # النتيجة تأتي كقاموس مباشرة الآن
                return result
            return None
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على المستخدم {user_id}: {e}")
        return None


async def create_user(user_id: int, username: str = None, first_name: str = None) -> bool:
    """إنشاء مستخدم جديد"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO users (user_id, username, first_name, balance, bank_balance, created_at, updated_at, last_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, username, first_name, 1000, 0, datetime.now().isoformat(), 
                 datetime.now().isoformat(), datetime.now().isoformat())
            )
            await db.commit()
            
            logging.info(f"تم إنشاء مستخدم جديد: {user_id} - {username}")
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إنشاء المستخدم {user_id}: {e}")
        return False


async def get_or_create_user(user_id: int, username: str = None, first_name: str = None) -> Optional[Dict[str, Any]]:
    """الحصول على المستخدم أو إنشاؤه إذا لم يكن موجوداً"""
    try:
        # محاولة الحصول على المستخدم
        user = await get_user(user_id)
        
        if user:
            # تحديث آخر نشاط
            await update_user_activity(user_id)
            return user
        
        # إنشاء مستخدم جديد إذا لم يكن موجوداً
        if await create_user(user_id, username, first_name):
            return await get_user(user_id)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في get_or_create_user للمستخدم {user_id}: {e}")
        return None


async def update_user_balance(user_id: int, new_balance: int) -> bool:
    """تحديث رصيد المستخدم"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE users SET balance = ?, updated_at = ? WHERE user_id = ?",
                (new_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد المستخدم {user_id}: {e}")
        return False


async def update_user_bank_balance(user_id: int, new_bank_balance: int) -> bool:
    """تحديث رصيد البنك للمستخدم"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE users SET bank_balance = ?, updated_at = ? WHERE user_id = ?",
                (new_bank_balance, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث رصيد البنك للمستخدم {user_id}: {e}")
        return False


async def update_user_activity(user_id: int) -> bool:
    """تحديث آخر نشاط للمستخدم"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE users SET last_active = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث نشاط المستخدم {user_id}: {e}")
        return False


async def update_last_daily(user_id: int, date_str: str = None) -> bool:
    """تحديث تاريخ آخر مكافأة يومية"""
    try:
        if not date_str:
            date_str = date.today().isoformat()
        
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE users SET last_daily = ?, updated_at = ? WHERE user_id = ?",
                (date_str, datetime.now().isoformat(), user_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث آخر مكافأة يومية للمستخدم {user_id}: {e}")
        return False


async def add_transaction(from_user_id: Optional[int], to_user_id: Optional[int], 
                         transaction_type: str, amount: int, description: str = None) -> bool:
    """إضافة معاملة جديدة"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO transactions (from_user_id, to_user_id, transaction_type, amount, description, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (from_user_id, to_user_id, transaction_type, amount, description, datetime.now().isoformat())
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إضافة المعاملة: {e}")
        return False


async def get_user_transactions(user_id: int, limit: int = 10) -> List[Dict[str, Any]]:
    """الحصول على معاملات المستخدم"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                SELECT * FROM transactions 
                WHERE from_user_id = ? OR to_user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
                """,
                (user_id, user_id, limit)
            )
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على معاملات المستخدم {user_id}: {e}")
        return []


async def is_user_banned(user_id: int) -> bool:
    """التحقق من حظر المستخدم"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM banned_users WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result['count'] > 0 if result else False
            
    except Exception as e:
        logging.error(f"خطأ في التحقق من حظر المستخدم {user_id}: {e}")
        return False


async def ban_user(user_id: int, banned_by: int, reason: str = None) -> bool:
    """حظر مستخدم"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO banned_users (user_id, banned_by, banned_at, reason)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, banned_by, datetime.now().isoformat(), reason)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في حظر المستخدم {user_id}: {e}")
        return False


async def unban_user(user_id: int) -> bool:
    """إلغاء حظر مستخدم"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "DELETE FROM banned_users WHERE user_id = ?",
                (user_id,)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إلغاء حظر المستخدم {user_id}: {e}")
        return False


async def get_all_users(limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
    """الحصول على جميع المستخدمين"""
    try:
        async with get_db_connection() as db:
            query = "SELECT * FROM users ORDER BY created_at DESC"
            params = []
            
            if limit:
                query += " LIMIT ? OFFSET ?"
                params.extend([limit, offset])
            
            cursor = await db.execute(query, params)
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على جميع المستخدمين: {e}")
        return []


async def get_users_count() -> int:
    """الحصول على عدد المستخدمين"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute("SELECT COUNT(*) as count FROM users")
            result = await cursor.fetchone()
            return result['count'] if result else 0
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على عدد المستخدمين: {e}")
        return 0


async def get_active_users_count(days: int = 7) -> int:
    """الحصول على عدد المستخدمين النشطين"""
    try:
        cutoff_date = datetime.now() - datetime.timedelta(days=days)
        
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT COUNT(*) as count FROM users WHERE last_active >= ?",
                (cutoff_date.isoformat(),)
            )
            result = await cursor.fetchone()
            return result['count'] if result else 0
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على عدد المستخدمين النشطين: {e}")
        return 0


async def add_property(user_id: int, property_type: str, location: str, price: int, income_per_hour: int) -> Optional[int]:
    """إضافة عقار جديد"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO properties (user_id, property_type, location, price, income_per_hour, purchased_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, property_type, location, price, income_per_hour, datetime.now().isoformat())
            )
            await db.commit()
            return cursor.lastrowid
            
    except Exception as e:
        logging.error(f"خطأ في إضافة العقار: {e}")
        return None


async def get_user_properties(user_id: int) -> List[Dict[str, Any]]:
    """الحصول على عقارات المستخدم"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "SELECT * FROM properties WHERE user_id = ? ORDER BY purchased_at DESC",
                (user_id,)
            )
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على عقارات المستخدم {user_id}: {e}")
        return []


async def remove_property(property_id: int, user_id: int) -> bool:
    """حذف عقار"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                "DELETE FROM properties WHERE id = ? AND user_id = ?",
                (property_id, user_id)
            )
            await db.commit()
            return cursor.rowcount > 0
            
    except Exception as e:
        logging.error(f"خطأ في حذف العقار {property_id}: {e}")
        return False


async def add_investment(user_id: int, investment_type: str, amount: int, expected_return: float, maturity_date: datetime) -> Optional[int]:
    """إضافة استثمار جديد"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO investments (user_id, investment_type, amount, expected_return, maturity_date, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (user_id, investment_type, amount, expected_return, maturity_date.isoformat(), 'active', datetime.now().isoformat())
            )
            await db.commit()
            return cursor.lastrowid
            
    except Exception as e:
        logging.error(f"خطأ في إضافة الاستثمار: {e}")
        return None


async def get_user_investments(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    """الحصول على استثمارات المستخدم"""
    try:
        async with get_db_connection() as db:
            if status:
                cursor = await db.execute(
                    "SELECT * FROM investments WHERE user_id = ? AND status = ? ORDER BY created_at DESC",
                    (user_id, status)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM investments WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                )
            
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على استثمارات المستخدم {user_id}: {e}")
        return []


async def update_investment_status(investment_id: int, status: str) -> bool:
    """تحديث حالة الاستثمار"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE investments SET status = ? WHERE id = ?",
                (status, investment_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث حالة الاستثمار {investment_id}: {e}")
        return False


async def add_stock(user_id: int, symbol: str, quantity: int, purchase_price: float) -> Optional[int]:
    """إضافة سهم جديد"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO stocks (user_id, symbol, quantity, purchase_price, purchased_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, symbol, quantity, purchase_price, datetime.now().isoformat())
            )
            await db.commit()
            return cursor.lastrowid
            
    except Exception as e:
        logging.error(f"خطأ في إضافة السهم: {e}")
        return None


async def get_user_stocks(user_id: int, symbol: str = None) -> List[Dict[str, Any]]:
    """الحصول على أسهم المستخدم"""
    try:
        async with get_db_connection() as db:
            if symbol:
                cursor = await db.execute(
                    "SELECT * FROM stocks WHERE user_id = ? AND symbol = ? ORDER BY purchased_at DESC",
                    (user_id, symbol)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM stocks WHERE user_id = ? ORDER BY purchased_at DESC",
                    (user_id,)
                )
            
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على أسهم المستخدم {user_id}: {e}")
        return []


async def update_stock_quantity(user_id: int, symbol: str, new_quantity: int) -> bool:
    """تحديث كمية الأسهم"""
    try:
        async with get_db_connection() as db:
            if new_quantity <= 0:
                await db.execute(
                    "DELETE FROM stocks WHERE user_id = ? AND symbol = ?",
                    (user_id, symbol)
                )
            else:
                await db.execute(
                    "UPDATE stocks SET quantity = ? WHERE user_id = ? AND symbol = ?",
                    (new_quantity, user_id, symbol)
                )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث كمية الأسهم للمستخدم {user_id}: {e}")
        return False


async def add_farm_crop(user_id: int, crop_type: str, quantity: int, harvest_time: datetime) -> Optional[int]:
    """إضافة محصول جديد للمزرعة"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(
                """
                INSERT INTO farm (user_id, crop_type, quantity, planted_at, harvest_time, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, crop_type, quantity, datetime.now().isoformat(), harvest_time.isoformat(), 'growing')
            )
            await db.commit()
            return cursor.lastrowid
            
    except Exception as e:
        logging.error(f"خطأ في إضافة المحصول: {e}")
        return None


async def get_user_crops(user_id: int, status: str = None) -> List[Dict[str, Any]]:
    """الحصول على محاصيل المستخدم"""
    try:
        async with get_db_connection() as db:
            if status:
                cursor = await db.execute(
                    "SELECT * FROM farm WHERE user_id = ? AND status = ? ORDER BY planted_at DESC",
                    (user_id, status)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM farm WHERE user_id = ? ORDER BY planted_at DESC",
                    (user_id,)
                )
            
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على محاصيل المستخدم {user_id}: {e}")
        return []


async def update_crop_status(crop_id: int, status: str) -> bool:
    """تحديث حالة المحصول"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                "UPDATE farm SET status = ? WHERE id = ?",
                (status, crop_id)
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث حالة المحصول {crop_id}: {e}")
        return False


async def get_or_create_castle(user_id: int) -> Optional[Dict[str, Any]]:
    """الحصول على قلعة المستخدم أو إنشاؤها"""
    try:
        async with get_db_connection() as db:
            # محاولة الحصول على القلعة
            cursor = await db.execute(
                "SELECT * FROM castle WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            
            if result:
                return result
            
            # إنشاء قلعة جديدة
            await db.execute(
                """
                INSERT INTO castle (user_id, level, defense_points, attack_points, gold_production, last_upgrade)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, 1, 100, 50, 10, datetime.now().isoformat())
            )
            await db.commit()
            
            # إرجاع القلعة الجديدة
            cursor = await db.execute(
                "SELECT * FROM castle WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            return result if result else None
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على/إنشاء قلعة المستخدم {user_id}: {e}")
        return None


async def update_castle_stats(user_id: int, level: int = None, defense_points: int = None, 
                             attack_points: int = None, gold_production: int = None) -> bool:
    """تحديث إحصائيات القلعة"""
    try:
        updates = []
        params = []
        
        if level is not None:
            updates.append("level = ?")
            params.append(level)
        
        if defense_points is not None:
            updates.append("defense_points = ?")
            params.append(defense_points)
        
        if attack_points is not None:
            updates.append("attack_points = ?")
            params.append(attack_points)
        
        if gold_production is not None:
            updates.append("gold_production = ?")
            params.append(gold_production)
        
        if not updates:
            return False
        
        updates.append("last_upgrade = ?")
        params.append(datetime.now().isoformat())
        params.append(user_id)
        
        query = f"UPDATE castle SET {', '.join(updates)} WHERE user_id = ?"
        
        async with get_db_connection() as db:
            await db.execute(query, params)
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث إحصائيات قلعة المستخدم {user_id}: {e}")
        return False


async def add_stats_entry(user_id: int, action_type: str, action_data: str = None) -> bool:
    """إضافة إدخال إحصائيات"""
    try:
        async with get_db_connection() as db:
            await db.execute(
                """
                INSERT INTO stats (user_id, action_type, action_data, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, action_type, action_data, datetime.now().isoformat())
            )
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إضافة إحصائيات للمستخدم {user_id}: {e}")
        return False


async def get_user_stats(user_id: int, action_type: str = None, limit: int = 100) -> List[Dict[str, Any]]:
    """الحصول على إحصائيات المستخدم"""
    try:
        async with get_db_connection() as db:
            if action_type:
                cursor = await db.execute(
                    "SELECT * FROM stats WHERE user_id = ? AND action_type = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, action_type, limit)
                )
            else:
                cursor = await db.execute(
                    "SELECT * FROM stats WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
                    (user_id, limit)
                )
            
            results = await cursor.fetchall()
            return results if results else []
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات المستخدم {user_id}: {e}")
        return []


async def cleanup_old_data(days_old: int = 90) -> int:
    """تنظيف البيانات القديمة"""
    try:
        cutoff_date = datetime.now() - datetime.timedelta(days=days_old)
        total_deleted = 0
        
        async with get_db_connection() as db:
            # حذف المعاملات القديمة
            cursor = await db.execute(
                "DELETE FROM transactions WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            )
            total_deleted += cursor.rowcount
            
            # حذف الإحصائيات القديمة
            cursor = await db.execute(
                "DELETE FROM stats WHERE created_at < ?",
                (cutoff_date.isoformat(),)
            )
            total_deleted += cursor.rowcount
            
            # حذف المحاصيل المحصودة القديمة
            cursor = await db.execute(
                "DELETE FROM farm WHERE status = 'harvested' AND planted_at < ?",
                (cutoff_date.isoformat(),)
            )
            total_deleted += cursor.rowcount
            
            await db.commit()
            
            logging.info(f"تم حذف {total_deleted} سجل قديم")
            return total_deleted
            
    except Exception as e:
        logging.error(f"خطأ في تنظيف البيانات القديمة: {e}")
        return 0


async def backup_database(backup_path: str) -> bool:
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        import shutil
        shutil.copy2(DB_PATH, backup_path)
        logging.info(f"تم إنشاء نسخة احتياطية في: {backup_path}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        return False


async def get_database_size() -> Dict[str, int]:
    """الحصول على حجم قاعدة البيانات وعدد السجلات"""
    try:
        import os
        
        size_info = {
            'file_size_bytes': os.path.getsize(DB_PATH) if os.path.exists(DB_PATH) else 0,
            'users_count': 0,
            'transactions_count': 0,
            'properties_count': 0,
            'investments_count': 0,
            'stocks_count': 0,
            'farm_count': 0,
            'stats_count': 0
        }
        
        tables = [
            'users', 'transactions', 'properties', 
            'investments', 'stocks', 'farm', 'stats'
        ]
        
        async with get_db_connection() as db:
            for table in tables:
                try:
                    cursor = await db.execute(f"SELECT COUNT(*) as count FROM {table}")
                    result = await cursor.fetchone()
                    size_info[f'{table}_count'] = result['count'] if result else 0
                except:
                    pass
        
        return size_info
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على حجم قاعدة البيانات: {e}")
        return {}


async def optimize_database() -> bool:
    """تحسين قاعدة البيانات"""
    try:
        async with get_db_connection() as db:
            await db.execute("VACUUM")
            await db.execute("ANALYZE")
            await db.commit()
            
            logging.info("تم تحسين قاعدة البيانات بنجاح")
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحسين قاعدة البيانات: {e}")
        return False

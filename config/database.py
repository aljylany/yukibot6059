"""
إعدادات قاعدة البيانات
Database Configuration and Initialization
"""

import sqlite3
import logging
from typing import Optional
from contextlib import asynccontextmanager
import aiosqlite

# متغير عام لحفظ مسار قاعدة البيانات
DB_PATH = "bot_database.db"


async def init_database() -> None:
    """تهيئة قاعدة البيانات وإنشاء الجداول"""
    try:
        async with aiosqlite.connect(DB_PATH) as db:
            # جدول المستخدمين
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    balance INTEGER DEFAULT 1000,
                    bank_balance INTEGER DEFAULT 0,
                    last_daily DATE,
                    security_level INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول العقارات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    property_type TEXT NOT NULL,
                    location TEXT NOT NULL,
                    price INTEGER NOT NULL,
                    income_per_hour INTEGER DEFAULT 0,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول الاستثمارات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    investment_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    expected_return REAL NOT NULL,
                    maturity_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول الأسهم
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    symbol TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    purchase_price REAL NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول المزرعة
            await db.execute("""
                CREATE TABLE IF NOT EXISTS farm (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    crop_type TEXT NOT NULL,
                    quantity INTEGER NOT NULL,
                    planted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    harvest_time TIMESTAMP,
                    status TEXT DEFAULT 'growing',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول القلعة
            await db.execute("""
                CREATE TABLE IF NOT EXISTS castle (
                    user_id INTEGER PRIMARY KEY,
                    level INTEGER DEFAULT 1,
                    defense_points INTEGER DEFAULT 100,
                    attack_points INTEGER DEFAULT 50,
                    gold_production INTEGER DEFAULT 10,
                    last_upgrade TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول السجلات (للسرقة والمعاملات)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    transaction_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # جدول الإحصائيات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action_type TEXT NOT NULL,
                    action_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
            
            # جدول المحظورين
            await db.execute("""
                CREATE TABLE IF NOT EXISTS banned_users (
                    user_id INTEGER PRIMARY KEY,
                    banned_by INTEGER NOT NULL,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT,
                    FOREIGN KEY (banned_by) REFERENCES users (user_id)
                )
            """)
            
            await db.commit()
            logging.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
    except Exception as e:
        logging.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        raise


@asynccontextmanager
async def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات مع إدارة تلقائية للموارد"""
    conn = None
    try:
        conn = await aiosqlite.connect(DB_PATH)
        conn.row_factory = aiosqlite.Row  # لإرجاع النتائج كقاموس
        yield conn
    except Exception as e:
        logging.error(f"❌ خطأ في الاتصال بقاعدة البيانات: {e}")
        if conn:
            await conn.rollback()
        raise
    finally:
        if conn:
            await conn.close()


async def execute_query(query: str, params: tuple = (), fetch: bool = False):
    """تنفيذ استعلام قاعدة بيانات مع معالجة الأخطاء"""
    try:
        async with get_db_connection() as db:
            cursor = await db.execute(query, params)
            
            if fetch:
                if query.strip().upper().startswith('SELECT'):
                    if 'LIMIT 1' in query.upper() or query.count('?') == 1:
                        result = await cursor.fetchone()
                    else:
                        result = await cursor.fetchall()
                else:
                    result = cursor.rowcount
            else:
                result = cursor.rowcount
                
            await db.commit()
            return result
            
    except Exception as e:
        logging.error(f"❌ خطأ في تنفيذ الاستعلام: {e}")
        logging.error(f"الاستعلام: {query}")
        logging.error(f"المعاملات: {params}")
        raise

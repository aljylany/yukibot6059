"""
إعدادات وإدارة قاعدة البيانات
Database Configuration and Management
"""

import sqlite3
import aiosqlite
import logging
from typing import Optional
from .settings import DATABASE_URL

# إعداد نظام التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def init_database():
    """تهيئة قاعدة البيانات وإنشاء الجداول المطلوبة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # إنشاء جدول المستخدمين
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    last_name TEXT,
                    balance REAL DEFAULT 0,
                    bank_balance REAL DEFAULT 0,
                    total_earned REAL DEFAULT 0,
                    total_spent REAL DEFAULT 0,
                    level INTEGER DEFAULT 1,
                    xp INTEGER DEFAULT 0,
                    daily_bonus_last TIMESTAMP,
                    bank_type TEXT DEFAULT 'الأهلي',
                    security_level INTEGER DEFAULT 1,
                    successful_thefts INTEGER DEFAULT 0,
                    failed_thefts INTEGER DEFAULT 0,
                    times_stolen INTEGER DEFAULT 0,
                    is_banned BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء جدول المعاملات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS transactions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    transaction_type TEXT,
                    amount REAL,
                    description TEXT,
                    from_user_id INTEGER,
                    to_user_id INTEGER,
                    status TEXT DEFAULT 'completed',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (from_user_id) REFERENCES users (user_id),
                    FOREIGN KEY (to_user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول العقارات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_properties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    property_type TEXT,
                    quantity INTEGER DEFAULT 1,
                    purchase_price REAL,
                    income_per_hour REAL,
                    last_income_collected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول الأسهم
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_stocks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    stock_symbol TEXT,
                    quantity INTEGER,
                    purchase_price REAL,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول الاستثمارات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    investment_type TEXT,
                    amount REAL,
                    expected_return REAL,
                    start_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول المزارع
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_farms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    farm_type TEXT,
                    level INTEGER DEFAULT 1,
                    productivity REAL,
                    last_harvest TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    upgrade_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول القلاع
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_castles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    castle_level INTEGER DEFAULT 1,
                    defense_points INTEGER DEFAULT 100,
                    attack_points INTEGER DEFAULT 50,
                    gold_storage REAL DEFAULT 0,
                    last_collection TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    upgrade_cost REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول أسعار الأسهم التاريخية
            await db.execute('''
                CREATE TABLE IF NOT EXISTS stock_prices (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT,
                    price REAL,
                    change_percent REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء جدول سجل الأنشطة
            await db.execute('''
                CREATE TABLE IF NOT EXISTS activity_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    activity_type TEXT,
                    description TEXT,
                    amount REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول الإعدادات العامة
            await db.execute('''
                CREATE TABLE IF NOT EXISTS system_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # إنشاء جدول رتب المجموعة (نظام الإدارة)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS group_ranks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    rank_type TEXT,
                    promoted_by INTEGER,
                    promoted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, chat_id, rank_type)
                )
            ''')
            
            # إنشاء جدول المحظورين
            await db.execute('''
                CREATE TABLE IF NOT EXISTS banned_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    banned_by INTEGER,
                    ban_reason TEXT,
                    banned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, chat_id)
                )
            ''')
            
            # إنشاء جدول المكتومين
            await db.execute('''
                CREATE TABLE IF NOT EXISTS muted_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    muted_by INTEGER,
                    mute_reason TEXT,
                    muted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    until_date TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, chat_id)
                )
            ''')
            
            # إنشاء جدول التحذيرات
            await db.execute('''
                CREATE TABLE IF NOT EXISTS user_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    warned_by INTEGER,
                    warn_level TEXT,
                    warn_reason TEXT,
                    warned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول إعدادات المجموعة
            await db.execute('''
                CREATE TABLE IF NOT EXISTS group_settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    setting_key TEXT,
                    setting_value TEXT,
                    updated_by INTEGER,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, setting_key)
                )
            ''')
            
            # إنشاء جدول الكلمات المحظورة
            await db.execute('''
                CREATE TABLE IF NOT EXISTS forbidden_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    word TEXT,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(chat_id, word)
                )
            ''')
            
            # إنشاء جدول أعمال الإدارة
            await db.execute('''
                CREATE TABLE IF NOT EXISTS admin_actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    action_type TEXT,
                    target TEXT,
                    details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إنشاء جدول رتب التسلية
            await db.execute('''
                CREATE TABLE IF NOT EXISTS entertainment_ranks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    rank_type TEXT,
                    given_by INTEGER,
                    given_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    UNIQUE(user_id, chat_id, rank_type)
                )
            ''')
            
            # إنشاء جدول الزواج (للتسلية)
            await db.execute('''
                CREATE TABLE IF NOT EXISTS entertainment_marriages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user1_id INTEGER,
                    user2_id INTEGER,
                    chat_id INTEGER,
                    married_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user1_id) REFERENCES users (user_id),
                    FOREIGN KEY (user2_id) REFERENCES users (user_id),
                    UNIQUE(user1_id, chat_id),
                    UNIQUE(user2_id, chat_id)
                )
            ''')
            
            # إنشاء فهارس لتحسين الأداء
            await db.execute('CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON transactions(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_properties_user_id ON user_properties(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_stocks_user_id ON user_stocks(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_investments_user_id ON user_investments(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_activity_user_id ON activity_log(user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_group_ranks_chat_user ON group_ranks(chat_id, user_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_group_settings_chat ON group_settings(chat_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_banned_users_chat ON banned_users(chat_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_muted_users_chat ON muted_users(chat_id)')
            await db.execute('CREATE INDEX IF NOT EXISTS idx_entertainment_ranks_chat ON entertainment_ranks(chat_id)')
            
            await db.commit()
            logger.info("✅ تم تهيئة قاعدة البيانات بنجاح")
            
    except Exception as e:
        logger.error(f"❌ خطأ في تهيئة قاعدة البيانات: {e}")
        raise


async def get_database_connection():
    """الحصول على اتصال بقاعدة البيانات"""
    try:
        return await aiosqlite.connect(DATABASE_URL)
    except Exception as e:
        logger.error(f"خطأ في الاتصال بقاعدة البيانات: {e}")
        raise


async def execute_query(query: str, params: tuple = (), fetch_one: bool = False, fetch_all: bool = False):
    """تنفيذ استعلام قاعدة البيانات مع معالجة الأخطاء"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            async with db.execute(query, params) as cursor:
                if fetch_one:
                    result = await cursor.fetchone()
                    await db.commit()
                    return result
                elif fetch_all:
                    result = await cursor.fetchall()
                    await db.commit()
                    return result
                else:
                    await db.commit()
                    return cursor.rowcount
    except Exception as e:
        logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
        logger.error(f"الاستعلام: {query}")
        logger.error(f"المعاملات: {params}")
        raise


async def backup_database(backup_path: str):
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as source:
            async with aiosqlite.connect(backup_path) as backup:
                await source.backup(backup)
        logger.info(f"✅ تم إنشاء نسخة احتياطية في: {backup_path}")
    except Exception as e:
        logger.error(f"❌ خطأ في إنشاء النسخة الاحتياطية: {e}")
        raise


async def get_database_stats():
    """الحصول على إحصائيات قاعدة البيانات"""
    try:
        stats = {}
        
        # عدد المستخدمين
        async with aiosqlite.connect(DATABASE_URL) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                users_count = await cursor.fetchone()
                stats['total_users'] = users_count[0] if users_count else 0
            
            # عدد المعاملات
            async with db.execute("SELECT COUNT(*) FROM transactions") as cursor:
                transactions_count = await cursor.fetchone()
                stats['total_transactions'] = transactions_count[0] if transactions_count else 0
            
            # إجمالي الأموال في النظام
            async with db.execute("SELECT SUM(balance + bank_balance) FROM users") as cursor:
                total_money = await cursor.fetchone()
                stats['total_money'] = total_money[0] if total_money and total_money[0] else 0
            
            # المستخدمين النشطين (آخر 24 ساعة)
            async with db.execute("SELECT COUNT(*) FROM users WHERE updated_at > datetime('now', '-1 day')") as cursor:
                active_users = await cursor.fetchone()
                stats['active_users'] = active_users[0] if active_users else 0
        
        return stats
        
    except Exception as e:
        logger.error(f"خطأ في الحصول على إحصائيات قاعدة البيانات: {e}")
        return {}


async def cleanup_old_data(days_old: int = 30):
    """تنظيف البيانات القديمة"""
    try:
        # حذف المعاملات القديمة
        await execute_query(
            "DELETE FROM transactions WHERE created_at < datetime('now', '-{} days')".format(days_old)
        )
        
        # حذف أسعار الأسهم القديمة
        await execute_query(
            "DELETE FROM stock_prices WHERE timestamp < datetime('now', '-{} days')".format(days_old)
        )
        
        # حذف سجل الأنشطة القديمة
        await execute_query(
            "DELETE FROM activity_log WHERE created_at < datetime('now', '-{} days')".format(days_old)
        )
        
        logger.info(f"✅ تم تنظيف البيانات الأقدم من {days_old} يوم")
        
    except Exception as e:
        logger.error(f"❌ خطأ في تنظيف البيانات القديمة: {e}")
        raise
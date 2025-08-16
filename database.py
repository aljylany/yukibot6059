import sqlite3
import os
import shutil
from datetime import datetime

DB_PATH = 'yukibot.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # جدول المستخدمين
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        balance BIGINT DEFAULT 0,
        account_number TEXT,
        last_salary TIMESTAMP DEFAULT 0,
        last_robbery TIMESTAMP DEFAULT 0,
        last_luck TIMESTAMP DEFAULT 0,
        last_gamble TIMESTAMP DEFAULT 0,
        last_stock TIMESTAMP DEFAULT 0
    )''')
    
    # جدول الممتلكات
    c.execute('''CREATE TABLE IF NOT EXISTS properties (
        user_id INTEGER,
        property_name TEXT,
        quantity INTEGER,
        PRIMARY KEY (user_id, property_name),
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    
    # جدول الأسهم
    c.execute('''CREATE TABLE IF NOT EXISTS stocks (
        user_id INTEGER PRIMARY KEY,
        amount INTEGER DEFAULT 0,
        last_buy TIMESTAMP DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES users(user_id)
    )''')
    
    # جدول الحظر
    c.execute('''CREATE TABLE IF NOT EXISTS bans (
        user_id INTEGER PRIMARY KEY,
        reason TEXT,
        banned_by INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # جدول الرتب
    c.execute('''CREATE TABLE IF NOT EXISTS user_ranks (
        user_id INTEGER PRIMARY KEY,
        rank TEXT,
        expiry TEXT
    )''')
    
    # جدول المزارع
    c.execute('''CREATE TABLE IF NOT EXISTS farms (
        user_id INTEGER PRIMARY KEY,
        crops TEXT,
        last_planted REAL
    )''')
    
    # جدول القلاع
    c.execute('''CREATE TABLE IF NOT EXISTS castles (
        user_id INTEGER PRIMARY KEY,
        buildings TEXT,
        army_level INTEGER DEFAULT 1
    )''')
    
    # جدول المستويات (جديد)
    c.execute('''CREATE TABLE IF NOT EXISTS levels (
        user_id INTEGER PRIMARY KEY,
        xp INTEGER DEFAULT 0,
        current_level TEXT DEFAULT 'نجم 1',
        current_world TEXT DEFAULT 'عالم النجوم',
        last_xp_gain TIMESTAMP DEFAULT 0
    )''')
    
    conn.commit()
    conn.close()

def get_db():
    return sqlite3.connect(DB_PATH)

def format_number(num):
    return f"{num:,}".replace(",", ".")

def delete_user(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        # حذف المستخدم من جميع الجداول
        c.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM properties WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM stocks WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM bans WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM user_ranks WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM farms WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM castles WHERE user_id = ?", (user_id,))
        c.execute("DELETE FROM levels WHERE user_id = ?", (user_id,))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error deleting user: {e}")
        return False
    finally:
        conn.close()

def backup_db():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"backups/yukibot_{timestamp}.db"
    os.makedirs(os.path.dirname(backup_path), exist_ok=True)
    shutil.copy2(DB_PATH, backup_path)
    return backup_path
    # أضف في نهاية الملف
def get_last_robbery_time(user_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT last_robbery FROM users WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row and row[0]:
        return float(row[0])
    return 0.0  # قيمة افتراضية إذا لم تكن 
    

#!/usr/bin/env python3
"""
إعداد قاعدة البيانات - إنشاء الجداول المطلوبة
Database Setup - Create Required Tables
"""

import asyncio
import aiosqlite
import logging

async def setup_database():
    """إنشاء جداول قاعدة البيانات المطلوبة"""
    try:
        async with aiosqlite.connect("bot_database.db") as db:
            # إنشاء جدول الاستثمارات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS investments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    investment_type TEXT NOT NULL,
                    amount INTEGER NOT NULL,
                    expected_return REAL NOT NULL,
                    maturity_date TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    created_at TEXT NOT NULL,
                    withdrawn_at TEXT NULL
                )
            """)
            
            # إنشاء جدول المستويات
            await db.execute("""
                CREATE TABLE IF NOT EXISTS levels (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER UNIQUE NOT NULL,
                    xp INTEGER DEFAULT 0,
                    level_name TEXT DEFAULT 'نجم 1',
                    world_name TEXT DEFAULT 'عالم النجوم',
                    last_xp_gain REAL DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # إنشاء الفهارس
            await db.execute("CREATE INDEX IF NOT EXISTS idx_investments_user_id ON investments(user_id)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_investments_status ON investments(status)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_investments_maturity ON investments(maturity_date)")
            await db.execute("CREATE INDEX IF NOT EXISTS idx_levels_user_id ON levels(user_id)")
            
            await db.commit()
            print("✅ تم إنشاء جداول قاعدة البيانات بنجاح")
            
            # فحص الجداول المنشأة
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table'") as cursor:
                tables = await cursor.fetchall()
                print("📊 الجداول الموجودة:")
                for table in tables:
                    print(f"  - {table[0]}")
                    
    except Exception as e:
        print(f"❌ خطأ في إنشاء قاعدة البيانات: {e}")

if __name__ == "__main__":
    asyncio.run(setup_database())
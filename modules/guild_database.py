"""
قاعدة بيانات لعبة النقابة
Guild Game Database Operations
"""

import logging
import sqlite3
import aiosqlite
from datetime import datetime
from typing import Optional, Dict, Any, List
from config.database import DATABASE_URL

async def init_guild_database():
    """تهيئة جداول قاعدة بيانات النقابة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # جدول لاعبي النقابة
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_players (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    name TEXT NOT NULL,
                    guild TEXT NOT NULL,
                    gender TEXT NOT NULL,
                    character_class TEXT NOT NULL,
                    advanced_class TEXT DEFAULT 'غير متاح',
                    level INTEGER DEFAULT 1,
                    power INTEGER DEFAULT 100,
                    experience INTEGER DEFAULT 0,
                    money INTEGER DEFAULT 5000,
                    weapon TEXT,
                    badge TEXT,
                    title TEXT,
                    potion TEXT,
                    ring TEXT,
                    animal TEXT,
                    personal_code TEXT UNIQUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # إضافة عمود المال إذا لم يكن موجوداً (للترقية)
            try:
                await db.execute("ALTER TABLE guild_players ADD COLUMN money INTEGER DEFAULT 5000")
            except:
                pass  # العمود موجود بالفعل
            
            # جدول المهام النشطة
            await db.execute("""
                CREATE TABLE IF NOT EXISTS active_guild_missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    mission_id TEXT NOT NULL,
                    mission_name TEXT NOT NULL,
                    mission_type TEXT NOT NULL,
                    duration_minutes INTEGER NOT NULL,
                    experience_reward INTEGER NOT NULL,
                    money_reward INTEGER NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    completed BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES guild_players (user_id)
                )
            """)
            
            # جدول إحصائيات النقابة
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_missions_completed INTEGER DEFAULT 0,
                    total_experience_gained INTEGER DEFAULT 0,
                    total_money_earned INTEGER DEFAULT 0,
                    favorite_mission_type TEXT,
                    longest_mission_duration INTEGER DEFAULT 0,
                    items_purchased INTEGER DEFAULT 0,
                    level_ups INTEGER DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES guild_players (user_id)
                )
            """)
            
            # جدول مخزون العناصر
            await db.execute("""
                CREATE TABLE IF NOT EXISTS guild_inventory (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    item_type TEXT NOT NULL,
                    item_id TEXT NOT NULL,
                    item_name TEXT NOT NULL,
                    equipped BOOLEAN DEFAULT FALSE,
                    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES guild_players (user_id)
                )
            """)
            
            await db.commit()
            logging.info("✅ تم تهيئة قاعدة بيانات النقابة بنجاح")
            
    except Exception as e:
        logging.error(f"❌ خطأ في تهيئة قاعدة بيانات النقابة: {e}")

async def save_guild_player(player_data: Dict[str, Any]) -> bool:
    """حفظ بيانات لاعب النقابة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute("""
                INSERT OR REPLACE INTO guild_players (
                    user_id, username, name, guild, gender, character_class,
                    advanced_class, level, power, experience, money, weapon, badge,
                    title, potion, ring, animal, personal_code, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                player_data['user_id'],
                player_data['username'],
                player_data['name'],
                player_data['guild'],
                player_data['gender'],
                player_data['character_class'],
                player_data['advanced_class'],
                player_data['level'],
                player_data['power'],
                player_data['experience'],
                player_data.get('money', 5000),  # قيمة افتراضية للمال
                player_data['weapon'],
                player_data['badge'],
                player_data['title'],
                player_data['potion'],
                player_data['ring'],
                player_data['animal'],
                player_data['personal_code'],
                datetime.now().isoformat()
            ))
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في حفظ لاعب النقابة: {e}")
        return False

async def load_guild_player(user_id: int) -> Optional[Dict[str, Any]]:
    """تحميل بيانات لاعب النقابة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM guild_players WHERE user_id = ?",
                (user_id,)
            )
            result = await cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
    except Exception as e:
        logging.error(f"خطأ في تحميل لاعب النقابة: {e}")
        return None

async def save_active_mission(mission_data: Dict[str, Any]) -> bool:
    """حفظ مهمة نشطة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute("""
                INSERT INTO active_guild_missions (
                    user_id, mission_id, mission_name, mission_type,
                    duration_minutes, experience_reward, money_reward, start_time
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                mission_data['user_id'],
                mission_data['mission_id'],
                mission_data['mission_name'],
                mission_data['mission_type'],
                mission_data['duration_minutes'],
                mission_data['experience_reward'],
                mission_data['money_reward'],
                mission_data['start_time'].isoformat()
            ))
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في حفظ المهمة النشطة: {e}")
        return False

async def complete_mission(user_id: int, mission_id: str) -> bool:
    """إنهاء مهمة وتحديث الإحصائيات"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute("""
                UPDATE active_guild_missions 
                SET completed = TRUE 
                WHERE user_id = ? AND mission_id = ? AND completed = FALSE
            """, (user_id, mission_id))
            
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إنهاء المهمة: {e}")
        return False

async def get_active_mission(user_id: int) -> Optional[Dict[str, Any]]:
    """الحصول على المهمة النشطة للاعب"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM active_guild_missions 
                WHERE user_id = ? AND completed = FALSE 
                ORDER BY start_time DESC LIMIT 1
            """, (user_id,))
            result = await cursor.fetchone()
            
            if result:
                return dict(result)
            return None
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على المهمة النشطة: {e}")
        return None

async def update_guild_stats(user_id: int, stat_type: str, value: int) -> bool:
    """تحديث إحصائيات النقابة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # إنشاء سجل إحصائيات إذا لم يكن موجود
            await db.execute("""
                INSERT OR IGNORE INTO guild_stats (user_id) VALUES (?)
            """, (user_id,))
            
            # تحديث الإحصائية المطلوبة
            if stat_type == "missions_completed":
                await db.execute("""
                    UPDATE guild_stats 
                    SET total_missions_completed = total_missions_completed + ?
                    WHERE user_id = ?
                """, (value, user_id))
            elif stat_type == "experience_gained":
                await db.execute("""
                    UPDATE guild_stats 
                    SET total_experience_gained = total_experience_gained + ?
                    WHERE user_id = ?
                """, (value, user_id))
            elif stat_type == "money_earned":
                await db.execute("""
                    UPDATE guild_stats 
                    SET total_money_earned = total_money_earned + ?
                    WHERE user_id = ?
                """, (value, user_id))
            elif stat_type == "level_ups":
                await db.execute("""
                    UPDATE guild_stats 
                    SET level_ups = level_ups + ?
                    WHERE user_id = ?
                """, (value, user_id))
            
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تحديث إحصائيات النقابة: {e}")
        return False

async def add_inventory_item(user_id: int, item_type: str, item_id: str, item_name: str) -> bool:
    """إضافة عنصر لمخزون اللاعب"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute("""
                INSERT INTO guild_inventory (user_id, item_type, item_id, item_name)
                VALUES (?, ?, ?, ?)
            """, (user_id, item_type, item_id, item_name))
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في إضافة عنصر للمخزون: {e}")
        return False

async def get_player_inventory(user_id: int) -> List[Dict[str, Any]]:
    """الحصول على مخزون اللاعب"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM guild_inventory WHERE user_id = ?
                ORDER BY purchase_date DESC
            """, (user_id,))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على المخزون: {e}")
        return []

async def equip_item(user_id: int, item_id: str, item_type: str) -> bool:
    """تجهيز عنصر"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            # إلغاء تجهيز العناصر الأخرى من نفس النوع
            await db.execute("""
                UPDATE guild_inventory 
                SET equipped = FALSE 
                WHERE user_id = ? AND item_type = ?
            """, (user_id, item_type))
            
            # تجهيز العنصر الجديد
            await db.execute("""
                UPDATE guild_inventory 
                SET equipped = TRUE 
                WHERE user_id = ? AND item_id = ?
            """, (user_id, item_id))
            
            await db.commit()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في تجهيز العنصر: {e}")
        return False

async def get_guild_leaderboard(limit: int = 10) -> List[Dict[str, Any]]:
    """الحصول على ترتيب النقابة"""
    try:
        async with aiosqlite.connect(DATABASE_URL) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT p.name, p.level, p.power, p.experience, p.guild,
                       COALESCE(s.total_missions_completed, 0) as missions,
                       COALESCE(s.total_experience_gained, 0) as total_exp
                FROM guild_players p
                LEFT JOIN guild_stats s ON p.user_id = s.user_id
                ORDER BY p.level DESC, p.experience DESC, p.power DESC
                LIMIT ?
            """, (limit,))
            results = await cursor.fetchall()
            
            return [dict(row) for row in results]
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على ترتيب النقابة: {e}")
        return []

# تصدير الدوال
__all__ = [
    'init_guild_database',
    'save_guild_player',
    'load_guild_player',
    'save_active_mission',
    'complete_mission',
    'get_active_mission',
    'update_guild_stats',
    'add_inventory_item',
    'get_player_inventory',
    'equip_item',
    'get_guild_leaderboard'
]
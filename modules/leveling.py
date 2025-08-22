import sqlite3
import time
import json
import logging
from database.operations import execute_query
from utils.helpers import format_number
import sys
sys.path.append('.')
from config import LEVELS

class LevelingSystem:
    def __init__(self):
        self.levels = LEVELS

    def get_world(self, world_name):
        for world in self.levels:
            if world["name"] == world_name:
                return world
        return None

    async def add_xp(self, user_id, action_type="message"):
        try:
            # جلب بيانات المستوى الحالي
            level_data = await execute_query(
                "SELECT * FROM levels WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            if not level_data:
                # إنشاء سجل جديد
                await execute_query(
                    "INSERT INTO levels (user_id, xp, level_name, world_name, last_xp_gain) VALUES (?, 0, 'نجم 1', 'عالم النجوم', ?)",
                    (user_id, time.time())
                )
                current_xp = 0
                current_world = "عالم النجوم"
                current_level = "نجم 1"
            else:
                if isinstance(level_data, dict):
                    current_xp = level_data.get('xp', 0)
                    current_world = level_data.get('world_name', "عالم النجوم")
                    current_level = level_data.get('level_name', "نجم 1")
                else:
                    current_xp = 0
                    current_world = "عالم النجوم"
                    current_level = "نجم 1"
            
            # الحصول على العالم الحالي
            world = self.get_world(current_world)
            if not world:
                return False, "العالم غير موجود"
            
            # حساب XP الممنوحة
            xp_gain = world["xp_per_action"]
            
            # تحديث الـ XP
            new_xp = current_xp + xp_gain
            await execute_query(
                "UPDATE levels SET xp = ?, last_xp_gain = ? WHERE user_id = ?",
                (new_xp, time.time(), user_id)
            )
            
            # التحقق من ترقية المستوى
            upgrade_result = await self.check_level_up(user_id, new_xp, current_world, current_level)
            
            return True, f"✨ +{xp_gain} XP"
        except Exception as e:
            logging.error(f"خطأ في إضافة XP: {e}")
            return False, f"حدث خطأ: {str(e)}"

    async def check_level_up(self, user_id, current_xp, current_world, current_level):
        try:
            world = self.get_world(current_world)
            if not world:
                return False, "العالم غير موجود"
            
            # الحصول على العالم التالي
            next_world_index = next((i for i, w in enumerate(self.levels) if w["name"] == current_world), -1) + 1
            next_world = self.levels[next_world_index] if next_world_index < len(self.levels) else None
            
            # التحقق إذا كان يمكن الترقية لعالم جديد
            if next_world and current_xp >= next_world["xp_required"]:
                # ترقية لعالم جديد
                new_world_name = next_world["name"]
                new_level_name = next_world["levels"][0]["name"]
                
                await execute_query(
                    "UPDATE levels SET world_name = ?, level_name = ? WHERE user_id = ?",
                    (new_world_name, new_level_name, user_id)
                )
                
                return True, f"🎉 ترقية للعالم الجديد: {new_world_name}!"
            
            # التحقق من ترقية داخل نفس العالم
            current_level_index = next((i for i, level in enumerate(world["levels"]) if level["name"] == current_level), -1)
            if current_level_index >= 0 and current_level_index < len(world["levels"]) - 1:
                next_level = world["levels"][current_level_index + 1]
                
                if current_xp >= next_level["xp_required"]:
                    # ترقية لمستوى جديد في نفس العالم
                    await execute_query(
                        "UPDATE levels SET level_name = ? WHERE user_id = ?",
                        (next_level["name"], user_id)
                    )
                    
                    return True, f"🌟 ترقية لمستوى جديد: {next_level['name']}!"
            
            return False, "لا توجد ترقية"
            
        except Exception as e:
            logging.error(f"خطأ في فحص ترقية المستوى: {e}")
            return False, f"حدث خطأ: {str(e)}"
    
    async def get_user_level_info(self, user_id):
        """الحصول على معلومات مستوى المستخدم"""
        try:
            level_data = await execute_query(
                "SELECT * FROM levels WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            if not level_data:
                return {
                    'xp': 0,
                    'level_name': 'نجم 1',
                    'world_name': 'عالم النجوم',
                    'progress': 0
                }
            
            if isinstance(level_data, dict):
                return {
                    'xp': level_data.get('xp', 0),
                    'level_name': level_data.get('level_name', 'نجم 1'),
                    'world_name': level_data.get('world_name', 'عالم النجوم'),
                    'progress': 0  # يمكن حساب التقدم لاحقاً
                }
            else:
                return {
                    'xp': 0,
                    'level_name': 'نجم 1',
                    'world_name': 'عالم النجوم',
                    'progress': 0
                }
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على معلومات المستوى: {e}")
            return None


# إنشاء نسخة عامة من نظام التطوير
leveling_system = LevelingSystem()
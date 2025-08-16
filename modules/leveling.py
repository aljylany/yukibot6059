import sqlite3
import time
import json
from database import get_db, format_number
from config import LEVELS

class LevelingSystem:
    def __init__(self):
        self.levels = LEVELS

    def get_world(self, world_name):
        for world in self.levels:
            if world["name"] == world_name:
                return world
        return None

    def add_xp(self, user_id, action_type="message"):
        conn = get_db()
        c = conn.cursor()
        
        try:
            # جلب بيانات المستوى الحالي
            c.execute("SELECT * FROM levels WHERE user_id = ?", (user_id,))
            level_data = c.fetchone()
            
            if not level_data:
                # إنشاء سجل جديد
                c.execute("INSERT INTO levels (user_id) VALUES (?)", (user_id,))
                conn.commit()
                current_xp = 0
                current_world = "عالم النجوم"
                current_level = "نجم 1"
            else:
                current_xp = level_data[1] or 0
                current_world = level_data[3] or "عالم النجوم"
                current_level = level_data[2] or "نجم 1"
            
            # الحصول على العالم الحالي
            world = self.get_world(current_world)
            if not world:
                return False, "العالم غير موجود"
            
            # حساب XP الممنوحة
            xp_gain = world["xp_per_action"]
            
            # تحديث الـ XP
            new_xp = current_xp + xp_gain
            c.execute("UPDATE levels SET xp = ?, last_xp_gain = ? WHERE user_id = ?", 
                     (new_xp, time.time(), user_id))
            
            # التحقق من ترقية المستوى
            upgrade_result = self.check_level_up(user_id, new_xp, current_world, current_level)
            
            conn.commit()
            return True, f"✨ +{xp_gain} XP"
        except Exception as e:
            return False, f"حدث خطأ: {str(e)}"
        finally:
            conn.close()

    def check_level_up(self, user_id, current_xp, current_world, current_level):
        conn = get_db()
        c = conn.cursor()
        
        try:
            world = self.get_world(current_world)
            if not world:
                return False, "العالم غير موجود"
            
            # الحصول على العالم التالي
            next_world_index = next((i for i, w in enumerate(self.levels) if w["name"] == current_world), -1) + 1
            next_world = self.levels[next_world_index] if next_world_index < len(self.levels) else None
            
            # التحقق إذا كان يمكن الترقية لعالم جديد
            if next_world and current_xp >= next_world["xp_required"]:
                new_world = next_world["name"]
                new_level = next_world.get("sub_levels", [])[0] if "sub_levels" in next_world else new_world
                c.execute("UPDATE levels SET current_world = ?, current_level = ? WHERE user_id = ?", 
                         (new_world, new_level, user_id))
                return True, f"🎉 تطورت إلى {new_world}!"
            
            # الترقية داخل العالم الحالي
            if "sub_levels" in world:
                sub_levels = world["sub_levels"]
                current_index = sub_levels.index(current_level)
                if current_index < len(sub_levels) - 1:
                    new_level = sub_levels[current_index + 1]
                    c.execute("UPDATE levels SET current_level = ? WHERE user_id = ?", 
                             (new_level, user_id))
                    return True, f"📈 تقدمت إلى {new_level}!"
            
            elif "stages" in world:
                # البحث عن المرحلة الحالية
                for stage, levels_list in world["stages"].items():
                    if current_level in levels_list:
                        current_index = levels_list.index(current_level)
                        if current_index < len(levels_list) - 1:
                            new_level = levels_list[current_index + 1]
                            c.execute("UPDATE levels SET current_level = ? WHERE user_id = ?", 
                                     (new_level, user_id))
                            return True, f"📈 تقدمت إلى {new_level} في {stage}!"
                        else:
                            # الانتقال لمرحلة جديدة
                            next_stage_index = list(world["stages"].keys()).index(stage) + 1
                            if next_stage_index < len(world["stages"]):
                                next_stage = list(world["stages"].keys())[next_stage_index]
                                new_level = world["stages"][next_stage][0]
                                c.execute("UPDATE levels SET current_level = ? WHERE user_id = ?", 
                                         (new_level, user_id))
                                return True, f"🚀 تطورت إلى مرحلة {next_stage}!"
            
            return False, "لا يوجد ترقية متاحة"
        except Exception as e:
            return False, f"حدث خطأ: {str(e)}"
        finally:
            conn.close()

    def get_user_level(self, user_id):
        conn = get_db()
        c = conn.cursor()
        try:
            c.execute("SELECT * FROM levels WHERE user_id = ?", (user_id,))
            level_data = c.fetchone()
            
            if not level_data:
                return {
                    "world": "عالم النجوم",
                    "level": "نجم 1",
                    "xp": 0,
                    "next_xp": 100,
                    "world_icon": "⭐",
                    "desc": "البداية الحقيقية لمسار القوة",
                    "abilities": ["هالة الطاقة الأساسية", "ضربات محسنة", "تحمل أفضل"]
                }
            
            xp = level_data[1]
            current_level = level_data[2]
            current_world = level_data[3]
            
            world = self.get_world(current_world)
            next_world_index = next((i for i, w in enumerate(self.levels) if w["name"] == current_world), -1) + 1
            next_world = self.levels[next_world_index] if next_world_index < len(self.levels) else None
            
            return {
                "world": current_world,
                "level": current_level,
                "xp": xp,
                "next_xp": next_world["xp_required"] if next_world else None,
                "world_icon": world["icon"] if world else "⭐",
                "desc": world["desc"] if world else "",
                "abilities": world["abilities_unlocked"] if world else []
            }
        except:
            return None
        finally:
            conn.close()

    def get_level_progress(self, user_id):
        user_level = self.get_user_level(user_id)
        if not user_level:
            return "لا توجد بيانات"
        
        world = self.get_world(user_level["world"])
        if not world:
            return "عالم غير معروف"
        
        progress = ""
        
        if "sub_levels" in world:
            sub_levels = world["sub_levels"]
            current_index = sub_levels.index(user_level["level"]) if user_level["level"] in sub_levels else 0
            
            for i, level in enumerate(sub_levels):
                if i == current_index:
                    progress += f"**[{level}]** → "
                else:
                    progress += f"{level} → "
            
            progress = progress.rstrip(" → ")
            
        elif "stages" in world:
            for stage, levels_list in world["stages"].items():
                stage_text = f"\n\n**{stage}:**\n"
                for level in levels_list:
                    if level == user_level["level"]:
                        stage_text += f"**[{level}]** → "
                    else:
                        stage_text += f"{level} → "
                progress += stage_text.rstrip(" → ")
        
        else:
            progress = f"{user_level['world']} - {user_level['level']}"
        
        return progress

# إنشاء كائن النظام
leveling_system = LevelingSystem()
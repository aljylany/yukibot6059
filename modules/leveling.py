import sqlite3
import time
import json
import logging
from database.operations import execute_query
from utils.helpers import format_number
import sys
sys.path.append('.')

# استيراد إعدادات المستويات مع معالجة أخطاء الاستيراد
try:
    from config.settings import LEVELS
    logging.info(f"✅ تم تحميل LEVELS من config.settings: {len(LEVELS) if LEVELS else 0} عوالم")
except ImportError:
    try:
        from config import LEVELS
        logging.info(f"✅ تم تحميل LEVELS من config: {len(LEVELS) if LEVELS else 0} عوالم")
    except ImportError:
        logging.error("❌ فشل في تحميل LEVELS - استخدام البيانات الاحتياطية")
        LEVELS = [
            {
                "name": "عالم النجوم",
                "icon": "⭐",
                "sub_levels": ["نجم 1", "نجم 2", "نجم 3", "نجم 4", "نجم 5", "نجم 6", "نجم 7", "نجم 8", "نجم 9"],
                "xp_required": 0,
                "xp_per_action": 10,
                "abilities_unlocked": ["هالة الطاقة الأساسية", "ضربات محسنة", "تحمل أفضل"]
            }
        ]

class LevelingSystem:
    def __init__(self):
        self.levels = LEVELS
        logging.info(f"🎮 تم تهيئة نظام المستويات مع {len(self.levels)} عوالم")

    def get_world(self, world_name):
        # إضافة logging للتشخيص
        logging.info(f"البحث عن العالم: '{world_name}'")
        logging.info(f"العوالم المتاحة: {[w['name'] for w in self.levels]}")
        
        for world in self.levels:
            if world["name"] == world_name:
                logging.info(f"تم العثور على العالم: {world['name']}")
                return world
        
        logging.warning(f"لم يتم العثور على العالم: '{world_name}'")
        # إرجاع العالم الأول كحل احتياطي
        if self.levels:
            logging.info(f"استخدام العالم الاحتياطي: {self.levels[0]['name']}")
            return self.levels[0]
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
                # معالجة أفضل للبيانات
                try:
                    if hasattr(level_data, 'keys'):  # Row object
                        current_xp = level_data['xp'] if 'xp' in level_data.keys() else 0
                        current_world = level_data['world_name'] if 'world_name' in level_data.keys() else "عالم النجوم"
                        current_level = level_data['level_name'] if 'level_name' in level_data.keys() else "نجم 1"
                    elif isinstance(level_data, dict):
                        current_xp = level_data.get('xp', 0)
                        current_world = level_data.get('world_name', "عالم النجوم")
                        current_level = level_data.get('level_name', "نجم 1")
                    else:
                        current_xp = 0
                        current_world = "عالم النجوم"
                        current_level = "نجم 1"
                except Exception as data_error:
                    logging.error(f"خطأ في قراءة بيانات المستوى: {data_error}")
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
                # استخدام المفتاح الصحيح للمستويات
                if "sub_levels" in next_world:
                    new_level_name = next_world["sub_levels"][0]
                elif "stages" in next_world:
                    first_stage_name = list(next_world["stages"].keys())[0]
                    new_level_name = f"{first_stage_name} - {next_world['stages'][first_stage_name][0]}"
                else:
                    new_level_name = "مستوى 1"
                
                await execute_query(
                    "UPDATE levels SET world_name = ?, level_name = ? WHERE user_id = ?",
                    (new_world_name, new_level_name, user_id)
                )
                
                return True, f"🎉 ترقية للعالم الجديد: {new_world_name}!"
            
            # التحقق من ترقية داخل نفس العالم
            # معالجة المستويات الفرعية
            if "sub_levels" in world:
                try:
                    current_level_index = world["sub_levels"].index(current_level)
                    if current_level_index < len(world["sub_levels"]) - 1:
                        next_level_name = world["sub_levels"][current_level_index + 1]
                        # حساب XP المطلوب للمستوى التالي (مبسط)
                        required_xp = (current_level_index + 2) * 200
                        
                        if current_xp >= required_xp:
                            await execute_query(
                                "UPDATE levels SET level_name = ? WHERE user_id = ?",
                                (next_level_name, user_id)
                            )
                            return True, f"🌟 ترقية لمستوى جديد: {next_level_name}!"
                except ValueError:
                    pass
            
            # معالجة العوالم ذات المراحل
            elif "stages" in world:
                # تنفيذ منطق المراحل لاحقاً
                pass
            
            return False, "لا توجد ترقية"
            
        except Exception as e:
            logging.error(f"خطأ في فحص ترقية المستوى: {e}")
            logging.error(f"تفاصيل الخطأ - current_world: {current_world}, current_level: {current_level}, current_xp: {current_xp}")
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
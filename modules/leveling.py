import sqlite3
import time
import json
import logging
from database.operations import execute_query
from utils.helpers import format_number
import sys
import os
sys.path.append('.')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# استيراد LEVELS من ملف config.py مباشرة
import importlib.util
import os

try:
    # محاولة استيراد LEVELS من config.py مباشرة
    config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'config.py')
    spec = importlib.util.spec_from_file_location("config_module", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    LEVELS = config_module.LEVELS
    logging.info(f"✅ تم استيراد LEVELS من config.py: {len(LEVELS)} عوالم")
except Exception as e:
    logging.error(f"خطأ في استيراد LEVELS من config.py: {e}")
    # نسخة احتياطية أساسية
    LEVELS = [
        {
            "name": "عالم النجوم",
            "icon": "⭐",
            "desc": "البداية الحقيقية لمسار القوة.",
            "sub_levels": ["نجم 1", "نجم 2", "نجم 3", "نجم 4", "نجم 5", "نجم 6", "نجم 7", "نجم 8", "نجم 9"],
            "xp_required": 0,
            "xp_per_action": 15,
            "abilities_unlocked": ["هالة الطاقة الأساسية", "ضربات محسنة", "تحمل أفضل"]
        }
    ]
    logging.warning("تم استخدام LEVELS احتياطي مبسط")

# تم إزالة إعدادات LEVELS المكررة - يتم استيرادها الآن من config.py

logging.info(f"✅ تم تحميل إعدادات المستويات: {len(LEVELS)} عوالم")

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
            # التأكد من وجود المستخدم أو إنشاء سجل جديد
            await self.ensure_user_exists(user_id)
            
            # جلب بيانات المستوى الحالي لحساب العالم
            level_data = await execute_query(
                "SELECT world_name, level_name, xp FROM levels WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            if not level_data:
                logging.warning(f"لم يتم العثور على بيانات المستوى للمستخدم {user_id} بعد التأكد من وجوده")
                return False, "خطأ في البيانات"
            
            # معالجة آمنة للبيانات
            if isinstance(level_data, dict):
                current_world = level_data.get('world_name', "عالم النجوم")
                current_level = level_data.get('level_name', "نجم 1")
                current_xp = level_data.get('xp', 0)
            else:
                current_world = "عالم النجوم"
                current_level = "نجم 1"
                current_xp = 0
            
            # تصحيح القيم إذا كانت فارغة أو None
            current_world = current_world or "عالم النجوم"
            current_level = current_level or "نجم 1"
            current_xp = max(0, current_xp or 0)
            
            # الحصول على العالم الحالي وحساب XP
            world = self.get_world(current_world)
            if not world:
                logging.error(f"عالم غير معروف: {current_world} للمستخدم {user_id}")
                # تصحيح البيانات
                await self.repair_user_data(user_id)
                world = self.get_world("عالم النجوم")
                if not world:
                    return False, "خطأ في إعدادات النظام"
            
            xp_gain = world["xp_per_action"]
            
            # تحديث XP بطريقة atomic وآمنة
            result = await execute_query(
                "UPDATE levels SET xp = xp + ?, last_xp_gain = ? WHERE user_id = ? AND xp >= 0",
                (xp_gain, time.time(), user_id)
            )
            
            # جلب XP المحدث
            updated_data = await execute_query(
                "SELECT xp FROM levels WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            if updated_data and isinstance(updated_data, dict):
                new_xp = updated_data.get('xp', current_xp + xp_gain)
            else:
                new_xp = current_xp + xp_gain
                # التحقق من ترقية المستوى
                upgrade_result = await self.check_level_up(user_id, new_xp, current_world, current_level)
                if upgrade_result[0]:  # إذا تم ترقية
                    return True, f"✨ +{xp_gain} XP | {upgrade_result[1]}"
                else:
                    return True, f"✨ +{xp_gain} XP"
            
            return False, "فشل في تحديث XP"
            
        except Exception as e:
            logging.error(f"خطأ في إضافة XP للمستخدم {user_id}: {e}")
            return False, f"حدث خطأ: {str(e)[:50]}"  # تقليم رسالة الخطأ
    
    async def ensure_user_exists(self, user_id):
        """التأكد من وجود المستخدم في قاعدة البيانات أو إنشاؤه"""
        try:
            # فحص وجود المستخدم
            existing = await execute_query(
                "SELECT user_id FROM levels WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            
            if not existing:
                # إنشاء سجل جديد بقيم افتراضية صحيحة
                await execute_query(
                    "INSERT OR IGNORE INTO levels (user_id, xp, level_name, world_name, last_xp_gain) VALUES (?, ?, ?, ?, ?)",
                    (user_id, 0, "نجم 1", "عالم النجوم", time.time())
                )
                logging.info(f"تم إنشاء سجل جديد للمستخدم {user_id}")
            
        except Exception as e:
            logging.error(f"خطأ في التأكد من وجود المستخدم {user_id}: {e}")
            raise
    
    async def repair_user_data(self, user_id):
        """إصلاح بيانات المستخدم في حالة وجود أخطاء"""
        try:
            await execute_query(
                "UPDATE levels SET world_name = ?, level_name = ? WHERE user_id = ? AND (world_name IS NULL OR world_name = '' OR level_name IS NULL OR level_name = '')",
                ("عالم النجوم", "نجم 1", user_id)
            )
            logging.info(f"تم إصلاح بيانات المستخدم {user_id}")
        except Exception as e:
            logging.error(f"خطأ في إصلاح بيانات المستخدم {user_id}: {e}")

    def parse_stage_level(self, level_name):
        """فصل المرحلة عن المستوى الفرعي"""
        if " - " in level_name:
            stage, sub_level = level_name.split(" - ", 1)
            return stage, sub_level
        return None, level_name
    
    def get_stage_xp_threshold(self, world, stage_name, sub_level):
        """الحصول على عتبة XP لمرحلة ومستوى فرعي محدد"""
        if "stage_thresholds" in world and stage_name in world["stage_thresholds"]:
            stage_levels = world["stages"][stage_name]
            if sub_level in stage_levels:
                sub_index = stage_levels.index(sub_level)
                if sub_index < len(world["stage_thresholds"][stage_name]):
                    return world["stage_thresholds"][stage_name][sub_index]
        return None
    
    def get_xp_threshold(self, world, level_name):
        """الحصول على عتبة XP لمستوى محدد"""
        if "sub_levels" in world and "xp_thresholds" in world:
            if level_name in world["sub_levels"]:
                level_index = world["sub_levels"].index(level_name)
                if level_index < len(world["xp_thresholds"]):
                    return world["xp_thresholds"][level_index]
        elif "stages" in world:
            stage, sub_level = self.parse_stage_level(level_name)
            if stage:
                return self.get_stage_xp_threshold(world, stage, sub_level)
        return None

    async def check_level_up(self, user_id, current_xp, current_world, current_level):
        try:
            world = self.get_world(current_world)
            if not world:
                return False, "العالم غير موجود"
            
            # أولاً: تحقق من الترقية داخل العالم الحالي
            upgrade_result = await self.check_intra_world_upgrade(user_id, current_xp, world, current_level)
            if upgrade_result[0]:  # إذا تمت ترقية داخلية
                return upgrade_result
            
            # ثانياً: تحقق من الترقية لعالم جديد
            next_world_index = next((i for i, w in enumerate(self.levels) if w["name"] == current_world), -1) + 1
            next_world = self.levels[next_world_index] if next_world_index < len(self.levels) else None
            
            if next_world and current_xp >= next_world["xp_required"]:
                # تأكد من أن المستخدم في أعلى مستوى في العالم الحالي
                if self.is_at_max_level_in_world(world, current_level):
                    return await self.upgrade_to_next_world(user_id, next_world)
            
            return False, "لا توجد ترقية"
            
        except Exception as e:
            logging.error(f"خطأ في فحص ترقية المستوى: {e}")
            return False, f"حدث خطأ: {str(e)}"
    
    def is_at_max_level_in_world(self, world, current_level):
        """تحقق إذا كان المستخدم في أعلى مستوى في العالم"""
        if "sub_levels" in world:
            return current_level == world["sub_levels"][-1]
        elif "stages" in world:
            stage, sub_level = self.parse_stage_level(current_level)
            if stage:
                last_stage = list(world["stages"].keys())[-1]
                last_sub_level = world["stages"][last_stage][-1]
                return stage == last_stage and sub_level == last_sub_level
        return False
    
    async def upgrade_to_next_world(self, user_id, next_world):
        """ترقية إلى عالم جديد"""
        new_world_name = next_world["name"]
        if "sub_levels" in next_world:
            new_level_name = next_world["sub_levels"][0]
        elif "stages" in next_world:
            first_stage_name = list(next_world["stages"].keys())[0]
            first_sub_level = next_world["stages"][first_stage_name][0]
            new_level_name = f"{first_stage_name} - {first_sub_level}"
        else:
            new_level_name = "مستوى 1"
        
        await execute_query(
            "UPDATE levels SET world_name = ?, level_name = ? WHERE user_id = ?",
            (new_world_name, new_level_name, user_id)
        )
        
        return True, f"🎉 ترقية للعالم الجديد: {new_world_name}!"
    
    async def check_intra_world_upgrade(self, user_id, current_xp, world, current_level):
        """تحقق من الترقية داخل نفس العالم"""
        if "sub_levels" in world:
            return await self.check_sub_level_upgrade(user_id, current_xp, world, current_level)
        elif "stages" in world:
            return await self.check_stage_upgrade(user_id, current_xp, world, current_level)
        return False, "نوع عالم غير مدعوم"
    
    async def check_sub_level_upgrade(self, user_id, current_xp, world, current_level):
        """تحقق من ترقية المستويات الفرعية"""
        try:
            current_level_index = world["sub_levels"].index(current_level)
            if current_level_index < len(world["sub_levels"]) - 1:
                next_level_name = world["sub_levels"][current_level_index + 1]
                
                # استخدام xp_thresholds إذا كان متوفراً
                if "xp_thresholds" in world and current_level_index + 1 < len(world["xp_thresholds"]):
                    required_xp = world["xp_thresholds"][current_level_index + 1]
                else:
                    # حساب احتياطي محسن
                    base_xp = world.get("xp_required", 0)
                    level_multiplier = (current_level_index + 1) * 100
                    required_xp = base_xp + level_multiplier
                
                if current_xp >= required_xp:
                    await execute_query(
                        "UPDATE levels SET level_name = ? WHERE user_id = ?",
                        (next_level_name, user_id)
                    )
                    return True, f"🌟 ترقية لمستوى جديد: {next_level_name}!"
        except ValueError:
            logging.warning(f"مستوى غير موجود في العالم: {current_level}")
        return False, "لا توجد ترقية"
    
    async def check_stage_upgrade(self, user_id, current_xp, world, current_level):
        """تحقق من ترقية المراحل"""
        stage, sub_level = self.parse_stage_level(current_level)
        if not stage or stage not in world["stages"]:
            logging.warning(f"مرحلة غير صحيحة: {current_level}")
            return False, "مرحلة غير صحيحة"
        
        stage_levels = world["stages"][stage]
        if sub_level not in stage_levels:
            logging.warning(f"مستوى فرعي غير صحيح: {sub_level}")
            return False, "مستوى فرعي غير صحيح"
        
        current_sub_index = stage_levels.index(sub_level)
        
        # تحقق من الترقية داخل نفس المرحلة
        if current_sub_index < len(stage_levels) - 1:
            next_sub_level = stage_levels[current_sub_index + 1]
            next_level_name = f"{stage} - {next_sub_level}"
            
            required_xp = self.get_stage_xp_threshold(world, stage, next_sub_level)
            if required_xp and current_xp >= required_xp:
                await execute_query(
                    "UPDATE levels SET level_name = ? WHERE user_id = ?",
                    (next_level_name, user_id)
                )
                return True, f"🌟 ترقية لمستوى جديد: {next_level_name}!"
        
        # تحقق من الترقية لمرحلة تالية
        else:
            stage_names = list(world["stages"].keys())
            if stage in stage_names:
                current_stage_index = stage_names.index(stage)
                if current_stage_index < len(stage_names) - 1:
                    next_stage = stage_names[current_stage_index + 1]
                    next_sub_level = world["stages"][next_stage][0]
                    next_level_name = f"{next_stage} - {next_sub_level}"
                    
                    required_xp = self.get_stage_xp_threshold(world, next_stage, next_sub_level)
                    if required_xp and current_xp >= required_xp:
                        await execute_query(
                            "UPDATE levels SET level_name = ? WHERE user_id = ?",
                            (next_level_name, user_id)
                        )
                        return True, f"🎆 ترقية لمرحلة جديدة: {next_stage}!"
        
        return False, "لا توجد ترقية"
    
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


async def get_user_level_info(user_id: int):
    """الحصول على معلومات مستوى المستخدم كنص منسق"""
    try:
        user_level = await leveling_system.get_user_level_info(user_id)
        
        if not user_level:
            return None
        
        current_xp = user_level.get('xp', 0)
        level_name = user_level.get('level_name', 'نجم 1')
        world_name = user_level.get('world_name', 'عالم النجوم')
        
        # حساب XP المطلوب للمستوى التالي (مبسط)
        if "نجم" in level_name:
            try:
                star_num = int(level_name.split()[-1])
                next_level_xp = 1000 * star_num  # حساب بسيط
            except:
                next_level_xp = 1000
        else:
            next_level_xp = 2000
            
        remaining_xp = max(0, next_level_xp - current_xp)
        
        level_display = f"""⭐ **مستواك:**

🎯 المستوى: {level_name}
✨ النقاط: {current_xp:,} XP
🎪 للمستوى التالي: {remaining_xp:,} XP
📊 التقدم: {current_xp:,} XP"""
        
        return level_display.strip()
        
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المستوى: {e}")
        return None


async def add_xp(user_id: int, amount = None):
    """إضافة XP للمستخدم - wrapper function للاستخدام الخارجي"""
    try:
        success, message = await leveling_system.add_xp(user_id, "generic")
        return success
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للمستخدم {user_id}: {e}")
        return False
"""
نظام الخبرة والمستويات المحسن
Enhanced XP and Leveling System
"""

import logging
from modules.leveling import leveling_system
from database.operations import get_user, execute_query


async def add_xp_for_activity(user_id: int, activity_type: str):
    """إضافة XP للمستخدم عند القيام بنشاط معين"""
    try:
        # قاموس أنواع الأنشطة وXP المقابلة
        activity_xp = {
            "banking": 5,
            "investment": 15,
            "property_deal": 25,
            "theft": 10,
            "farm_activity": 8,
            "castle_activity": 12,
            "marriage": 20,
            "salary": 3,
            "transfer": 5,
            "gambling": 7,
            "message": 1
        }
        
        if activity_type not in activity_xp:
            return False, "نوع النشاط غير مدعوم"
        
        # إضافة XP
        success, message = await leveling_system.add_xp(user_id, activity_type)
        
        if success:
            xp_gained = activity_xp[activity_type]
            return True, f"✨ +{xp_gained} XP من {activity_type}"
        else:
            return False, message
            
    except Exception as e:
        logging.error(f"خطأ في إضافة XP للنشاط: {e}")
        return False, f"حدث خطأ: {str(e)}"


async def get_user_level_display(user_id: int):
    """عرض معلومات مستوى المستخدم"""
    try:
        level_info = await leveling_system.get_user_level_info(user_id)
        
        if not level_info:
            return "❌ لا توجد معلومات مستوى"
        
        # حساب التقدم للمستوى التالي
        current_xp = level_info['xp']
        current_world = level_info['world_name']
        current_level = level_info['level_name']
        
        # البحث عن المستوى التالي
        next_level_xp = get_next_level_xp(current_world, current_level)
        
        level_display = f"""
🌟 **معلومات مستواك:**

🌍 العالم: {current_world}
⭐ المستوى: {current_level}
✨ XP الحالي: {current_xp:,}
🎯 XP للمستوى التالي: {next_level_xp:,}
📊 التقدم: {min(100, (current_xp / next_level_xp) * 100):.1f}%

💡 استمر في النشاط لكسب المزيد من XP!
        """
        
        return level_display.strip()
        
    except Exception as e:
        logging.error(f"خطأ في عرض مستوى المستخدم: {e}")
        return "❌ حدث خطأ في عرض المستوى"


def get_next_level_xp(current_world: str, current_level: str):
    """الحصول على XP المطلوب للمستوى التالي"""
    try:
        from config import LEVELS
        
        # البحث عن العالم الحالي
        for world in LEVELS:
            if world["name"] == current_world:
                if "sub_levels" in world:
                    # عالم به مستويات فرعية
                    try:
                        current_index = world["sub_levels"].index(current_level)
                        if current_index < len(world["sub_levels"]) - 1:
                            # هناك مستوى تالٍ في نفس العالم
                            return (current_index + 2) * 100  # مثال على حساب XP
                        else:
                            # المستوى التالي في العالم التالي
                            world_index = LEVELS.index(world)
                            if world_index < len(LEVELS) - 1:
                                return LEVELS[world_index + 1]["xp_required"]
                    except ValueError:
                        pass
                
                # العالم التالي
                world_index = LEVELS.index(world)
                if world_index < len(LEVELS) - 1:
                    return LEVELS[world_index + 1]["xp_required"]
                else:
                    return 99999  # أقصى XP
        
        return 1000  # افتراضي
        
    except Exception as e:
        logging.error(f"خطأ في حساب XP المستوى التالي: {e}")
        return 1000


async def check_and_notify_level_up(user_id: int, chat_id: int, bot):
    """فحص وإشعار ترقية المستوى"""
    try:
        level_info = await leveling_system.get_user_level_info(user_id)
        
        if not level_info:
            return
        
        # يمكن إضافة لوجيك فحص الترقية هنا
        # وإرسال إشعارات للمستخدم
        
    except Exception as e:
        logging.error(f"خطأ في فحص ترقية المستوى: {e}")
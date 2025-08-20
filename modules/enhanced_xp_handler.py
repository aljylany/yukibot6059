"""
نظام XP محسن ومتكامل
Enhanced and Integrated XP System
"""

import logging
from aiogram.types import Message
from database.operations import get_user, execute_query, get_or_create_user, update_user_activity
from modules.leveling import leveling_system
from utils.helpers import format_number
from datetime import datetime
import asyncio


class EnhancedXPSystem:
    def __init__(self):
        self.xp_rewards = {
            "message": 1,
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
            "custom_reply": 2,
            "command_usage": 3
        }
    
    async def add_xp(self, user_id: int, activity_type: str, amount: int = None):
        """إضافة XP للمستخدم مع تحسينات"""
        try:
            # التأكد من وجود المستخدم
            user = await get_or_create_user(user_id)
            if not user:
                return False, "فشل في إنشاء المستخدم"
            
            # تحديد مقدار XP
            xp_amount = amount if amount else self.xp_rewards.get(activity_type, 1)
            
            # إضافة XP باستخدام النظام المحسن
            success, message = await leveling_system.add_xp(user_id, activity_type)
            
            if success:
                # فحص الترقية
                await self.check_level_up_notification(user_id)
                return True, f"✨ +{xp_amount} XP"
            else:
                return False, message
                
        except Exception as e:
            logging.error(f"خطأ في إضافة XP: {e}")
            return False, f"حدث خطأ: {str(e)}"
    
    async def check_level_up_notification(self, user_id: int):
        """فحص وإشعار ترقية المستوى"""
        try:
            # يمكن إضافة لوجيك إشعار الترقية هنا
            pass
        except Exception as e:
            logging.error(f"خطأ في فحص الترقية: {e}")
    
    async def get_user_stats(self, user_id: int):
        """الحصول على إحصائيات المستخدم الشاملة"""
        try:
            level_info = await leveling_system.get_user_level_info(user_id)
            user = await get_user(user_id)
            
            if not level_info or not user:
                return None
            
            # حساب التقدم
            current_xp = level_info.get('xp', 0)
            current_world = level_info.get('world_name', 'عالم النجوم')
            current_level = level_info.get('level_name', 'نجم 1')
            
            # البحث عن العالم الحالي لحساب XP المطلوب
            next_level_xp = await self.calculate_next_level_xp(current_world, current_level, current_xp)
            progress_percentage = min(100, (current_xp / next_level_xp) * 100) if next_level_xp > 0 else 100
            
            stats = {
                'user_id': user_id,
                'xp': current_xp,
                'level_name': current_level,
                'world_name': current_world,
                'progress': progress_percentage,
                'next_level_xp': next_level_xp,
                'balance': user.get('balance', 0),
                'bank_balance': user.get('bank_balance', 0)
            }
            
            return stats
            
        except Exception as e:
            logging.error(f"خطأ في إحصائيات المستخدم: {e}")
            return None
    
    async def calculate_next_level_xp(self, current_world: str, current_level: str, current_xp: int):
        """حساب XP المطلوب للمستوى التالي بدقة"""
        try:
            from config import LEVELS
            
            # البحث عن العالم الحالي
            for i, world in enumerate(LEVELS):
                if world["name"] == current_world:
                    # إذا كان العالم له مستويات فرعية
                    if "sub_levels" in world:
                        try:
                            current_index = world["sub_levels"].index(current_level)
                            if current_index < len(world["sub_levels"]) - 1:
                                # المستوى التالي في نفس العالم
                                return (current_index + 2) * 200  # تحسين نظام حساب XP
                            else:
                                # العالم التالي
                                if i + 1 < len(LEVELS):
                                    return LEVELS[i + 1]["xp_required"]
                        except ValueError:
                            pass
                    
                    # عالم بدون مستويات فرعية
                    if i + 1 < len(LEVELS):
                        return LEVELS[i + 1]["xp_required"]
                    else:
                        return 99999  # أقصى مستوى
            
            return 1000  # افتراضي
            
        except Exception as e:
            logging.error(f"خطأ في حساب XP التالي: {e}")
            return 1000
    
    async def format_user_level_display(self, user_id: int):
        """تنسيق عرض مستوى المستخدم"""
        try:
            stats = await self.get_user_stats(user_id)
            
            if not stats:
                return "❌ لا توجد معلومات مستوى"
            
            # تنسيق العرض
            display = f"""
🌟 **معلومات مستواك:**

🌍 **العالم:** {stats['world_name']}
⭐ **المستوى:** {stats['level_name']}
✨ **XP الحالي:** {format_number(stats['xp'])}
🎯 **XP للمستوى التالي:** {format_number(stats['next_level_xp'])}
📊 **التقدم:** {stats['progress']:.1f}%

💰 **رصيدك النقدي:** {format_number(stats['balance'])}$
🏦 **رصيدك البنكي:** {format_number(stats['bank_balance'])}$

💡 **استمر في النشاط لكسب المزيد من XP!**

🎮 **أنشطة تمنح XP:**
• الرسائل: +1 XP
• العمليات المصرفية: +5 XP  
• الاستثمار: +15 XP
• العقارات: +25 XP
• المزرعة: +8 XP
• القلعة: +12 XP
            """
            
            return display.strip()
            
        except Exception as e:
            logging.error(f"خطأ في تنسيق العرض: {e}")
            return "❌ حدث خطأ في عرض المستوى"


# إنشاء نسخة عامة من النظام المحسن
enhanced_xp_system = EnhancedXPSystem()


async def add_xp_for_activity(user_id: int, activity_type: str):
    """دالة مساعدة لإضافة XP"""
    return await enhanced_xp_system.add_xp(user_id, activity_type)


async def get_user_level_display(user_id: int):
    """دالة مساعدة لعرض المستوى"""
    return await enhanced_xp_system.format_user_level_display(user_id)


async def handle_level_command(message: Message):
    """معالج أمر عرض المستوى"""
    try:
        # التأكد من وجود المستخدم في قاعدة البيانات
        await update_user_activity(message.from_user.id)
        
        level_display = await get_user_level_display(message.from_user.id)
        await message.reply(level_display)
        
        # إضافة XP لاستخدام الأمر
        await add_xp_for_activity(message.from_user.id, "command_usage")
        
    except Exception as e:
        logging.error(f"خطأ في عرض مستوى المستخدم: {e}")
        await message.reply("❌ حدث خطأ في عرض معلومات المستوى")
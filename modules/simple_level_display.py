"""
عرض مبسط للمستوى والتقدم
Simple Level and Progress Display
"""

import logging
from aiogram.types import Message
from database.operations import get_user, execute_query, update_user_activity
from utils.helpers import format_number
from config.hierarchy import MASTERS


async def get_user_level_info(user_id: int):
    """الحصول على معلومات مستوى المستخدم كنص"""
    try:
        current_xp = 0
        current_level = 'نجم 1'
        current_world = 'عالم النجوم'
        
        # الحصول على بيانات المستخدم
        level_data = await execute_query(
            "SELECT xp, level_name, world_name FROM levels WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if level_data:
            if isinstance(level_data, dict):
                current_xp = level_data.get('xp', 0)
                current_level = level_data.get('level_name', 'نجم 1')
                current_world = level_data.get('world_name', 'عالم النجوم')
            elif isinstance(level_data, (list, tuple)) and level_data:
                current_xp = level_data[0] if len(level_data) > 0 else 0
                current_level = level_data[1] if len(level_data) > 1 else 'نجم 1'
                current_world = level_data[2] if len(level_data) > 2 else 'عالم النجوم'
        
        # حساب XP المطلوب للمستوى التالي
        next_level_xp = calculate_next_xp(current_world, current_level, current_xp)
        remaining_xp = max(0, next_level_xp - current_xp)  # التأكد من عدم وجود قيم سالبة
        
        # عرض المستوى بشكل مبسط
        level_display = f"""⭐ **مستواك:**

🎯 المستوى: {current_level}
✨ النقاط: {format_number(current_xp)} XP
🎪 للمستوى التالي: {format_number(remaining_xp)} XP
📊 التقدم: {format_number(current_xp)} XP"""
        
        return level_display.strip()
        
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المستوى: {e}")
        return None


async def show_simple_level(message: Message):
    """عرض مبسط للمستوى فقط"""
    try:
        # التأكد من وجود المستخدم
        await update_user_activity(message.from_user.id)
        user_id = message.from_user.id
        
        # الحصول على معلومات المستوى
        level_data = await execute_query(
            "SELECT xp, level_name, world_name FROM levels WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if not level_data:
            # إنشاء سجل جديد للمستخدم
            from datetime import datetime
            await execute_query(
                "INSERT INTO levels (user_id, xp, level_name, world_name, last_xp_gain) VALUES (?, 0, 'نجم 1', 'عالم النجوم', ?)",
                (user_id, datetime.now().timestamp())
            )
            current_xp = 0
            current_level = "نجم 1"
            current_world = "عالم النجوم"
        else:
            if isinstance(level_data, dict):
                current_xp = level_data.get('xp', 0)
                current_level = level_data.get('level_name', 'نجم 1')
                current_world = level_data.get('world_name', 'عالم النجوم')
            else:
                # إذا كان level_data tuple أو list
                current_xp = level_data[0] if len(level_data) > 0 else 0
                current_level = level_data[1] if len(level_data) > 1 else 'نجم 1'
                current_world = level_data[2] if len(level_data) > 2 else 'عالم النجوم'
        
        # حساب XP المطلوب للمستوى التالي
        next_level_xp = calculate_next_xp(current_world, current_level, current_xp)
        
        # عرض المستوى بشكل مبسط
        level_display = f"""
🌟 **مستواك الحالي:**

🌍 العالم: {current_world}
⭐ المستوى: {current_level}
✨ XP: {format_number(current_xp)}

🎯 للمستوى التالي: {format_number(next_level_xp)} XP
📊 تحتاج: {format_number(next_level_xp - current_xp)} XP

💡 كل نشاط يمنحك XP!
        """
        
        await message.reply(level_display.strip())
        
        # إضافة XP للاستعلام
        await add_simple_xp(user_id, 2)
        
    except Exception as e:
        logging.error(f"خطأ في عرض المستوى المبسط: {e}")
        await message.reply("❌ حدث خطأ في عرض مستواك")


def calculate_next_xp(world_name: str, level_name: str, current_xp: int):
    """حساب XP المطلوب للمستوى التالي"""
    try:
        # نظام بسيط لحساب XP
        base_xp = 100
        
        # زيادة XP حسب العالم
        world_multipliers = {
            "عالم النجوم": 1,
            "عالم القمر": 2,
            "عالم الشمس": 3,
            "عالم الأسطورة": 5,
            "العالم السيادي": 8,
            "العالم النهائي": 12
        }
        
        multiplier = world_multipliers.get(world_name, 1)
        
        # حساب XP للمستوى التالي
        if "نجم" in level_name:
            try:
                star_num = int(level_name.split()[-1])
                return base_xp * multiplier * (star_num + 1)
            except:
                return base_xp * multiplier * 2
        
        return base_xp * multiplier * 10
        
    except Exception as e:
        logging.error(f"خطأ في حساب XP التالي: {e}")
        return 1000


async def add_simple_xp(user_id: int, amount: int = 1):
    """إضافة XP بسيطة"""
    try:
        from datetime import datetime
        
        # التحقق من كون المستخدم من الأسياد - المستوى 1000
        # قائمة الأسياد المباشرة (ID: 6524680126 كمثال)
        # استخدام قائمة الأسياد الرسمية
        is_master = user_id in MASTERS
        
        # الحصول على XP الحالي
        current_data = await execute_query(
            "SELECT xp, level_name, world_name FROM levels WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if current_data:
            if isinstance(current_data, dict):
                current_xp = current_data.get('xp', 0)
                current_level = current_data.get('level_name', 'نجم 1')
                current_world = current_data.get('world_name', 'عالم النجوم')
            else:
                current_xp = current_data[0] if len(current_data) > 0 else 0
                current_level = current_data[1] if len(current_data) > 1 else 'نجم 1'
                current_world = current_data[2] if len(current_data) > 2 else 'عالم النجوم'
            
            # للأسياد - مستوى 1000 دائماً
            if is_master:
                new_xp = max(current_xp + amount, 100000)  # XP عالي للمستوى 1000
                new_level = "سيد المطلق"
                new_world = "العالم السيادي المطلق"
            else:
                new_xp = current_xp + amount
                new_level = current_level
                new_world = current_world
            
            # تحديث XP
            await execute_query(
                "UPDATE levels SET xp = ?, level_name = ?, world_name = ?, last_xp_gain = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                (new_xp, new_level, new_world, datetime.now().timestamp(), user_id)
            )
        else:
            # إنشاء سجل جديد
            if is_master:
                # الأسياد يبدؤون بمستوى 1000
                await execute_query(
                    "INSERT INTO levels (user_id, xp, level_name, world_name, last_xp_gain) VALUES (?, ?, 'سيد المطلق', 'العالم السيادي المطلق', ?)",
                    (user_id, 100000, datetime.now().timestamp())
                )
            else:
                await execute_query(
                    "INSERT INTO levels (user_id, xp, level_name, world_name, last_xp_gain) VALUES (?, ?, 'نجم 1', 'عالم النجوم', ?)",
                    (user_id, amount, datetime.now().timestamp())
                )
            
    except Exception as e:
        logging.error(f"خطأ في إضافة XP البسيط: {e}")


async def handle_simple_progress_command(message: Message):
    """معالج أمر 'تقدمي' البسيط"""
    await show_simple_level(message)
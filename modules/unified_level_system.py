"""
نظام المستويات الموحد
Unified Level System
"""

import logging
from database.operations import execute_query
from config.hierarchy import MASTERS

async def get_unified_user_level(user_id: int):
    """
    الحصول على مستوى المستخدم من النظام الموحد
    Returns: dict with level, xp, level_name, world_name
    """
    try:
        # التحقق من كون المستخدم من الأسياد
        is_master = user_id in MASTERS
        
        if is_master:
            return {
                'level': 1000,
                'xp': 100000,
                'level_name': 'سيد المطلق',
                'world_name': 'العالم السيادي المطلق',
                'is_master': True
            }
        
        # البحث في جدول المستويات الجديد
        level_data = await execute_query(
            "SELECT xp, level_name, world_name FROM levels WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if level_data:
            if isinstance(level_data, tuple):
                xp = level_data[0] if len(level_data) > 0 else 0
                level_name = level_data[1] if len(level_data) > 1 else 'نجم 1'
                world_name = level_data[2] if len(level_data) > 2 else 'عالم النجوم'
            else:
                xp = level_data.get('xp', 0)
                level_name = level_data.get('level_name', 'نجم 1')
                world_name = level_data.get('world_name', 'عالم النجوم')
            
            # حساب المستوى من XP
            if xp >= 30000:
                level = 1000
            elif xp >= 15000:
                level = 500
            elif xp >= 7000:
                level = 100
            elif xp >= 3000:
                level = 50
            elif xp >= 1000:
                level = 25
            else:
                level = max(1, xp // 100)
                
            return {
                'level': level,
                'xp': xp,
                'level_name': level_name,
                'world_name': world_name,
                'is_master': False
            }
        else:
            # مستخدم جديد
            return {
                'level': 1,
                'xp': 0,
                'level_name': 'نجم 1',
                'world_name': 'عالم النجوم',
                'is_master': False
            }
            
    except Exception as e:
        logging.error(f"خطأ في الحصول على مستوى المستخدم: {e}")
        return {
            'level': 1,
            'xp': 0,
            'level_name': 'نجم 1',
            'world_name': 'عالم النجوم',
            'is_master': False
        }


async def show_unified_user_info(message, user_id):
    """عرض معلومات المستخدم مع النظام الموحد"""
    try:
        from database.operations import get_user
        from utils.helpers import format_number
        
        # الحصول على معلومات المستخدم الأساسية
        user = await get_user(user_id)
        if not user:
            return "❌ المستخدم غير مسجل في النظام"
        
        # الحصول على معلومات المستوى الموحدة
        level_info = await get_unified_user_level(user_id)
        
        # معلومات أساسية
        username = message.from_user.username or "غير محدد"
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        
        # تحديد التصنيف
        if level_info['is_master']:
            user_type = "سيد مطلق"
            type_emoji = "👑"
        elif level_info['level'] >= 100:
            user_type = "لاعب أسطوري"
            type_emoji = "🔥"
        elif level_info['level'] >= 50:
            user_type = "لاعب محترف"
            type_emoji = "⭐"
        elif level_info['level'] >= 25:
            user_type = "لاعب متقدم"
            type_emoji = "🎯"
        else:
            user_type = "لاعب عادي"
            type_emoji = "👤"
        
        # بناء الرسالة
        user_name = message.from_user.first_name or "المستخدم"
        info_text = f"""👤 **حساب {user_name}**

📋 **المعلومات الأساسية:**
• 🆔 الرقم التعريفي: {user_id}
• 📛 اسم المستخدم: @{username}
• {type_emoji} التصنيف: {user_type}
• 📊 المستوى: {level_info['level']}
• ⭐ نقاط الخبرة: {format_number(level_info['xp'])}
• 🌍 العالم: {level_info['world_name']}
• 🎭 الرتبة: {level_info['level_name']}

💰 **الوضع المالي:**
• 💵 الرصيد الحالي: {format_number(balance)}$
• 🏦 رصيد البنك: {format_number(bank_balance)}$
• 🏛️ نوع البنك: {bank_type}

📈 **القيمة الإجمالية:**
{format_number(balance + bank_balance)}$"""

        return info_text
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات المستخدم الموحدة: {e}")
        return "❌ حدث خطأ في عرض المعلومات"
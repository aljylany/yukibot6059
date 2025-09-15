"""
وحدة معلومات المستخدم
User Information Module
"""

import logging
from aiogram.types import Message
from database.operations import execute_query, get_user
from utils.helpers import format_number
from config.hierarchy import MASTERS


async def show_my_rank(message: Message):
    """عرض رتبة المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # استخدام النظام الهرمي المتقدم للتحقق من الرتبة
        from config.hierarchy import get_user_admin_level, get_admin_level_name, AdminLevel
        
        # الحصول على مستوى الإدارة الفعلي (يتضمن التحقق من تليجرام)
        admin_level = get_user_admin_level(user_id, chat_id)
        level_name = get_admin_level_name(admin_level)
        
        # تحديد الرمز والوصف حسب المستوى
        rank_emoji = {
            AdminLevel.MEMBER: '👤',
            AdminLevel.MODERATOR: '🛡️',
            AdminLevel.GROUP_OWNER: '👑',
            AdminLevel.MASTER: '🔥',
            AdminLevel.KING: '👑',
            AdminLevel.QUEEN: '👸'
        }
        
        rank_description = {
            AdminLevel.MEMBER: 'عضو في المجموعة',
            AdminLevel.MODERATOR: 'مشرف - صلاحيات إدارية',
            AdminLevel.GROUP_OWNER: 'مالك المجموعة - صلاحيات كاملة',
            AdminLevel.MASTER: 'السيد - صلاحيات مطلقة',
            AdminLevel.KING: 'الملك - أعلى مستوى في النظام',
            AdminLevel.QUEEN: 'الملكة - أعلى مستوى في النظام'
        }
        
        emoji = rank_emoji.get(admin_level, '🎖️')
        description = rank_description.get(admin_level, 'رتبة خاصة')
        
        # إضافة تمييز خاص للأسياد والملوك
        crown_emoji = ""
        if user_id in MASTERS:
            crown_emoji = " 👑"
        
        # البحث عن تاريخ الترقية من قاعدة البيانات (إذا كان متوفراً)
        promoted_at = None
        try:
            rank_info = await execute_query(
                "SELECT promoted_at FROM group_ranks WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
                fetch_one=True
            )
            if rank_info:
                promoted_at = rank_info[0] if isinstance(rank_info, tuple) else rank_info.get('promoted_at', '')
        except:
            pass
        
        # تنسيق الرسالة
        response_text = f"{emoji} **رتبتك:**{crown_emoji}\n\n"
        response_text += f"📋 الرتبة: {level_name}\n"
        response_text += f"📝 الوصف: {description}"
        
        if promoted_at:
            date_str = promoted_at[:10] if len(promoted_at) >= 10 else promoted_at
            response_text += f"\n📅 تاريخ الترقية: {date_str}"
        elif admin_level == AdminLevel.MEMBER:
            response_text += "\n💡 يمكن للمشرفين رفع رتبتك"
        
        await message.reply(response_text)
    
    except Exception as e:
        logging.error(f"خطأ في عرض الرتبة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتبة")


async def show_my_balance(message: Message):
    """عرض رصيد المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        user = await get_user(user_id)
        
        if not user:
            await message.reply(
                "❌ **لم يتم العثور على حسابك**\n\n"
                "💡 استخدم الأوامر التالية لإنشاء حساب:\n"
                "• `حساب بنكي`\n"
                "• `انشاء حساب`"
            )
            return
        
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        total_earned = user.get('total_earned', 0) if isinstance(user, dict) else 0
        total_spent = user.get('total_spent', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        
        await message.reply(
            f"💰 **رصيدك المالي:**\n\n"
            f"💵 النقد: {format_number(balance)}$\n"
            f"🏦 البنك ({bank_type}): {format_number(bank_balance)}$\n"
            f"💎 المجموع: {format_number(balance + bank_balance)}$\n\n"
            f"📊 **الإحصائيات:**\n"
            f"📈 إجمالي الكسب: {format_number(total_earned)}$\n"
            f"📉 إجمالي الإنفاق: {format_number(total_spent)}$"
        )
    
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرصيد")


async def show_user_balance(message: Message):
    """عرض رصيد مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `فلوسه`\n\n"
                "💡 أو استخدم `فلوسي` لمعرفة رصيدك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        user = await get_user(target_user.id)
        
        if not user:
            target_name = target_user.first_name or "المستخدم"
            await message.reply(
                f"❌ **{target_name} ليس مسجل في النظام**\n\n"
                "💡 يحتاج لإنشاء حساب بنكي أولاً"
            )
            return
        
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        target_name = target_user.first_name or "المستخدم"
        
        await message.reply(
            f"💰 **رصيد {target_name}:**\n\n"
            f"💵 النقد: {format_number(balance)}$\n"
            f"🏦 البنك ({bank_type}): {format_number(bank_balance)}$\n"
            f"💎 المجموع: {format_number(balance + bank_balance)}$"
        )
    
    except Exception as e:
        logging.error(f"خطأ في عرض رصيد المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرصيد")


async def show_user_rank(message: Message):
    """عرض رتبة مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `رتبته`\n\n"
                "💡 أو استخدم `رتبتي` لمعرفة رتبتك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        user_id = target_user.id
        chat_id = message.chat.id
        target_name = target_user.first_name or "المستخدم"
        
        # استخدام النظام الهرمي المتقدم للتحقق من الرتبة
        from config.hierarchy import get_user_admin_level, get_admin_level_name, AdminLevel
        
        # الحصول على مستوى الإدارة الفعلي (يتضمن التحقق من تليجرام)
        admin_level = get_user_admin_level(user_id, chat_id)
        level_name = get_admin_level_name(admin_level)
        
        # تحديد الرمز والوصف حسب المستوى
        rank_emoji = {
            AdminLevel.MEMBER: '👤',
            AdminLevel.MODERATOR: '🛡️',
            AdminLevel.GROUP_OWNER: '👑',
            AdminLevel.MASTER: '🔥',
            AdminLevel.KING: '👑',
            AdminLevel.QUEEN: '👸'
        }
        
        rank_description = {
            AdminLevel.MEMBER: 'عضو في المجموعة',
            AdminLevel.MODERATOR: 'مشرف - صلاحيات إدارية',
            AdminLevel.GROUP_OWNER: 'مالك المجموعة - صلاحيات كاملة',
            AdminLevel.MASTER: 'السيد - صلاحيات مطلقة',
            AdminLevel.KING: 'الملك - أعلى مستوى في النظام',
            AdminLevel.QUEEN: 'الملكة - أعلى مستوى في النظام'
        }
        
        emoji = rank_emoji.get(admin_level, '🎖️')
        description = rank_description.get(admin_level, 'رتبة خاصة')
        
        # إضافة تمييز خاص للأسياد والملوك
        crown_emoji = ""
        if user_id in MASTERS:
            crown_emoji = " 👑"
        
        # البحث عن تاريخ الترقية من قاعدة البيانات (إذا كان متوفراً)
        promoted_at = None
        try:
            rank_info = await execute_query(
                "SELECT promoted_at FROM group_ranks WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
                fetch_one=True
            )
            if rank_info:
                promoted_at = rank_info[0] if isinstance(rank_info, tuple) else rank_info.get('promoted_at', '')
        except:
            pass
        
        # تنسيق الرسالة
        response_text = f"{emoji} **رتبة {target_name}:**{crown_emoji}\n\n"
        response_text += f"📋 الرتبة: {level_name}\n"
        response_text += f"📝 الوصف: {description}"
        
        if promoted_at:
            date_str = promoted_at[:10] if len(promoted_at) >= 10 else promoted_at
            response_text += f"\n📅 تاريخ الترقية: {date_str}"
        
        await message.reply(response_text)
    
    except Exception as e:
        logging.error(f"خطأ في عرض رتبة المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتبة")


async def show_user_level(message: Message):
    """عرض مستوى مستخدم آخر بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "1️⃣ رد على رسالة الشخص\n"
                "2️⃣ اكتب: `مستواه`\n\n"
                "💡 أو استخدم `مستواي` لمعرفة مستواك"
            )
            return
        
        target_user = message.reply_to_message.from_user
        target_name = target_user.first_name or "المستخدم"
        
        # استخدام نظام المستويات الجديد
        from modules.leveling import get_user_level_info
        level_info = await get_user_level_info(target_user.id)
        
        if not level_info:
            await message.reply(
                f"❌ **{target_name} ليس مسجل في النظام**\n\n"
                "💡 يحتاج لإرسال رسالة أولاً لإنشاء حساب"
            )
            return
        
        await message.reply(level_info.replace("**مستواك:**", f"**مستوى {target_name}:**"))
    
    except Exception as e:
        logging.error(f"خطأ في عرض مستوى المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المستوى")


async def show_my_level(message: Message):
    """عرض مستوى المستخدم الحالي"""
    try:
        user_id = message.from_user.id
        
        # استخدام نظام المستويات الجديد  
        from modules.leveling import get_user_level_info
        level_info = await get_user_level_info(user_id)
        
        if not level_info:
            await message.reply(
                "❌ **لم يتم العثور على حسابك**\n\n"
                "💡 ارسل أي رسالة لإنشاء حساب جديد"
            )
            return
        
        await message.reply(level_info)
    
    except Exception as e:
        logging.error(f"خطأ في عرض المستوى: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المستوى")


async def show_comprehensive_account_info(message: Message):
    """عرض معلومات الحساب الشاملة - بديل unified_level_system"""
    try:
        user_id = message.from_user.id
        user = await get_user(user_id)
        
        if not user:
            await message.reply(
                "❌ **لم يتم العثور على حسابك**\n\n"
                "💡 استخدم 'انشاء حساب بنكي' لإنشاء حساب جديد"
            )
            return
        
        # الحصول على معلومات المستوى
        try:
            from modules.leveling import get_user_level_info
            level_info_raw = await get_user_level_info(user_id)
        except:
            level_info_raw = "❌ نظام المستويات غير متاح"
        
        # معلومات الرصيد
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        bank_balance = user.get('bank_balance', 0) if isinstance(user, dict) else 0
        bank_type = user.get('bank_type', 'الأهلي') if isinstance(user, dict) else 'الأهلي'
        total_wealth = balance + bank_balance
        
        # معلومات إضافية
        total_earned = user.get('total_earned', 0) if isinstance(user, dict) else 0
        total_spent = user.get('total_spent', 0) if isinstance(user, dict) else 0
        
        # الحصول على معلومات العقارات
        try:
            user_properties = await execute_query(
                "SELECT property_type, quantity FROM user_properties WHERE user_id = ?",
                (user_id,),
                fetch_all=True
            )
            properties_count = sum(prop[1] if isinstance(prop, tuple) else prop.get('quantity', 0) for prop in user_properties) if user_properties else 0
        except:
            properties_count = 0
        
        # الحصول على معلومات الاستثمارات
        try:
            user_investments = await execute_query(
                "SELECT COUNT(*), SUM(amount) FROM user_investments WHERE user_id = ? AND status = 'active'",
                (user_id,),
                fetch_one=True
            )
            investments_count = user_investments[0] if user_investments and user_investments[0] else 0
            investments_total = user_investments[1] if user_investments and user_investments[1] else 0
        except:
            investments_count = 0
            investments_total = 0
        
        # الحصول على معلومات المزرعة
        try:
            farm_crops = await execute_query(
                "SELECT COUNT(*) FROM user_crops WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            crops_count = farm_crops[0] if farm_crops and farm_crops[0] else 0
        except:
            crops_count = 0
        
        # الحصول على معلومات القلعة
        try:
            castle_data = await execute_query(
                "SELECT castle_level FROM user_castle WHERE user_id = ?",
                (user_id,),
                fetch_one=True
            )
            castle_level = castle_data[0] if castle_data and castle_data[0] else 0
        except:
            castle_level = 0
        
        # تنسيق رسالة شاملة
        account_info = f"""
👤 **معلومات حسابك الشاملة**

💰 **الوضع المالي:**
💵 النقد: {format_number(balance)}$
🏦 البنك ({bank_type}): {format_number(bank_balance)}$
💎 إجمالي الثروة: {format_number(total_wealth)}$

📊 **الإحصائيات المالية:**
📈 إجمالي الكسب: {format_number(total_earned)}$
📉 إجمالي الإنفاق: {format_number(total_spent)}$

🎮 **الأنشطة الاقتصادية:**
🏠 العقارات: {properties_count} عقار
📈 الاستثمارات: {investments_count} استثمار نشط ({format_number(investments_total)}$)
🌾 المحاصيل: {crops_count} محصول
🏰 مستوى القلعة: {castle_level}

{level_info_raw if level_info_raw != "❌ نظام المستويات غير متاح" else ""}
        """.strip()
        
        await message.reply(account_info)
    
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات الحساب الشاملة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات الحساب")
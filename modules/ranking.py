"""
وحدة الترتيب والمتصدرين
Ranking and Leaderboard Module
"""

import logging
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from database.operations import get_user, execute_query
from utils.helpers import format_number


async def show_leaderboard(message: Message):
    """عرض قائمة المتصدرين العامة"""
    try:
        # الحصول على أغنى اللاعبين
        top_players = await get_top_players_by_wealth()
        
        if not top_players:
            await message.reply("❌ لا توجد بيانات متاحة حالياً")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 الأغنى", callback_data="ranking_wealth"),
                InlineKeyboardButton(text="🏦 أكبر مودع", callback_data="ranking_bank")
            ],
            [
                InlineKeyboardButton(text="🏠 أكثر عقارات", callback_data="ranking_properties"),
                InlineKeyboardButton(text="📈 أفضل مستثمر", callback_data="ranking_investor")
            ],
            [
                InlineKeyboardButton(text="🔓 أمهر لص", callback_data="ranking_thief"),
                InlineKeyboardButton(text="🛡 أقوى حماية", callback_data="ranking_security")
            ]
        ])
        
        leaderboard_text = "🏆 **قائمة المتصدرين - الأغنى**\n\n"
        
        for i, player in enumerate(top_players[:10], 1):
            total_wealth = player['balance'] + player['bank_balance']
            
            # رموز المراكز
            if i == 1:
                rank_emoji = "🥇"
            elif i == 2:
                rank_emoji = "🥈"
            elif i == 3:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"{i}️⃣"
            
            username = player.get('username', 'مجهول')
            if username == 'مجهول':
                username = player.get('first_name', 'مجهول')[:10]
            
            leaderboard_text += f"{rank_emoji} **{username}**\n"
            leaderboard_text += f"   💰 الثروة: {format_number(total_wealth)}$\n"
            leaderboard_text += f"   💵 النقد: {format_number(player['balance'])}$\n"
            leaderboard_text += f"   🏦 البنك: {format_number(player['bank_balance'])}$\n\n"
        
        # العثور على ترتيب المستخدم الحالي
        if message.from_user:
            user_rank = await get_user_rank(message.from_user.id, 'wealth')
            user = await get_user(message.from_user.id)
        else:
            user_rank = None
            user = None
        
        if user and user_rank:
            user_wealth = user['balance'] + user['bank_balance']
            leaderboard_text += f"📊 **ترتيبك الحالي:**\n"
            leaderboard_text += f"🎯 المركز: #{user_rank}\n"
            leaderboard_text += f"💰 ثروتك: {format_number(user_wealth)}$"
        
        await message.reply(leaderboard_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة المتصدرين: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المتصدرين")


async def show_user_ranking(message: Message):
    """عرض ترتيب المستخدم الشخصي"""
    try:
        if message.from_user:
            user = await get_user(message.from_user.id)
        else:
            await message.reply("❌ حدث خطأ في التعرف على المستخدم")
            return
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على جميع التصنيفات
        if message.from_user:
            wealth_rank = await get_user_rank(message.from_user.id, 'wealth')
            bank_rank = await get_user_rank(message.from_user.id, 'bank')
            properties_rank = await get_user_rank(message.from_user.id, 'properties')
            investments_rank = await get_user_rank(message.from_user.id, 'investments')
            
            # حساب الإحصائيات
            total_wealth = user['balance'] + user['bank_balance']
            properties_count = await get_user_properties_count(message.from_user.id)
            investments_value = await get_user_investments_value(message.from_user.id)
        else:
            wealth_rank = bank_rank = properties_rank = investments_rank = None
            total_wealth = properties_count = investments_value = 0
        
        ranking_text = f"""
🎯 **ترتيبك الشخصي**

👤 **معلوماتك:**
💰 إجمالي الثروة: {format_number(total_wealth)}$
💵 النقد: {format_number(user['balance'])}$
🏦 البنك: {format_number(user['bank_balance'])}$
🏠 العقارات: {properties_count}
💼 الاستثمارات: {format_number(investments_value)}$

🏆 **تصنيفاتك:**
💰 الثروة: #{wealth_rank or 'غير مصنف'}
🏦 الودائع المصرفية: #{bank_rank or 'غير مصنف'}
🏠 العقارات: #{properties_rank or 'غير مصنف'}
💼 الاستثمارات: #{investments_rank or 'غير مصنف'}

💡 استمر في اللعب لتحسين ترتيبك!
        """
        
        await message.reply(ranking_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الترتيب الشخصي: {e}")
        await message.reply("❌ حدث خطأ في عرض ترتيبك")


async def show_weekly_ranking(message: Message):
    """عرض ترتيب الأسبوع"""
    try:
        # حساب تاريخ بداية الأسبوع
        week_start = datetime.now() - timedelta(days=7)
        
        # الحصول على أكثر المستخدمين نشاطاً هذا الأسبوع
        weekly_active = await get_weekly_active_users(week_start)
        
        if not weekly_active:
            await message.reply("❌ لا توجد بيانات للأسبوع الحالي")
            return
        
        weekly_text = "📅 **ترتيب الأسبوع - الأكثر نشاطاً**\n\n"
        
        for i, player in enumerate(weekly_active[:10], 1):
            if i == 1:
                rank_emoji = "🥇"
            elif i == 2:
                rank_emoji = "🥈"
            elif i == 3:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"{i}️⃣"
            
            username = player.get('username', player.get('first_name', 'مجهول'))[:10]
            
            weekly_text += f"{rank_emoji} **{username}**\n"
            weekly_text += f"   🎯 المعاملات: {player.get('transaction_count', 0)}\n"
            weekly_text += f"   💰 حجم النشاط: {format_number(player.get('total_activity', 0))}$\n\n"
        
        await message.reply(weekly_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض ترتيب الأسبوع: {e}")
        await message.reply("❌ حدث خطأ في عرض ترتيب الأسبوع")


async def show_monthly_ranking(message: Message):
    """عرض ترتيب الشهر"""
    try:
        # حساب تاريخ بداية الشهر
        month_start = datetime.now() - timedelta(days=30)
        
        # الحصول على أفضل المستثمرين هذا الشهر
        monthly_investors = await get_monthly_top_investors(month_start)
        
        if not monthly_investors:
            await message.reply("❌ لا توجد بيانات للشهر الحالي")
            return
        
        monthly_text = "📊 **ترتيب الشهر - أفضل المستثمرين**\n\n"
        
        for i, investor in enumerate(monthly_investors[:10], 1):
            if i == 1:
                rank_emoji = "🥇"
            elif i == 2:
                rank_emoji = "🥈"
            elif i == 3:
                rank_emoji = "🥉"
            else:
                rank_emoji = f"{i}️⃣"
            
            username = investor.get('username', investor.get('first_name', 'مجهول'))[:10]
            
            monthly_text += f"{rank_emoji} **{username}**\n"
            monthly_text += f"   💼 الاستثمارات: {format_number(investor.get('total_invested', 0))}$\n"
            monthly_text += f"   📈 العائد: {format_number(investor.get('total_return', 0))}$\n\n"
        
        await message.reply(monthly_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض ترتيب الشهر: {e}")
        await message.reply("❌ حدث خطأ في عرض ترتيب الشهر")


async def get_top_players_by_wealth():
    """الحصول على أغنى اللاعبين"""
    try:
        players = await execute_query(
            "SELECT user_id, username, first_name, balance, bank_balance, (balance + bank_balance) as total_wealth FROM users ORDER BY total_wealth DESC LIMIT 20",
            (),
            fetch_all=True
        )
        return players if players else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على أغنى اللاعبين: {e}")
        return []


async def get_top_players_by_bank():
    """الحصول على أكبر المودعين في البنك"""
    try:
        players = await execute_query(
            "SELECT user_id, username, first_name, bank_balance FROM users WHERE bank_balance > 0 ORDER BY bank_balance DESC LIMIT 20",
            (),
            fetch_all=True
        )
        return players if players else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على أكبر المودعين: {e}")
        return []


async def get_top_property_owners():
    """الحصول على أكبر ملاك العقارات"""
    try:
        owners = await execute_query(
            """
            SELECT u.user_id, u.username, u.first_name, COUNT(p.id) as property_count, SUM(p.price) as total_value
            FROM users u
            LEFT JOIN properties p ON u.user_id = p.user_id
            GROUP BY u.user_id
            HAVING property_count > 0
            ORDER BY property_count DESC, total_value DESC
            LIMIT 20
            """,
            (),
            fetch_all=True
        )
        return owners if owners else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على ملاك العقارات: {e}")
        return []


async def get_top_investors():
    """الحصول على أفضل المستثمرين"""
    try:
        investors = await execute_query(
            """
            SELECT u.user_id, u.username, u.first_name, 
                   SUM(i.amount) as total_invested, 
                   SUM(i.amount * i.expected_return) as total_expected_return
            FROM users u
            LEFT JOIN investments i ON u.user_id = i.user_id
            GROUP BY u.user_id
            HAVING total_invested > 0
            ORDER BY total_invested DESC
            LIMIT 20
            """,
            (),
            fetch_all=True
        )
        return investors if investors else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على أفضل المستثمرين: {e}")
        return []


async def get_user_rank(user_id: int, category: str):
    """الحصول على ترتيب مستخدم محدد في فئة معينة"""
    try:
        if category == 'wealth':
            query = """
            SELECT COUNT(*) + 1 as rank 
            FROM users 
            WHERE (balance + bank_balance) > (
                SELECT (balance + bank_balance) 
                FROM users 
                WHERE user_id = ?
            )
            """
        elif category == 'bank':
            query = """
            SELECT COUNT(*) + 1 as rank 
            FROM users 
            WHERE bank_balance > (
                SELECT bank_balance 
                FROM users 
                WHERE user_id = ?
            )
            """
        elif category == 'properties':
            query = """
            SELECT COUNT(*) + 1 as rank 
            FROM (
                SELECT user_id, COUNT(*) as property_count
                FROM properties 
                GROUP BY user_id
                HAVING property_count > (
                    SELECT COUNT(*) 
                    FROM properties 
                    WHERE user_id = ?
                )
            )
            """
        elif category == 'investments':
            query = """
            SELECT COUNT(*) + 1 as rank 
            FROM (
                SELECT user_id, SUM(amount) as total_invested
                FROM investments 
                GROUP BY user_id
                HAVING total_invested > (
                    SELECT COALESCE(SUM(amount), 0) 
                    FROM investments 
                    WHERE user_id = ?
                )
            )
            """
        else:
            return None
        
        result = await execute_query(query, (user_id,), fetch_one=True)
        return result['rank'] if result else None
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على ترتيب المستخدم: {e}")
        return None


async def get_user_properties_count(user_id: int):
    """الحصول على عدد عقارات المستخدم"""
    try:
        result = await execute_query(
            "SELECT COUNT(*) as count FROM properties WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        return result['count'] if result else 0
    except Exception as e:
        logging.error(f"خطأ في الحصول على عدد العقارات: {e}")
        return 0


async def get_user_investments_value(user_id: int):
    """الحصول على قيمة استثمارات المستخدم"""
    try:
        result = await execute_query(
            "SELECT SUM(amount) as total FROM investments WHERE user_id = ? AND status = 'active'",
            (user_id,),
            fetch_one=True
        )
        return result['total'] if result and result['total'] else 0
    except Exception as e:
        logging.error(f"خطأ في الحصول على قيمة الاستثمارات: {e}")
        return 0


async def get_weekly_active_users(week_start: datetime):
    """الحصول على المستخدمين الأكثر نشاطاً هذا الأسبوع"""
    try:
        users = await execute_query(
            """
            SELECT u.user_id, u.username, u.first_name, 
                   COUNT(t.id) as transaction_count,
                   SUM(t.amount) as total_activity
            FROM users u
            LEFT JOIN transactions t ON u.user_id = t.from_user_id OR u.user_id = t.to_user_id
            WHERE t.created_at >= ?
            GROUP BY u.user_id
            HAVING transaction_count > 0
            ORDER BY transaction_count DESC, total_activity DESC
            LIMIT 20
            """,
            (week_start.isoformat(),),
            fetch_all=True
        )
        return users if users else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على المستخدمين النشطين: {e}")
        return []


async def get_monthly_top_investors(month_start: datetime):
    """الحصول على أفضل المستثمرين هذا الشهر"""
    try:
        investors = await execute_query(
            """
            SELECT u.user_id, u.username, u.first_name,
                   SUM(i.amount) as total_invested,
                   SUM(i.amount * i.expected_return) as total_return
            FROM users u
            LEFT JOIN investments i ON u.user_id = i.user_id
            WHERE i.created_at >= ?
            GROUP BY u.user_id
            HAVING total_invested > 0
            ORDER BY total_invested DESC
            LIMIT 20
            """,
            (month_start.isoformat(),),
            fetch_all=True
        )
        return investors if investors else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على أفضل المستثمرين الشهريين: {e}")
        return []


async def update_user_statistics(user_id: int, stat_type: str, value: int = 1):
    """تحديث إحصائيات المستخدم"""
    try:
        await execute_query(
            "INSERT INTO stats (user_id, action_type, action_data) VALUES (?, ?, ?)",
            (user_id, stat_type, str(value))
        )
    except Exception as e:
        logging.error(f"خطأ في تحديث الإحصائيات: {e}")


async def get_global_statistics():
    """الحصول على الإحصائيات العامة للبوت"""
    try:
        stats = {}
        
        # عدد المستخدمين
        total_users = await execute_query(
            "SELECT COUNT(*) as count FROM users",
            (),
            fetch_one=True
        )
        stats['total_users'] = total_users['count'] if total_users else 0
        
        # إجمالي الأموال في النظام
        total_money = await execute_query(
            "SELECT SUM(balance + bank_balance) as total FROM users",
            (),
            fetch_one=True
        )
        stats['total_money'] = total_money['total'] if total_money and total_money['total'] else 0
        
        # عدد المعاملات
        total_transactions = await execute_query(
            "SELECT COUNT(*) as count FROM transactions",
            (),
            fetch_one=True
        )
        stats['total_transactions'] = total_transactions['count'] if total_transactions else 0
        
        # عدد العقارات
        total_properties = await execute_query(
            "SELECT COUNT(*) as count FROM properties",
            (),
            fetch_one=True
        )
        stats['total_properties'] = total_properties['count'] if total_properties else 0
        
        # عدد الاستثمارات
        total_investments = await execute_query(
            "SELECT COUNT(*) as count FROM investments WHERE status = 'active'",
            (),
            fetch_one=True
        )
        stats['total_investments'] = total_investments['count'] if total_investments else 0
        
        return stats
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على الإحصائيات العامة: {e}")
        return {}

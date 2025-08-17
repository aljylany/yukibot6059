"""
وحدة لوحة تحكم إدارة المجموعات مع التحليلات المرئية
Group Management Dashboard with Visual Analytics Module
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from config.database import execute_query
from database.operations import get_user
from utils.decorators import admin_required, group_only
from utils.helpers import format_number, format_user_mention
from config.settings import ADMINS


class GroupAnalytics:
    """فئة تحليلات المجموعة"""
    
    @staticmethod
    async def get_member_statistics(chat_id: int) -> Dict:
        """احصائيات الأعضاء"""
        try:
            # إجمالي الأعضاء المسجلين
            total_members = await execute_query(
                "SELECT COUNT(*) FROM users WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # الأعضاء النشطين (آخر 7 أيام)
            week_ago = (datetime.now() - timedelta(days=7)).isoformat()
            active_members = await execute_query(
                "SELECT COUNT(*) FROM users WHERE chat_id = ? AND updated_at > ?",
                (chat_id, week_ago),
                fetch_one=True
            )
            
            # الأعضاء الجدد (آخر 30 يوم)
            month_ago = (datetime.now() - timedelta(days=30)).isoformat()
            new_members = await execute_query(
                "SELECT COUNT(*) FROM users WHERE chat_id = ? AND created_at > ?",
                (chat_id, month_ago),
                fetch_one=True
            )
            
            # توزيع البنوك
            bank_distribution = await execute_query(
                "SELECT bank, COUNT(*) as count FROM users WHERE chat_id = ? AND bank IS NOT NULL GROUP BY bank",
                (chat_id,),
                fetch_all=True
            )
            
            return {
                'total_members': total_members[0] if total_members else 0,
                'active_members': active_members[0] if active_members else 0,
                'new_members': new_members[0] if new_members else 0,
                'bank_distribution': dict(bank_distribution) if bank_distribution else {}
            }
            
        except Exception as e:
            logging.error(f"خطأ في احصائيات الأعضاء: {e}")
            return {}

    @staticmethod
    async def get_financial_statistics(chat_id: int) -> Dict:
        """احصائيات مالية"""
        try:
            # إجمالي الأموال في النظام
            total_money = await execute_query(
                "SELECT SUM(balance) FROM users WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # متوسط الرصيد
            avg_balance = await execute_query(
                "SELECT AVG(balance) FROM users WHERE chat_id = ? AND balance > 0",
                (chat_id,),
                fetch_one=True
            )
            
            # أكبر رصيد
            max_balance = await execute_query(
                "SELECT MAX(balance), username FROM users WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # عدد المعاملات اليومية
            today = datetime.now().date().isoformat()
            daily_transactions = await execute_query(
                "SELECT COUNT(*) FROM transactions WHERE date(created_at) = ?",
                (today,),
                fetch_one=True
            )
            
            # أكثر البنوك استخداماً
            popular_banks = await execute_query(
                """SELECT bank, COUNT(*) as users, SUM(balance) as total_balance 
                   FROM users WHERE chat_id = ? AND bank IS NOT NULL 
                   GROUP BY bank ORDER BY users DESC""",
                (chat_id,),
                fetch_all=True
            )
            
            return {
                'total_money': total_money[0] if total_money and total_money[0] else 0,
                'avg_balance': avg_balance[0] if avg_balance and avg_balance[0] else 0,
                'max_balance': max_balance[0] if max_balance and max_balance[0] else 0,
                'richest_user': max_balance[1] if max_balance and max_balance[1] else "غير محدد",
                'daily_transactions': daily_transactions[0] if daily_transactions else 0,
                'popular_banks': popular_banks if popular_banks else []
            }
            
        except Exception as e:
            logging.error(f"خطأ في الاحصائيات المالية: {e}")
            return {}

    @staticmethod
    async def get_moderation_statistics(chat_id: int) -> Dict:
        """احصائيات الإشراف"""
        try:
            # عدد المحظورين
            banned_count = await execute_query(
                "SELECT COUNT(*) FROM banned_users WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # عدد المكتومين
            muted_count = await execute_query(
                "SELECT COUNT(*) FROM muted_users WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # عدد التحذيرات
            warnings_count = await execute_query(
                "SELECT COUNT(*) FROM user_warnings WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            # الإجراءات الإدارية اليومية
            today = datetime.now().date().isoformat()
            daily_actions = await execute_query(
                """SELECT 
                    (SELECT COUNT(*) FROM banned_users WHERE chat_id = ? AND date(banned_at) = ?) +
                    (SELECT COUNT(*) FROM muted_users WHERE chat_id = ? AND date(muted_at) = ?) +
                    (SELECT COUNT(*) FROM user_warnings WHERE chat_id = ? AND date(warned_at) = ?)""",
                (chat_id, today, chat_id, today, chat_id, today),
                fetch_one=True
            )
            
            # أكثر المشرفين نشاطاً
            active_moderators = await execute_query(
                """SELECT warned_by as mod_id, COUNT(*) as actions
                   FROM (
                       SELECT banned_by as warned_by FROM banned_users WHERE chat_id = ?
                       UNION ALL
                       SELECT muted_by FROM muted_users WHERE chat_id = ?
                       UNION ALL  
                       SELECT warned_by FROM user_warnings WHERE chat_id = ?
                   ) GROUP BY warned_by ORDER BY actions DESC LIMIT 5""",
                (chat_id, chat_id, chat_id),
                fetch_all=True
            )
            
            return {
                'banned_count': banned_count[0] if banned_count else 0,
                'muted_count': muted_count[0] if muted_count else 0,
                'warnings_count': warnings_count[0] if warnings_count else 0,
                'daily_actions': daily_actions[0] if daily_actions else 0,
                'active_moderators': active_moderators if active_moderators else []
            }
            
        except Exception as e:
            logging.error(f"خطأ في احصائيات الإشراف: {e}")
            return {}

    @staticmethod
    async def get_activity_trends(chat_id: int, days: int = 7) -> Dict:
        """اتجاهات النشاط"""
        try:
            trends = {}
            
            for i in range(days):
                date = (datetime.now() - timedelta(days=i)).date().isoformat()
                
                # نشاط يومي
                daily_activity = await execute_query(
                    "SELECT COUNT(*) FROM users WHERE chat_id = ? AND date(updated_at) = ?",
                    (chat_id, date),
                    fetch_one=True
                )
                
                # معاملات يومية
                daily_transactions = await execute_query(
                    "SELECT COUNT(*) FROM transactions WHERE date(created_at) = ?",
                    (date,),
                    fetch_one=True
                )
                
                trends[date] = {
                    'active_users': daily_activity[0] if daily_activity else 0,
                    'transactions': daily_transactions[0] if daily_transactions else 0
                }
            
            return trends
            
        except Exception as e:
            logging.error(f"خطأ في اتجاهات النشاط: {e}")
            return {}


class DashboardGenerator:
    """مولد لوحة التحكم"""
    
    @staticmethod
    def create_text_chart(data: List[Tuple], title: str, max_width: int = 20) -> str:
        """إنشاء مخطط نصي"""
        if not data:
            return f"📊 **{title}**\n\n❌ لا توجد بيانات"
        
        chart = f"📊 **{title}**\n\n"
        max_value = max(item[1] for item in data)
        
        for item, value in data:
            if max_value > 0:
                bar_length = int((value / max_value) * max_width)
                bar = "█" * bar_length + "░" * (max_width - bar_length)
                percentage = (value / max_value) * 100
                chart += f"{item}: {bar} {value} ({percentage:.1f}%)\n"
            else:
                chart += f"{item}: ░" * max_width + f" {value}\n"
        
        return chart

    @staticmethod
    def create_progress_bar(current: int, total: int, width: int = 20) -> str:
        """إنشاء شريط تقدم"""
        if total == 0:
            return "░" * width + " 0%"
        
        percentage = (current / total) * 100
        filled = int((current / total) * width)
        bar = "█" * filled + "░" * (width - filled)
        return f"{bar} {percentage:.1f}%"

    @staticmethod
    async def generate_overview_dashboard(chat_id: int) -> str:
        """توليد لوحة التحكم العامة"""
        try:
            analytics = GroupAnalytics()
            
            # جمع الإحصائيات
            member_stats = await analytics.get_member_statistics(chat_id)
            financial_stats = await analytics.get_financial_statistics(chat_id)
            moderation_stats = await analytics.get_moderation_statistics(chat_id)
            
            dashboard = "🏛️ **لوحة تحكم إدارة المجموعة**\n"
            dashboard += "═" * 35 + "\n\n"
            
            # إحصائيات الأعضاء
            dashboard += "👥 **إحصائيات الأعضاء:**\n"
            dashboard += f"📊 إجمالي الأعضاء: {format_number(member_stats.get('total_members', 0))}\n"
            dashboard += f"🔥 النشطين (7 أيام): {format_number(member_stats.get('active_members', 0))}\n"
            dashboard += f"🆕 الجدد (30 يوم): {format_number(member_stats.get('new_members', 0))}\n"
            
            if member_stats.get('total_members', 0) > 0:
                activity_rate = (member_stats.get('active_members', 0) / member_stats.get('total_members', 1)) * 100
                dashboard += f"📈 معدل النشاط: {activity_rate:.1f}%\n"
            
            dashboard += "\n"
            
            # إحصائيات مالية
            dashboard += "💰 **الإحصائيات المالية:**\n"
            dashboard += f"💵 إجمالي الأموال: {format_number(financial_stats.get('total_money', 0))}$\n"
            dashboard += f"📊 متوسط الرصيد: {format_number(financial_stats.get('avg_balance', 0))}$\n"
            dashboard += f"🏆 أكبر رصيد: {format_number(financial_stats.get('max_balance', 0))}$\n"
            dashboard += f"👑 الأغنى: @{financial_stats.get('richest_user', 'غير محدد')}\n"
            dashboard += f"🔄 معاملات اليوم: {format_number(financial_stats.get('daily_transactions', 0))}\n\n"
            
            # إحصائيات الإشراف
            dashboard += "🛡️ **إحصائيات الإشراف:**\n"
            dashboard += f"🚫 المحظورين: {format_number(moderation_stats.get('banned_count', 0))}\n"
            dashboard += f"🔇 المكتومين: {format_number(moderation_stats.get('muted_count', 0))}\n"
            dashboard += f"⚠️ التحذيرات: {format_number(moderation_stats.get('warnings_count', 0))}\n"
            dashboard += f"⚡ إجراءات اليوم: {format_number(moderation_stats.get('daily_actions', 0))}\n\n"
            
            # توزيع البنوك
            bank_dist = member_stats.get('bank_distribution', {})
            if bank_dist:
                dashboard += DashboardGenerator.create_text_chart(
                    list(bank_dist.items()),
                    "توزيع البنوك"
                ) + "\n\n"
            
            dashboard += f"🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
            dashboard += "═" * 35
            
            return dashboard
            
        except Exception as e:
            logging.error(f"خطأ في توليد لوحة التحكم: {e}")
            return "❌ حدث خطأ في توليد لوحة التحكم"

    @staticmethod
    async def generate_financial_dashboard(chat_id: int) -> str:
        """توليد لوحة التحكم المالية"""
        try:
            analytics = GroupAnalytics()
            financial_stats = await analytics.get_financial_statistics(chat_id)
            
            dashboard = "💰 **لوحة التحكم المالية**\n"
            dashboard += "═" * 30 + "\n\n"
            
            # نظرة عامة مالية
            total_money = financial_stats.get('total_money', 0)
            avg_balance = financial_stats.get('avg_balance', 0)
            
            dashboard += "📈 **النظرة العامة:**\n"
            dashboard += f"💵 إجمالي السيولة: {format_number(total_money)}$\n"
            dashboard += f"📊 متوسط الرصيد: {format_number(avg_balance)}$\n"
            dashboard += f"🏆 أعلى رصيد: {format_number(financial_stats.get('max_balance', 0))}$\n\n"
            
            # البنوك الشائعة
            popular_banks = financial_stats.get('popular_banks', [])
            if popular_banks:
                dashboard += "🏦 **أداء البنوك:**\n"
                for bank_data in popular_banks[:5]:
                    bank_name = bank_data[0]
                    users_count = bank_data[1]
                    bank_total = bank_data[2] if len(bank_data) > 2 else 0
                    dashboard += f"• {bank_name}: {users_count} مستخدم - {format_number(bank_total)}$\n"
                dashboard += "\n"
            
            # مؤشرات الأداء
            dashboard += "📊 **مؤشرات الأداء:**\n"
            dashboard += f"🔄 معاملات اليوم: {financial_stats.get('daily_transactions', 0)}\n"
            
            if total_money > 0 and avg_balance > 0:
                economy_health = min((avg_balance / 10000) * 100, 100)  # Health based on average balance
                dashboard += f"💚 صحة الاقتصاد: {economy_health:.1f}%\n"
                dashboard += DashboardGenerator.create_progress_bar(int(economy_health), 100) + "\n"
            
            dashboard += f"\n🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            return dashboard
            
        except Exception as e:
            logging.error(f"خطأ في اللوحة المالية: {e}")
            return "❌ حدث خطأ في توليد اللوحة المالية"

    @staticmethod
    async def generate_activity_dashboard(chat_id: int) -> str:
        """توليد لوحة نشاط المجموعة"""
        try:
            analytics = GroupAnalytics()
            activity_trends = await analytics.get_activity_trends(chat_id, 7)
            
            dashboard = "📈 **لوحة نشاط المجموعة**\n"
            dashboard += "═" * 25 + "\n\n"
            
            if activity_trends:
                dashboard += "📅 **النشاط الأسبوعي:**\n"
                dates = sorted(activity_trends.keys(), reverse=True)
                
                # إنشاء مخطط النشاط
                max_activity = max(activity_trends[date]['active_users'] for date in dates)
                
                for date in dates:
                    data = activity_trends[date]
                    active_users = data['active_users']
                    transactions = data['transactions']
                    
                    # تحويل التاريخ لصيغة أجمل
                    date_obj = datetime.strptime(date, '%Y-%m-%d')
                    day_name = date_obj.strftime('%A')
                    formatted_date = date_obj.strftime('%m-%d')
                    
                    # شريط النشاط
                    if max_activity > 0:
                        bar_length = int((active_users / max_activity) * 15)
                        bar = "█" * bar_length + "░" * (15 - bar_length)
                    else:
                        bar = "░" * 15
                    
                    dashboard += f"{formatted_date}: {bar} {active_users} مستخدم, {transactions} معاملة\n"
                
                dashboard += "\n"
                
                # إحصائيات الاتجاه
                total_week_activity = sum(activity_trends[date]['active_users'] for date in dates)
                total_week_transactions = sum(activity_trends[date]['transactions'] for date in dates)
                
                dashboard += "📊 **ملخص الأسبوع:**\n"
                dashboard += f"👥 إجمالي النشطين: {format_number(total_week_activity)}\n"
                dashboard += f"💸 إجمالي المعاملات: {format_number(total_week_transactions)}\n"
                dashboard += f"📈 معدل النشاط اليومي: {total_week_activity/7:.1f}\n"
            
            dashboard += f"\n🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
            
            return dashboard
            
        except Exception as e:
            logging.error(f"خطأ في لوحة النشاط: {e}")
            return "❌ حدث خطأ في توليد لوحة النشاط"


async def show_main_dashboard(message: Message):
    """عرض لوحة التحكم الرئيسية"""
    try:
        # التحقق من الصلاحيات
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        # توليد لوحة التحكم
        dashboard_text = await DashboardGenerator.generate_overview_dashboard(message.chat.id)
        
        await message.reply(dashboard_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض لوحة التحكم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض لوحة التحكم")


async def show_financial_dashboard(message: Message):
    """عرض لوحة التحكم المالية"""
    try:
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        dashboard_text = await DashboardGenerator.generate_financial_dashboard(message.chat.id)
        await message.reply(dashboard_text)
        
    except Exception as e:
        logging.error(f"خطأ في اللوحة المالية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض اللوحة المالية")


async def show_activity_dashboard(message: Message):
    """عرض لوحة نشاط المجموعة"""
    try:
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        dashboard_text = await DashboardGenerator.generate_activity_dashboard(message.chat.id)
        await message.reply(dashboard_text)
        
    except Exception as e:
        logging.error(f"خطأ في لوحة النشاط: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض لوحة النشاط")


async def show_moderation_stats(message: Message):
    """عرض إحصائيات الإشراف"""
    try:
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        analytics = GroupAnalytics()
        moderation_stats = await analytics.get_moderation_statistics(message.chat.id)
        
        stats_text = "🛡️ **إحصائيات الإشراف**\n"
        stats_text += "═" * 20 + "\n\n"
        
        stats_text += f"🚫 المحظورين: {format_number(moderation_stats.get('banned_count', 0))}\n"
        stats_text += f"🔇 المكتومين: {format_number(moderation_stats.get('muted_count', 0))}\n"
        stats_text += f"⚠️ التحذيرات: {format_number(moderation_stats.get('warnings_count', 0))}\n"
        stats_text += f"⚡ إجراءات اليوم: {format_number(moderation_stats.get('daily_actions', 0))}\n\n"
        
        # أكثر المشرفين نشاطاً
        active_mods = moderation_stats.get('active_moderators', [])
        if active_mods:
            stats_text += "👮 **أكثر المشرفين نشاطاً:**\n"
            for i, (mod_id, actions) in enumerate(active_mods[:5], 1):
                user = await get_user(mod_id)
                username = user.get('username', f'مستخدم#{mod_id}') if user else f'مستخدم#{mod_id}'
                stats_text += f"{i}. @{username}: {actions} إجراء\n"
        
        stats_text += f"\n🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        await message.reply(stats_text)
        
    except Exception as e:
        logging.error(f"خطأ في إحصائيات الإشراف: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض إحصائيات الإشراف")


async def show_comprehensive_report(message: Message):
    """عرض التقرير الشامل للمجموعة"""
    try:
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        chat_id = message.chat.id
        
        report = "📊 **التقرير الشامل للمجموعة**\n"
        report += "═" * 40 + "\n\n"
        
        # الحصول على الإحصائيات
        analytics = GroupAnalytics()
        member_stats = await analytics.get_member_statistics(chat_id)
        financial_stats = await analytics.get_financial_statistics(chat_id)
        moderation_stats = await analytics.get_moderation_statistics(chat_id)
        
        # 1. ملخص عام
        report += "📋 **الملخص العام:**\n"
        report += f"👥 إجمالي الأعضاء: {format_number(member_stats.get('total_members', 0))}\n"
        report += f"🔥 النشطين (7 أيام): {format_number(member_stats.get('active_members', 0))}\n"
        report += f"🆕 الجدد (30 يوم): {format_number(member_stats.get('new_members', 0))}\n"
        report += f"💰 إجمالي الأموال: {format_number(financial_stats.get('total_money', 0))}$\n"
        report += f"🔄 معاملات اليوم: {financial_stats.get('daily_transactions', 0)}\n\n"
        
        # 2. معدلات الأداء
        total_members = member_stats.get('total_members', 0)
        active_members = member_stats.get('active_members', 0)
        
        if total_members > 0:
            activity_rate = (active_members / total_members) * 100
            report += f"📈 **معدل النشاط:** {activity_rate:.1f}%\n"
            
            # شريط النشاط
            from modules.visual_charts import TextChartGenerator
            activity_bar = TextChartGenerator.create_progress_bar(int(activity_rate), 100)
            report += f"   {activity_bar}\n\n"
        
        # 3. توزيع البنوك
        bank_dist = member_stats.get('bank_distribution', {})
        if bank_dist:
            report += "🏦 **توزيع البنوك:**\n"
            for bank, count in sorted(bank_dist.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_members) * 100 if total_members > 0 else 0
                report += f"• {bank}: {count} مستخدم ({percentage:.1f}%)\n"
            report += "\n"
        
        # 4. إحصائيات الإشراف
        report += "🛡️ **إحصائيات الإشراف:**\n"
        report += f"🚫 المحظورين: {moderation_stats.get('banned_count', 0)}\n"
        report += f"🔇 المكتومين: {moderation_stats.get('muted_count', 0)}\n"
        report += f"⚠️ التحذيرات: {moderation_stats.get('warnings_count', 0)}\n"
        report += f"⚡ إجراءات اليوم: {moderation_stats.get('daily_actions', 0)}\n\n"
        
        # 5. أهم البنوك
        popular_banks = financial_stats.get('popular_banks', [])
        if popular_banks:
            report += "💳 **أداء البنوك:**\n"
            for i, bank_data in enumerate(popular_banks[:3], 1):
                bank_name = bank_data[0]
                users_count = bank_data[1]
                bank_total = bank_data[2] if len(bank_data) > 2 else 0
                report += f"{i}. {bank_name}: {users_count} مستخدم - {format_number(bank_total)}$\n"
            report += "\n"
        
        report += f"🕒 تم إنشاء التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        report += "═" * 40
        
        await message.reply(report)
        
    except Exception as e:
        logging.error(f"خطأ في التقرير الشامل: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء التقرير الشامل")


async def show_health_dashboard(message: Message):
    """عرض لوحة صحة المجموعة"""
    try:
        from modules.admin_management import has_permission
        if not await has_permission(message.from_user.id, message.chat.id, "ادمن"):
            await message.reply("❌ هذا الأمر للمشرفين فقط")
            return
        
        from modules.visual_charts import TextChartGenerator
        
        chat_id = message.chat.id
        
        dashboard = "🏥 **لوحة صحة المجموعة**\n"
        dashboard += "═" * 30 + "\n\n"
        
        # حساب عوامل الصحة
        analytics = GroupAnalytics()
        member_stats = await analytics.get_member_statistics(chat_id)
        financial_stats = await analytics.get_financial_statistics(chat_id)
        moderation_stats = await analytics.get_moderation_statistics(chat_id)
        
        # حساب نقاط الصحة
        health_scores = {}
        
        # 1. معدل النشاط (40%)
        total_members = member_stats.get('total_members', 0)
        active_members = member_stats.get('active_members', 0)
        activity_rate = (active_members / total_members * 100) if total_members > 0 else 0
        health_scores['activity'] = min(activity_rate, 100) * 0.4
        
        # 2. النمو (30%)
        new_members = member_stats.get('new_members', 0)
        growth_score = min(new_members * 10, 100)  # كل عضو جديد = 10 نقاط
        health_scores['growth'] = growth_score * 0.3
        
        # 3. النشاط المالي (20%)
        daily_transactions = financial_stats.get('daily_transactions', 0)
        financial_score = min(daily_transactions * 5, 100)  # كل معاملة = 5 نقاط
        health_scores['financial'] = financial_score * 0.2
        
        # 4. جودة الإشراف (10%)
        daily_actions = moderation_stats.get('daily_actions', 0)
        moderation_score = max(0, 100 - daily_actions * 10)  # كلما قل الإشراف كان أفضل
        health_scores['moderation'] = moderation_score * 0.1
        
        # النتيجة الإجمالية
        total_score = sum(health_scores.values())
        
        # تصنيف الصحة
        if total_score >= 80:
            health_grade = "ممتاز"
            health_color = "🟢"
        elif total_score >= 60:
            health_grade = "جيد"
            health_color = "🟡"
        elif total_score >= 40:
            health_grade = "متوسط"
            health_color = "🟠"
        else:
            health_grade = "ضعيف"
            health_color = "🔴"
        
        # عرض النتيجة
        dashboard += f"🎯 **النتيجة الإجمالية:** {health_color} {total_score:.1f}%\n"
        dashboard += f"📊 **التصنيف:** {health_grade}\n\n"
        
        # مقياس الصحة
        health_gauge = TextChartGenerator.create_gauge_meter(
            int(total_score), 100, "صحة المجموعة"
        )
        dashboard += health_gauge + "\n\n"
        
        # تفصيل العوامل
        dashboard += "📈 **تفصيل العوامل:**\n"
        dashboard += f"🔥 النشاط: {health_scores['activity']:.1f}/40\n"
        dashboard += f"📈 النمو: {health_scores['growth']:.1f}/30\n"
        dashboard += f"💰 المالي: {health_scores['financial']:.1f}/20\n"
        dashboard += f"🛡️ الإشراف: {health_scores['moderation']:.1f}/10\n\n"
        
        # توصيات
        dashboard += "💡 **توصيات:**\n"
        if health_scores['activity'] < 20:
            dashboard += "• شجع المزيد من التفاعل\n"
        if health_scores['growth'] < 15:
            dashboard += "• ركز على جذب أعضاء جدد\n"
        if health_scores['financial'] < 10:
            dashboard += "• حفز النشاط الاقتصادي\n"
        if health_scores['moderation'] < 8:
            dashboard += "• راجع قوانين المجموعة\n"
        
        if total_score > 80:
            dashboard += "🎉 المجموعة في حالة ممتازة!\n"
        
        dashboard += f"\n🕒 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        await message.reply(dashboard)
        
    except Exception as e:
        logging.error(f"خطأ في لوحة الصحة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض لوحة صحة المجموعة")
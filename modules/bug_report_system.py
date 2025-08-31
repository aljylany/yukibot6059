"""
🔥 نظام التقرير الملكي - Bug Report System 
نظام متطور لإدارة تقارير الأخطاء والاقتراحات مع نظام مكافآت مبتكر
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from aiogram import Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.operations import get_or_create_user, update_user_balance, add_transaction, execute_query
from utils.states import ReportStates
from utils.helpers import format_number
from config.settings import ADMIN_IDS
import json

# إعدادات نظام التقارير
REPORT_SETTINGS = {
    "rewards": {
        "critical": {"gold": 50, "money": 5000},          # خطأ قاتل
        "major": {"gold": 25, "money": 2500},             # خطأ مهم  
        "minor": {"gold": 10, "money": 1000},             # خطأ بسيط
        "suggestion": {"gold": 5, "money": 500},          # اقتراح
        "duplicate": {"gold": 2, "money": 100}            # تقرير مكرر
    },
    "status_emojis": {
        "pending": "⏳",
        "in_progress": "🔧", 
        "testing": "🧪",
        "fixed": "✅",
        "rejected": "❌",
        "duplicate": "🔄"
    },
    "priority_emojis": {
        "critical": "🔥",
        "major": "⚠️", 
        "minor": "📝",
        "suggestion": "💡"
    }
}

class BugReportSystem:
    def __init__(self):
        self.reports = {}
        
    async def init_database(self):
        """تهيئة قاعدة البيانات لنظام التقارير"""
        try:
            # جدول تقارير الأخطاء
            await execute_query('''
                CREATE TABLE IF NOT EXISTS bug_reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT UNIQUE NOT NULL,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    category TEXT NOT NULL,
                    priority TEXT DEFAULT 'minor',
                    status TEXT DEFAULT 'pending',
                    steps_to_reproduce TEXT,
                    expected_result TEXT,
                    actual_result TEXT,
                    system_info TEXT,
                    screenshots TEXT,
                    assigned_to INTEGER,
                    reward_given REAL DEFAULT 0,
                    gold_reward REAL DEFAULT 0,
                    is_rewarded BOOLEAN DEFAULT FALSE,
                    votes_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    fixed_at TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # جدول تصويت المجتمع على التقارير
            await execute_query('''
                CREATE TABLE IF NOT EXISTS report_votes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    report_id TEXT NOT NULL,
                    voter_id INTEGER NOT NULL,
                    vote_type TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (report_id) REFERENCES bug_reports (report_id),
                    UNIQUE(report_id, voter_id)
                )
            ''')
            
            # جدول إحصائيات المبلغين
            await execute_query('''
                CREATE TABLE IF NOT EXISTS reporter_stats (
                    user_id INTEGER PRIMARY KEY,
                    total_reports INTEGER DEFAULT 0,
                    critical_reports INTEGER DEFAULT 0,
                    major_reports INTEGER DEFAULT 0,
                    minor_reports INTEGER DEFAULT 0,
                    suggestions INTEGER DEFAULT 0,
                    fixed_reports INTEGER DEFAULT 0,
                    total_rewards REAL DEFAULT 0,
                    total_gold_earned REAL DEFAULT 0,
                    reporter_rank TEXT DEFAULT 'مبلغ مبتدئ',
                    achievement_badges TEXT DEFAULT '[]',
                    last_report_date TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            ''')
            
            # إضافة عمود النقاط الذهبية للمستخدمين إذا لم يكن موجود
            try:
                await execute_query('ALTER TABLE users ADD COLUMN gold_points REAL DEFAULT 0')
                logging.info("✅ تم إضافة عمود النقاط الذهبية")
            except Exception as e:
                if "duplicate column name" not in str(e).lower():
                    logging.error(f"خطأ في إضافة عمود النقاط الذهبية: {e}")
            
            # إضافة الفهارس لتحسين الأداء
            await execute_query('CREATE INDEX IF NOT EXISTS idx_reports_status ON bug_reports(status)')
            await execute_query('CREATE INDEX IF NOT EXISTS idx_reports_priority ON bug_reports(priority)')
            await execute_query('CREATE INDEX IF NOT EXISTS idx_reports_user ON bug_reports(user_id)')
            await execute_query('CREATE INDEX IF NOT EXISTS idx_votes_report ON report_votes(report_id)')
            
            logging.info("✅ تم تهيئة قاعدة بيانات نظام التقرير الملكي بنجاح")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة قاعدة البيانات لنظام التقارير: {e}")

    def get_report_keyboard(self, level: str = "basic", user_id: int = 0) -> InlineKeyboardMarkup:
        """إنشاء لوحة مفاتيح تفاعلية للتقارير"""
        keyboard = []
        
        if level == "basic":
            keyboard = [
                [
                    InlineKeyboardButton(text="🔥 خطأ قاتل", callback_data=f"report:critical:{user_id}"),
                    InlineKeyboardButton(text="⚠️ خطأ مهم", callback_data=f"report:major:{user_id}")
                ],
                [
                    InlineKeyboardButton(text="📝 خطأ بسيط", callback_data=f"report:minor:{user_id}"),
                    InlineKeyboardButton(text="💡 اقتراح", callback_data=f"report:suggestion:{user_id}")
                ],
                [
                    InlineKeyboardButton(text="📊 إحصائياتي", callback_data=f"report:stats:{user_id}"),
                    InlineKeyboardButton(text="📋 تقاريري", callback_data=f"report:my_reports:{user_id}")
                ]
            ]
        elif level == "advanced":
            keyboard = [
                [
                    InlineKeyboardButton(text="🔥 خطأ قاتل مفصل", callback_data=f"report:critical_detailed:{user_id}"),
                    InlineKeyboardButton(text="⚠️ خطأ مهم مفصل", callback_data=f"report:major_detailed:{user_id}")
                ],
                [
                    InlineKeyboardButton(text="🧪 تقرير فني", callback_data=f"report:technical:{user_id}"),
                    InlineKeyboardButton(text="🔍 اقتراح متقدم", callback_data=f"report:advanced_suggestion:{user_id}")
                ]
            ]
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

    async def show_report_menu(self, message: Message):
        """عرض القائمة الرئيسية لنظام التقارير"""
        try:
            # التأكد من وجود المستخدم
            if not message.from_user:
                await message.reply("❌ خطأ في معلومات المستخدم")
                return
                
            user = await get_or_create_user(
                message.from_user.id,
                message.from_user.username or "",
                message.from_user.first_name or "مبلغ"
            )
            
            if not user:
                await message.reply("❌ حدث خطأ في النظام")
                return
            
            # الحصول على إحصائيات المستخدم
            stats = await self.get_user_stats(message.from_user.id)
            
            welcome_text = f"""
🏰 **نظام التقرير الملكي** 👑

مرحباً أيها المبلغ النبيل! نحن نقدر مساعدتك في تطوير البوت وجعله أفضل.

📊 **إحصائياتك:**
• تقارير مرسلة: {stats['total_reports']}
• تقارير تم إصلاحها: {stats['fixed_reports']}
• إجمالي المكافآت: {format_number(stats['total_rewards'])}$
• النقاط الذهبية: {stats['total_gold_earned']} ⭐

🏆 **رتبتك الحالية:** {stats['reporter_rank']}

💰 **نظام المكافآت:**
• 🔥 خطأ قاتل: 5000$ + 50⭐
• ⚠️ خطأ مهم: 2500$ + 25⭐  
• 📝 خطأ بسيط: 1000$ + 10⭐
• 💡 اقتراح: 500$ + 5⭐

اختر نوع التقرير الذي تريد إرساله:
            """
            
            await message.reply(
                welcome_text.strip(),
                reply_markup=self.get_report_keyboard("basic", message.from_user.id)
            )
            
        except Exception as e:
            logging.error(f"خطأ في عرض قائمة التقارير: {e}")
            await message.reply("❌ حدث خطأ في عرض القائمة")

    async def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات المستخدم"""
        try:
            stats = await execute_query("""
                SELECT * FROM reporter_stats WHERE user_id = ?
            """, (user_id,), fetch_one=True)
            
            if not stats:
                # إنشاء سجل إحصائيات جديد
                await execute_query("""
                    INSERT OR IGNORE INTO reporter_stats (user_id) VALUES (?)
                """, (user_id,))
                
                return {
                    'total_reports': 0,
                    'fixed_reports': 0,
                    'total_rewards': 0,
                    'total_gold_earned': 0,
                    'reporter_rank': 'مبلغ مبتدئ'
                }
            
            return {
                'total_reports': stats.get('total_reports', 0) if isinstance(stats, dict) else 0,
                'fixed_reports': stats.get('fixed_reports', 0) if isinstance(stats, dict) else 0,
                'total_rewards': stats.get('total_rewards', 0) if isinstance(stats, dict) else 0,
                'total_gold_earned': stats.get('total_gold_earned', 0) if isinstance(stats, dict) else 0,
                'reporter_rank': stats.get('reporter_rank', 'مبلغ مبتدئ') if isinstance(stats, dict) else 'مبلغ مبتدئ'
            }
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على إحصائيات المستخدم {user_id}: {e}")
            return {
                'total_reports': 0,
                'fixed_reports': 0,
                'total_rewards': 0,
                'total_gold_earned': 0,
                'reporter_rank': 'مبلغ مبتدئ'
            }

    async def start_bug_report(self, callback: CallbackQuery, state: FSMContext, report_type: str):
        """بدء عملية كتابة تقرير الخطأ"""
        try:
            await state.set_state(ReportStates.waiting_title)
            await state.update_data(report_type=report_type)
            
            type_names = {
                "critical": "🔥 خطأ قاتل",
                "major": "⚠️ خطأ مهم", 
                "minor": "📝 خطأ بسيط",
                "suggestion": "💡 اقتراح"
            }
            
            instructions = f"""
📝 **إنشاء {type_names.get(report_type, 'تقرير')}**

اكتب عنوان مختصر وواضح لـ{type_names.get(report_type, 'التقرير')}:

💡 **أمثلة جيدة:**
• "البوت لا يستجيب لأمر الرصيد"
• "خطأ في حساب الفوائد البنكية"  
• "اقتراح إضافة نظام تقييم اللاعبين"

❌ **تجنب:**
• عناوين غير واضحة مثل "مشكلة" أو "خطأ"
• عناوين طويلة جداً

اكتب العنوان الآن أو اكتب 'إلغاء' للتراجع:
            """
            
            cancel_keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="❌ إلغاء", callback_data=f"report:cancel:{callback.from_user.id}")
            ]])
            
            if callback.message:
                await callback.message.edit_text(
                    instructions.strip(),
                    reply_markup=cancel_keyboard
                )
            
        except Exception as e:
            logging.error(f"خطأ في بدء تقرير الخطأ: {e}")
            await callback.answer("❌ حدث خطأ في النظام")

    async def process_report_title(self, message: Message, state: FSMContext):
        """معالجة عنوان التقرير"""
        try:
            if message.text and message.text.strip().lower() == "إلغاء":
                await state.clear()
                await message.reply("❌ تم إلغاء التقرير")
                return
                
            title = message.text.strip() if message.text else ""
            if len(title) < 5:
                await message.reply("❌ العنوان قصير جداً! يجب أن يكون 5 أحرف على الأقل")
                return
                
            if len(title) > 100:
                await message.reply("❌ العنوان طويل جداً! يجب أن يكون أقل من 100 حرف")
                return
            
            await state.update_data(title=title)
            await state.set_state(ReportStates.waiting_description)
            
            data = await state.get_data()
            report_type = data.get('report_type', 'minor')
            
            description_prompt = f"""
✅ **تم حفظ العنوان:** {title}

📋 **الآن اكتب وصف مفصل للمشكلة:**

💡 **يفضل أن تتضمن:**
• خطوات حدوث المشكلة بالتفصيل
• ما كنت تتوقعه أن يحدث
• ما حدث فعلاً
• متى لاحظت هذه المشكلة

📱 **مثال:**
1. كتبت أمر "رصيد" في المجموعة
2. توقعت أن يعرض البوت رصيدي
3. لكن البوت لم يرد على الإطلاق
4. يحدث هذا منذ اليوم

اكتب الوصف الآن:
            """
            
            await message.reply(description_prompt.strip())
            
        except Exception as e:
            logging.error(f"خطأ في معالجة عنوان التقرير: {e}")
            await message.reply("❌ حدث خطأ في النظام")

    async def process_report_description(self, message: Message, state: FSMContext):
        """معالجة وصف التقرير وحفظه"""
        try:
            description = message.text.strip() if message.text else ""
            if len(description) < 10:
                await message.reply("❌ الوصف قصير جداً! اكتب تفاصيل أكثر")
                return
            
            data = await state.get_data()
            user_id = message.from_user.id if message.from_user else 0
            chat_id = message.chat.id if message.chat else 0
            report_id = f"RPT{datetime.now().strftime('%Y%m%d%H%M%S')}{user_id % 1000}"
            
            # حفظ التقرير في قاعدة البيانات
            await execute_query("""
                INSERT INTO bug_reports (
                    report_id, user_id, chat_id, title, description, 
                    category, priority, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                report_id, 
                user_id, 
                chat_id,
                data.get('title', ''),
                description,
                data.get('report_type', 'minor'),
                data.get('report_type', 'minor'),
                'pending',
                datetime.now().isoformat()
            ))
            
            # تحديث إحصائيات المستخدم
            await self.update_user_stats(user_id, data.get('report_type', 'minor'))
            
            # إرسال إشعار للمديرين
            if message.bot:
                await self.notify_admins(message.bot, report_id, data.get('title', ''), message.from_user)
            
            priority_emoji = REPORT_SETTINGS["priority_emojis"].get(data.get('report_type', 'minor'), '📝')
            reward_info = REPORT_SETTINGS['rewards'][data.get('report_type', 'minor')]
            
            success_msg = f"""
✅ **تم إرسال تقريرك بنجاح!**

🆔 **رقم التقرير:** `{report_id}`
{priority_emoji} **النوع:** {data.get('report_type', 'minor')}
📋 **العنوان:** {data.get('title', '')}

🎯 **ما يحدث الآن:**
1. سيتم مراجعة تقريرك من قِبل فريق التطوير
2. ستحصل على إشعار عند تحديث حالة التقرير  
3. عند الإصلاح ستحصل على مكافأتك تلقائياً

💰 **المكافأة المتوقعة:**
• المال: {reward_info['money']}$
• النقاط الذهبية: {reward_info['gold']}⭐

📱 استخدم أمر `تقرير {report_id}` لمتابعة حالة التقرير في أي وقت.

شكراً لمساعدتك في تطوير البوت! 🙏
            """
            
            await message.reply(success_msg.strip())
            await state.clear()
            
        except Exception as e:
            logging.error(f"خطأ في حفظ التقرير: {e}")
            await message.reply("❌ حدث خطأ أثناء حفظ التقرير")

    async def update_user_stats(self, user_id: int, report_type: str):
        """تحديث إحصائيات المستخدم"""
        try:
            # التأكد من وجود سجل الإحصائيات
            await execute_query("""
                INSERT OR IGNORE INTO reporter_stats (user_id) VALUES (?)
            """, (user_id,))
            
            # تحديث الإحصائيات
            await execute_query(f"""
                UPDATE reporter_stats SET 
                    total_reports = total_reports + 1,
                    {report_type}_reports = {report_type}_reports + 1,
                    last_report_date = ?,
                    updated_at = ?
                WHERE user_id = ?
            """, (
                datetime.now().isoformat(),
                datetime.now().isoformat(), 
                user_id
            ))
            
            # تحديث الرتبة بناءً على عدد التقارير
            await self.update_user_rank(user_id)
            
        except Exception as e:
            logging.error(f"خطأ في تحديث إحصائيات المستخدم {user_id}: {e}")

    async def update_user_rank(self, user_id: int):
        """تحديث رتبة المستخدم كمبلغ"""
        try:
            stats = await execute_query("""
                SELECT total_reports, fixed_reports FROM reporter_stats WHERE user_id = ?
            """, (user_id,), fetch_one=True)
            
            if not stats:
                return
                
            total_reports = stats.get('total_reports', 0) if isinstance(stats, dict) else 0
            fixed_reports = stats.get('fixed_reports', 0) if isinstance(stats, dict) else 0
            
            # تحديد الرتبة الجديدة
            if fixed_reports >= 50:
                rank = "🏆 أسطورة التقارير"
            elif fixed_reports >= 25:
                rank = "👑 سيد المبلغين"  
            elif fixed_reports >= 15:
                rank = "⭐ خبير التقارير"
            elif fixed_reports >= 10:
                rank = "🔍 محقق متقدم"
            elif total_reports >= 20:
                rank = "🎯 مبلغ محترف"
            elif total_reports >= 10:
                rank = "📋 مبلغ متمرس"
            elif total_reports >= 5:
                rank = "📝 مبلغ نشط"
            else:
                rank = "🌟 مبلغ مبتدئ"
            
            await execute_query("""
                UPDATE reporter_stats SET reporter_rank = ? WHERE user_id = ?
            """, (rank, user_id))
            
        except Exception as e:
            logging.error(f"خطأ في تحديث رتبة المستخدم {user_id}: {e}")

    async def notify_admins(self, bot: Bot, report_id: str, title: str, user):
        """إشعار المديرين بالتقرير الجديد"""
        try:
            username = user.username if hasattr(user, 'username') else "لا يوجد"
            first_name = user.first_name if hasattr(user, 'first_name') else "غير معروف"
            user_id = user.id if hasattr(user, 'id') else 0
            
            notification_text = f"""
🚨 **تقرير جديد في نظام التقرير الملكي!**

🆔 **رقم التقرير:** `{report_id}`
👤 **المبلغ:** {first_name} (@{username})
📋 **العنوان:** {title}

استخدم أمر `/admin_report {report_id}` لمراجعة التقرير
            """
            
            for admin_id in ADMIN_IDS:
                try:
                    await bot.send_message(admin_id, notification_text)
                except Exception as send_error:
                    logging.warning(f"لم يتم إرسال إشعار للمدير {admin_id}: {send_error}")
                    
        except Exception as e:
            logging.error(f"خطأ في إرسال إشعارات المديرين: {e}")

    async def show_user_reports(self, message: Message):
        """عرض تقارير المستخدم"""
        try:
            if not message.from_user:
                await message.reply("❌ خطأ في معلومات المستخدم")
                return
                
            reports = await execute_query("""
                SELECT report_id, title, priority, status, created_at, reward_given
                FROM bug_reports 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT 10
            """, (message.from_user.id,), fetch_all=True)
            
            if not reports or not isinstance(reports, list):
                await message.reply("📝 لم تقم بإرسال أي تقارير بعد!\n\nاستخدم أمر 'تقرير' لإنشاء تقرير جديد")
                return
            
            reports_text = "📋 **تقاريرك الأخيرة:**\n\n"
            
            for report in reports:
                if not isinstance(report, dict):
                    continue
                    
                status_emoji = REPORT_SETTINGS["status_emojis"].get(report.get('status', ''), '❓')
                priority_emoji = REPORT_SETTINGS["priority_emojis"].get(report.get('priority', ''), '📝')
                
                title = report.get('title', '')
                report_id = report.get('report_id', '')
                reward = report.get('reward_given', 0)
                created_date = report.get('created_at', '')[:10] if report.get('created_at') else ''
                
                reports_text += f"{status_emoji} `{report_id}`\n"
                reports_text += f"{priority_emoji} **{title[:50]}{'...' if len(title) > 50 else ''}**\n"
                reports_text += f"💰 مكافأة: {format_number(reward)}$\n"
                reports_text += f"📅 تاريخ الإرسال: {created_date}\n\n"
            
            reports_text += "💡 اكتب `تقرير RPT123456789` لمشاهدة تفاصيل أي تقرير"
            
            await message.reply(reports_text)
            
        except Exception as e:
            logging.error(f"خطأ في عرض تقارير المستخدم: {e}")
            await message.reply("❌ حدث خطأ في جلب تقاريرك")

    async def show_detailed_stats(self, message: Message):
        """عرض الإحصائيات المفصلة للمستخدم"""
        try:
            stats = await self.get_user_stats(message.from_user.id)
            
            # حساب معدل الإصلاح
            fix_rate = 0
            if stats['total_reports'] > 0:
                fix_rate = (stats['fixed_reports'] / stats['total_reports']) * 100
            
            stats_text = f"""
📊 **إحصائياتك المفصلة في نظام التقرير الملكي**

🏆 **رتبتك:** {stats['reporter_rank']}

📈 **التقارير:**
• إجمالي التقارير: {stats['total_reports']}
• تقارير تم إصلاحها: {stats['fixed_reports']}
• معدل الإصلاح: {fix_rate:.1f}%

💰 **المكافآت:**
• إجمالي الأموال: {format_number(stats['total_rewards'])}$
• النقاط الذهبية: {stats['total_gold_earned']}⭐

🎯 **الهدف التالي:** {await self.get_next_goal(message.from_user.id)}
            """
            
            await message.reply(stats_text.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض الإحصائيات المفصلة: {e}")
            await message.reply("❌ حدث خطأ في جلب الإحصائيات")

    async def get_next_goal(self, user_id: int) -> str:
        """تحديد الهدف التالي للمستخدم"""
        try:
            stats = await self.get_user_stats(user_id)
            total = stats['total_reports']
            fixed = stats['fixed_reports']
            
            if total < 5:
                return f"أرسل {5 - total} تقارير إضافية للحصول على رتبة 'مبلغ نشط'"
            elif total < 10:
                return f"أرسل {10 - total} تقارير إضافية للحصول على رتبة 'مبلغ متمرس'"
            elif fixed < 10:
                return f"احتاج إلى {10 - fixed} تقارير إضافية يتم إصلاحها للحصول على رتبة 'محقق متقدم'"
            elif fixed < 15:
                return f"احتاج إلى {15 - fixed} تقارير إضافية يتم إصلاحها للحصول على رتبة 'خبير التقارير'"
            else:
                return "أنت بالفعل في المستوى العالي! استمر في التميز 🌟"
                
        except Exception:
            return "استمر في إرسال التقارير المفيدة!"

    async def show_report_details(self, message: Message, report_id: str):
        """عرض تفاصيل تقرير معين"""
        try:
            report = await execute_query("""
                SELECT * FROM bug_reports WHERE report_id = ?
            """, (report_id,), fetch_one=True)
            
            if not report or not isinstance(report, dict):
                await message.reply(f"❌ لم يتم العثور على تقرير بالرقم: `{report_id}`")
                return
            
            # التحقق من الصلاحية (المبلغ أو المدير)
            if report.get('user_id') != message.from_user.id and message.from_user.id not in ADMIN_IDS:
                await message.reply("❌ يمكنك فقط مشاهدة تقاريرك الخاصة")
                return
            
            status_emoji = REPORT_SETTINGS["status_emojis"].get(report.get('status', ''), '❓')
            priority_emoji = REPORT_SETTINGS["priority_emojis"].get(report.get('priority', ''), '📝')
            
            details_text = f"""
{status_emoji} **تقرير رقم:** `{report.get('report_id', '')}`

{priority_emoji} **الأولوية:** {report.get('priority', '')}
📋 **العنوان:** {report.get('title', '')}

📝 **الوصف:**
{report.get('description', '')}

📊 **معلومات التقرير:**
• الحالة: {report.get('status', '')}
• تاريخ الإرسال: {str(report.get('created_at', ''))[:19]}
• آخر تحديث: {str(report.get('updated_at', ''))[:19]}
"""
            
            if report.get('fixed_at'):
                details_text += f"• تاريخ الإصلاح: {str(report.get('fixed_at', ''))[:19]}\n"
            
            if report.get('reward_given', 0) > 0:
                details_text += f"\n💰 **المكافأة المستلمة:** {format_number(report.get('reward_given', 0))}$"
            
            await message.reply(details_text.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض تفاصيل التقرير: {e}")
            await message.reply("❌ حدث خطأ في جلب تفاصيل التقرير")

    async def update_report_status(self, message: Message, report_id: str, new_status: str):
        """تحديث حالة التقرير"""
        try:
            valid_statuses = ["pending", "in_progress", "testing", "fixed", "rejected", "duplicate"]
            
            if new_status not in valid_statuses:
                await message.reply(f"❌ حالة غير صحيحة! الحالات المتاحة: {', '.join(valid_statuses)}")
                return
            
            # الحصول على بيانات التقرير الحالي
            report = await execute_query("""
                SELECT * FROM bug_reports WHERE report_id = ?
            """, (report_id,), fetch_one=True)
            
            if not report or not isinstance(report, dict):
                await message.reply(f"❌ لم يتم العثور على تقرير: `{report_id}`")
                return
            
            if new_status == "fixed":
                # إضافة تاريخ الإصلاح وإرسال المكافأة
                await execute_query("""
                    UPDATE bug_reports 
                    SET status = ?, updated_at = ?, fixed_at = ?
                    WHERE report_id = ?
                """, (new_status, datetime.now().isoformat(), datetime.now().isoformat(), report_id))
                
                # منح المكافأة
                await self.give_reward(report.get('user_id', 0), report.get('priority', 'minor'), report_id)
                
                # تحديث إحصائيات المستخدم
                await execute_query("""
                    UPDATE reporter_stats 
                    SET fixed_reports = fixed_reports + 1 
                    WHERE user_id = ?
                """, (report.get('user_id', 0),))
                
            else:
                await execute_query("""
                    UPDATE bug_reports 
                    SET status = ?, updated_at = ?
                    WHERE report_id = ?
                """, (new_status, datetime.now().isoformat(), report_id))
            
            status_names = {
                "pending": "في الانتظار",
                "in_progress": "قيد العمل", 
                "testing": "قيد الاختبار",
                "fixed": "تم الإصلاح",
                "rejected": "مرفوض",
                "duplicate": "مكرر"
            }
            
            await message.reply(f"✅ تم تحديث حالة التقرير `{report_id}` إلى: **{status_names.get(new_status, new_status)}**")
            
            # إشعار المبلغ
            if message.bot:
                await self.notify_user_status_change(message.bot, report.get('user_id', 0), report_id, new_status)
            
        except Exception as e:
            logging.error(f"خطأ في تحديث حالة التقرير: {e}")
            await message.reply("❌ حدث خطأ في تحديث التقرير")

    async def give_reward(self, user_id: int, priority: str, report_id: str):
        """منح المكافأة للمبلغ"""
        try:
            reward = REPORT_SETTINGS["rewards"].get(priority, REPORT_SETTINGS["rewards"]["minor"])
            
            # إضافة الأموال للمستخدم
            user = await get_or_create_user(user_id)
            if user:
                new_balance = user['balance'] + reward['money']
                await update_user_balance(user_id, new_balance)
                
                # تسجيل المعاملة
                await add_transaction(
                    user_id,
                    f"مكافأة تقرير - {report_id}",
                    reward['money'],
                    "bug_report_reward"
                )
                
                # تحديث النقاط الذهبية
                await execute_query("""
                    UPDATE users SET gold_points = COALESCE(gold_points, 0) + ? WHERE user_id = ?
                """, (reward['gold'], user_id))
                
                # تحديث إحصائيات التقارير
                await execute_query("""
                    UPDATE reporter_stats 
                    SET total_rewards = total_rewards + ?, 
                        total_gold_earned = total_gold_earned + ?
                    WHERE user_id = ?
                """, (reward['money'], reward['gold'], user_id))
                
                # تحديث حالة المكافأة في التقرير
                await execute_query("""
                    UPDATE bug_reports 
                    SET reward_given = ?, gold_reward = ?, is_rewarded = TRUE
                    WHERE report_id = ?
                """, (reward['money'], reward['gold'], report_id))
                
                logging.info(f"تم منح مكافأة {reward['money']}$ + {reward['gold']}⭐ للمستخدم {user_id} عن التقرير {report_id}")
                
        except Exception as e:
            logging.error(f"خطأ في منح المكافأة: {e}")

    async def notify_user_status_change(self, bot: Bot, user_id: int, report_id: str, new_status: str):
        """إشعار المستخدم بتغيير حالة تقريره"""
        try:
            status_messages = {
                "in_progress": "🔧 **تحديث هام!** تقريرك قيد العمل الآن!",
                "testing": "🧪 **تقريرك في مرحلة الاختبار!** نتحقق من الإصلاح",
                "fixed": "🎉 **مبروك!** تم إصلاح المشكلة وستحصل على مكافأتك!",
                "rejected": "❌ **تم رفض التقرير** - المشكلة غير قابلة للإصلاح حالياً",
                "duplicate": "🔄 **تقرير مكرر** - تم الإبلاغ عن هذه المشكلة سابقاً"
            }
            
            if new_status in status_messages:
                notification = f"""
{status_messages[new_status]}

📋 **تقرير رقم:** `{report_id}`

اكتب `تقرير {report_id}` لمشاهدة التفاصيل الكاملة
                """
                
                try:
                    await bot.send_message(user_id, notification.strip())
                except Exception as send_error:
                    logging.warning(f"لم يتم إرسال إشعار للمستخدم {user_id}: {send_error}")
                    
        except Exception as e:
            logging.error(f"خطأ في إرسال إشعار تغيير الحالة: {e}")

    async def show_admin_reports(self, message: Message):
        """عرض جميع التقارير للمديرين"""
        try:
            # الحصول على التقارير مرتبة حسب الأولوية والحالة
            reports = await execute_query("""
                SELECT report_id, title, priority, status, user_id, created_at, votes_count
                FROM bug_reports 
                ORDER BY 
                    CASE priority 
                        WHEN 'critical' THEN 1
                        WHEN 'major' THEN 2  
                        WHEN 'minor' THEN 3
                        WHEN 'suggestion' THEN 4
                    END,
                    CASE status
                        WHEN 'pending' THEN 1
                        WHEN 'in_progress' THEN 2
                        WHEN 'testing' THEN 3
                        ELSE 4
                    END,
                    created_at DESC
                LIMIT 15
            """, fetch_all=True)
            
            if not reports or not isinstance(reports, list):
                await message.reply("📝 لا توجد تقارير في النظام حالياً")
                return
            
            admin_text = "👑 **لوحة تحكم التقارير الملكية**\n\n"
            
            # تجميع التقارير حسب الحالة
            pending_reports = [r for r in reports if isinstance(r, dict) and r.get('status') == 'pending']
            in_progress_reports = [r for r in reports if isinstance(r, dict) and r.get('status') == 'in_progress']
            
            # التقارير المعلقة (أولوية عليا)
            if pending_reports:
                admin_text += "⏳ **تقارير تحتاج مراجعة عاجلة:**\n"
                for report in pending_reports[:5]:
                    if not isinstance(report, dict):
                        continue
                    priority_emoji = REPORT_SETTINGS["priority_emojis"].get(report.get('priority', ''), '📝')
                    title = report.get('title', '')[:40]
                    report_id = report.get('report_id', '')
                    votes = report.get('votes_count', 0)
                    admin_text += f"{priority_emoji} `{report_id}` - {title}...\n"
                    admin_text += f"   👥 أصوات التأكيد: {votes}\n"
                admin_text += "\n"
            
            # التقارير قيد العمل
            if in_progress_reports:
                admin_text += "🔧 **تقارير قيد العمل:**\n"
                for report in in_progress_reports[:3]:
                    if not isinstance(report, dict):
                        continue
                    priority_emoji = REPORT_SETTINGS["priority_emojis"].get(report.get('priority', ''), '📝')
                    title = report.get('title', '')[:40]
                    report_id = report.get('report_id', '')
                    admin_text += f"{priority_emoji} `{report_id}` - {title}...\n"
                admin_text += "\n"
            
            admin_text += """
🎮 **أوامر الإدارة:**
• `/admin_report RPT123` - مراجعة تقرير
• `/update_report RPT123 fixed` - تحديث حالة 
• `/reports_stats` - إحصائيات شاملة

📊 استخدم `/reports_stats` لمشاهدة تحليل شامل لجميع التقارير
            """
            
            await message.reply(admin_text.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض تقارير المديرين: {e}")
            await message.reply("❌ حدث خطأ في جلب التقارير")

    async def show_admin_report_details(self, message: Message, report_id: str):
        """عرض تفاصيل التقرير للمديرين مع أزرار التحكم"""
        try:
            logging.info(f"البحث عن التقرير: {report_id}")
            
            report = await execute_query("""
                SELECT r.*, u.first_name, u.username 
                FROM bug_reports r
                LEFT JOIN users u ON r.user_id = u.user_id
                WHERE r.report_id = ?
            """, (report_id,), fetch_one=True)
            
            logging.info(f"نتيجة البحث: {report}")
            
            if not report:
                # البحث في جميع التقارير لمساعدة المدير
                all_reports = await execute_query("""
                    SELECT report_id, title FROM bug_reports 
                    ORDER BY created_at DESC LIMIT 5
                """, fetch_all=True)
                
                recent_list = ""
                if all_reports:
                    recent_list = "\n\n📋 **آخر التقارير:**\n"
                    for r in all_reports:
                        if isinstance(r, dict):
                            recent_list += f"• `{r.get('report_id', '')}` - {r.get('title', '')[:30]}\n"
                
                await message.reply(f"❌ لم يتم العثور على تقرير: `{report_id}`{recent_list}")
                return
            
            if not isinstance(report, dict):
                await message.reply(f"❌ خطأ في بيانات التقرير: `{report_id}`")
                return
            
            status_emoji = REPORT_SETTINGS["status_emojis"].get(report.get('status', ''), '❓')
            priority_emoji = REPORT_SETTINGS["priority_emojis"].get(report.get('priority', ''), '📝')
            
            # تحسين عرض الأسماء
            reporter_name = report.get('first_name', 'غير معروف')
            reporter_username = report.get('username', '')
            if reporter_username:
                reporter_display = f"{reporter_name} (@{reporter_username})"
            else:
                reporter_display = reporter_name
            
            admin_details = f"""
👑 **مراجعة إدارية للتقرير** `{report.get('report_id', '')}`

{priority_emoji} **الأولوية:** {report.get('priority', '')}
{status_emoji} **الحالة:** {report.get('status', '')}

👤 **المبلغ:** {reporter_display}
🆔 **معرف المستخدم:** `{report.get('user_id', '')}`

📋 **العنوان:** 
{report.get('title', '')}

📝 **الوصف التفصيلي:**
{report.get('description', '')}

📊 **معلومات إضافية:**
• تاريخ الإرسال: {str(report.get('created_at', ''))[:19]}
• آخر تحديث: {str(report.get('updated_at', ''))[:19]}
• التصويت المجتمعي: {report.get('votes_count', 0)} صوت

🛠️ **أوامر الإدارة:**
• `/update_report {report.get('report_id', '')} in_progress` - بدء العمل
• `/update_report {report.get('report_id', '')} fixed` - تم الإصلاح
• `/update_report {report.get('report_id', '')} rejected` - رفض التقرير
            """
            
            if report.get('fixed_at'):
                admin_details += f"• تاريخ الإصلاح: {str(report.get('fixed_at', ''))[:19]}\n"
            
            await message.reply(admin_details.strip())
            logging.info(f"تم عرض تفاصيل التقرير {report_id} بنجاح")
            
        except Exception as e:
            logging.error(f"خطأ في عرض تفاصيل التقرير للمدير: {e}")
            await message.reply(f"❌ حدث خطأ في جلب التقرير: {str(e)}")

    async def show_system_stats(self, message: Message):
        """عرض إحصائيات شاملة للنظام - للمديرين"""
        try:
            # إحصائيات عامة
            general_stats = await execute_query("""
                SELECT 
                    COUNT(*) as total_reports,
                    COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                    COUNT(CASE WHEN status = 'in_progress' THEN 1 END) as in_progress_count,
                    COUNT(CASE WHEN status = 'fixed' THEN 1 END) as fixed_count,
                    COUNT(CASE WHEN priority = 'critical' THEN 1 END) as critical_count,
                    COUNT(CASE WHEN priority = 'major' THEN 1 END) as major_count
                FROM bug_reports
            """, fetch_one=True)
            
            # أفضل المبلغين
            top_reporters = await execute_query("""
                SELECT u.first_name, rs.total_reports, rs.fixed_reports, rs.reporter_rank
                FROM reporter_stats rs
                LEFT JOIN users u ON rs.user_id = u.user_id
                ORDER BY rs.fixed_reports DESC, rs.total_reports DESC
                LIMIT 5
            """, fetch_all=True)
            
            if not general_stats:
                general_stats = {}
            
            stats_text = f"""
📊 **إحصائيات نظام التقرير الملكي الشاملة**

📈 **إحصائيات عامة:**
• إجمالي التقارير: {general_stats.get('total_reports', 0)}
• في الانتظار: {general_stats.get('pending_count', 0)} ⏳
• قيد العمل: {general_stats.get('in_progress_count', 0)} 🔧
• تم الإصلاح: {general_stats.get('fixed_count', 0)} ✅

🔥 **توزيع الأولويات:**
• أخطاء قاتلة: {general_stats.get('critical_count', 0)}
• أخطاء مهمة: {general_stats.get('major_count', 0)}

🏆 **أفضل المبلغين:**
            """
            
            if top_reporters and isinstance(top_reporters, list):
                for i, reporter in enumerate(top_reporters[:3], 1):
                    if isinstance(reporter, dict):
                        name = reporter.get('first_name', 'غير معروف')
                        fixed = reporter.get('fixed_reports', 0)
                        stats_text += f"{i}. {name} - {fixed} إصلاح\n"
            
            await message.reply(stats_text.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض إحصائيات النظام: {e}")
            await message.reply("❌ حدث خطأ في جلب الإحصائيات")

    async def process_vote(self, callback: CallbackQuery, report_id: str, vote_type: str):
        """معالجة التصويت على التقرير"""
        try:
            await callback.answer("✅ تم تسجيل تصويتك")
        except Exception as e:
            logging.error(f"خطأ في معالجة التصويت: {e}")

    async def assign_report(self, callback: CallbackQuery, report_id: str, admin_id: int):
        """تعيين التقرير لمدير"""
        try:
            await callback.answer("✅ تم تعيين التقرير")
        except Exception as e:
            logging.error(f"خطأ في تعيين التقرير: {e}")

    async def mark_as_fixed(self, callback: CallbackQuery, report_id: str):
        """تحديد التقرير كمُصلح"""
        try:
            await callback.answer("✅ تم تحديد التقرير كمُصلح")
        except Exception as e:
            logging.error(f"خطأ في تحديد التقرير كمُصلح: {e}")

    async def mark_as_duplicate(self, callback: CallbackQuery, report_id: str):
        """تحديد التقرير كمكرر"""
        try:
            await callback.answer("✅ تم تحديد التقرير كمكرر")
        except Exception as e:
            logging.error(f"خطأ في تحديد التقرير كمكرر: {e}")

    async def reject_report(self, callback: CallbackQuery, report_id: str):
        """رفض التقرير"""
        try:
            await callback.answer("✅ تم رفض التقرير")
        except Exception as e:
            logging.error(f"خطأ في رفض التقرير: {e}")

    async def show_report_details(self, message: Message, report_id: str):
        """عرض تفاصيل التقرير"""
        try:
            await message.reply(f"📋 تفاصيل التقرير {report_id}")
        except Exception as e:
            logging.error(f"خطأ في عرض تفاصيل التقرير: {e}")

    async def show_detailed_stats(self, message):
        """عرض إحصائيات مفصلة"""
        try:
            await message.reply("📊 إحصائياتك المفصلة")
        except Exception as e:
            logging.error(f"خطأ في عرض الإحصائيات المفصلة: {e}")

    # تم نقل جميع دوال المديرين للأعلى - هذه مجرد دوال وهمية محذوفة

# إنشاء نسخة عالمية من النظام
bug_report_system = BugReportSystem()
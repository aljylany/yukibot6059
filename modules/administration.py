"""
وحدة الإدارة
Administration Module
"""

import logging
import asyncio
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, execute_query
from modules.ranking import get_global_statistics
from utils.states import AdminStates
from utils.helpers import format_number
from config.settings import ADMIN_IDS


async def show_bot_stats(message: Message):
    """عرض إحصائيات البوت"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # الحصول على الإحصائيات العامة
        stats = await get_global_statistics()
        
        # إحصائيات إضافية
        daily_stats = await get_daily_statistics()
        weekly_stats = await get_weekly_statistics()
        
        stats_text = f"""
📊 **إحصائيات البوت الشاملة**

👥 **المستخدمين:**
📊 إجمالي المستخدمين: {format_number(stats.get('total_users', 0))}
📈 مستخدمين جدد اليوم: {format_number(daily_stats.get('new_users', 0))}
📅 مستخدمين جدد هذا الأسبوع: {format_number(weekly_stats.get('new_users', 0))}
🎯 المستخدمين النشطين: {format_number(daily_stats.get('active_users', 0))}

💰 **الاقتصاد:**
💵 إجمالي الأموال: {format_number(stats.get('total_money', 0))}$
🏦 أموال البنوك: {format_number(daily_stats.get('bank_money', 0))}$
💸 المعاملات اليوم: {format_number(daily_stats.get('transactions_today', 0))}
📊 إجمالي المعاملات: {format_number(stats.get('total_transactions', 0))}

🏠 **العقارات:**
🏘 إجمالي العقارات: {format_number(stats.get('total_properties', 0))}
🏠 عقارات جديدة اليوم: {format_number(daily_stats.get('properties_today', 0))}

💼 **الاستثمارات:**
📈 استثمارات نشطة: {format_number(stats.get('total_investments', 0))}
💰 قيمة الاستثمارات: {format_number(daily_stats.get('investments_value', 0))}$

🎮 **النشاط:**
⚡ أوامر اليوم: {format_number(daily_stats.get('commands_today', 0))}
🕐 متوسط وقت الاستجابة: {daily_stats.get('avg_response_time', 'غير متاح')}

🗓 آخر تحديث: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        """
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 تقرير مفصل", callback_data="admin_detailed_report"),
                InlineKeyboardButton(text="🔄 تحديث", callback_data="admin_stats")
            ],
            [
                InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="admin_users"),
                InlineKeyboardButton(text="💾 نسخة احتياطية", callback_data="admin_backup")
            ]
        ])
        
        await message.reply(stats_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات البوت: {e}")
        await message.reply("❌ حدث خطأ في عرض الإحصائيات")


async def start_broadcast(message: Message, state: FSMContext):
    """بدء إرسال رسالة جماعية"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        await state.set_state(AdminStates.waiting_broadcast_message)
        await message.reply(
            "📢 **إرسال رسالة جماعية**\n\n"
            "اكتب الرسالة التي تريد إرسالها لجميع المستخدمين:\n\n"
            "💡 يمكنك استخدام تنسيق HTML\n"
            "❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء الرسالة الجماعية: {e}")
        await message.reply("❌ حدث خطأ في إعداد الرسالة الجماعية")


async def process_broadcast_message(message: Message, state: FSMContext):
    """معالجة الرسالة الجماعية وإرسالها"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            await state.clear()
            return
        
        if message.text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء الرسالة الجماعية")
            return
        
        broadcast_text = message.text
        
        # الحصول على جميع المستخدمين
        all_users = await execute_query(
            "SELECT user_id FROM users",
            (),
            fetch_one=True
        )
        
        if not all_users:
            await message.reply("❌ لا توجد مستخدمين للإرسال إليهم")
            await state.clear()
            return
        
        # رسالة تأكيد
        confirm_keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ إرسال", callback_data="admin_confirm_broadcast"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="admin_cancel_broadcast")
            ]
        ])
        
        await state.update_data(broadcast_message=broadcast_text, target_users=all_users)
        
        await message.reply(
            f"📢 **تأكيد الرسالة الجماعية**\n\n"
            f"**الرسالة:**\n{broadcast_text}\n\n"
            f"👥 عدد المستقبلين: {len(all_users)}\n\n"
            f"هل أنت متأكد من الإرسال؟",
            reply_markup=confirm_keyboard
        )
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الرسالة الجماعية: {e}")
        await message.reply("❌ حدث خطأ في معالجة الرسالة")
        await state.clear()


async def execute_broadcast(message: Message, state: FSMContext):
    """تنفيذ الرسالة الجماعية"""
    try:
        data = await state.get_data()
        broadcast_message = data.get('broadcast_message')
        target_users = data.get('target_users', [])
        
        if not broadcast_message or not target_users:
            await message.reply("❌ بيانات الرسالة غير كاملة")
            await state.clear()
            return
        
        await message.reply(
            f"🚀 **بدء الإرسال الجماعي...**\n\n"
            f"👥 المستهدفين: {len(target_users)}\n"
            f"⏳ يرجى الانتظار..."
        )
        
        # إرسال الرسالة لجميع المستخدمين
        success_count = 0
        failed_count = 0
        
        for user in target_users:
            try:
                await message.bot.send_message(user['user_id'], broadcast_message)
                success_count += 1
                
                # توقف قصير لتجنب حدود التلقرام
                await asyncio.sleep(0.05)
                
            except Exception as e:
                failed_count += 1
                logging.warning(f"فشل إرسال رسالة للمستخدم {user['user_id']}: {e}")
        
        # تقرير النتائج
        await message.reply(
            f"✅ **تم الإرسال الجماعي!**\n\n"
            f"📊 **النتائج:**\n"
            f"✅ نجح: {success_count}\n"
            f"❌ فشل: {failed_count}\n"
            f"📈 معدل النجاح: {(success_count/(success_count+failed_count)*100):.1f}%"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في تنفيذ الرسالة الجماعية: {e}")
        await message.reply("❌ حدث خطأ في الإرسال الجماعي")
        await state.clear()


async def show_user_management(message: Message):
    """عرض إدارة المستخدمين"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # الحصول على أحدث المستخدمين
        recent_users = await get_recent_users()
        top_users = await get_top_users_by_activity()
        
        management_text = "👥 **إدارة المستخدمين**\n\n"
        
        management_text += "📈 **أحدث المستخدمين:**\n"
        for user in recent_users[:5]:
            username = user.get('username', user.get('first_name', 'مجهول'))[:15]
            management_text += f"• {username} (ID: {user['user_id']})\n"
        
        management_text += "\n🎯 **الأكثر نشاطاً:**\n"
        for user in top_users[:5]:
            username = user.get('username', user.get('first_name', 'مجهول'))[:15]
            management_text += f"• {username} ({user.get('activity_count', 0)} نشاط)\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔍 بحث مستخدم", callback_data="admin_search_user"),
                InlineKeyboardButton(text="📊 تقرير مستخدم", callback_data="admin_user_report")
            ],
            [
                InlineKeyboardButton(text="⛔ حظر مستخدم", callback_data="admin_ban_user"),
                InlineKeyboardButton(text="✅ إلغاء حظر", callback_data="admin_unban_user")
            ]
        ])
        
        await message.reply(management_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في إدارة المستخدمين: {e}")
        await message.reply("❌ حدث خطأ في إدارة المستخدمين")


async def ban_user(message: Message, user_id: int):
    """حظر مستخدم"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # التحقق من وجود المستخدم
        user = await get_user(user_id)
        if not user:
            await message.reply("❌ المستخدم غير موجود")
            return
        
        # إضافة المستخدم لقائمة المحظورين
        await execute_query(
            "INSERT OR REPLACE INTO banned_users (user_id, banned_by, banned_at, reason) VALUES (?, ?, ?, ?)",
            (user_id, message.from_user.id, datetime.now().isoformat(), "تم الحظر بواسطة الإدارة")
        )
        
        username = user.get('username', user.get('first_name', 'مجهول'))
        
        await message.reply(
            f"⛔ **تم حظر المستخدم**\n\n"
            f"👤 المستخدم: {username}\n"
            f"🆔 المعرف: {user_id}\n"
            f"👮 بواسطة: {message.from_user.username or message.from_user.first_name}\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # إشعار المستخدم المحظور
        try:
            await message.bot.send_message(
                user_id,
                "⛔ **تم حظرك من البوت**\n\n"
                "تم حظرك من قبل الإدارة. إذا كنت تعتقد أن هذا خطأ، "
                "يرجى التواصل مع الإدارة."
            )
        except:
            pass  # في حالة فشل الإرسال
        
    except Exception as e:
        logging.error(f"خطأ في حظر المستخدم: {e}")
        await message.reply("❌ حدث خطأ في عملية الحظر")


async def unban_user(message: Message, user_id: int):
    """إلغاء حظر مستخدم"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        # إزالة المستخدم من قائمة المحظورين
        result = await execute_query(
            "DELETE FROM banned_users WHERE user_id = ?",
            (user_id,)
        )
        
        if result == 0:
            await message.reply("❌ المستخدم غير محظور")
            return
        
        user = await get_user(user_id)
        username = user.get('username', user.get('first_name', 'مجهول')) if user else 'غير معروف'
        
        await message.reply(
            f"✅ **تم إلغاء حظر المستخدم**\n\n"
            f"👤 المستخدم: {username}\n"
            f"🆔 المعرف: {user_id}\n"
            f"👮 بواسطة: {message.from_user.username or message.from_user.first_name}\n"
            f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # إشعار المستخدم بإلغاء الحظر
        try:
            await message.bot.send_message(
                user_id,
                "✅ **تم إلغاء حظرك**\n\n"
                "يمكنك الآن استخدام البوت بشكل طبيعي. "
                "يرجى الالتزام بقوانين البوت."
            )
        except:
            pass
        
    except Exception as e:
        logging.error(f"خطأ في إلغاء حظر المستخدم: {e}")
        await message.reply("❌ حدث خطأ في إلغاء الحظر")


async def create_backup(message: Message):
    """إنشاء نسخة احتياطية"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ غير مصرح لك بالوصول لهذه الميزة")
            return
        
        await message.reply("🔄 **إنشاء نسخة احتياطية...**\n\nيرجى الانتظار...")
        
        # إنشاء النسخة الاحتياطية
        backup_data = await create_database_backup()
        
        if backup_data:
            backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # حفظ البيانات في ملف
            import json
            with open(backup_filename, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, ensure_ascii=False, indent=2)
            
            await message.reply(
                f"✅ **تم إنشاء النسخة الاحتياطية بنجاح!**\n\n"
                f"📁 اسم الملف: {backup_filename}\n"
                f"📊 البيانات المحفوظة:\n"
                f"• المستخدمين: {len(backup_data.get('users', []))}\n"
                f"• المعاملات: {len(backup_data.get('transactions', []))}\n"
                f"• العقارات: {len(backup_data.get('properties', []))}\n"
                f"• الاستثمارات: {len(backup_data.get('investments', []))}\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
        else:
            await message.reply("❌ فشل في إنشاء النسخة الاحتياطية")
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        await message.reply("❌ حدث خطأ في إنشاء النسخة الاحتياطية")


async def get_daily_statistics():
    """الحصول على إحصائيات اليوم"""
    try:
        today = datetime.now().date()
        today_start = datetime.combine(today, datetime.min.time())
        
        stats = {}
        
        # مستخدمين جدد اليوم
        new_users = await execute_query(
            "SELECT COUNT(*) as count FROM users WHERE DATE(created_at) = ?",
            (today,),
            fetch_one=True
        )
        stats['new_users'] = new_users['count'] if new_users else 0
        
        # معاملات اليوم
        transactions = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE DATE(created_at) = ?",
            (today,),
            fetch_one=True
        )
        stats['transactions_today'] = transactions['count'] if transactions else 0
        
        # أموال البنوك
        bank_money = await execute_query(
            "SELECT SUM(bank_balance) as total FROM users",
            (),
            fetch_one=True
        )
        stats['bank_money'] = bank_money['total'] if bank_money and bank_money['total'] else 0
        
        # عقارات جديدة اليوم
        properties = await execute_query(
            "SELECT COUNT(*) as count FROM properties WHERE DATE(purchased_at) = ?",
            (today,),
            fetch_one=True
        )
        stats['properties_today'] = properties['count'] if properties else 0
        
        # قيمة الاستثمارات
        investments = await execute_query(
            "SELECT SUM(amount) as total FROM investments WHERE status = 'active'",
            (),
            fetch_one=True
        )
        stats['investments_value'] = investments['total'] if investments and investments['total'] else 0
        
        # أوامر اليوم (تقدير)
        stats['commands_today'] = stats['transactions_today'] * 2  # تقدير تقريبي
        
        # مستخدمين نشطين (تقدير)
        stats['active_users'] = min(stats['new_users'] + 10, stats.get('total_users', 0))
        
        return stats
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات اليوم: {e}")
        return {}


async def get_weekly_statistics():
    """الحصول على إحصائيات الأسبوع"""
    try:
        week_start = datetime.now() - timedelta(days=7)
        
        stats = {}
        
        # مستخدمين جدد هذا الأسبوع
        new_users = await execute_query(
            "SELECT COUNT(*) as count FROM users WHERE created_at >= ?",
            (week_start.isoformat(),),
            fetch_one=True
        )
        stats['new_users'] = new_users['count'] if new_users else 0
        
        return stats
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات الأسبوع: {e}")
        return {}


async def get_recent_users():
    """الحصول على أحدث المستخدمين"""
    try:
        users = await execute_query(
            "SELECT user_id, username, first_name, created_at FROM users ORDER BY created_at DESC LIMIT 10",
            (),
            fetch_one=True
        )
        return users if users else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على أحدث المستخدمين: {e}")
        return []


async def get_top_users_by_activity():
    """الحصول على المستخدمين الأكثر نشاطاً"""
    try:
        users = await execute_query(
            """
            SELECT u.user_id, u.username, u.first_name, COUNT(t.id) as activity_count
            FROM users u
            LEFT JOIN transactions t ON u.user_id = t.from_user_id OR u.user_id = t.to_user_id
            GROUP BY u.user_id
            ORDER BY activity_count DESC
            LIMIT 10
            """,
            (),
            fetch_one=True
        )
        return users if users else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على المستخدمين النشطين: {e}")
        return []


async def create_database_backup():
    """إنشاء نسخة احتياطية من قاعدة البيانات"""
    try:
        backup_data = {}
        
        # نسخ احتياطية للجداول المهمة
        tables = ['users', 'transactions', 'properties', 'investments', 'stocks', 'farm', 'castle']
        
        for table in tables:
            try:
                data = await execute_query(f"SELECT * FROM {table}", (), fetch_one=True)
                backup_data[table] = data if data else []
            except Exception as e:
                logging.warning(f"تعذر نسخ جدول {table}: {e}")
                backup_data[table] = []
        
        # إضافة معلومات النسخة الاحتياطية
        backup_data['backup_info'] = {
            'created_at': datetime.now().isoformat(),
            'version': '1.0',
            'creator': 'Admin Bot'
        }
        
        return backup_data
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء النسخة الاحتياطية: {e}")
        return None


# معالجات الحالات
async def process_user_id_action(message: Message, state: FSMContext):
    """معالجة إجراء معرف المستخدم"""
    await message.reply("تم استلام معرف المستخدم")
    await state.clear()

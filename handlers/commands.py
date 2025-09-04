"""
معالج أوامر البوت
Bot Commands Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.operations import get_or_create_user, update_user_activity
from modules import banks, real_estate, theft, stocks, investment, ranking, administration, farm, castle
from utils.decorators import user_required, admin_required, group_only, registration_required
from config.settings import SYSTEM_MESSAGES, ADMIN_IDS, NOTIFICATION_CHANNEL
from handlers.advanced_admin_handler import handle_advanced_admin_commands
from config.hierarchy import has_permission, AdminLevel

router = Router()


# نعدل أمر البدء ليعمل في المحادثات الخاصة فقط
from aiogram.enums import ChatType

@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """أمر البدء /start - يعمل في المحادثات الخاصة فقط"""
    try:
        # التحقق من نوع المحادثة - يعمل فقط في المحادثات الخاصة
        if message.chat.type != ChatType.PRIVATE:
            # إذا كان الأمر في مجموعة، لا نفعل شيئاً
            return
        
        # فحص إذا كان الأمر مخصص للهمسة
        if message.text and "whisper_" in message.text:
            from modules.utility_commands import handle_whisper_start
            await handle_whisper_start(message, state)
            return
            
        # رسالة في الخاص - طلب إضافة البوت للمجموعة مع زر
        welcome_text = """
🎮 **مرحباً بك في بوت الألعاب الاقتصادية!**

👋 أنا Yuki، بوت ألعاب اقتصادية تفاعلي باللغة العربية.

📢 **لاستخدام البوت:**
1️⃣ أضفني إلى مجموعتك
2️⃣ امنحني صلاحيات الإدارة
3️⃣ ابدأ اللعب مع أصدقائك!

🎯 **الميزات المتاحة:**
• 💰 نظام مصرفي متكامل
• 🏠 شراء وبيع العقارات
• 📈 تداول الأسهم والاستثمار
• 🔓 آليات السرقة والحماية
• 🌾 نظام المزارع والإنتاج
• 🏰 بناء وترقية القلاع
• 🏆 نظام ترتيب اللاعبين

بعد إضافتي للمجموعة، ابدأ باستخدام الكلمات المفتاحية مباشرة! 🚀
        """
        # إنشاء زر لإضافة البوت كمشرف
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text="➕ إضافة البوت كمشرف في المجموعة",
                url="https://telegram.me/theyuki_bot?startgroup=admin&admin=delete_messages+restrict_members+pin_messages+invite_users"
            )]
        ])
        
        await message.reply(welcome_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في أمر البدء: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])



@router.message(Command("help"))
@registration_required
async def help_command(message: Message):
    """أمر المساعدة /help"""
    try:
        await message.reply(SYSTEM_MESSAGES["help"])
    except Exception as e:
        logging.error(f"خطأ في أمر المساعدة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("balance"))
@registration_required
async def balance_command(message: Message):
    """عرض الرصيد /balance"""
    try:
        await banks.show_balance(message)
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("daily"))
@registration_required
async def daily_command(message: Message):
    """المكافأة اليومية /daily"""
    try:
        await banks.daily_bonus(message)
    except Exception as e:
        logging.error(f"خطأ في المكافأة اليومية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("transfer"))
@registration_required
async def transfer_command(message: Message, state: FSMContext):
    """تحويل الأموال /transfer"""
    try:
        await banks.start_transfer(message, state)
    except Exception as e:
        logging.error(f"خطأ في تحويل الأموال: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("bank"))
@registration_required
async def bank_command(message: Message):
    """إدارة البنك /bank"""
    try:
        bank_info = """
🏦 **معلومات البنك**

💰 **الخدمات المتاحة:**
• `/deposit [المبلغ]` - إيداع أموال في البنك
• `/withdraw [المبلغ]` - سحب أموال من البنك
• `/balance` - عرض رصيدك الحالي
• `/bank_balance` - عرض رصيد البنك
• `/transfer [المبلغ] [معرف المستخدم]` - تحويل أموال

📈 **نظام الفوائد:**
• معدل الفائدة: 5% سنوياً
• يتم حساب الفوائد يومياً
• الحد الأدنى للإيداع: 100 وحدة

💡 **نصائح:**
• احتفظ بأموالك في البنك لتكسب فوائد
• يمكنك السحب في أي وقت
• التحويلات فورية بين اللاعبين
        """
        await message.reply(bank_info)
    except Exception as e:
        logging.error(f"خطأ في قائمة البنك: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("deposit"))
@user_required
async def deposit_command(message: Message, state: FSMContext):
    """إيداع في البنك /deposit"""
    try:
        await banks.start_deposit(message, state)
    except Exception as e:
        logging.error(f"خطأ في الإيداع: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("withdraw"))
@user_required
async def withdraw_command(message: Message, state: FSMContext):
    """سحب من البنك /withdraw"""
    try:
        await banks.start_withdraw(message, state)
    except Exception as e:
        logging.error(f"خطأ في السحب: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("property"))
@user_required
async def property_command(message: Message):
    """إدارة العقارات /property"""
    try:
        await real_estate.show_property_menu(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة العقارات: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("buy_property"))
@user_required
async def buy_property_command(message: Message):
    """شراء عقار /buy_property"""
    try:
        await real_estate.show_available_properties(message)
    except Exception as e:
        logging.error(f"خطأ في شراء العقار: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("sell_property"))
@user_required
async def sell_property_command(message: Message):
    """بيع عقار /sell_property"""
    try:
        await real_estate.show_owned_properties(message)
    except Exception as e:
        logging.error(f"خطأ في بيع العقار: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("steal"))
@user_required
async def steal_command(message: Message, state: FSMContext):
    """سرقة لاعب /steal"""
    try:
        await theft.start_steal(message, state)
    except Exception as e:
        logging.error(f"خطأ في السرقة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("security"))
@user_required
async def security_command(message: Message):
    """تحسين الأمان /security"""
    try:
        await theft.show_security_menu(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة الأمان: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("stocks"))
@user_required
async def stocks_command(message: Message):
    """عرض الأسهم /stocks"""
    try:
        await stocks.show_stocks_menu(message)
    except Exception as e:
        logging.error(f"خطأ في عرض الأسهم: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("invest"))
@user_required
async def invest_command(message: Message):
    """الاستثمار /invest"""
    try:
        await investment.show_investment_menu(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة الاستثمار: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("portfolio"))
@user_required
async def portfolio_command(message: Message):
    """محفظة الاستثمارات /portfolio"""
    try:
        await investment.show_portfolio(message)
    except Exception as e:
        logging.error(f"خطأ في عرض المحفظة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ranking"))
@user_required
async def ranking_command(message: Message):
    """الترتيب /ranking"""
    try:
        await ranking.show_user_ranking(message)
    except Exception as e:
        logging.error(f"خطأ في عرض الترتيب: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("leaderboard"))
@user_required
async def leaderboard_command(message: Message):
    """قائمة المتصدرين /leaderboard"""
    try:
        await ranking.show_leaderboard(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة المتصدرين: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("farm"))
@user_required
async def farm_command(message: Message):
    """المزرعة /farm"""
    try:
        await farm.show_farm_menu(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة المزرعة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("plant"))
@user_required
async def plant_command(message: Message):
    """زراعة المحاصيل /plant"""
    try:
        await farm.show_planting_options(message)
    except Exception as e:
        logging.error(f"خطأ في زراعة المحاصيل: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("harvest"))
@user_required
async def harvest_command(message: Message):
    """حصاد المحاصيل /harvest"""
    try:
        await farm.harvest_crops(message)
    except Exception as e:
        logging.error(f"خطأ في حصاد المحاصيل: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("castle"))
@user_required
async def castle_command(message: Message):
    """القلعة /castle"""
    try:
        await castle.show_castle_menu(message)
    except Exception as e:
        logging.error(f"خطأ في قائمة القلعة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


# أمر اختبار القناة الفرعية - للمديرين فقط
@router.message(Command("test_channel"))
async def test_channel_command(message: Message):
    """اختبار القناة الفرعية /test_channel - للمديرين فقط"""
    try:
        # التحقق من أن المستخدم مدير
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط!")
            return
        
        # استيراد مدير الإشعارات واختبار القناة
        from modules.notification_manager import NotificationManager
        notification_manager = NotificationManager(message.bot)
        
        # تشغيل اختبار القناة
        success = await notification_manager.test_notification_channel()
        
        if success:
            await message.reply("✅ تم اختبار القناة الفرعية بنجاح! تحقق من القناة لرؤية رسالة الاختبار.")
        else:
            await message.reply("❌ فشل في اختبار القناة الفرعية. تحقق من إعدادات القناة وصلاحيات البوت.")
            
    except Exception as e:
        logging.error(f"خطأ في اختبار القناة الفرعية: {e}")
        await message.reply("❌ حدث خطأ أثناء اختبار القناة الفرعية")


# أمر للحصول على Chat ID للمحادثة الحالية - للمديرين فقط
@router.message(Command("get_chat_id"))
async def get_chat_id_command(message: Message):
    """الحصول على Chat ID للمحادثة الحالية /get_chat_id - للمديرين فقط"""
    try:
        # التحقق من أن المستخدم مدير
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط!")
            return
        
        chat_info = f"""
🆔 **معلومات المحادثة:**

**Chat ID:** `{message.chat.id}`
**نوع المحادثة:** {message.chat.type}
**عنوان المحادثة:** {message.chat.title or "لا يوجد"}
**اسم المستخدم:** @{message.chat.username or "لا يوجد"}

📋 **خطوات ربط قناة الإشعارات:**
1. انسخ الـ Chat ID أعلاه
2. استخدم أمر `/set_channel {message.chat.id}` لربط هذه القناة
3. جرب أمر `/test_channel` للتأكد من عمل النظام

💡 **ملاحظة:** تأكد من أن البوت مشرف في القناة مع صلاحيات إرسال الرسائل
        """
        
        await message.reply(chat_info)
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على Chat ID: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات المحادثة")


# أمر لتعيين قناة الإشعارات - للمديرين فقط
@router.message(Command("set_channel"))
async def set_channel_command(message: Message):
    """تعيين قناة الإشعارات /set_channel [chat_id] - للمديرين فقط"""
    try:
        # التحقق من أن المستخدم مدير
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط!")
            return
        
        # الحصول على معرف القناة من الأمر
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("❌ يرجى إدخال معرف القناة!\nمثال: `/set_channel -1001234567890`")
            return
        
        chat_id = command_parts[1].strip()
        
        # محاولة تحديث ملف الإعدادات
        from config.settings import NOTIFICATION_CHANNEL
        
        # قراءة الملف وتحديثه
        with open('config/settings.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # تحديث المعرف وتفعيل النظام
        old_line = f'    "chat_id": "",  # معرف القناة الفرعية (يجب الحصول على الـ Chat ID الصحيح)'
        new_line = f'    "chat_id": "{chat_id}",  # معرف القناة الفرعية'
        content = content.replace(old_line, new_line)
        
        # تفعيل النظام
        content = content.replace('"enabled": False,  # معطل مؤقتاً حتى الحصول على المعرف الصحيح', '"enabled": True,')
        
        # حفظ الملف
        with open('config/settings.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        # إعادة تحميل الإعدادات
        import importlib
        import config.settings
        importlib.reload(config.settings)
        
        # اختبار الاتصال بالقناة
        from modules.notification_manager import NotificationManager
        notification_manager = NotificationManager(message.bot)
        
        test_success = await notification_manager.test_notification_channel()
        
        if test_success:
            await message.reply(f"✅ تم ربط قناة الإشعارات بنجاح!\n\n🆔 **معرف القناة:** `{chat_id}`\n\n🎉 النظام جاهز الآن وتم إرسال رسالة اختبار للقناة!")
        else:
            await message.reply(f"⚠️ تم حفظ معرف القناة ولكن فشل الاختبار.\n\n🆔 **معرف القناة:** `{chat_id}`\n\n❌ تأكد من:\n- البوت مشرف في القناة\n- البوت لديه صلاحية إرسال الرسائل\n- معرف القناة صحيح")
        
    except Exception as e:
        logging.error(f"خطأ في تعيين قناة الإشعارات: {e}")
        await message.reply("❌ حدث خطأ أثناء تعيين قناة الإشعارات")


@router.message(Command("upgrade"))
@user_required
async def upgrade_command(message: Message):
    """ترقية المباني /upgrade"""
    try:
        await castle.show_upgrade_options(message)
    except Exception as e:
        logging.error(f"خطأ في ترقية المباني: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("defend"))
@user_required
async def defend_command(message: Message):
    """الدفاع عن القلعة /defend"""
    try:
        await castle.show_defense_menu(message)
    except Exception as e:
        logging.error(f"خطأ في الدفاع عن القلعة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


# أوامر الإدارة
@router.message(Command("admin"))
@admin_required
async def admin_command(message: Message):
    """لوحة تحكم الإدارة /admin"""
    try:
        admin_menu = """
🔧 **لوحة تحكم الإدارة**

📋 **الأوامر المتاحة:**

📊 **إحصائيات:**
• `/stats` - إحصائيات البوت
• `/bot_info` - معلومات النظام

👥 **إدارة المستخدمين:**
• `/ban_user [معرف المستخدم]` - حظر مستخدم
• `/unban_user [معرف المستخدم]` - إلغاء حظر مستخدم
• `/user_info [معرف المستخدم]` - معلومات المستخدم

📢 **التواصل:**
• `/broadcast` - بدء رسالة جماعية
• `/announcement` - إعلان مهم

💾 **النظام:**
• `/backup` - إنشاء نسخة احتياطية
• `/maintenance` - وضع الصيانة

استخدم الأوامر أعلاه لإدارة البوت.
        """
        await message.reply(admin_menu)
    except Exception as e:
        logging.error(f"خطأ في لوحة الإدارة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("stats"))
@admin_required
async def stats_command(message: Message):
    """إحصائيات البوت /stats"""
    try:
        await administration.show_bot_stats(message)
    except Exception as e:
        logging.error(f"خطأ في عرض الإحصائيات: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("broadcast"))
@admin_required
async def broadcast_command(message: Message, state: FSMContext):
    """رسالة جماعية /broadcast"""
    try:
        await administration.start_broadcast(message, state)
    except Exception as e:
        logging.error(f"خطأ في الرسالة الجماعية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("uptime"))
async def uptime_command(message: Message):
    """أمر عرض وقت التشغيل الحالي /uptime"""
    try:
        from modules.notification_manager import NotificationManager
        
        # يمكن استخدامه في أي مكان، ليس مقيد بالقناة الفرعية
        if not message.bot:
            await message.reply("❌ خطأ في النظام")
            return
            
        notification_manager = NotificationManager(message.bot)
        uptime = await notification_manager.get_uptime()
        
        from datetime import datetime
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        uptime_message = f"""
⏱️ **وقت تشغيل بوت يوكي**

🕐 **الوقت الحالي:** {current_time}
⏰ **مدة التشغيل:** {uptime}
🚀 **حالة البوت:** يعمل بشكل طبيعي

---
💡 **نصيحة:** استخدم هذا الأمر في أي وقت لمعرفة مدة تشغيل البوت
        """
        
        await message.reply(uptime_message.strip())
        
    except Exception as e:
        logging.error(f"خطأ في أمر وقت التشغيل: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات وقت التشغيل.")


# أوامر الترقية الملكية - للسيد الأعلى فقط
@router.message(Command("promote_queen"))
async def promote_queen_command(message: Message):
    """ترقية مستخدم إلى ملكة /promote_queen [user_id] - للسيد الأعلى فقط"""
    try:
        from config.hierarchy import is_supreme_master, promote_to_queen
        
        # التحقق من أن المستخدم هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            await message.reply("❌ هذا الأمر متاح للسيد الأعلى فقط!")
            return
        
        # الحصول على معرف المستخدم من الأمر
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("❌ يرجى إدخال معرف المستخدم!\nمثال: `/promote_queen 123456789`")
            return
        
        try:
            user_id = int(command_parts[1].strip())
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً!")
            return
        
        # ترقية المستخدم إلى ملكة
        success = promote_to_queen(user_id)
        
        if success:
            await message.reply(
                f"👑✨ **تمت الترقية الملكية بنجاح!** ✨👑\n\n"
                f"🎭 المستخدم {user_id} أصبح الآن **ملكة**!\n"
                f"💎 يتمتع بجميع الامتيازات الملكية الحصرية\n"
                f"🏰 زواج ملكي مجاني + راتب مضاعف 10 مرات\n\n"
                f"👑 عاشت الملكة الجديدة! 👑"
            )
        else:
            await message.reply(f"❌ فشل في ترقية المستخدم {user_id} إلى ملكة")
        
    except Exception as e:
        logging.error(f"خطأ في ترقية الملكة: {e}")
        await message.reply("❌ حدث خطأ أثناء ترقية الملكة")


@router.message(Command("promote_king"))
async def promote_king_command(message: Message):
    """ترقية مستخدم إلى ملك /promote_king [user_id] - للسيد الأعلى فقط"""
    try:
        from config.hierarchy import is_supreme_master, promote_to_king
        
        # التحقق من أن المستخدم هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            await message.reply("❌ هذا الأمر متاح للسيد الأعلى فقط!")
            return
        
        # الحصول على معرف المستخدم من الأمر
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("❌ يرجى إدخال معرف المستخدم!\nمثال: `/promote_king 123456789`")
            return
        
        try:
            user_id = int(command_parts[1].strip())
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً!")
            return
        
        # ترقية المستخدم إلى ملك
        success = promote_to_king(user_id)
        
        if success:
            await message.reply(
                f"👑✨ **تمت الترقية الملكية بنجاح!** ✨👑\n\n"
                f"🎭 المستخدم {user_id} أصبح الآن **ملك**!\n"
                f"💎 يتمتع بجميع الامتيازات الملكية الحصرية\n"
                f"🏰 زواج ملكي مجاني + راتب مضاعف 10 مرات\n\n"
                f"👑 عاش الملك الجديد! 👑"
            )
        else:
            await message.reply(f"❌ فشل في ترقية المستخدم {user_id} إلى ملك")
        
    except Exception as e:
        logging.error(f"خطأ في ترقية الملك: {e}")
        await message.reply("❌ حدث خطأ أثناء ترقية الملك")


@router.message(Command("demote_royal"))
async def demote_royal_command(message: Message):
    """تنزيل مستخدم من المستوى الملكي /demote_royal [user_id] - للسيد الأعلى فقط"""
    try:
        from config.hierarchy import is_supreme_master, demote_from_royalty
        
        # التحقق من أن المستخدم هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            await message.reply("❌ هذا الأمر متاح للسيد الأعلى فقط!")
            return
        
        # الحصول على معرف المستخدم من الأمر
        command_parts = message.text.split()
        if len(command_parts) < 2:
            await message.reply("❌ يرجى إدخال معرف المستخدم!\nمثال: `/demote_royal 123456789`")
            return
        
        try:
            user_id = int(command_parts[1].strip())
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً!")
            return
        
        # تنزيل المستخدم من المستوى الملكي
        success = demote_from_royalty(user_id)
        
        if success:
            await message.reply(
                f"📉 **تم التنزيل من المستوى الملكي**\n\n"
                f"👤 المستخدم {user_id} لم يعد ملكاً أو ملكة\n"
                f"🔄 تمت إعادته إلى مستوى السيد\n"
                f"❌ فقد جميع الامتيازات الملكية"
            )
        else:
            await message.reply(f"❌ فشل في تنزيل المستخدم {user_id} من المستوى الملكي")
        
    except Exception as e:
        logging.error(f"خطأ في تنزيل الملكي: {e}")
        await message.reply("❌ حدث خطأ أثناء تنزيل المستخدم من المستوى الملكي")


@router.message(Command("royal_status"))
async def royal_status_command(message: Message):
    """عرض حالة العائلة الملكية /royal_status - للسيد الأعلى فقط"""
    try:
        from config.hierarchy import is_supreme_master, ROYALTY
        
        # التحقق من أن المستخدم هو السيد الأعلى
        if not is_supreme_master(message.from_user.id):
            await message.reply("❌ هذا الأمر متاح للسيد الأعلى فقط!")
            return
        
        kings = ROYALTY["KINGS"]
        queens = ROYALTY["QUEENS"]
        
        status_message = f"""
👑 **حالة العائلة الملكية** 👑

🤴 **الملوك ({len(kings)}):**
"""
        
        if kings:
            for king_id in kings:
                status_message += f"• {king_id}\n"
        else:
            status_message += "• لا يوجد ملوك حالياً\n"
        
        status_message += f"""
👸 **الملكات ({len(queens)}):**
"""
        
        if queens:
            for queen_id in queens:
                status_message += f"• {queen_id}\n"
        else:
            status_message += "• لا يوجد ملكات حالياً\n"
        
        status_message += f"""
✨ **إجمالي العائلة الملكية:** {len(kings) + len(queens)} أفراد

🎭 **الأوامر المتاحة:**
• `/promote_king [user_id]` - ترقية إلى ملك
• `/promote_queen [user_id]` - ترقية إلى ملكة  
• `/demote_royal [user_id]` - تنزيل من المستوى الملكي
        """
        
        await message.reply(status_message.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة العائلة الملكية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض حالة العائلة الملكية")


@router.message(Command("groups"))
async def groups_command(message: Message):
    """أمر المجموعات /groups - يعمل فقط في القناة الفرعية للإشعارات"""
    try:
        # التحقق من أن الأمر تم استخدامه في القناة الفرعية فقط
        if str(message.chat.id) != str(NOTIFICATION_CHANNEL["chat_id"]):
            # لا نرد إذا تم استخدام الأمر في مكان آخر
            return
        
        # التحقق من أن المستخدم مدير
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط!")
            return
        
        from config.hierarchy import GROUP_OWNERS, MODERATORS
        from modules.notification_manager import NotificationManager
        
        # جمع معلومات المجموعات من البيانات المتاحة
        all_groups = set()
        all_groups.update(GROUP_OWNERS.keys())
        all_groups.update(MODERATORS.keys())
        
        if not all_groups:
            await message.reply("📝 لا توجد مجموعات مسجلة في النظام حالياً.")
            return
        
        notification_manager = NotificationManager(message.bot)
        groups_info = []
        
        for group_id in all_groups:
            try:
                # محاولة الحصول على معلومات المجموعة
                chat = await message.bot.get_chat(group_id)
                members_count = await message.bot.get_chat_member_count(group_id)
                
                # جمع معلومات المشرفين
                owners = GROUP_OWNERS.get(group_id, [])
                moderators = MODERATORS.get(group_id, [])
                
                group_info = {
                    'title': chat.title,
                    'id': group_id,
                    'username': chat.username or 'غير متاح',
                    'members_count': members_count,
                    'owners_count': len(owners),
                    'moderators_count': len(moderators),
                    'type': chat.type
                }
                groups_info.append(group_info)
                
            except Exception as group_error:
                logging.warning(f"لا يمكن الوصول للمجموعة {group_id}: {group_error}")
                # إضافة معلومات أساسية حتى لو فشل جلب التفاصيل
                owners = GROUP_OWNERS.get(group_id, [])
                moderators = MODERATORS.get(group_id, [])
                group_info = {
                    'title': f'مجموعة غير متاحة (ID: {group_id})',
                    'id': group_id,
                    'username': 'غير متاح',
                    'members_count': 'غير متاح',
                    'owners_count': len(owners),
                    'moderators_count': len(moderators),
                    'type': 'غير محدد'
                }
                groups_info.append(group_info)
        
        # تنسيق الرسالة
        if groups_info:
            uptime = await notification_manager.get_uptime()
            
            groups_text = ""
            for i, group in enumerate(groups_info, 1):
                link = f"https://t.me/{group['username']}" if group['username'] != 'غير متاح' else "غير متاح"
                groups_text += f"""
{i}. 🏷️ **{group['title']}**
   🆔 المعرف: `{group['id']}`
   👤 اسم المستخدم: @{group['username']}
   🔗 الرابط: {link}
   👥 الأعضاء: {group['members_count']}
   👑 المالكين: {group['owners_count']}
   🔧 المشرفين: {group['moderators_count']}
   📝 النوع: {group['type']}

"""
            
            final_message = f"""
📊 **قائمة المجموعات المسجلة في نظام يوكي**

🤖 **معلومات البوت:**
⏱️ وقت التشغيل: {uptime}
📈 إجمالي المجموعات: {len(groups_info)}
⏰ آخر تحديث: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🏘️ **المجموعات:**
{groups_text}
---
💡 **ملاحظة:** هذه المجموعات مسجلة في نظام إدارة يوكي"""
            
            # تقسيم الرسالة إذا كانت طويلة جداً
            if len(final_message) > 4096:
                # إرسال معلومات البوت أولاً
                header = f"""
📊 **قائمة المجموعات المسجلة في نظام يوكي**

🤖 **معلومات البوت:**
⏱️ وقت التشغيل: {uptime}
📈 إجمالي المجموعات: {len(groups_info)}
⏰ آخر تحديث: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🏘️ **المجموعات:**"""
                
                await message.reply(header)
                
                # تقسيم المجموعات
                current_message = ""
                for i, group in enumerate(groups_info, 1):
                    link = f"https://t.me/{group['username']}" if group['username'] != 'غير متاح' else "غير متاح"
                    group_text = f"""
{i}. 🏷️ **{group['title']}**
   🆔 المعرف: `{group['id']}`
   👤 اسم المستخدم: @{group['username']}
   🔗 الرابط: {link}
   👥 الأعضاء: {group['members_count']}
   👑 المالكين: {group['owners_count']}
   🔧 المشرفين: {group['moderators_count']}
   📝 النوع: {group['type']}

"""
                    
                    if len(current_message + group_text) > 4000:
                        await message.reply(current_message)
                        current_message = group_text
                    else:
                        current_message += group_text
                
                if current_message:
                    await message.reply(current_message + "\n---\n💡 **ملاحظة:** هذه المجموعات مسجلة في نظام إدارة يوكي")
            else:
                await message.reply(final_message)
        else:
            await message.reply("📝 لا توجد مجموعات متاحة حالياً.")
            
    except Exception as e:
        logging.error(f"خطأ في أمر المجموعات: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات المجموعات.")


# أوامر الذكاء الاصطناعي الجديدة
from modules.ai_integration_handler import ai_integration


# أوامر الذكاء الاصطناعي بالعربية
@router.message(F.text.in_(["تحليل اقتصادي", "تحليل ذكي", "حلل وضعي", "تحليل مالي"]))
@user_required
async def ai_analysis_arabic_command(message: Message):
    """تحليل اقتصادي ذكي شخصي"""
    try:
        analysis = await ai_integration.generate_economic_analysis(
            message.from_user.id, message.chat.id
        )
        await message.reply(analysis, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في التحليل الاقتصادي الذكي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_analysis"))
@user_required
async def ai_analysis_command(message: Message):
    """تحليل اقتصادي ذكي شخصي /ai_analysis"""
    try:
        analysis = await ai_integration.generate_economic_analysis(
            message.from_user.id, message.chat.id
        )
        await message.reply(analysis, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في التحليل الاقتصادي الذكي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["استراتيجية ذكية", "استراتيجية استثمار", "اقترح استراتيجية", "نصائح استثمار"]))
@user_required
async def ai_strategy_arabic_command(message: Message):
    """اقتراح استراتيجية استثمار ذكية"""
    try:
        strategy = await ai_integration.suggest_investment_strategy(
            message.from_user.id, message.chat.id
        )
        await message.reply(strategy, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في اقتراح الاستراتيجية الذكية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_strategy"))
@user_required
async def ai_strategy_command(message: Message):
    """اقتراح استراتيجية استثمار ذكية /ai_strategy"""
    try:
        strategy = await ai_integration.suggest_investment_strategy(
            message.from_user.id, message.chat.id
        )
        await message.reply(strategy, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في اقتراح الاستراتيجية الذكية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["العاب ذكية", "اقترح لعبة", "العاب مناسبة", "ألعاب ذكية"]))
@user_required
async def ai_games_arabic_command(message: Message):
    """اقتراح ألعاب ذكية مخصصة"""
    try:
        games_suggestion = await ai_integration.get_game_suggestions(
            message.from_user.id, message.chat.id
        )
        await message.reply(games_suggestion, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في اقتراح الألعاب الذكية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_games"))
@user_required
async def ai_games_command(message: Message):
    """اقتراح ألعاب ذكية مخصصة /ai_games"""
    try:
        games_suggestion = await ai_integration.get_game_suggestions(
            message.from_user.id, message.chat.id
        )
        await message.reply(games_suggestion, parse_mode='Markdown')
    except Exception as e:
        logging.error(f"خطأ في اقتراح الألعاب الذكية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["كويز ذكي", "اختبار ذكي", "سؤال وجواب", "اختبار تكيفي"]))
@user_required
async def smart_quiz_arabic_command(message: Message):
    """بدء كويز ذكي تكيفي"""
    try:
        # تحديد الفئة من النص
        category = 'general'
        if 'رياضة' in message.text or 'رياضيات' in message.text:
            category = 'math'
        elif 'العاب' in message.text or 'ألعاب' in message.text:
            category = 'gaming'
        
        quiz_data = await ai_integration.start_adaptive_quiz(
            message.from_user.id, message.chat.id, category
        )
        
        if quiz_data:
            quiz_text = f"""
🧠 **{quiz_data['quiz_id']}**

📚 **الفئة:** {quiz_data['category']}
📊 **الصعوبة:** {quiz_data['difficulty']}
❓ **عدد الأسئلة:** {quiz_data['total_questions']}
⏰ **الوقت المحدد:** {quiz_data['time_limit']} ثانية
🏆 **مكافأة XP:** {quiz_data['xp_reward']}

**السؤال الأول:**
{quiz_data['questions'][0]['q']}

**الخيارات:**
{chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(quiz_data['questions'][0]['options'])])}

💡 أرسل رقم الإجابة (1-4)
            """
            await message.reply(quiz_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن إنشاء كويز في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء الكويز الذكي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("smart_quiz"))
@user_required
async def smart_quiz_command(message: Message):
    """بدء كويز ذكي تكيفي /smart_quiz"""
    try:
        # استخراج الفئة من الأمر إذا وجدت
        command_parts = message.text.split()
        category = 'general'
        if len(command_parts) > 1:
            category = command_parts[1].lower()
            if category not in ['general', 'math', 'gaming']:
                category = 'general'
        
        quiz_data = await ai_integration.start_adaptive_quiz(
            message.from_user.id, message.chat.id, category
        )
        
        if quiz_data:
            quiz_text = f"""
🧠 **{quiz_data['quiz_id']}**

📚 **الفئة:** {quiz_data['category']}
📊 **الصعوبة:** {quiz_data['difficulty']}
❓ **عدد الأسئلة:** {quiz_data['total_questions']}
⏰ **الوقت المحدد:** {quiz_data['time_limit']} ثانية
🏆 **مكافأة XP:** {quiz_data['xp_reward']}

**السؤال الأول:**
{quiz_data['questions'][0]['q']}

**الخيارات:**
{chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(quiz_data['questions'][0]['options'])])}

💡 أرسل رقم الإجابة (1-4)
            """
            await message.reply(quiz_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن إنشاء كويز في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء الكويز الذكي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["تحدي اقتصادي", "تحدي ذكي", "تحدي مالي", "اختبار اقتصادي"]))
@user_required
async def eco_challenge_arabic_command(message: Message):
    """بدء تحدي اقتصادي ذكي"""
    try:
        challenge_data = await ai_integration.start_economic_challenge(
            message.from_user.id, message.chat.id
        )
        
        if challenge_data:
            challenge_text = f"""
💼 **{challenge_data['title']}**

📋 **الوصف:** {challenge_data['description']}

🎯 **السيناريو:**
{challenge_data['scenario']['situation']}

**الخيارات:**
{chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(challenge_data['scenario']['options'])])}

🏆 **مكافأة XP:** {challenge_data['xp_reward']}
💰 **مكافأة ثروة:** {challenge_data['wealth_bonus']}$

💡 أرسل رقم الإجابة (1-4)
            """
            await message.reply(challenge_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن إنشاء تحدي في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء التحدي الاقتصادي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("eco_challenge"))
@user_required
async def eco_challenge_command(message: Message):
    """بدء تحدي اقتصادي ذكي /eco_challenge"""
    try:
        challenge_data = await ai_integration.start_economic_challenge(
            message.from_user.id, message.chat.id
        )
        
        if challenge_data:
            challenge_text = f"""
💼 **{challenge_data['title']}**

📋 **الوصف:** {challenge_data['description']}

🎯 **السيناريو:**
{challenge_data['scenario']['situation']}

**الخيارات:**
{chr(10).join([f"{i+1}. {opt}" for i, opt in enumerate(challenge_data['scenario']['options'])])}

🏆 **مكافأة XP:** {challenge_data['xp_reward']}
💰 **مكافأة ثروة:** {challenge_data['wealth_bonus']}$

💡 أرسل رقم الإجابة (1-4)
            """
            await message.reply(challenge_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن إنشاء تحدي في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء التحدي الاقتصادي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["قصة ذكية", "قصة تفاعلية", "احكي قصة", "قصة مغامرة"]))
@user_required
async def ai_story_arabic_command(message: Message):
    """بدء قصة تفاعلية ذكية"""
    try:
        story_data = await ai_integration.start_interactive_story(
            message.from_user.id, message.chat.id
        )
        
        if story_data:
            story_text = f"""
📖 **{story_data['title']}**

{story_data['chapter_data']['text']}

**الخيارات:**
{chr(10).join([f"{i+1}. {choice['text']}" for i, choice in enumerate(story_data['chapter_data']['choices'])])}

🏆 **مكافأة XP:** {story_data['xp_reward']}

💡 أرسل رقم الاختيار (1-{len(story_data['chapter_data']['choices'])})
            """
            await message.reply(story_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن بدء القصة في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء القصة التفاعلية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_story"))
@user_required
async def ai_story_command(message: Message):
    """بدء قصة تفاعلية ذكية /ai_story"""
    try:
        story_data = await ai_integration.start_interactive_story(
            message.from_user.id, message.chat.id
        )
        
        if story_data:
            story_text = f"""
📖 **{story_data['title']}**

{story_data['chapter_data']['text']}

**الخيارات:**
{chr(10).join([f"{i+1}. {choice['text']}" for i, choice in enumerate(story_data['chapter_data']['choices'])])}

🏆 **مكافأة XP:** {story_data['xp_reward']}

💡 أرسل رقم الاختيار (1-{len(story_data['chapter_data']['choices'])})
            """
            await message.reply(story_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن بدء القصة في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء القصة التفاعلية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["معركة ذكية", "تحدي يوكي", "معركة مع يوكي", "باتل ذكي"]))
@user_required
async def ai_battle_arabic_command(message: Message):
    """بدء معركة ذكية مع يوكي"""
    try:
        battle_data = await ai_integration.start_ai_battle(
            message.from_user.id, message.chat.id
        )
        
        if battle_data:
            battle_text = f"""
⚔️ **معركة الذكاء مع يوكي**

🎮 **نوع التحدي:** {battle_data['type_name']}
📊 **مستوى الصعوبة:** {battle_data['difficulty_level']}/5
⏰ **الوقت المحدد:** {battle_data['time_limit']} ثانية
🏆 **مكافأة XP:** {battle_data['xp_reward']}

**التحدي:**
{battle_data['challenge']['question']}

💡 أرسل إجابتك الآن!

🤖 يوكي مستعد للتحدي... هل أنت؟
            """
            await message.reply(battle_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن بدء معركة الذكاء في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء معركة الذكاء: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_battle"))
@user_required
async def ai_battle_command(message: Message):
    """بدء معركة ذكية مع يوكي /ai_battle"""
    try:
        battle_data = await ai_integration.start_ai_battle(
            message.from_user.id, message.chat.id
        )
        
        if battle_data:
            battle_text = f"""
⚔️ **معركة الذكاء مع يوكي**

🎮 **نوع التحدي:** {battle_data['type_name']}
📊 **مستوى الصعوبة:** {battle_data['difficulty_level']}/5
⏰ **الوقت المحدد:** {battle_data['time_limit']} ثانية
🏆 **مكافأة XP:** {battle_data['xp_reward']}

**التحدي:**
{battle_data['challenge']['question']}

💡 أرسل إجابتك الآن!

🤖 يوكي مستعد للتحدي... هل أنت؟
            """
            await message.reply(battle_text.strip(), parse_mode='Markdown')
        else:
            await message.reply("❌ لا يمكن بدء معركة الذكاء في الوقت الحالي")
            
    except Exception as e:
        logging.error(f"خطأ في بدء معركة الذكاء: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(F.text.in_(["حالة الذكاء الاصطناعي", "حالة الانظمة الذكية", "وضع الذكاء", "فحص الانظمة"]))
@user_required
async def ai_status_arabic_command(message: Message):
    """حالة أنظمة الذكاء الاصطناعي"""
    try:
        status = await ai_integration.get_ai_system_status()
        
        if 'error' not in status:
            status_text = f"""
🤖 **حالة أنظمة الذكاء الاصطناعي**

**النظام الشامل:**
✅ متاح: {'نعم' if status['comprehensive_ai']['available'] else 'لا'}
🔧 المزود: {status['comprehensive_ai']['provider']}
🧠 الذاكرة: {'مفعلة' if status['comprehensive_ai']['memory_enabled'] else 'معطلة'}
🛡️ حماية الشخصية: {'مفعلة' if status['comprehensive_ai']['personality_protection'] else 'معطلة'}

**معالج الرسائل الذكي:**
✅ متاح: {'نعم' if status['smart_processor']['available'] else 'لا'}
🤖 الذكاء الأساسي: {'نعم' if status['smart_processor']['basic_ai'] else 'لا'}
💬 الردود الخاصة: {'محملة' if status['smart_processor']['special_responses'] else 'غير محملة'}
🚫 حماية الكلام البذيء: {'مفعلة' if status['smart_processor']['profanity_protection'] else 'معطلة'}

**النظام الاقتصادي الذكي:**
✅ متاح: {'نعم' if status['intelligent_economics']['available'] else 'لا'}
📊 الاستراتيجيات: {status['intelligent_economics']['strategies_loaded']} استراتيجية
📈 أنماط السوق: {status['intelligent_economics']['market_patterns']} نمط

**نظام الألعاب الذكية:**
✅ متاح: {'نعم' if status['intelligent_games']['available'] else 'لا'}
🎮 الألعاب: {status['intelligent_games']['games_loaded']} لعبة
📚 القصص: {status['intelligent_games']['stories_loaded']} قصة

**إعدادات التكامل:**
🔧 الردود الذكية: {'مفعلة' if status['integration_settings']['ai_responses_enabled'] else 'معطلة'}
💰 الاقتصاد الذكي: {'مفعل' if status['integration_settings']['smart_economics_enabled'] else 'معطل'}
🎯 الألعاب الذكية: {'مفعلة' if status['integration_settings']['intelligent_games_enabled'] else 'معطلة'}
📚 وضع التعلم: {'مفعل' if status['integration_settings']['learning_mode'] else 'معطل'}
💡 الاقتراحات التلقائية: {'مفعلة' if status['integration_settings']['auto_suggestions'] else 'معطلة'}
            """
            await message.reply(status_text.strip(), parse_mode='Markdown')
        else:
            await message.reply(f"❌ خطأ في الحصول على حالة الأنظمة: {status['error']}")
            
    except Exception as e:
        logging.error(f"خطأ في عرض حالة أنظمة الذكاء الاصطناعي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("ai_status"))
@user_required
async def ai_status_command(message: Message):
    """حالة أنظمة الذكاء الاصطناعي /ai_status"""
    try:
        status = await ai_integration.get_ai_system_status()
        
        if 'error' not in status:
            status_text = f"""
🤖 **حالة أنظمة الذكاء الاصطناعي**

**النظام الشامل:**
✅ متاح: {'نعم' if status['comprehensive_ai']['available'] else 'لا'}
🔧 المزود: {status['comprehensive_ai']['provider']}
🧠 الذاكرة: {'مفعلة' if status['comprehensive_ai']['memory_enabled'] else 'معطلة'}
🛡️ حماية الشخصية: {'مفعلة' if status['comprehensive_ai']['personality_protection'] else 'معطلة'}

**معالج الرسائل الذكي:**
✅ متاح: {'نعم' if status['smart_processor']['available'] else 'لا'}
🤖 الذكاء الأساسي: {'نعم' if status['smart_processor']['basic_ai'] else 'لا'}
💬 الردود الخاصة: {'محملة' if status['smart_processor']['special_responses'] else 'غير محملة'}
🚫 حماية الكلام البذيء: {'مفعلة' if status['smart_processor']['profanity_protection'] else 'معطلة'}

**النظام الاقتصادي الذكي:**
✅ متاح: {'نعم' if status['intelligent_economics']['available'] else 'لا'}
📊 الاستراتيجيات: {status['intelligent_economics']['strategies_loaded']} استراتيجية
📈 أنماط السوق: {status['intelligent_economics']['market_patterns']} نمط

**نظام الألعاب الذكية:**
✅ متاح: {'نعم' if status['intelligent_games']['available'] else 'لا'}
🎮 الألعاب: {status['intelligent_games']['games_loaded']} لعبة
📚 القصص: {status['intelligent_games']['stories_loaded']} قصة

**إعدادات التكامل:**
🔧 الردود الذكية: {'مفعلة' if status['integration_settings']['ai_responses_enabled'] else 'معطلة'}
💰 الاقتصاد الذكي: {'مفعل' if status['integration_settings']['smart_economics_enabled'] else 'معطل'}
🎯 الألعاب الذكية: {'مفعلة' if status['integration_settings']['intelligent_games_enabled'] else 'معطلة'}
📚 وضع التعلم: {'مفعل' if status['integration_settings']['learning_mode'] else 'معطل'}
💡 الاقتراحات التلقائية: {'مفعلة' if status['integration_settings']['auto_suggestions'] else 'معطلة'}
            """
            await message.reply(status_text.strip(), parse_mode='Markdown')
        else:
            await message.reply(f"❌ خطأ في الحصول على حالة الأنظمة: {status['error']}")
            
    except Exception as e:
        logging.error(f"خطأ في عرض حالة أنظمة الذكاء الاصطناعي: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])



# أوامر إدارة نظام كشف المحتوى الإباحي
@router.message(F.text.in_({"نظام كشف المحتوى", "كشف المحتوى", "نظام الحماية", "قائمة الحماية", "إعدادات الحماية"}))
@group_only
async def content_filter_command(message: Message):
    """إدارة نظام كشف المحتوى الإباحي"""
    try:
        # التحقق من الصلاحيات (مالكين أو سادة فقط)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not has_permission(user_id, AdminLevel.GROUP_OWNER, chat_id):
            await message.reply("❌ هذا الأمر متاح لمالكي المجموعات والسادة فقط")
            return
        status = "🟢 مفعل" if content_filter.is_enabled() else "🔴 معطل"
        
        filter_menu = f"""
🛡️ **نظام كشف المحتوى الإباحي**

📊 **الحالة الحالية:** {status}

⚙️ **الأوامر المتاحة:**
• `تفعيل نظام الحماية` - تفعيل النظام
• `إلغاء نظام الحماية` - إلغاء تفعيل النظام
• `حالة نظام الحماية` - حالة النظام
• `تفعيل كشف المحتوى` - بديل للتفعيل
• `إلغاء كشف المحتوى` - بديل للإلغاء

📋 **معلومات النظام:**
• يستخدم Google AI لتحليل الصور
• يحذف المحتوى غير المناسب تلقائياً
• يرسل تحذيرات للمديرين
• يدعم الصور والملفات والفيديوهات

🔧 **مستويات الثقة:**
• 70%+ للصور - حذف تلقائي
• 60%+ للملفات - حذف تلقائي  
• 50%+ للفيديوهات - حذف تلقائي
        """
        
        await message.reply(filter_menu.strip())
        
    except Exception as e:
        logging.error(f"خطأ في قائمة كشف المحتوى: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات النظام")


@router.message(F.text.in_({"تفعيل كشف المحتوى", "تفعيل نظام كشف المحتوى", "تشغيل كشف المحتوى", "تفعيل نظام الحماية", "تشغيل نظام الحماية"}))
@group_only
async def enable_filter_command(message: Message):
    """تفعيل نظام كشف المحتوى"""
    try:
        # التحقق من الصلاحيات (مالكين أو سادة فقط)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not has_permission(user_id, AdminLevel.GROUP_OWNER, chat_id):
            await message.reply("❌ هذا الأمر متاح لمالكي المجموعات والسادة فقط")
            return
        if content_filter.is_enabled():
            await message.reply(
                "✅ **نظام كشف المحتوى مفعل بالفعل**\\n\\n"
                "🛡️ النظام يعمل بشكل طبيعي\\n"
                "📸 جميع الصور والملفات تُفحص تلقائياً"
            )
            return
        
        content_filter.toggle_system(True)
        
        await message.reply(
            "✅ **تم تفعيل نظام كشف المحتوى بنجاح!**\\n\\n"
            "🛡️ النظام الآن يحمي المجموعة من:\\n"
            "• الصور الإباحية\\n"
            "• المحتوى غير المناسب\\n"
            "• الملفات المشبوهة\\n"
            "• الفيديوهات غير اللائقة\\n\\n"
            "⚡ سيتم حذف المحتوى المشبوه تلقائياً"
        )
        
        logging.info(f"تم تفعيل نظام كشف المحتوى بواسطة المدير {message.from_user.id}")
        
    except Exception as e:
        logging.error(f"خطأ في تفعيل كشف المحتوى: {e}")
        await message.reply("❌ حدث خطأ أثناء تفعيل النظام")


@router.message(F.text.in_({"إلغاء كشف المحتوى", "إيقاف كشف المحتوى", "تعطيل كشف المحتوى", "إلغاء نظام الحماية", "إيقاف نظام الحماية"}))
@group_only
async def disable_filter_command(message: Message):
    """إلغاء تفعيل نظام كشف المحتوى"""
    try:
        # التحقق من الصلاحيات (مالكين أو سادة فقط)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not has_permission(user_id, AdminLevel.GROUP_OWNER, chat_id):
            await message.reply("❌ هذا الأمر متاح لمالكي المجموعات والسادة فقط")
            return
        if not content_filter.is_enabled():
            await message.reply(
                "🔴 **نظام كشف المحتوى معطل بالفعل**\\n\\n"
                "⚠️ المجموعة غير محمية من المحتوى الإباحي\\n"
                "💡 استخدم `تفعيل كشف المحتوى` لتفعيل الحماية"
            )
            return
        
        content_filter.toggle_system(False)
        
        await message.reply(
            "🔴 **تم إلغاء تفعيل نظام كشف المحتوى**\\n\\n"
            "⚠️ تحذير: المجموعة لم تعد محمية\\n"
            "📸 لن يتم فحص الصور والملفات\\n"
            "🚨 قد يتم نشر محتوى غير مناسب\\n\\n"
            "💡 يمكنك إعادة التفعيل بـ `تفعيل كشف المحتوى`"
        )
        
        logging.warning(f"تم إلغاء تفعيل نظام كشف المحتوى بواسطة المدير {message.from_user.id}")
        
    except Exception as e:
        logging.error(f"خطأ في إلغاء تفعيل كشف المحتوى: {e}")
        await message.reply("❌ حدث خطأ أثناء إلغاء تفعيل النظام")


@router.message(F.text.in_({"حالة كشف المحتوى", "حالة نظام كشف المحتوى", "وضع كشف المحتوى", "حالة نظام الحماية", "وضع الحماية"}))
@group_only
async def filter_status_command(message: Message):
    """حالة نظام كشف المحتوى"""
    try:
        # التحقق من الصلاحيات (مالكين أو سادة فقط)
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not has_permission(user_id, AdminLevel.GROUP_OWNER, chat_id):
            await message.reply("❌ هذا الأمر متاح لمالكي المجموعات والسادة فقط")
            return
        is_enabled = content_filter.is_enabled()
        num_keys = len(content_filter.api_keys)
        current_key = content_filter.current_key_index + 1 if content_filter.api_keys else 0
        
        status_icon = "🟢" if is_enabled else "🔴"
        status_text = "مفعل ويعمل" if is_enabled else "معطل"
        
        status_info = f"""
🛡️ **حالة نظام كشف المحتوى**

{status_icon} **الحالة:** {status_text}
🔑 **مفاتيح API:** {num_keys} متوفر
📊 **المفتاح الحالي:** {current_key}/{num_keys}

📈 **الإحصائيات:**
• الصور: فحص مع حذف تلقائي عند 70%+
• الملفات: فحص اسم الملف والمحتوى عند 60%+
• الفيديوهات: فحص اسم الملف عند 50%+
• الصور المتحركة: فحص اسم الملف عند 50%+

🔧 **التقنية المستخدمة:**
• Google AI (Gemini)
• تحليل ذكي للصور
• كشف الكلمات المفاتيح

⚡ **الأداء:**
• استجابة فورية
• دقة عالية في الكشف
• حماية تلقائية
        """
        
        await message.reply(status_info.strip())
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة كشف المحتوى: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات النظام")



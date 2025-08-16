"""
معالج أوامر البوت
Bot Commands Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext

from database.operations import get_or_create_user, update_user_activity
from modules import banks, real_estate, theft, stocks, investment, ranking, administration, farm, castle
from utils.decorators import user_required, admin_required, group_only
from config.settings import SYSTEM_MESSAGES, ADMIN_IDS

router = Router()


@router.message(CommandStart())
async def start_command(message: Message, state: FSMContext):
    """أمر البدء /start"""
    try:
        # التحقق من نوع المحادثة
        if message.chat.type == 'private':
            # رسالة في الخاص - طلب إضافة البوت للمجموعة
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

➕ **لإضافتي للمجموعة:**
اضغط على اسمي واختر "Add to Group" أو انسخ اسم المستخدم: @theyuki_bot

بعد إضافتي للمجموعة، اكتب /start في المجموعة لبدء اللعب! 🚀
            """
            await message.reply(welcome_text)
            
        else:
            # في مجموعة - تسجيل المستخدم وبدء اللعبة
            user = await get_or_create_user(
                message.from_user.id, 
                message.from_user.username or "", 
                message.from_user.first_name or "User"
            )
            await update_user_activity(message.from_user.id)
            
            group_welcome = """
🎮 **مرحباً بكم في بوت الألعاب الاقتصادية!**

🌟 تم تفعيل البوت في هذه المجموعة بنجاح!

🏦 **للبدء في اللعبة:**
اكتب "انشاء حساب بنكي" لاختيار بنكك المفضل وبدء جمع الأموال!

📋 **الأوامر والكلمات المفتاحية:**

💰 **الاقتصاد الأساسي:**
• "رصيد" أو "فلوس" - عرض رصيدك
• "راتب" أو "مرتب" - جمع راتبك اليومي العشوائي
• "بنك" - خدمات البنك والإيداع/السحب

🎯 **الأنشطة الاقتصادية:**
• "استثمار" - استثمار أموالك لزيادة الأرباح
• "اسهم" - تداول في البورصة
• "عقار" - شراء وبيع العقارات
• "سرقة" - آليات السرقة والحماية
• "مزرعة" - زراعة وحصاد المحاصيل
• "قلعة" - بناء وترقية قلعتك
• "ترتيب" - عرض أغنى اللاعبين

💸 **تحويل الأموال:**
• رد على رسالة أي لاعب واكتب "تحويل [المبلغ]"
• مثال: رد على رسالة زميلك واكتب "تحويل 500"

💡 **نصائح للبدء:**
• ابدأ بكتابة "انشاء حساب بنكي" لاختيار البنك
• اجمع راتبك يومياً بكتابة "راتب"
• استثمر أموالك لتصبح الأغنى في المجموعة

استمتعوا باللعب! 🎉
            """
            await message.reply(group_welcome)
        
    except Exception as e:
        logging.error(f"خطأ في أمر البدء: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("help"))
@user_required
async def help_command(message: Message):
    """أمر المساعدة /help"""
    try:
        await message.reply(SYSTEM_MESSAGES["help"])
    except Exception as e:
        logging.error(f"خطأ في أمر المساعدة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("balance"))
@user_required
async def balance_command(message: Message):
    """عرض الرصيد /balance"""
    try:
        await banks.show_balance(message)
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("daily"))
@user_required
async def daily_command(message: Message):
    """المكافأة اليومية /daily"""
    try:
        await banks.daily_bonus(message)
    except Exception as e:
        logging.error(f"خطأ في المكافأة اليومية: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("transfer"))
@user_required
async def transfer_command(message: Message, state: FSMContext):
    """تحويل الأموال /transfer"""
    try:
        await banks.start_transfer(message, state)
    except Exception as e:
        logging.error(f"خطأ في تحويل الأموال: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])


@router.message(Command("bank"))
@user_required
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

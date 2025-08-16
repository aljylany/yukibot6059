"""
وحدة البنوك والخدمات المصرفية
Banks and Banking Services Module
"""

import logging
import random
from datetime import datetime, date
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import get_user, get_or_create_user, update_user_balance, update_user_bank_balance, add_transaction, update_user_activity
from utils.states import BanksStates
from utils.helpers import format_number, is_valid_amount, parse_user_mention
from config.settings import GAME_SETTINGS

# أنواع البنوك المختلفة
BANK_TYPES = {
    "الأهلي": {
        "name": "بنك الأهلي",
        "description": "البنك الأكثر أماناً وموثوقية",
        "initial_bonus": 2000,
        "daily_salary": (200, 400),
        "interest_rate": 0.03,
        "emoji": "🏛️"
    },
    "الراجحي": {
        "name": "مصرف الراجحي",
        "description": "البنك الإسلامي الرائد",
        "initial_bonus": 1500,
        "daily_salary": (150, 350),
        "interest_rate": 0.025,
        "emoji": "🕌"
    },
    "سامبا": {
        "name": "بنك سامبا",
        "description": "البنك العالمي للاستثمار",
        "initial_bonus": 2500,
        "daily_salary": (250, 500),
        "interest_rate": 0.035,
        "emoji": "🌍"
    },
    "الرياض": {
        "name": "بنك الرياض",
        "description": "بنك الاستثمار والتطوير",
        "initial_bonus": 1800,
        "daily_salary": (180, 380),
        "interest_rate": 0.028,
        "emoji": "🏙️"
    }
}


async def start_bank_selection(message: Message):
    """بدء عملية اختيار البنك للمستخدمين الجدد"""
    try:
        banks_list = "🏦 **اختر البنك المناسب لك:**\n\n"
        
        for key, bank in BANK_TYPES.items():
            banks_list += f"{bank['emoji']} **{bank['name']}**\n"
            banks_list += f"📄 {bank['description']}\n"
            banks_list += f"💰 مكافأة التسجيل: {format_number(bank['initial_bonus'])}$\n"
            banks_list += f"💼 الراتب اليومي: {bank['daily_salary'][0]}-{bank['daily_salary'][1]}$\n"
            banks_list += f"📈 معدل الفائدة: {bank['interest_rate']*100:.1f}%\n\n"
            banks_list += f"اكتب '{key}' لاختيار هذا البنك\n\n"
        
        banks_list += "💡 **نصائح:**\n"
        banks_list += "• كل بنك له مميزات مختلفة\n"
        banks_list += "• ستحصل على راتب يومي عشوائي\n"
        banks_list += "• يمكنك استثمار أموالك لزيادة الأرباح\n"
        
        await message.reply(banks_list)
        
        # إعداد المعرف للحالة - سيتم تطبيقه في معالج الرسائل
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة البنوك: {e}")
        await message.reply("❌ حدث خطأ في عرض البنوك")


async def process_bank_selection(message: Message, state: FSMContext):
    """معالجة اختيار البنك"""
    try:
        selected_bank = message.text.strip()
        
        if selected_bank not in BANK_TYPES:
            available_banks = ", ".join(BANK_TYPES.keys())
            await message.reply(f"❌ اختيار غير صحيح!\n\nالبنوك المتاحة: {available_banks}")
            return
        
        bank_info = BANK_TYPES[selected_bank]
        
        # إنشاء المستخدم مع البنك المختار
        user = await get_or_create_user(
            message.from_user.id,
            message.from_user.username or "",
            message.from_user.first_name or "لاعب"
        )
        
        # إضافة مكافأة التسجيل
        initial_balance = bank_info["initial_bonus"]
        await update_user_balance(message.from_user.id, initial_balance)
        
        # تسجيل معاملة المكافأة
        await add_transaction(
            message.from_user.id,
            "مكافأة التسجيل",
            initial_balance,
            "bonus"
        )
        
        # رسالة الترحيب مع تفاصيل البنك
        welcome_msg = f"""
🎉 **مبروك! تم إنشاء حسابك بنجاح!**

{bank_info['emoji']} **{bank_info['name']}**
💰 رصيدك الحالي: {format_number(initial_balance)}$
💼 راتبك اليومي: {bank_info['daily_salary'][0]}-{bank_info['daily_salary'][1]}$
📈 معدل الفائدة: {bank_info['interest_rate']*100:.1f}%

🎮 **الآن يمكنك:**
• كتابة 'راتب' لجمع راتبك اليومي
• كتابة 'رصيد' لعرض رصيدك
• كتابة 'استثمار' للاستثمار وزيادة أموالك
• كتابة 'اسهم' للتداول في البورصة

💡 **نصيحة:** اجمع راتبك يومياً واستثمر أموالك لتصبح الأغنى في المجموعة!
        """
        
        await message.reply(welcome_msg)
        await state.clear()
        
        # إضافة راتب يومي فوري كهدية
        daily_salary = random.randint(*bank_info["daily_salary"])
        new_balance = initial_balance + daily_salary
        await update_user_balance(message.from_user.id, new_balance)
        
        await message.reply(
            f"🎁 **هدية ترحيبية!**\n"
            f"حصلت على راتبك الأول: {format_number(daily_salary)}$\n"
            f"💰 رصيدك الجديد: {format_number(new_balance)}$"
        )
        
    except Exception as e:
        logging.error(f"خطأ في اختيار البنك: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء حسابك")


async def show_balance(message: Message):
    """عرض رصيد المستخدم"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ لم تقم بإنشاء حساب بنكي بعد!\n\nاكتب 'انشاء حساب بنكي' للبدء")
            return
        
        total_balance = user['balance'] + user['bank_balance']
        
        balance_text = f"""
💰 **رصيدك الحالي:**

💵 النقد المتاح: {format_number(user['balance'])}$
🏦 رصيد البنك: {format_number(user['bank_balance'])}$
📊 إجمالي الثروة: {format_number(total_balance)}$

🎮 **الأوامر المتاحة:**
• 'راتب' - اجمع راتبك اليومي
• 'استثمار' - استثمر أموالك
• 'اسهم' - تداول في البورصة
• 'عقار' - اشتري عقارات

💡 نصيحة: احتفظ بأموالك في البنك لحمايتها من السرقة!
        """
        
        await message.reply(balance_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply("❌ حدث خطأ في عرض الرصيد")


async def collect_daily_salary(message: Message):
    """جمع الراتب اليومي العشوائي"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ لم تقم بإنشاء حساب بنكي بعد!\n\nاكتب 'انشاء حساب بنكي' للبدء")
            return
        
        today = date.today()
        last_salary = user.get('last_daily')
        
        # التحقق من آخر راتب
        if last_salary and str(last_salary) == str(today):
            await message.reply("⏰ لقد جمعت راتبك اليومي بالفعل!\n\nعد غداً لجمع راتب جديد.")
            return
        
        # تحديد نوع البنك المختار (افتراضي سامبا للمستخدمين القدامى)
        bank_type = user.get('bank_type', 'سامبا')
        if bank_type not in BANK_TYPES:
            bank_type = 'سامبا'
        
        bank_info = BANK_TYPES[bank_type]
        
        # حساب راتب عشوائي حسب نوع البنك
        min_salary, max_salary = bank_info["daily_salary"]
        daily_salary = random.randint(min_salary, max_salary)
        
        # إضافة مكافآت عشوائية أحياناً
        bonus_chance = random.randint(1, 100)
        bonus = 0
        bonus_msg = ""
        
        if bonus_chance <= 10:  # 10% احتمال مكافأة كبيرة
            bonus = random.randint(500, 1500)
            bonus_msg = f"\n🎉 **مكافأة خاصة:** +{format_number(bonus)}$"
        elif bonus_chance <= 25:  # 15% احتمال مكافأة صغيرة  
            bonus = random.randint(100, 400)
            bonus_msg = f"\n🎁 **مكافأة إضافية:** +{format_number(bonus)}$"
        
        total_earned = daily_salary + bonus
        new_balance = user['balance'] + total_earned
        
        # تحديث الرصيد وتاريخ آخر راتب
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            f"راتب يومي - {bank_info['name']}",
            total_earned,
            "salary"
        )
        
        # رسالة النجاح
        salary_msg = f"""
💼 **راتبك اليومي من {bank_info['emoji']} {bank_info['name']}**

💰 الراتب: {format_number(daily_salary)}${bonus_msg}
📊 إجمالي المبلغ: {format_number(total_earned)}$
💵 رصيدك الجديد: {format_number(new_balance)}$

💡 **نصائح للربح أكثر:**
• استثمر أموالك في الأسهم والعقارات
• اجمع راتبك يومياً بانتظام
• شارك في الأنشطة التجارية للحصول على مكافآت إضافية

عد غداً لجمع راتب جديد! 🎯
        """
        
        await message.reply(salary_msg)
        
    except Exception as e:
        logging.error(f"خطأ في جمع الراتب: {e}")
        await message.reply("❌ حدث خطأ أثناء جمع راتبك")


async def daily_bonus(message: Message):
    """المكافأة اليومية - استخدام النظام الجديد"""
    await collect_daily_salary(message)


async def show_bank_menu(message: Message):
    """عرض قائمة البنك"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ لم تقم بإنشاء حساب بنكي بعد!\n\nاكتب 'انشاء حساب بنكي' للبدء")
            return
        
        bank_text = f"""
🏦 **البنك الخاص بك**

💵 النقد المتاح: {format_number(user['balance'])}$
🏦 رصيد البنك: {format_number(user['bank_balance'])}$

🎮 **الخدمات المتاحة:**
• اكتب 'ايداع [المبلغ]' لإيداع أموال في البنك
• اكتب 'سحب [المبلغ]' لسحب أموال من البنك
• رد على رسالة أي لاعب واكتب 'تحويل [المبلغ]' لتحويل أموال له
• اكتب 'راتب' لجمع راتبك اليومي

💡 **مميزات البنك:**
• حماية أموالك من السرقة
• إمكانية الإيداع والسحب بأوامر بسيطة
• تحويل الأموال بسهولة عن طريق الرد على الرسائل
• راتب يومي عشوائي حسب نوع البنك

💰 **أمثلة:**
• ايداع 1000
• سحب 500
• رد على رسالة اللاعب واكتب: تحويل 200
        """
        
        await message.reply(bank_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة البنك: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة البنك")


async def start_deposit(message: Message, state: FSMContext):
    """بدء عملية الإيداع"""
    try:
        await state.set_state(BanksStates.waiting_deposit_amount)
        await message.reply(
            "💵 **إيداع في البنك**\n\n"
            "كم تريد أن تودع في البنك؟\n"
            "💡 اكتب المبلغ أو اكتب 'الكل' لإيداع جميع أموالك\n\n"
            "❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء الإيداع: {e}")
        await message.reply("❌ حدث خطأ في عملية الإيداع")


async def process_deposit_amount(message: Message, state: FSMContext):
    """معالجة مبلغ الإيداع"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية الإيداع")
            return
        
        # تحديد المبلغ
        if text.lower() in ['الكل', 'كل', 'all']:
            amount = user['balance']
        else:
            if not is_valid_amount(text):
                await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح أو 'الكل'")
                return
            amount = int(text)
        
        # التحقق من صحة المبلغ
        if amount <= 0:
            await message.reply("❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if amount > user['balance']:
            await message.reply(f"❌ ليس لديك رصيد كافٍ!\nرصيدك الحالي: {format_number(user['balance'])}$")
            return
        
        # تنفيذ الإيداع
        new_cash_balance = user['balance'] - amount
        new_bank_balance = user['bank_balance'] + amount
        
        await update_user_balance(message.from_user.id, new_cash_balance)
        await update_user_bank_balance(message.from_user.id, new_bank_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=message.from_user.id,
            transaction_type="bank_deposit",
            amount=amount,
            description="إيداع في البنك"
        )
        
        await message.reply(
            f"✅ **تم الإيداع بنجاح!**\n\n"
            f"💵 المبلغ المودع: {format_number(amount)}$\n"
            f"💰 رصيدك النقدي: {format_number(new_cash_balance)}$\n"
            f"🏦 رصيد البنك: {format_number(new_bank_balance)}$"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الإيداع: {e}")
        await message.reply("❌ حدث خطأ في عملية الإيداع")
        await state.clear()


async def start_withdraw(message: Message, state: FSMContext):
    """بدء عملية السحب"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        if user['bank_balance'] <= 0:
            await message.reply("❌ ليس لديك أموال في البنك للسحب!")
            return
        
        await state.set_state(BanksStates.waiting_withdraw_amount)
        await message.reply(
            f"🏧 **سحب من البنك**\n\n"
            f"💰 رصيد البنك: {format_number(user['bank_balance'])}$\n\n"
            f"كم تريد أن تسحب؟\n"
            f"💡 اكتب المبلغ أو اكتب 'الكل' لسحب جميع أموالك\n\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء السحب: {e}")
        await message.reply("❌ حدث خطأ في عملية السحب")


async def process_withdraw_amount(message: Message, state: FSMContext):
    """معالجة مبلغ السحب"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية السحب")
            return
        
        # تحديد المبلغ
        if text.lower() in ['الكل', 'كل', 'all']:
            amount = user['bank_balance']
        else:
            if not is_valid_amount(text):
                await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح أو 'الكل'")
                return
            amount = int(text)
        
        # التحقق من صحة المبلغ
        if amount <= 0:
            await message.reply("❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if amount > user['bank_balance']:
            await message.reply(f"❌ ليس لديك رصيد كافٍ في البنك!\nرصيد البنك: {format_number(user['bank_balance'])}$")
            return
        
        # تنفيذ السحب
        new_cash_balance = user['balance'] + amount
        new_bank_balance = user['bank_balance'] - amount
        
        await update_user_balance(message.from_user.id, new_cash_balance)
        await update_user_bank_balance(message.from_user.id, new_bank_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=message.from_user.id,
            transaction_type="bank_withdraw",
            amount=amount,
            description="سحب من البنك"
        )
        
        await message.reply(
            f"✅ **تم السحب بنجاح!**\n\n"
            f"💵 المبلغ المسحوب: {format_number(amount)}$\n"
            f"💰 رصيدك النقدي: {format_number(new_cash_balance)}$\n"
            f"🏦 رصيد البنك: {format_number(new_bank_balance)}$"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة السحب: {e}")
        await message.reply("❌ حدث خطأ في عملية السحب")
        await state.clear()


async def start_transfer(message: Message, state: FSMContext):
    """بدء عملية تحويل الأموال"""
    try:
        await state.set_state(BanksStates.waiting_transfer_user)
        await message.reply(
            "💳 **تحويل أموال**\n\n"
            "لمن تريد أن تحول؟\n"
            "💡 يمكنك كتابة:\n"
            "- @username\n"
            "- معرف المستخدم (رقم)\n"
            "- الرد على رسالة الشخص\n\n"
            "❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء التحويل: {e}")
        await message.reply("❌ حدث خطأ في عملية التحويل")


async def process_transfer_user(message: Message, state: FSMContext):
    """معالجة اختيار المستخدم للتحويل"""
    try:
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية التحويل")
            return
        
        # استخراج معرف المستخدم
        target_user_id = await parse_user_mention(text, message)
        
        if not target_user_id:
            await message.reply("❌ لم أتمكن من العثور على هذا المستخدم. حاول مرة أخرى.")
            return
        
        if target_user_id == message.from_user.id:
            await message.reply("❌ لا يمكنك تحويل أموال لنفسك!")
            return
        
        # التحقق من وجود المستخدم المستهدف
        target_user = await get_user(target_user_id)
        if not target_user:
            await message.reply("❌ هذا المستخدم غير مسجل في البوت")
            return
        
        # حفظ معرف المستخدم المستهدف
        await state.update_data(target_user_id=target_user_id, target_username=target_user.get('username', 'مجهول'))
        await state.set_state(BanksStates.waiting_transfer_amount)
        
        user = await get_user(message.from_user.id)
        await message.reply(
            f"💳 **تحويل أموال إلى {target_user.get('username', 'المستخدم')}**\n\n"
            f"💰 رصيدك الحالي: {format_number(user['balance'])}$\n\n"
            f"كم تريد أن تحول؟\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في معالجة المستخدم المستهدف: {e}")
        await message.reply("❌ حدث خطأ، يرجى المحاولة مرة أخرى")


async def process_transfer_amount(message: Message, state: FSMContext):
    """معالجة مبلغ التحويل"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية التحويل")
            return
        
        if not is_valid_amount(text):
            await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح")
            return
        
        amount = int(text)
        
        # التحقق من صحة المبلغ
        if amount <= 0:
            await message.reply("❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if amount > user['balance']:
            await message.reply(f"❌ ليس لديك رصيد كافٍ!\nرصيدك الحالي: {format_number(user['balance'])}$")
            return
        
        # الحصول على بيانات المستخدم المستهدف
        data = await state.get_data()
        target_user_id = data['target_user_id']
        target_username = data['target_username']
        
        target_user = await get_user(target_user_id)
        if not target_user:
            await message.reply("❌ المستخدم المستهدف غير موجود")
            await state.clear()
            return
        
        # تنفيذ التحويل
        new_sender_balance = user['balance'] - amount
        new_receiver_balance = target_user['balance'] + amount
        
        await update_user_balance(message.from_user.id, new_sender_balance)
        await update_user_balance(target_user_id, new_receiver_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=target_user_id,
            transaction_type="transfer",
            amount=amount,
            description=f"تحويل إلى {target_username}"
        )
        
        await message.reply(
            f"✅ **تم التحويل بنجاح!**\n\n"
            f"💸 المبلغ المحول: {format_number(amount)}$\n"
            f"👤 إلى: {target_username}\n"
            f"💰 رصيدك الجديد: {format_number(new_sender_balance)}$"
        )
        
        # إشعار المستقبل
        try:
            await message.bot.send_message(
                target_user_id,
                f"💰 **تم استلام تحويل!**\n\n"
                f"💸 المبلغ: {format_number(amount)}$\n"
                f"👤 من: {message.from_user.username or message.from_user.first_name}\n"
                f"💰 رصيدك الجديد: {format_number(new_receiver_balance)}$"
            )
        except:
            pass  # في حالة فشل إرسال الإشعار
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التحويل: {e}")
        await message.reply("❌ حدث خطأ في عملية التحويل")
        await state.clear()


async def show_bank_balance(message: Message):
    """عرض رصيد البنك"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        await message.reply(
            f"🏦 **رصيد البنك**\n\n"
            f"💰 المبلغ المودع: {format_number(user['bank_balance'])}$\n"
            f"📈 الفائدة اليومية: {format_number(user['bank_balance'] * GAME_SETTINGS['bank_interest_rate'])}$\n"
            f"🛡 حماية كاملة من السرقة"
        )
        
    except Exception as e:
        logging.error(f"خطأ في عرض رصيد البنك: {e}")
        await message.reply("❌ حدث خطأ في عرض رصيد البنك")


async def show_interest_info(message: Message):
    """عرض معلومات الفائدة"""
    try:
        interest_rate = GAME_SETTINGS['bank_interest_rate'] * 100
        
        await message.reply(
            f"📊 **معلومات الفائدة المصرفية**\n\n"
            f"📈 معدل الفائدة: {interest_rate}% يومياً\n"
            f"⏰ يتم احتساب الفائدة تلقائياً كل 24 ساعة\n"
            f"🛡 أموالك محمية من السرقة في البنك\n\n"
            f"💡 **مثال:**\n"
            f"إذا كان لديك 1000$ في البنك\n"
            f"ستحصل على {1000 * GAME_SETTINGS['bank_interest_rate']}$ فائدة يومية"
        )
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات الفائدة: {e}")
        await message.reply("❌ حدث خطأ في عرض معلومات الفائدة")

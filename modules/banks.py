"""
وحدة البنوك والخدمات المصرفية
Banks and Banking Services Module
"""

import logging
from datetime import datetime, date
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, update_user_bank_balance, add_transaction
from utils.states import BanksStates
from utils.helpers import format_number, is_valid_amount, parse_user_mention
from config.settings import GAME_SETTINGS


async def show_balance(message: Message):
    """عرض رصيد المستخدم"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        total_balance = user['balance'] + user['bank_balance']
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🏦 البنك", callback_data="bank_balance"),
                InlineKeyboardButton(text="💳 تحويل", callback_data="bank_transfer")
            ]
        ])
        
        balance_text = f"""
💰 **رصيدك الحالي:**

💵 النقد المتاح: {format_number(user['balance'])}$
🏦 رصيد البنك: {format_number(user['bank_balance'])}$
📊 إجمالي الثروة: {format_number(total_balance)}$

💡 نصيحة: احتفظ بأموالك في البنك لحمايتها من السرقة!
        """
        
        await message.reply(balance_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الرصيد: {e}")
        await message.reply("❌ حدث خطأ في عرض الرصيد")


async def daily_bonus(message: Message):
    """المكافأة اليومية"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        today = date.today()
        last_daily = user.get('last_daily')
        
        # التحقق من آخر مكافأة يومية
        if last_daily and str(last_daily) == str(today):
            await message.reply("⏰ لقد حصلت على مكافأتك اليومية بالفعل!\n\nعد غداً للحصول على مكافأة جديدة.")
            return
        
        # إعطاء المكافأة اليومية
        bonus_amount = GAME_SETTINGS["daily_bonus"]
        new_balance = user['balance'] + bonus_amount
        
        # تحديث الرصيد وتاريخ آخر مكافأة
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=0,  # النظام
            to_user_id=message.from_user.id,
            transaction_type="daily_bonus",
            amount=bonus_amount,
            description="مكافأة يومية"
        )
        
        await message.reply(
            f"🎁 **مكافأة يومية!**\n\n"
            f"تم إضافة {format_number(bonus_amount)}$ إلى رصيدك!\n"
            f"💰 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"📅 عد غداً للحصول على مكافأة جديدة!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في المكافأة اليومية: {e}")
        await message.reply("❌ حدث خطأ في المكافأة اليومية")


async def show_bank_menu(message: Message):
    """عرض قائمة البنك"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 إيداع", callback_data="bank_deposit"),
                InlineKeyboardButton(text="🏧 سحب", callback_data="bank_withdraw")
            ],
            [
                InlineKeyboardButton(text="💰 رصيد البنك", callback_data="bank_balance"),
                InlineKeyboardButton(text="📊 معلومات الفائدة", callback_data="bank_interest")
            ]
        ])
        
        bank_text = f"""
🏦 **البنك الخاص بك**

💵 النقد المتاح: {format_number(user['balance'])}$
🏦 رصيد البنك: {format_number(user['bank_balance'])}$

💡 **مميزات البنك:**
• حماية أموالك من السرقة
• فائدة يومية بنسبة {GAME_SETTINGS['bank_interest_rate']*100}%
• عمليات إيداع وسحب مجانية

اختر العملية المطلوبة:
        """
        
        await message.reply(bank_text, reply_markup=keyboard)
        
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

"""
وحدة الاستثمار
Investment Module
"""

import logging
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import InvestmentStates
from utils.helpers import format_number, is_valid_amount
from config.settings import GAME_SETTINGS

# أنواع الاستثمارات المتاحة
INVESTMENT_TYPES = {
    "savings": {
        "name": "حساب توفير",
        "min_amount": 1000,
        "interest_rate": 0.02,  # 2% شهرياً
        "duration_days": 30,
        "risk": "منخفض",
        "emoji": "💰"
    },
    "bonds": {
        "name": "سندات حكومية",
        "min_amount": 5000,
        "interest_rate": 0.05,  # 5% شهرياً
        "duration_days": 60,
        "risk": "منخفض",
        "emoji": "📋"
    },
    "mutual_funds": {
        "name": "صناديق استثمار",
        "min_amount": 10000,
        "interest_rate": 0.08,  # 8% شهرياً
        "duration_days": 90,
        "risk": "متوسط",
        "emoji": "📊"
    },
    "real_estate": {
        "name": "استثمار عقاري",
        "min_amount": 50000,
        "interest_rate": 0.12,  # 12% شهرياً
        "duration_days": 180,
        "risk": "متوسط",
        "emoji": "🏢"
    },
    "high_yield": {
        "name": "استثمار عالي العائد",
        "min_amount": 100000,
        "interest_rate": 0.20,  # 20% شهرياً
        "duration_days": 365,
        "risk": "عالي",
        "emoji": "🚀"
    }
}


async def show_investment_menu(message: Message):
    """عرض قائمة الاستثمار الرئيسية"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على استثمارات المستخدم
        user_investments = await get_user_investments(message.from_user.id)
        total_investment = sum(inv['amount'] for inv in user_investments)
        expected_returns = sum(inv['amount'] * inv['expected_return'] for inv in user_investments)
        
        investment_text = f"""
💼 **مركز الاستثمار**

💰 رصيدك النقدي: {format_number(user['balance'])}$
📊 إجمالي الاستثمار: {format_number(total_investment)}$
💎 العوائد المتوقعة: {format_number(expected_returns)}$

🎯 عدد الاستثمارات النشطة: {len(user_investments)}

💡 الاستثمار طويل المدى يحقق عوائد أعلى!

📋 **الأوامر المتاحة:**
💼 اكتب: "استثمار جديد" لبدء استثمار
📊 اكتب: "محفظة الاستثمارات" لعرض استثماراتك
💰 اكتب: "سحب استثمار" لسحب استثمار
📈 اكتب: "تقرير الاستثمارات" للإحصائيات
        """
        
        await message.reply(investment_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الاستثمار")


async def show_investment_options(message: Message):
    """عرض خيارات الاستثمار المتاحة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        keyboard_buttons = []
        for inv_type, inv_info in INVESTMENT_TYPES.items():
            affordable = user['balance'] >= inv_info['min_amount']
            button_text = f"{inv_info['emoji']} {inv_info['name']}"
            if not affordable:
                button_text = f"❌ {button_text}"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"investment_create_{inv_type}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        options_text = "💼 **خيارات الاستثمار المتاحة:**\n\n"
        for inv_type, inv_info in INVESTMENT_TYPES.items():
            affordable = "✅" if user['balance'] >= inv_info['min_amount'] else "❌"
            duration_months = inv_info['duration_days'] // 30
            
            options_text += f"{affordable} {inv_info['emoji']} **{inv_info['name']}**\n"
            options_text += f"   💰 الحد الأدنى: {format_number(inv_info['min_amount'])}$\n"
            options_text += f"   📈 العائد: {inv_info['interest_rate']*100:.0f}% شهرياً\n"
            options_text += f"   ⏰ المدة: {duration_months} شهر\n"
            options_text += f"   ⚠️ المخاطر: {inv_info['risk']}\n\n"
        
        options_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$"
        
        await message.reply(options_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الاستثمار")


async def start_investment_process(message: Message, investment_type: str, state: FSMContext):
    """بدء عملية استثمار جديد"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if investment_type not in INVESTMENT_TYPES:
            await message.reply("❌ نوع استثمار غير صحيح")
            return
        
        inv_info = INVESTMENT_TYPES[investment_type]
        
        if user['balance'] < inv_info['min_amount']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"{inv_info['emoji']} {inv_info['name']}\n"
                f"💰 الحد الأدنى: {format_number(inv_info['min_amount'])}$\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        await state.update_data(investment_type=investment_type)
        await state.set_state(InvestmentStates.waiting_investment_amount)
        
        duration_months = inv_info['duration_days'] // 30
        expected_return = inv_info['interest_rate'] * duration_months
        
        await message.reply(
            f"💼 **استثمار جديد - {inv_info['name']}**\n\n"
            f"{inv_info['emoji']} نوع الاستثمار: {inv_info['name']}\n"
            f"📈 العائد الشهري: {inv_info['interest_rate']*100:.0f}%\n"
            f"⏰ مدة الاستثمار: {duration_months} شهر\n"
            f"📊 العائد الإجمالي: {expected_return*100:.0f}%\n"
            f"⚠️ مستوى المخاطر: {inv_info['risk']}\n\n"
            f"💰 الحد الأدنى: {format_number(inv_info['min_amount'])}$\n"
            f"💵 رصيدك: {format_number(user['balance'])}$\n\n"
            f"كم تريد أن تستثمر؟\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء عملية الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عملية الاستثمار")


async def process_investment_amount(message: Message, state: FSMContext):
    """معالجة مبلغ الاستثمار"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية الاستثمار")
            return
        
        if not is_valid_amount(text):
            await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح")
            return
        
        amount = int(text)
        
        # الحصول على بيانات الاستثمار
        data = await state.get_data()
        investment_type = data['investment_type']
        inv_info = INVESTMENT_TYPES[investment_type]
        
        # التحقق من صحة المبلغ
        if amount < inv_info['min_amount']:
            await message.reply(f"❌ المبلغ أقل من الحد الأدنى: {format_number(inv_info['min_amount'])}$")
            return
        
        if amount > user['balance']:
            await message.reply(f"❌ رصيد غير كافٍ!\nرصيدك: {format_number(user['balance'])}$")
            return
        
        # حساب تفاصيل الاستثمار
        duration_months = inv_info['duration_days'] // 30
        expected_return = inv_info['interest_rate'] * duration_months
        maturity_date = datetime.now() + timedelta(days=inv_info['duration_days'])
        total_return = amount + (amount * expected_return)
        
        # تنفيذ الاستثمار
        new_balance = user['balance'] - amount
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة الاستثمار إلى قاعدة البيانات
        await execute_query(
            "INSERT INTO investments (user_id, investment_type, amount, expected_return, maturity_date) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, investment_type, amount, expected_return, maturity_date)
        )
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="investment",
            amount=amount,
            description=f"استثمار في {inv_info['name']}"
        )
        
        await message.reply(
            f"🎉 **تم إنشاء الاستثمار بنجاح!**\n\n"
            f"{inv_info['emoji']} نوع الاستثمار: {inv_info['name']}\n"
            f"💰 المبلغ المستثمر: {format_number(amount)}$\n"
            f"📈 العائد المتوقع: {expected_return*100:.0f}%\n"
            f"💎 المبلغ عند النضج: {format_number(total_return)}$\n"
            f"📅 تاريخ النضج: {maturity_date.strftime('%Y-%m-%d')}\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🎯 سيتم إضافة الأرباح تلقائياً عند النضج!"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة مبلغ الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عملية الاستثمار")
        await state.clear()


async def show_portfolio(message: Message):
    """عرض محفظة الاستثمارات"""
    try:
        user_investments = await get_user_investments(message.from_user.id)
        
        if not user_investments:
            await message.reply("📊 **محفظة الاستثمارات فارغة**\n\nاستخدم /invest لبدء استثمار جديد")
            return
        
        portfolio_text = "📊 **محفظة الاستثمارات**\n\n"
        
        total_investment = 0
        total_expected_return = 0
        active_investments = 0
        
        for inv in user_investments:
            inv_info = INVESTMENT_TYPES.get(inv['investment_type'], {})
            maturity_date = datetime.fromisoformat(inv['maturity_date'])
            days_remaining = (maturity_date - datetime.now()).days
            
            if inv['status'] == 'active':
                status_emoji = "🟢"
                status_text = f"نشط ({days_remaining} يوم متبقي)"
                active_investments += 1
            else:
                status_emoji = "✅"
                status_text = "مكتمل"
            
            expected_amount = inv['amount'] + (inv['amount'] * inv['expected_return'])
            
            portfolio_text += f"{inv_info.get('emoji', '💼')} **{inv_info.get('name', 'استثمار')}**\n"
            portfolio_text += f"   💰 المبلغ: {format_number(inv['amount'])}$\n"
            portfolio_text += f"   📈 العائد: {inv['expected_return']*100:.0f}%\n"
            portfolio_text += f"   💎 المبلغ المتوقع: {format_number(expected_amount)}$\n"
            portfolio_text += f"   {status_emoji} الحالة: {status_text}\n"
            portfolio_text += f"   📅 تاريخ النضج: {maturity_date.strftime('%Y-%m-%d')}\n\n"
            
            total_investment += inv['amount']
            if inv['status'] == 'active':
                total_expected_return += expected_amount
        
        portfolio_text += f"📊 **ملخص المحفظة:**\n"
        portfolio_text += f"💰 إجمالي الاستثمار: {format_number(total_investment)}$\n"
        portfolio_text += f"📈 العائد المتوقع: {format_number(total_expected_return)}$\n"
        portfolio_text += f"🎯 الاستثمارات النشطة: {active_investments}"
        
        await message.reply(portfolio_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض محفظة الاستثمارات: {e}")
        await message.reply("❌ حدث خطأ في عرض محفظة الاستثمارات")


async def show_withdrawal_options(message: Message):
    """عرض خيارات السحب المتاحة"""
    try:
        mature_investments = await get_mature_investments(message.from_user.id)
        
        if not mature_investments:
            await message.reply("❌ لا توجد استثمارات جاهزة للسحب حالياً")
            return
        
        keyboard_buttons = []
        withdrawal_text = "💰 **الاستثمارات المتاحة للسحب:**\n\n"
        
        for inv in mature_investments:
            inv_info = INVESTMENT_TYPES.get(inv['investment_type'], {})
            expected_amount = inv['amount'] + (inv['amount'] * inv['expected_return'])
            
            withdrawal_text += f"{inv_info.get('emoji', '💼')} {inv_info.get('name', 'استثمار')}\n"
            withdrawal_text += f"   💰 المبلغ الأصلي: {format_number(inv['amount'])}$\n"
            withdrawal_text += f"   💎 المبلغ الإجمالي: {format_number(expected_amount)}$\n"
            withdrawal_text += f"   📈 الربح: {format_number(expected_amount - inv['amount'])}$\n\n"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=f"{inv_info.get('emoji', '💼')} سحب {format_number(expected_amount)}$",
                callback_data=f"investment_withdraw_{inv['id']}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.reply(withdrawal_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات السحب: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات السحب")


async def withdraw_investment(message: Message, investment_id: int):
    """سحب استثمار مكتمل"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على بيانات الاستثمار
        investment = await execute_query(
            "SELECT * FROM investments WHERE id = ? AND user_id = ? AND status = 'active'",
            (investment_id, message.from_user.id),
            fetch_one=True
        )
        
        if not investment:
            await message.reply("❌ الاستثمار غير موجود أو تم سحبه بالفعل")
            return
        
        # التحقق من تاريخ النضج
        maturity_date = datetime.fromisoformat(investment['maturity_date'])
        if datetime.now() < maturity_date:
            await message.reply("❌ الاستثمار لم ينضج بعد، لا يمكن سحبه الآن")
            return
        
        # حساب المبلغ الإجمالي
        total_amount = investment['amount'] + (investment['amount'] * investment['expected_return'])
        profit = total_amount - investment['amount']
        
        # تحديث الرصيد
        new_balance = user['balance'] + total_amount
        await update_user_balance(message.from_user.id, new_balance)
        
        # تحديث حالة الاستثمار
        await execute_query(
            "UPDATE investments SET status = 'completed' WHERE id = ?",
            (investment_id,)
        )
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=0,  # النظام
            to_user_id=message.from_user.id,
            transaction_type="investment_return",
            amount=int(total_amount),
            description=f"عائد استثمار {investment['investment_type']}"
        )
        
        inv_info = INVESTMENT_TYPES.get(investment['investment_type'], {})
        
        await message.reply(
            f"🎉 **تم سحب الاستثمار بنجاح!**\n\n"
            f"{inv_info.get('emoji', '💼')} نوع الاستثمار: {inv_info.get('name', 'استثمار')}\n"
            f"💰 المبلغ الأصلي: {format_number(investment['amount'])}$\n"
            f"📈 الربح المحقق: {format_number(profit)}$\n"
            f"💎 المبلغ الإجمالي: {format_number(total_amount)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🎯 مبروك على الاستثمار الناجح!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في سحب الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عملية السحب")


async def get_user_investments(user_id: int):
    """الحصول على استثمارات المستخدم"""
    try:
        investments = await execute_query(
            "SELECT * FROM investments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
            fetch_all=True
        )
        return investments if investments else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على استثمارات المستخدم: {e}")
        return []


async def get_mature_investments(user_id: int):
    """الحصول على الاستثمارات المكتملة"""
    try:
        now = datetime.now().isoformat()
        investments = await execute_query(
            "SELECT * FROM investments WHERE user_id = ? AND status = 'active' AND maturity_date <= ?",
            (user_id, now),
            fetch_all=True
        )
        return investments if investments else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على الاستثمارات المكتملة: {e}")
        return []


async def check_and_mature_investments():
    """فحص وإنضاج الاستثمارات (دالة للتشغيل الدوري)"""
    try:
        now = datetime.now().isoformat()
        mature_investments = await execute_query(
            "SELECT * FROM investments WHERE status = 'active' AND maturity_date <= ?",
            (now,),
            fetch_all=True
        )
        
        if mature_investments:
            for investment in mature_investments:
                # يمكن إضافة إشعار للمستخدم هنا
                if isinstance(investment, dict):
                    logging.info(f"استثمار مكتمل للمستخدم {investment.get('user_id')}: {investment.get('id')}")
        
        return len(mature_investments) if mature_investments else 0
        
    except Exception as e:
        logging.error(f"خطأ في فحص الاستثمارات المكتملة: {e}")
        return 0


# معالجات الحالات
async def process_investment_duration(message: Message, state: FSMContext):
    """معالجة مدة الاستثمار"""
    await message.reply("تم استلام مدة الاستثمار")
    await state.clear()


async def show_investment_report(message: Message):
    """عرض تقرير شامل للاستثمارات"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
            
        user_investments = await get_user_investments(message.from_user.id)
        
        if not user_investments:
            await message.reply("📊 لا توجد استثمارات حالياً\n\nابدأ رحلتك الاستثمارية باستخدام 'استثمار'")
            return
            
        report_text = "📊 **تقرير الاستثمارات:**\n\n"
        
        total_invested = 0
        total_expected = 0
        active_count = 0
        mature_count = 0
        
        if user_investments:
            for inv in user_investments:
                if isinstance(inv, dict) and inv.get('status') == 'active':
                    active_count += 1
                    total_invested += inv.get('amount', 0)
                    expected_return = inv.get('amount', 0) + (inv.get('amount', 0) * inv.get('expected_return', 0))
                    total_expected += expected_return
                    
                    # التحقق من النضج
                    maturity_date_str = inv.get('maturity_date')
                    if maturity_date_str:
                        maturity_date = datetime.fromisoformat(maturity_date_str)
                        if datetime.now() >= maturity_date:
                            mature_count += 1
        
        report_text += f"💰 **إجمالي المبلغ المستثمر:** {format_number(total_invested)}$\n"
        report_text += f"📈 **العائد المتوقع:** {format_number(total_expected)}$\n"
        report_text += f"🎯 **الربح المتوقع:** {format_number(total_expected - total_invested)}$\n\n"
        report_text += f"📊 **الإحصائيات:**\n"
        report_text += f"   🔄 استثمارات نشطة: {active_count}\n"
        report_text += f"   ✅ استثمارات مكتملة: {mature_count}\n"
        
        if total_invested > 0:
            profit_percentage = ((total_expected - total_invested) / total_invested) * 100
            report_text += f"   📈 نسبة الربح المتوقعة: {profit_percentage:.1f}%"
        
        await message.reply(report_text)
        
    except Exception as e:
        logging.error(f"خطأ في تقرير الاستثمارات: {e}")
        await message.reply("❌ حدث خطأ في عرض تقرير الاستثمارات")

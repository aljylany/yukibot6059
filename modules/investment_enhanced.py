"""
نظام الاستثمار المحسن مع تكامل XP
Enhanced Investment System with XP Integration
"""

import logging
from datetime import datetime, timedelta
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.helpers import format_number, is_valid_amount
try:
    from modules.enhanced_xp_handler import add_xp_for_activity
except ImportError:
    async def add_xp_for_activity(user_id: int, activity_type: str):
        """دالة بديلة لإضافة XP"""
        try:
            from modules.simple_level_display import add_simple_xp
            await add_simple_xp(user_id, 5)
        except:
            pass


# أنواع الاستثمارات المحسنة - شركات عربية
ENHANCED_INVESTMENT_TYPES = {
    "ارامكو": {
        "name": "أسهم أرامكو السعودية",
        "min_amount": 1000,
        "interest_rate": 0.02,  # 2% شهرياً
        "duration_days": 30,
        "risk": "منخفض",
        "emoji": "🛢️",
        "xp_reward": 10
    },
    "الراجحي": {
        "name": "مصرف الراجحي",
        "min_amount": 5000,
        "interest_rate": 0.05,  # 5% شهرياً
        "duration_days": 60,
        "risk": "منخفض",
        "emoji": "🏦",
        "xp_reward": 15
    },
    "سابك": {
        "name": "الشركة السعودية للصناعات الأساسية",
        "min_amount": 10000,
        "interest_rate": 0.08,  # 8% شهرياً
        "duration_days": 90,
        "risk": "متوسط",
        "emoji": "🏭",
        "xp_reward": 20
    },
    "اتصالات": {
        "name": "شركة الاتصالات السعودية",
        "min_amount": 50000,
        "interest_rate": 0.12,  # 12% شهرياً
        "duration_days": 180,
        "risk": "متوسط",
        "emoji": "📱",
        "xp_reward": 30
    },
    "الكهرباء": {
        "name": "الشركة السعودية للكهرباء",
        "min_amount": 100000,
        "interest_rate": 0.20,  # 20% شهرياً
        "duration_days": 365,
        "risk": "عالي",
        "emoji": "⚡",
        "xp_reward": 50
    }
}


async def show_enhanced_investment_menu(message: Message):
    """عرض قائمة الاستثمار المحسنة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على استثمارات المستخدم
        user_investments = await get_enhanced_user_investments(message.from_user.id)
        total_investment = 0
        expected_returns = 0
        
        if user_investments:
            for inv in user_investments:
                if isinstance(inv, dict):
                    total_investment += inv.get('amount', 0)
                    expected_returns += inv.get('amount', 0) * inv.get('expected_return', 0)
        
        investment_text = f"""
💼 **مركز الاستثمار المحسن**

💰 رصيدك النقدي: {format_number(user['balance'])}$
📊 إجمالي الاستثمار: {format_number(total_investment)}$
💎 العوائد المتوقعة: {format_number(expected_returns)}$

🎯 عدد الاستثمارات النشطة: {len(user_investments) if user_investments else 0}

✨ **مميزات جديدة:**
• كسب XP مع كل استثمار
• عوائد محسنة حسب المستوى
• إشعارات الاستحقاق

📋 **الأوامر المتاحة:**
💼 "استثمار جديد" - بدء استثمار جديد
📊 "محفظة الاستثمارات" - عرض استثماراتك
💰 "سحب استثمار" - سحب استثمار مكتمل
📈 "تقرير الاستثمارات" - إحصائيات شاملة
        """
        
        await message.reply(investment_text)
        
        # إضافة XP لاستخدام نظام الاستثمار
        await add_xp_for_activity(message.from_user.id, "investment")
        
    except Exception as e:
        logging.error(f"خطأ في قائمة الاستثمار المحسنة: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الاستثمار")


async def show_enhanced_investment_options(message: Message):
    """عرض خيارات الاستثمار المحسنة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        options_text = "💼 **خيارات الاستثمار المحسنة:**\n\n"
        
        for inv_type, inv_info in ENHANCED_INVESTMENT_TYPES.items():
            affordable = "✅" if user['balance'] >= inv_info['min_amount'] else "❌"
            duration_months = inv_info['duration_days'] // 30
            
            options_text += f"{affordable} {inv_info['emoji']} **{inv_info['name']}**\n"
            options_text += f"   💰 الحد الأدنى: {format_number(inv_info['min_amount'])}$\n"
            options_text += f"   📈 العائد: {inv_info['interest_rate']*100:.0f}% شهرياً\n"
            options_text += f"   ⏰ المدة: {duration_months} شهر\n"
            options_text += f"   ⚠️ المخاطر: {inv_info['risk']}\n"
            options_text += f"   ✨ XP مكافأة: +{inv_info['xp_reward']} XP\n\n"
        
        options_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$\n\n"
        options_text += "📝 **للاستثمار:** اكتب 'استثمار [النوع] [المبلغ]'\n"
        options_text += "مثال: استثمار ارامكو 5000"
        
        await message.reply(options_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الاستثمار")


async def process_enhanced_investment(message: Message, investment_type: str, amount: int):
    """معالجة الاستثمار المحسن"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً")
            return
        
        # التحقق من نوع الاستثمار
        if investment_type not in ENHANCED_INVESTMENT_TYPES:
            available_types = ", ".join(ENHANCED_INVESTMENT_TYPES.keys())
            await message.reply(f"❌ نوع استثمار غير صحيح\nالأنواع المتاحة: {available_types}")
            return
        
        inv_info = ENHANCED_INVESTMENT_TYPES[investment_type]
        
        # التحقق من المبلغ
        if amount < inv_info['min_amount']:
            await message.reply(
                f"❌ المبلغ أقل من الحد الأدنى\n"
                f"💰 الحد الأدنى لـ{inv_info['name']}: {format_number(inv_info['min_amount'])}$"
            )
            return
        
        if amount > user['balance']:
            await message.reply(f"❌ رصيدك غير كافٍ!\n💰 رصيدك: {format_number(user['balance'])}$")
            return
        
        # حساب تاريخ الاستحقاق والعائد
        maturity_date = datetime.now() + timedelta(days=inv_info['duration_days'])
        expected_return = inv_info['interest_rate']
        
        # إنشاء الاستثمار
        await execute_query(
            """
            INSERT INTO investments (user_id, investment_type, amount, expected_return, maturity_date, status, created_at)
            VALUES (?, ?, ?, ?, ?, 'active', ?)
            """,
            (message.from_user.id, investment_type, amount, expected_return, maturity_date.isoformat(), datetime.now().isoformat())
        )
        
        # خصم المبلغ من رصيد المستخدم
        new_balance = user['balance'] - amount
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            f"استثمار في {inv_info['name']}",
            -amount,
            "investment"
        )
        
        # حساب العائد المتوقع
        total_return = amount + (amount * expected_return)
        profit = total_return - amount
        
        success_message = f"""
✅ **تم إنشاء الاستثمار بنجاح!**

{inv_info['emoji']} **النوع:** {inv_info['name']}
💰 **المبلغ المستثمر:** {format_number(amount)}$
📈 **العائد المتوقع:** {format_number(total_return)}$
💎 **الربح المتوقع:** {format_number(profit)}$
📅 **تاريخ الاستحقاق:** {maturity_date.strftime('%Y-%m-%d')}
⚠️ **المخاطر:** {inv_info['risk']}

💵 **رصيدك الجديد:** {format_number(new_balance)}$
✨ **مكافأة XP:** +{inv_info['xp_reward']} XP

🎯 **نصيحة:** كلما زاد مستواك، زادت عوائدك!
        """
        
        await message.reply(success_message)
        
        # إضافة XP للاستثمار
        await add_xp_for_activity(message.from_user.id, "investment")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الاستثمار المحسن: {e}")
        await message.reply("❌ حدث خطأ في إنشاء الاستثمار")


async def get_enhanced_user_investments(user_id: int):
    """الحصول على استثمارات المستخدم المحسنة"""
    try:
        investments = await execute_query(
            "SELECT * FROM investments WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,),
            fetch_all=True
        )
        return investments if investments else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على الاستثمارات: {e}")
        return []


async def handle_enhanced_investment_text(message: Message):
    """معالجة أوامر الاستثمار النصية المحسنة"""
    try:
        text = message.text.lower().strip()
        
        # استثمار جديد
        if "استثمار جديد" in text:
            await show_enhanced_investment_options(message)
            return True
        
        # محفظة الاستثمارات
        if any(keyword in text for keyword in ["محفظة الاستثمارات", "استثماراتي", "محفظتي"]):
            await show_enhanced_user_investments(message)
            return True
        
        # تقرير الاستثمارات
        if "تقرير الاستثمارات" in text:
            await show_enhanced_investment_report(message)
            return True
        
        # استثمار مع نوع ومبلغ
        if text.startswith("استثمار "):
            parts = text.split()
            if len(parts) >= 3:
                investment_type = parts[1]
                try:
                    amount = int(parts[2])
                    await process_enhanced_investment(message, investment_type, amount)
                    return True
                except ValueError:
                    await message.reply("❌ يرجى كتابة مبلغ صحيح\nمثال: استثمار سندات 5000")
                    return True
        
        # قائمة الاستثمار العامة - تجاهل الأوامر البسيطة
        words = text.split()
        
        # تجاهل الاستثمار البسيط
        if (text == "استثمار فلوسي" or 
            (len(words) == 2 and words[0] == "استثمار" and words[1].replace('.', '').replace(',', '').isdigit())):
            return False
            
        # عرض قائمة الاستثمار للأوامر العامة فقط
        if text == "استثمار" or any(keyword in text for keyword in ["الاستثمار"]):
            await show_enhanced_investment_menu(message)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالجة أوامر الاستثمار: {e}")
        return False


async def show_enhanced_user_investments(message: Message):
    """عرض استثمارات المستخدم بشكل محسن"""
    try:
        user_investments = await get_enhanced_user_investments(message.from_user.id)
        
        if not user_investments:
            await message.reply("📊 لا توجد استثمارات حالياً\n\nابدأ رحلتك الاستثمارية باستخدام 'استثمار جديد'")
            return
        
        investments_text = "📊 **محفظة الاستثمارات:**\n\n"
        
        for i, inv in enumerate(user_investments, 1):
            if isinstance(inv, dict):
                inv_type = inv.get('investment_type', '')
                inv_info = ENHANCED_INVESTMENT_TYPES.get(inv_type, {})
                
                amount = inv.get('amount', 0)
                expected_return = inv.get('expected_return', 0)
                total_return = amount + (amount * expected_return)
                
                maturity_date_str = inv.get('maturity_date', '')
                if maturity_date_str:
                    maturity_date = datetime.fromisoformat(maturity_date_str)
                    is_mature = datetime.now() >= maturity_date
                    status_emoji = "✅" if is_mature else "⏳"
                    date_display = maturity_date.strftime('%Y-%m-%d')
                else:
                    status_emoji = "❓"
                    date_display = "غير محدد"
                
                investments_text += f"{status_emoji} **الاستثمار {i}:**\n"
                investments_text += f"   {inv_info.get('emoji', '💼')} {inv_info.get('name', inv_type)}\n"
                investments_text += f"   💰 المبلغ: {format_number(amount)}$\n"
                investments_text += f"   📈 العائد المتوقع: {format_number(total_return)}$\n"
                investments_text += f"   📅 الاستحقاق: {date_display}\n\n"
        
        investments_text += "💡 **استثماراتك المكتملة جاهزة للسحب!**"
        
        await message.reply(investments_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الاستثمارات: {e}")
        await message.reply("❌ حدث خطأ في عرض الاستثمارات")


async def show_enhanced_investment_report(message: Message):
    """عرض تقرير الاستثمارات المحسن"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً")
            return
        
        user_investments = await get_enhanced_user_investments(message.from_user.id)
        
        if not user_investments:
            await message.reply("📊 لا توجد استثمارات لإنشاء تقرير")
            return
        
        # حساب الإحصائيات
        total_invested = 0
        total_expected = 0
        active_count = 0
        mature_count = 0
        
        for inv in user_investments:
            if isinstance(inv, dict) and inv.get('status') == 'active':
                active_count += 1
                amount = inv.get('amount', 0)
                expected_return = inv.get('expected_return', 0)
                
                total_invested += amount
                total_expected += amount + (amount * expected_return)
                
                # فحص النضج
                maturity_date_str = inv.get('maturity_date')
                if maturity_date_str:
                    maturity_date = datetime.fromisoformat(maturity_date_str)
                    if datetime.now() >= maturity_date:
                        mature_count += 1
        
        total_profit = total_expected - total_invested
        profit_percentage = ((total_profit / total_invested) * 100) if total_invested > 0 else 0
        
        report_text = f"""
📊 **تقرير الاستثمارات الشامل:**

💰 **إجمالي المبلغ المستثمر:** {format_number(total_invested)}$
📈 **العائد المتوقع:** {format_number(total_expected)}$
💎 **الربح المتوقع:** {format_number(total_profit)}$
📊 **نسبة الربح:** {profit_percentage:.1f}%

🎯 **الإحصائيات:**
   🔄 استثمارات نشطة: {active_count}
   ✅ استثمارات مكتملة: {mature_count}

💰 **رصيدك الحالي:** {format_number(user['balance'])}$

✨ **استمر في الاستثمار لزيادة XP ومستواك!**
        """
        
        await message.reply(report_text)
        
    except Exception as e:
        logging.error(f"خطأ في تقرير الاستثمارات: {e}")
        await message.reply("❌ حدث خطأ في إنشاء التقرير")
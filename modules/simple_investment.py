"""
نظام الاستثمار البسيط
Simple Investment System
"""

import logging
import random
from datetime import datetime, timedelta
from aiogram.types import Message
from database.operations import execute_query, get_user, update_user_balance
from utils.helpers import format_number

# فترة الانتظار بين الاستثمارات (5 دقائق)
INVESTMENT_COOLDOWN = 5 * 60  # 5 دقائق بالثانية

# نسب الربح العشوائية (0% إلى 30%)
MIN_PROFIT_RATE = 0.0
MAX_PROFIT_RATE = 0.30

# XP المكافأة للاستثمار البسيط
INVESTMENT_XP_REWARD = 50


async def can_invest(user_id: int) -> bool:
    """التحقق من إمكانية الاستثمار (فترة الانتظار)"""
    try:
        result = await execute_query(
            "SELECT last_simple_investment FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if not result:
            return True
            
        last_investment = result[0] if isinstance(result, tuple) else result.get('last_simple_investment')
        
        if not last_investment:
            return True
            
        # تحويل النص إلى datetime
        if isinstance(last_investment, str):
            last_investment_time = datetime.fromisoformat(last_investment)
        else:
            last_investment_time = last_investment
            
        time_since_last = datetime.now() - last_investment_time
        return time_since_last.total_seconds() >= INVESTMENT_COOLDOWN
        
    except Exception as e:
        logging.error(f"خطأ في فحص إمكانية الاستثمار: {e}")
        return True


async def get_remaining_cooldown(user_id: int) -> int:
    """الحصول على الوقت المتبقي لفترة الانتظار بالثواني"""
    try:
        result = await execute_query(
            "SELECT last_simple_investment FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        if not result:
            return 0
            
        last_investment = result[0] if isinstance(result, tuple) else result.get('last_simple_investment')
        
        if not last_investment:
            return 0
            
        if isinstance(last_investment, str):
            last_investment_time = datetime.fromisoformat(last_investment)
        else:
            last_investment_time = last_investment
            
        time_since_last = datetime.now() - last_investment_time
        remaining = INVESTMENT_COOLDOWN - time_since_last.total_seconds()
        
        return max(0, int(remaining))
        
    except Exception as e:
        logging.error(f"خطأ في حساب الوقت المتبقي: {e}")
        return 0


async def perform_simple_investment(message: Message, amount: int):
    """تنفيذ الاستثمار البسيط"""
    try:
        user_id = message.from_user.id
        user = await get_user(user_id)
        
        if not user:
            await message.reply("❌ لم يتم العثور على حسابك. يرجى إنشاء حساب بنكي أولاً")
            return
            
        # التحقق من فترة الانتظار
        if not await can_invest(user_id):
            remaining = await get_remaining_cooldown(user_id)
            minutes = remaining // 60
            seconds = remaining % 60
            await message.reply(
                f"⏰ **يجب الانتظار قبل الاستثمار مرة أخرى**\n\n"
                f"🕐 الوقت المتبقي: {minutes} دقيقة و {seconds} ثانية\n"
                f"💡 يمكنك الاستثمار كل 5 دقائق"
            )
            return
            
        # التحقق من الرصيد
        balance = user.get('balance', 0) if isinstance(user, dict) else 0
        if balance < amount:
            await message.reply(
                f"❌ **رصيد غير كافي**\n\n"
                f"💰 المبلغ المطلوب: {format_number(amount)}$\n"
                f"💵 رصيدك الحالي: {format_number(balance)}$\n"
                f"💸 تحتاج إلى: {format_number(amount - balance)}$ إضافية"
            )
            return
            
        # حساب الربح العشوائي (0% إلى 30%)
        profit_rate = random.uniform(MIN_PROFIT_RATE, MAX_PROFIT_RATE)
        profit_amount = int(amount * profit_rate)
        total_return = amount + profit_amount
        
        # تحديث الرصيد
        new_balance = balance - amount + total_return
        
        # تحديث قاعدة البيانات
        await execute_query(
            "UPDATE users SET balance = ?, last_simple_investment = ? WHERE user_id = ?",
            (new_balance, datetime.now().isoformat(), user_id)
        )
        
        # إضافة XP للاستثمار
        try:
            from modules.leveling import add_xp
            await add_xp(user_id, INVESTMENT_XP_REWARD)
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP للاستثمار: {xp_error}")
        
        # تحديد نوع النتيجة
        if profit_amount > 0:
            result_emoji = "📈"
            result_text = "ربح"
            result_color = "🟢"
        elif profit_amount == 0:
            result_emoji = "➖"
            result_text = "تعادل"
            result_color = "🟡"
        else:
            result_emoji = "📉"
            result_text = "خسارة"
            result_color = "🔴"
            
        # رسالة النتيجة
        result_message = f"""💼 **نتيجة الاستثمار البسيط**

💰 المبلغ المستثمر: {format_number(amount)}$
{result_emoji} النتيجة: {result_color} {result_text}
📊 نسبة الربح: {profit_rate:.1%}
💵 الربح: {format_number(profit_amount)}$
💎 المبلغ المستلم: {format_number(total_return)}$

💰 رصيدك الجديد: {format_number(new_balance)}$
⭐ مكافأة XP: +{INVESTMENT_XP_REWARD}

⏰ يمكنك الاستثمار مرة أخرى خلال 5 دقائق"""

        await message.reply(result_message)
        
    except Exception as e:
        logging.error(f"خطأ في الاستثمار البسيط: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الاستثمار")


async def handle_simple_investment_command(message: Message, text: str):
    """معالجة أمر الاستثمار البسيط"""
    try:
        parts = text.split()
        
        if len(parts) < 2:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "💡 استثمار [المبلغ]\n"
                "💡 استثمار فلوسي\n\n"
                "📝 **أمثلة:**\n"
                "• استثمار 1000\n"
                "• استثمار فلوسي\n\n"
                "🎯 **نظام الاستثمار البسيط:**\n"
                "• ربح عشوائي من 0% إلى 30%\n"
                "• مكافأة 50 XP لكل استثمار\n"
                "• يمكن الاستثمار كل 5 دقائق"
            )
            return
            
        amount_input = parts[1]
        
        # التعامل مع "فلوسي"
        if amount_input == "فلوسي":
            user = await get_user(message.from_user.id)
            if not user:
                await message.reply("❌ لم يتم العثور على حسابك")
                return
                
            amount = user.get('balance', 0) if isinstance(user, dict) else 0
            if amount <= 0:
                await message.reply("❌ ليس لديك رصيد للاستثمار")
                return
        else:
            # التحقق من صحة المبلغ
            try:
                amount = int(amount_input)
                if amount <= 0:
                    await message.reply("❌ يجب أن يكون المبلغ أكبر من صفر")
                    return
            except ValueError:
                await message.reply("❌ يرجى إدخال مبلغ صحيح")
                return
                
        # تنفيذ الاستثمار
        await perform_simple_investment(message, amount)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر الاستثمار البسيط: {e}")
        await message.reply("❌ حدث خطأ في معالجة الأمر")


async def show_investment_info(message: Message):
    """عرض معلومات الاستثمار البسيط"""
    try:
        user_id = message.from_user.id
        
        # التحقق من إمكانية الاستثمار
        can_invest_now = await can_invest(user_id)
        
        if can_invest_now:
            status = "🟢 جاهز للاستثمار"
            cooldown_text = ""
        else:
            remaining = await get_remaining_cooldown(user_id)
            minutes = remaining // 60
            seconds = remaining % 60
            status = "🔴 في فترة انتظار"
            cooldown_text = f"\n⏰ الوقت المتبقي: {minutes} دقيقة و {seconds} ثانية"
            
        info_text = f"""💼 **معلومات الاستثمار البسيط**

📊 **النظام:**
• 🎯 ربح عشوائي: 0% - 30%
• ⏰ فترة الانتظار: 5 دقائق
• ⭐ مكافأة XP: 50 نقطة

🎮 **طريقة الاستخدام:**
• استثمار [المبلغ]
• استثمار فلوسي

📈 **الحالة الحالية:**
{status}{cooldown_text}

💡 **نصائح:**
• استثمر بمبالغ صغيرة للبداية
• الاستثمار البسيط سريع وفوري
• استخدم الاستثمار المتقدم للمبالغ الكبيرة"""

        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في عرض المعلومات")
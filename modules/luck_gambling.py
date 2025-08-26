"""
نظام مراهنة الحظ - Luck Gambling System
نظام مراهنة بسيط: 30% فرصة ربح ضعف المبلغ، 70% خسارة كاملة
"""

import logging
import random
import time
from typing import Dict
from aiogram.types import Message
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number

# تخزين آخر مراهنة لكل مستخدم لمنع التكرار المفرط
LAST_GAMBLE: Dict[int, float] = {}
GAMBLE_COOLDOWN = 10  # 10 ثوانِ بين كل مراهنة

async def process_luck_gamble(message: Message, bet_amount: float = None, bet_all: bool = False):
    """معالجة مراهنة الحظ"""
    try:
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "اللاعب"
        username = message.from_user.username or ""
        
        # التحقق من تسجيل المستخدم
        user_data = await get_or_create_user(user_id, username, user_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # فحص الكولداون
        current_time = time.time()
        if user_id in LAST_GAMBLE:
            time_passed = current_time - LAST_GAMBLE[user_id]
            if time_passed < GAMBLE_COOLDOWN:
                remaining = int(GAMBLE_COOLDOWN - time_passed)
                await message.reply(
                    f"⏰ **انتظر قليلاً!**\n\n"
                    f"🕐 الوقت المتبقي: {remaining} ثانية\n"
                    f"🎰 يمكنك المراهنة كل {GAMBLE_COOLDOWN} ثوانِ"
                )
                return
        
        # تحديد مبلغ المراهنة
        current_balance = user_data['balance']
        
        if bet_all:
            if current_balance <= 0:
                await message.reply("❌ **ليس لديك أموال للمراهنة!**\n\n💡 اكسب بعض المال أولاً من الألعاب الأخرى")
                return
            bet_amount = current_balance
        else:
            if bet_amount is None or bet_amount <= 0:
                await message.reply("❌ **مبلغ المراهنة غير صحيح!**\n\n📝 استخدم: 'حظ [المبلغ]' أو 'حظ فلوسي'")
                return
            
            if bet_amount > current_balance:
                await message.reply(
                    f"❌ **ليس لديك ما يكفي من المال!**\n\n"
                    f"💰 رصيدك الحالي: {format_number(current_balance)}$\n"
                    f"🎯 المبلغ المطلوب: {format_number(bet_amount)}$"
                )
                return
        
        # تحديث وقت آخر مراهنة
        LAST_GAMBLE[user_id] = current_time
        
        # تحديد النتيجة (30% ربح، 70% خسارة)
        win_chance = 30  # نسبة الربح
        is_winner = random.randint(1, 100) <= win_chance
        
        if is_winner:
            # ربح: يحصل على ضعف المبلغ
            winnings = bet_amount * 2
            new_balance = current_balance + bet_amount  # الرصيد الأصلي + المبلغ المربوح
            
            # تحديث الرصيد
            success = await update_user_balance(user_id, new_balance)
            if success:
                # إضافة سجل المعاملة
                await add_transaction(user_id, bet_amount, "luck_gamble_win", f"ربح مراهنة الحظ: {format_number(bet_amount)}$")
                
                result_text = (
                    f"🎉 **مبروك! فزت!** 🎉\n\n"
                    f"👤 **اللاعب:** {user_name}\n"
                    f"🎰 **المبلغ المراهن:** {format_number(bet_amount)}$\n"
                    f"💰 **المبلغ المربوح:** {format_number(bet_amount)}$\n"
                    f"📈 **الرصيد الجديد:** {format_number(new_balance)}$\n\n"
                    f"🔥 **الحظ معك اليوم!**"
                )
            else:
                result_text = "❌ حدث خطأ في تحديث الرصيد، حاول مرة أخرى"
        else:
            # خسارة: يفقد المبلغ كاملاً
            new_balance = current_balance - bet_amount
            
            # تحديث الرصيد
            success = await update_user_balance(user_id, new_balance)
            if success:
                # إضافة سجل المعاملة
                await add_transaction(user_id, -bet_amount, "luck_gamble_loss", f"خسارة مراهنة الحظ: {format_number(bet_amount)}$")
                
                result_text = (
                    f"💥 **للأسف... خسرت!** 💥\n\n"
                    f"👤 **اللاعب:** {user_name}\n"
                    f"🎰 **المبلغ المفقود:** {format_number(bet_amount)}$\n"
                    f"📉 **الرصيد الجديد:** {format_number(new_balance)}$\n\n"
                    f"🍀 **الحظ سيأتي في المرة القادمة!**"
                )
            else:
                result_text = "❌ حدث خطأ في تحديث الرصيد، حاول مرة أخرى"
        
        # إضافة XP للمراهنة
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(user_id, "gambling")
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP لمراهنة الحظ: {xp_error}")
        
        # عرض النتيجة مع إحصائيات الحظ
        luck_stats = (
            f"\n\n📊 **إحصائيات مراهنة الحظ:**\n"
            f"🎯 فرصة الربح: {win_chance}%\n"
            f"💀 فرصة الخسارة: {100-win_chance}%\n"
            f"💰 مضاعف الربح: x2\n\n"
            f"⚠️ **تذكير:** المراهنة قد تؤدي لخسارة كل أموالك!"
        )
        
        await message.reply(result_text + luck_stats)
        
    except Exception as e:
        logging.error(f"خطأ في مراهنة الحظ: {e}")
        await message.reply("❌ حدث خطأ في مراهنة الحظ، حاول مرة أخرى")

def parse_gamble_command(text: str) -> tuple:
    """تحليل أمر المراهنة واستخراج المبلغ"""
    try:
        text = text.strip().lower()
        
        # فحص "حظ فلوسي"
        if any(phrase in text for phrase in ['حظ فلوسي', 'حظ كل فلوسي', 'حظ كامل فلوسي']):
            return None, True
        
        # فحص "حظ [مبلغ]"
        words = text.split()
        
        # البحث عن الرقم بعد كلمة "حظ"
        for i, word in enumerate(words):
            if word == 'حظ' and i + 1 < len(words):
                try:
                    amount_str = words[i + 1]
                    # إزالة العلامات والحروف الزائدة
                    amount_str = amount_str.replace('$', '').replace(',', '').replace('ريال', '').replace('دولار', '')
                    amount = float(amount_str)
                    
                    if amount <= 0:
                        return None, False
                    
                    return amount, False
                except (ValueError, IndexError):
                    return None, False
        
        return None, False
        
    except Exception as e:
        logging.error(f"خطأ في تحليل أمر المراهنة: {e}")
        return None, False

async def show_gambling_help(message: Message):
    """عرض مساعدة نظام المراهنة"""
    try:
        user_data = await get_or_create_user(message.from_user.id, 
                                           message.from_user.username or "", 
                                           message.from_user.first_name or "اللاعب")
        
        current_balance = user_data['balance'] if user_data else 0
        
        help_text = f"""
🎰 **نظام مراهنة الحظ** 🎰

💰 **رصيدك الحالي:** {format_number(current_balance)}$

📋 **الأوامر المتاحة:**
• `حظ [المبلغ]` - مراهنة بمبلغ محدد
• `حظ فلوسي` - مراهنة بكامل رصيدك

💡 **أمثلة:**
• حظ 1000
• حظ 50000  
• حظ فلوسي

📊 **قوانين اللعبة:**
🎯 فرصة الربح: 30%
💰 مكسب الربح: ضعف المبلغ (x2)
💀 فرصة الخسارة: 70%
📉 خسارة: المبلغ كاملاً

⚠️ **تحذير:** المراهنة قد تؤدي لخسارة كل أموالك!
⏰ **الكولداون:** {GAMBLE_COOLDOWN} ثوانِ بين كل مراهنة

🍀 **حظاً سعيداً!**
"""
        
        await message.reply(help_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض مساعدة المراهنة: {e}")
        await message.reply("❌ حدث خطأ في عرض المساعدة")
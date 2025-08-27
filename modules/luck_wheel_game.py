"""
لعبة عجلة الحظ - Luck Wheel Game
لعبة بسيطة وسريعة مع جوائز فورية
"""

import logging
import random
import time
from typing import Dict, List
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.leveling import LevelingSystem
from utils.helpers import format_number

# الجوائز المتاحة في العجلة
WHEEL_PRIZES = [
    {"name": "💰 10,000$", "value": 10000, "type": "money", "probability": 25},
    {"name": "💎 25,000$", "value": 25000, "type": "money", "probability": 15},
    {"name": "🎯 50,000$", "value": 50000, "type": "money", "probability": 10},
    {"name": "🏆 100,000$", "value": 100000, "type": "money", "probability": 5},
    {"name": "✨ 50 XP", "value": 50, "type": "xp", "probability": 20},
    {"name": "🌟 100 XP", "value": 100, "type": "xp", "probability": 10},
    {"name": "🔥 مضاعف x2", "value": 2, "type": "multiplier", "probability": 8},
    {"name": "💥 حظ سيء", "value": 0, "type": "nothing", "probability": 7}
]

# تخزين آخر دوران لكل مستخدم لمنع التكرار المفرط
LAST_SPIN: Dict[int, float] = {}
SPIN_COOLDOWN = 30  # 30 ثانية بين كل دوران

async def start_luck_wheel(message: Message):
    """بدء لعبة عجلة الحظ"""
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
        if user_id in LAST_SPIN:
            time_passed = current_time - LAST_SPIN[user_id]
            if time_passed < SPIN_COOLDOWN:
                remaining = int(SPIN_COOLDOWN - time_passed)
                await message.reply(
                    f"⏰ **انتظر قليلاً!**\n\n"
                    f"🕐 الوقت المتبقي: {remaining} ثانية\n"
                    f"🎲 يمكنك إدارة العجلة كل {SPIN_COOLDOWN} ثانية"
                )
                return
        
        # عرض العجلة
        wheel_text = (
            "🎲 **عجلة الحظ**\n\n"
            f"👤 **اللاعب:** {user_name}\n"
            f"💰 **رصيدك:** {format_number(user_data['balance'])}$\n\n"
            f"🎯 **الجوائز المتاحة:**\n"
            f"💰 10,000$ - 25,000$ - 50,000$ - 100,000$\n"
            f"✨ 50 XP - 100 XP\n"
            f"🔥 مضاعف الحظ x2\n"
            f"💥 أو حظ سيء...\n\n"
            f"🎪 **أدر العجلة واكتشف جائزتك!**"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🎲 إدارة العجلة", callback_data=f"spin_wheel_{user_id}")
        ]])
        
        await message.reply(wheel_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في بدء عجلة الحظ: {e}")
        await message.reply("❌ حدث خطأ في عجلة الحظ")

async def handle_wheel_spin(callback: CallbackQuery):
    """معالجة دوران العجلة"""
    try:
        # استخراج معرف المستخدم من البيانات
        user_id_from_data = int(callback.data.split("_")[-1])
        current_user_id = callback.from_user.id
        
        # التحقق من أن المستخدم الذي يضغط الزر هو نفسه الذي بدأ اللعبة
        if current_user_id != user_id_from_data:
            await callback.answer("❌ هذه ليست عجلة الحظ الخاصة بك!", show_alert=True)
            return
        
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "اللاعب"
        username = callback.from_user.username or ""
        
        # فحص الكولداون مرة أخرى
        current_time = time.time()
        if user_id in LAST_SPIN:
            time_passed = current_time - LAST_SPIN[user_id]
            if time_passed < SPIN_COOLDOWN:
                remaining = int(SPIN_COOLDOWN - time_passed)
                await callback.answer(f"⏰ انتظر {remaining} ثانية أخرى!", show_alert=True)
                return
        
        # تحديث وقت آخر دوران
        LAST_SPIN[user_id] = current_time
        
        # اختيار جائزة عشوائية حسب الاحتمالات
        prize = select_random_prize()
        
        # الحصول على بيانات المستخدم
        user_data = await get_or_create_user(user_id, username, user_name)
        if not user_data:
            await callback.answer("❌ خطأ في البيانات!", show_alert=True)
            return
        
        # تطبيق الجائزة
        result_text = await apply_prize(user_id, user_data, prize, user_name)
        
        # إضافة XP للعب
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(user_id, "gambling")
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP لعجلة الحظ: {xp_error}")
        
        # رسالة النتيجة مع أنيميشن العجلة
        wheel_animation = get_wheel_animation()
        final_text = (
            f"🎲 **نتيجة عجلة الحظ**\n\n"
            f"{wheel_animation}\n\n"
            f"🎯 **الجائزة:** {prize['name']}\n"
            f"{result_text}\n\n"
            f"⏰ **العجلة التالية خلال:** {SPIN_COOLDOWN} ثانية"
        )
        
        await callback.message.edit_text(final_text)
        await callback.answer(f"🎉 حصلت على: {prize['name']}")
        
    except Exception as e:
        logging.error(f"خطأ في دوران العجلة: {e}")
        await callback.answer("❌ حدث خطأ في دوران العجلة", show_alert=True)

def select_random_prize():
    """اختيار جائزة عشوائية حسب الاحتمالات"""
    total_prob = sum(prize["probability"] for prize in WHEEL_PRIZES)
    random_num = random.randint(1, total_prob)
    
    current_prob = 0
    for prize in WHEEL_PRIZES:
        current_prob += prize["probability"]
        if random_num <= current_prob:
            return prize
    
    return WHEEL_PRIZES[-1]  # احتياطي

async def apply_prize(user_id: int, user_data: dict, prize: dict, user_name: str) -> str:
    """تطبيق الجائزة على المستخدم"""
    try:
        if prize["type"] == "money":
            # جائزة مالية
            new_balance = user_data['balance'] + prize["value"]
            await update_user_balance(user_id, new_balance)
            await add_transaction(user_id, f"عجلة الحظ - {prize['name']}", prize["value"], "luck_wheel")
            return f"💰 تم إضافة {format_number(prize['value'])}$ لرصيدك!\n💳 رصيدك الجديد: {format_number(new_balance)}$"
        
        elif prize["type"] == "xp":
            # جائزة خبرة
            leveling_system = LevelingSystem()
            for _ in range(prize["value"] // 10):  # كل 10 XP = مرة واحدة
                await leveling_system.add_xp(user_id, "gaming")
            return f"✨ حصلت على {prize['value']} نقطة خبرة!\n🎯 استمر في اللعب لترتفع مستوياتك"
        
        elif prize["type"] == "multiplier":
            # مضاعف الحظ - نطبق على الرصيد الحالي
            bonus = min(user_data['balance'] // 10, 50000)  # حد أقصى 50K
            if bonus > 0:
                new_balance = user_data['balance'] + bonus
                await update_user_balance(user_id, new_balance)
                await add_transaction(user_id, "مضاعف عجلة الحظ", bonus, "luck_multiplier")
                return f"🔥 مضاعف الحظ نشط!\n💎 حصلت على {format_number(bonus)}$ إضافية!"
            else:
                return f"🔥 مضاعف الحظ نشط!\n💡 لكن رصيدك قليل للاستفادة منه"
        
        else:  # nothing
            return f"💥 حظ سيء هذه المرة!\n🔄 جرب مرة أخرى خلال {SPIN_COOLDOWN} ثانية"
    
    except Exception as e:
        logging.error(f"خطأ في تطبيق الجائزة: {e}")
        return "❌ حدث خطأ في منح الجائزة"

def get_wheel_animation() -> str:
    """رسم أنيميشن بسيط للعجلة"""
    wheel_frames = [
        "🎲",
        "🔄", 
        "⚡",
        "🌟",
        "🎯"
    ]
    return random.choice(wheel_frames)

# إضافة معلومات العجلة لقائمة الألعاب
LUCK_WHEEL_INFO = {
    "name": "🎲 عجلة الحظ",
    "description": "أدر العجلة واكسب جوائز فورية كل 30 ثانية",
    "commands": ["عجلة الحظ", "عجلة", "wheel", "حظ"],
    "players": "1 لاعب", 
    "duration": "30 ثانية",
    "status": "متاحة"
}
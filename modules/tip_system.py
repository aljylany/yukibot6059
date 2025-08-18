"""
نظام البقشيش - يتيح للمستخدمين إعطاء بقشيش للبوت والحصول على مكافآت
"""
import logging
import random
from aiogram.types import Message
from database.operations import get_user, update_user_balance

# أنواع البقشيش والمكافآت
TIP_REWARDS = {
    10: {"min": 5, "max": 15, "bonus_msg": "شكراً لك! 💝"},
    50: {"min": 30, "max": 70, "bonus_msg": "كرمك رائع! 🌟"},
    100: {"min": 80, "max": 150, "bonus_msg": "سخاؤك مذهل! ✨"},
    500: {"min": 400, "max": 700, "bonus_msg": "أنت كريم جداً! 👑"},
    1000: {"min": 900, "max": 1500, "bonus_msg": "كرم استثنائي! 💎"}
}

async def give_tip_command(message: Message):
    """معالجة أمر البقشيش"""
    try:
        if not message.text:
            await message.reply("❌ خطأ في النص")
            return
            
        text = message.text.strip()
        parts = text.split()
        
        if len(parts) < 2:
            await message.reply("""
💝 **نظام البقشيش**

🎁 أعط البوت بقشيش واحصل على مكافآت مضاعفة!

📝 **كيفية الاستخدام:**
💰 اكتب: "بقشيش [المبلغ]"
💰 مثال: بقشيش 100

🎯 **المكافآت المتاحة:**
• 10$ ← مكافأة: 5-15$
• 50$ ← مكافأة: 30-70$  
• 100$ ← مكافأة: 80-150$
• 500$ ← مكافأة: 400-700$
• 1000$ ← مكافأة: 900-1500$

💡 كلما زاد البقشيش، زادت المكافأة!
            """)
            return
        
        try:
            tip_amount = int(parts[1])
        except ValueError:
            await message.reply("❌ يرجى إدخال مبلغ صحيح\n\nمثال: بقشيش 100")
            return
        
        if tip_amount <= 0:
            await message.reply("❌ مبلغ البقشيش يجب أن يكون أكبر من صفر!")
            return
        
        # التحقق من المستخدم والرصيد
        if not message.from_user:
            await message.reply("❌ خطأ في بيانات المستخدم")
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if user['balance'] < tip_amount:
            await message.reply(f"""
❌ **رصيد غير كافٍ!**

💰 مبلغ البقشيش: {tip_amount}$
💵 رصيدك الحالي: {user['balance']}$
📉 تحتاج: {tip_amount - user['balance']}$ إضافية
            """)
            return
        
        # تحديد المكافأة
        reward_info = None
        for tip_threshold in sorted(TIP_REWARDS.keys(), reverse=True):
            if tip_amount >= tip_threshold:
                reward_info = TIP_REWARDS[tip_threshold]
                break
        
        if not reward_info:
            # مكافأة أساسية للمبالغ الصغيرة
            reward = random.randint(1, tip_amount // 2)
            bonus_msg = "شكراً لكرمك! 😊"
        else:
            reward = random.randint(reward_info["min"], reward_info["max"])
            bonus_msg = reward_info["bonus_msg"]
        
        # تطبيق البقشيش والمكافأة
        new_balance = user['balance'] - tip_amount + reward
        if not message.from_user:
            await message.reply("❌ خطأ في بيانات المستخدم")
            return
            
        success = await update_user_balance(message.from_user.id, new_balance)
        
        if success:
            net_change = reward - tip_amount
            if net_change > 0:
                change_text = f"💰 ربحت: +{net_change}$"
                change_emoji = "🎉"
            elif net_change < 0:
                change_text = f"💸 خسرت: {abs(net_change)}$"
                change_emoji = "😅"
            else:
                change_text = "💰 توازن مثالي!"
                change_emoji = "⚖️"
            
            await message.reply(f"""
{change_emoji} **{bonus_msg}**

💝 بقشيشك: {tip_amount}$
🎁 مكافأتك: {reward}$
{change_text}

💵 رصيدك الجديد: {new_balance}$

💖 شكراً لكرمك! البوت يقدر لك ذلك كثيراً
            """)
        else:
            await message.reply("❌ حدث خطأ في معالجة البقشيش، يرجى المحاولة مرة أخرى")
        
    except Exception as e:
        logging.error(f"خطأ في نظام البقشيش: {e}")
        await message.reply("❌ حدث خطأ في نظام البقشيش")

async def tip_menu(message: Message):
    """عرض قائمة البقشيش"""
    try:
        if not message.from_user:
            await message.reply("❌ خطأ في بيانات المستخدم")
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        menu_text = f"""
💝 **نظام البقشيش**

💰 رصيدك الحالي: {user['balance']}$

🎁 **أعط البوت بقشيش واحصل على مكافآت مضاعفة!**

🎯 **المكافآت المتاحة:**
💎 1000$ ← مكافأة: 900-1500$ 
👑 500$ ← مكافأة: 400-700$
✨ 100$ ← مكافأة: 80-150$
🌟 50$ ← مكافأة: 30-70$  
💝 10$ ← مكافأة: 5-15$

📝 **للإعطاء:**
اكتب: "بقشيش [المبلغ]"
مثال: بقشيش 100

💡 **نصائح:**
• كلما زاد البقشيش، زادت فرصة المكافآت الكبيرة
• يمكنك إعطاء أي مبلغ تريده
• البوت سيرد لك بمكافأة عشوائية
        """
        await message.reply(menu_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة البقشيش: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة البقشيش")
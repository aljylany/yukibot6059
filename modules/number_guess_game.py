"""
لعبة خمن الرقم - Number Guessing Game  
لعبة جماعية بسيطة وسريعة
"""

import logging
import random
import time
from typing import Dict, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.leveling import LevelingSystem
from utils.helpers import format_number

# الألعاب النشطة {group_id: game_data}
ACTIVE_GUESS_GAMES: Dict[int, dict] = {}

class NumberGuessGame:
    """فئة لعبة خمن الرقم"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.target_number = random.randint(1, 100)
        self.attempts = []  # قائمة المحاولات {user_id, name, guess, result}
        self.max_attempts = 15  # الحد الأقصى للمحاولات
        self.game_started = True
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.prize_pool = 50000  # جائزة ثابتة
    
    def make_guess(self, user_id: int, user_name: str, guess: int) -> str:
        """تسجيل محاولة تخمين"""
        # فحص إذا كان المستخدم جرب من قبل
        if any(attempt['user_id'] == user_id for attempt in self.attempts):
            return "❌ لديك محاولة واحدة فقط!"
        
        # فحص صحة الرقم
        if guess < 1 or guess > 100:
            return "❌ اختر رقم من 1 إلى 100!"
        
        # تسجيل المحاولة
        if guess == self.target_number:
            result = "🎯 صحيح!"
            self.winner = {"user_id": user_id, "name": user_name, "guess": guess}
            self.game_ended = True
        elif abs(guess - self.target_number) <= 5:
            result = "🔥 ساخن جداً!"
        elif abs(guess - self.target_number) <= 10:
            result = "🌡️ ساخن!"
        elif abs(guess - self.target_number) <= 20:
            result = "😐 فاتر"
        else:
            result = "🧊 بارد!"
        
        self.attempts.append({
            'user_id': user_id,
            'name': user_name,
            'guess': guess,
            'result': result
        })
        
        # فحص انتهاء المحاولات
        if len(self.attempts) >= self.max_attempts and not self.winner:
            self.game_ended = True
        
        return result
    
    def get_game_status(self) -> str:
        """الحصول على حالة اللعبة"""
        status_text = (
            f"🔢 **خمن الرقم (1-100)**\n\n"
            f"🎯 **الهدف:** خمن الرقم السري\n"
            f"👤 **منشئ اللعبة:** {self.creator_name}\n"
            f"💰 **الجائزة:** {format_number(self.prize_pool)}$\n"
            f"📊 **المحاولات:** {len(self.attempts)}/{self.max_attempts}\n\n"
        )
        
        if self.winner:
            status_text += (
                f"🏆 **الفائز:** {self.winner['name']}\n"
                f"🎯 **الرقم:** {self.target_number}\n"
                f"✅ **تخمينه:** {self.winner['guess']}"
            )
        elif self.game_ended:
            status_text += f"💔 **انتهت اللعبة!**\nالرقم كان: {self.target_number}"
        else:
            status_text += "💬 **اكتب رقمك في الشات!**"
        
        # عرض آخر 5 محاولات
        if self.attempts:
            status_text += "\n\n🎯 **آخر المحاولات:**\n"
            for attempt in self.attempts[-5:]:
                status_text += f"• {attempt['name']}: {attempt['guess']} → {attempt['result']}\n"
        
        return status_text

async def start_number_guess_game(message: Message):
    """بدء لعبة خمن الرقم"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # فحص إذا كانت اللعبة في مجموعة
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذه اللعبة تعمل في المجموعات فقط!")
            return
        
        # فحص وجود لعبة نشطة
        if group_id in ACTIVE_GUESS_GAMES:
            await message.reply("🔢 **يوجد لعبة تخمين نشطة!**\n\nانتظر انتهاء اللعبة الحالية")
            return
        
        # التحقق من تسجيل المنشئ
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء لعبة جديدة
        game = NumberGuessGame(group_id, creator_id, creator_name)
        ACTIVE_GUESS_GAMES[group_id] = game
        
        game_text = game.get_game_status()
        
        await message.reply(game_text)
        logging.info(f"تم بدء لعبة خمن الرقم في المجموعة {group_id} بواسطة {creator_name}")
        
        # إعداد مؤقت انتهاء اللعبة (3 دقائق)
        import asyncio
        asyncio.create_task(game_timeout(game, message, 180))
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة خمن الرقم: {e}")
        await message.reply("❌ حدث خطأ في بدء اللعبة")

async def handle_number_input(message: Message):
    """معالجة محاولات التخمين"""
    try:
        group_id = message.chat.id
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "اللاعب"
        
        # فحص وجود لعبة نشطة
        if group_id not in ACTIVE_GUESS_GAMES:
            return  # لا توجد لعبة نشطة
        
        game = ACTIVE_GUESS_GAMES[group_id]
        
        if game.game_ended:
            return  # اللعبة انتهت
        
        # محاولة استخراج رقم من الرسالة
        text = message.text.strip()
        try:
            guess = int(text)
        except ValueError:
            return  # ليس رقم
        
        # التحقق من تسجيل المستخدم
        user_data = await get_or_create_user(user_id, message.from_user.username or "", user_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً!")
            return
        
        # تسجيل المحاولة
        result = game.make_guess(user_id, user_name, guess)
        
        # إرسال النتيجة
        if game.winner:
            # فاز شخص
            await handle_game_end(game, message)
        elif game.game_ended:
            # انتهت المحاولات
            await handle_game_end(game, message)
        else:
            # استمرار اللعبة
            quick_response = f"{user_name}: {guess} → {result}"
            await message.reply(quick_response)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التخمين: {e}")

async def handle_game_end(game: NumberGuessGame, message: Message):
    """معالجة نهاية اللعبة"""
    try:
        leveling_system = LevelingSystem()
        
        if game.winner:
            # منح الجائزة للفائز
            winner_data = await get_or_create_user(game.winner['user_id'])
            if winner_data:
                new_balance = winner_data['balance'] + game.prize_pool
                await update_user_balance(game.winner['user_id'], new_balance)
                await add_transaction(game.winner['user_id'], "فوز في خمن الرقم", game.prize_pool, "number_guess_win")
                await leveling_system.add_xp(game.winner['user_id'], "gaming")
            
            end_text = (
                f"🏆 **انتهت اللعبة!**\n\n"
                f"👑 **الفائز:** {game.winner['name']}\n"
                f"🎯 **الرقم السري:** {game.target_number}\n"
                f"✅ **تخمينه:** {game.winner['guess']}\n"
                f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
                f"📊 **عدد المحاولات:** {len(game.attempts)}\n\n"
                f"🎉 **أحسنت! لعبة أخرى؟**"
            )
        else:
            # لا يوجد فائز
            end_text = (
                f"💔 **انتهت اللعبة بدون فائز!**\n\n"
                f"🎯 **الرقم السري كان:** {game.target_number}\n"
                f"📊 **عدد المحاولات:** {len(game.attempts)}/{game.max_attempts}\n\n"
                f"🔄 **جربوا مرة أخرى!**"
            )
        
        await message.reply(end_text)
        
        # إزالة اللعبة من الذاكرة
        if game.group_id in ACTIVE_GUESS_GAMES:
            del ACTIVE_GUESS_GAMES[game.group_id]
        
        logging.info(f"انتهت لعبة خمن الرقم في المجموعة {game.group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية لعبة خمن الرقم: {e}")

async def game_timeout(game: NumberGuessGame, message: Message, timeout: int):
    """مؤقت انتهاء اللعبة"""
    import asyncio
    await asyncio.sleep(timeout)
    
    if game.group_id in ACTIVE_GUESS_GAMES and not game.game_ended:
        game.game_ended = True
        await handle_game_end(game, message)

# معلومات اللعبة لقائمة الألعاب
NUMBER_GUESS_INFO = {
    "name": "🔢 خمن الرقم",
    "description": "خمن الرقم السري من 1-100 واكسب الجائزة",
    "commands": ["خمن الرقم", "تخمين", "رقم", "guess"],
    "players": "مفتوح للجميع",
    "duration": "3 دقائق",
    "status": "متاحة"
}
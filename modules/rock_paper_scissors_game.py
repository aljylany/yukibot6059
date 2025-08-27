"""
لعبة حجر ورقة مقص - لعبة سريعة وممتعة
Rock Paper Scissors Game Module
"""

import logging
import random
import time
from typing import Dict, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import get_or_create_user
from modules.leveling import LevelingSystem
from modules.ai_player import get_ai_player
from utils.helpers import format_number

# الألعاب النشطة {group_id: game_data}
ACTIVE_RPS_GAMES: Dict[int, dict] = {}

# خيارات اللعبة
CHOICES = {
    "rock": {"emoji": "🗿", "name": "حجر", "beats": "scissors"},
    "paper": {"emoji": "📄", "name": "ورقة", "beats": "rock"},
    "scissors": {"emoji": "✂️", "name": "مقص", "beats": "paper"}
}

class RockPaperScissorsGame:
    """فئة لعبة حجر ورقة مقص"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.rounds = 3  # عدد الجولات
        self.current_round = 1
        self.player_score = 0
        self.ai_score = 0
        self.game_ended = False
        self.created_at = time.time()
        self.ai_enabled = True  # دائماً ضد الذكاء الاصطناعي
        self.game_duration = 60  # مدة اللعبة بالثواني
        
    def get_ai_choice(self) -> str:
        """اختيار AI العشوائي مع بعض الذكاء"""
        choices = list(CHOICES.keys())
        # AI بسيط - اختيار عشوائي مع تفضيل طفيف
        if random.random() < 0.4:  # 40% من الوقت يختار الحجر
            return "rock"
        else:
            return random.choice(choices)
    
    def determine_winner(self, player_choice: str, ai_choice: str) -> str:
        """تحديد الفائز في الجولة"""
        if player_choice == ai_choice:
            return "tie"
        elif CHOICES[player_choice]["beats"] == ai_choice:
            return "player"
        else:
            return "ai"
    
    def play_round(self, player_choice: str) -> dict:
        """لعب جولة واحدة"""
        ai_choice = self.get_ai_choice()
        winner = self.determine_winner(player_choice, ai_choice)
        
        if winner == "player":
            self.player_score += 1
        elif winner == "ai":
            self.ai_score += 1
        
        # الانتقال للجولة التالية
        if self.current_round >= self.rounds:
            self.game_ended = True
        else:
            self.current_round += 1
        
        return {
            "player_choice": player_choice,
            "ai_choice": ai_choice,
            "winner": winner,
            "round": self.current_round - 1,
            "game_ended": self.game_ended
        }
    
    def get_game_result(self) -> dict:
        """الحصول على نتيجة اللعبة النهائية"""
        if self.player_score > self.ai_score:
            overall_winner = "player"
        elif self.ai_score > self.player_score:
            overall_winner = "ai"
        else:
            overall_winner = "tie"
        
        return {
            "overall_winner": overall_winner,
            "player_score": self.player_score,
            "ai_score": self.ai_score,
            "total_rounds": self.rounds
        }
    
    def is_expired(self) -> bool:
        """فحص انتهاء وقت اللعبة"""
        return time.time() - self.created_at > self.game_duration

def get_choice_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح خيارات اللعبة"""
    keyboard = []
    
    # صف واحد يحتوي على جميع الخيارات
    row = []
    for choice_key, choice_data in CHOICES.items():
        button_text = f"{choice_data['emoji']} {choice_data['name']}"
        callback_data = f"rps_choice_{choice_key}"
        row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
    
    keyboard.append(row)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def start_rock_paper_scissors_game(message: Message):
    """بدء لعبة حجر ورقة مقص"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_RPS_GAMES:
            await message.reply("🎮 **يوجد لعبة حجر ورقة مقص نشطة!**\n\nانتظر انتهاء اللعبة الحالية")
            return
        
        # التأكد من تسجيل المستخدم
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء لعبة جديدة
        game = RockPaperScissorsGame(group_id, creator_id, creator_name)
        ACTIVE_RPS_GAMES[group_id] = game
        
        # رسالة بدء اللعبة
        game_text = (
            f"🎮 **لعبة حجر ورقة مقص ضد يوكي!**\n\n"
            f"👤 **اللاعب:** {creator_name}\n"
            f"🤖 **الخصم:** يوكي\n\n"
            f"🎯 **عدد الجولات:** {game.rounds}\n"
            f"📊 **الجولة الحالية:** {game.current_round}/{game.rounds}\n\n"
            f"🏆 **مكافآت:**\n"
            f"• الفوز: +15 XP + 1000$\n"
            f"• التعادل: +5 XP + 500$\n"
            f"• الخسارة: +3 XP + 100$\n\n"
            f"🎯 **اختر خيارك لهذه الجولة:**"
        )
        
        keyboard = get_choice_keyboard()
        await message.reply(game_text, reply_markup=keyboard)
        
        logging.info(f"بدأت لعبة حجر ورقة مقص في المجموعة {group_id} بواسطة {creator_name}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة حجر ورقة مقص: {e}")
        await message.reply("❌ حدث خطأ في بدء اللعبة")

async def handle_rps_choice(callback: CallbackQuery):
    """معالجة اختيار اللاعب"""
    try:
        # استخراج الاختيار
        choice = callback.data.split("_")[-1]
        if choice not in CHOICES:
            await callback.answer("❌ اختيار غير صحيح!", show_alert=True)
            return
        
        group_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_RPS_GAMES:
            await callback.answer("❌ لا توجد لعبة نشطة!", show_alert=True)
            return
        
        game = ACTIVE_RPS_GAMES[group_id]
        
        # فحص إذا كان المستخدم هو منشئ اللعبة
        if user_id != game.creator_id:
            await callback.answer("❌ هذه ليست لعبتك!", show_alert=True)
            return
        
        # فحص انتهاء اللعبة أو انتهاء الوقت
        if game.game_ended or game.is_expired():
            await callback.answer("❌ انتهت اللعبة!", show_alert=True)
            return
        
        # لعب الجولة
        round_result = game.play_round(choice)
        
        # تحديد نص النتيجة
        player_choice_data = CHOICES[round_result["player_choice"]]
        ai_choice_data = CHOICES[round_result["ai_choice"]]
        
        round_text = (
            f"🎯 **نتيجة الجولة {round_result['round']}:**\n\n"
            f"👤 **أنت:** {player_choice_data['emoji']} {player_choice_data['name']}\n"
            f"🤖 **يوكي:** {ai_choice_data['emoji']} {ai_choice_data['name']}\n\n"
        )
        
        if round_result["winner"] == "player":
            round_text += "🎉 **فزت في هذه الجولة!**"
        elif round_result["winner"] == "ai":
            round_text += "😅 **فاز يوكي في هذه الجولة!**"
        else:
            round_text += "🤝 **تعادل في هذه الجولة!**"
        
        round_text += f"\n\n📊 **النتيجة:** أنت {game.player_score} - {game.ai_score} يوكي"
        
        if game.game_ended:
            # اللعبة انتهت
            final_result = game.get_game_result()
            await handle_game_end(callback, game, final_result)
        else:
            # استمرار اللعبة
            round_text += f"\n\n🎯 **الجولة {game.current_round}:**\nاختر خيارك!"
            
            keyboard = get_choice_keyboard()
            await callback.message.edit_text(round_text, reply_markup=keyboard)
        
        await callback.answer("✅ تم تسجيل اختيارك!")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة اختيار حجر ورقة مقص: {e}")
        await callback.answer("❌ حدث خطأ في معالجة اختيارك", show_alert=True)

async def handle_game_end(callback: CallbackQuery, game: RockPaperScissorsGame, final_result: dict):
    """معالجة نهاية اللعبة"""
    try:
        leveling_system = LevelingSystem()
        user_id = game.creator_id
        
        # تحديد المكافآت
        if final_result["overall_winner"] == "player":
            xp_reward = 15
            money_reward = 1000
            result_text = "🎉 **مبروك! فزت في اللعبة!**"
        elif final_result["overall_winner"] == "ai":
            xp_reward = 3
            money_reward = 100
            result_text = "😅 **فاز يوكي هذه المرة!**"
        else:
            xp_reward = 5
            money_reward = 500
            result_text = "🤝 **تعادل! لعبة ممتازة!**"
        
        # منح المكافآت
        await leveling_system.add_xp(user_id, "gaming")
        
        user_data = await get_or_create_user(user_id)
        if user_data:
            from database.operations import update_user_balance, add_transaction
            new_balance = user_data['balance'] + money_reward
            await update_user_balance(user_id, new_balance)
            await add_transaction(user_id, "حجر ورقة مقص", money_reward, "rps_game")
        
        # رسالة النتيجة النهائية
        end_text = (
            f"🏁 **انتهت لعبة حجر ورقة مقص!**\n\n"
            f"{result_text}\n\n"
            f"📊 **النتيجة النهائية:**\n"
            f"👤 **أنت:** {final_result['player_score']} فوز\n"
            f"🤖 **يوكي:** {final_result['ai_score']} فوز\n"
            f"🎯 **إجمالي الجولات:** {final_result['total_rounds']}\n\n"
            f"🎉 **مكافآتك:**\n"
            f"• +{xp_reward} XP\n"
            f"• +{format_number(money_reward)}$\n\n"
            f"🎮 **لعبة أخرى؟**"
        )
        
        await callback.message.edit_text(end_text)
        
        # إزالة اللعبة من الذاكرة
        if game.group_id in ACTIVE_RPS_GAMES:
            del ACTIVE_RPS_GAMES[game.group_id]
        
        # رسالة من يوكي
        ai_player = get_ai_player("rps")
        if final_result["overall_winner"] == "player":
            ai_message = await ai_player.get_game_response("defeat")
        elif final_result["overall_winner"] == "ai":
            ai_message = await ai_player.get_game_response("victory")
        else:
            ai_message = await ai_player.get_game_response("encouragement", "لعبة رائعة!")
        
        await callback.message.reply(f"🤖 {ai_message}")
        
        logging.info(f"انتهت لعبة حجر ورقة مقص في المجموعة {game.group_id} - الفائز: {final_result['overall_winner']}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية لعبة حجر ورقة مقص: {e}")

# معلومات اللعبة
RPS_GAME_INFO = {
    "name": "🎮 حجر ورقة مقص",
    "description": "لعبة سريعة ضد يوكي - 3 جولات",
    "commands": ["حجر ورقة مقص", "حجر ورقة", "rps"],
    "players": "لاعب واحد ضد يوكي",
    "duration": "دقيقة واحدة",
    "status": "متاحة"
}
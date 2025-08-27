"""
لعبة صدق أم كذب - لعبة ضد يوكي أو لاعب آخر
True or False Game Module
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
ACTIVE_TRUE_FALSE_GAMES: Dict[int, dict] = {}

# قاعدة بيانات الأسئلة
QUESTIONS_DB = [
    {"question": "القطة لديها 9 أرواح حقيقياً", "answer": False, "category": "خرافات"},
    {"question": "الإنسان يستخدم 10% فقط من دماغه", "answer": False, "category": "علوم"},
    {"question": "الذهب أثقل من الفضة", "answer": True, "category": "كيمياء"},
    {"question": "البطريق طائر لا يطير", "answer": True, "category": "حيوانات"},
    {"question": "الشمس تدور حول الأرض", "answer": False, "category": "فلك"},
    {"question": "العسل لا يفسد أبداً", "answer": True, "category": "طعام"},
    {"question": "الضوء أسرع من الصوت", "answer": True, "category": "فيزياء"},
    {"question": "الفيل يخاف من الفأر", "answer": False, "category": "حيوانات"},
    {"question": "الماء يغلي عند 100 درجة مئوية", "answer": True, "category": "فيزياء"},
    {"question": "البرق لا يضرب نفس المكان مرتين", "answer": False, "category": "طبيعة"},
    {"question": "القلب الإنساني يخفق حوالي 100,000 مرة يومياً", "answer": True, "category": "طب"},
    {"question": "الأخطبوط له 3 قلوب", "answer": True, "category": "حيوانات"},
    {"question": "الماس مصنوع من الكربون", "answer": True, "category": "كيمياء"},
    {"question": "العظام أقوى من الفولاذ", "answer": True, "category": "طب"},
    {"question": "النمل لا ينام أبداً", "answer": True, "category": "حيوانات"}
]

class TrueFalseGame:
    """فئة لعبة صدق أم كذب"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str, vs_ai: bool = True):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.vs_ai = vs_ai  # ضد يوكي أم ضد لاعب آخر
        self.players = []  # قائمة اللاعبين
        self.current_question = None
        self.current_question_index = 0
        self.player_answers = {}  # إجابات اللاعبين
        self.scores = {}  # النقاط
        self.round_number = 1
        self.max_rounds = 5
        self.game_started = False
        self.game_ended = False
        self.created_at = time.time()
        self.waiting_for_players = not vs_ai  # إذا كانت ضد لاعب آخر، ننتظر لاعبين
        self.ai_player_index = None
        
        # إضافة المنشئ كأول لاعب
        self.players.append({
            'id': creator_id,
            'name': creator_name,
            'score': 0
        })
        self.scores[creator_id] = 0
        
        if vs_ai:
            # إضافة يوكي كلاعب ثاني
            self.players.append({
                'id': -1,  # معرف خاص ليوكي
                'name': 'يوكي',
                'score': 0
            })
            self.scores[-1] = 0
            self.ai_player_index = 1
            self.game_started = True
    
    def get_random_question(self) -> dict:
        """اختيار سؤال عشوائي"""
        return random.choice(QUESTIONS_DB)
    
    def add_player(self, user_id: int, user_name: str) -> bool:
        """إضافة لاعب جديد (للعب ضد لاعب آخر)"""
        if self.vs_ai or len(self.players) >= 2:
            return False
        
        self.players.append({
            'id': user_id,
            'name': user_name,
            'score': 0
        })
        self.scores[user_id] = 0
        
        if len(self.players) == 2:
            self.waiting_for_players = False
            self.game_started = True
        
        return True
    
    def get_ai_answer(self, question: dict) -> bool:
        """يوكي يجيب على السؤال (مع بعض الأخطاء أحياناً)"""
        # يوكي لديه 85% من الصحة
        if random.random() < 0.85:
            return question["answer"]
        else:
            return not question["answer"]
    
    def submit_answer(self, user_id: int, answer: bool) -> bool:
        """تسجيل إجابة اللاعب"""
        if user_id not in [p['id'] for p in self.players]:
            return False
        
        self.player_answers[user_id] = answer
        return True
    
    def check_round_complete(self) -> bool:
        """فحص إذا اكتملت الجولة"""
        expected_players = len(self.players)
        if self.vs_ai:
            # في حالة اللعب ضد يوكي، نحتاج إجابة اللاعب الحقيقي فقط
            return self.creator_id in self.player_answers
        else:
            # في حالة اللعب ضد لاعب آخر، نحتاج إجابات جميع اللاعبين
            return len(self.player_answers) == expected_players
    
    def process_round(self) -> dict:
        """معالجة نتائج الجولة"""
        correct_answer = self.current_question["answer"]
        round_results = {}
        
        for player in self.players:
            player_id = player['id']
            
            if player_id == -1:  # يوكي
                ai_answer = self.get_ai_answer(self.current_question)
                self.player_answers[player_id] = ai_answer
            
            player_answer = self.player_answers.get(player_id)
            is_correct = player_answer == correct_answer
            
            if is_correct:
                self.scores[player_id] += 1
                player['score'] += 1
            
            round_results[player_id] = {
                'answer': player_answer,
                'correct': is_correct,
                'player_name': player['name']
            }
        
        # تنظيف الإجابات للجولة التالية
        self.player_answers.clear()
        self.round_number += 1
        
        # فحص انتهاء اللعبة
        if self.round_number > self.max_rounds:
            self.game_ended = True
        
        return {
            'correct_answer': correct_answer,
            'results': round_results,
            'question': self.current_question["question"],
            'category': self.current_question["category"]
        }
    
    def get_winner(self) -> Optional[dict]:
        """تحديد الفائز"""
        if not self.game_ended:
            return None
        
        max_score = max(self.scores.values())
        winners = [p for p in self.players if self.scores[p['id']] == max_score]
        
        if len(winners) == 1:
            return {"type": "winner", "player": winners[0], "score": max_score}
        else:
            return {"type": "tie", "players": winners, "score": max_score}

def get_game_keyboard(game: TrueFalseGame, waiting_for_answer: bool = False) -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح اللعبة"""
    keyboard = []
    
    if not game.game_started and game.waiting_for_players:
        # انتظار لاعب ثاني
        keyboard.append([
            InlineKeyboardButton(
                text="🎯 انضم للعبة", 
                callback_data=f"tf_join_{game.group_id}"
            )
        ])
    elif waiting_for_answer and not game.game_ended:
        # أزرار الإجابة
        keyboard.append([
            InlineKeyboardButton(
                text="✅ صحيح", 
                callback_data=f"tf_answer_true_{game.group_id}"
            ),
            InlineKeyboardButton(
                text="❌ خطأ", 
                callback_data=f"tf_answer_false_{game.group_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def start_true_false_game(message: Message, vs_ai: bool = True):
    """بدء لعبة صدق أم كذب"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_TRUE_FALSE_GAMES:
            await message.reply("🎮 **يوجد لعبة صدق أم كذب نشطة!**\n\nانتظر انتهاء اللعبة الحالية")
            return
        
        # التأكد من تسجيل المستخدم
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء لعبة جديدة
        game = TrueFalseGame(group_id, creator_id, creator_name, vs_ai)
        ACTIVE_TRUE_FALSE_GAMES[group_id] = game
        
        if vs_ai:
            # بدء اللعبة مباشرة ضد يوكي
            await start_new_round(message, game)
        else:
            # انتظار لاعب ثاني
            game_text = (
                f"🎮 **لعبة صدق أم كذب!**\n\n"
                f"👤 **المنشئ:** {creator_name}\n"
                f"👥 **نوع اللعبة:** ضد لاعب آخر\n"
                f"🎯 **عدد الجولات:** {game.max_rounds}\n\n"
                f"⏳ **انتظار لاعب ثاني للانضمام...**\n"
                f"🎖️ **اضغط على الزر للانضمام!**"
            )
            
            keyboard = get_game_keyboard(game)
            await message.reply(game_text, reply_markup=keyboard)
        
        logging.info(f"بدأت لعبة صدق أم كذب في المجموعة {group_id} - ضد {'يوكي' if vs_ai else 'لاعب آخر'}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة صدق أم كذب: {e}")
        await message.reply("❌ حدث خطأ في بدء اللعبة")

async def start_new_round(message: Message, game: TrueFalseGame):
    """بدء جولة جديدة"""
    try:
        # اختيار سؤال جديد
        game.current_question = game.get_random_question()
        
        # تنسيق أسماء اللاعبين
        players_text = ""
        for i, player in enumerate(game.players):
            score = player['score']
            if player['id'] == -1:
                players_text += f"🤖 **يوكي:** {score} نقطة\n"
            else:
                players_text += f"👤 **{player['name']}:** {score} نقطة\n"
        
        game_text = (
            f"🎮 **لعبة صدق أم كذب - الجولة {game.round_number}/{game.max_rounds}**\n\n"
            f"{players_text}\n"
            f"📚 **الفئة:** {game.current_question['category']}\n"
            f"❓ **السؤال:**\n{game.current_question['question']}\n\n"
            f"🤔 **هل هذه المعلومة صحيحة أم خاطئة؟**"
        )
        
        keyboard = get_game_keyboard(game, waiting_for_answer=True)
        
        if hasattr(message, 'edit_text'):
            await message.edit_text(game_text, reply_markup=keyboard)
        else:
            await message.reply(game_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في بدء جولة جديدة: {e}")

async def handle_tf_join(callback: CallbackQuery):
    """معالجة انضمام لاعب للعبة"""
    try:
        group_id = callback.message.chat.id
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "لاعب"
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_TRUE_FALSE_GAMES:
            await callback.answer("❌ لا توجد لعبة نشطة!", show_alert=True)
            return
        
        game = ACTIVE_TRUE_FALSE_GAMES[group_id]
        
        # فحص إذا كان المستخدم هو منشئ اللعبة
        if user_id == game.creator_id:
            await callback.answer("❌ أنت منشئ اللعبة بالفعل!", show_alert=True)
            return
        
        # إضافة اللاعب
        if game.add_player(user_id, user_name):
            await callback.answer("✅ تم انضمامك للعبة!")
            
            # بدء الجولة الأولى
            await start_new_round(callback.message, game)
        else:
            await callback.answer("❌ لا يمكن الانضمام للعبة!", show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في انضمام لاعب: {e}")
        await callback.answer("❌ حدث خطأ", show_alert=True)

async def handle_tf_answer(callback: CallbackQuery, answer: bool):
    """معالجة إجابة اللاعب"""
    try:
        group_id = callback.message.chat.id
        user_id = callback.from_user.id
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_TRUE_FALSE_GAMES:
            await callback.answer("❌ لا توجد لعبة نشطة!", show_alert=True)
            return
        
        game = ACTIVE_TRUE_FALSE_GAMES[group_id]
        
        # فحص إذا كان المستخدم جزء من اللعبة
        if user_id not in [p['id'] for p in game.players]:
            await callback.answer("❌ أنت لست جزءاً من هذه اللعبة!", show_alert=True)
            return
        
        # فحص إذا كان المستخدم أجاب بالفعل
        if user_id in game.player_answers:
            await callback.answer("❌ لقد أجبت بالفعل على هذا السؤال!", show_alert=True)
            return
        
        # تسجيل الإجابة
        game.submit_answer(user_id, answer)
        await callback.answer("✅ تم تسجيل إجابتك!")
        
        # فحص إذا اكتملت الجولة
        if game.check_round_complete():
            round_results = game.process_round()
            await show_round_results(callback.message, game, round_results)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة إجابة: {e}")
        await callback.answer("❌ حدث خطأ", show_alert=True)

async def show_round_results(message, game: TrueFalseGame, results: dict):
    """عرض نتائج الجولة"""
    try:
        # نتائج الجولة
        results_text = (
            f"📊 **نتائج الجولة {game.round_number - 1}:**\n\n"
            f"❓ **السؤال:** {results['question']}\n"
            f"📚 **الفئة:** {results['category']}\n"
            f"✅ **الإجابة الصحيحة:** {'صحيح' if results['correct_answer'] else 'خطأ'}\n\n"
        )
        
        # إجابات اللاعبين
        for player_id, result in results['results'].items():
            player_name = result['player_name']
            player_answer = 'صحيح' if result['answer'] else 'خطأ'
            status = '✅' if result['correct'] else '❌'
            
            results_text += f"{status} **{player_name}:** {player_answer}\n"
        
        # النقاط الحالية
        results_text += f"\n🏆 **النقاط الحالية:**\n"
        for player in game.players:
            score = player['score']
            if player['id'] == -1:
                results_text += f"🤖 **يوكي:** {score} نقطة\n"
            else:
                results_text += f"👤 **{player['name']}:** {score} نقطة\n"
        
        if game.game_ended:
            # انتهت اللعبة
            await handle_game_end(message, game, results_text)
        else:
            # استمرار للجولة التالية
            results_text += f"\n⏳ **الجولة التالية خلال 3 ثوان...**"
            await message.edit_text(results_text)
            
            # انتظار ثم بدء الجولة التالية
            import asyncio
            await asyncio.sleep(3)
            await start_new_round(message, game)
        
    except Exception as e:
        logging.error(f"خطأ في عرض نتائج الجولة: {e}")

async def handle_game_end(message, game: TrueFalseGame, results_text: str):
    """معالجة نهاية اللعبة"""
    try:
        leveling_system = LevelingSystem()
        winner_info = game.get_winner()
        
        # نص نهاية اللعبة
        end_text = results_text + f"\n\n🏁 **انتهت اللعبة!**\n\n"
        
        if winner_info["type"] == "winner":
            winner = winner_info["player"]
            winner_score = winner_info["score"]
            
            if winner['id'] == -1:
                end_text += f"🤖 **الفائز: يوكي** بـ {winner_score} نقطة!\n"
                end_text += f"😅 **حظ أفضل في المرة القادمة!**"
                
                # منح XP للاعب الخاسر
                await leveling_system.add_xp(game.creator_id, "gaming", 5)
            else:
                end_text += f"🎉 **الفائز: {winner['name']}** بـ {winner_score} نقطة!\n"
                end_text += f"🏆 **مبروك! مكافآتك:**\n• +20 XP\n• +1500$"
                
                # منح XP والمال للفائز
                await leveling_system.add_xp(winner['id'], "gaming", 20)
                
                # منح المال
                user_data = await get_or_create_user(winner['id'])
                if user_data:
                    from database.operations import update_user_balance, add_transaction
                    new_balance = user_data['balance'] + 1500
                    await update_user_balance(winner['id'], new_balance)
                    await add_transaction(winner['id'], "صدق أم كذب", 1500, "game_win")
        else:
            # تعادل
            end_text += f"🤝 **تعادل!** كل لاعب حصل على {winner_info['score']} نقطة\n"
            end_text += f"🎖️ **مكافآت التعادل:** +10 XP + 750$ لكل لاعب"
            
            # منح مكافآت التعادل
            for player in game.players:
                if player['id'] != -1:  # تجاهل يوكي
                    await leveling_system.add_xp(player['id'], "gaming", 10)
                    
                    user_data = await get_or_create_user(player['id'])
                    if user_data:
                        from database.operations import update_user_balance, add_transaction
                        new_balance = user_data['balance'] + 750
                        await update_user_balance(player['id'], new_balance)
                        await add_transaction(player['id'], "صدق أم كذب", 750, "game_tie")
        
        await message.edit_text(end_text)
        
        # إزالة اللعبة من الذاكرة
        if game.group_id in ACTIVE_TRUE_FALSE_GAMES:
            del ACTIVE_TRUE_FALSE_GAMES[game.group_id]
        
        # رد من يوكي
        ai_player = get_ai_player("quiz")
        if winner_info["type"] == "winner" and winner_info["player"]["id"] == -1:
            ai_message = await ai_player.get_game_response("victory", "فزت هذه المرة!")
        else:
            ai_message = await ai_player.get_game_response("encouragement", "لعبة ممتعة!")
        
        await message.reply(f"🤖 {ai_message}")
        
        logging.info(f"انتهت لعبة صدق أم كذب في المجموعة {game.group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية اللعبة: {e}")

# معلومات اللعبة
TRUE_FALSE_GAME_INFO = {
    "name": "🤔 صدق أم كذب",
    "description": "لعبة أسئلة ثقافية - ضد يوكي أو لاعب آخر",
    "commands": ["صدق أم كذب", "صدق كذب", "true false"],
    "players": "لاعب واحد ضد يوكي أو لاعبين",
    "duration": "3-5 دقائق",
    "status": "متاحة"
}
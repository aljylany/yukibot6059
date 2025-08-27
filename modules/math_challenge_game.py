"""
لعبة التحدي الرياضي - لعبة حل المعادلات البسيطة
Math Challenge Game - ضد يوكي أو لاعب آخر
"""

import logging
import random
import time
import operator
from typing import Dict, Optional, Tuple
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.operations import get_or_create_user
from modules.leveling import LevelingSystem
from modules.ai_player import get_ai_player
from utils.helpers import format_number

# الألعاب النشطة {group_id: game_data}
ACTIVE_MATH_GAMES: Dict[int, dict] = {}

class MathChallenge:
    """فئة لعبة التحدي الرياضي"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str, vs_ai: bool = True):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.vs_ai = vs_ai
        self.players = []
        self.current_question = None
        self.question_number = 1
        self.max_questions = 7
        self.player_answers = {}  # إجابات اللاعبين للسؤال الحالي
        self.scores = {}  # النقاط التراكمية
        self.game_started = False
        self.game_ended = False
        self.created_at = time.time()
        self.waiting_for_players = not vs_ai
        self.ai_player_index = None
        self.difficulty = "easy"  # easy, medium, hard
        
        # إضافة المنشئ
        self.players.append({
            'id': creator_id,
            'name': creator_name,
            'score': 0
        })
        self.scores[creator_id] = 0
        
        if vs_ai:
            # إضافة يوكي
            self.players.append({
                'id': -1,
                'name': 'يوكي',
                'score': 0
            })
            self.scores[-1] = 0
            self.ai_player_index = 1
            self.game_started = True
    
    def generate_question(self) -> Tuple[str, int, str]:
        """توليد سؤال رياضي حسب المستوى"""
        if self.difficulty == "easy":
            # جمع وطرح أرقام من 1-50
            num1 = random.randint(1, 50)
            num2 = random.randint(1, 50)
            op = random.choice(['+', '-'])
            
            if op == '+':
                answer = num1 + num2
                question = f"{num1} + {num2} = ؟"
                category = "جمع بسيط"
            else:
                # للطرح، نتأكد أن النتيجة موجبة
                if num1 < num2:
                    num1, num2 = num2, num1
                answer = num1 - num2
                question = f"{num1} - {num2} = ؟"
                category = "طرح بسيط"
                
        elif self.difficulty == "medium":
            # ضرب وقسمة أرقام بسيطة
            if random.random() < 0.5:
                # ضرب
                num1 = random.randint(2, 12)
                num2 = random.randint(2, 12)
                answer = num1 * num2
                question = f"{num1} × {num2} = ؟"
                category = "ضرب"
            else:
                # قسمة (نتأكد أن النتيجة صحيحة)
                answer = random.randint(2, 15)
                num2 = random.randint(2, 10)
                num1 = answer * num2
                question = f"{num1} ÷ {num2} = ؟"
                category = "قسمة"
                
        else:  # hard
            # معادلات مختلطة أكثر تعقيداً
            operations = [
                lambda: self._create_complex_addition(),
                lambda: self._create_square_operation(),
                lambda: self._create_mixed_operation()
            ]
            question, answer, category = random.choice(operations)()
        
        return question, answer, category
    
    def _create_complex_addition(self) -> Tuple[str, int, str]:
        """إنشاء معادلة جمع/طرح معقدة"""
        num1 = random.randint(50, 200)
        num2 = random.randint(20, 100)
        num3 = random.randint(10, 50)
        
        # مثال: 150 + 75 - 30
        answer = num1 + num2 - num3
        question = f"{num1} + {num2} - {num3} = ؟"
        return question, answer, "معادلة مختلطة"
    
    def _create_square_operation(self) -> Tuple[str, int, str]:
        """إنشاء معادلة مربع"""
        num = random.randint(3, 15)
        answer = num * num
        question = f"{num}² = ؟"
        return question, answer, "مربع العدد"
    
    def _create_mixed_operation(self) -> Tuple[str, int, str]:
        """إنشاء معادلة مختلطة"""
        num1 = random.randint(5, 20)
        num2 = random.randint(2, 8)
        num3 = random.randint(10, 30)
        
        # مثال: (15 × 4) + 25
        answer = (num1 * num2) + num3
        question = f"({num1} × {num2}) + {num3} = ؟"
        return question, answer, "معادلة مع أقواس"
    
    def add_player(self, user_id: int, user_name: str) -> bool:
        """إضافة لاعب جديد"""
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
    
    def get_ai_answer(self, correct_answer: int) -> int:
        """حساب إجابة يوكي (مع احتمال خطأ صغير)"""
        # يوكي يجيب صحيح 85% من الوقت
        if random.random() < 0.85:
            return correct_answer
        else:
            # خطأ بسيط في الحساب
            error_range = max(1, abs(correct_answer) // 10)
            error = random.randint(-error_range, error_range)
            return correct_answer + error
    
    def submit_answer(self, user_id: int, answer: int) -> bool:
        """تسجيل إجابة اللاعب"""
        if user_id not in [p['id'] for p in self.players]:
            return False
        
        self.player_answers[user_id] = answer
        return True
    
    def check_round_complete(self) -> bool:
        """فحص إذا اكتملت الجولة"""
        if self.vs_ai:
            return self.creator_id in self.player_answers
        else:
            return len(self.player_answers) == len(self.players)
    
    def process_round(self) -> dict:
        """معالجة نتائج الجولة"""
        correct_answer = self.current_question["answer"]
        round_results = {}
        
        for player in self.players:
            player_id = player['id']
            
            if player_id == -1:  # يوكي
                ai_answer = self.get_ai_answer(correct_answer)
                self.player_answers[player_id] = ai_answer
            
            player_answer = self.player_answers.get(player_id, 0)
            is_correct = player_answer == correct_answer
            
            if is_correct:
                points = 1
                self.scores[player_id] += points
                player['score'] += points
            else:
                points = 0
            
            round_results[player_id] = {
                'answer': player_answer,
                'correct': is_correct,
                'points': points,
                'player_name': player['name']
            }
        
        # تنظيف الإجابات
        self.player_answers.clear()
        self.question_number += 1
        
        # فحص انتهاء اللعبة
        if self.question_number > self.max_questions:
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

def get_answer_keyboard(game: MathChallenge, options: list) -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح خيارات الإجابة"""
    keyboard = []
    
    # إنشاء صفين من الخيارات
    row1 = []
    row2 = []
    
    for i, option in enumerate(options):
        button = InlineKeyboardButton(
            text=f"{option}",
            callback_data=f"math_answer_{game.group_id}_{option}"
        )
        if i < 2:
            row1.append(button)
        else:
            row2.append(button)
    
    keyboard.append(row1)
    if row2:
        keyboard.append(row2)
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def generate_answer_options(correct_answer: int) -> list:
    """توليد 4 خيارات للإجابة"""
    options = [correct_answer]
    
    # إضافة 3 خيارات خاطئة
    for _ in range(3):
        # توليد خيار خاطئ قريب من الإجابة الصحيحة
        error_range = max(1, abs(correct_answer) // 3)
        wrong_answer = correct_answer + random.randint(-error_range, error_range)
        
        # تأكد من عدم تكرار الإجابة
        while wrong_answer in options:
            wrong_answer = correct_answer + random.randint(-error_range, error_range)
        
        options.append(wrong_answer)
    
    # خلط الخيارات
    random.shuffle(options)
    return options

async def start_math_challenge_game(message: Message, vs_ai: bool = True, difficulty: str = "easy"):
    """بدء لعبة التحدي الرياضي"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_MATH_GAMES:
            await message.reply("🎮 **يوجد تحدي رياضي نشط!**\n\nانتظر انتهاء التحدي الحالي")
            return
        
        # التأكد من تسجيل المستخدم
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء لعبة جديدة
        game = MathChallenge(group_id, creator_id, creator_name, vs_ai)
        game.difficulty = difficulty
        ACTIVE_MATH_GAMES[group_id] = game
        
        difficulty_names = {
            "easy": "سهل (جمع وطرح)",
            "medium": "متوسط (ضرب وقسمة)", 
            "hard": "صعب (معادلات مختلطة)"
        }
        
        if vs_ai:
            # بدء اللعبة ضد يوكي
            await start_new_question(message, game)
        else:
            # انتظار لاعب ثاني
            game_text = (
                f"🧮 **التحدي الرياضي!**\n\n"
                f"👤 **المنشئ:** {creator_name}\n"
                f"👥 **نوع اللعبة:** ضد لاعب آخر\n"
                f"📊 **المستوى:** {difficulty_names[difficulty]}\n"
                f"🎯 **عدد الأسئلة:** {game.max_questions}\n\n"
                f"⏳ **انتظار لاعب ثاني للانضمام...**"
            )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🎯 انضم للتحدي", callback_data=f"math_join_{group_id}")
            ]])
            
            await message.reply(game_text, reply_markup=keyboard)
        
        logging.info(f"بدأ تحدي رياضي في المجموعة {group_id} - مستوى {difficulty}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء التحدي الرياضي: {e}")
        await message.reply("❌ حدث خطأ في بدء التحدي")

async def start_new_question(message, game: MathChallenge):
    """بدء سؤال جديد"""
    try:
        # توليد سؤال جديد
        question, answer, category = game.generate_question()
        game.current_question = {
            "question": question,
            "answer": answer,
            "category": category
        }
        
        # توليد خيارات الإجابة
        answer_options = generate_answer_options(answer)
        
        # تنسيق النقاط
        scores_text = ""
        for player in game.players:
            if player['id'] == -1:
                scores_text += f"🤖 **يوكي:** {player['score']} نقطة\n"
            else:
                scores_text += f"👤 **{player['name']}:** {player['score']} نقطة\n"
        
        game_text = (
            f"🧮 **التحدي الرياضي - السؤال {game.question_number}/{game.max_questions}**\n\n"
            f"{scores_text}\n"
            f"📚 **الفئة:** {category}\n"
            f"❓ **المعادلة:**\n**{question}**\n\n"
            f"🤔 **اختر الإجابة الصحيحة:**"
        )
        
        keyboard = get_answer_keyboard(game, answer_options)
        
        if hasattr(message, 'edit_text'):
            await message.edit_text(game_text, reply_markup=keyboard)
        else:
            await message.reply(game_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في بدء سؤال جديد: {e}")

async def handle_math_join(callback: CallbackQuery):
    """معالجة انضمام لاعب للتحدي"""
    try:
        group_id = callback.message.chat.id
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "لاعب"
        
        if group_id not in ACTIVE_MATH_GAMES:
            await callback.answer("❌ لا يوجد تحدي نشط!", show_alert=True)
            return
        
        game = ACTIVE_MATH_GAMES[group_id]
        
        if user_id == game.creator_id:
            await callback.answer("❌ أنت منشئ التحدي بالفعل!", show_alert=True)
            return
        
        if game.add_player(user_id, user_name):
            await callback.answer("✅ تم انضمامك للتحدي!")
            await start_new_question(callback.message, game)
        else:
            await callback.answer("❌ لا يمكن الانضمام!", show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في انضمام لاعب: {e}")
        await callback.answer("❌ حدث خطأ", show_alert=True)

async def handle_math_answer(callback: CallbackQuery):
    """معالجة إجابة اللاعب"""
    try:
        # استخراج البيانات
        parts = callback.data.split('_')
        group_id = int(parts[2])
        answer = int(parts[3])
        user_id = callback.from_user.id
        
        if group_id not in ACTIVE_MATH_GAMES:
            await callback.answer("❌ لا يوجد تحدي نشط!", show_alert=True)
            return
        
        game = ACTIVE_MATH_GAMES[group_id]
        
        # فحص إذا كان المستخدم جزء من اللعبة
        if user_id not in [p['id'] for p in game.players]:
            await callback.answer("❌ أنت لست جزءاً من هذا التحدي!", show_alert=True)
            return
        
        # فحص إذا أجاب بالفعل
        if user_id in game.player_answers:
            await callback.answer("❌ لقد أجبت بالفعل!", show_alert=True)
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

async def show_round_results(message, game: MathChallenge, results: dict):
    """عرض نتائج الجولة"""
    try:
        results_text = (
            f"📊 **نتائج السؤال {game.question_number - 1}:**\n\n"
            f"❓ **المعادلة:** {results['question']}\n"
            f"✅ **الإجابة الصحيحة:** {results['correct_answer']}\n\n"
        )
        
        # إجابات اللاعبين
        for player_id, result in results['results'].items():
            player_name = result['player_name']
            player_answer = result['answer']
            status = '✅' if result['correct'] else '❌'
            
            results_text += f"{status} **{player_name}:** {player_answer}\n"
        
        # النقاط الحالية
        results_text += f"\n🏆 **النقاط:**\n"
        for player in game.players:
            if player['id'] == -1:
                results_text += f"🤖 **يوكي:** {player['score']}/{game.max_questions}\n"
            else:
                results_text += f"👤 **{player['name']}:** {player['score']}/{game.max_questions}\n"
        
        if game.game_ended:
            await handle_game_end(message, game, results_text)
        else:
            results_text += f"\n⏳ **السؤال التالي خلال 3 ثوان...**"
            await message.edit_text(results_text)
            
            import asyncio
            await asyncio.sleep(3)
            await start_new_question(message, game)
        
    except Exception as e:
        logging.error(f"خطأ في عرض النتائج: {e}")

async def handle_game_end(message, game: MathChallenge, results_text: str):
    """معالجة نهاية اللعبة"""
    try:
        leveling_system = LevelingSystem()
        winner_info = game.get_winner()
        
        end_text = results_text + f"\n\n🏁 **انتهى التحدي الرياضي!**\n\n"
        
        if winner_info["type"] == "winner":
            winner = winner_info["player"]
            winner_score = winner_info["score"]
            
            if winner['id'] == -1:
                end_text += f"🤖 **الفائز: يوكي** بـ {winner_score} نقطة!\n"
                end_text += f"😅 **حالة أفضل في المرة القادمة!**"
                
                # منح XP للاعب
                await leveling_system.add_xp(game.creator_id, "gaming", 8)
            else:
                end_text += f"🎉 **الفائز: {winner['name']}** بـ {winner_score} نقطة!\n"
                end_text += f"🧠 **ممتاز! مكافآتك:**\n• +25 XP\n• +2000$"
                
                # منح المكافآت
                await leveling_system.add_xp(winner['id'], "gaming", 25)
                
                user_data = await get_or_create_user(winner['id'])
                if user_data:
                    from database.operations import update_user_balance, add_transaction
                    new_balance = user_data['balance'] + 2000
                    await update_user_balance(winner['id'], new_balance)
                    await add_transaction(winner['id'], "التحدي الرياضي", 2000, "math_win")
        else:
            # تعادل
            end_text += f"🤝 **تعادل!** نتيجة متميزة من الجميع\n"
            end_text += f"🎖️ **مكافآت التعادل:** +15 XP + 1000$ لكل لاعب"
            
            for player in game.players:
                if player['id'] != -1:
                    await leveling_system.add_xp(player['id'], "gaming", 15)
                    
                    user_data = await get_or_create_user(player['id'])
                    if user_data:
                        from database.operations import update_user_balance, add_transaction
                        new_balance = user_data['balance'] + 1000
                        await update_user_balance(player['id'], new_balance)
                        await add_transaction(player['id'], "التحدي الرياضي", 1000, "math_tie")
        
        await message.edit_text(end_text)
        
        # إزالة اللعبة
        if game.group_id in ACTIVE_MATH_GAMES:
            del ACTIVE_MATH_GAMES[game.group_id]
        
        # رد من يوكي
        ai_player = get_ai_player("math")
        if winner_info["type"] == "winner" and winner_info["player"]["id"] == -1:
            ai_message = await ai_player.get_game_response("victory", "الرياضيات ممتعة!")
        else:
            ai_message = await ai_player.get_game_response("encouragement", "عقول ذكية!")
        
        await message.reply(f"🤖 {ai_message}")
        
        logging.info(f"انتهى التحدي الرياضي في المجموعة {game.group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية التحدي: {e}")

# معلومات اللعبة
MATH_CHALLENGE_INFO = {
    "name": "🧮 التحدي الرياضي",
    "description": "حل المعادلات البسيطة - ضد يوكي أو لاعب آخر",
    "commands": ["تحدي رياضي", "رياضيات", "math challenge"],
    "players": "لاعب واحد ضد يوكي أو لاعبين",
    "duration": "3-5 دقائق",
    "status": "متاحة"
}
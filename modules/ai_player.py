"""
نظام AI Player - الذكاء الاصطناعي للألعاب
AI Player System - Artificial Intelligence for Games
"""

import logging
import asyncio
import random
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

class AIPlayer:
    """نظام الذكاء الاصطناعي للمشاركة في الألعاب"""
    
    def __init__(self):
        self.name = "يوكي"
        self.user_id = -1  # معرف خاص للبوت AI
        self.personality = {
            'competitive': 0.7,  # مدى التنافسية (0-1)
            'helpful': 0.9,      # مدى المساعدة (0-1)
            'playful': 0.8,      # مدى المرح (0-1)
            'strategic': 0.8     # مدى التفكير الاستراتيجي (0-1)
        }
        
        # ردود تفاعلية للألعاب
        self.game_responses = {
            'victory': [
                "🎉 يااااه! فزت! الذكاء الاصطناعي ممتاز في هذه اللعبة!",
                "🏆 هاها! يوكي لا يُقهر! لعبة ممتعة",
                "✨ فوز رائع! حبيت اللعب معكم",
                "🤖 الذكاء الاصطناعي 1 - البشر 0! لعبة أخرى؟"
            ],
            'defeat': [
                "😅 أحسنتم! أنتم أذكى مني في هذه المرة",
                "👏 مبروك الفوز! لعبتم بذكاء",
                "🎯 فوز مستحق! أنا أتعلم منكم",
                "😊 حلوة اللعبة! أنتم محترفين"
            ],
            'encouragement': [
                "🔥 تقدرون على هذا! لا تستسلموا",
                "💪 أنتم قريبين من الحل!",
                "🎯 فكروا أكثر، أنتم أذكى من كذا",
                "✨ ممتاز! أنتم في الطريق الصحيح"
            ],
            'hints': [
                "💡 نصيحة من يوكي: فكروا بطريقة مختلفة",
                "🧠 تلميح: أحياناً الحل البسيط هو الأفضل",
                "🎯 اقتراح: راجعوا خياراتكم مرة ثانية",
                "💭 فكرة: جربوا استراتيجية مختلفة"
            ]
        }
    
    async def should_join_game(self, game_type: str, players_count: int) -> bool:
        """تحديد إذا كان AI سينضم للعبة أم لا"""
        
        # معايير الانضمام للألعاب
        join_criteria = {
            'xo': players_count == 1,  # ينضم إذا كان هناك لاعب واحد فقط
            'number_guess': players_count >= 2,  # ينضم إذا كان هناك لاعبان أو أكثر
            'quick_quiz': players_count >= 1,  # ينضم دائماً للمساعدة
            'letter_shuffle': players_count >= 1,  # ينضم للمساعدة
            'symbols': players_count >= 1  # ينضم للمساعدة
        }
        
        base_chance = join_criteria.get(game_type, False)
        
        # إضافة عشوائية للقرار
        random_factor = random.random() < 0.8  # 80% احتمال
        
        return base_chance and random_factor
    
    async def get_game_response(self, response_type: str, context: Optional[str] = None) -> str:
        """الحصول على رد مناسب للعبة"""
        
        if response_type not in self.game_responses:
            return "🤖 يوكي في الخدمة!"
        
        response = random.choice(self.game_responses[response_type])
        
        # تخصيص الرد حسب السياق
        if context:
            response += f"\n{context}"
        
        return response

class XOAIPlayer(AIPlayer):
    """AI محترف للعب اكس-اوه"""
    
    def __init__(self):
        super().__init__()
        self.difficulty = 'hard'  # easy, medium, hard
    
    def evaluate_position(self, board: List[str], ai_symbol: str, player_symbol: str) -> int:
        """تقييم الموقف على اللوحة"""
        
        # فحص الفوز
        winner = self.check_winner(board)
        if winner == ai_symbol:
            return 10
        elif winner == player_symbol:
            return -10
        elif self.is_board_full(board):
            return 0
        
        return 0
    
    def minimax(self, board: List[str], depth: int, is_maximizing: bool, 
                ai_symbol: str, player_symbol: str, alpha: int = -1000, beta: int = 1000) -> int:
        """خوارزمية Minimax مع Alpha-Beta Pruning"""
        
        score = self.evaluate_position(board, ai_symbol, player_symbol)
        
        # إذا انتهت اللعبة
        if score == 10 or score == -10 or self.is_board_full(board):
            return score
        
        if is_maximizing:
            best_score = -1000
            for i in range(9):
                if board[i] == "⬜":
                    board[i] = ai_symbol
                    score = self.minimax(board, depth + 1, False, ai_symbol, player_symbol, alpha, beta)
                    board[i] = "⬜"
                    best_score = max(score, best_score)
                    alpha = max(alpha, best_score)
                    if beta <= alpha:
                        break
            return best_score
        else:
            best_score = 1000
            for i in range(9):
                if board[i] == "⬜":
                    board[i] = player_symbol
                    score = self.minimax(board, depth + 1, True, ai_symbol, player_symbol, alpha, beta)
                    board[i] = "⬜"
                    best_score = min(score, best_score)
                    beta = min(beta, best_score)
                    if beta <= alpha:
                        break
            return best_score
    
    def get_best_move(self, board: List[str], ai_symbol: str, player_symbol: str) -> int:
        """الحصول على أفضل حركة"""
        
        board_copy = board.copy()
        
        # صعوبة سهلة - حركات عشوائية أحياناً
        if self.difficulty == 'easy' and random.random() < 0.3:
            empty_positions = [i for i in range(9) if board[i] == "⬜"]
            return random.choice(empty_positions) if empty_positions else 0
        
        # صعوبة متوسطة - خطأ أحياناً
        if self.difficulty == 'medium' and random.random() < 0.15:
            empty_positions = [i for i in range(9) if board[i] == "⬜"]
            return random.choice(empty_positions) if empty_positions else 0
        
        best_move = -1
        best_score = -1000
        
        for i in range(9):
            if board_copy[i] == "⬜":
                board_copy[i] = ai_symbol
                move_score = self.minimax(board_copy, 0, False, ai_symbol, player_symbol)
                board_copy[i] = "⬜"
                
                if move_score > best_score:
                    best_score = move_score
                    best_move = i
        
        return best_move if best_move != -1 else 0
    
    def check_winner(self, board: List[str]) -> Optional[str]:
        """فحص الفائز"""
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # صفوف
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # أعمدة
            [0, 4, 8], [2, 4, 6]              # أقطار
        ]
        
        for combo in winning_combinations:
            if (board[combo[0]] == board[combo[1]] == board[combo[2]] and 
                board[combo[0]] != "⬜"):
                return board[combo[0]]
        
        return None
    
    def is_board_full(self, board: List[str]) -> bool:
        """فحص امتلاء اللوحة"""
        return "⬜" not in board
    
    async def make_move_with_personality(self, board: List[str], ai_symbol: str, player_symbol: str) -> Tuple[int, str]:
        """اتخاذ قرار مع شخصية AI"""
        
        move = self.get_best_move(board, ai_symbol, player_symbol)
        
        # ردود حسب الموقف
        winner_after_move = None
        board_copy = board.copy()
        board_copy[move] = ai_symbol
        winner_after_move = self.check_winner(board_copy)
        
        if winner_after_move == ai_symbol:
            response = await self.get_game_response('victory')
        else:
            # فحص إذا كان اللاعب قريب من الفوز
            player_can_win = False
            for i in range(9):
                if board[i] == "⬜":
                    board[i] = player_symbol
                    if self.check_winner(board) == player_symbol:
                        player_can_win = True
                    board[i] = "⬜"
                    break
            
            if player_can_win:
                response = "🛡️ لن تفوز بسهولة! يوكي يدافع"
            else:
                response = "🎯 حركة ذكية! دوركم الآن"
        
        return move, response

class NumberGuessAI(AIPlayer):
    """AI للمساعدة في لعبة خمن الرقم"""
    
    def __init__(self):
        super().__init__()
        self.strategy = 'helpful'  # helpful, competitive, balanced
    
    async def analyze_guess(self, guess: int, target: int, attempt_number: int) -> str:
        """تحليل محاولة التخمين وإعطاء نصائح"""
        
        distance = abs(guess - target)
        
        # تحليل ذكي للمحاولة
        if distance == 0:
            return await self.get_game_response('victory', "🎯 مبروك! خمنتوها بالضبط!")
        
        # نصائح مختلفة حسب المسافة
        if distance <= 3:
            hints = [
                "🔥 ساخن جداً! أنتم على بُعد خطوات قليلة!",
                "⚡ قريب جداً! حاولوا الأرقام المجاورة",
                "🎯 ممتاز! تقريباً وصلتم للهدف"
            ]
        elif distance <= 8:
            hints = [
                "🌡️ ساخن! الهدف قريب منكم",
                "🔎 جيد! ابحثوا في المنطقة المجاورة",
                "💫 تقدم رائع! واصلوا البحث"
            ]
        elif distance <= 15:
            hints = [
                "😐 دافئ... تحتاجون تعديل الاتجاه قليلاً",
                "🤔 قريبين نوعاً ما، فكروا في الاتجاه الصحيح",
                "📈 أو 📉 جربوا أرقام أعلى أو أقل"
            ]
        elif distance <= 25:
            hints = [
                "🧊 بارد... ابتعدوا عن هذه المنطقة",
                "🔄 غيروا الاستراتيجية تماماً",
                "🎲 جربوا أرقام مختلفة كلياً"
            ]
        else:
            hints = [
                "❄️ بارد جداً! أنتم في المنطقة الخاطئة",
                "🚀 غيروا الاتجاه كلياً!",
                "🔥 ابحثوا في منطقة مختلفة تماماً"
            ]
        
        hint = random.choice(hints)
        
        # إضافة تشجيع حسب عدد المحاولات
        if attempt_number <= 3:
            hint += "\n💪 بداية قوية! واصلوا"
        elif attempt_number <= 7:
            hint += "\n⏰ وقت مناسب للتركيز أكثر"
        else:
            hint += "\n🎯 الوقت ينفد! فكروا بذكاء"
        
        return hint
    
    async def give_strategic_hint(self, current_guesses: List[int], target: int, max_attempts: int) -> str:
        """إعطاء نصيحة استراتيجية"""
        
        if not current_guesses:
            return "💡 نصيحة يوكي: ابدؤوا بالأرقام الوسطى مثل 50!"
        
        min_guess = min(current_guesses)
        max_guess = max(current_guesses)
        
        strategies = [
            f"🧠 استراتيجية ذكية: جربوا Binary Search بين {min_guess} و {max_guess}",
            f"📊 تحليل يوكي: أرقامكم السابقة تشير لمنطقة معينة",
            f"🎯 خطة محكمة: قسموا المجال المتبقي إلى أجزاء",
            f"⚡ نصيحة سريعة: تجنبوا تكرار الأخطاء السابقة"
        ]
        
        return random.choice(strategies)

class QuizAI(AIPlayer):
    """AI للتفاعل مع لعبة السؤال والجواب"""
    
    def __init__(self):
        super().__init__()
        self.knowledge_level = 'expert'  # beginner, intermediate, expert
    
    async def analyze_answer(self, question: str, correct_answer: str, user_answer: str, 
                           is_correct: bool, response_time: float) -> str:
        """تحليل إجابة اللاعب"""
        
        if is_correct:
            if response_time < 2.0:
                return "⚡ إجابة سريعة وصحيحة! ممتاز جداً!"
            elif response_time < 5.0:
                return "✅ صحيح! وقت جيد"
            else:
                return "🎯 صحيح! المهم الإجابة الصحيحة"
        else:
            # تحليل الإجابة الخاطئة وإعطاء تلميح
            encouragement = [
                f"❌ خطأ، الإجابة الصحيحة: {correct_answer}",
                f"📚 تعلموا: الجواب كان {correct_answer}",
                f"💡 المرة القادمة! الصحيح: {correct_answer}"
            ]
            return random.choice(encouragement)
    
    async def give_hint(self, question: str, correct_answer: str) -> str:
        """إعطاء تلميح للسؤال"""
        
        hints = [
            f"💭 تلميح: فكروا في الموضوع الرئيسي للسؤال",
            f"🔍 دليل: راجعوا الخيارات بعناية",
            f"💡 مساعدة: استبعدوا الإجابات المستحيلة أولاً",
            f"🧠 نصيحة: ثقوا في معرفتكم الأولى"
        ]
        
        return random.choice(hints)
    
    async def react_to_game_progress(self, correct_answers: int, total_questions: int) -> str:
        """التفاعل مع تقدم اللعبة"""
        
        score_percentage = (correct_answers / total_questions) * 100
        
        if score_percentage >= 80:
            return "🏆 أداء ممتاز! أنتم عباقرة فعلاً!"
        elif score_percentage >= 60:
            return "👍 أداء جيد! واصلوا التقدم"
        elif score_percentage >= 40:
            return "💪 تحسن مستمر! لا تستسلموا"
        else:
            return "🎯 التركيز أكثر! أنتم تقدرون على الأفضل"

class LetterShuffleAI(AIPlayer):
    """AI للمساعدة في لعبة ترتيب الحروف"""
    
    def __init__(self):
        super().__init__()
        self.hint_level = 'progressive'  # direct, progressive, cryptic
    
    async def give_word_hint(self, word: str, shuffled_letters: str, attempt_count: int) -> str:
        """إعطاء تلميح للكلمة"""
        
        # تلميحات تدريجية حسب عدد المحاولات
        if attempt_count == 1:
            # تلميح عام
            return f"💭 تلميح يوكي: الكلمة مكونة من {len(word)} أحرف"
        
        elif attempt_count == 2:
            # تلميح الحرف الأول
            return f"🔤 الحرف الأول: {word[0]}"
        
        elif attempt_count == 3:
            # تلميح أكثر تفصيلاً
            hint_word = word[0] + "_" * (len(word) - 2) + word[-1]
            return f"📝 شكل الكلمة: {hint_word}"
        
        else:
            # تلميح قوي
            hint_word = ""
            for i, letter in enumerate(word):
                if i < len(word) // 2:
                    hint_word += letter
                else:
                    hint_word += "_"
            return f"💡 تلميح قوي: {hint_word}..."
    
    async def analyze_attempt(self, word: str, user_attempt: str) -> str:
        """تحليل محاولة اللاعب"""
        
        if user_attempt.lower() == word.lower():
            return await self.get_game_response('victory', "🎉 ممتاز! رتبتم الحروف بنجاح!")
        
        # تحليل مدى قرب المحاولة
        correct_letters = sum(1 for i, letter in enumerate(user_attempt.lower()) 
                             if i < len(word) and letter == word[i].lower())
        
        if correct_letters > len(word) // 2:
            return "🔥 قريب جداً! حاولوا ترتيب بعض الحروف"
        elif correct_letters > 0:
            return "👍 في الطريق الصحيح! بعض الحروف صحيحة"
        else:
            return "🤔 حاولوا التفكير في معنى الكلمة أولاً"

# إنشاء نسخ من المساعدين الذكيين
xo_ai = XOAIPlayer()
number_ai = NumberGuessAI()
quiz_ai = QuizAI()
shuffle_ai = LetterShuffleAI()
word_ai = shuffle_ai  # نفس AI للعبة ترتيب الحروف

# دالة مساعدة للوصول للـ AI المناسب
def get_ai_player(game_type: str) -> AIPlayer:
    """الحصول على AI player المناسب للعبة"""
    
    ai_players = {
        'xo': xo_ai,
        'number_guess': number_ai,
        'quick_quiz': quiz_ai,
        'letter_shuffle': shuffle_ai
    }
    
    return ai_players.get(game_type, AIPlayer())

async def should_ai_participate(game_type: str, players_count: int) -> bool:
    """تحديد إذا كان AI سيشارك في اللعبة"""
    
    ai_player = get_ai_player(game_type)
    return await ai_player.should_join_game(game_type, players_count)

# تصدير المساعدين
__all__ = [
    'AIPlayer', 'XOAIPlayer', 'NumberGuessAI', 'QuizAI', 'LetterShuffleAI',
    'xo_ai', 'number_ai', 'quiz_ai', 'shuffle_ai', 'word_ai', 'get_ai_player', 'should_ai_participate'
]
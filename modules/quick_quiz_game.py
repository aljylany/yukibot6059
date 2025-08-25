"""
لعبة سؤال وجواب سريعة - Quick Quiz Game
أسئلة ثقافة عامة بسيطة وممتعة للمجموعات
"""

import logging
import random
import time
from typing import Dict, List, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.leveling import LevelingSystem
from utils.helpers import format_number

# الألعاب النشطة {group_id: game_data}
ACTIVE_QUIZ_GAMES: Dict[int, dict] = {}

# قاعدة بيانات الأسئلة
QUIZ_QUESTIONS = [
    {
        "question": "ما هي عاصمة السعودية؟",
        "options": ["الرياض", "جدة", "مكة"],
        "correct": 0,
        "category": "جغرافيا"
    },
    {
        "question": "كم عدد أركان الإسلام؟",
        "options": ["4", "5", "6"],
        "correct": 1,
        "category": "دين"
    },
    {
        "question": "ما هو أكبر كوكب في النظام الشمسي؟",
        "options": ["الأرض", "المشتري", "زحل"],
        "correct": 1,
        "category": "علوم"
    },
    {
        "question": "في أي قارة تقع مصر؟",
        "options": ["آسيا", "أفريقيا", "أوروبا"],
        "correct": 1,
        "category": "جغرافيا"
    },
    {
        "question": "كم يوماً في السنة الميلادية؟",
        "options": ["364", "365", "366"],
        "correct": 1,
        "category": "عامة"
    },
    {
        "question": "ما هو لون دم الإنسان؟",
        "options": ["أزرق", "أحمر", "أخضر"],
        "correct": 1,
        "category": "علوم"
    },
    {
        "question": "كم عدد أصابع اليد الواحدة؟",
        "options": ["4", "5", "6"],
        "correct": 1,
        "category": "عامة"
    },
    {
        "question": "ما هي أطول سورة في القرآن؟",
        "options": ["الفاتحة", "البقرة", "آل عمران"],
        "correct": 1,
        "category": "دين"
    },
    {
        "question": "في أي شهر يصوم المسلمون؟",
        "options": ["شعبان", "رمضان", "شوال"],
        "correct": 1,
        "category": "دين"
    },
    {
        "question": "ما هو أسرع حيوان في البر؟",
        "options": ["الأسد", "الغزال", "الفهد"],
        "correct": 2,
        "category": "طبيعة"
    },
    {
        "question": "كم عدد قارات العالم؟",
        "options": ["6", "7", "8"],
        "correct": 1,
        "category": "جغرافيا"
    },
    {
        "question": "ما هي عملة الإمارات؟",
        "options": ["الريال", "الدرهم", "الدينار"],
        "correct": 1,
        "category": "عامة"
    },
    {
        "question": "كم عدد العجائب السبع في العالم؟",
        "options": ["6", "7", "8"],
        "correct": 1,
        "category": "تاريخ"
    },
    {
        "question": "ما هو أكبر محيط في العالم؟",
        "options": ["الأطلسي", "الهادئ", "الهندي"],
        "correct": 1,
        "category": "جغرافيا"
    },
    {
        "question": "كم عدد الصلوات المفروضة في اليوم؟",
        "options": ["3", "5", "7"],
        "correct": 1,
        "category": "دين"
    },
    {
        "question": "ما هو أطول نهر في العالم؟",
        "options": ["النيل", "الأمازون", "المسيسيبي"],
        "correct": 0,
        "category": "جغرافيا"
    },
    {
        "question": "في أي عام كانت كأس العالم في قطر؟",
        "options": ["2021", "2022", "2023"],
        "correct": 1,
        "category": "رياضة"
    },
    {
        "question": "كم عدد أشهر السنة؟",
        "options": ["10", "12", "14"],
        "correct": 1,
        "category": "عامة"
    },
    {
        "question": "ما هو الرقم الذي يأتي بعد 99؟",
        "options": ["100", "101", "199"],
        "correct": 0,
        "category": "رياضيات"
    },
    {
        "question": "أين تقع مدينة دبي؟",
        "options": ["السعودية", "الإمارات", "الكويت"],
        "correct": 1,
        "category": "جغرافيا"
    }
]

class QuickQuizGame:
    """فئة لعبة سؤال وجواب سريعة"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.current_question = None
        self.question_number = 0
        self.max_questions = 5  # 5 أسئلة لكل جولة
        self.participants = {}  # {user_id: {"name": str, "score": int, "answered": bool}}
        self.game_started = True
        self.game_ended = False
        self.created_at = time.time()
        self.question_start_time = 0
        self.answer_time_limit = 30  # 30 ثانية لكل سؤال
        self.prize_per_correct = 5000  # 5K لكل إجابة صحيحة
        
        # بدء أول سؤال
        self.start_new_question()
    
    def start_new_question(self):
        """بدء سؤال جديد"""
        if self.question_number >= self.max_questions:
            self.game_ended = True
            return
        
        self.question_number += 1
        self.current_question = random.choice(QUIZ_QUESTIONS)
        self.question_start_time = time.time()
        
        # إعادة تعيين حالة الإجابة لجميع المشاركين
        for participant in self.participants.values():
            participant["answered"] = False
    
    def add_participant(self, user_id: int, user_name: str):
        """إضافة مشارك جديد"""
        if user_id not in self.participants:
            self.participants[user_id] = {
                "name": user_name,
                "score": 0,
                "answered": False
            }
    
    def answer_question(self, user_id: int, user_name: str, choice: int) -> str:
        """الإجابة على السؤال"""
        # إضافة المشارك إذا لم يكن موجوداً
        self.add_participant(user_id, user_name)
        
        participant = self.participants[user_id]
        
        # فحص إذا أجاب من قبل على هذا السؤال
        if participant["answered"]:
            return "❌ لقد أجبت على هذا السؤال بالفعل!"
        
        # فحص انتهاء الوقت
        time_passed = time.time() - self.question_start_time
        if time_passed > self.answer_time_limit:
            return "⏰ انتهى الوقت المحدد للإجابة!"
        
        # تسجيل الإجابة
        participant["answered"] = True
        
        if choice == self.current_question["correct"]:
            participant["score"] += 1
            return f"✅ إجابة صحيحة يا {user_name}! (+1 نقطة)"
        else:
            correct_answer = self.current_question["options"][self.current_question["correct"]]
            return f"❌ إجابة خاطئة! الإجابة الصحيحة: {correct_answer}"
    
    def get_question_display(self) -> str:
        """عرض السؤال الحالي"""
        if not self.current_question or self.game_ended:
            return ""
        
        time_remaining = max(0, self.answer_time_limit - (time.time() - self.question_start_time))
        
        question_text = (
            f"📝 **سؤال وجواب سريع - السؤال {self.question_number}/{self.max_questions}**\n\n"
            f"🎯 **الفئة:** {self.current_question['category']}\n"
            f"❓ **السؤال:** {self.current_question['question']}\n\n"
            f"⏰ **الوقت المتبقي:** {int(time_remaining)} ثانية\n"
            f"👥 **المشاركين:** {len(self.participants)}\n\n"
            f"اختر الإجابة الصحيحة:"
        )
        
        return question_text
    
    def get_question_keyboard(self) -> InlineKeyboardMarkup:
        """إنشاء لوحة مفاتيح السؤال"""
        if not self.current_question or self.game_ended:
            return InlineKeyboardMarkup(inline_keyboard=[])
        
        keyboard = []
        for i, option in enumerate(self.current_question["options"]):
            button_text = f"{chr(65+i)}. {option}"  # A, B, C
            callback_data = f"quiz_answer_{self.group_id}_{i}"
            keyboard.append([InlineKeyboardButton(text=button_text, callback_data=callback_data)])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_final_results(self) -> str:
        """عرض النتائج النهائية"""
        if not self.participants:
            return "❌ لم يشارك أحد في الألعاب!"
        
        # ترتيب المشاركين حسب النقاط
        sorted_participants = sorted(
            self.participants.items(), 
            key=lambda x: x[1]["score"], 
            reverse=True
        )
        
        results_text = (
            f"🏆 **انتهت اللعبة - النتائج النهائية**\n\n"
            f"📊 **عدد الأسئلة:** {self.max_questions}\n"
            f"👥 **عدد المشاركين:** {len(self.participants)}\n\n"
            f"🎖️ **النتائج:**\n"
        )
        
        medals = ["🥇", "🥈", "🥉"]
        for i, (user_id, data) in enumerate(sorted_participants[:10]):  # أفضل 10
            medal = medals[i] if i < 3 else f"{i+1}."
            score_percent = int((data["score"] / self.max_questions) * 100)
            results_text += f"{medal} {data['name']}: {data['score']}/{self.max_questions} ({score_percent}%)\n"
        
        # عرض الفائز
        if sorted_participants:
            winner = sorted_participants[0]
            if winner[1]["score"] > 0:
                results_text += f"\n🎉 **المبروك للفائز:** {winner[1]['name']}"
        
        return results_text

async def start_quick_quiz_game(message: Message):
    """بدء لعبة سؤال وجواب سريعة"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # فحص إذا كانت اللعبة في مجموعة
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذه اللعبة تعمل في المجموعات فقط!")
            return
        
        # فحص وجود لعبة نشطة
        if group_id in ACTIVE_QUIZ_GAMES:
            await message.reply("📝 **يوجد مسابقة نشطة!**\n\nانتظر انتهاء المسابقة الحالية")
            return
        
        # التحقق من تسجيل المنشئ
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء لعبة جديدة
        game = QuickQuizGame(group_id, creator_id, creator_name)
        ACTIVE_QUIZ_GAMES[group_id] = game
        
        # عرض أول سؤال
        question_text = game.get_question_display()
        keyboard = game.get_question_keyboard()
        
        await message.reply(question_text, reply_markup=keyboard)
        logging.info(f"تم بدء مسابقة سؤال وجواب في المجموعة {group_id} بواسطة {creator_name}")
        
        # إعداد مؤقت السؤال
        import asyncio
        asyncio.create_task(question_timer(game, message))
        
    except Exception as e:
        logging.error(f"خطأ في بدء مسابقة سؤال وجواب: {e}")
        await message.reply("❌ حدث خطأ في بدء المسابقة")

async def handle_quiz_answer(callback_query, choice: int):
    """معالجة إجابة السؤال"""
    try:
        group_id = callback_query.message.chat.id
        user_id = callback_query.from_user.id
        user_name = callback_query.from_user.first_name or "اللاعب"
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_QUIZ_GAMES:
            await callback_query.answer("❌ لا توجد مسابقة نشطة!", show_alert=True)
            return
        
        game = ACTIVE_QUIZ_GAMES[group_id]
        
        if game.game_ended:
            await callback_query.answer("❌ انتهت المسابقة!", show_alert=True)
            return
        
        # التحقق من تسجيل المستخدم
        user_data = await get_or_create_user(user_id, callback_query.from_user.username or "", user_name)
        if not user_data:
            await callback_query.answer("❌ يجب إنشاء حساب أولاً!", show_alert=True)
            return
        
        # الإجابة على السؤال
        result = game.answer_question(user_id, user_name, choice)
        await callback_query.answer(result)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة إجابة المسابقة: {e}")
        await callback_query.answer("❌ حدث خطأ في معالجة الإجابة", show_alert=True)

async def question_timer(game: QuickQuizGame, message: Message):
    """مؤقت السؤال"""
    import asyncio
    
    while not game.game_ended and game.group_id in ACTIVE_QUIZ_GAMES:
        # انتظار انتهاء وقت السؤال
        await asyncio.sleep(game.answer_time_limit)
        
        if game.game_ended:
            break
        
        # عرض الإجابة الصحيحة والانتقال للسؤال التالي
        correct_answer = game.current_question["options"][game.current_question["correct"]]
        answered_count = len([p for p in game.participants.values() if p["answered"]])
        
        answer_text = (
            f"⏰ **انتهى وقت السؤال {game.question_number}!**\n\n"
            f"✅ **الإجابة الصحيحة:** {correct_answer}\n"
            f"👥 **عدد من أجاب:** {answered_count}\n\n"
        )
        
        # بدء السؤال التالي أو إنهاء اللعبة
        game.start_new_question()
        
        if game.game_ended:
            # عرض النتائج النهائية
            final_results = game.get_final_results()
            await message.reply(answer_text + final_results)
            
            # توزيع الجوائز
            await distribute_prizes(game)
            
            # إزالة اللعبة
            if game.group_id in ACTIVE_QUIZ_GAMES:
                del ACTIVE_QUIZ_GAMES[game.group_id]
            break
        else:
            # عرض السؤال التالي
            question_text = game.get_question_display()
            keyboard = game.get_question_keyboard()
            
            await message.reply(answer_text + "⬇️ **السؤال التالي:**")
            await message.reply(question_text, reply_markup=keyboard)

async def distribute_prizes(game: QuickQuizGame):
    """توزيع الجوائز على المشاركين"""
    try:
        leveling_system = LevelingSystem()
        
        for user_id, data in game.participants.items():
            if data["score"] > 0:
                # جائزة مالية حسب النقاط
                prize = data["score"] * game.prize_per_correct
                
                user_data = await get_or_create_user(user_id)
                if user_data:
                    new_balance = user_data["balance"] + prize
                    await update_user_balance(user_id, new_balance)
                    await add_transaction(user_id, f"مسابقة سؤال وجواب ({data['score']} نقطة)", prize, "quiz_prize")
                    await leveling_system.add_xp(user_id, "gaming")
        
    except Exception as e:
        logging.error(f"خطأ في توزيع جوائز المسابقة: {e}")

# معلومات اللعبة
QUICK_QUIZ_INFO = {
    "name": "🧠 سؤال وجواب سريع",
    "description": "أسئلة ثقافة عامة بسيطة مع 3 اختيارات لكل سؤال",
    "commands": ["سؤال وجواب", "مسابقة", "quiz"],
    "players": "مفتوح للجميع",
    "duration": "3-5 دقائق",
    "status": "متاحة"
}
"""
لعبة ترتيب الحروف - ترتيب الحروف المختلطة لتكوين كلمة
Letter Shuffle Game Module
"""

import logging
import random
import time
import asyncio
from typing import Dict, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number
from modules.ai_player import word_ai, should_ai_participate

# قاموس الألعاب النشطة {group_id: LetterShuffleGame}
ACTIVE_SHUFFLE_GAMES: Dict[int, 'LetterShuffleGame'] = {}

# حماية من الإزعاج - حد زمني بين الألعاب (30 ثانية)
GAME_COOLDOWN = {}  # {group_id: last_game_time}
COOLDOWN_DURATION = 30  # ثانية

# قاموس الكلمات للعبة ترتيب الحروف
SHUFFLE_WORDS = [
    {
        "word": "كتاب",
        "shuffled": "ب ت ك ا",
        "hint": "شيء نقرأ منه",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "مدرسة", 
        "shuffled": "س ة ر د م",
        "hint": "مكان التعلم",
        "difficulty": 2,
        "points": 150
    },
    {
        "word": "سيارة",
        "shuffled": "ر ة ا ي س",
        "hint": "مركبة بأربع عجلات",
        "difficulty": 2,
        "points": 150
    },
    {
        "word": "بيت",
        "shuffled": "ت ي ب",
        "hint": "مكان السكن",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "قلم",
        "shuffled": "م ل ق",
        "hint": "أداة الكتابة",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "حاسوب",
        "shuffled": "ب و س ا ح",
        "hint": "جهاز إلكتروني",
        "difficulty": 3,
        "points": 200
    },
    {
        "word": "هاتف",
        "shuffled": "ف ت ا ه",
        "hint": "جهاز للاتصال",
        "difficulty": 2,
        "points": 150
    },
    {
        "word": "شمس",
        "shuffled": "س م ش",
        "hint": "نجم مضيء في النهار",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "قمر",
        "shuffled": "ر م ق",
        "hint": "يضيء في الليل",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "ماء",
        "shuffled": "ء ا م",
        "hint": "سائل شفاف للشرب",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "نار",
        "shuffled": "ر ا ن",
        "hint": "تعطي حرارة ونور",
        "difficulty": 1,
        "points": 100
    },
    {
        "word": "طائرة",
        "shuffled": "ة ر ا ط ئ",
        "hint": "تطير في السماء",
        "difficulty": 3,
        "points": 200
    },
    {
        "word": "مستشفى",
        "shuffled": "ى ف ش ت س م",
        "hint": "مكان علاج المرضى",
        "difficulty": 4,
        "points": 250
    },
    {
        "word": "مكتبة",
        "shuffled": "ة ب ت ك م",
        "hint": "مكان الكتب",
        "difficulty": 3,
        "points": 200
    },
    {
        "word": "حديقة",
        "shuffled": "ة ق ي د ح",
        "hint": "مكان الأشجار والزهور",
        "difficulty": 3,
        "points": 200
    }
]

class LetterShuffleGame:
    """فئة لعبة ترتيب الحروف"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.current_word = None
        self.attempts = []  # قائمة المحاولات
        self.max_attempts = 20  # الحد الأقصى للمحاولات
        self.max_user_attempts = 3  # محاولات لكل لاعب
        self.game_started = True
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.game_duration = 60  # مدة اللعبة بالثواني
        self.prize_pool = 5000  # الجائزة الأساسية
        self.hint_used = False
        self.game_message_id = None  # لحذف الرسالة لاحقاً
        self.ai_enabled = False  # هل AI مفعل في اللعبة
        self.ai_hints_given = 0  # عدد التلميحات من AI
        
        # اختيار كلمة عشوائية
        self.select_random_word()
    
    def select_random_word(self):
        """اختيار كلمة عشوائية"""
        self.current_word = random.choice(SHUFFLE_WORDS)
        # زيادة الجائزة حسب الصعوبة
        self.prize_pool = self.current_word["points"] * 50
    
    def get_hint(self) -> str:
        """الحصول على تلميح"""
        if self.hint_used:
            return "💡 **تم استخدام التلميح مسبقاً!**"
        
        self.hint_used = True
        return f"💡 **تلميح:** {self.current_word['hint']}"
    
    async def get_ai_analysis(self, guess: str) -> str:
        """تحليل AI للتخمين"""
        if not self.ai_enabled:
            return ""
        
        try:
            analysis = await word_ai.analyze_guess(
                guess, 
                self.current_word['word'], 
                self.current_word['shuffled']
            )
            return analysis
        except Exception as e:
            logging.error(f"خطأ في AI analysis: {e}")
            return ""
    
    async def get_ai_hint(self) -> str:
        """تلميح ذكي من AI"""
        if not self.ai_enabled or self.ai_hints_given >= 2:
            return ""
        
        try:
            self.ai_hints_given += 1
            hint = await word_ai.give_hint(
                self.current_word['word'],
                self.current_word['shuffled'],
                self.current_word['hint']
            )
            return hint
        except Exception as e:
            logging.error(f"خطأ في AI hint: {e}")
            return ""
    
    def check_guess(self, user_id: int, user_name: str, guess: str) -> str:
        """فحص تخمين اللاعب"""
        # تنظيف النص
        guess = guess.strip().lower()
        correct_word = self.current_word["word"].lower()
        
        # فحص عدد محاولات المستخدم
        user_attempts = len([a for a in self.attempts if a["user_id"] == user_id])
        if user_attempts >= self.max_user_attempts:
            return f"❌ **{user_name}** لقد استنفدت محاولاتك ({self.max_user_attempts} محاولات)"
        
        # إضافة المحاولة
        attempt = {
            "user_id": user_id,
            "name": user_name,
            "guess": guess,
            "time": time.time(),
            "correct": guess == correct_word
        }
        self.attempts.append(attempt)
        
        if guess == correct_word:
            self.winner = {"id": user_id, "name": user_name}
            self.game_ended = True
            return f"🎉 **مبروك {user_name}!** أجبت بشكل صحيح!\n💰 ربحت {format_number(self.prize_pool)}$"
        else:
            remaining_attempts = self.max_user_attempts - (user_attempts + 1)
            if remaining_attempts > 0:
                return f"❌ **{user_name}** إجابة خاطئة! يتبقى لك {remaining_attempts} محاولة"
            else:
                return f"❌ **{user_name}** إجابة خاطئة! لقد استنفدت محاولاتك"
    
    def is_game_expired(self) -> bool:
        """فحص انتهاء وقت اللعبة"""
        return time.time() - self.created_at > self.game_duration
    
    def get_game_keyboard(self):
        """إنشاء لوحة مفاتيح اللعبة"""
        keyboard = []
        
        if not self.game_ended and not self.is_game_expired():
            # زر التلميح
            hint_text = "💡 تلميح" if not self.hint_used else "💡 تم استخدامه"
            keyboard.append([
                InlineKeyboardButton(
                    text=hint_text, 
                    callback_data=f"shuffle_hint_{self.group_id}"
                )
            ])
            
            # زر الحالة
            keyboard.append([
                InlineKeyboardButton(
                    text="📊 الحالة", 
                    callback_data=f"shuffle_status_{self.group_id}"
                )
            ])
        
        # زر الإلغاء/الإغلاق
        close_text = "❌ إنهاء اللعبة" if not self.game_ended else "🗑️ إغلاق"
        keyboard.append([
            InlineKeyboardButton(
                text=close_text, 
                callback_data=f"shuffle_close_{self.group_id}"
            )
        ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def get_game_status(self) -> str:
        """الحصول على حالة اللعبة"""
        if self.game_ended:
            if self.winner:
                return f"🏆 **انتهت اللعبة!**\n🎉 الفائز: {self.winner['name']}"
            else:
                return "⏰ **انتهت اللعبة!**\nلم يجب أحد بشكل صحيح"
        
        time_left = max(0, self.game_duration - (time.time() - self.created_at))
        return f"⏰ الوقت المتبقي: {int(time_left)} ثانية\n📊 المحاولات: {len(self.attempts)}/{self.max_attempts}"


def check_game_cooldown(group_id: int) -> bool:
    """فحص الحد الزمني بين الألعاب"""
    current_time = time.time()
    if group_id in GAME_COOLDOWN:
        time_passed = current_time - GAME_COOLDOWN[group_id]
        if time_passed < COOLDOWN_DURATION:
            return False
    return True

def set_game_cooldown(group_id: int):
    """تعيين الحد الزمني للمجموعة"""
    GAME_COOLDOWN[group_id] = time.time()

async def start_letter_shuffle_game(message: Message):
    """بدء لعبة ترتيب الحروف الجديدة"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # التحقق من أن البوت في مجموعة
        if message.chat.type == 'private':
            await message.reply(
                "🚫 **هذه اللعبة متاحة في المجموعات فقط!**\n\n"
                "➕ أضف البوت لمجموعتك واستمتع باللعب مع الأصدقاء"
            )
            return
        
        # فحص الحد الزمني بين الألعاب (منع الإزعاج)
        if not check_game_cooldown(group_id):
            time_left = COOLDOWN_DURATION - (time.time() - GAME_COOLDOWN[group_id])
            await message.reply(
                f"⏰ **انتظر قليلاً!**\n\n"
                f"لمنع الإزعاج، يجب انتظار {int(time_left)} ثانية قبل بدء لعبة جديدة"
            )
            return
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_SHUFFLE_GAMES and not ACTIVE_SHUFFLE_GAMES[group_id].game_ended:
            await message.reply(
                "⚠️ **يوجد لعبة ترتيب حروف نشطة حالياً!**\n\n"
                "🎯 انتظر انتهاء اللعبة الحالية أو شارك في الحل"
            )
            return
        
        # التأكد من تسجيل المنشئ
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # إنشاء اللعبة الجديدة
        game = LetterShuffleGame(group_id, creator_id, creator_name)
        ACTIVE_SHUFFLE_GAMES[group_id] = game
        
        # فحص إذا كان AI سيشارك
        if await should_ai_participate('word_shuffle', 1):
            game.ai_enabled = True
        
        # تعيين الحد الزمني
        set_game_cooldown(group_id)
        
        # إرسال رسالة اللعبة
        game_text = (
            f"🎯 **لعبة خلط الحروف بدأت!**\n\n"
            f"🔤 **الحروف المختلطة:** {game.current_word['shuffled']}\n"
            f"📝 **المطلوب:** رتب الحروف لتكوين كلمة صحيحة\n\n"
            f"👤 **منشئ اللعبة:** {creator_name}\n"
            f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
            f"⏱️ **المدة:** {game.game_duration} ثانية\n"
            f"🎯 **محاولات لكل لاعب:** {game.max_user_attempts}\n\n"
            f"🚀 **اكتب الكلمة الصحيحة في الدردشة لتفوز!**"
        )
        
        game_message = await message.reply(game_text, reply_markup=game.get_game_keyboard())
        game.game_message_id = game_message.message_id
        
        # رسالة ترحيب من AI إذا كان مفعل
        if game.ai_enabled:
            ai_welcome = await word_ai.get_game_response('encouragement', 
                f"🎯 لعبة رائعة! سأساعدكم في حل الكلمة")
            await message.reply(ai_welcome)
        
        # بدء مؤقت انتهاء اللعبة (منع الإزعاج)
        asyncio.create_task(auto_end_game(group_id, game.game_duration))
        
        logging.info(f"تم بدء لعبة خلط الحروف في المجموعة {group_id} - AI: {game.ai_enabled}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة ترتيب الحروف: {e}")
        await message.reply("❌ حدث خطأ في بدء اللعبة")

async def auto_end_game(group_id: int, duration: int):
    """إنهاء اللعبة تلقائياً بعد انتهاء الوقت (منع الإزعاج)"""
    await asyncio.sleep(duration)
    
    if group_id in ACTIVE_SHUFFLE_GAMES:
        game = ACTIVE_SHUFFLE_GAMES[group_id]
        if not game.game_ended:
            game.game_ended = True
            
            # حذف رسالة اللعبة القديمة لمنع الازدحام
            try:
                if game.game_message_id:
                    from aiogram import Bot
                    bot = Bot.get_current()
                    await bot.delete_message(group_id, game.game_message_id)
            except Exception as e:
                logging.error(f"خطأ في حذف رسالة اللعبة: {e}")
            
            # إرسال رسالة إنهاء بسيطة
            try:
                from aiogram import Bot
                bot = Bot.get_current()
                await bot.send_message(
                    group_id,
                    f"⏰ **انتهت لعبة خلط الحروف!**\n\n"
                    f"🔤 الكلمة الصحيحة كانت: **{game.current_word['word']}**\n"
                    f"❌ لم يجب أحد بشكل صحيح"
                )
            except Exception as e:
                logging.error(f"خطأ في إرسال رسالة انتهاء اللعبة: {e}")

async def handle_shuffle_guess(message: Message):
    """معالجة تخمين في لعبة ترتيب الحروف"""
    try:
        group_id = message.chat.id
        
        # التحقق من وجود لعبة نشطة
        if group_id not in ACTIVE_SHUFFLE_GAMES:
            return
        
        game = ACTIVE_SHUFFLE_GAMES[group_id]
        
        # التحقق من حالة اللعبة
        if game.game_ended or game.is_game_expired():
            return
        
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "لاعب"
        guess = message.text.strip()
        
        # فحص التخمين
        result = game.check_guess(user_id, user_name, guess)
        
        # إرسال النتيجة
        await message.reply(result)
        
        # إضافة تحليل AI إذا كان مفعل ولم يفز اللاعب
        if game.ai_enabled and not game.winner:
            ai_analysis = await game.get_ai_analysis(guess)
            if ai_analysis:
                await message.reply(f"🤖 **تحليل يوكي:** {ai_analysis}")
        
        # إذا فاز أحد
        if game.winner:
            # رسالة تهنئة من AI
            if game.ai_enabled:
                ai_congrats = await word_ai.get_game_response('victory', "مبروك للفائز!")
                await message.reply(ai_congrats)
            # منح الجائزة
            await update_user_balance(user_id, game.prize_pool)
            await add_transaction(
                user_id, 
                game.prize_pool, 
                "win", 
                "جائزة لعبة خلط الحروف"
            )
            
            # حذف رسالة اللعبة القديمة
            try:
                if game.game_message_id:
                    await message.bot.delete_message(group_id, game.game_message_id)
            except Exception as e:
                logging.error(f"خطأ في حذف رسالة اللعبة: {e}")
            
            # إنهاء اللعبة
            del ACTIVE_SHUFFLE_GAMES[group_id]
        
        # التحقق من استنفاد المحاولات
        elif len(game.attempts) >= game.max_attempts:
            game.game_ended = True
            
            # حذف رسالة اللعبة القديمة
            try:
                if game.game_message_id:
                    await message.bot.delete_message(group_id, game.game_message_id)
            except Exception as e:
                logging.error(f"خطأ في حذف رسالة اللعبة: {e}")
            
            await message.reply(
                f"❌ **انتهت اللعبة!**\n\n"
                f"🔤 الكلمة الصحيحة كانت: **{game.current_word['word']}**\n"
                f"📊 استنفدت المحاولات المسموحة ({game.max_attempts})"
            )
            
            del ACTIVE_SHUFFLE_GAMES[group_id]
        
    except Exception as e:
        logging.error(f"خطأ في معالجة تخمين ترتيب الحروف: {e}")

async def handle_shuffle_hint_callback(callback_query):
    """معالجة طلب التلميح"""
    try:
        group_id = int(callback_query.data.split("_")[-1])
        
        if group_id not in ACTIVE_SHUFFLE_GAMES:
            await callback_query.answer("❌ اللعبة غير متاحة", show_alert=True)
            return
        
        game = ACTIVE_SHUFFLE_GAMES[group_id]
        
        if game.game_ended or game.is_game_expired():
            await callback_query.answer("❌ انتهت اللعبة", show_alert=True)
            return
        
        hint = game.get_hint()
        
        # إضافة تلميح AI إضافي إذا كان متاح
        if game.ai_enabled and not game.hint_used:  # إذا لم يُستخدم التلميح الأساسي بعد
            ai_hint = await game.get_ai_hint()
            if ai_hint:
                hint += f"\n\n🤖 {ai_hint}"
        
        await callback_query.answer(hint, show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التلميح: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

async def handle_shuffle_status_callback(callback_query):
    """معالجة طلب الحالة"""
    try:
        group_id = int(callback_query.data.split("_")[-1])
        
        if group_id not in ACTIVE_SHUFFLE_GAMES:
            await callback_query.answer("❌ اللعبة غير متاحة", show_alert=True)
            return
        
        game = ACTIVE_SHUFFLE_GAMES[group_id]
        status = game.get_game_status()
        await callback_query.answer(status, show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الحالة: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

async def handle_shuffle_close_callback(callback_query):
    """معالجة إغلاق اللعبة"""
    try:
        group_id = int(callback_query.data.split("_")[-1])
        user_id = callback_query.from_user.id
        
        if group_id not in ACTIVE_SHUFFLE_GAMES:
            await callback_query.answer("❌ اللعبة غير متاحة", show_alert=True)
            return
        
        game = ACTIVE_SHUFFLE_GAMES[group_id]
        
        # التحقق من الصلاحيات (المنشئ أو مشرف)
        if user_id != game.creator_id:
            # يمكن إضافة فحص المشرفين هنا إذا لزم الأمر
            await callback_query.answer("❌ يمكن لمنشئ اللعبة فقط إغلاقها", show_alert=True)
            return
        
        # حذف رسالة اللعبة
        try:
            await callback_query.message.delete()
        except Exception as e:
            logging.error(f"خطأ في حذف رسالة اللعبة: {e}")
        
        # إنهاء اللعبة
        del ACTIVE_SHUFFLE_GAMES[group_id]
        
        await callback_query.answer("✅ تم إغلاق اللعبة")
        
    except Exception as e:
        logging.error(f"خطأ في إغلاق اللعبة: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)
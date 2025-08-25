"""
لعبة الكلمة - تخمين الكلمة من التعريف
Word Game Module - Guess the word from definition
"""

import logging
import random
import time
from typing import Dict, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number

# قاموس الألعاب النشطة {group_id: WordGame}
ACTIVE_WORD_GAMES: Dict[int, 'WordGame'] = {}

# قاموس الكلمات والتعريفات
WORD_DATABASE = [
    {
        "word": "مدرسة",
        "definition": "مكان التعلم والتعليم للطلاب",
        "category": "تعليم",
        "difficulty": 1
    },
    {
        "word": "مستشفى", 
        "definition": "مكان لعلاج المرضى والجرحى",
        "category": "طب",
        "difficulty": 1
    },
    {
        "word": "مطار",
        "definition": "مكان إقلاع وهبوط الطائرات",
        "category": "نقل",
        "difficulty": 1
    },
    {
        "word": "مكتبة",
        "definition": "مكان يحتوي على الكتب للقراءة والاستعارة",
        "category": "ثقافة",
        "difficulty": 1
    },
    {
        "word": "صحراء",
        "definition": "أرض واسعة مليئة بالرمال وقليلة المطر",
        "category": "جغرافيا",
        "difficulty": 1
    },
    {
        "word": "قلم",
        "definition": "أداة للكتابة والرسم",
        "category": "أدوات",
        "difficulty": 1
    },
    {
        "word": "شمس",
        "definition": "النجم المضيء الذي ينير الأرض في النهار",
        "category": "طبيعة", 
        "difficulty": 1
    },
    {
        "word": "قمر",
        "definition": "الجرم السماوي الذي يضيء ليلاً ويدور حول الأرض",
        "category": "طبيعة",
        "difficulty": 1
    },
    {
        "word": "بحر",
        "definition": "مسطح مائي كبير مالح",
        "category": "طبيعة",
        "difficulty": 1
    },
    {
        "word": "جبل", 
        "definition": "ارتفاع عالي من الأرض والصخر",
        "category": "طبيعة",
        "difficulty": 1
    },
    {
        "word": "نهر",
        "definition": "مجرى ماء عذب يتدفق من منبع إلى مصب",
        "category": "طبيعة",
        "difficulty": 1
    },
    {
        "word": "سيارة",
        "definition": "مركبة بأربع عجلات تعمل بالمحرك",
        "category": "نقل",
        "difficulty": 1
    },
    {
        "word": "طائرة",
        "definition": "مركبة تطير في السماء بالأجنحة",
        "category": "نقل",
        "difficulty": 1
    },
    {
        "word": "حاسوب",
        "definition": "جهاز إلكتروني لمعالجة البيانات والبرمجة",
        "category": "تكنولوجيا",
        "difficulty": 2
    },
    {
        "word": "هاتف",
        "definition": "جهاز للاتصال والتواصل عن بعد",
        "category": "تكنولوجيا",
        "difficulty": 1
    },
    {
        "word": "تلفزيون",
        "definition": "جهاز لعرض الصور والأصوات المنقولة",
        "category": "تكنولوجيا",
        "difficulty": 1
    },
    {
        "word": "ساعة",
        "definition": "أداة لقياس الوقت وعرض الساعات والدقائق",
        "category": "أدوات",
        "difficulty": 1
    },
    {
        "word": "مفتاح",
        "definition": "أداة لفتح وإغلاق الأقفال",
        "category": "أدوات", 
        "difficulty": 1
    },
    {
        "word": "مقص",
        "definition": "أداة ذات شفرتين لقطع الورق والقماش",
        "category": "أدوات",
        "difficulty": 1
    },
    {
        "word": "طبيب",
        "definition": "شخص متخصص في علاج المرضى",
        "category": "مهن",
        "difficulty": 1
    },
    {
        "word": "معلم",
        "definition": "شخص يقوم بتعليم الطلاب في المدرسة",
        "category": "مهن",
        "difficulty": 1
    },
    {
        "word": "مهندس",
        "definition": "شخص متخصص في تصميم وبناء المشاريع",
        "category": "مهن",
        "difficulty": 2
    },
    {
        "word": "طباخ",
        "definition": "شخص يحضر الطعام والوجبات",
        "category": "مهن",
        "difficulty": 1
    },
    {
        "word": "رياضة",
        "definition": "نشاط بدني لتقوية الجسم والمتعة",
        "category": "رياضة",
        "difficulty": 1
    },
    {
        "word": "كتاب",
        "definition": "مجموعة من الصفحات المطبوعة والمجلدة",
        "category": "ثقافة",
        "difficulty": 1
    },
    {
        "word": "قصر",
        "definition": "بناء كبير وفاخر يسكنه الملوك والأثرياء",
        "category": "مباني",
        "difficulty": 2
    },
    {
        "word": "مسجد",
        "definition": "مكان العبادة للمسلمين",
        "category": "دين",
        "difficulty": 1
    },
    {
        "word": "كنيسة",
        "definition": "مكان العبادة للمسيحيين",
        "category": "دين",
        "difficulty": 1
    },
    {
        "word": "ثلاجة",
        "definition": "جهاز كهربائي لحفظ الطعام بارداً",
        "category": "أجهزة",
        "difficulty": 1
    },
    {
        "word": "فرن",
        "definition": "جهاز للطبخ والخبز بالحرارة العالية",
        "category": "أجهزة",
        "difficulty": 1
    },
    {
        "word": "غسالة",
        "definition": "جهاز لغسل الملابس والأقمشة",
        "category": "أجهزة",
        "difficulty": 1
    }
]

class WordGame:
    """فئة لعبة الكلمة"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.current_word = None
        self.attempts = []  # قائمة المحاولات
        self.max_attempts = 30  # الحد الأقصى لجميع المحاولات
        self.max_user_attempts = 3  # محاولات لكل لاعب
        self.game_started = True
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.prize_pool = 30000  # جائزة ثابتة
        self.hint_used = False
        self.start_time = time.time()
        self.game_duration = 60  # مدة اللعبة 60 ثانية
        
        # اختيار كلمة عشوائية
        self.select_random_word()
    
    def select_random_word(self):
        """اختيار كلمة عشوائية من قاعدة البيانات"""
        self.current_word = random.choice(WORD_DATABASE)
    
    def get_hint(self) -> str:
        """الحصول على تلميح للكلمة"""
        if self.hint_used:
            return "❌ تم استخدام التلميح بالفعل!"
        
        self.hint_used = True
        word = self.current_word["word"]
        
        # إخفاء نصف الأحرف
        hint = ""
        for i, char in enumerate(word):
            if i == 0 or i == len(word) - 1 or i % 2 == 0:
                hint += char
            else:
                hint += "_"
        
        return f"💡 **تلميح:** {hint}"
    
    def check_guess(self, user_id: int, user_name: str, guess: str) -> str:
        """فحص التخمين"""
        guess = guess.strip()
        
        # حساب عدد محاولات المستخدم
        user_attempts = len([a for a in self.attempts if a['user_id'] == user_id])
        max_user_attempts = 3  # 3 محاولات لكل لاعب
        
        # فحص إذا كان المستخدم استنفد محاولاته
        if user_attempts >= max_user_attempts:
            return "❌ لقد استنفدت محاولاتك الـ3!"
        
        # تسجيل المحاولة
        if guess.lower() == self.current_word["word"].lower():
            # إجابة صحيحة!
            result = "🎯 صحيح! أحسنت!"
            self.winner = {"user_id": user_id, "name": user_name, "guess": guess}
            self.game_ended = True
        else:
            result = "❌ خطأ! حاول مرة أخرى"
        
        self.attempts.append({
            'user_id': user_id,
            'name': user_name,
            'guess': guess,
            'result': result,
            'timestamp': time.time()
        })
        
        # فحص انتهاء المحاولات أو انتهاء الوقت
        elapsed_time = time.time() - self.start_time
        if (len(self.attempts) >= self.max_attempts and not self.winner) or elapsed_time >= self.game_duration:
            self.game_ended = True
        
        return result
    
    def get_game_status(self) -> str:
        """الحصول على حالة اللعبة"""
        elapsed_time = int(time.time() - self.start_time)
        remaining_time = max(0, self.game_duration - elapsed_time)
        
        status_text = (
            f"💭 **لعبة الكلمة**\n\n"
            f"📝 **التعريف:** {self.current_word['definition']}\n"
            f"📚 **الفئة:** {self.current_word['category']}\n"
            f"👤 **منشئ اللعبة:** {self.creator_name}\n"
            f"💰 **الجائزة:** {format_number(self.prize_pool)}$\n"
            f"📊 **المحاولات:** {len(self.attempts)}/{self.max_attempts}\n"
            f"⏱️ **الوقت المتبقي:** {remaining_time} ثانية\n"
            f"🎯 **محاولات لكل لاعب:** {self.max_user_attempts}\n\n"
        )
        
        if self.winner:
            status_text += (
                f"🏆 **الفائز:** {self.winner['name']}\n"
                f"✅ **الإجابة:** {self.current_word['word']}\n"
                f"🎉 **تهانينا للفائز!**"
            )
        elif self.game_ended:
            status_text += (
                f"⏰ **انتهت اللعبة!**\n"
                f"✅ **الكلمة كانت:** {self.current_word['word']}\n"
                f"😔 **لم يتمكن أحد من التخمين**"
            )
        else:
            status_text += "🎯 **اكتب تخمينك للكلمة في الدردشة!**"
            
            # عرض آخر المحاولات
            if self.attempts:
                status_text += "\n\n📋 **آخر المحاولات:**\n"
                for attempt in self.attempts[-3:]:  # آخر 3 محاولات
                    status_text += f"• {attempt['name']}: {attempt['guess']} {attempt['result']}\n"
        
        return status_text
    
    def get_game_keyboard(self):
        """إنشاء لوحة مفاتيح اللعبة"""
        keyboard = []
        
        if not self.game_ended:
            # صف الأزرار الأول: تلميح وحالة
            row1 = []
            if not self.hint_used:
                row1.append(InlineKeyboardButton(text="💡 تلميح", callback_data=f"word_hint_{self.group_id}"))
            row1.append(InlineKeyboardButton(text="📊 الحالة", callback_data=f"word_status_{self.group_id}"))
            keyboard.append(row1)
            
            # صف الأزرار الثاني: إلغاء
            keyboard.append([
                InlineKeyboardButton(text="❌ إلغاء اللعبة", callback_data=f"word_cancel_{self.group_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(text="📊 النتيجة النهائية", callback_data=f"word_status_{self.group_id}")
            ])
            keyboard.append([
                InlineKeyboardButton(text="🆕 لعبة جديدة", callback_data=f"start_game_الكلمة")
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def start_word_game(message: Message):
    """بدء لعبة الكلمة الجديدة"""
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
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_WORD_GAMES and not ACTIVE_WORD_GAMES[group_id].game_ended:
            await message.reply(
                "⚠️ **يوجد لعبة كلمة نشطة حالياً!**\n\n"
                "🎯 انتظر انتهاء اللعبة الحالية أو شارك في الحل"
            )
            return
        
        # إنشاء لعبة جديدة
        game = WordGame(group_id, creator_id, creator_name)
        ACTIVE_WORD_GAMES[group_id] = game
        
        # رسالة بدء اللعبة
        game_text = (
            f"💭 **لعبة الكلمة بدأت!**\n\n"
            f"🎯 **المهمة:** خمن الكلمة من التعريف\n"
            f"📝 **التعريف:** {game.current_word['definition']}\n"
            f"📚 **الفئة:** {game.current_word['category']}\n\n"
            f"👤 **منشئ اللعبة:** {creator_name}\n"
            f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
            f"⏱️ **المدة:** {game.game_duration} ثانية\n"
            f"🎯 **محاولات لكل لاعب:** {game.max_user_attempts}\n\n"
            f"🚀 **اكتب تخمينك في الدردشة لتفوز بالجائزة!**"
        )
        
        await message.reply(game_text, reply_markup=game.get_game_keyboard())
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة الكلمة: {e}")
        await message.reply("❌ حدث خطأ في بدء لعبة الكلمة")

async def handle_word_guess(message: Message):
    """معالجة تخمين الكلمة"""
    try:
        group_id = message.chat.id
        
        # التحقق من وجود لعبة نشطة
        if group_id not in ACTIVE_WORD_GAMES:
            return  # لا توجد لعبة نشطة
        
        game = ACTIVE_WORD_GAMES[group_id]
        
        # التحقق من أن اللعبة لم تنته
        if game.game_ended:
            return  # اللعبة انتهت
        
        user_id = message.from_user.id
        user_name = message.from_user.first_name or "اللاعب"
        user_username = message.from_user.username or ""
        guess = message.text.strip()
        
        # فحص انتهاء الوقت أولاً
        elapsed_time = time.time() - game.start_time
        if elapsed_time >= game.game_duration:
            game.game_ended = True
            return  # اللعبة انتهت بانتهاء الوقت
        
        # فحص التخمين
        result = game.check_guess(user_id, user_name, guess)
        
        if "صحيح" in result:
            # الفائز وجد!
            user_data = await get_or_create_user(user_id, user_username, user_name)
            creator_data = await get_or_create_user(game.creator_id, "", game.creator_name)
            
            if user_data:
                # إضافة الجائزة والخبرة للفائز
                new_balance = user_data['balance'] + game.prize_pool
                new_xp = user_data.get('xp', 0) + 250
                
                await update_user_balance(user_id, new_balance)
                
                # تحديث XP للفائز
                import aiosqlite
                from config.database import DATABASE_URL
                async with aiosqlite.connect(DATABASE_URL) as conn:
                    await conn.execute(
                        "UPDATE users SET xp = ? WHERE user_id = ?",
                        (new_xp, user_id)
                    )
                    await conn.commit()
                
                await add_transaction(user_id, "فوز في لعبة الكلمة", game.prize_pool, "word_game_win")
                
                # إعطاء 50 XP لمنشئ اللعبة
                if creator_data and game.creator_id != user_id:
                    creator_new_xp = creator_data.get('xp', 0) + 50
                    async with aiosqlite.connect(DATABASE_URL) as conn:
                        await conn.execute(
                            "UPDATE users SET xp = ? WHERE user_id = ?",
                            (creator_new_xp, game.creator_id)
                        )
                        await conn.commit()
                
                winner_text = (
                    f"🏆 **تهانينا {user_name}!**\n\n"
                    f"✅ **الإجابة الصحيحة:** {game.current_word['word']}\n"
                    f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
                    f"✨ **الخبرة:** +250 XP\n"
                    f"📊 **رصيدك الجديد:** {format_number(new_balance)}$\n"
                    f"⏱️ **الوقت:** {int(time.time() - game.start_time)} ثانية\n\n"
                )
                
                if game.creator_id != user_id:
                    winner_text += f"🎁 **منشئ اللعبة {game.creator_name} حصل على +50 XP**\n\n"
                
                winner_text += f"🎉 **أحسنت! لعبة ممتازة**"
                
                await message.reply(winner_text, reply_markup=game.get_game_keyboard())
            else:
                await message.reply("❌ خطأ في معالجة الجائزة")
                
        elif "خطأ" in result:
            await message.reply(f"❌ **{user_name}:** {guess}\n🚫 إجابة خاطئة! حاول مرة أخرى")
            
        elif "استنفدت محاولاتك" in result:
            return  # لا نرد على من استنفد محاولاته
        
        # التحقق من انتهاء اللعبة (فقط مرة واحدة عند الانتهاء الفعلي)
        if game.game_ended and not game.winner:
            # التحقق أن اللعبة انتهت للتو وليس منذ قبل
            elapsed_time = time.time() - game.start_time
            if elapsed_time >= game.game_duration or len(game.attempts) >= game.max_attempts:
                if elapsed_time >= game.game_duration:
                    end_reason = "⏰ انتهى الوقت!"
                else:
                    end_reason = "📊 انتهت جميع المحاولات!"
                
                end_text = (
                    f"🔚 **انتهت لعبة الكلمة!**\n\n"
                    f"{end_reason}\n"
                    f"✅ **الإجابة كانت:** {game.current_word['word']}\n"
                    f"😔 **لم يتمكن أحد من التخمين**\n"
                    f"📊 **عدد المحاولات:** {len(game.attempts)}\n\n"
                    f"🎮 جرب لعبة جديدة!"
                )
                await message.reply(end_text, reply_markup=game.get_game_keyboard())
        
    except Exception as e:
        logging.error(f"خطأ في معالجة تخمين الكلمة: {e}")

async def handle_word_hint_callback(callback_query):
    """معالجة طلب التلميح"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_WORD_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_WORD_GAMES[group_id]
        
        if game.game_ended:
            await callback_query.answer("❌ اللعبة انتهت", show_alert=True)
            return
        
        hint = game.get_hint()
        await callback_query.answer(hint, show_alert=True)
        
        # تحديث الرسالة
        updated_status = game.get_game_status()
        await callback_query.message.edit_text(updated_status, reply_markup=game.get_game_keyboard())
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التلميح: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

async def handle_word_status_callback(callback_query):
    """معالجة طلب حالة اللعبة"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_WORD_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_WORD_GAMES[group_id]
        
        # فحص انتهاء الوقت
        elapsed_time = time.time() - game.start_time
        if elapsed_time >= game.game_duration and not game.game_ended:
            game.game_ended = True
        
        status = game.get_game_status()
        
        await callback_query.message.edit_text(status, reply_markup=game.get_game_keyboard())
        await callback_query.answer("🔄 تم تحديث الحالة")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة حالة اللعبة: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

async def handle_word_cancel_callback(callback_query):
    """معالجة إلغاء اللعبة"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_WORD_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_WORD_GAMES[group_id]
        
        # التحقق من أن الملغي هو منشئ اللعبة أو مشرف
        user_id = callback_query.from_user.id
        
        if user_id != game.creator_id:
            # فحص إذا كان المستخدم مشرف في المجموعة
            try:
                member = await callback_query.bot.get_chat_member(group_id, user_id)
                if member.status not in ['administrator', 'creator']:
                    await callback_query.answer("❌ يمكن فقط لمنشئ اللعبة أو المشرفين إلغاؤها", show_alert=True)
                    return
            except:
                await callback_query.answer("❌ يمكن فقط لمنشئ اللعبة أو المشرفين إلغاؤها", show_alert=True)
                return
        
        # إنهاء اللعبة
        game.game_ended = True
        
        cancel_text = (
            f"❌ **تم إلغاء لعبة الكلمة**\n\n"
            f"✅ **الإجابة كانت:** {game.current_word['word']}\n"
            f"👤 **ألغاها:** {callback_query.from_user.first_name}\n"
            f"📊 **المحاولات:** {len(game.attempts)}\n\n"
            f"🎮 يمكنك بدء لعبة جديدة!"
        )
        
        await callback_query.message.edit_text(cancel_text, reply_markup=game.get_game_keyboard())
        await callback_query.answer("❌ تم إلغاء اللعبة")
        
    except Exception as e:
        logging.error(f"خطأ في إلغاء اللعبة: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

# تنظيف الألعاب القديمة (تشغل كل 30 دقيقة)
async def cleanup_old_games():
    """تنظيف الألعاب القديمة"""
    try:
        current_time = time.time()
        games_to_remove = []
        
        for group_id, game in ACTIVE_WORD_GAMES.items():
            # إذا مرت 30 دقيقة على اللعبة
            if current_time - game.created_at > 1800:  # 30 دقيقة
                games_to_remove.append(group_id)
        
        for group_id in games_to_remove:
            del ACTIVE_WORD_GAMES[group_id]
        
        if games_to_remove:
            logging.info(f"تم تنظيف {len(games_to_remove)} لعبة كلمة قديمة")
            
    except Exception as e:
        logging.error(f"خطأ في تنظيف الألعاب القديمة: {e}")
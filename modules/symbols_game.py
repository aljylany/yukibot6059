"""
لعبة الرموز - حل الرموز والألغاز المشفرة
Symbols Game Module
"""

import logging
import time
import random
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.operations import get_or_create_user, update_user_balance, add_transaction

# الألعاب النشطة - مؤقت في الذاكرة
ACTIVE_SYMBOLS_GAMES = {}

def format_number(num):
    """تنسيق الأرقام مع فواصل الآلاف"""
    return f"{num:,}".replace(",", "٬")

# قاموس الرموز والألغاز
SYMBOLS_PUZZLES = [
    {
        "puzzle": "أ ب ج د = 1 2 3 4، إذن: ه و ز = ؟",
        "answer": "567",
        "hint": "استمر في التسلسل الرقمي",
        "category": "أرقام"
    },
    {
        "puzzle": "🌞 + 🌙 = يوم، إذن: ⭐ + ☁️ = ؟",
        "answer": "ليل",
        "hint": "فكر في أضداد اليوم",
        "category": "رموز"
    },
    {
        "puzzle": "2 × 2 = 4، 3 × 3 = 9، إذن: 5 × 5 = ؟",
        "answer": "25",
        "hint": "مربع العدد",
        "category": "حساب"
    },
    {
        "puzzle": "أحمد = A، محمد = M، إذن: سارة = ؟",
        "answer": "S",
        "hint": "الحرف الأول من الاسم بالإنجليزية",
        "category": "أحرف"
    },
    {
        "puzzle": "🔴 + 🔵 = بنفسجي، إذن: 🟡 + 🔴 = ؟",
        "answer": "برتقالي",
        "hint": "خلط الألوان الأساسية",
        "category": "ألوان"
    },
    {
        "puzzle": "1234 ← 4321، إذن: 5678 ← ؟",
        "answer": "8765",
        "hint": "اقلب ترتيب الأرقام",
        "category": "انعكاس"
    },
    {
        "puzzle": "CAT = قطة، DOG = كلب، إذن: BIRD = ؟",
        "answer": "طير",
        "hint": "ترجمة الكلمة للعربية",
        "category": "ترجمة"
    },
    {
        "puzzle": "🏠 → منزل، 🚗 → سيارة، إذن: ✈️ → ؟",
        "answer": "طائرة",
        "hint": "ما يدل عليه الرمز",
        "category": "رموز"
    },
    {
        "puzzle": "1+1=2، 2+2=4، 3+3=6، إذن: 4+4=؟",
        "answer": "8",
        "hint": "ضعف العدد",
        "category": "حساب"
    },
    {
        "puzzle": "ABC → 123، DEF → 456، إذن: GHI → ؟",
        "answer": "789",
        "hint": "ترقيم الأحرف تتابعياً",
        "category": "أحرف"
    },
    {
        "puzzle": "شمس ← س م ش، قمر ← ؟",
        "answer": "ر م ق",
        "hint": "اقلب ترتيب الأحرف",
        "category": "كلمات"
    },
    {
        "puzzle": "🌱 → 🌿 → 🌳، إذن: 🥚 → 🐣 → ؟",
        "answer": "🐔",
        "hint": "مراحل نمو الكتكوت",
        "category": "تطور"
    },
    {
        "puzzle": "12 ÷ 3 = 4، 15 ÷ 3 = 5، إذن: 18 ÷ 3 = ؟",
        "answer": "6",
        "hint": "القسمة على 3",
        "category": "حساب"
    },
    {
        "puzzle": "كتاب = 4 حروف، قلم = 3 حروف، إذن: مدرسة = ؟",
        "answer": "5",
        "hint": "عدد حروف الكلمة",
        "category": "عد"
    },
    {
        "puzzle": "🔥 + 🧊 = ماء، إذن: ☀️ + 🌧️ = ؟",
        "answer": "قوس قزح",
        "hint": "ظاهرة جوية ملونة",
        "category": "طبيعة"
    },
    {
        "puzzle": "A=1, B=2, C=3، إذن: D=؟",
        "answer": "4",
        "hint": "ترتيب الأحرف في الأبجدية",
        "category": "أحرف"
    },
    {
        "puzzle": "🎵 + 🎤 = غناء، إذن: 📚 + ✏️ = ؟",
        "answer": "دراسة",
        "hint": "نشاط يجمع الكتاب والقلم",
        "category": "أنشطة"
    },
    {
        "puzzle": "100 - 25 = 75، 75 - 25 = 50، إذن: 50 - 25 = ؟",
        "answer": "25",
        "hint": "طرح 25 في كل مرة",
        "category": "حساب"
    },
    {
        "puzzle": "مفتاح → باب، مطرقة → ؟",
        "answer": "مسمار",
        "hint": "أداة وما تستخدم معه",
        "category": "أدوات"
    },
    {
        "puzzle": "🍎 × 2 = 🍎🍎، 🍌 × 3 = 🍌🍌🍌، إذن: 🍊 × 4 = ؟",
        "answer": "🍊🍊🍊🍊",
        "hint": "تكرار الرمز حسب العدد",
        "category": "تكرار"
    }
]

class SymbolsGame:
    """كلاس لعبة الرموز"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.current_puzzle = None
        self.attempts = []  # قائمة المحاولات
        self.max_attempts = 30  # الحد الأقصى لجميع المحاولات
        self.max_user_attempts = 3  # محاولات لكل لاعب
        self.game_started = True
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.prize_pool = 25000  # جائزة ثابتة
        self.hint_used = False
        self.start_time = time.time()
        self.game_duration = 60  # مدة اللعبة 60 ثانية
        
        # اختيار لغز عشوائي
        self.select_random_puzzle()
    
    def select_random_puzzle(self):
        """اختيار لغز عشوائي"""
        self.current_puzzle = random.choice(SYMBOLS_PUZZLES)
    
    def get_hint(self) -> str:
        """الحصول على تلميح"""
        if self.hint_used:
            return "💡 **تم استخدام التلميح مسبقاً!**"
        
        self.hint_used = True
        return f"💡 **تلميح:** {self.current_puzzle['hint']}"
    
    def check_guess(self, user_id: int, user_name: str, guess: str) -> str:
        """فحص التخمين"""
        guess = guess.strip()
        
        # حساب عدد محاولات المستخدم
        user_attempts = len([a for a in self.attempts if a['user_id'] == user_id])
        
        # فحص إذا كان المستخدم استنفد محاولاته
        if user_attempts >= self.max_user_attempts:
            return "❌ لقد استنفدت محاولاتك الـ3!"
        
        # تسجيل المحاولة
        if guess.lower() == self.current_puzzle["answer"].lower():
            # إجابة صحيحة!
            self.winner = {
                'user_id': user_id,
                'name': user_name,
                'guess': guess,
                'attempt_number': len(self.attempts) + 1
            }
            self.game_ended = True
            result = "✅ إجابة صحيحة! تهانينا!"
        else:
            result = "❌ إجابة خاطئة"
        
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
            f"🔤 **لعبة الرموز**\n\n"
            f"🧩 **اللغز:** {self.current_puzzle['puzzle']}\n"
            f"📚 **الفئة:** {self.current_puzzle['category']}\n"
            f"👤 **منشئ اللعبة:** {self.creator_name}\n"
            f"💰 **الجائزة:** {format_number(self.prize_pool)}$\n"
            f"📊 **المحاولات:** {len(self.attempts)}/{self.max_attempts}\n"
            f"⏱️ **الوقت المتبقي:** {remaining_time} ثانية\n"
            f"🎯 **محاولات لكل لاعب:** {self.max_user_attempts}\n\n"
        )
        
        if self.winner:
            status_text += (
                f"🏆 **الفائز:** {self.winner['name']}\n"
                f"✅ **الحل:** {self.current_puzzle['answer']}\n"
                f"🎉 **مبروك للفائز!**"
            )
        elif self.attempts:
            status_text += f"📝 **آخر المحاولات:**\n"
            for attempt in self.attempts[-5:]:  # آخر 5 محاولات
                status_text += f"• {attempt['name']}: {attempt['guess']} {attempt['result']}\n"
        
        return status_text
    
    def get_game_keyboard(self):
        """إنشاء لوحة مفاتيح اللعبة"""
        keyboard = []
        
        if not self.game_ended:
            # صف الأزرار الأول: تلميح وحالة
            row1 = []
            if not self.hint_used:
                row1.append(InlineKeyboardButton(text="💡 تلميح", callback_data=f"symbols_hint_{self.group_id}"))
            row1.append(InlineKeyboardButton(text="📊 الحالة", callback_data=f"symbols_status_{self.group_id}"))
            keyboard.append(row1)
            
            # صف الأزرار الثاني: إلغاء
            keyboard.append([
                InlineKeyboardButton(text="❌ إلغاء اللعبة", callback_data=f"symbols_cancel_{self.group_id}")
            ])
        else:
            keyboard.append([
                InlineKeyboardButton(text="📊 النتيجة النهائية", callback_data=f"symbols_status_{self.group_id}")
            ])
            keyboard.append([
                InlineKeyboardButton(text="🆕 لعبة جديدة", callback_data=f"start_game_الرموز")
            ])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)

async def start_symbols_game(message: Message):
    """بدء لعبة الرموز الجديدة"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "اللاعب"
        
        # التحقق من أن الرسالة من مجموعة
        if message.chat.type not in ['group', 'supergroup']:
            # إرسال رسالة باستخدام bot.send_message إذا لم تكن رسالة عادية
            if hasattr(message, 'reply'):
                await message.reply(
                    "⚠️ **لعبة الرموز تعمل فقط في المجموعات!**\n\n"
                    "➕ أضف البوت لمجموعتك واستمتع باللعب مع الأصدقاء"
                )
            return
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_SYMBOLS_GAMES and not ACTIVE_SYMBOLS_GAMES[group_id].game_ended:
            if hasattr(message, 'reply'):
                await message.reply(
                    "⚠️ **يوجد لعبة رموز نشطة حالياً!**\n\n"
                    "🎯 انتظر انتهاء اللعبة الحالية أو شارك في الحل"
                )
            return
        
        # إنشاء لعبة جديدة
        game = SymbolsGame(group_id, creator_id, creator_name)
        ACTIVE_SYMBOLS_GAMES[group_id] = game
        
        # إرسال رسالة بدء اللعبة
        game_text = (
            f"🔤 **لعبة الرموز بدأت!**\n\n"
            f"🧩 **اللغز:** {game.current_puzzle['puzzle']}\n"
            f"📚 **الفئة:** {game.current_puzzle['category']}\n\n"
            f"👤 **منشئ اللعبة:** {creator_name}\n"
            f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
            f"⏱️ **المدة:** {game.game_duration} ثانية\n"
            f"🎯 **محاولات لكل لاعب:** {game.max_user_attempts}\n\n"
            f"🚀 **اكتب حلك في الدردشة لتفوز بالجائزة!**"
        )
        
        # إرسال الرسالة باستخدام الطريقة المناسبة
        if hasattr(message, 'reply'):
            await message.reply(game_text, reply_markup=game.get_game_keyboard())
        else:
            # للرسائل الوهمية من الأزرار
            from aiogram import Bot
            bot = Bot.get_current()
            await bot.send_message(
                chat_id=message.chat.id,
                text=game_text,
                reply_markup=game.get_game_keyboard()
            )
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة الرموز: {e}")
        if hasattr(message, 'reply'):
            await message.reply("❌ حدث خطأ في بدء لعبة الرموز")

async def handle_symbols_guess(message: Message):
    """معالجة تخمين الرموز"""
    try:
        group_id = message.chat.id
        
        # التحقق من وجود لعبة نشطة
        if group_id not in ACTIVE_SYMBOLS_GAMES:
            return  # لا توجد لعبة نشطة
        
        game = ACTIVE_SYMBOLS_GAMES[group_id]
        
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
                
                await add_transaction(user_id, "فوز في لعبة الرموز", game.prize_pool, "symbols_game_win")
                
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
                    f"✅ **الحل الصحيح:** {game.current_puzzle['answer']}\n"
                    f"💰 **الجائزة:** {format_number(game.prize_pool)}$\n"
                    f"✨ **الخبرة:** +250 XP\n"
                    f"📊 **رصيدك الجديد:** {format_number(new_balance)}$\n"
                    f"⏱️ **الوقت:** {int(time.time() - game.start_time)} ثانية\n\n"
                )
                
                if game.creator_id != user_id:
                    winner_text += f"🎁 **منشئ اللعبة {game.creator_name} حصل على +50 XP**\n\n"
                
                winner_text += f"🎉 **أحسنت! لغز ممتاز**"
                
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
                    f"🔚 **انتهت لعبة الرموز!**\n\n"
                    f"{end_reason}\n"
                    f"✅ **الحل كان:** {game.current_puzzle['answer']}\n"
                    f"😔 **لم يتمكن أحد من الحل**\n"
                    f"📊 **عدد المحاولات:** {len(game.attempts)}\n\n"
                    f"🎮 جرب لعبة جديدة!"
                )
                await message.reply(end_text, reply_markup=game.get_game_keyboard())
        
    except Exception as e:
        logging.error(f"خطأ في معالجة تخمين الرموز: {e}")

async def handle_symbols_hint_callback(callback_query):
    """معالجة طلب التلميح"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_SYMBOLS_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_SYMBOLS_GAMES[group_id]
        
        if game.game_ended:
            await callback_query.answer("⏰ اللعبة انتهت", show_alert=True)
            return
        
        hint = game.get_hint()
        
        # إرسال التلميح كرسالة جديدة
        await callback_query.message.reply(hint)
        
        # تحديث لوحة المفاتيح
        await callback_query.message.edit_reply_markup(reply_markup=game.get_game_keyboard())
        await callback_query.answer("💡 تم إرسال التلميح")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التلميح: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)

async def handle_symbols_status_callback(callback_query):
    """معالجة طلب حالة اللعبة"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_SYMBOLS_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_SYMBOLS_GAMES[group_id]
        
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

async def handle_symbols_cancel_callback(callback_query):
    """معالجة إلغاء اللعبة"""
    try:
        group_id = int(callback_query.data.split('_')[-1])
        
        if group_id not in ACTIVE_SYMBOLS_GAMES:
            await callback_query.answer("❌ لا توجد لعبة نشطة", show_alert=True)
            return
        
        game = ACTIVE_SYMBOLS_GAMES[group_id]
        
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
            f"❌ **تم إلغاء لعبة الرموز**\n\n"
            f"✅ **الحل كان:** {game.current_puzzle['answer']}\n"
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
async def cleanup_old_symbols_games():
    """تنظيف الألعاب القديمة"""
    try:
        current_time = time.time()
        old_games = []
        
        for group_id, game in ACTIVE_SYMBOLS_GAMES.items():
            # حذف الألعاب الأقدم من ساعة أو المنتهية منذ 10 دقائق
            if (current_time - game.created_at > 3600) or (game.game_ended and current_time - game.created_at > 600):
                old_games.append(group_id)
        
        for group_id in old_games:
            del ACTIVE_SYMBOLS_GAMES[group_id]
            
        if old_games:
            logging.info(f"تم حذف {len(old_games)} لعبة رموز قديمة")
            
    except Exception as e:
        logging.error(f"خطأ في تنظيف ألعاب الرموز: {e}")
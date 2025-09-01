"""
قائمة الألعاب المتاحة في البوت
Games List Module
"""

import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

# متغير لتتبع الفهرس الحالي للعبة لكل مستخدم
user_game_index = {}

# قائمة الألعاب المتاحة
AVAILABLE_GAMES = {
    "xo": {
        "name": "🎯 لعبة اكس اوه",
        "description": "لعبة كلاسيكية للاعبين، الهدف ترتيب 3 رموز في خط مستقيم",
        "commands": ["اكس اوه", "xo", "اكس او"],
        "players": "2 لاعبين",
        "duration": "2-5 دقائق",
        "status": "متاحة"
    },
    "royal": {
        "name": "👑 لعبة الرويال",
        "description": "معركة البقاء الملكية، آخر لاعب يبقى هو الفائز",
        "commands": ["رويال", "royal", "لعبة الحظ"],
        "players": "5-20 لاعب",
        "duration": "10-15 دقيقة", 
        "status": "متاحة"
    },
    "battle_arena": {
        "name": "⚔️ ساحة الموت الأخيرة",
        "description": "معركة البقاء المثيرة، كل دقيقة تنقص مساحة الساحة والناجي الوحيد يفوز",
        "commands": ["ساحة الموت", "battle", "معركة"],
        "players": "8-15 لاعب", 
        "duration": "8-12 دقيقة",
        "status": "متاحة"
    },
    "luck_wheel": {
        "name": "🎲 عجلة الحظ",
        "description": "أدر العجلة واكسب جوائز فورية كل 30 ثانية",
        "commands": ["عجلة الحظ", "عجلة", "wheel"],
        "players": "1 لاعب",
        "duration": "30 ثانية",
        "status": "متاحة"
    },
    "number_guess": {
        "name": "🔢 خمن الرقم", 
        "description": "خمن الرقم السري من 1-100 واكسب الجائزة",
        "commands": ["خمن الرقم", "تخمين", "رقم"],
        "players": "مفتوح للجميع",
        "duration": "3 دقائق",
        "status": "متاحة"
    },
    "quick_quiz": {
        "name": "🧠 سؤال وجواب سريع",
        "description": "أسئلة ثقافة عامة بسيطة مع 3 اختيارات لكل سؤال",
        "commands": ["سؤال وجواب", "مسابقة", "quiz"],
        "players": "مفتوح للجميع", 
        "duration": "3-5 دقائق",
        "status": "متاحة"
    },
    "word": {
        "name": "💭 لعبة الكلمة",
        "description": "خمن الكلمة الصحيحة من التعريف المعطى",
        "commands": ["الكلمة", "كلمة", "word"],
        "players": "مفتوح للجميع",
        "duration": "1-3 دقائق",
        "status": "متاحة"
    },
    "symbols": {
        "name": "🔤 لعبة الرموز",
        "description": "حل الرموز والألغاز المشفرة بالأرقام والحروف",
        "commands": ["الرموز", "رموز", "symbols"],
        "players": "مفتوح للجميع",
        "duration": "1-2 دقيقة",
        "status": "متاحة"
    },
    "letter_shuffle": {
        "name": "🎯 لعبة خلط الحروف",
        "description": "رتب الحروف المختلطة لتكوين كلمة صحيحة وافوز بالجائزة",
        "commands": ["خلط الحروف", "حروف مختلطة", "كلمة مخفية"],
        "players": "مفتوح للجميع",
        "duration": "1 دقيقة",
        "status": "متاحة"
    },
    "rock_paper_scissors": {
        "name": "🎮 حجر ورقة مقص",
        "description": "لعبة سريعة ضد يوكي - 3 جولات",
        "commands": ["حجر ورقة مقص", "حجر ورقة", "rps"],
        "players": "لاعب واحد ضد يوكي",
        "duration": "دقيقة واحدة",
        "status": "متاحة"
    },
    "true_false": {
        "name": "🤔 صدق أم كذب",
        "description": "لعبة أسئلة ثقافية - ضد يوكي أو لاعب آخر",
        "commands": ["صدق أم كذب", "صدق كذب", "true false"],
        "players": "لاعب واحد ضد يوكي أو لاعبين",
        "duration": "3-5 دقائق",
        "status": "متاحة"
    },
    "math_challenge": {
        "name": "🧮 التحدي الرياضي",
        "description": "حل المعادلات البسيطة - ضد يوكي أو لاعب آخر",
        "commands": ["تحدي رياضي", "رياضيات", "math challenge"],
        "players": "لاعب واحد ضد يوكي أو لاعبين",
        "duration": "3-5 دقائق",
        "status": "متاحة"
    },
    "guild_game": {
        "name": "🏰 لعبة النقابة",
        "description": "لعبة RPG شاملة - انضم لنقابة، قم بمهام، اشتري أسلحة، وارتقي بمستواك!",
        "commands": ["نقابة", "لعبة النقابة", "guild"],
        "players": "مفتوح للجميع",
        "duration": "لعبة مستمرة",
        "status": "متاحة"
    }
}

async def show_games_list(message: Message):
    """عرض قائمة الألعاب المتاحة بشكل أفقي مع التنقل"""
    try:
        # التحقق من وجود from_user
        if not message.from_user:
            await message.reply("❌ حدث خطأ في التعرف على المستخدم")
            return
            
        user_id = message.from_user.id
        
        # تهيئة الفهرس للمستخدم إذا لم يكن موجوداً
        if user_id not in user_game_index:
            user_game_index[user_id] = 0
        
        await show_game_carousel(message, user_id, user_game_index[user_id])
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الألعاب: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الألعاب")

async def show_game_carousel(message_or_callback, user_id: int, game_index: int):
    """عرض لعبة واحدة مع أزرار التنقل"""
    try:
        # الحصول على الألعاب المتاحة
        available_games = [
            (game_key, game_info) 
            for game_key, game_info in AVAILABLE_GAMES.items() 
            if game_info["status"] == "متاحة"
        ]
        
        if not available_games:
            text = "❌ لا توجد ألعاب متاحة حالياً"
            keyboard = None
        else:
            # التأكد من أن الفهرس ضمن النطاق المسموح
            game_index = max(0, min(game_index, len(available_games) - 1))
            user_game_index[user_id] = game_index
            
            # الحصول على اللعبة الحالية
            game_key, game_info = available_games[game_index]
            
            # إنشاء النص
            text = (
                f"🎮 **قائمة الألعاب المتاحة**\n\n"
                f"✅ **{game_info['name']}**\n\n"
                f"📝 **الوصف:** {game_info['description']}\n"
                f"👥 **اللاعبين:** {game_info['players']}\n"
                f"⏱️ **المدة:** {game_info['duration']}\n"
                f"🎯 **الأوامر:** {', '.join(game_info['commands'])}\n\n"
                f"📊 **اللعبة {game_index + 1} من {len(available_games)}**\n\n"
                f"🚀 **اضغط 'ابدأ اللعبة' للعب الآن!**"
            )
            
            # إنشاء لوحة المفاتيح
            keyboard = []
            
            # الصف الأول: زر بدء اللعبة
            main_command = game_info["commands"][0]
            keyboard.append([
                InlineKeyboardButton(
                    text="🚀 ابدأ اللعبة", 
                    callback_data=f"start_game_{main_command}"
                )
            ])
            
            # الصف الثاني: أزرار التنقل
            nav_row = []
            
            # زر السابق (إذا لم نكن في أول لعبة)
            if game_index > 0:
                nav_row.append(InlineKeyboardButton(
                    text="⬅️ السابق", 
                    callback_data=f"games_nav_prev_{user_id}"
                ))
            
            # زر التالي (إذا لم نكن في آخر لعبة)
            if game_index < len(available_games) - 1:
                nav_row.append(InlineKeyboardButton(
                    text="التالي ➡️", 
                    callback_data=f"games_nav_next_{user_id}"
                ))
            
            if nav_row:
                keyboard.append(nav_row)
            
            # الصف الثالث: زر إغلاق
            keyboard.append([
                InlineKeyboardButton(
                    text="❌ إغلاق القائمة", 
                    callback_data=f"games_close_{user_id}"
                )
            ])
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
        
        # إرسال أو تحديث الرسالة
        if hasattr(message_or_callback, 'message'):  # callback query
            await message_or_callback.message.edit_text(text, reply_markup=reply_markup)
        else:  # رسالة عادية
            await message_or_callback.reply(text, reply_markup=reply_markup)
            
    except Exception as e:
        logging.error(f"خطأ في عرض carousel الألعاب: {e}")
        if hasattr(message_or_callback, 'answer'):
            await message_or_callback.answer("❌ حدث خطأ", show_alert=True)

async def handle_game_start_callback(callback_query, game_command: str):
    """معالجة بدء اللعبة من الأزرار"""
    try:
        # إنشاء رسالة وهمية شاملة للجميع
        import types
        fake_message = types.SimpleNamespace()
        fake_message.chat = callback_query.message.chat
        fake_message.from_user = callback_query.from_user
        fake_message.text = game_command
        
        # إضافة دالة reply للرسالة الوهمية
        async def fake_reply(text, **kwargs):
            return await callback_query.bot.send_message(
                chat_id=callback_query.message.chat.id,
                text=text,
                **kwargs
            )
        fake_message.reply = fake_reply
        
        # محاكاة رسالة جديدة لبدء اللعبة
        if game_command in ["اكس اوه", "xo"]:
            from modules.xo_game import start_xo_game
            await start_xo_game(fake_message)
            await callback_query.answer("🎮 تم بدء لعبة اكس اوه!")
            
        elif game_command in ["رويال", "royal"]:
            from modules.royal_game import start_royal_game  
            await start_royal_game(fake_message)
            await callback_query.answer("👑 تم بدء لعبة الرويال!")
            
        elif game_command in ["الكلمة", "كلمة", "word"]:
            from modules.word_game import start_word_game
            await start_word_game(fake_message)
            await callback_query.answer("💭 تم بدء لعبة الكلمة!")
            
        elif game_command in ["الرموز", "رموز", "symbols"]:
            from modules.symbols_game import start_symbols_game
            await start_symbols_game(fake_message)
            await callback_query.answer("🔤 تم بدء لعبة الرموز!")
            
        elif game_command in ["ساحة الموت", "battle", "معركة"]:
            await callback_query.answer("⚔️ ساحة الموت الأخيرة - قريباً!", show_alert=True)
            
        elif game_command in ["عجلة الحظ", "عجلة", "wheel"]:
            from modules.luck_wheel_game import start_luck_wheel
            await start_luck_wheel(fake_message)
            await callback_query.answer("🎲 تم بدء عجلة الحظ!")
            
        elif game_command in ["خمن الرقم", "تخمين", "رقم"]:
            from modules.number_guess_game import start_number_guess_game
            await start_number_guess_game(fake_message)
            await callback_query.answer("🔢 تم بدء لعبة خمن الرقم!")
            
        elif game_command in ["سؤال وجواب", "مسابقة", "quiz"]:
            from modules.quick_quiz_game import start_quick_quiz_game
            await start_quick_quiz_game(fake_message)
            await callback_query.answer("🧠 تم بدء سؤال وجواب!")
            
        elif game_command in ["خلط الحروف", "حروف مختلطة", "كلمة مخفية"]:
            from modules.letter_shuffle_game import start_letter_shuffle_game
            await start_letter_shuffle_game(fake_message)
            await callback_query.answer("🎯 تم بدء لعبة خلط الحروف!")
            
        elif game_command in ["حجر ورقة مقص", "حجر ورقة", "rps"]:
            from modules.rock_paper_scissors_game import start_rock_paper_scissors_game
            await start_rock_paper_scissors_game(fake_message)
            await callback_query.answer("🎮 تم بدء لعبة حجر ورقة مقص!")
            
        elif game_command in ["صدق أم كذب", "صدق كذب", "true false"]:
            from modules.true_false_game import start_true_false_game
            await start_true_false_game(fake_message, vs_ai=True)
            await callback_query.answer("🤔 تم بدء لعبة صدق أم كذب!")
            
        elif game_command in ["تحدي رياضي", "رياضيات", "math challenge"]:
            from modules.math_challenge_game import start_math_challenge_game
            await start_math_challenge_game(fake_message, vs_ai=True)
            await callback_query.answer("🧮 تم بدء التحدي الرياضي!")
            
        elif game_command in ["نقابة", "لعبة النقابة", "guild"]:
            from modules.guild_game import start_guild_registration
            # إنشاء state فارغ
            state = None
            await start_guild_registration(fake_message, state)
            await callback_query.answer("🏰 مرحباً في لعبة النقابة!")
            
        else:
            await callback_query.answer("❌ هذه اللعبة غير متاحة حالياً", show_alert=True)
            
    except Exception as e:
        logging.error(f"خطأ في بدء اللعبة من الزر: {e}")
        await callback_query.answer("❌ حدث خطأ في بدء اللعبة", show_alert=True)

async def handle_games_navigation_callback(callback_query):
    """معالجة أزرار التنقل في قائمة الألعاب"""
    try:
        data = callback_query.data
        user_id = callback_query.from_user.id
        
        if data.startswith("games_nav_prev_"):
            # الانتقال للعبة السابقة
            if user_id in user_game_index:
                user_game_index[user_id] = max(0, user_game_index[user_id] - 1)
            await show_game_carousel(callback_query, user_id, user_game_index.get(user_id, 0))
            await callback_query.answer("⬅️ اللعبة السابقة")
            
        elif data.startswith("games_nav_next_"):
            # الانتقال للعبة التالية
            available_games = [
                game for game in AVAILABLE_GAMES.values() 
                if game["status"] == "متاحة"
            ]
            max_index = len(available_games) - 1
            
            if user_id in user_game_index:
                user_game_index[user_id] = min(max_index, user_game_index[user_id] + 1)
            await show_game_carousel(callback_query, user_id, user_game_index.get(user_id, 0))
            await callback_query.answer("➡️ اللعبة التالية")
            
        elif data.startswith("games_close_"):
            # إغلاق قائمة الألعاب
            await callback_query.message.delete()
            await callback_query.answer("✅ تم إغلاق قائمة الألعاب")
            
    except Exception as e:
        logging.error(f"خطأ في معالجة تنقل الألعاب: {e}")
        await callback_query.answer("❌ حدث خطأ", show_alert=True)
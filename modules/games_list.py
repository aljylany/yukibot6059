"""
قائمة الألعاب المتاحة في البوت
Games List Module
"""

import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

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
    }
}

async def show_games_list(message: Message):
    """عرض قائمة الألعاب المتاحة"""
    try:
        games_text = "🎮 **قائمة الألعاب المتاحة**\n\n"
        
        for game_key, game_info in AVAILABLE_GAMES.items():
            status_icon = "✅" if game_info["status"] == "متاحة" else "🔜"
            
            games_text += f"{status_icon} **{game_info['name']}**\n"
            games_text += f"📝 {game_info['description']}\n"
            games_text += f"👥 اللاعبين: {game_info['players']}\n"
            games_text += f"⏱️ المدة: {game_info['duration']}\n"
            games_text += f"🎯 الأوامر: {', '.join(game_info['commands'])}\n"
            games_text += f"📊 الحالة: {game_info['status']}\n\n"
        
        games_text += "🔥 **استمتع باللعب وحظ سعيد!**"
        
        # أزرار سريعة للألعاب المتاحة
        keyboard = []
        available_games = [game for game in AVAILABLE_GAMES.values() if game["status"] == "متاحة"]
        
        for i in range(0, len(available_games), 2):
            row = []
            if i < len(available_games):
                game = available_games[i]
                main_command = game["commands"][0]
                row.append(InlineKeyboardButton(text=game["name"], callback_data=f"start_game_{main_command}"))
            
            if i + 1 < len(available_games):
                game = available_games[i + 1]
                main_command = game["commands"][0]
                row.append(InlineKeyboardButton(text=game["name"], callback_data=f"start_game_{main_command}"))
            
            keyboard.append(row)
        
        reply_markup = InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None
        
        await message.reply(games_text, reply_markup=reply_markup)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الألعاب: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الألعاب")

async def handle_game_start_callback(callback_query, game_command: str):
    """معالجة بدء اللعبة من الأزرار"""
    try:
        # محاكاة رسالة جديدة لبدء اللعبة
        if game_command in ["اكس اوه", "xo"]:
            from modules.xo_game import start_xo_game
            # إنشاء رسالة وهمية لبدء اللعبة
            fake_message = callback_query.message
            fake_message.text = game_command
            await start_xo_game(fake_message)
            await callback_query.answer("🎮 تم بدء لعبة اكس اوه!")
            
        elif game_command in ["رويال", "royal"]:
            from modules.royal_game import start_royal_game  
            fake_message = callback_query.message
            fake_message.text = game_command
            await start_royal_game(fake_message)
            await callback_query.answer("👑 تم بدء لعبة الرويال!")
            
        elif game_command in ["الكلمة", "كلمة", "word"]:
            from modules.word_game import start_word_game
            # إنشاء رسالة وهمية محاكاة للضغط على الزر
            import types
            fake_message = types.SimpleNamespace()
            fake_message.chat = callback_query.message.chat
            fake_message.from_user = callback_query.from_user
            fake_message.text = game_command
            await start_word_game(fake_message)
            await callback_query.answer("💭 تم بدء لعبة الكلمة!")
            
        else:
            await callback_query.answer("❌ هذه اللعبة غير متاحة حالياً", show_alert=True)
            
    except Exception as e:
        logging.error(f"خطأ في بدء اللعبة من الزر: {e}")
        await callback_query.answer("❌ حدث خطأ في بدء اللعبة", show_alert=True)
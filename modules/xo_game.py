"""
لعبة اكس اوه (Tic-Tac-Toe) 
XO Game Module for Telegram Bot
"""

import logging
import asyncio
import time
from typing import Dict, List, Optional, Tuple
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.leveling import LevelingSystem
from utils.helpers import format_number
from modules.ai_player import xo_ai, should_ai_participate

# قاموس الألعاب النشطة {group_id: game_data}
ACTIVE_XO_GAMES: Dict[int, 'XOGame'] = {}

# رموز اللعبة
EMPTY = "⬜"
X = "❌"
O = "⭕"

class XOGame:
    """فئة لعبة اكس اوه"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.players = []  # قائمة اللاعبين
        self.board = [EMPTY] * 9  # لوحة اللعبة 3x3
        self.current_player = 0  # فهرس اللاعب الحالي
        self.game_started = False
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.has_ai_player = False  # هل يوجد AI في اللعبة
        self.ai_player_index = None  # فهرس لاعب AI
    
    def get_board_keyboard(self):
        """إنشاء لوحة مفاتيح اللعبة"""
        keyboard = []
        for i in range(3):
            row = []
            for j in range(3):
                index = i * 3 + j
                button_text = self.board[index]
                callback_data = f"xo_move_{self.group_id}_{index}"
                row.append(InlineKeyboardButton(text=button_text, callback_data=callback_data))
            keyboard.append(row)
        
        # إضافة معلومات اللعبة
        if not self.game_ended:
            if self.game_started and len(self.players) == 2:
                current_symbol = O if self.current_player == 0 else X
                current_name = self.players[self.current_player]['name']
                info_text = f"🎮 دور: {current_name} ({current_symbol})"
            else:
                info_text = "⏳ انتظار لاعب ثاني..."
        else:
            info_text = "🏁 انتهت اللعبة"
        
        keyboard.append([InlineKeyboardButton(text=info_text, callback_data="xo_info")])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def check_winner(self) -> Optional[int]:
        """فحص الفائز"""
        winning_combinations = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],  # صفوف
            [0, 3, 6], [1, 4, 7], [2, 5, 8],  # أعمدة
            [0, 4, 8], [2, 4, 6]              # أقطار
        ]
        
        for combo in winning_combinations:
            if (self.board[combo[0]] == self.board[combo[1]] == self.board[combo[2]] and 
                self.board[combo[0]] != EMPTY):
                # العثور على الفائز بناءً على الرمز
                symbol = self.board[combo[0]]
                if symbol == O:
                    return 0  # اللاعب الأول
                else:
                    return 1  # اللاعب الثاني
        
        return None
    
    def is_board_full(self) -> bool:
        """فحص امتلاء اللوحة"""
        return EMPTY not in self.board
    
    def make_move(self, position: int, player_index: int) -> bool:
        """تنفيذ حركة"""
        if (self.board[position] == EMPTY and 
            player_index == self.current_player and 
            not self.game_ended):
            
            # تحديد الرمز
            symbol = O if player_index == 0 else X
            self.board[position] = symbol
            
            # فحص الفائز
            winner_index = self.check_winner()
            if winner_index is not None:
                self.winner = winner_index
                self.game_ended = True
            elif self.is_board_full():
                self.game_ended = True  # تعادل
            else:
                # تبديل الدور
                self.current_player = 1 - self.current_player
            
            return True
        
        return False
    
    async def add_ai_player(self):
        """إضافة AI كلاعب ثاني"""
        if len(self.players) == 1 and not self.has_ai_player:
            ai_player = {
                'id': -1,  # معرف خاص للـ AI
                'name': 'يوكي',
                'username': 'yuki_ai'
            }
            self.players.append(ai_player)
            self.has_ai_player = True
            self.ai_player_index = 1
            self.game_started = True
            return True
        return False
    
    async def get_ai_move(self):
        """الحصول على حركة AI"""
        if not self.has_ai_player or self.current_player != self.ai_player_index:
            return None, None
        
        # تحديد رموز اللاعبين
        ai_symbol = X if self.ai_player_index == 1 else O
        player_symbol = O if self.ai_player_index == 1 else X
        
        # الحصول على أفضل حركة من AI
        move, response = await xo_ai.make_move_with_personality(
            self.board, ai_symbol, player_symbol
        )
        
        return move, response

async def start_xo_game(message: Message):
    """بدء لعبة اكس اوه جديدة"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "لاعب"
        
        # التأكد من تسجيل المنشئ
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # فحص وجود لعبة نشطة
        if group_id in ACTIVE_XO_GAMES:
            await message.reply(
                "🎮 **لعبة اكس اوه نشطة بالفعل!**\n\n"
                "❌ يجب انتهاء اللعبة الحالية أولاً"
            )
            return
        
        # إنشاء لعبة جديدة
        game = XOGame(group_id, creator_id, creator_name)
        ACTIVE_XO_GAMES[group_id] = game
        
        # إضافة المنشئ كأول لاعب
        game.players.append({
            'id': creator_id,
            'name': creator_name,
            'symbol': O
        })
        
        # فحص إذا كان AI سيشارك
        ai_will_join = await should_ai_participate('xo', len(game.players))
        
        # إرسال رسالة اللعبة
        game_text = (
            "🎮 **لعبة اكس اوه (Tic-Tac-Toe)**\n\n"
            f"👤 **منشئ اللعبة:** {creator_name}\n"
            f"🎯 **اللاعب الأول:** {creator_name} ({O})\n"
            f"⏳ **في انتظار لاعب ثاني...**\n\n"
            f"🏆 **الجائزة:** الفائز يحصل على 100 XP\n"
            f"🎖️ **المشاركة:** الخاسر يحصل على 5 XP\n\n"
            f"📝 **القوانين:**\n"
            f"• الهدف: ترتيب 3 رموز في خط مستقيم\n"
            f"• {O} للاعب الأول، {X} للاعب الثاني\n"
            f"• انقر على المربع الفارغ للعب\n\n"
            f"👥 **انضم للعبة أو العب ضد الذكاء الاصطناعي!**"
        )
        
        buttons = []
        buttons.append([InlineKeyboardButton(text="🎯 انضمام للعبة", callback_data=f"xo_join_{group_id}")])
        
        if ai_will_join:
            buttons.append([InlineKeyboardButton(text="🤖 العب ضد يوكي", callback_data=f"xo_ai_join_{group_id}")])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        await message.reply(game_text, reply_markup=keyboard)
        logging.info(f"تم إنشاء لعبة اكس اوه في المجموعة {group_id} بواسطة {creator_name}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة اكس اوه: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء لعبة اكس اوه")

async def handle_xo_join(callback: CallbackQuery):
    """معالجة انضمام لاعب للعبة"""
    try:
        # استخراج معرف المجموعة
        if not callback.data:
            await callback.answer("❌ بيانات غير صحيحة!", show_alert=True)
            return
        group_id = int(callback.data.split("_")[-1])
        if not callback.from_user:
            await callback.answer("❌ خطأ في بيانات المستخدم!", show_alert=True)
            return
        
        user_id = callback.from_user.id
        user_name = callback.from_user.first_name or "لاعب"
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_XO_GAMES:
            await callback.answer("❌ اللعبة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_XO_GAMES[group_id]
        
        # فحص إذا كان المنشئ يحاول الانضمام مرة أخرى
        if user_id == game.creator_id:
            await callback.answer("✅ أنت منشئ اللعبة بالفعل!", show_alert=True)
            return
        
        # فحص إذا كان اللاعب موجود بالفعل
        for player in game.players:
            if player['id'] == user_id:
                await callback.answer("✅ أنت مشارك في اللعبة بالفعل!", show_alert=True)
                return
        
        # فحص إذا كانت اللعبة ممتلئة
        if len(game.players) >= 2:
            await callback.answer("❌ اللعبة ممتلئة!", show_alert=True)
            return
        
        # التأكد من تسجيل المستخدم
        user_data = await get_or_create_user(user_id, getattr(callback.from_user, 'username', None) or "", user_name)
        if not user_data:
            await callback.answer("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'", show_alert=True)
            return
        
        # إضافة اللاعب الثاني
        game.players.append({
            'id': user_id,
            'name': user_name,
            'symbol': X
        })
        
        game.game_started = True
        
        # تحديث رسالة اللعبة
        game_text = (
            "🎮 **لعبة اكس اوه بدأت!**\n\n"
            f"👤 **{O} اللاعب الأول:** {game.players[0]['name']}\n"
            f"👤 **{X} اللاعب الثاني:** {game.players[1]['name']}\n\n"
            f"🎯 **دور اللاعب:** {game.players[game.current_player]['name']} ({game.players[game.current_player]['symbol']})\n\n"
            f"🏆 **الجائزة:** الفائز يحصل على 100 XP\n"
            f"🎖️ **المشاركة:** الخاسر يحصل على 5 XP"
        )
        
        if callback.message:
            await callback.message.edit_text(game_text, reply_markup=game.get_board_keyboard())
        await callback.answer(f"✅ تم انضمامك للعبة! أنت {X}")
        
        logging.info(f"انضم {user_name} ({user_id}) للعبة اكس اوه في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في انضمام لاعب لعبة اكس اوه: {e}")
        await callback.answer("❌ حدث خطأ أثناء الانضمام للعبة", show_alert=True)

async def handle_xo_move(callback: CallbackQuery):
    """معالجة حركة في اللعبة"""
    try:
        # استخراج البيانات
        if not callback.data:
            await callback.answer("❌ بيانات غير صحيحة!", show_alert=True)
            return
        data_parts = callback.data.split("_")
        group_id = int(data_parts[2])
        position = int(data_parts[3])
        user_id = callback.from_user.id
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_XO_GAMES:
            await callback.answer("❌ اللعبة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_XO_GAMES[group_id]
        
        # فحص إذا كانت اللعبة انتهت
        if game.game_ended:
            await callback.answer("🏁 اللعبة انتهت بالفعل!", show_alert=True)
            return
        
        # فحص إذا كانت اللعبة بدأت
        if not game.game_started or len(game.players) < 2:
            await callback.answer("⏳ انتظار اللاعب الثاني!", show_alert=True)
            return
        
        # العثور على فهرس اللاعب
        player_index = None
        for i, player in enumerate(game.players):
            if player['id'] == user_id:
                player_index = i
                break
        
        if player_index is None:
            await callback.answer("❌ أنت لست لاعب في هذه اللعبة!", show_alert=True)
            return
        
        # فحص الدور
        if player_index != game.current_player:
            current_player_name = game.players[game.current_player]['name']
            await callback.answer(f"⏳ دور {current_player_name}!", show_alert=True)
            return
        
        # تنفيذ الحركة
        if not game.make_move(position, player_index):
            await callback.answer("❌ مربع محجوز أو حركة غير صالحة!", show_alert=True)
            return
        
        # تحديث رسالة اللعبة
        if game.game_ended:
            await handle_game_end(callback, game)
        else:
            # فحص إذا كان دور AI
            if game.has_ai_player and game.current_player == game.ai_player_index:
                # معالجة حركة AI
                from modules.xo_ai_handler import process_ai_move
                await process_ai_move(game, callback)
            else:
                # تحديث اللوحة
                current_player_name = game.players[game.current_player]['name']
                current_symbol = game.players[game.current_player]['symbol']
                
                emoji = "🤖" if game.has_ai_player else "👤"
                
                game_text = (
                    "🎮 **لعبة اكس اوه جارية**\n\n"
                    f"👤 **{O} اللاعب الأول:** {game.players[0]['name']}\n"
                    f"{emoji} **{X} اللاعب الثاني:** {game.players[1]['name']}\n\n"
                    f"🎯 **دور اللاعب:** {current_player_name} ({current_symbol})"
                )
                
                if callback.message:
                    await callback.message.edit_text(game_text, reply_markup=game.get_board_keyboard())
            
            await callback.answer("✅ تم تنفيذ الحركة!")
        
    except Exception as e:
        logging.error(f"خطأ في حركة لعبة اكس اوه: {e}")
        await callback.answer("❌ حدث خطأ أثناء اللعب", show_alert=True)

async def handle_game_end(callback: CallbackQuery, game: XOGame):
    """معالجة نهاية اللعبة"""
    try:
        leveling_system = LevelingSystem()
        
        if game.winner is not None:
            # هناك فائز
            winner = game.players[game.winner]
            loser = game.players[1 - game.winner]
            
            # إضافة XP للفائز والخاسر
            await leveling_system.add_xp(winner['id'], "gaming")
            await leveling_system.add_xp(loser['id'], "gaming")
            
            # تحديث رصيد اللاعبين (اختياري - مكافأة إضافية)
            winner_data = await get_or_create_user(winner['id'])
            loser_data = await get_or_create_user(loser['id'])
            
            if winner_data and loser_data:
                await update_user_balance(winner['id'], winner_data['balance'] + 50)
                await update_user_balance(loser['id'], loser_data['balance'] + 10)
                
                await add_transaction(winner['id'], "gaming", 50, "فوز في لعبة اكس اوه")
                await add_transaction(loser['id'], "gaming", 10, "مشاركة في لعبة اكس اوه")
            
            game_text = (
                "🏆 **انتهت لعبة اكس اوه!**\n\n"
                f"👑 **الفائز:** {winner['name']} ({winner['symbol']})\n"
                f"💔 **الخاسر:** {loser['name']} ({loser['symbol']})\n\n"
                f"🎉 **مكافآت:**\n"
                f"• {winner['name']}: +100 XP + 50$\n"
                f"• {loser['name']}: +5 XP + 10$\n\n"
                f"🎮 **شكراً للعب! لعبة أخرى؟**"
            )
        else:
            # تعادل
            for player in game.players:
                await leveling_system.add_xp(player['id'], "gaming")
                player_data = await get_or_create_user(player['id'])
                if player_data:
                    await update_user_balance(player['id'], player_data['balance'] + 25)
                    await add_transaction(player['id'], "gaming", 25, "تعادل في لعبة اكس اوه")
            
            game_text = (
                "🤝 **تعادل في لعبة اكس اوه!**\n\n"
                f"👥 **اللاعبان:**\n"
                f"• {game.players[0]['name']} ({O})\n"
                f"• {game.players[1]['name']} ({X})\n\n"
                f"🎉 **مكافآت:**\n"
                f"• كل لاعب: +25 XP + 25$\n\n"
                f"🎮 **لعبة ممتازة! لعبة أخرى؟**"
            )
        
        # عرض اللوحة النهائية
        if callback.message:
            await callback.message.edit_text(game_text, reply_markup=game.get_board_keyboard())
        
        # حذف اللعبة
        if game.group_id in ACTIVE_XO_GAMES:
            del ACTIVE_XO_GAMES[game.group_id]
        
        logging.info(f"انتهت لعبة اكس اوه في المجموعة {game.group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية لعبة اكس اوه: {e}")

async def handle_xo_info(callback: CallbackQuery):
    """معالجة الضغط على معلومات اللعبة"""
    await callback.answer("ℹ️ معلومات اللعبة الحالية")

# وظائف إضافية
def get_active_games_count() -> int:
    """عدد الألعاب النشطة"""
    return len(ACTIVE_XO_GAMES)

def cleanup_old_games():
    """تنظيف الألعاب القديمة (أكثر من ساعة)"""
    current_time = time.time()
    games_to_remove = []
    
    for group_id, game in ACTIVE_XO_GAMES.items():
        if current_time - game.created_at > 3600:  # ساعة واحدة
            games_to_remove.append(group_id)
    
    for group_id in games_to_remove:
        del ACTIVE_XO_GAMES[group_id]
        logging.info(f"تم حذف لعبة اكس اوه قديمة من المجموعة {group_id}")
    
    return len(games_to_remove)
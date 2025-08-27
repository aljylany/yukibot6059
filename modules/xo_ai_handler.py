"""
معالج AI للعبة اكس-اوه
XO AI Handler - separate handler for AI integration
"""

import logging
import asyncio
from typing import Optional
from aiogram.types import CallbackQuery
from modules.xo_game import ACTIVE_XO_GAMES
from modules.ai_player import xo_ai

async def handle_xo_ai_join(callback: CallbackQuery):
    """معالجة انضمام AI للعبة"""
    try:
        # استخراج معرف المجموعة
        if not callback.data:
            await callback.answer("❌ بيانات غير صحيحة!", show_alert=True)
            return
        group_id = int(callback.data.split("_")[-1])
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_XO_GAMES:
            await callback.answer("❌ اللعبة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_XO_GAMES[group_id]
        
        # فحص إذا كانت اللعبة ممتلئة
        if len(game.players) >= 2:
            await callback.answer("❌ اللعبة ممتلئة!", show_alert=True)
            return
        
        # إضافة AI للعبة
        success = await game.add_ai_player()
        if not success:
            await callback.answer("❌ لا يمكن إضافة AI الآن!", show_alert=True)
            return
        
        # تحديث رسالة اللعبة
        game_text = (
            "🎮 **لعبة اكس اوه ضد AI بدأت!**\n\n"
            f"👤 **⭕ اللاعب:** {game.players[0]['name']}\n"
            f"🤖 **❌ يوكي:** {game.players[1]['name']}\n\n"
            f"🎯 **دور اللاعب:** {game.players[game.current_player]['name']} ({game.players[game.current_player]['symbol']})\n\n"
            f"🏆 **الجائزة:** الفائز يحصل على 100 XP\n"
            f"🎖️ **المشاركة:** الخاسر يحصل على 5 XP\n\n"
            f"🤖 لعبة ضد يوكي المتطور!"
        )
        
        if callback.message:
            await callback.message.edit_text(game_text, reply_markup=game.get_board_keyboard())
        await callback.answer("✅ تم بدء اللعبة ضد يوكي!")
        
        logging.info(f"بدأت لعبة ضد AI في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في إضافة AI للعبة: {e}")
        await callback.answer("❌ حدث خطأ أثناء إضافة AI", show_alert=True)

async def process_ai_move(game, callback: CallbackQuery = None):
    """معالجة حركة AI"""
    try:
        if not game.has_ai_player or game.current_player != game.ai_player_index:
            return None
        
        # انتظار قصير لمحاكاة التفكير
        await asyncio.sleep(1.5)
        
        # الحصول على حركة AI
        ai_move, ai_msg = await game.get_ai_move()
        if ai_move is not None:
            # تنفيذ حركة AI
            game.make_move(ai_move, game.ai_player_index)
            
            # تحديث الرسالة
            if callback and callback.message:
                if game.game_ended:
                    await handle_ai_game_end(callback, game, ai_msg)
                else:
                    # اللعبة مستمرة
                    current_player_name = game.players[game.current_player]['name']
                    current_symbol = game.players[game.current_player]['symbol']
                    
                    game_text = (
                        "🎮 **لعبة اكس اوه ضد AI جارية**\n\n"
                        f"👤 **⭕ اللاعب:** {game.players[0]['name']}\n"
                        f"🤖 **❌ يوكي:** {game.players[1]['name']}\n\n"
                        f"🎯 **دور اللاعب:** {current_player_name} ({current_symbol})\n\n"
                        f"🤖 {ai_msg}"
                    )
                    
                    await callback.message.edit_text(game_text, reply_markup=game.get_board_keyboard())
            
            return ai_msg
            
    except Exception as e:
        logging.error(f"خطأ في حركة AI: {e}")
        return None

async def handle_ai_game_end(callback: CallbackQuery, game, ai_msg: Optional[str] = None):
    """معالجة نهاية اللعبة مع AI"""
    try:
        from modules.leveling import LevelingSystem
        
        if game.winner is not None:
            winner_name = game.players[game.winner]['name']
            winner_symbol = game.players[game.winner]['symbol']
            
            # رد خاص عند فوز أو خسارة AI
            if game.has_ai_player:
                if game.winner == game.ai_player_index:
                    ai_victory_msg = await xo_ai.get_game_response('victory')
                    game_text = (
                        f"🏆 **انتهت اللعبة!**\n\n"
                        f"🤖 **الفائز:** {winner_name} ({winner_symbol})\n\n"
                        f"{ai_victory_msg}\n\n"
                        f"🎯 AI حصل على فوز استراتيجي!"
                    )
                else:
                    ai_defeat_msg = await xo_ai.get_game_response('defeat')
                    game_text = (
                        f"🏆 **انتهت اللعبة!**\n\n"
                        f"🎉 **الفائز:** {winner_name} ({winner_symbol})\n\n"
                        f"{ai_defeat_msg}\n\n"
                        f"✨ مبروك الفوز! حصلت على 100 XP"
                    )
            
            # إعطاء جوائز XP فقط للاعبين الحقيقيين
            try:
                leveling_system = LevelingSystem()
                for i, player in enumerate(game.players):
                    if player['id'] != -1:  # تجاهل AI
                        if i == game.winner:
                            await leveling_system.add_xp(player['id'], "gaming", 100)
                        else:
                            await leveling_system.add_xp(player['id'], "gaming", 5)
            except Exception as e:
                logging.error(f"خطأ في إعطاء XP: {e}")
        else:
            # تعادل
            game_text = (
                "🤝 **تعادل!**\n\n"
                "🎖️ لعبتم بمهارة عالية! حصل كل لاعب على 50 XP\n\n"
                "🤖 حتى يوكي يقدر مهارتكم!"
            )
            
            # إعطاء جوائز التعادل
            try:
                leveling_system = LevelingSystem()
                for player in game.players:
                    if player['id'] != -1:  # تجاهل AI
                        await leveling_system.add_xp(player['id'], "gaming", 50)
            except Exception as e:
                logging.error(f"خطأ في إعطاء XP: {e}")
        
        # إزالة الأزرار عند انتهاء اللعبة
        if callback.message:
            await callback.message.edit_text(game_text)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة نهاية اللعبة مع AI: {e}")

# تصدير الدوال
__all__ = ['handle_xo_ai_join', 'process_ai_move', 'handle_ai_game_end']
"""
لعبة الرويال - Royal Battle Game
نظام لعبة البقاء للأثرياء
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, timedelta

# حالات اللعبة
class RoyalGameStates(StatesGroup):
    waiting_for_players = State()
    waiting_for_confirmation = State()
    game_in_progress = State()

# تخزين ألعاب الرويال النشطة
ACTIVE_ROYAL_GAMES: Dict[int, Dict] = {}  # {group_id: game_data}

# معرف الشيخ للحصول على العمولة
SHEIKH_ID = 6154647949  # معرف الشيخ

async def start_royal_game(message: Message):
    """بدء لعبة الرويال الجديدة"""
    try:
        group_id = message.chat.id
        
        # التحقق من وجود لعبة نشطة
        if group_id in ACTIVE_ROYAL_GAMES:
            await message.reply("🎮 **يوجد لعبة رويال نشطة حالياً!**\n\nانتظروا انتهاء اللعبة الحالية")
            return
        
        # التحقق من أن المستخدم يملك مليون أو أكثر
        from database.operations import get_user
        user_data = await get_user(message.from_user.id)
        if not user_data or user_data.get('balance', 0) < 1000000:
            from utils.helpers import format_number
            current_balance = user_data.get('balance', 0) if user_data else 0
            await message.reply(
                f"💰 **عذراً، لا تملك الرصيد الكافي!**\n\n"
                f"💳 رصيدك الحالي: {format_number(current_balance)}$\n"
                f"💸 الرصيد المطلوب: {format_number(1000000)}$ أو أكثر\n\n"
                f"🏦 استخدم البنك لزيادة رصيدك"
            )
            return
        
        # إنشاء اللعبة الجديدة
        game_data = {
            'creator': message.from_user.id,
            'creator_name': message.from_user.first_name or "المنشئ",
            'players': [],
            'start_time': datetime.now(),
            'phase': 'registration',
            'message_id': None,
            'confirmed_players': set(),
            'eliminated_players': [],
            'total_pot': 0,
            'invited_players': [message.from_user.id],  # المنشئ مدعو تلقائياً
            'is_private': True  # اللعبة خاصة بالمدعوين فقط
        }
        
        ACTIVE_ROYAL_GAMES[group_id] = game_data
        
        # رسالة البداية
        game_message = await message.reply(
            f"🏆 **لعبة الرويال الملكية**\n\n"
            f"🎮 **بدأ التسجيل للعبة الرويال!**\n"
            f"👤 **منشئ اللعبة:** {game_data['creator_name']}\n\n"
            f"💰 **رسوم الدخول:** 1,000,000$ لكل لاعب\n"
            f"👥 **عدد اللاعبين:** 5-20 لاعب\n"
            f"⏰ **وقت التسجيل:** 3 دقائق\n\n"
            f"📊 **اللاعبين المسجلين (0/20):**\n"
            f"_لا يوجد لاعبين بعد..._\n\n"
            f"🔥 **انقر الزر أدناه للانضمام!**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🎯 انضمام للرويال", callback_data=f"royal_join_{group_id}")
            ]])
        )
        
        game_data['message_id'] = game_message.message_id
        
        # بدء العداد التنازلي
        asyncio.create_task(royal_registration_countdown(message.bot, group_id, game_message))
        
        logging.info(f"تم بدء لعبة رويال في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في بدء لعبة الرويال: {e}")
        await message.reply("❌ حدث خطأ أثناء بدء اللعبة")

async def royal_registration_countdown(bot, group_id: int, game_message: Message):
    """العداد التنازلي لفترة التسجيل"""
    try:
        # انتظار 3 دقائق (180 ثانية)
        for remaining_minutes in [2, 1]:
            await asyncio.sleep(60)  # انتظار دقيقة
            
            if group_id not in ACTIVE_ROYAL_GAMES:
                return  # اللعبة ملغية
            
            game_data = ACTIVE_ROYAL_GAMES[group_id]
            players_count = len(game_data['players'])
            players_list = "\n".join([f"• {player['name']}" for player in game_data['players']]) or "_لا يوجد لاعبين بعد..._"
            
            await bot.edit_message_text(
                chat_id=group_id,
                message_id=game_message.message_id,
                text=(
                    f"🏆 **لعبة الرويال الملكية**\n\n"
                    f"🎮 **التسجيل مستمر للعبة الرويال!**\n"
                    f"👤 **منشئ اللعبة:** {game_data['creator_name']}\n\n"
                    f"💰 **رسوم الدخول:** 1,000,000$ لكل لاعب\n"
                    f"👥 **عدد اللاعبين:** 5-20 لاعب\n"
                    f"⏰ **الوقت المتبقي:** {remaining_minutes} دقيقة\n\n"
                    f"📊 **اللاعبين المسجلين ({players_count}/20):**\n"
                    f"{players_list}\n\n"
                    f"🔥 **انقر الزر أدناه للانضمام!**"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🎯 انضمام للرويال", callback_data=f"royal_join_{group_id}")
                ]])
            )
        
        # انتظار الدقيقة الأخيرة
        await asyncio.sleep(60)
        
        if group_id not in ACTIVE_ROYAL_GAMES:
            return
        
        # انتهاء وقت التسجيل
        await finalize_royal_registration(bot, group_id)
        
    except Exception as e:
        logging.error(f"خطأ في العداد التنازلي للرويال: {e}")

async def handle_royal_join(callback_query: CallbackQuery):
    """معالجة انضمام لاعب للرويال"""
    try:
        group_id = int(callback_query.data.split("_")[-1])
        user_id = callback_query.from_user.id
        user_name = callback_query.from_user.first_name or "لاعب"
        
        if group_id not in ACTIVE_ROYAL_GAMES:
            await callback_query.answer("❌ اللعبة غير متاحة", show_alert=True)
            return
        
        game_data = ACTIVE_ROYAL_GAMES[group_id]
        
        # التحقق من أن التسجيل لا يزال مفتوحاً
        if game_data['phase'] != 'registration':
            await callback_query.answer("❌ انتهى وقت التسجيل", show_alert=True)
            return
        
        # التحقق من أن اللاعب مدعو (إذا كانت اللعبة خاصة)
        if game_data.get('is_private', False):
            if user_id not in game_data.get('invited_players', []):
                await callback_query.answer("❌ لست مدعواً لهذه اللعبة الخاصة", show_alert=True)
                return
        
        # التحقق من أن اللاعب غير مسجل مسبقاً
        if any(player['id'] == user_id for player in game_data['players']):
            await callback_query.answer("✅ أنت مسجل مسبقاً في اللعبة", show_alert=True)
            return
        
        # التحقق من العدد الأقصى
        if len(game_data['players']) >= 20:
            await callback_query.answer("❌ وصل عدد اللاعبين للحد الأقصى", show_alert=True)
            return
        
        # التحقق من رصيد اللاعب
        from database.operations import get_user
        user_data = await get_user(user_id)
        if not user_data or user_data.get('balance', 0) < 1000000:
            await callback_query.answer("❌ رصيدك غير كافٍ! تحتاج مليون دولار على الأقل", show_alert=True)
            return
        
        # إضافة اللاعب
        game_data['players'].append({
            'id': user_id,
            'name': user_name,
            'balance': user_data['balance']
        })
        
        players_count = len(game_data['players'])
        players_list = "\n".join([f"• {player['name']}" for player in game_data['players']])
        
        # تحديث الرسالة
        await callback_query.message.edit_text(
            text=(
                f"🏆 **لعبة الرويال الملكية**\n\n"
                f"🎮 **التسجيل مستمر للعبة الرويال!**\n"
                f"👤 **منشئ اللعبة:** {game_data['creator_name']}\n\n"
                f"💰 **رسوم الدخول:** 1,000,000$ لكل لاعب\n"
                f"👥 **عدد اللاعبين:** 5-20 لاعب\n"
                f"⏰ **حالة التسجيل:** مفتوح\n\n"
                f"📊 **اللاعبين المسجلين ({players_count}/20):**\n"
                f"{players_list}\n\n"
                f"🔥 **انقر الزر أدناه للانضمام!**"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🎯 انضمام للرويال", callback_data=f"royal_join_{group_id}")
            ]])
        )
        
        await callback_query.answer(f"✅ تم تسجيلك في اللعبة! ({players_count}/20)", show_alert=True)
        
        logging.info(f"انضم اللاعب {user_name} ({user_id}) للعبة الرويال في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في انضمام اللاعب للرويال: {e}")
        await callback_query.answer("❌ حدث خطأ أثناء التسجيل", show_alert=True)

async def finalize_royal_registration(bot, group_id: int):
    """إنهاء فترة التسجيل وبدء اللعبة"""
    try:
        if group_id not in ACTIVE_ROYAL_GAMES:
            return
        
        game_data = ACTIVE_ROYAL_GAMES[group_id]
        players_count = len(game_data['players'])
        
        # التحقق من العدد الأدنى
        if players_count < 5:
            players_list = "\n".join([f"• {player['name']}" for player in game_data['players']]) or "_لا يوجد لاعبين_"
            
            await bot.edit_message_text(
                chat_id=group_id,
                message_id=game_data['message_id'],
                text=(
                    f"🏆 **لعبة الرويال ملغية**\n\n"
                    f"❌ **لم يكتمل العدد المطلوب**\n"
                    f"📊 **اللاعبين المسجلين ({players_count}/5):**\n"
                    f"{players_list}\n\n"
                    f"💡 **يجب أن يكون هناك 5 لاعبين على الأقل لبدء اللعبة**\n"
                    f"🔄 يمكنكم إعادة المحاولة لاحقاً"
                ),
                reply_markup=None
            )
            
            # حذف اللعبة
            del ACTIVE_ROYAL_GAMES[group_id]
            return
        
        # بدء مرحلة التأكيد
        game_data['phase'] = 'confirmation'
        players_list = "\n".join([f"• {player['name']}" for player in game_data['players']])
        total_pot = players_count * 1000000
        
        from utils.helpers import format_number
        
        await bot.edit_message_text(
            chat_id=group_id,
            message_id=game_data['message_id'],
            text=(
                f"🏆 **لعبة الرويال - مرحلة التأكيد**\n\n"
                f"✅ **اكتمل التسجيل!**\n"
                f"👥 **عدد اللاعبين:** {players_count}\n"
                f"💰 **إجمالي الجائزة:** {format_number(total_pot)}$\n\n"
                f"📊 **اللاعبين المشاركين:**\n"
                f"{players_list}\n\n"
                f"⚠️ **تنبيه هام:**\n"
                f"• سيتم خصم 1,000,000$ من كل لاعب\n"
                f"• الشيخ سيحصل على عمولة 2%\n"
                f"• الفائز سيحصل على باقي المبلغ\n\n"
                f"🔴 **اضغط للتأكيد النهائي ودفع المبلغ**"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="✅ أؤكد وأدفع", callback_data=f"royal_confirm_{group_id}")
            ]])
        )
        
        logging.info(f"بدأت مرحلة التأكيد للعبة الرويال في المجموعة {group_id}")
        
        # انتظار التأكيد لمدة دقيقتين
        await asyncio.sleep(120)
        await start_royal_battle(bot, group_id)
        
    except Exception as e:
        logging.error(f"خطأ في إنهاء التسجيل للرويال: {e}")

async def handle_royal_confirmation(callback_query: CallbackQuery):
    """معالجة تأكيد اللاعب للدفع"""
    try:
        group_id = int(callback_query.data.split("_")[-1])
        user_id = callback_query.from_user.id
        
        if group_id not in ACTIVE_ROYAL_GAMES:
            await callback_query.answer("❌ اللعبة غير متاحة", show_alert=True)
            return
        
        game_data = ACTIVE_ROYAL_GAMES[group_id]
        
        # التحقق من أن اللاعب مسجل
        if not any(player['id'] == user_id for player in game_data['players']):
            await callback_query.answer("❌ لست مسجلاً في هذه اللعبة", show_alert=True)
            return
        
        # التحقق من أن اللاعب لم يؤكد مسبقاً
        if user_id in game_data['confirmed_players']:
            await callback_query.answer("✅ لقد أكدت مسبقاً", show_alert=True)
            return
        
        # التحقق من رصيد اللاعب مرة أخيرة
        from database.operations import get_user, update_user_balance
        user_data = await get_user(user_id)
        if not user_data or user_data.get('balance', 0) < 1000000:
            await callback_query.answer("❌ رصيدك غير كافٍ الآن!", show_alert=True)
            return
        
        # خصم المبلغ
        new_balance = user_data['balance'] - 1000000
        await update_user_balance(user_id, new_balance)
        
        # إضافة التأكيد
        game_data['confirmed_players'].add(user_id)
        game_data['total_pot'] += 1000000
        
        confirmed_count = len(game_data['confirmed_players'])
        total_players = len(game_data['players'])
        
        await callback_query.answer(f"✅ تم دفع 1,000,000$! ({confirmed_count}/{total_players})", show_alert=True)
        
        logging.info(f"أكد اللاعب {user_id} ودفع 1,000,000$ في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في تأكيد اللاعب للرويال: {e}")
        await callback_query.answer("❌ حدث خطأ أثناء التأكيد", show_alert=True)

async def start_royal_battle(bot, group_id: int):
    """بدء معارك الرويال الفعلية"""
    try:
        if group_id not in ACTIVE_ROYAL_GAMES:
            return
        
        game_data = ACTIVE_ROYAL_GAMES[group_id]
        confirmed_players = [player for player in game_data['players'] if player['id'] in game_data['confirmed_players']]
        
        if len(confirmed_players) < 2:
            await bot.edit_message_text(
                chat_id=group_id,
                message_id=game_data['message_id'],
                text=(
                    f"🏆 **لعبة الرويال ملغية**\n\n"
                    f"❌ **لم يؤكد عدد كافٍ من اللاعبين**\n"
                    f"📊 **اللاعبين الذين أكدوا:** {len(confirmed_players)}\n\n"
                    f"💰 **سيتم إرجاع الأموال للذين دفعوا**"
                )
            )
            
            # إرجاع الأموال
            from database.operations import get_user, update_user_balance
            for player_id in game_data['confirmed_players']:
                user_data = await get_user(player_id)
                if user_data:
                    new_balance = user_data['balance'] + 1000000
                    await update_user_balance(player_id, new_balance)
            
            del ACTIVE_ROYAL_GAMES[group_id]
            return
        
        # تحديث حالة اللعبة
        game_data['phase'] = 'battle'
        game_data['active_players'] = confirmed_players.copy()
        
        from utils.helpers import format_number
        total_pot = len(confirmed_players) * 1000000
        sheikh_commission = int(total_pot * 0.02)  # 2%
        final_prize = total_pot - sheikh_commission
        
        # بدء الجولات
        round_number = 1
        while len(game_data['active_players']) > 1:
            await conduct_royal_round(bot, group_id, round_number)
            round_number += 1
            
            if group_id not in ACTIVE_ROYAL_GAMES:
                return
            
            await asyncio.sleep(5)  # انتظار بين الجولات
        
        # إعلان الفائز
        if len(game_data['active_players']) == 1:
            winner = game_data['active_players'][0]
            
            # إرسال العمولة للشيخ
            from database.operations import get_user, update_user_balance
            sheikh_data = await get_user(SHEIKH_ID)
            if sheikh_data:
                sheikh_new_balance = sheikh_data['balance'] + sheikh_commission
                await update_user_balance(SHEIKH_ID, sheikh_new_balance)
            
            # إرسال الجائزة للفائز
            winner_data = await get_user(winner['id'])
            if winner_data:
                winner_new_balance = winner_data['balance'] + final_prize
                await update_user_balance(winner['id'], winner_new_balance)
            
            # إعلان الفائز
            await bot.send_message(
                chat_id=group_id,
                text=(
                    f"🏆 **انتهت لعبة الرويال!**\n\n"
                    f"👑 **الفائز:** {winner['name']}\n"
                    f"💰 **الجائزة:** {format_number(final_prize)}$\n"
                    f"💸 **عمولة الشيخ:** {format_number(sheikh_commission)}$ (2%)\n\n"
                    f"🎉 **مبروك للفائز!**\n"
                    f"🔥 لعبة مثيرة ومليئة بالإثارة"
                )
            )
            
            logging.info(f"فاز اللاعب {winner['name']} ({winner['id']}) في لعبة الرويال في المجموعة {group_id}")
        
        # حذف اللعبة
        del ACTIVE_ROYAL_GAMES[group_id]
        
    except Exception as e:
        logging.error(f"خطأ في بدء معارك الرويال: {e}")

async def conduct_royal_round(bot, group_id: int, round_number: int):
    """إجراء جولة واحدة من الرويال"""
    try:
        if group_id not in ACTIVE_ROYAL_GAMES:
            return
        
        game_data = ACTIVE_ROYAL_GAMES[group_id]
        active_players = game_data['active_players'].copy()
        
        if len(active_players) <= 1:
            return
        
        # عرض اللاعبين المتبقين
        players_list = ", ".join([player['name'] for player in active_players])
        
        await bot.send_message(
            chat_id=group_id,
            text=(
                f"⚔️ **الجولة {round_number}**\n\n"
                f"👥 **اللاعبين المتبقين ({len(active_players)}):**\n"
                f"{players_list}\n\n"
                f"🎲 **جاري إجراء القرعة...**"
            )
        )
        
        await asyncio.sleep(2)
        
        # إجراء القرعة المثيرة
        await bot.send_message(
            chat_id=group_id,
            text="🔄 **تدوير عجلة القدر...**"
        )
        
        await asyncio.sleep(2)
        
        # عرض الأسماء بطريقة مثيرة
        shuffled_players = active_players.copy()
        random.shuffle(shuffled_players)
        
        suspense_text = "🎯 **الأسماء تظهر على الشاشة...**\n\n"
        for i, player in enumerate(shuffled_players):
            suspense_text += f"{'🔸' if i < len(shuffled_players)-1 else '🔴'} {player['name']}\n"
        
        await bot.send_message(chat_id=group_id, text=suspense_text)
        await asyncio.sleep(3)
        
        # اختيار الخاسر
        eliminated_player = random.choice(active_players)
        game_data['active_players'] = [p for p in active_players if p['id'] != eliminated_player['id']]
        game_data['eliminated_players'].append(eliminated_player)
        
        remaining_count = len(game_data['active_players'])
        
        elimination_message = (
            f"💀 **تم الإقصاء!**\n\n"
            f"❌ **الخاسر:** {eliminated_player['name']}\n"
            f"👥 **متبقي:** {remaining_count} لاعب\n\n"
        )
        
        if remaining_count > 1:
            elimination_message += f"⚡ **الجولة القادمة قريباً...**"
        else:
            elimination_message += f"🏆 **نهاية اللعبة!**"
        
        await bot.send_message(chat_id=group_id, text=elimination_message)
        
        logging.info(f"تم إقصاء اللاعب {eliminated_player['name']} في الجولة {round_number} في المجموعة {group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في إجراء جولة الرويال: {e}")
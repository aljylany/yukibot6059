"""
معالجات أزرار لعبة ساحة الموت الأخيرة
Battle Arena Game Callbacks Handler
"""

import logging
import random
from aiogram.types import CallbackQuery
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.battle_arena_game import ACTIVE_BATTLE_GAMES
from utils.helpers import format_number

async def handle_battle_join(callback: CallbackQuery):
    """معالجة انضمام لاعب للمعركة"""
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
        user_name = callback.from_user.first_name or "محارب"
        username = callback.from_user.username or ""
        
        # فحص وجود اللعبة
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        # فحص إذا كانت اللعبة قد بدأت
        if game.game_started:
            await callback.answer("❌ المعركة بدأت بالفعل!", show_alert=True)
            return
        
        # فحص إذا كان اللاعب موجود بالفعل
        if any(p['id'] == user_id for p in game.players):
            await callback.answer("✅ أنت مشارك في المعركة بالفعل!", show_alert=True)
            return
        
        # التحقق من تسجيل اللاعب
        user_data = await get_or_create_user(user_id, username, user_name)
        if not user_data:
            await callback.answer("❌ يجب إنشاء حساب أولاً!", show_alert=True)
            return
        
        # فحص الرصيد
        if user_data['balance'] < game.entry_fee:
            await callback.answer(
                f"❌ رصيدك غير كافٍ!\n"
                f"💰 تحتاج: {format_number(game.entry_fee)}$\n"
                f"💳 رصيدك: {format_number(user_data['balance'])}$",
                show_alert=True
            )
            return
        
        # خصم رسوم الدخول
        await update_user_balance(user_id, user_data['balance'] - game.entry_fee)
        await add_transaction(user_id, "دخول ساحة الموت", -game.entry_fee, "battle_arena")
        
        # إضافة اللاعب
        if game.add_player(user_id, username, user_name):
            await callback.answer(f"✅ انضممت للمعركة! محاربين: {len(game.players)}/15")
            
            # تحديث رسالة اللعبة
            updated_text = (
                "⚔️ **ساحة الموت الأخيرة**\n\n"
                f"👤 **منشئ المعركة:** {game.creator_name}\n"
                f"💰 **رسوم الدخول:** {format_number(game.entry_fee)}$ لكل محارب\n"
                f"👥 **المحاربين المسجلين:** {len(game.players)}/15\n"
                f"⏰ **وقت التسجيل:** 3 دقائق\n\n"
                f"🏆 **المحاربين:**\n"
            )
            
            for i, player in enumerate(game.players[:10]):  # عرض أول 10 لاعبين
                updated_text += f"{i+1}. {player['name']} {player['weapon']}\n"
            
            if len(game.players) > 10:
                updated_text += f"... و {len(game.players) - 10} محاربين آخرين\n"
            
            updated_text += f"\n💎 **الجائزة الحالية:** {format_number(game.total_prize)}$\n\n"
            
            if len(game.players) >= 8:
                updated_text += "✅ **يمكن بدء المعركة الآن!**"
            else:
                updated_text += f"⏳ **تحتاج {8 - len(game.players)} محاربين إضافيين لبدء المعركة**"
            
            if callback.message:
                await callback.message.edit_text(updated_text, reply_markup=game.get_game_keyboard())
        else:
            await callback.answer("❌ فشل في الانضمام - المعركة ممتلئة!", show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في انضمام المعركة: {e}")
        await callback.answer("❌ حدث خطأ أثناء الانضمام", show_alert=True)

async def handle_battle_start(callback: CallbackQuery):
    """معالجة بدء المعركة"""
    try:
        group_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id if callback.from_user else 0
        
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        # فحص الصلاحيات - فقط منشئ اللعبة أو الأدمن
        if user_id != game.creator_id:
            await callback.answer("❌ فقط منشئ المعركة يمكنه البدء!", show_alert=True)
            return
        
        # فحص عدد اللاعبين
        if len(game.players) < 8:
            await callback.answer(f"❌ تحتاج {8 - len(game.players)} محاربين إضافيين!", show_alert=True)
            return
        
        if game.game_started:
            await callback.answer("❌ المعركة بدأت بالفعل!", show_alert=True)
            return
        
        # بدء المعركة
        game.game_started = True
        
        start_text = (
            "🚀 **بدأت المعركة!**\n\n"
            f"⚔️ {len(game.players)} محارب دخلوا الساحة\n"
            f"💰 الجائزة الكبرى: {format_number(game.total_prize)}$\n\n"
            f"🎯 **نصائح للبقاء:**\n"
            f"• تحرك باستمرار لتجنب العاصفة\n"
            f"• هاجم بحكمة واختر أهدافك\n"
            f"• استخدم الدفاع عند الحاجة\n\n"
            f"⏱️ **ستتقلص الساحة كل دقيقة!**\n\n"
            f"{game.get_arena_display()}"
        )
        
        await callback.message.edit_text(start_text, reply_markup=game.get_game_keyboard())
        await callback.answer("🔥 بدأت المعركة!")
        
        # بدء دورة تقليص الساحة
        from modules.battle_arena_game import arena_shrink_cycle
        import asyncio
        asyncio.create_task(arena_shrink_cycle(game, callback.message))
        
    except Exception as e:
        logging.error(f"خطأ في بدء المعركة: {e}")
        await callback.answer("❌ حدث خطأ في بدء المعركة", show_alert=True)

async def handle_battle_move(callback: CallbackQuery):
    """معالجة حركة اللاعب"""
    try:
        group_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id if callback.from_user else 0
        
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        if not game.game_started or game.game_ended:
            await callback.answer("❌ المعركة لم تبدأ أو انتهت!", show_alert=True)
            return
        
        # العثور على اللاعب
        player = next((p for p in game.players if p['id'] == user_id), None)
        if not player or not player['alive']:
            await callback.answer("❌ أنت لست في المعركة أو قد قُتلت!", show_alert=True)
            return
        
        # تحريك اللاعب عشوائياً
        old_position = player['position']
        player['position'] = random.randint(0, game.safe_zone_size - 1)
        
        # منح HP إضافي للحركة
        if player['health'] < 100:
            player['health'] = min(100, player['health'] + 5)
        
        await callback.answer(f"🏃‍♂️ تحركت إلى موقع جديد! (+5 صحة)")
        
    except Exception as e:
        logging.error(f"خطأ في حركة اللاعب: {e}")
        await callback.answer("❌ حدث خطأ في الحركة", show_alert=True)

async def handle_battle_attack(callback: CallbackQuery):
    """معالجة هجوم اللاعب"""
    try:
        group_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id if callback.from_user else 0
        
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        if not game.game_started or game.game_ended:
            await callback.answer("❌ المعركة لم تبدأ أو انتهت!", show_alert=True)
            return
        
        # العثور على اللاعب
        attacker = next((p for p in game.players if p['id'] == user_id), None)
        if not attacker or not attacker['alive']:
            await callback.answer("❌ أنت لست في المعركة أو قد قُتلت!", show_alert=True)
            return
        
        # العثور على هدف عشوائي
        alive_enemies = [p for p in game.players if p['alive'] and p['id'] != user_id]
        if not alive_enemies:
            await callback.answer("❌ لا يوجد أعداء متاحين!", show_alert=True)
            return
        
        target = random.choice(alive_enemies)
        
        # تنفيذ الهجوم
        combat_result = game.process_combat(user_id, target['id'])
        
        await callback.answer(combat_result[:100] + "..." if len(combat_result) > 100 else combat_result)
        
        # فحص انتهاء اللعبة
        if game.check_game_end():
            from modules.battle_arena_game import handle_battle_end
            await handle_battle_end(game, callback.message)
        
    except Exception as e:
        logging.error(f"خطأ في هجوم اللاعب: {e}")
        await callback.answer("❌ حدث خطأ في الهجوم", show_alert=True)

async def handle_battle_defend(callback: CallbackQuery):
    """معالجة دفاع اللاعب"""
    try:
        group_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id if callback.from_user else 0
        
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        if not game.game_started or game.game_ended:
            await callback.answer("❌ المعركة لم تبدأ أو انتهت!", show_alert=True)
            return
        
        # العثور على اللاعب
        player = next((p for p in game.players if p['id'] == user_id), None)
        if not player or not player['alive']:
            await callback.answer("❌ أنت لست في المعركة أو قد قُتلت!", show_alert=True)
            return
        
        # تفعيل الدفاع
        healing = random.randint(10, 20)
        player['health'] = min(100, player['health'] + healing)
        
        # منح درع مؤقت
        if not player['shield']:
            shields = ["🛡️", "🚧", "⛑️"]
            player['shield'] = random.choice(shields)
        
        await callback.answer(f"🛡️ تم تفعيل الدفاع! (+{healing} صحة + درع)")
        
    except Exception as e:
        logging.error(f"خطأ في دفاع اللاعب: {e}")
        await callback.answer("❌ حدث خطأ في الدفاع", show_alert=True)

async def handle_battle_scout(callback: CallbackQuery):
    """معالجة استطلاع اللاعب"""
    try:
        group_id = int(callback.data.split("_")[-1])
        user_id = callback.from_user.id if callback.from_user else 0
        
        if group_id not in ACTIVE_BATTLE_GAMES:
            await callback.answer("❌ المعركة غير موجودة!", show_alert=True)
            return
        
        game = ACTIVE_BATTLE_GAMES[group_id]
        
        if not game.game_started or game.game_ended:
            await callback.answer("❌ المعركة لم تبدأ أو انتهت!", show_alert=True)
            return
        
        # العثور على اللاعب
        player = next((p for p in game.players if p['id'] == user_id), None)
        if not player or not player['alive']:
            await callback.answer("❌ أنت لست في المعركة أو قد قُتلت!", show_alert=True)
            return
        
        # معلومات الاستطلاع
        alive_count = len([p for p in game.players if p['alive']])
        scout_info = (
            f"🔍 **استطلاع الساحة:**\n"
            f"👥 محاربين أحياء: {alive_count}\n"
            f"🟦 المنطقة الآمنة: {game.safe_zone_size} مربع\n"
            f"⚔️ الجولة: {game.current_round}/{game.max_rounds}\n"
            f"❤️ صحتك: {player['health']}/100\n"
            f"🗡️ سلاحك: {player['weapon']}\n"
            f"🛡️ درعك: {player['shield'] or 'لا يوجد'}"
        )
        
        await callback.answer(scout_info, show_alert=True)
        
    except Exception as e:
        logging.error(f"خطأ في استطلاع اللاعب: {e}")
        await callback.answer("❌ حدث خطأ في الاستطلاع", show_alert=True)
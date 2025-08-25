"""
لعبة ساحة الموت الأخيرة - Battle Arena Game
معركة البقاء المثيرة للبوت
"""

import logging
import asyncio
import time
import random
from typing import Dict, List, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from database.operations import get_or_create_user, update_user_balance, add_transaction
from modules.leveling import LevelingSystem
from utils.helpers import format_number

# قاموس الألعاب النشطة {group_id: game_data}
ACTIVE_BATTLE_GAMES: Dict[int, 'BattleArenaGame'] = {}

# رموز اللعبة
ALIVE_PLAYER = "🟢"
ELIMINATED_PLAYER = "💀" 
SAFE_ZONE = "🟦"
DANGER_ZONE = "🟥"
WEAPONS = ["🗡️", "🏹", "⚔️", "🔫", "💣"]
SHIELDS = ["🛡️", "🚧", "⛑️"]

class BattleArenaGame:
    """فئة لعبة ساحة الموت الأخيرة"""
    
    def __init__(self, group_id: int, creator_id: int, creator_name: str):
        self.group_id = group_id
        self.creator_id = creator_id
        self.creator_name = creator_name
        self.players = []  # قائمة اللاعبين
        self.arena_size = 25  # حجم الساحة (5x5)
        self.safe_zone_size = 25  # المنطقة الآمنة
        self.current_round = 0
        self.max_rounds = 8  # عدد الجولات القصوى
        self.game_started = False
        self.game_ended = False
        self.winner = None
        self.created_at = time.time()
        self.last_shrink = time.time()
        self.entry_fee = 100000  # رسوم الدخول 100K
        self.total_prize = 0
        
    def add_player(self, user_id: int, username: str, display_name: str) -> bool:
        """إضافة لاعب جديد"""
        if len(self.players) >= 15:  # الحد الأقصى 15 لاعب
            return False
            
        if any(p['id'] == user_id for p in self.players):
            return False  # اللاعب موجود بالفعل
            
        player = {
            'id': user_id,
            'username': username,
            'name': display_name,
            'position': random.randint(0, 24),  # موقع عشوائي في الساحة
            'health': 100,
            'weapon': random.choice(WEAPONS),
            'shield': random.choice(SHIELDS) if random.random() < 0.3 else None,
            'alive': True,
            'kills': 0,
            'damage_dealt': 0
        }
        
        self.players.append(player)
        self.total_prize += self.entry_fee
        return True
    
    def get_arena_display(self) -> str:
        """عرض الساحة الحالية"""
        arena_text = "🎯 **ساحة المعركة**\n\n"
        
        # عرض حالة الساحة
        arena_text += f"📊 الجولة: {self.current_round}/{self.max_rounds}\n"
        arena_text += f"🟦 المنطقة الآمنة: {self.safe_zone_size} مربع\n"
        arena_text += f"👥 اللاعبين الأحياء: {len([p for p in self.players if p['alive']])}\n\n"
        
        # عرض اللاعبين
        alive_players = [p for p in self.players if p['alive']]
        for i, player in enumerate(alive_players[:8]):  # عرض أول 8 لاعبين
            status = ALIVE_PLAYER if player['alive'] else ELIMINATED_PLAYER
            arena_text += f"{status} {player['name']} {player['weapon']}"
            if player['shield']:
                arena_text += f" {player['shield']}"
            arena_text += f" (❤️{player['health']})\n"
            
        if len(alive_players) > 8:
            arena_text += f"... و {len(alive_players) - 8} لاعبين آخرين\n"
            
        return arena_text
    
    def get_game_keyboard(self) -> InlineKeyboardMarkup:
        """إنشاء لوحة مفاتيح اللعبة"""
        keyboard = []
        
        if not self.game_started:
            # مرحلة التسجيل
            keyboard.append([
                InlineKeyboardButton(text="⚔️ انضمام للمعركة", callback_data=f"battle_join_{self.group_id}")
            ])
            keyboard.append([
                InlineKeyboardButton(text="🚀 بدء المعركة", callback_data=f"battle_start_{self.group_id}")
            ])
        else:
            # مرحلة اللعب
            row1 = [
                InlineKeyboardButton(text="🏃‍♂️ تحرك", callback_data=f"battle_move_{self.group_id}"),
                InlineKeyboardButton(text="⚔️ هجوم", callback_data=f"battle_attack_{self.group_id}")
            ]
            row2 = [
                InlineKeyboardButton(text="🛡️ دفاع", callback_data=f"battle_defend_{self.group_id}"),
                InlineKeyboardButton(text="🔍 استطلاع", callback_data=f"battle_scout_{self.group_id}")
            ]
            keyboard.extend([row1, row2])
        
        return InlineKeyboardMarkup(inline_keyboard=keyboard)
    
    def shrink_arena(self):
        """تقليص الساحة"""
        if self.safe_zone_size > 4:
            self.safe_zone_size = max(4, self.safe_zone_size - 3)
            self.current_round += 1
            
            # إلحاق ضرر باللاعبين خارج المنطقة الآمنة
            for player in self.players:
                if player['alive'] and player['position'] >= self.safe_zone_size:
                    damage = random.randint(15, 35)
                    player['health'] -= damage
                    if player['health'] <= 0:
                        player['alive'] = False
                        player['health'] = 0
    
    def process_combat(self, attacker_id: int, target_id: int) -> str:
        """معالجة القتال بين لاعبين"""
        attacker = next((p for p in self.players if p['id'] == attacker_id), None)
        target = next((p for p in self.players if p['id'] == target_id), None)
        
        if not attacker or not target or not attacker['alive'] or not target['alive']:
            return "❌ لا يمكن تنفيذ الهجوم"
        
        # حساب الضرر
        base_damage = random.randint(20, 40)
        weapon_bonus = random.randint(5, 15)
        damage = base_damage + weapon_bonus
        
        # تأثير الدرع
        if target['shield'] and random.random() < 0.4:
            damage = damage // 2
            shield_text = f" (امتص الدرع {damage} ضرر)"
        else:
            shield_text = ""
        
        target['health'] -= damage
        attacker['damage_dealt'] += damage
        
        if target['health'] <= 0:
            target['alive'] = False
            target['health'] = 0
            attacker['kills'] += 1
            return f"💀 {attacker['name']} قتل {target['name']} بـ{attacker['weapon']}! (+{damage} ضرر){shield_text}"
        else:
            return f"⚔️ {attacker['name']} هاجم {target['name']} بـ{attacker['weapon']}! (-{damage} صحة){shield_text}"
    
    def check_game_end(self) -> bool:
        """فحص انتهاء اللعبة"""
        alive_players = [p for p in self.players if p['alive']]
        
        if len(alive_players) <= 1:
            if alive_players:
                self.winner = alive_players[0]
            self.game_ended = True
            return True
        
        if self.current_round >= self.max_rounds:
            # اللعبة انتهت بالوقت - أعلى صحة يفوز
            alive_players.sort(key=lambda x: x['health'], reverse=True)
            if alive_players:
                self.winner = alive_players[0]
            self.game_ended = True
            return True
            
        return False

async def start_battle_arena(message: Message):
    """بدء لعبة ساحة الموت الأخيرة"""
    try:
        group_id = message.chat.id
        creator_id = message.from_user.id
        creator_name = message.from_user.first_name or "المحارب"
        
        # التحقق من تسجيل المنشئ
        user_data = await get_or_create_user(creator_id, message.from_user.username or "", creator_name)
        if not user_data:
            await message.reply("❌ يجب إنشاء حساب أولاً! اكتب 'انشاء حساب بنكي'")
            return
        
        # فحص الرصيد
        if user_data['balance'] < 100000:
            await message.reply(
                f"💰 **رصيدك غير كافٍ للدخول!**\n\n"
                f"💳 رصيدك الحالي: {format_number(user_data['balance'])}$\n"
                f"💸 رسوم الدخول: {format_number(100000)}$\n\n"
                f"🏦 استخدم البنك لزيادة رصيدك أو العب ألعاب أخرى"
            )
            return
        
        # فحص وجود لعبة نشطة
        if group_id in ACTIVE_BATTLE_GAMES:
            await message.reply(
                "⚔️ **معركة نشطة بالفعل!**\n\n"
                "❌ انتظر انتهاء المعركة الحالية"
            )
            return
        
        # إنشاء لعبة جديدة
        game = BattleArenaGame(group_id, creator_id, creator_name)
        ACTIVE_BATTLE_GAMES[group_id] = game
        
        # خصم رسوم الدخول من المنشئ
        await update_user_balance(creator_id, user_data['balance'] - 100000)
        await add_transaction(creator_id, "دخول ساحة الموت", -100000, "battle_arena")
        
        # إضافة المنشئ كأول لاعب
        game.add_player(creator_id, message.from_user.username or "", creator_name)
        
        # رسالة البداية
        game_text = (
            "⚔️ **ساحة الموت الأخيرة**\n\n"
            f"👤 **منشئ المعركة:** {creator_name}\n"
            f"💰 **رسوم الدخول:** {format_number(100000)}$ لكل محارب\n"
            f"👥 **عدد المحاربين:** 8-15 محارب\n"
            f"⏰ **وقت التسجيل:** 3 دقائق\n\n"
            f"🎯 **القوانين:**\n"
            f"• آخر محارب على قيد الحياة يفوز بكل شيء\n"
            f"• الساحة تتقلص كل دقيقة\n"
            f"• الخروج من المنطقة الآمنة = ضرر مستمر\n"
            f"• أسلحة عشوائية ودروع محدودة\n\n"
            f"💎 **الجائزة الحالية:** {format_number(game.total_prize)}$\n\n"
            f"🔥 **انضم الآن قبل بدء المعركة!**"
        )
        
        await message.reply(game_text, reply_markup=game.get_game_keyboard())
        logging.info(f"تم إنشاء ساحة الموت في المجموعة {group_id} بواسطة {creator_name}")
        
        # بدء عداد التسجيل (3 دقائق)
        asyncio.create_task(registration_timer(game, message))
        
    except Exception as e:
        logging.error(f"خطأ في بدء ساحة الموت: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء ساحة الموت")

async def registration_timer(game: BattleArenaGame, message: Message):
    """عداد التسجيل (3 دقائق)"""
    await asyncio.sleep(180)  # 3 دقائق
    
    if game.group_id in ACTIVE_BATTLE_GAMES and not game.game_started:
        if len(game.players) < 8:
            # إلغاء اللعبة - عدد لاعبين غير كافٍ
            await message.reply(
                "❌ **تم إلغاء المعركة!**\n\n"
                f"👥 عدد المحاربين غير كافٍ: {len(game.players)}/8\n"
                f"💰 سيتم استرداد رسوم الدخول لجميع اللاعبين"
            )
            
            # استرداد المال
            for player in game.players:
                user_data = await get_or_create_user(player['id'])
                if user_data:
                    await update_user_balance(player['id'], user_data['balance'] + 100000)
                    await add_transaction(player['id'], "استرداد رسوم ساحة الموت", 100000, "refund")
            
            del ACTIVE_BATTLE_GAMES[game.group_id]
        else:
            # بدء اللعبة تلقائياً
            await auto_start_battle(game, message)

async def auto_start_battle(game: BattleArenaGame, message: Message):
    """بدء المعركة تلقائياً"""
    game.game_started = True
    
    start_text = (
        "🚀 **بدأت المعركة!**\n\n"
        f"⚔️ {len(game.players)} محارب دخلوا الساحة\n"
        f"💰 الجائزة الكبرى: {format_number(game.total_prize)}$\n\n"
        f"🎯 **نصائح للبقاء:**\n"
        f"• تحرك باستمرار\n"
        f"• هاجم بحكمة\n"
        f"• ابق في المنطقة الآمنة\n\n"
        f"⏱️ **ستتقلص الساحة كل دقيقة!**"
    )
    
    await message.reply(start_text + "\n\n" + game.get_arena_display(), 
                       reply_markup=game.get_game_keyboard())
    
    # بدء دورة تقليص الساحة
    asyncio.create_task(arena_shrink_cycle(game, message))

async def arena_shrink_cycle(game: BattleArenaGame, message: Message):
    """دورة تقليص الساحة"""
    while not game.game_ended and game.group_id in ACTIVE_BATTLE_GAMES:
        await asyncio.sleep(60)  # انتظار دقيقة
        
        if game.game_ended:
            break
            
        game.shrink_arena()
        
        shrink_text = (
            f"🔥 **تقلصت الساحة! - الجولة {game.current_round}**\n\n"
            f"🟦 المنطقة الآمنة: {game.safe_zone_size} مربع\n"
            f"👥 المحاربين الأحياء: {len([p for p in game.players if p['alive']])}\n\n"
        )
        
        # عرض اللاعبين المتضررين
        damaged_players = [p for p in game.players if p['position'] >= game.safe_zone_size and p['alive']]
        if damaged_players:
            shrink_text += "💥 **متضررين من العاصفة:**\n"
            for player in damaged_players[:3]:
                shrink_text += f"🔴 {player['name']} (❤️{player['health']})\n"
        
        await message.reply(shrink_text + "\n" + game.get_arena_display(), 
                           reply_markup=game.get_game_keyboard())
        
        # فحص انتهاء اللعبة
        if game.check_game_end():
            await handle_battle_end(game, message)
            break

async def handle_battle_end(game: BattleArenaGame, message: Message):
    """معالجة نهاية المعركة"""
    try:
        leveling_system = LevelingSystem()
        
        if game.winner:
            winner = game.winner
            
            # مكافأة الفائز
            winner_data = await get_or_create_user(winner['id'])
            if winner_data:
                prize_amount = int(game.total_prize * 0.8)  # 80% للفائز
                await update_user_balance(winner['id'], winner_data['balance'] + prize_amount)
                await add_transaction(winner['id'], "فوز في ساحة الموت", prize_amount, "battle_win")
                await leveling_system.add_xp(winner['id'], "gaming")
            
            # مكافآت اللاعبين الآخرين
            alive_players = [p for p in game.players if p['alive'] and p['id'] != winner['id']]
            participation_reward = max(1000, int(game.total_prize * 0.2 / len(game.players)))
            
            for player in game.players:
                if player['id'] != winner['id']:
                    player_data = await get_or_create_user(player['id'])
                    if player_data:
                        reward = participation_reward + (player['kills'] * 5000)
                        await update_user_balance(player['id'], player_data['balance'] + reward)
                        await add_transaction(player['id'], "مشاركة في ساحة الموت", reward, "battle_participation")
                        await leveling_system.add_xp(player['id'], "gaming")
            
            end_text = (
                "🏆 **انتهت المعركة!**\n\n"
                f"👑 **البطل المنتصر:** {winner['name']}\n"
                f"💰 **الجائزة:** {format_number(prize_amount)}$\n"
                f"⚔️ **عدد القتلى:** {winner['kills']}\n"
                f"❤️ **الصحة المتبقية:** {winner['health']}\n"
                f"🎯 **الضرر المُلحق:** {winner['damage_dealt']}\n\n"
                f"🎖️ **إحصائيات المعركة:**\n"
                f"• المشاركين: {len(game.players)}\n"
                f"• الجولات: {game.current_round}\n"
                f"• إجمالي الجوائز: {format_number(game.total_prize)}$\n\n"
                f"🔥 **معركة أخرى؟ ابدأ جولة جديدة!**"
            )
        else:
            end_text = "💥 **انتهت المعركة بدون فائز!**\n\n📜 تم استرداد 50% من رسوم الدخول"
        
        await message.reply(end_text)
        
        # إزالة اللعبة من الذاكرة
        if game.group_id in ACTIVE_BATTLE_GAMES:
            del ACTIVE_BATTLE_GAMES[game.group_id]
        
        logging.info(f"انتهت ساحة الموت في المجموعة {game.group_id}")
        
    except Exception as e:
        logging.error(f"خطأ في نهاية ساحة الموت: {e}")

# سيتم إضافة معالجات الأزرار والأحداث في ملف منفصل
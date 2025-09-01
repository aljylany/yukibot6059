"""
نظام متاهات النقابة
Guild Mazes System
"""

import logging
import time
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from modules.guild_game import GUILD_PLAYERS, GuildPlayer
from modules.guild_database import save_guild_player
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number

# تخزين المتاهات النشطة {user_id: ActiveMaze}
ACTIVE_MAZES: Dict[int, 'ActiveMaze'] = {}

# كولداون المتاهات (5 دقائق بين المتاهات)
MAZE_COOLDOWN: Dict[int, float] = {}
MAZE_COOLDOWN_DURATION = 300  # 5 دقائق

class ActiveMaze:
    """متاهة نشطة"""
    def __init__(self, user_id: int, maze_type: str, maze_name: str, floor: int, 
                 duration_minutes: int, monsters: int, power_required: int,
                 experience_reward: int, experience_loss: int):
        self.user_id = user_id
        self.maze_type = maze_type
        self.maze_name = maze_name
        self.floor = floor
        self.duration_minutes = duration_minutes
        self.monsters = monsters
        self.power_required = power_required
        self.experience_reward = experience_reward
        self.experience_loss = experience_loss
        self.start_time = datetime.now()
    
    def is_completed(self) -> bool:
        """فحص إذا انتهت المتاهة"""
        elapsed = datetime.now() - self.start_time
        return elapsed.total_seconds() >= (self.duration_minutes * 60)
    
    def time_remaining(self) -> str:
        """الوقت المتبقي للانتهاء"""
        elapsed = datetime.now() - self.start_time
        remaining_seconds = (self.duration_minutes * 60) - elapsed.total_seconds()
        
        if remaining_seconds <= 0:
            return "انتهت!"
        
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

# متاهات متاحة
MAZES = {
    "single": {
        "eternal_hell": {
            "name": "🔥 الجحيم الأبدي",
            "description": "متاهة الجحيم الأسطورية",
            "floors": {
                1: {"power_required": 500, "experience_reward": 5000, "experience_loss": 100, "monsters": 4, "duration": 15},
                2: {"power_required": 800, "experience_reward": 8000, "experience_loss": 200, "monsters": 6, "duration": 18},
                3: {"power_required": 1200, "experience_reward": 12000, "experience_loss": 300, "monsters": 8, "duration": 22},
                4: {"power_required": 1600, "experience_reward": 16000, "experience_loss": 400, "monsters": 10, "duration": 25},
                5: {"power_required": 2000, "experience_reward": 20000, "experience_loss": 500, "monsters": 12, "duration": 30},
                6: {"power_required": 2500, "experience_reward": 25000, "experience_loss": 600, "monsters": 15, "duration": 35},
                7: {"power_required": 3000, "experience_reward": 30000, "experience_loss": 700, "monsters": 18, "duration": 40},
                8: {"power_required": 3500, "experience_reward": 35000, "experience_loss": 800, "monsters": 20, "duration": 45},
                9: {"power_required": 4000, "experience_reward": 40000, "experience_loss": 900, "monsters": 25, "duration": 50},
                10: {"power_required": 5000, "experience_reward": 50000, "experience_loss": 1000, "monsters": 30, "duration": 60}
            }
        }
    },
    "multiplayer": {
        "shadow_castle": {
            "name": "🏰 قلعة الظلال",
            "description": "متاهة جماعية للفرق القوية",
            "floors": {
                1: {"power_required": 1000, "experience_reward": 8000, "experience_loss": 150, "monsters": 8, "duration": 20},
                2: {"power_required": 1500, "experience_reward": 12000, "experience_loss": 250, "monsters": 12, "duration": 25},
                3: {"power_required": 2000, "experience_reward": 16000, "experience_loss": 350, "monsters": 16, "duration": 30}
            }
        }
    }
}

async def show_mazes_menu(callback: CallbackQuery):
    """عرض قائمة المتاهات"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        # فحص المتاهة النشطة
        if user_id in ACTIVE_MAZES:
            await show_active_maze_status(callback)
            return
        
        # فحص الكولداون
        current_time = time.time()
        if user_id in MAZE_COOLDOWN:
            time_passed = current_time - MAZE_COOLDOWN[user_id]
            if time_passed < MAZE_COOLDOWN_DURATION:
                remaining = int(MAZE_COOLDOWN_DURATION - time_passed)
                minutes = remaining // 60
                seconds = remaining % 60
                await callback.message.edit_text(
                    f"⏰ **انتظر قليلاً!**\n\n"
                    f"🔒 يجب الانتظار {minutes}:{seconds:02d} قبل دخول متاهة جديدة\n"
                    f"💡 استخدم هذا الوقت لتقوية نفسك!",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
                    ]])
                )
                await callback.answer()
                return
        
        player = GUILD_PLAYERS[user_id]
        
        keyboard = [
            [InlineKeyboardButton(text="🏰 متاهة فردية", callback_data="mazes_single")],
            [InlineKeyboardButton(text="👥 متاهة متعددة", callback_data="mazes_multiplayer")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")]
        ]
        
        await callback.message.edit_text(
            f"🏰 **مرحباً في متاهات النقابة الأسطورية!**\n\n"
            f"👤 **اللاعب:** {player.name}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"⚔️ **القوة:** {format_number(player.power)}\n\n"
            f"🎯 **اختر نوع المتاهة:**\n\n"
            f"🏰 **فردية** - تحدى وحدك!\n"
            f"👥 **متعددة** - تعاون مع الآخرين!\n\n"
            f"⚠️ **تحذير:** الفشل في المتاهة يؤدي لخسارة خبرة!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة المتاهات: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_single_mazes(callback: CallbackQuery):
    """عرض المتاهات الفردية"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        
        for maze_id, maze_data in MAZES["single"].items():
            keyboard.append([InlineKeyboardButton(
                text=maze_data["name"],
                callback_data=f"maze_single_{maze_id}"
            )])
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_mazes")])
        
        await callback.message.edit_text(
            f"🏰 **المتاهات الفردية**\n\n"
            f"⚔️ **قوتك الحالية:** {format_number(player.power)}\n\n"
            f"🔥 **الجحيم الأبدي** - متاهة نارية بـ 100 طابق!\n"
            f"💀 كل طابق أصعب من الذي قبله\n"
            f"💎 مكافآت خبرة هائلة للشجعان\n\n"
            f"⚠️ **تحذير:** كل طابق له متطلبات قوة مختلفة!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المتاهات الفردية: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_maze_floors(callback: CallbackQuery, maze_type: str, maze_id: str):
    """عرض طوابق المتاهة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        maze_data = MAZES[maze_type][maze_id]
        
        keyboard = []
        
        # عرض أول 10 طوابق (2x5)
        floors_shown = 0
        current_row = []
        
        for floor_num in range(1, 11):
            if floor_num in maze_data["floors"]:
                floor_data = maze_data["floors"][floor_num]
                
                # فحص إذا كان اللاعب قوي بما فيه الكفاية
                if player.power >= floor_data["power_required"]:
                    emoji = "🔓"
                    callback_data = f"enter_maze_{maze_type}_{maze_id}_{floor_num}"
                else:
                    emoji = "🔒"
                    callback_data = f"locked_maze_{floor_num}_{floor_data['power_required']}"
                
                current_row.append(InlineKeyboardButton(
                    text=f"{emoji} طابق {floor_num}",
                    callback_data=callback_data
                ))
                
                floors_shown += 1
                
                # إضافة صف كل عنصرين
                if len(current_row) == 2:
                    keyboard.append(current_row)
                    current_row = []
        
        # إضافة الصف الأخير إذا كان غير مكتمل
        if current_row:
            keyboard.append(current_row)
        
        # زر التالي للمزيد من الطوابق (إذا وجدت)
        if len(maze_data["floors"]) > 10:
            keyboard.append([InlineKeyboardButton(text="➡️ الطوابق التالية", callback_data=f"maze_floors_next_{maze_type}_{maze_id}_2")])
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="mazes_single")])
        
        await callback.message.edit_text(
            f"🏰 **{maze_data['name']}**\n\n"
            f"📖 **الوصف:** {maze_data['description']}\n"
            f"⚔️ **قوتك:** {format_number(player.power)}\n\n"
            f"📋 **اختر الطابق الذي تريد دخوله:**\n\n"
            f"🔓 **مفتوح** - يمكنك دخوله\n"
            f"🔒 **مقفل** - تحتاج قوة أكبر\n\n"
            f"💡 **نصيحة:** ابدأ بالطوابق السفلى أولاً!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض طوابق المتاهة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_maze_info(callback: CallbackQuery, maze_type: str, maze_id: str, floor: int):
    """عرض معلومات طابق المتاهة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        maze_data = MAZES[maze_type][maze_id]
        floor_data = maze_data["floors"][floor]
        
        keyboard = [
            [InlineKeyboardButton(text="⚔️ دخول", callback_data=f"start_maze_{maze_type}_{maze_id}_{floor}")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data=f"maze_{maze_type}_{maze_id}")]
        ]
        
        await callback.message.edit_text(
            f"🏰 **{maze_data['name']} - طابق {floor}**\n\n"
            f"ℹ️ **معلومات الطابق:**\n"
            f"💪 القوة المطلوبة: {format_number(floor_data['power_required'])}\n"
            f"📉 خسارة الخبرة عند الخسارة: {format_number(floor_data['experience_loss'])}\n"
            f"📈 مكافأة الخبرة عند الفوز: {format_number(floor_data['experience_reward'])}\n"
            f"👹 عدد الوحوش: {floor_data['monsters']}\n"
            f"⏱️ مدة الغزو: {floor_data['duration']} دقيقة\n\n"
            f"⚔️ **قوتك الحالية:** {format_number(player.power)}\n\n"
            f"⚠️ **اقرأ المعلومات قبل الدخول!**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات المتاهة: {e}")
        await callback.answer("❌ حدث خطأ")

async def start_maze(callback: CallbackQuery, maze_type: str, maze_id: str, floor: int):
    """بدء غزو المتاهة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        # فحص إذا كان لديه متاهة نشطة
        if user_id in ACTIVE_MAZES:
            await callback.answer("❌ لديك متاهة جارية حالياً!")
            return
        
        maze_data = MAZES[maze_type][maze_id]
        floor_data = maze_data["floors"][floor]
        
        # فحص القوة المطلوبة
        if player.power < floor_data["power_required"]:
            await callback.answer(f"❌ تحتاج {format_number(floor_data['power_required'])} قوة لدخول هذا الطابق!")
            return
        
        # إنشاء متاهة نشطة
        active_maze = ActiveMaze(
            user_id=user_id,
            maze_type=maze_type,
            maze_name=maze_data["name"],
            floor=floor,
            duration_minutes=floor_data["duration"],
            monsters=floor_data["monsters"],
            power_required=floor_data["power_required"],
            experience_reward=floor_data["experience_reward"],
            experience_loss=floor_data["experience_loss"]
        )
        
        ACTIVE_MAZES[user_id] = active_maze
        
        # تحديد نتيجة المتاهة (70% نجاح)
        success = random.random() < 0.7
        
        # إنشاء تايمر للإشعار
        asyncio.create_task(maze_completion_timer(callback, active_maze, success))
        
        await callback.message.edit_text(
            f"⚔️ **دخلت متاهة '{maze_data['name']}' - طابق {floor}!**\n\n"
            f"👹 **عدد الوحوش:** {floor_data['monsters']}\n"
            f"⏱️ **مدة الغزو:** {floor_data['duration']} دقيقة\n"
            f"💎 **مكافأة النجاح:** {format_number(floor_data['experience_reward'])} خبرة\n"
            f"💀 **عقوبة الفشل:** {format_number(floor_data['experience_loss'])} خبرة\n\n"
            f"🗡️ **يتم القتال الآن...** انتظر انتهاء مدة الغزو!\n\n"
            f"⚡ سيتم إشعارك بالنتيجة بعد {floor_data['duration']} دقيقة",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⏱️ حالة المتاهة", callback_data="maze_status")
            ]])
        )
        
        await callback.answer("⚔️ بدأ الغزو!")
        
    except Exception as e:
        logging.error(f"خطأ في بدء المتاهة: {e}")
        await callback.answer("❌ حدث خطأ")

async def maze_completion_timer(callback: CallbackQuery, maze: ActiveMaze, success: bool):
    """تايمر إنهاء المتاهة"""
    try:
        # انتظار مدة المتاهة
        await asyncio.sleep(maze.duration_minutes * 60)
        
        user_id = maze.user_id
        player = GUILD_PLAYERS.get(user_id)
        
        if not player:
            return
        
        # إزالة المتاهة من القائمة النشطة
        if user_id in ACTIVE_MAZES:
            del ACTIVE_MAZES[user_id]
        
        # إضافة كولداون
        MAZE_COOLDOWN[user_id] = time.time()
        
        if success:
            # نجح في المتاهة
            player.experience += maze.experience_reward
            await player.save_to_database()
            
            result_text = (
                f"🎉 **مبروك! نجحت في المتاهة!**\n\n"
                f"🏰 **المتاهة:** {maze.maze_name} - طابق {maze.floor}\n"
                f"⚔️ **هزمت جميع الوحوش:** {maze.monsters} وحش\n"
                f"📈 **حصلت على:** {format_number(maze.experience_reward)} نقطة خبرة!\n"
                f"⭐ **خبرتك الآن:** {format_number(player.experience)}\n\n"
                f"🔓 **الطابق التالي مفتوح الآن!**\n"
                f"💎 كلما تقدمت، زادت المكافآت!"
            )
        else:
            # فشل في المتاهة
            player.experience = max(0, player.experience - maze.experience_loss)
            await player.save_to_database()
            
            result_text = (
                f"💀 **للأسف! فشلت في المتاهة!**\n\n"
                f"🏰 **المتاهة:** {maze.maze_name} - طابق {maze.floor}\n"
                f"👹 **الوحوش غلبتك!** لم تتمكن من هزيمة {maze.monsters} وحش\n"
                f"📉 **خسرت:** {format_number(maze.experience_loss)} نقطة خبرة\n"
                f"⭐ **خبرتك الآن:** {format_number(player.experience)}\n\n"
                f"💪 **لا تيأس!** قو نفسك وحاول مرة أخرى!\n"
                f"🏋️ تدرب أكثر وارفع قوتك للنجاح"
            )
        
        # إرسال النتيجة
        try:
            await callback.message.reply(result_text)
        except:
            # إذا فشل الرد، نحاول إرسال رسالة جديدة
            try:
                from aiogram import Bot
                bot = callback.bot
                await bot.send_message(user_id, result_text)
            except:
                pass
        
    except Exception as e:
        logging.error(f"خطأ في تايمر المتاهة: {e}")

async def show_active_maze_status(callback: CallbackQuery):
    """عرض حالة المتاهة النشطة"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ACTIVE_MAZES:
            await callback.answer("❌ لا توجد متاهة نشطة!")
            return
        
        maze = ACTIVE_MAZES[user_id]
        time_remaining = maze.time_remaining()
        
        if maze.is_completed():
            await callback.answer("✅ المتاهة انتهت! انتظر النتيجة...")
            return
        
        await callback.message.edit_text(
            f"⚔️ **متاهة نشطة حالياً!**\n\n"
            f"🏰 **المتاهة:** {maze.maze_name}\n"
            f"📍 **الطابق:** {maze.floor}\n"
            f"👹 **الوحوش:** {maze.monsters}\n"
            f"⏱️ **الوقت المتبقي:** {time_remaining}\n\n"
            f"🗡️ **المعركة جارية...** انتظر انتهاء الوقت!\n"
            f"📱 سيتم إشعارك بالنتيجة عند الانتهاء",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 تحديث", callback_data="maze_status"),
                InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة المتاهة: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_locked_maze(callback: CallbackQuery, floor: int, required_power: int):
    """معالجة المتاهة المقفلة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        needed_power = required_power - player.power
        
        await callback.answer(
            f"🔒 طابق {floor} مقفل!\n"
            f"💪 تحتاج {format_number(needed_power)} قوة إضافية\n"
            f"🏋️ قو نفسك أكثر!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في معالجة المتاهة المقفلة: {e}")
        await callback.answer("❌ حدث خطأ")

# تصدير الدوال المطلوبة
__all__ = [
    'show_mazes_menu',
    'show_single_mazes', 
    'show_maze_floors',
    'show_maze_info',
    'start_maze',
    'show_active_maze_status',
    'handle_locked_maze',
    'ACTIVE_MAZES'
]
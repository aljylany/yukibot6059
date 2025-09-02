"""
معالج لعبة النقابة المتخصص
Guild Game Specialized Handler
تم إنشاؤه في: 1 سبتمبر 2025
"""

import logging
import asyncio
from typing import Dict

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# استيراد جميع وحدات النقابة
from modules.guild_game import (
    start_guild_registration, handle_guild_selection, handle_gender_selection,
    handle_class_selection, show_guild_main_menu, show_personal_code,
    GUILD_PLAYERS, ACTIVE_MISSIONS, create_new_player
)
from modules.guild_database import init_guild_database, load_guild_player
from modules.guild_missions import (
    show_missions_menu, show_normal_missions, show_collect_missions,
    show_medium_missions, show_legendary_missions,
    start_mission, show_active_mission_status, handle_locked_mission
)
from modules.guild_shop import (
    show_shop_menu, show_weapons_shop, show_badges_shop, show_titles_shop,
    show_potions_shop, show_rings_shop, show_animals_shop,
    buy_item, show_inventory, handle_cant_buy
)
from modules.guild_upgrade import (
    show_upgrade_menu, level_up_player, show_advanced_classes,
    change_advanced_class, handle_current_class
)
from modules.guild_mazes import (
    show_mazes_menu, show_single_mazes, show_maze_floors, show_maze_info,
    start_maze, show_active_maze_status, handle_locked_maze
)
from utils.decorators import user_required

# إنشاء router متخصص للنقابة
guild_router = Router()

# إزالة نظام التحقق من المستخدم للسماح للجميع بالتفاعل

async def initialize_guild_system():
    """تهيئة نظام النقابة"""
    try:
        await init_guild_database()
        logging.info("✅ تم تهيئة نظام النقابة بنجاح")
        return True
    except Exception as e:
        logging.error(f"❌ خطأ في تهيئة نظام النقابة: {e}")
        return False

# ===== أوامر البدء =====
@guild_router.message(Command("guild"))
@user_required
async def guild_command(message: Message, state: FSMContext):
    """أمر بدء لعبة النقابة الرسمي"""
    try:
        await start_guild_registration(message, state)
    except Exception as e:
        logging.error(f"خطأ في أمر النقابة: {e}")
        await message.reply("❌ حدث خطأ في بدء لعبة النقابة")

# ===== الأوامر النصية المتخصصة للنقابة =====
@guild_router.message(F.text.in_(["نقابة", "لعبة النقابة", "انضمام نقابة"]))
@user_required
async def guild_text_command(message: Message, state: FSMContext):
    """أوامر نصية لبدء النقابة"""
    try:
        await start_guild_registration(message, state)
    except Exception as e:
        logging.error(f"خطأ في أمر النقابة النصي: {e}")
        await message.reply("❌ حدث خطأ في بدء لعبة النقابة")

@guild_router.message(F.text.in_(["مهام", "مهمة", "المهام"]))
@user_required  
async def guild_missions_command(message: Message, state: FSMContext):
    """أمر عرض مهام النقابة"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        
        # إذا لم يكن مسجلاً في النقابة، قم بالتسجيل
        if user_id not in GUILD_PLAYERS:
            # تحميل البيانات أو إنشاء لاعب جديد
            player = await load_guild_player(user_id)
            if not player:
                # إنشاء لاعب جديد
                from modules.guild_game import create_new_player
                await create_new_player(user_id, message.from_user.first_name or "لاعب")
        
        # عرض قائمة المهام مباشرة
        from modules.guild_missions import format_number
        
        keyboard = [
            [InlineKeyboardButton(text="⭐ عادية", callback_data="missions_normal")],
            [InlineKeyboardButton(text="⚔️ متوسطة", callback_data="missions_medium")],
            [InlineKeyboardButton(text="🔮 متقدمة", callback_data="missions_advanced")],
            [InlineKeyboardButton(text="🔥 أسطورية", callback_data="missions_legendary")],
            [InlineKeyboardButton(text="💎 جمع", callback_data="missions_collect")],
            [InlineKeyboardButton(text="👹 قتل وحوش", callback_data="missions_kill")],
            [InlineKeyboardButton(text="🎮 القائمة الرئيسية", callback_data="guild_main_menu")]
        ]
        
        player = GUILD_PLAYERS[user_id]
        await message.reply(
            f"📋 **اختر فئة المهمة:**\n\n"
            f"👤 **اللاعب:** {player.name}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"⚔️ **القوة:** {format_number(player.power)}\n\n"
            f"⭐ **عادية** - مهام بسيطة ومربحة\n"
            f"⚔️ **متوسطة** - مهام أكثر صعوبة وخطراً\n"
            f"🔮 **متقدمة** - مهام للمحاربين المتقدمين\n"
            f"🔥 **أسطورية** - مهام للمحاربين الأقوياء\n"
            f"💎 **جمع** - مهام جمع الموارد الثمينة\n"
            f"👹 **قتل وحوش** - مهام قتال الوحوش",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        logging.error(f"خطأ في أمر المهام: {e}")

@guild_router.message(F.text.in_(["متجر", "متجر النقابة", "شراء"]))
@user_required
async def guild_shop_command(message: Message, state: FSMContext):
    """أمر عرض متجر النقابة"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        
        # إذا لم يكن مسجلاً في النقابة، قم بالتسجيل
        if user_id not in GUILD_PLAYERS:
            player = await load_guild_player(user_id)
            if not player:
                from modules.guild_game import create_new_player
                await create_new_player(user_id, message.from_user.first_name or "لاعب")
        
        # عرض قائمة المتجر مباشرة
        from modules.guild_missions import format_number
        
        keyboard = [
            [InlineKeyboardButton(text="⚔️ أسلحة", callback_data="shop_weapons")],
            [InlineKeyboardButton(text="🏅 أوسمة", callback_data="shop_badges")],
            [InlineKeyboardButton(text="👑 ألقاب", callback_data="shop_titles")],
            [InlineKeyboardButton(text="🧪 جرعات", callback_data="shop_potions")],
            [InlineKeyboardButton(text="💍 خواتم", callback_data="shop_rings")],
            [InlineKeyboardButton(text="🐾 حيوانات", callback_data="shop_animals")],
            [InlineKeyboardButton(text="🎒 حقيبتي", callback_data="shop_inventory")],
            [InlineKeyboardButton(text="🎮 القائمة الرئيسية", callback_data="guild_main_menu")]
        ]
        
        player = GUILD_PLAYERS[user_id]
        await message.reply(
            f"🛒 **متجر النقابة**\n\n"
            f"👤 **اللاعب:** {player.name}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"⚔️ **القوة:** {format_number(player.power)}\n\n"
            f"🛍️ **فئات المتجر:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
    except Exception as e:
        logging.error(f"خطأ في أمر المتجر: {e}")

@guild_router.message(F.text.in_(["ترقية", "مستوى", "ترقية مستوى"]))
@user_required
async def guild_upgrade_command(message: Message, state: FSMContext):
    """أمر ترقية المستوى"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        if user_id in GUILD_PLAYERS:
            await message.reply("⚡ **ترقية المستوى**\n\nاستخدم أمر /guild للوصول للقائمة الكاملة")
        else:
            await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
    except Exception as e:
        logging.error(f"خطأ في أمر الترقية: {e}")

@guild_router.message(F.text.in_(["رمزي", "كودي", "رمز"]))
@user_required
async def guild_code_command(message: Message, state: FSMContext):
    """أمر عرض الرمز الشخصي"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        if user_id in GUILD_PLAYERS:
            player = GUILD_PLAYERS[user_id]
            await message.reply(f"🆔 **رمز {player.name}: {player.personal_code} - مفتاح هويته!**")
        else:
            await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
    except Exception as e:
        logging.error(f"خطأ في أمر الرمز: {e}")

@guild_router.message(F.text.in_(["معلوماتي", "حالة", "ملفي الشخصي"]))
@user_required
async def guild_info_command(message: Message, state: FSMContext):
    """أمر عرض معلومات اللاعب"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        if user_id in GUILD_PLAYERS:
            await show_guild_main_menu(message, state)
        else:
            await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
    except Exception as e:
        logging.error(f"خطأ في أمر المعلومات: {e}")

# ===== معالجة Callbacks النقابة =====
@guild_router.callback_query(lambda c: c.data and (
    c.data.startswith("guild_") or 
    c.data.startswith("missions_") or 
    c.data.startswith("shop_") or 
    c.data.startswith("buy_") or 
    c.data.startswith("change_class_") or 
    c.data.startswith("gender_select_") or 
    c.data.startswith("class_select_") or 
    c.data.startswith("mazes_") or
    c.data.startswith("maze_") or
    c.data.startswith("enter_maze_") or
    c.data.startswith("start_maze_") or
    c.data.startswith("locked_maze_") or
    c.data.startswith("inventory") or
    c.data.startswith("cant_buy_") or
    c.data == "current_class" or
    c.data == "maze_status" or
    c.data == "mission_status"
))
async def handle_guild_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالجة callbacks النقابة المتخصصة"""
    try:
        data = callback.data
        
        # التحقق من وجود البيانات
        if not data:
            await callback.answer("❌ خطأ في البيانات")
            return
        
        # معالجة اختيار النقابة
        if data.startswith("guild_select_"):
            await handle_guild_selection(callback, state)
        
        # معالجة اختيار الجنس
        elif data.startswith("gender_select_"):
            await handle_gender_selection(callback, state)
        
        # معالجة اختيار الفئة
        elif data.startswith("class_select_"):
            await handle_class_selection(callback, state)
        
        # القوائم الرئيسية
        elif data.startswith("guild_main_menu:"):
            user_id_from_data = int(data.split(":")[1])
            if callback.message and hasattr(callback.message, 'chat') and hasattr(callback.message, 'from_user'):
                from aiogram.types import Message
                if isinstance(callback.message, Message):
                    await show_guild_main_menu(callback.message, state)
                else:
                    await callback.answer("✅ تم فتح القائمة الرئيسية للنقابة")
            else:
                await callback.answer("✅ تم فتح القائمة الرئيسية للنقابة")
        
        elif data == "guild_main_menu":
            # معالجة زر الرجوع بدون user_id
            if callback.message and hasattr(callback.message, 'chat') and hasattr(callback.message, 'from_user'):
                from aiogram.types import Message
                if isinstance(callback.message, Message):
                    await show_guild_main_menu(callback.message, state)
                else:
                    await callback.answer("✅ تم فتح القائمة الرئيسية للنقابة")
            else:
                await callback.answer("✅ تم فتح القائمة الرئيسية للنقابة")
        
        elif data == "guild_code":
            await show_personal_code(callback)
        
        # نظام المهام - مع دعم callbacks بـ user_id وبدونه
        elif data == "guild_missions":
            await show_missions_menu(callback)
        
        elif data == "missions_normal" or data.startswith("missions_normal:"):
            await show_normal_missions(callback)
        
        elif data == "missions_collect" or data.startswith("missions_collect:"):
            await show_collect_missions(callback)
        
        elif data == "missions_medium" or data.startswith("missions_medium:"):
            await show_medium_missions(callback)
        
        elif data == "missions_advanced" or data.startswith("missions_advanced:"):
            from modules.guild_missions import show_advanced_missions
            await show_advanced_missions(callback)
        
        elif data == "missions_legendary" or data.startswith("missions_legendary:"):
            await show_legendary_missions(callback)
        
        elif data == "missions_kill" or data.startswith("missions_kill:"):
            from modules.guild_missions import show_kill_missions
            await show_kill_missions(callback)
        
        elif data.startswith("start_mission_"):
            await start_mission(callback)
        
        elif data == "mission_status":
            await show_active_mission_status(callback)
        
        elif data.startswith("locked_mission_"):
            await handle_locked_mission(callback)
        
        # نظام المتجر - مع دعم callbacks بـ user_id وبدونه
        elif data == "guild_shop":
            await show_shop_menu(callback)
        
        elif data == "shop_weapons" or data.startswith("shop_weapons:"):
            await show_weapons_shop(callback)
        
        elif data == "shop_badges" or data.startswith("shop_badges:"):
            await show_badges_shop(callback)
        
        elif data == "shop_titles" or data.startswith("shop_titles:"):
            await show_titles_shop(callback)
        
        elif data == "shop_potions" or data.startswith("shop_potions:"):
            await show_potions_shop(callback)
        
        elif data == "shop_rings" or data.startswith("shop_rings:"):
            await show_rings_shop(callback)
        
        elif data == "shop_animals" or data.startswith("shop_animals:"):
            await show_animals_shop(callback)
        
        elif data == "shop_inventory" or data.startswith("inventory"):
            await show_inventory(callback)
        
        elif data.startswith("buy_"):
            await buy_item(callback)
        
        elif data.startswith("cant_buy_"):
            await handle_cant_buy(callback)
        
        # نظام المتاهات
        elif data == "guild_mazes":
            await show_mazes_menu(callback)
        
        elif data == "mazes_single":
            await show_single_mazes(callback)
        
        elif data.startswith("maze_single_"):
            maze_id = data.split("_")[2]
            await show_maze_floors(callback, "single", maze_id)
        
        elif data.startswith("enter_maze_"):
            parts = data.split("_")
            maze_type = parts[2]
            maze_id = parts[3]
            floor = int(parts[4])
            await show_maze_info(callback, maze_type, maze_id, floor)
        
        elif data.startswith("start_maze_"):
            parts = data.split("_")
            maze_type = parts[2]
            maze_id = parts[3]
            floor = int(parts[4])
            await start_maze(callback, maze_type, maze_id, floor)
        
        elif data == "maze_status":
            await show_active_maze_status(callback)
        
        elif data.startswith("locked_maze_"):
            parts = data.split("_")
            floor = int(parts[2])
            required_power = int(parts[3])
            await handle_locked_maze(callback, floor, required_power)
        
        # نظام الترقية
        elif data == "guild_upgrade":
            await show_upgrade_menu(callback)
        
        elif data == "guild_level_up":
            await level_up_player(callback)
        
        elif data == "guild_advanced_class":
            await show_advanced_classes(callback)
        
        elif data.startswith("change_class_"):
            await change_advanced_class(callback)
        
        elif data == "current_class":
            await handle_current_class(callback)
        
        # تغيير الفئة العادية
        elif data == "guild_change_class":
            await callback.answer("🔧 هذه الميزة ستكون متاحة قريباً!")
        
        # معالجة callbacks قديمة بـ user_id (توافق للخلف)
        elif ":" in data:
            # استخراج الأمر الأساسي
            base_data = data.split(":")[0]
            # إعادة المعالجة بدون user_id بتغيير data مؤقتاً
            original_data = callback.data
            callback.data = base_data
            # معالجة recursive لنفس الدالة
            await handle_guild_callback(callback, state)
            callback.data = original_data  # إرجاع القيمة الأصلية
            return
        
        # callbacks غير معروفة للنقابة فقط
        else:
            await callback.answer("❓ أمر نقابة غير معروف")
    
    except Exception as e:
        logging.error(f"خطأ في معالجة callback النقابة: {e}")
        await callback.answer("❌ حدث خطأ")

async def load_existing_players():
    """تحميل اللاعبين الموجودين من قاعدة البيانات"""
    try:
        # هذه دالة مساعدة لتحميل البيانات عند إعادة تشغيل البوت
        logging.info("🔄 نظام تحميل اللاعبين جاهز")
    except Exception as e:
        logging.error(f"خطأ في تحميل اللاعبين: {e}")

# تصدير العناصر المطلوبة
__all__ = [
    'guild_router',
    'initialize_guild_system',
    'load_existing_players'
]
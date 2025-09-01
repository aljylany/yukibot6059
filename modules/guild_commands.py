"""
أوامر النقابة - ربط مع النظام الرئيسي
Guild Commands - Integration with Main System
"""

import logging
import asyncio
from typing import Dict

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

# استيراد جميع وحدات النقابة
from modules.guild_game import (
    start_guild_registration, handle_guild_selection, handle_gender_selection,
    handle_class_selection, show_guild_main_menu, show_personal_code,
    GUILD_PLAYERS, ACTIVE_MISSIONS
)
from modules.guild_database import init_guild_database, load_guild_player
from modules.guild_missions import (
    show_missions_menu, show_normal_missions, show_collect_missions,
    start_mission, show_active_mission_status, handle_locked_mission
)
from modules.guild_shop import (
    show_shop_menu, show_weapons_shop, show_badges_shop, show_titles_shop,
    buy_item, show_inventory, handle_cant_buy
)
from modules.guild_upgrade import (
    show_upgrade_menu, level_up_player, show_advanced_classes,
    change_advanced_class, handle_current_class
)
from utils.decorators import user_required

# إنشاء router للنقابة
guild_router = Router()

async def initialize_guild_system():
    """تهيئة نظام النقابة"""
    try:
        await init_guild_database()
        logging.info("✅ تم تهيئة نظام النقابة بنجاح")
        return True
    except Exception as e:
        logging.error(f"❌ خطأ في تهيئة نظام النقابة: {e}")
        return False

# أوامر البدء
@guild_router.message(Command("guild"))
@user_required
async def guild_command(message: Message, state: FSMContext):
    """أمر بدء لعبة النقابة"""
    try:
        await start_guild_registration(message, state)
    except Exception as e:
        logging.error(f"خطأ في أمر النقابة: {e}")
        await message.reply("❌ حدث خطأ في بدء لعبة النقابة")

# معالجة الرسائل النصية
@guild_router.message()
async def handle_guild_text_commands(message: Message, state: FSMContext):
    """معالجة الأوامر النصية للنقابة"""
    try:
        text = message.text.lower().strip()
        
        if text in ["نقابة", "لعبة النقابة", "انضمام نقابة"]:
            await start_guild_registration(message, state)
        elif text in ["مهام", "مهمة", "المهام"]:
            user_id = message.from_user.id
            if user_id in GUILD_PLAYERS:
                # محاكاة callback للمهام
                fake_callback = type('obj', (object,), {
                    'from_user': message.from_user,
                    'message': message,
                    'answer': lambda text="", show_alert=False: asyncio.create_task(message.reply("تم!"))
                })
                await show_missions_menu(fake_callback)
            else:
                await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
        elif text in ["متجر", "متجر النقابة", "شراء"]:
            user_id = message.from_user.id
            if user_id in GUILD_PLAYERS:
                fake_callback = type('obj', (object,), {
                    'from_user': message.from_user,
                    'message': message,
                    'answer': lambda text="", show_alert=False: asyncio.create_task(message.reply("تم!"))
                })
                await show_shop_menu(fake_callback)
            else:
                await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
        elif text in ["رمزي", "كودي", "رمز"]:
            user_id = message.from_user.id
            if user_id in GUILD_PLAYERS:
                player = GUILD_PLAYERS[user_id]
                await message.reply(f"🆔 **رمز {player.name}: {player.personal_code} - مفتاح هويته!**")
            else:
                await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
        elif text in ["ترقية", "مستوى", "ترقية مستوى"]:
            user_id = message.from_user.id
            if user_id in GUILD_PLAYERS:
                fake_callback = type('obj', (object,), {
                    'from_user': message.from_user,
                    'message': message,
                    'answer': lambda text="", show_alert=False: asyncio.create_task(message.reply("تم!"))
                })
                await show_upgrade_menu(fake_callback)
            else:
                await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
        elif text in ["معلوماتي", "حالة", "ملفي الشخصي"]:
            user_id = message.from_user.id
            if user_id in GUILD_PLAYERS:
                fake_callback = type('obj', (object,), {
                    'from_user': message.from_user,
                    'message': message,
                    'answer': lambda text="", show_alert=False: asyncio.create_task(message.reply("تم!"))
                })
                await show_guild_main_menu(message, state)
            else:
                await message.reply("❌ يجب التسجيل في النقابة أولاً! اكتب: نقابة")
    except Exception as e:
        logging.error(f"خطأ في معالجة أوامر النقابة النصية: {e}")

# معالجة callbacks النقابة فقط
@guild_router.callback_query(lambda c: c.data and (c.data.startswith("guild_") or c.data.startswith("missions_") or c.data.startswith("shop_") or c.data.startswith("buy_") or c.data.startswith("change_class_") or c.data.startswith("gender_select_") or c.data.startswith("class_select_") or c.data == "current_class"))
async def handle_guild_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالجة callbacks النقابة فقط"""
    try:
        data = callback.data
        
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
        elif data == "guild_main_menu":
            await show_guild_main_menu(callback.message, state)
            await callback.answer()
        
        elif data == "guild_code":
            await show_personal_code(callback)
        
        # نظام المهام
        elif data == "guild_missions":
            await show_missions_menu(callback)
        
        elif data == "missions_normal":
            await show_normal_missions(callback)
        
        elif data == "missions_collect":
            await show_collect_missions(callback)
        
        elif data.startswith("start_mission_"):
            await start_mission(callback)
        
        elif data == "mission_status":
            await show_active_mission_status(callback)
        
        elif data.startswith("locked_mission_"):
            await handle_locked_mission(callback)
        
        # نظام المتجر
        elif data == "guild_shop":
            await show_shop_menu(callback)
        
        elif data == "shop_weapons":
            await show_weapons_shop(callback)
        
        elif data == "shop_badges":
            await show_badges_shop(callback)
        
        elif data == "shop_titles":
            await show_titles_shop(callback)
        
        elif data == "shop_inventory":
            await show_inventory(callback)
        
        elif data.startswith("buy_"):
            await buy_item(callback)
        
        elif data.startswith("cant_buy_"):
            await handle_cant_buy(callback)
        
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
        # في الوقت الحالي، البيانات تُحفظ في قاعدة البيانات فقط
        # وتُحمل عند الحاجة، لا نحتاج لتحميل كل شيء في الذاكرة
        logging.info("🔄 نظام تحميل اللاعبين جاهز")
    except Exception as e:
        logging.error(f"خطأ في تحميل اللاعبين: {e}")

# تصدير العناصر المطلوبة
__all__ = [
    'guild_router',
    'initialize_guild_system',
    'load_existing_players'
]
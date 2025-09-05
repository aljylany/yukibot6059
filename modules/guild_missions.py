"""
نظام مهام النقابة
Guild Missions System
"""

import logging
import time
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext

from modules.guild_game import GUILD_PLAYERS, ACTIVE_MISSIONS, MISSIONS, ActiveMission, GuildPlayer
from modules.guild_database import save_active_mission, complete_mission, get_active_mission, update_guild_stats, save_guild_player
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number

# دالة مساعدة للتعامل مع callback.message بأمان
async def safe_edit_text(callback: CallbackQuery, text: str, reply_markup=None):
    """تعديل النص بشكل آمن مع التحقق من callback.message"""
    try:
        if (callback.message and 
            hasattr(callback.message, 'edit_text') and 
            callback.message.__class__.__name__ == 'Message'):
            await callback.message.edit_text(text, reply_markup=reply_markup)
        else:
            # إذا لم يكن edit_text متاحاً، استخدم answer مع رسالة جديدة
            await callback.answer(text[:200] + "..." if len(text) > 200 else text)
    except Exception as e:
        logging.error(f"خطأ في تعديل النص: {e}")
        await callback.answer("❌ حدث خطأ في التحديث")

# كولداون المهام (30 ثانية بين المهام)
MISSION_COOLDOWN: Dict[int, float] = {}
COOLDOWN_DURATION = 30

# تخزين المؤقتات النشطة
ACTIVE_TIMERS: Dict[int, asyncio.Task] = {}

async def show_missions_menu(callback: CallbackQuery):
    """عرض قائمة المهام"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        # فحص المهمة النشطة
        if user_id in ACTIVE_MISSIONS:
            await show_active_mission_status(callback)
            return
        
        # فحص الكولداون
        current_time = time.time()
        if user_id in MISSION_COOLDOWN:
            time_passed = current_time - MISSION_COOLDOWN[user_id]
            if time_passed < COOLDOWN_DURATION:
                remaining = int(COOLDOWN_DURATION - time_passed)
                await safe_edit_text(
                    callback,
                    f"⏳ **انتظر {remaining} ثانية قبل بدء مهمة جديدة!**",
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
                    ]])
                )
                await callback.answer()
                return
        
        player = GUILD_PLAYERS[user_id]
        
        keyboard = [
            [InlineKeyboardButton(text="⭐ عادية", callback_data="missions_normal")],
            [InlineKeyboardButton(text="⚔️ متوسطة", callback_data="missions_medium")],
            [InlineKeyboardButton(text="🎯 متقدمة", callback_data="missions_advanced")],
            [InlineKeyboardButton(text="🔥 أسطورية", callback_data="missions_legendary")],
            [InlineKeyboardButton(text="💎 جمع", callback_data="missions_collect")],
            [InlineKeyboardButton(text="👹 قتل وحوش", callback_data="missions_kill")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")]
        ]
        
        await safe_edit_text(
            callback,
            f"📋 **اختر فئة المهمة:**\n\n"
            f"👤 **اللاعب:** {player.name}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"⚔️ **القوة:** {format_number(player.power)}\n\n"
            f"⭐ **عادية** - مهام بسيطة ومربحة\n"
            f"⚔️ **متوسطة** - مهام أكثر صعوبة وخطراً\n"
            f"🎯 **متقدمة** - مهام للمحاربين المتمرسين\n"
            f"🔥 **أسطورية** - مهام للمحاربين الأقوياء\n"
            f"💎 **جمع** - مهام جمع الموارد الثمينة\n"
            f"👹 **قتل وحوش** - مهام قتال الوحوش الشرسة",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة المهام: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_normal_missions(callback: CallbackQuery):
    """عرض المهام العادية"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "⭐ **المهام العادية:**\n\n"
        
        for mission_id, mission_data in MISSIONS["normal"].items():
            # فحص متطلبات المستوى
            if player.level >= mission_data["required_level"]:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_normal_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']} (مستوى {mission_data['required_level']})"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            status = "✅ متاح" if player.level >= mission_data["required_level"] else f"🔒 يحتاج مستوى {mission_data['required_level']}"
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المهام العادية: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_collect_missions(callback: CallbackQuery):
    """عرض مهام الجمع"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "💎 **مهام الجمع:**\n\n"
        
        for mission_id, mission_data in MISSIONS["collect"].items():
            # فحص متطلبات المستوى والقوة
            level_ok = player.level >= mission_data["required_level"]
            power_ok = player.power >= mission_data["power_requirement"]
            
            if level_ok and power_ok:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_collect_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']}"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            if level_ok and power_ok:
                status = "✅ متاح"
            elif not level_ok:
                status = f"🔒 يحتاج مستوى {mission_data['required_level']}"
            else:
                status = f"🔒 يحتاج قوة {format_number(mission_data['power_requirement'])}"
            
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"💪 القوة المطلوبة: {format_number(mission_data['power_requirement'])}\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض مهام الجمع: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_medium_missions(callback: CallbackQuery):
    """عرض المهام المتوسطة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "⚔️ **المهام المتوسطة:**\n\n"
        
        for mission_id, mission_data in MISSIONS["medium"].items():
            # فحص متطلبات المستوى والقوة
            level_met = player.level >= mission_data["required_level"]
            power_met = player.power >= mission_data["power_requirement"]
            available = level_met and power_met
            
            if available:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_medium_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']}"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            if available:
                status = "✅ متاح"
            elif not level_met:
                status = f"🔒 يحتاج مستوى {mission_data['required_level']}"
            else:
                status = f"🔒 يحتاج قوة {format_number(mission_data['power_requirement'])}"
                
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المهام المتوسطة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_legendary_missions(callback: CallbackQuery):
    """عرض المهام الأسطورية"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "🔥 **المهام الأسطورية:**\n\n"
        
        for mission_id, mission_data in MISSIONS["legendary"].items():
            # فحص متطلبات المستوى والقوة
            level_met = player.level >= mission_data["required_level"]
            power_met = player.power >= mission_data["power_requirement"]
            available = level_met and power_met
            
            if available:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_legendary_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']}"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            if available:
                status = "✅ متاح"
            elif not level_met:
                status = f"🔒 يحتاج مستوى {mission_data['required_level']}"
            else:
                status = f"🔒 يحتاج قوة {format_number(mission_data['power_requirement'])}"
                
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المهام الأسطورية: {e}")
        await callback.answer("❌ حدث خطأ")

async def start_mission(callback: CallbackQuery):
    """بدء مهمة جديدة"""
    try:
        user_id = callback.from_user.id
        logging.info(f"🎯 START MISSION DEBUG: بدء مهمة للمستخدم {user_id}, callback_data: {callback.data}")
        
        # تحليل البيانات
        parts = callback.data.split("_")
        logging.info(f"🔍 PARTS DEBUG: {parts}")
        mission_type = parts[2]  # normal أو collect
        mission_id = parts[3]
        logging.info(f"🎯 MISSION DEBUG: نوع المهمة: {mission_type}, معرف المهمة: {mission_id}")
        
        if user_id not in GUILD_PLAYERS:
            logging.info(f"🚫 MISSION ERROR: المستخدم {user_id} غير مسجل في النقابة!")
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        if user_id in ACTIVE_MISSIONS:
            await callback.answer("⚠️ لديك مهمة نشطة بالفعل!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        # الحصول على بيانات المهمة
        if mission_type not in MISSIONS or mission_id not in MISSIONS[mission_type]:
            await callback.answer("❌ مهمة غير موجودة!")
            return
        
        mission_data = MISSIONS[mission_type][mission_id]
        
        # فحص المتطلبات
        if player.level < mission_data["required_level"]:
            await callback.answer(f"🔒 تحتاج مستوى {mission_data['required_level']}!")
            return
        
        if mission_type == "collect" and player.power < mission_data["power_requirement"]:
            await callback.answer(f"🔒 تحتاج قوة {format_number(mission_data['power_requirement'])}!")
            return
        
        # إنشاء المهمة النشطة
        active_mission = ActiveMission(
            mission_id=mission_id,
            mission_name=mission_data["name"],
            mission_type=mission_type,
            duration_minutes=mission_data["duration"],
            experience_reward=mission_data["experience"],
            money_reward=mission_data["money"],
            start_time=datetime.now()
        )
        
        # حفظ المهمة
        ACTIVE_MISSIONS[user_id] = active_mission
        MISSION_COOLDOWN[user_id] = time.time()
        
        # حفظ في قاعدة البيانات
        await save_active_mission({
            'user_id': user_id,
            'mission_id': mission_id,
            'mission_name': mission_data["name"],
            'mission_type': mission_type,
            'duration_minutes': mission_data["duration"],
            'experience_reward': mission_data["experience"],
            'money_reward': mission_data["money"],
            'start_time': datetime.now()
        })
        
        # بدء المؤقت (فقط إذا كان callback.message صالح)
        if (callback.message and 
            callback.message.__class__.__name__ == 'Message'):
            timer_task = asyncio.create_task(mission_timer(user_id, callback.message))
            ACTIVE_TIMERS[user_id] = timer_task
        
        await safe_edit_text(
            callback,
            f"⚡ **بدأت تنفيذ مهمة '{mission_data['name']}'!**\n\n"
            f"📝 **الوصف:** {mission_data['description']}\n"
            f"⏱️ **المدة:** {mission_data['duration']} دقيقة\n"
            f"⭐ **مكافأة الخبرة:** {format_number(mission_data['experience'])}\n"
            f"💰 **مكافأة المال:** {format_number(mission_data['money'])}$\n\n"
            f"🕐 **سيتم إشعارك عند انتهاء المهمة...**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="📊 حالة المهمة", callback_data="mission_status")
            ], [
                InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer("⚡ تم بدء المهمة!")
        
    except Exception as e:
        logging.error(f"خطأ في بدء المهمة: {e}")
        await callback.answer("❌ حدث خطأ في بدء المهمة")

async def show_active_mission_status(callback: CallbackQuery):
    """عرض حالة المهمة النشطة"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in ACTIVE_MISSIONS:
            await callback.answer("❌ لا توجد مهمة نشطة!")
            return
        
        mission = ACTIVE_MISSIONS[user_id]
        
        if mission.is_completed():
            # استخدام callback بدلاً من callback.message للإنهاء
            if (callback.message and 
                callback.message.__class__.__name__ == 'Message'):
                await complete_active_mission(user_id, callback.message)
            return
        
        time_remaining = mission.time_remaining()
        progress_percent = ((datetime.now() - mission.start_time).total_seconds() / (mission.duration_minutes * 60)) * 100
        progress_percent = min(progress_percent, 100)
        
        # شريط التقدم
        progress_bar = "🟩" * int(progress_percent // 10) + "⬜" * (10 - int(progress_percent // 10))
        
        await safe_edit_text(
            callback,
            f"📊 **حالة المهمة النشطة:**\n\n"
            f"🎯 **المهمة:** {mission.mission_name}\n"
            f"⏱️ **الوقت المتبقي:** {time_remaining}\n"
            f"📈 **التقدم:** {progress_percent:.1f}%\n"
            f"{progress_bar}\n\n"
            f"⭐ **مكافأة الخبرة:** {format_number(mission.experience_reward)}\n"
            f"💰 **مكافأة المال:** {format_number(mission.money_reward)}$\n\n"
            f"⏳ **يرجى الانتظار حتى انتهاء المهمة...**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔄 تحديث", callback_data="mission_status")
            ], [
                InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة المهمة: {e}")
        await callback.answer("❌ حدث خطأ")

async def mission_timer(user_id: int, message: Message):
    """مؤقت المهمة"""
    try:
        if user_id not in ACTIVE_MISSIONS:
            return
        
        mission = ACTIVE_MISSIONS[user_id]
        
        # انتظار انتهاء المهمة
        await asyncio.sleep(mission.duration_minutes * 60)
        
        # التحقق من أن المهمة ما زالت نشطة
        if user_id in ACTIVE_MISSIONS:
            await complete_active_mission(user_id, message)
        
    except asyncio.CancelledError:
        logging.info(f"تم إلغاء مؤقت المهمة للمستخدم {user_id}")
    except Exception as e:
        logging.error(f"خطأ في مؤقت المهمة: {e}")

async def complete_active_mission(user_id: int, message: Message):
    """إنهاء المهمة النشطة"""
    try:
        if user_id not in ACTIVE_MISSIONS:
            return
        
        mission = ACTIVE_MISSIONS[user_id]
        player = GUILD_PLAYERS[user_id]
        
        # إضافة المكافآت
        old_level = player.level
        player.experience += mission.experience_reward
        
        # فحص الترقية
        level_ups = 0
        while player.can_level_up():
            if player.level_up():
                level_ups += 1
        
        # تحديث المال
        user_data = await get_or_create_user(user_id, player.username, player.name)
        if user_data:
            new_balance = user_data.get('balance', 0) + mission.money_reward
            await update_user_balance(user_id, new_balance)
            await add_transaction(user_id, "مكافأة مهمة", mission.money_reward, f"مكافأة مهمة: {mission.mission_name}")
        
        # حفظ بيانات اللاعب المحدثة
        await save_guild_player({
            'user_id': player.user_id,
            'username': player.username,
            'name': player.name,
            'guild': player.guild,
            'gender': player.gender,
            'character_class': player.character_class,
            'advanced_class': player.advanced_class,
            'level': player.level,
            'power': player.power,
            'experience': player.experience,
            'weapon': player.weapon,
            'badge': player.badge,
            'title': player.title,
            'potion': player.potion,
            'ring': player.ring,
            'animal': player.animal,
            'personal_code': player.personal_code
        })
        
        # تحديث الإحصائيات
        await update_guild_stats(user_id, "missions_completed", 1)
        await update_guild_stats(user_id, "experience_gained", mission.experience_reward)
        await update_guild_stats(user_id, "money_earned", mission.money_reward)
        if level_ups > 0:
            await update_guild_stats(user_id, "level_ups", level_ups)
        
        # إنهاء المهمة في قاعدة البيانات
        await complete_mission(user_id, mission.mission_id)
        
        # إزالة المهمة من الذاكرة
        del ACTIVE_MISSIONS[user_id]
        if user_id in ACTIVE_TIMERS:
            ACTIVE_TIMERS[user_id].cancel()
            del ACTIVE_TIMERS[user_id]
        
        # رسالة الإنجاز
        completion_text = (
            f"🎉 **مبروك!**\n\n"
            f"✅ **أكملت مهمة '{mission.mission_name}' بنجاح!**\n\n"
            f"🎁 **المكافآت:**\n"
            f"⭐ الخبرة: +{format_number(mission.experience_reward)}\n"
            f"💰 المال: +{format_number(mission.money_reward)}$\n"
        )
        
        if level_ups > 0:
            completion_text += f"🆙 **ترقية المستوى:** {old_level} ← {player.level} (+{level_ups} مستوى)\n"
            completion_text += f"⚔️ **قوة جديدة:** {format_number(player.power)}\n"
        
        completion_text += f"\n🏅 **مستواك الحالي:** {player.level}\n"
        completion_text += f"⭐ **خبرتك:** {format_number(player.experience)}/{format_number(player.get_experience_for_next_level())}\n"
        
        try:
            await message.reply(
                completion_text,
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🎯 مهمة جديدة", callback_data="guild_missions")
                ], [
                    InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="guild_main_menu")
                ]])
            )
        except:
            # إذا فشل الرد، نرسل رسالة جديدة
            await message.answer(completion_text)
        
    except Exception as e:
        logging.error(f"خطأ في إنهاء المهمة: {e}")

async def show_advanced_missions(callback: CallbackQuery):
    """عرض المهام المتقدمة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "🎯 **المهام المتقدمة:**\n\n"
        
        # مهام متقدمة (بين المتوسطة والأسطورية)
        advanced_missions = {
            "elite_exploration": {
                "name": "🏛️ استكشاف المعبد النخبوي",
                "description": "استكشف المعابد المخفية بحثاً عن الكنوز",
                "duration": 45,
                "experience": 2500,
                "money": 3500,
                "required_level": 15,
                "power_requirement": 2500
            },
            "dragon_hunt": {
                "name": "🐉 صيد التنين الصغير",
                "description": "اقتل التنانين الصغيرة واحصل على مكافآت ثمينة",
                "duration": 60,
                "experience": 3500,
                "money": 5000,
                "required_level": 20,
                "power_requirement": 3500
            }
        }
        
        for mission_id, mission_data in advanced_missions.items():
            # فحص متطلبات المستوى والقوة
            level_met = player.level >= mission_data["required_level"]
            power_met = player.power >= mission_data["power_requirement"]
            available = level_met and power_met
            
            if available:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_advanced_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']}"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            if available:
                status = "✅ متاح"
            elif not level_met:
                status = f"🔒 يحتاج مستوى {mission_data['required_level']}"
            else:
                status = f"🔒 يحتاج قوة {format_number(mission_data['power_requirement'])}"
                
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المهام المتقدمة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_kill_missions(callback: CallbackQuery):
    """عرض مهام قتل الوحوش"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        missions_text = "👹 **مهام قتل الوحوش:**\n\n"
        
        # مهام قتل الوحوش
        kill_missions = {
            "goblin_slayer": {
                "name": "👺 إبادة الغوبلن",
                "description": "اقتل مجموعة من الغوبلن المؤذيين",
                "duration": 25,
                "experience": 1200,
                "money": 1800,
                "required_level": 8,
                "power_requirement": 1200
            },
            "orc_destroyer": {
                "name": "💀 محطم الأورك",
                "description": "واجه قبيلة الأورك واهزمها",
                "duration": 40,
                "experience": 2200,
                "money": 3200,
                "required_level": 12,
                "power_requirement": 2000
            },
            "beast_hunter": {
                "name": "🐺 صياد الوحوش",
                "description": "اصطد الوحوش الشرسة في الغابة المظلمة",
                "duration": 50,
                "experience": 3000,
                "money": 4500,
                "required_level": 18,
                "power_requirement": 2800
            }
        }
        
        for mission_id, mission_data in kill_missions.items():
            # فحص متطلبات المستوى والقوة
            level_met = player.level >= mission_data["required_level"]
            power_met = player.power >= mission_data["power_requirement"]
            available = level_met and power_met
            
            if available:
                button_text = f"✅ {mission_data['name']}"
                callback_data = f"start_mission_kill_{mission_id}"
            else:
                button_text = f"🔒 {mission_data['name']}"
                callback_data = f"locked_mission_{mission_id}"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=callback_data
            )])
            
            # إضافة معلومات المهمة
            if available:
                status = "✅ متاح"
            elif not level_met:
                status = f"🔒 يحتاج مستوى {mission_data['required_level']}"
            else:
                status = f"🔒 يحتاج قوة {format_number(mission_data['power_requirement'])}"
                
            missions_text += (
                f"{mission_data['name']}\n"
                f"📝 {mission_data['description']}\n"
                f"⏱️ المدة: {mission_data['duration']} دقيقة\n"
                f"⭐ الخبرة: {format_number(mission_data['experience'])}\n"
                f"💰 المال: {format_number(mission_data['money'])}$\n"
                f"🎯 الحالة: {status}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمهام", callback_data="guild_missions")])
        
        await safe_edit_text(
            callback,
            missions_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض مهام قتل الوحوش: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_locked_mission(callback: CallbackQuery):
    """معالجة المهام المغلقة"""
    try:
        await callback.answer("🔒 هذه المهمة مغلقة! ارفع مستواك أو قوتك أولاً", show_alert=True)
    except Exception as e:
        logging.error(f"خطأ في معالجة المهمة المغلقة: {e}")

# تصدير الدوال
__all__ = [
    'show_missions_menu',
    'show_normal_missions',
    'show_medium_missions', 
    'show_advanced_missions',
    'show_legendary_missions',
    'show_collect_missions',
    'show_kill_missions',
    'start_mission',
    'show_active_mission_status',
    'handle_locked_mission',
    'complete_active_mission'
]
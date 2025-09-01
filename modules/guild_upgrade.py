"""
نظام ترقية النقابة
Guild Upgrade System
"""

import logging
from typing import Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from modules.guild_game import GUILD_PLAYERS, ADVANCED_CLASSES
from modules.guild_database import save_guild_player, update_guild_stats
from utils.helpers import format_number

async def show_upgrade_menu(callback: CallbackQuery):
    """عرض قائمة الترقية"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        
        # زر ترقية المستوى
        if player.can_level_up():
            keyboard.append([InlineKeyboardButton(
                text="🆙 ترقية المستوى",
                callback_data="guild_level_up"
            )])
        
        # زر تغيير الفئة المتقدمة
        keyboard.append([InlineKeyboardButton(
            text="⚡ تغيير فئة متقدمة",
            callback_data="guild_advanced_class"
        )])
        
        keyboard.append([InlineKeyboardButton(
            text="🔙 رجوع",
            callback_data="guild_main_menu"
        )])
        
        # معلومات الترقية
        experience_needed = player.get_experience_for_next_level()
        can_level_up_text = "✅ متاح!" if player.can_level_up() else f"❌ تحتاج {format_number(experience_needed - player.experience)} خبرة"
        
        await callback.message.edit_text(
            f"🏅 **ترقية {player.name}**\n\n"
            f"📊 **حالتك الحالية:**\n"
            f"🏅 المستوى: {player.level}\n"
            f"⭐ الخبرة: {format_number(player.experience)}/{format_number(experience_needed)}\n"
            f"⚔️ القوة: {format_number(player.power)}\n\n"
            f"🆙 **ترقية المستوى:** {can_level_up_text}\n"
            f"💡 كل مستوى يمنحك +50 قوة إضافية\n\n"
            f"⚡ **الفئة المتقدمة:** {player.advanced_class}\n"
            f"💡 الفئات المتقدمة تمنح قوة هائلة!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الترقية: {e}")
        await callback.answer("❌ حدث خطأ")

async def level_up_player(callback: CallbackQuery):
    """ترقية مستوى اللاعب"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        if not player.can_level_up():
            experience_needed = player.get_experience_for_next_level()
            await callback.answer(f"❌ تحتاج {format_number(experience_needed - player.experience)} خبرة إضافية!")
            return
        
        old_level = player.level
        old_power = player.power
        
        # ترقية المستوى
        success = player.level_up()
        if not success:
            await callback.answer("❌ فشل في الترقية!")
            return
        
        # حفظ البيانات المحدثة
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
        await update_guild_stats(user_id, "level_ups", 1)
        
        keyboard = []
        
        # فحص إمكانية ترقية أخرى
        if player.can_level_up():
            keyboard.append([InlineKeyboardButton(
                text="🆙 ترقية أخرى",
                callback_data="guild_level_up"
            )])
        
        keyboard.extend([[
            InlineKeyboardButton(text="📊 قائمة الترقية", callback_data="guild_upgrade")
        ], [
            InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="guild_main_menu")
        ]])
        
        await callback.message.edit_text(
            f"🎉 **مبروك الترقية!**\n\n"
            f"🆙 **تمت ترقيتك من المستوى {old_level} إلى المستوى {player.level}!**\n\n"
            f"📈 **التحسينات:**\n"
            f"⚔️ القوة: {format_number(old_power)} ← {format_number(player.power)} (+50)\n"
            f"⭐ الخبرة المتبقية: {format_number(player.experience)}\n\n"
            f"🔥 **حالتك الجديدة:**\n"
            f"🏅 المستوى: {player.level}\n"
            f"⚔️ القوة الإجمالية: {format_number(player.power)}\n"
            f"⭐ الخبرة: {format_number(player.experience)}/{format_number(player.get_experience_for_next_level())}\n\n"
            f"💡 استمر في أداء المهام للحصول على خبرة أكثر!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer("🎉 تمت الترقية بنجاح!")
        
    except Exception as e:
        logging.error(f"خطأ في ترقية المستوى: {e}")
        await callback.answer("❌ حدث خطأ في الترقية")

async def show_advanced_classes(callback: CallbackQuery):
    """عرض الفئات المتقدمة"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        keyboard = []
        classes_text = f"⚡ **الفئات المتقدمة لـ {player.name}**\n\n"
        classes_text += f"🏅 **مستواك الحالي:** {player.level}\n"
        classes_text += f"🔥 **فئتك المتقدمة:** {player.advanced_class}\n\n"
        
        available_classes = 0
        
        for class_id, class_data in ADVANCED_CLASSES.items():
            if player.level >= class_data["required_level"]:
                # فئة متاحة
                if player.advanced_class == class_data["name"]:
                    button_text = f"✅ {class_data['name']} (مفعلة)"
                    callback_data = "current_class"
                else:
                    button_text = f"⚡ {class_data['name']}"
                    callback_data = f"change_class_{class_id}"
                    available_classes += 1
                
                keyboard.append([InlineKeyboardButton(
                    text=button_text,
                    callback_data=callback_data
                )])
                
                classes_text += f"✅ **{class_data['name']}** - مستوى {class_data['required_level']}\n"
            else:
                # فئة مغلقة
                classes_text += f"🔒 **{class_data['name']}** - مستوى {class_data['required_level']}\n"
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للترقية", callback_data="guild_upgrade")])
        
        if available_classes == 0 and player.advanced_class == "غير متاح":
            classes_text += "\n💡 ارفع مستواك للوصول للفئات المتقدمة!"
        elif available_classes > 0:
            classes_text += f"\n🎯 لديك {available_classes} فئة متقدمة متاحة!"
        
        await callback.message.edit_text(
            classes_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض الفئات المتقدمة: {e}")
        await callback.answer("❌ حدث خطأ")

async def change_advanced_class(callback: CallbackQuery):
    """تغيير الفئة المتقدمة"""
    try:
        user_id = callback.from_user.id
        class_id = callback.data.split("_")[2]
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        if class_id not in ADVANCED_CLASSES:
            await callback.answer("❌ فئة غير موجودة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        class_data = ADVANCED_CLASSES[class_id]
        
        # فحص المتطلبات
        if player.level < class_data["required_level"]:
            await callback.answer(f"🔒 تحتاج مستوى {class_data['required_level']}!")
            return
        
        old_class = player.advanced_class
        
        # تغيير الفئة
        player.advanced_class = class_data["name"]
        
        # إضافة قوة الفئة المتقدمة (كل فئة تضيف 100 قوة)
        power_bonus = 100
        player.power += power_bonus
        
        # حفظ البيانات
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
        
        await callback.message.edit_text(
            f"🎉 **تهانينا!**\n\n"
            f"⚡ **تم تغيير فئتك المتقدمة بنجاح!**\n\n"
            f"📈 **التغيير:**\n"
            f"🔥 من: {old_class}\n"
            f"⚡ إلى: {class_data['name']}\n\n"
            f"💪 **القوة الإضافية:** +{power_bonus}\n"
            f"⚔️ **قوتك الجديدة:** {format_number(player.power)}\n\n"
            f"🔥 **أنت الآن {class_data['name']} قوي وجبار!**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="⚡ فئات أخرى", callback_data="guild_advanced_class")
            ], [
                InlineKeyboardButton(text="📊 قائمة الترقية", callback_data="guild_upgrade")
            ], [
                InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer("⚡ تم تغيير الفئة بنجاح!")
        
    except Exception as e:
        logging.error(f"خطأ في تغيير الفئة المتقدمة: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_current_class(callback: CallbackQuery):
    """معالجة النقر على الفئة الحالية"""
    try:
        await callback.answer("✅ هذه فئتك المتقدمة الحالية!")
    except Exception as e:
        logging.error(f"خطأ في معالجة الفئة الحالية: {e}")

# تصدير الدوال
__all__ = [
    'show_upgrade_menu',
    'level_up_player',
    'show_advanced_classes',
    'change_advanced_class',
    'handle_current_class'
]
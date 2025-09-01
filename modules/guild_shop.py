"""
متجر النقابة
Guild Shop System
"""

import logging
from typing import Dict, Optional

from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from modules.guild_game import GUILD_PLAYERS, SHOP_ITEMS
from modules.guild_database import add_inventory_item, get_player_inventory, equip_item, save_guild_player
from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number

async def show_shop_menu(callback: CallbackQuery):
    """عرض القائمة الرئيسية للمتجر"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        user_data = await get_or_create_user(user_id, player.username, player.name)
        balance = user_data.get('balance', 0) if user_data else 0
        
        keyboard = [
            [InlineKeyboardButton(text="⚔️ متجر الأسلحة", callback_data="shop_weapons")],
            [InlineKeyboardButton(text="🏅 متجر الأوسمة", callback_data="shop_badges")],
            [InlineKeyboardButton(text="🏷️ متجر الألقاب", callback_data="shop_titles")],
            [InlineKeyboardButton(text="🧪 متجر الجرعات", callback_data="shop_potions")],
            [InlineKeyboardButton(text="💍 متجر الخواتم", callback_data="shop_rings")],
            [InlineKeyboardButton(text="🐾 متجر الحيوانات", callback_data="shop_animals")],
            [InlineKeyboardButton(text="🎒 مخزوني", callback_data="shop_inventory")],
            [InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")]
        ]
        
        await callback.message.edit_text(
            f"🛒 **مرحباً في المتجر الأسطوري!**\n\n"
            f"👤 **اللاعب:** {player.name}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"💰 **رصيدك:** {format_number(balance)}$\n\n"
            f"🎯 **اختر قسماً لاستكشاف الكنوز الملحمية:**\n\n"
            f"⚔️ **الأسلحة** - أدوات القتال الفتاكة\n"
            f"🏅 **الأوسمة** - رموز الشرف والقوة\n"
            f"🏷️ **الألقاب** - أسماء تُخلد في التاريخ\n"
            f"🧪 **الجرعات** - إكسيرات القوة السحرية\n"
            f"💍 **الخواتم** - خواتم القدر الأسطورية\n"
            f"🐾 **الحيوانات** - رفاق المعركة الأوفياء\n"
            f"🎒 **مخزوني** - عناصرك المملوكة",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض متجر النقابة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_weapons_shop(callback: CallbackQuery):
    """عرض متجر الأسلحة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        user_data = await get_or_create_user(user_id, player.username, player.name)
        balance = user_data.get('balance', 0) if user_data else 0
        
        keyboard = []
        shop_text = f"⚔️ **متجر الأسلحة الأسطورية**\n\n💰 **رصيدك:** {format_number(balance)}$\n\n"
        
        for weapon_id, weapon_data in SHOP_ITEMS["weapons"].items():
            # فحص إذا كان يملك المال الكافي
            can_afford = balance >= weapon_data["price"]
            button_text = f"{'✅' if can_afford else '❌'} {weapon_data['name']} - {format_number(weapon_data['price'])}$"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"buy_weapon_{weapon_id}" if can_afford else f"cant_buy_{weapon_id}"
            )])
            
            shop_text += (
                f"{weapon_data['name']}\n"
                f"📝 {weapon_data['description']}\n"
                f"⚔️ قوة إضافية: +{weapon_data['power_bonus']}\n"
                f"💰 السعر: {format_number(weapon_data['price'])}$\n"
                f"{'✅ متاح' if can_afford else '❌ رصيد غير كافي'}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمتجر", callback_data="guild_shop")])
        
        await callback.message.edit_text(
            shop_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض متجر الأسلحة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_badges_shop(callback: CallbackQuery):
    """عرض متجر الأوسمة"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        user_data = await get_or_create_user(user_id, player.username, player.name)
        balance = user_data.get('balance', 0) if user_data else 0
        
        keyboard = []
        shop_text = f"🏅 **متجر الأوسمة المجيدة**\n\n💰 **رصيدك:** {format_number(balance)}$\n\n"
        
        for badge_id, badge_data in SHOP_ITEMS["badges"].items():
            can_afford = balance >= badge_data["price"]
            button_text = f"{'✅' if can_afford else '❌'} {badge_data['name']} - {format_number(badge_data['price'])}$"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"buy_badge_{badge_id}" if can_afford else f"cant_buy_{badge_id}"
            )])
            
            shop_text += (
                f"{badge_data['name']}\n"
                f"📝 {badge_data['description']}\n"
                f"⚔️ قوة إضافية: +{badge_data['power_bonus']}\n"
                f"💰 السعر: {format_number(badge_data['price'])}$\n"
                f"{'✅ متاح' if can_afford else '❌ رصيد غير كافي'}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمتجر", callback_data="guild_shop")])
        
        await callback.message.edit_text(
            shop_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض متجر الأوسمة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_titles_shop(callback: CallbackQuery):
    """عرض متجر الألقاب"""
    try:
        user_id = callback.from_user.id
        player = GUILD_PLAYERS[user_id]
        user_data = await get_or_create_user(user_id, player.username, player.name)
        balance = user_data.get('balance', 0) if user_data else 0
        
        keyboard = []
        shop_text = f"🏷️ **متجر الألقاب الخالدة**\n\n💰 **رصيدك:** {format_number(balance)}$\n\n"
        
        for title_id, title_data in SHOP_ITEMS["titles"].items():
            can_afford = balance >= title_data["price"]
            button_text = f"{'✅' if can_afford else '❌'} {title_data['name']} - {format_number(title_data['price'])}$"
            
            keyboard.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"buy_title_{title_id}" if can_afford else f"cant_buy_{title_id}"
            )])
            
            shop_text += (
                f"{title_data['name']}\n"
                f"📝 {title_data['description']}\n"
                f"⚔️ قوة إضافية: +{title_data['power_bonus']}\n"
                f"💰 السعر: {format_number(title_data['price'])}$\n"
                f"{'✅ متاح' if can_afford else '❌ رصيد غير كافي'}\n\n"
            )
        
        keyboard.append([InlineKeyboardButton(text="🔙 رجوع للمتجر", callback_data="guild_shop")])
        
        await callback.message.edit_text(
            shop_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض متجر الألقاب: {e}")
        await callback.answer("❌ حدث خطأ")

async def buy_item(callback: CallbackQuery):
    """شراء عنصر من المتجر"""
    try:
        user_id = callback.from_user.id
        
        # تحليل البيانات
        parts = callback.data.split("_")
        item_type = parts[1]  # weapon, badge, title
        item_id = parts[2]
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        # الحصول على بيانات العنصر
        if item_type == "weapon":
            category = "weapons"
        elif item_type == "badge":
            category = "badges"
        elif item_type == "title":
            category = "titles"
        else:
            await callback.answer("❌ نوع عنصر غير صحيح!")
            return
        
        if item_id not in SHOP_ITEMS[category]:
            await callback.answer("❌ عنصر غير موجود!")
            return
        
        item_data = SHOP_ITEMS[category][item_id]
        
        # فحص الرصيد
        user_data = await get_or_create_user(user_id, player.username, player.name)
        if not user_data:
            await callback.answer("❌ خطأ في البيانات!")
            return
        
        balance = user_data.get('balance', 0)
        if balance < item_data["price"]:
            await callback.answer(f"❌ رصيد غير كافي! تحتاج {format_number(item_data['price'])}$")
            return
        
        # خصم المبلغ
        new_balance = balance - item_data["price"]
        success = await update_user_balance(user_id, new_balance)
        if not success:
            await callback.answer("❌ فشل في خصم المبلغ!")
            return
        
        # إضافة المعاملة
        await add_transaction(user_id, -item_data["price"], "شراء عنصر نقابة", f"شراء {item_data['name']}")
        
        # إضافة العنصر للمخزون
        await add_inventory_item(user_id, item_type, item_id, item_data["name"])
        
        # تجهيز العنصر تلقائياً
        await equip_item(user_id, item_id, item_type)
        
        # تحديث قوة اللاعب
        player.power += item_data["power_bonus"]
        
        # تحديث العنصر المجهز في بيانات اللاعب
        if item_type == "weapon":
            player.weapon = item_data["name"]
        elif item_type == "badge":
            player.badge = item_data["name"]
        elif item_type == "title":
            player.title = item_data["name"]
        
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
        
        await callback.message.edit_text(
            f"🎉 **مبروك!**\n\n"
            f"✅ **تم شراء {item_data['name']} بنجاح!**\n\n"
            f"💰 **المبلغ المدفوع:** {format_number(item_data['price'])}$\n"
            f"💳 **رصيدك الجديد:** {format_number(new_balance)}$\n"
            f"⚔️ **قوتك الجديدة:** {format_number(player.power)} (+{item_data['power_bonus']})\n\n"
            f"🎒 **تم إضافة العنصر لمخزونك وتجهيزه تلقائياً!**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛒 متابعة التسوق", callback_data="guild_shop")
            ], [
                InlineKeyboardButton(text="🎒 عرض المخزون", callback_data="shop_inventory")
            ], [
                InlineKeyboardButton(text="🏠 القائمة الرئيسية", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer("🎉 تم الشراء بنجاح!")
        
    except Exception as e:
        logging.error(f"خطأ في شراء العنصر: {e}")
        await callback.answer("❌ حدث خطأ في الشراء")

async def show_inventory(callback: CallbackQuery):
    """عرض مخزون اللاعب"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        inventory = await get_player_inventory(user_id)
        
        if not inventory:
            await callback.message.edit_text(
                f"🎒 **مخزون {player.name}**\n\n"
                f"📦 **المخزون فارغ!**\n\n"
                f"💡 قم بشراء عناصر من المتجر لتظهر هنا",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                    InlineKeyboardButton(text="🛒 اذهب للمتجر", callback_data="guild_shop")
                ], [
                    InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
                ]])
            )
            await callback.answer()
            return
        
        # تجميع العناصر حسب النوع
        weapons = [item for item in inventory if item['item_type'] == 'weapon']
        badges = [item for item in inventory if item['item_type'] == 'badge']
        titles = [item for item in inventory if item['item_type'] == 'title']
        
        inventory_text = f"🎒 **مخزون {player.name}**\n\n"
        
        if weapons:
            inventory_text += "⚔️ **الأسلحة:**\n"
            for weapon in weapons:
                status = "🟢 مجهز" if weapon['equipped'] else "⚪ غير مجهز"
                inventory_text += f"  • {weapon['item_name']} {status}\n"
            inventory_text += "\n"
        
        if badges:
            inventory_text += "🏅 **الأوسمة:**\n"
            for badge in badges:
                status = "🟢 مجهز" if badge['equipped'] else "⚪ غير مجهز"
                inventory_text += f"  • {badge['item_name']} {status}\n"
            inventory_text += "\n"
        
        if titles:
            inventory_text += "🏷️ **الألقاب:**\n"
            for title in titles:
                status = "🟢 مجهز" if title['equipped'] else "⚪ غير مجهز"
                inventory_text += f"  • {title['item_name']} {status}\n"
            inventory_text += "\n"
        
        inventory_text += f"📊 **إجمالي العناصر:** {len(inventory)}\n"
        inventory_text += f"⚔️ **القوة الإجمالية:** {format_number(player.power)}"
        
        await callback.message.edit_text(
            inventory_text,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🛒 متابعة التسوق", callback_data="guild_shop")
            ], [
                InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض المخزون: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_cant_buy(callback: CallbackQuery):
    """معالجة عدم القدرة على الشراء"""
    try:
        await callback.answer("❌ رصيدك غير كافي لشراء هذا العنصر!", show_alert=True)
    except Exception as e:
        logging.error(f"خطأ في معالجة عدم القدرة على الشراء: {e}")

# تصدير الدوال
__all__ = [
    'show_shop_menu',
    'show_weapons_shop',
    'show_badges_shop',
    'show_titles_shop',
    'buy_item',
    'show_inventory',
    'handle_cant_buy'
]
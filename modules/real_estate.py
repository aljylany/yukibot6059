"""
وحدة العقارات
Real Estate Module
"""

import logging
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
import re

from database.operations import get_user, update_user_balance, execute_query
from utils.states import PropertyStates  
from utils.helpers import format_number, is_valid_amount
from modules.leveling import add_xp

# قائمة العقارات المتاحة - محدثة مع 10 أنواع
AVAILABLE_PROPERTIES = {
    "apartment": {"name": "شقة", "price": 50000, "income": 100, "emoji": "🏠", "key": "شقة"},
    "house": {"name": "بيت", "price": 120000, "income": 250, "emoji": "🏡", "key": "بيت"},
    "villa": {"name": "فيلا", "price": 300000, "income": 600, "emoji": "🏘", "key": "فيلا"},
    "building": {"name": "مبنى", "price": 800000, "income": 1500, "emoji": "🏢", "key": "مبنى"},
    "mall": {"name": "مول تجاري", "price": 2000000, "income": 4000, "emoji": "🏬", "key": "مول"},
    "skyscraper": {"name": "ناطحة سحاب", "price": 5000000, "income": 10000, "emoji": "🏙", "key": "ناطحة"},
    "office": {"name": "مكتب إداري", "price": 750000, "income": 1200, "emoji": "🏢", "key": "مكتب"},
    "warehouse": {"name": "مستودع", "price": 400000, "income": 800, "emoji": "🏭", "key": "مستودع"},
    "factory": {"name": "مصنع", "price": 1500000, "income": 3000, "emoji": "🏭", "key": "مصنع"},
    "resort": {"name": "منتجع سياحي", "price": 3000000, "income": 6000, "emoji": "🏖", "key": "منتجع"}
}


async def show_property_menu(message: Message):
    """عرض قائمة العقارات الرئيسية"""
    try:
        if not message.from_user:
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على عقارات المستخدم
        user_properties = await get_user_properties(message.from_user.id)
        if user_properties and isinstance(user_properties, list):
            total_income = sum(prop.get('income_per_hour', 0) for prop in user_properties)
            total_value = sum(AVAILABLE_PROPERTIES.get(prop.get('property_type', ''), {}).get('price', 0) for prop in user_properties)
        else:
            total_income = 0
            total_value = 0
            user_properties = []
        
        property_text = f"""
🏠 **محفظة العقارات**

💰 رصيدك النقدي: {format_number(user['balance'])}$
🏠 عدد العقارات: {len(user_properties)}
💎 قيمة العقارات: {format_number(total_value)}$
📈 الدخل بالساعة: {format_number(total_income)}$/ساعة

💡 العقارات تولد دخل سلبي كل ساعة!

📋 **الأوامر المتاحة:**
🛒 "شراء عقار [النوع] [الكمية]" - مثال: شراء عقار شقة 2
💰 "بيع عقار [النوع] [الكمية]" - مثال: بيع عقار بيت 1  
🏠 "عقاراتي" لعرض عقاراتك
📊 "قائمة العقارات" لعرض الأنواع المتاحة
📈 "احصائيات العقارات" للإحصائيات
        """
        
        await message.reply(property_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة العقارات: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة العقارات")


async def show_available_properties(message: Message):
    """عرض العقارات المتاحة للشراء"""
    try:
        if not message.from_user:
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        keyboard_buttons = []
        for prop_type, prop_info in AVAILABLE_PROPERTIES.items():
            if user['balance'] >= prop_info['price']:
                button_text = f"{prop_info['emoji']} {prop_info['name']} - {format_number(prop_info['price'])}$"
            else:
                button_text = f"❌ {prop_info['name']} - {format_number(prop_info['price'])}$"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"property_buy_{prop_type}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        properties_text = "🛒 **العقارات المتاحة للشراء:**\n\n"
        for prop_type, prop_info in AVAILABLE_PROPERTIES.items():
            affordable = "✅" if user['balance'] >= prop_info['price'] else "❌"
            properties_text += f"{affordable} {prop_info['emoji']} **{prop_info['name']}**\n"
            properties_text += f"   💰 السعر: {format_number(prop_info['price'])}$\n"
            properties_text += f"   📈 الدخل: {format_number(prop_info['income'])}$/ساعة\n\n"
        
        properties_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$"
        
        await message.reply(properties_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض العقارات المتاحة: {e}")
        await message.reply("❌ حدث خطأ في عرض العقارات المتاحة")


async def show_owned_properties(message: Message):
    """عرض العقارات المملوكة للمستخدم"""
    try:
        if not message.from_user:
            return
            
        user_properties = await get_user_properties(message.from_user.id)
        if not user_properties or not isinstance(user_properties, list):
            user_properties = []
        
        if not user_properties:
            await message.reply("❌ لا تملك أي عقارات حالياً\n\nاستخدم /buy_property لشراء عقار")
            return
        
        keyboard_buttons = []
        for prop in user_properties:
            prop_info = AVAILABLE_PROPERTIES.get(prop.get('property_type', ''), {})
            sell_price = int(prop_info.get('price', 0) * 0.8)  # بيع بـ 80% من السعر الأصلي
            
            button_text = f"{prop_info.get('emoji', '🏠')} {prop_info.get('name', 'عقار')} - {format_number(sell_price)}$"
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"property_sell_{prop.get('id', 0)}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        properties_text = "💰 **عقاراتك للبيع:**\n\n"
        total_value = 0
        
        for prop in user_properties:
            prop_info = AVAILABLE_PROPERTIES.get(prop.get('property_type', ''), {})
            sell_price = int(prop_info.get('price', 0) * 0.8)
            total_value += sell_price
            
            properties_text += f"{prop_info.get('emoji', '🏠')} **{prop_info.get('name', 'عقار')}**\n"
            properties_text += f"   💰 سعر البيع: {format_number(sell_price)}$\n"
            properties_text += f"   📈 الدخل: {format_number(prop.get('income_per_hour', 0))}$/ساعة\n\n"
        
        properties_text += f"💎 إجمالي قيمة البيع: {format_number(total_value)}$"
        
        await message.reply(properties_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض العقارات المملوكة: {e}")
        await message.reply("❌ حدث خطأ في عرض العقارات المملوكة")


async def buy_property(message: Message, property_type: str):
    """شراء عقار"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if property_type not in AVAILABLE_PROPERTIES:
            await message.reply("❌ نوع عقار غير صحيح")
            return
        
        prop_info = AVAILABLE_PROPERTIES[property_type]
        
        # التحقق من الرصيد
        if user['balance'] < prop_info['price']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"💰 سعر {prop_info['name']}: {format_number(prop_info['price'])}$\n"
                f"💵 رصيدك الحالي: {format_number(user['balance'])}$\n"
                f"💸 تحتاج إلى: {format_number(prop_info['price'] - user['balance'])}$ إضافية"
            )
            return
        
        # شراء العقار
        new_balance = user['balance'] - prop_info['price']
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة العقار إلى قاعدة البيانات
        await execute_query(
            "INSERT INTO properties (user_id, property_type, location, price, income_per_hour) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, property_type, "المدينة", prop_info['price'], prop_info['income'])
        )
        
        await message.reply(
            f"🎉 **تم شراء العقار بنجاح!**\n\n"
            f"{prop_info['emoji']} العقار: {prop_info['name']}\n"
            f"💰 السعر المدفوع: {format_number(prop_info['price'])}$\n"
            f"📈 الدخل بالساعة: {format_number(prop_info['income'])}$/ساعة\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"💡 سيبدأ العقار في توليد الدخل كل ساعة!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في شراء العقار: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")


async def sell_property(message: Message, property_id: int):
    """بيع عقار"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على بيانات العقار
        property_data = await execute_query(
            "SELECT * FROM properties WHERE id = ? AND user_id = ?",
            (property_id, message.from_user.id),
            fetch_one=True
        )
        
        if not property_data:
            await message.reply("❌ العقار غير موجود أو لا تملكه")
            return
        
        prop_info = AVAILABLE_PROPERTIES.get(property_data['property_type'], {})
        sell_price = int(prop_info.get('price', 0) * 0.8)  # بيع بـ 80% من السعر الأصلي
        
        # بيع العقار
        new_balance = user['balance'] + sell_price
        await update_user_balance(message.from_user.id, new_balance)
        
        # حذف العقار من قاعدة البيانات
        await execute_query(
            "DELETE FROM properties WHERE id = ? AND user_id = ?",
            (property_id, message.from_user.id)
        )
        
        await message.reply(
            f"💰 **تم بيع العقار بنجاح!**\n\n"
            f"{prop_info.get('emoji', '🏠')} العقار: {prop_info.get('name', 'عقار')}\n"
            f"💵 المبلغ المستلم: {format_number(sell_price)}$\n"
            f"💰 رصيدك الجديد: {format_number(new_balance)}$"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بيع العقار: {e}")
        await message.reply("❌ حدث خطأ في عملية البيع")


async def show_property_management(message: Message):
    """إدارة العقارات"""
    try:
        user_properties = await get_user_properties(message.from_user.id)
        
        if not user_properties:
            await message.reply("❌ لا تملك أي عقارات حالياً")
            return
        
        properties_text = "🏠 **إدارة العقارات**\n\n"
        total_income = 0
        total_value = 0
        
        for prop in user_properties:
            prop_info = AVAILABLE_PROPERTIES.get(prop['property_type'], {})
            current_value = int(prop_info.get('price', 0) * 0.8)
            
            properties_text += f"{prop_info.get('emoji', '🏠')} **{prop_info.get('name', 'عقار')}**\n"
            properties_text += f"   📍 الموقع: {prop['location']}\n"
            properties_text += f"   💰 قيمة البيع: {format_number(current_value)}$\n"
            properties_text += f"   📈 الدخل: {format_number(prop['income_per_hour'])}$/ساعة\n"
            properties_text += f"   📅 تاريخ الشراء: {prop['purchased_at'][:10]}\n\n"
            
            total_income += prop['income_per_hour']
            total_value += current_value
        
        properties_text += f"📊 **الملخص:**\n"
        properties_text += f"🏠 عدد العقارات: {len(user_properties)}\n"
        properties_text += f"💎 القيمة الإجمالية: {format_number(total_value)}$\n"
        properties_text += f"📈 الدخل بالساعة: {format_number(total_income)}$/ساعة\n"
        properties_text += f"💰 الدخل اليومي: {format_number(total_income * 24)}$/يوم"
        
        await message.reply(properties_text)
        
    except Exception as e:
        logging.error(f"خطأ في إدارة العقارات: {e}")
        await message.reply("❌ حدث خطأ في إدارة العقارات")


async def get_user_properties(user_id: int):
    """الحصول على عقارات المستخدم"""
    try:
        properties = await execute_query(
            "SELECT * FROM properties WHERE user_id = ? ORDER BY purchased_at DESC",
            (user_id,),
            fetch_all=True
        )
        return properties if properties else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على عقارات المستخدم: {e}")
        return []


async def collect_property_income(user_id: int):
    """جمع دخل العقارات (يتم استدعاؤها دورياً)"""
    try:
        user_properties = await get_user_properties(user_id)
        if not user_properties:
            return 0
        
        total_income = sum(prop['income_per_hour'] for prop in user_properties)
        
        if total_income > 0:
            user = await get_user(user_id)
            if user:
                new_balance = user['balance'] + total_income
                await update_user_balance(user_id, new_balance)
        
        return total_income
        
    except Exception as e:
        logging.error(f"خطأ في جمع دخل العقارات: {e}")
        return 0


# State handlers
async def process_property_choice(message: Message, state: FSMContext):
    """معالجة اختيار العقار"""
    await message.reply("تم استلام اختيارك، سيتم المعالجة...")
    await state.clear()


async def process_sell_confirmation(message: Message, state: FSMContext):
    """معالجة تأكيد البيع"""
    await message.reply("تم تأكيد العملية")
    await state.clear()


# ==================== دوال الأوامر النصية الجديدة ====================

async def handle_buy_property_text(message: Message, property_name: str, quantity: int):
    """معالجة أمر شراء عقار بالنص مع الكمية"""
    try:
        if not message.from_user:
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # البحث عن العقار بالاسم العربي
        property_type = None
        for key, prop_info in AVAILABLE_PROPERTIES.items():
            if prop_info['key'].lower() == property_name.lower():
                property_type = key
                break
        
        if not property_type:
            # إنشاء قائمة بأسماء العقارات المتاحة
            available_names = [prop['key'] for prop in AVAILABLE_PROPERTIES.values()]
            await message.reply(
                f"❌ نوع عقار غير صحيح!\n\n"
                f"📋 **الأنواع المتاحة:**\n" + 
                "\n".join([f"• {name}" for name in available_names])
            )
            return
        
        if quantity <= 0:
            await message.reply("❌ يجب أن تكون الكمية أكبر من صفر")
            return
            
        if quantity > 100:
            await message.reply("❌ لا يمكن شراء أكثر من 100 عقار في المرة الواحدة")
            return
        
        prop_info = AVAILABLE_PROPERTIES[property_type]
        total_cost = prop_info['price'] * quantity
        
        # التحقق من الرصيد
        if user['balance'] < total_cost:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"💰 تكلفة {quantity} {prop_info['name']}: {format_number(total_cost)}$\n"
                f"💵 رصيدك الحالي: {format_number(user['balance'])}$\n"
                f"💸 تحتاج إلى: {format_number(total_cost - user['balance'])}$ إضافية"
            )
            return
        
        # الشراء
        new_balance = user['balance'] - total_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة العقارات إلى قاعدة البيانات
        total_income = prop_info['income'] * quantity
        for i in range(quantity):
            await execute_query(
                "INSERT INTO properties (user_id, property_type, location, price, income_per_hour) VALUES (?, ?, ?, ?, ?)",
                (message.from_user.id, property_type, "المدينة", prop_info['price'], prop_info['income'])
            )
        
        # إضافة XP
        for _ in range(quantity):
            await add_xp(message.from_user.id, 25)
        
        await message.reply(
            f"🎉 **تم الشراء بنجاح!**\n\n"
            f"{prop_info['emoji']} **العقار:** {prop_info['name']}\n"
            f"🔢 **الكمية:** {quantity}\n"
            f"💰 **التكلفة الإجمالية:** {format_number(total_cost)}$\n"
            f"📈 **الدخل الإضافي:** {format_number(total_income)}$/ساعة\n"
            f"💵 **رصيدك الجديد:** {format_number(new_balance)}$\n"
            f"⭐ **XP مكتسب:** +{quantity * 25}\n\n"
            f"💡 ستبدأ العقارات في توليد الدخل كل ساعة!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في شراء العقار بالنص: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")


async def handle_sell_property_text(message: Message, property_name: str, quantity: int):
    """معالجة أمر بيع عقار بالنص مع الكمية"""
    try:
        if not message.from_user:
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # البحث عن العقار بالاسم العربي
        property_type = None
        for key, prop_info in AVAILABLE_PROPERTIES.items():
            if prop_info['key'].lower() == property_name.lower():
                property_type = key
                break
        
        if not property_type:
            available_names = [prop['key'] for prop in AVAILABLE_PROPERTIES.values()]
            await message.reply(
                f"❌ نوع عقار غير صحيح!\n\n"
                f"📋 **الأنواع المتاحة:**\n" + 
                "\n".join([f"• {name}" for name in available_names])
            )
            return
        
        if quantity <= 0:
            await message.reply("❌ يجب أن تكون الكمية أكبر من صفر")
            return
        
        # التحقق من ملكية العقارات
        user_properties = await execute_query(
            "SELECT * FROM properties WHERE user_id = ? AND property_type = ? ORDER BY purchased_at ASC LIMIT ?",
            (message.from_user.id, property_type, quantity),
            fetch_all=True
        )
        
        if not user_properties or len(user_properties) < quantity:
            owned_count = len(user_properties) if user_properties else 0
            await message.reply(
                f"❌ لا تملك ما يكفي من هذا العقار!\n\n"
                f"📋 **تملك حالياً:** {owned_count} من {AVAILABLE_PROPERTIES[property_type]['name']}\n"
                f"🔢 **تريد بيع:** {quantity}\n"
                f"💡 استخدم \"عقاراتي\" لعرض عقاراتك"
            )
            return
        
        prop_info = AVAILABLE_PROPERTIES[property_type]
        sell_price_per_unit = int(prop_info['price'] * 0.8)  # بيع بـ 80%
        total_sell_price = sell_price_per_unit * quantity
        
        # بيع العقارات
        new_balance = user['balance'] + total_sell_price
        await update_user_balance(message.from_user.id, new_balance)
        
        # حذف العقارات من قاعدة البيانات
        property_ids = [prop['id'] for prop in user_properties[:quantity]]
        for prop_id in property_ids:
            await execute_query(
                "DELETE FROM properties WHERE id = ? AND user_id = ?",
                (prop_id, message.from_user.id)
            )
        
        # إضافة XP أقل للبيع
        for _ in range(quantity):
            await add_xp(message.from_user.id, 25)
        
        lost_income = prop_info['income'] * quantity
        
        await message.reply(
            f"💰 **تم البيع بنجاح!**\n\n"
            f"{prop_info['emoji']} **العقار:** {prop_info['name']}\n"
            f"🔢 **الكمية:** {quantity}\n"
            f"💵 **المبلغ المستلم:** {format_number(total_sell_price)}$\n"
            f"📉 **دخل مفقود:** -{format_number(lost_income)}$/ساعة\n"
            f"💰 **رصيدك الجديد:** {format_number(new_balance)}$\n"
            f"⭐ **XP مكتسب:** +{quantity * 25}"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بيع العقار بالنص: {e}")
        await message.reply("❌ حدث خطأ في عملية البيع")


async def show_properties_list(message: Message):
    """عرض قائمة أنواع العقارات المتاحة مع الأسعار"""
    try:
        if not message.from_user:
            return
            
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        properties_text = "🏠 **قائمة العقارات المتاحة**\n\n"
        
        # ترتيب العقارات حسب السعر
        sorted_properties = sorted(AVAILABLE_PROPERTIES.items(), key=lambda x: x[1]['price'])
        
        for i, (prop_type, prop_info) in enumerate(sorted_properties, 1):
            affordable = "✅" if user['balance'] >= prop_info['price'] else "❌"
            properties_text += f"{i}. {affordable} {prop_info['emoji']} **{prop_info['name']}**\n"
            properties_text += f"   💰 السعر: {format_number(prop_info['price'])}$\n"
            properties_text += f"   📈 الدخل: {format_number(prop_info['income'])}$/ساعة\n"
            properties_text += f"   🔤 للشراء: `شراء عقار {prop_info['key']} [الكمية]`\n\n"
        
        properties_text += f"💵 **رصيدك الحالي:** {format_number(user['balance'])}$\n\n"
        properties_text += "💡 **مثال للشراء:** شراء عقار شقة 2\n"
        properties_text += "💡 **مثال للبيع:** بيع عقار بيت 1"
        
        await message.reply(properties_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة العقارات: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة العقارات")

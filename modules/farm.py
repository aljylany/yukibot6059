"""
وحدة المزرعة
Farm Module
"""

import logging
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import FarmStates
from utils.helpers import format_number, is_valid_amount

# أنواع المحاصيل المتاحة
CROP_TYPES = {
    "wheat": {
        "name": "قمح",
        "cost_per_unit": 50,
        "grow_time_minutes": 2,
        "yield_per_unit": 80,
        "min_quantity": 1,
        "max_quantity": 100,
        "emoji": "🌾"
    },
    "corn": {
        "name": "ذرة",
        "cost_per_unit": 75,
        "grow_time_minutes": 5,
        "yield_per_unit": 120,
        "min_quantity": 1,
        "max_quantity": 80,
        "emoji": "🌽"
    },
    "tomato": {
        "name": "طماطم",
        "cost_per_unit": 100,
        "grow_time_minutes": 8,
        "yield_per_unit": 180,
        "min_quantity": 1,
        "max_quantity": 60,
        "emoji": "🍅"
    },
    "potato": {
        "name": "بطاطس",
        "cost_per_unit": 60,
        "grow_time_minutes": 4,
        "yield_per_unit": 100,
        "min_quantity": 1,
        "max_quantity": 90,
        "emoji": "🥔"
    },
    "carrot": {
        "name": "جزر",
        "cost_per_unit": 40,
        "grow_time_minutes": 1,
        "yield_per_unit": 65,
        "min_quantity": 1,
        "max_quantity": 120,
        "emoji": "🥕"
    },
    "strawberry": {
        "name": "فراولة",
        "cost_per_unit": 150,
        "grow_time_minutes": 10,
        "yield_per_unit": 300,
        "min_quantity": 1,
        "max_quantity": 40,
        "emoji": "🍓"
    }
}


async def show_farm_menu(message: Message):
    """عرض قائمة المزرعة الرئيسية"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على محاصيل المستخدم
        user_crops = await get_user_crops(message.from_user.id)
        growing_crops = [crop for crop in user_crops if crop['status'] == 'growing']
        ready_crops = [crop for crop in user_crops if crop['status'] == 'ready']
        
        # حساب القيمة الإجمالية للمحاصيل
        total_investment = sum(
            CROP_TYPES.get(crop['crop_type'], {}).get('cost_per_unit', 0) * crop['quantity']
            for crop in growing_crops
        )
        
        potential_income = sum(
            CROP_TYPES.get(crop['crop_type'], {}).get('yield_per_unit', 0) * crop['quantity']
            for crop in ready_crops
        )
        
        farm_text = f"""
🌾 **مزرعتك الخاصة**

💰 رصيدك النقدي: {format_number(user['balance'])}$

🌱 **حالة المزرعة:**
🌾 محاصيل تنمو: {len(growing_crops)}
✅ محاصيل جاهزة: {len(ready_crops)}
💰 الاستثمار الحالي: {format_number(total_investment)}$
💎 الدخل المتوقع: {format_number(potential_income)}$

💡 نصيحة: المحاصيل المختلفة لها أوقات نمو وأرباح مختلفة!

📋 **الأوامر المتاحة:**
🌱 اكتب: "زراعة" لزراعة محاصيل جديدة
🌾 اكتب: "حصاد" لحصاد المحاصيل الجاهزة
📊 اكتب: "حالة المزرعة" لعرض حالة المزرعة
📈 اكتب: "ارباح المزرعة" للإحصائيات
        """
        
        await message.reply(farm_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة المزرعة: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المزرعة")


async def list_crops(message: Message):
    """عرض قائمة المزروعات المتاحة"""
    try:
        crops_text = """
🌾 **قائمة المزروعات المتاحة:**

🌾 القمح - السعر: 50$ - مدة النضج: 2 دقيقة - العائد: 80$
🌽 الذرة - السعر: 75$ - مدة النضج: 5 دقائق - العائد: 120$ 
🍅 الطماطم - السعر: 100$ - مدة النضج: 8 دقائق - العائد: 180$
🥔 البطاطس - السعر: 60$ - مدة النضج: 4 دقائق - العائد: 100$
🥕 الجزر - السعر: 40$ - مدة النضج: 1 دقيقة - العائد: 65$
🍓 الفراولة - السعر: 150$ - مدة النضج: 10 دقائق - العائد: 300$

📝 **للزراعة:** اكتب "زراعة [النوع]"
📝 **مثال:** زراعة قمح
        """
        await message.reply(crops_text)
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة المزروعات: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة المزروعات")

async def plant_crop_command(message: Message):
    """معالجة أمر زراعة المحاصيل"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
            
        if not message.text:
            await message.reply("❌ يرجى تحديد نوع المحصول للزراعة")
            return
            
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ يرجى كتابة نوع المحصول\n\nمثال: زراعة قمح")
            return
            
        crop_name = parts[1].lower()
        
        # البحث عن المحصول
        crop_type = None
        for key, crop_info in CROP_TYPES.items():
            if crop_name in crop_info['name'].lower():
                crop_type = key
                break
                
        if not crop_type:
            await message.reply("❌ نوع المحصول غير متاح\n\nاستخدم 'قائمة المزروعات' لعرض المحاصيل المتاحة")
            return
        
        crop_info = CROP_TYPES[crop_type]
        quantity = 1  # كمية افتراضية
        total_cost = crop_info['cost_per_unit'] * quantity
        
        # التحقق من الرصيد
        if total_cost > user['balance']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"{crop_info['emoji']} {crop_info['name']}\n"
                f"💰 التكلفة: {total_cost}$\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        # حساب وقت الحصاد
        harvest_time = datetime.now() + timedelta(minutes=crop_info['grow_time_minutes'])
        
        # خصم التكلفة من الرصيد
        new_balance = user['balance'] - total_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # حفظ المحصول في قاعدة البيانات
        await execute_query(
            "INSERT INTO farm (user_id, crop_type, quantity, plant_time, harvest_time, status) VALUES (?, ?, ?, ?, ?, ?)",
            (message.from_user.id, crop_type, quantity, datetime.now().isoformat(), harvest_time.isoformat(), 'growing')
        )
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="crop_purchase",
            amount=total_cost,
            description=f"زراعة {quantity} وحدة من {crop_info['name']}"
        )
        
        expected_yield = crop_info['yield_per_unit'] * quantity
        expected_profit = expected_yield - total_cost
        
        await message.reply(
            f"🎉 **تم زراعة {crop_info['name']} بنجاح!**\n\n"
            f"{crop_info['emoji']} الكمية: {quantity} وحدة\n"
            f"💰 التكلفة: {format_number(total_cost)}$\n"
            f"⏰ وقت النضج: {crop_info['grow_time_minutes']} دقيقة\n"
            f"💎 العائد المتوقع: {format_number(expected_yield)}$\n"
            f"📈 الربح المتوقع: {format_number(expected_profit)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🌱 استخدم 'حالة المزرعة' لمتابعة نمو محاصيلك!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في زراعة المحصول: {e}")
        await message.reply("❌ حدث خطأ في عملية الزراعة")

async def harvest_command(message: Message):
    """معالجة أمر الحصاد"""
    try:
        user_crops = await get_user_crops(message.from_user.id)
        
        if not user_crops:
            await message.reply("""
🌾 **لا توجد محاصيل للحصاد**

مزرعتك فارغة! ابدأ بزراعة بعض المحاصيل أولاً.

📝 **للبدء:**
🌾 اكتب "قائمة المزروعات" لرؤية الخيارات
🌱 اكتب "زراعة [النوع]" مثل "زراعة قمح"
            """)
            return
            
        ready_crops = [crop for crop in user_crops if crop['status'] == 'ready']
        
        if not ready_crops:
            growing_crops = [crop for crop in user_crops if crop['status'] == 'growing']
            await message.reply(f"""
🌾 **لا توجد محاصيل جاهزة للحصاد حالياً**

🌱 لديك {len(growing_crops)} محاصيل لا تزال تنمو
⏰ انتظر حتى تنضج ثم اكتب "حصاد" مرة أخرى

💡 استخدم "حالة المزرعة" لمتابعة التقدم
            """)
            return
            
        await message.reply(f"🌾 تم العثور على {len(ready_crops)} محصول جاهز للحصاد!")
    except Exception as e:
        logging.error(f"خطأ في الحصاد: {e}")
        await message.reply("❌ حدث خطأ في عملية الحصاد")

async def show_farm_status(message: Message):
    """عرض حالة المزرعة"""
    try:
        user_crops = await get_user_crops(message.from_user.id)
        
        if not user_crops:
            await message.reply("""
🌱 **مزرعتك فارغة**

ابدأ بزراعة بعض المحاصيل لتحقيق الأرباح!

📝 **للبدء:**
🌾 اكتب "قائمة المزروعات" لرؤية الخيارات المتاحة
🌱 اكتب "زراعة [النوع]" مثل "زراعة قمح"
            """)
            return
            
        growing_crops = [crop for crop in user_crops if crop['status'] == 'growing']
        ready_crops = [crop for crop in user_crops if crop['status'] == 'ready']
        
        status_text = f"""
🏡 **حالة مزرعتك:**

🌱 المحاصيل النامية: {len(growing_crops)}
🌾 المحاصيل الجاهزة: {len(ready_crops)}
💧 مستوى المياه: 100%
🌡️ الطقس: مثالي للزراعة
⭐ مستوى المزرعة: 1

💡 ازرع محاصيل متنوعة لزيادة الأرباح!
        """
        await message.reply(status_text)
    except Exception as e:
        logging.error(f"خطأ في عرض حالة المزرعة: {e}")
        await message.reply("❌ حدث خطأ في عرض حالة المزرعة")

async def show_seeds_shop(message: Message):
    """عرض متجر البذور"""
    try:
        shop_text = """
🛒 **متجر البذور:**

🌾 بذور قمح - 50$ (عائد: 80$)
🌽 بذور ذرة - 120$ (عائد: 200$)
🍅 بذور طماطم - 200$ (عائد: 350$)
🥕 بذور جزر - 40$ (عائد: 65$)
🍓 بذور فراولة - 150$ (عائد: 300$)

💡 لشراء وزراعة: اكتب "زراعة [النوع]"
💡 مثال: زراعة قمح
        """
        await message.reply(shop_text)
    except Exception as e:
        logging.error(f"خطأ في عرض متجر البذور: {e}")
        await message.reply("❌ حدث خطأ في عرض متجر البذور")


async def show_planting_options(message: Message):
    """عرض خيارات الزراعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        keyboard_buttons = []
        for crop_type, crop_info in CROP_TYPES.items():
            affordable = user['balance'] >= crop_info['cost_per_unit']
            
            button_text = f"{crop_info['emoji']} {crop_info['name']} - {crop_info['cost_per_unit']}$"
            if not affordable:
                button_text = f"❌ {button_text}"
            
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"farm_plant_{crop_type}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        planting_text = "🌱 **خيارات الزراعة المتاحة:**\n\n"
        
        for crop_type, crop_info in CROP_TYPES.items():
            affordable = "✅" if user['balance'] >= crop_info['cost_per_unit'] else "❌"
            profit = crop_info['yield_per_unit'] - crop_info['cost_per_unit']
            profit_percentage = (profit / crop_info['cost_per_unit']) * 100
            
            planting_text += f"{affordable} {crop_info['emoji']} **{crop_info['name']}**\n"
            planting_text += f"   💰 التكلفة: {crop_info['cost_per_unit']}$ للوحدة\n"
            planting_text += f"   ⏰ وقت النمو: {crop_info['grow_time_hours']} ساعة\n"
            planting_text += f"   💎 العائد: {crop_info['yield_per_unit']}$ للوحدة\n"
            planting_text += f"   📈 الربح: {profit}$ ({profit_percentage:.0f}%)\n"
            planting_text += f"   📊 الحد الأقصى: {crop_info['max_quantity']} وحدة\n\n"
        
        planting_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$"
        
        await message.reply(planting_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الزراعة: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الزراعة")


async def start_planting_process(message: Message, crop_type: str, state: FSMContext):
    """بدء عملية زراعة محصول"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if crop_type not in CROP_TYPES:
            await message.reply("❌ نوع محصول غير صحيح")
            return
        
        crop_info = CROP_TYPES[crop_type]
        
        if user['balance'] < crop_info['cost_per_unit']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"{crop_info['emoji']} {crop_info['name']}\n"
                f"💰 التكلفة: {crop_info['cost_per_unit']}$ للوحدة\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        max_affordable = min(
            user['balance'] // crop_info['cost_per_unit'],
            crop_info['max_quantity']
        )
        
        await state.update_data(crop_type=crop_type)
        await state.set_state(FarmStates.waiting_crop_quantity)
        
        profit_per_unit = crop_info['yield_per_unit'] - crop_info['cost_per_unit']
        
        await message.reply(
            f"🌱 **زراعة {crop_info['name']}**\n\n"
            f"{crop_info['emoji']} المحصول: {crop_info['name']}\n"
            f"💰 التكلفة: {crop_info['cost_per_unit']}$ للوحدة\n"
            f"⏰ وقت النمو: {crop_info['grow_time_hours']} ساعة\n"
            f"💎 العائد: {crop_info['yield_per_unit']}$ للوحدة\n"
            f"📈 الربح: {profit_per_unit}$ للوحدة\n\n"
            f"💵 رصيدك: {format_number(user['balance'])}$\n"
            f"📊 أقصى كمية: {max_affordable} وحدة\n\n"
            f"كم وحدة تريد زراعة؟\n"
            f"❌ اكتب 'إلغاء' للإلغاء"
        )
        
    except Exception as e:
        logging.error(f"خطأ في بدء عملية الزراعة: {e}")
        await message.reply("❌ حدث خطأ في عملية الزراعة")


async def process_crop_quantity(message: Message, state: FSMContext):
    """معالجة كمية المحصول للزراعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            await state.clear()
            return
        
        text = message.text.strip()
        
        if text.lower() in ['إلغاء', 'cancel']:
            await state.clear()
            await message.reply("❌ تم إلغاء عملية الزراعة")
            return
        
        if not is_valid_amount(text):
            await message.reply("❌ كمية غير صحيحة. يرجى إدخال رقم صحيح")
            return
        
        quantity = int(text)
        
        # الحصول على بيانات المحصول
        data = await state.get_data()
        crop_type = data['crop_type']
        crop_info = CROP_TYPES[crop_type]
        
        # التحقق من صحة الكمية
        if quantity < crop_info['min_quantity']:
            await message.reply(f"❌ الكمية أقل من الحد الأدنى: {crop_info['min_quantity']}")
            return
        
        if quantity > crop_info['max_quantity']:
            await message.reply(f"❌ الكمية أكبر من الحد الأقصى: {crop_info['max_quantity']}")
            return
        
        total_cost = crop_info['cost_per_unit'] * quantity
        
        if total_cost > user['balance']:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"💰 التكلفة الإجمالية: {format_number(total_cost)}$\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        # تنفيذ الزراعة
        new_balance = user['balance'] - total_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # حساب وقت الحصاد
        harvest_time = datetime.now() + timedelta(hours=crop_info['grow_time_hours'])
        
        # إضافة المحصول إلى قاعدة البيانات
        await execute_query(
            "INSERT INTO user_farms (user_id, farm_type, level, productivity, last_harvest) VALUES (?, ?, ?, ?, ?)",
            (message.from_user.id, crop_type, 1, crop_info['yield_per_unit'], harvest_time.isoformat())
        )
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="crop_purchase",
            amount=total_cost,
            description=f"زراعة {quantity} وحدة من {crop_info['name']}"
        )
        
        expected_yield = crop_info['yield_per_unit'] * quantity
        expected_profit = expected_yield - total_cost
        
        await message.reply(
            f"🎉 **تمت الزراعة بنجاح!**\n\n"
            f"{crop_info['emoji']} المحصول: {crop_info['name']}\n"
            f"📊 الكمية: {quantity} وحدة\n"
            f"💰 التكلفة: {format_number(total_cost)}$\n"
            f"⏰ وقت الحصاد: {harvest_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"💎 العائد المتوقع: {format_number(expected_yield)}$\n"
            f"📈 الربح المتوقع: {format_number(expected_profit)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🌱 المحصول ينمو الآن... عد بعد {crop_info['grow_time_hours']} ساعة للحصاد!"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة كمية المحصول: {e}")
        await message.reply("❌ حدث خطأ في عملية الزراعة")
        await state.clear()


async def harvest_crops(message: Message):
    """حصاد المحاصيل الجاهزة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # الحصول على المحاصيل الجاهزة للحصاد
        ready_crops = await get_ready_crops(message.from_user.id)
        
        if not ready_crops:
            await message.reply(
                "🌱 **لا توجد محاصيل جاهزة للحصاد**\n\n"
                "تحقق من حالة محاصيلك باستخدام قائمة المزرعة"
            )
            return
        
        total_yield = 0
        total_crops = 0
        harvest_summary = {}
        
        # حصاد جميع المحاصيل الجاهزة
        for crop in ready_crops:
            crop_info = CROP_TYPES.get(crop['crop_type'], {})
            yield_amount = crop_info.get('yield_per_unit', 0) * crop['quantity']
            total_yield += yield_amount
            total_crops += crop['quantity']
            
            # تجميع المحاصيل حسب النوع
            crop_name = crop_info.get('name', 'محصول مجهول')
            if crop_name not in harvest_summary:
                harvest_summary[crop_name] = {
                    'quantity': 0,
                    'yield': 0,
                    'emoji': crop_info.get('emoji', '🌾')
                }
            harvest_summary[crop_name]['quantity'] += crop['quantity']
            harvest_summary[crop_name]['yield'] += yield_amount
            
            # تحديث حالة المحصول في قاعدة البيانات
            await execute_query(
                "UPDATE farm SET status = 'harvested' WHERE id = ?",
                (crop['id'],)
            )
        
        # إضافة العائد إلى رصيد المستخدم
        new_balance = user['balance'] + total_yield
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=0,  # النظام
            to_user_id=message.from_user.id,
            transaction_type="crop_harvest",
            amount=total_yield,
            description=f"حصاد {total_crops} وحدة محصول"
        )
        
        # إعداد نص الحصاد
        harvest_text = f"🎉 **تم الحصاد بنجاح!**\n\n"
        
        for crop_name, data in harvest_summary.items():
            harvest_text += f"{data['emoji']} **{crop_name}**: {data['quantity']} وحدة\n"
            harvest_text += f"   💰 العائد: {format_number(data['yield'])}$\n\n"
        
        harvest_text += f"📊 **ملخص الحصاد:**\n"
        harvest_text += f"🌾 إجمالي المحاصيل: {total_crops} وحدة\n"
        harvest_text += f"💰 إجمالي العائد: {format_number(total_yield)}$\n"
        harvest_text += f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
        harvest_text += f"🎯 أحسنت! استمر في الزراعة لزيادة أرباحك!"
        
        await message.reply(harvest_text)
        
    except Exception as e:
        logging.error(f"خطأ في حصاد المحاصيل: {e}")
        await message.reply("❌ حدث خطأ في عملية الحصاد")


async def show_farm_status(message: Message):
    """عرض حالة المزرعة التفصيلية"""
    try:
        user_crops = await get_user_crops(message.from_user.id)
        
        if not user_crops:
            await message.reply(
                "🌱 **مزرعتك فارغة**\n\n"
                "ابدأ بزراعة بعض المحاصيل لتحقيق الأرباح!\n"
                "استخدم /farm للوصول لقائمة الزراعة"
            )
            return
        
        status_text = "📊 **حالة المزرعة التفصيلية**\n\n"
        
        growing_crops = []
        ready_crops = []
        harvested_crops = []
        
        now = datetime.now()
        
        for crop in user_crops:
            crop_info = CROP_TYPES.get(crop['crop_type'], {})
            harvest_time = datetime.fromisoformat(crop['harvest_time'])
            
            if crop['status'] == 'harvested':
                harvested_crops.append(crop)
            elif now >= harvest_time:
                ready_crops.append(crop)
                # تحديث الحالة إلى جاهز
                await execute_query(
                    "UPDATE farm SET status = 'ready' WHERE id = ?",
                    (crop['id'],)
                )
            else:
                growing_crops.append(crop)
        
        # عرض المحاصيل التي تنمو
        if growing_crops:
            status_text += "🌱 **محاصيل تنمو:**\n"
            for crop in growing_crops:
                crop_info = CROP_TYPES.get(crop['crop_type'], {})
                harvest_time = datetime.fromisoformat(crop['harvest_time'])
                time_remaining = harvest_time - now
                hours_remaining = int(time_remaining.total_seconds() // 3600)
                minutes_remaining = int((time_remaining.total_seconds() % 3600) // 60)
                
                status_text += f"{crop_info.get('emoji', '🌾')} {crop_info.get('name', 'محصول')} x{crop['quantity']}\n"
                status_text += f"   ⏰ متبقي: {hours_remaining}س {minutes_remaining}د\n"
                status_text += f"   💎 عائد متوقع: {format_number(crop_info.get('yield_per_unit', 0) * crop['quantity'])}$\n\n"
        
        # عرض المحاصيل الجاهزة
        if ready_crops:
            status_text += "✅ **محاصيل جاهزة للحصاد:**\n"
            total_ready_yield = 0
            for crop in ready_crops:
                crop_info = CROP_TYPES.get(crop['crop_type'], {})
                yield_amount = crop_info.get('yield_per_unit', 0) * crop['quantity']
                total_ready_yield += yield_amount
                
                status_text += f"{crop_info.get('emoji', '🌾')} {crop_info.get('name', 'محصول')} x{crop['quantity']}\n"
                status_text += f"   💰 العائد: {format_number(yield_amount)}$\n\n"
            
            status_text += f"💎 **إجمالي العائد الجاهز: {format_number(total_ready_yield)}$**\n\n"
        
        # إحصائيات عامة
        if harvested_crops:
            total_harvested_yield = sum(
                CROP_TYPES.get(crop['crop_type'], {}).get('yield_per_unit', 0) * crop['quantity']
                for crop in harvested_crops
            )
            status_text += f"📊 **إحصائيات:**\n"
            status_text += f"🌾 محاصيل محصودة: {len(harvested_crops)}\n"
            status_text += f"💰 إجمالي الأرباح السابقة: {format_number(total_harvested_yield)}$\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🌾 حصاد الآن", callback_data="farm_harvest"),
                InlineKeyboardButton(text="🌱 زراعة جديدة", callback_data="farm_plant")
            ]
        ])
        
        await message.reply(status_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة المزرعة: {e}")
        await message.reply("❌ حدث خطأ في عرض حالة المزرعة")


async def get_user_crops(user_id: int):
    """الحصول على محاصيل المستخدم"""
    try:
        crops = await execute_query(
            "SELECT * FROM farm WHERE user_id = ? ORDER BY plant_time DESC",
            (user_id,),
            fetch_all=True
        )
        return crops if crops else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على محاصيل المستخدم: {e}")
        return []


async def get_ready_crops(user_id: int):
    """الحصول على المحاصيل الجاهزة للحصاد"""
    try:
        now = datetime.now().isoformat()
        crops = await execute_query(
            "SELECT * FROM farm WHERE user_id = ? AND harvest_time <= ? AND status = 'ready'",
            (user_id, now),
            fetch_all=True
        )
        return crops if crops else []
    except Exception as e:
        logging.error(f"خطأ في الحصول على المحاصيل الجاهزة: {e}")
        return []


async def auto_update_crop_status():
    """تحديث حالة المحاصيل تلقائياً (للتشغيل الدوري)"""
    try:
        now = datetime.now().isoformat()
        
        # تحديث المحاصيل التي وصلت لوقت الحصاد
        result = await execute_query(
            "UPDATE farm SET status = 'ready' WHERE harvest_time <= ? AND status = 'growing'",
            (now,)
        )
        
        if result > 0:
            logging.info(f"تم تحديث {result} محصول إلى حالة جاهز للحصاد")
        
        return result
        
    except Exception as e:
        logging.error(f"خطأ في تحديث حالة المحاصيل: {e}")
        return 0


async def get_farm_statistics(user_id: int):
    """الحصول على إحصائيات المزرعة للمستخدم"""
    try:
        stats = {}
        
        # إجمالي المحاصيل المزروعة
        total_planted = await execute_query(
            "SELECT COUNT(*) as count, SUM(quantity) as total_quantity FROM farm WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        stats['total_plantings'] = total_planted['count'] if total_planted else 0
        stats['total_crops'] = total_planted['total_quantity'] if total_planted and total_planted['total_quantity'] else 0
        
        # إجمالي الأرباح من الزراعة
        harvest_profits = await execute_query(
            "SELECT SUM(amount) as total FROM transactions WHERE to_user_id = ? AND transaction_type = 'crop_harvest'",
            (user_id,),
            fetch_one=True
        )
        
        stats['total_harvest_income'] = harvest_profits['total'] if harvest_profits and harvest_profits['total'] else 0
        
        # إجمالي الاستثمار في الزراعة
        planting_costs = await execute_query(
            "SELECT SUM(amount) as total FROM transactions WHERE from_user_id = ? AND transaction_type = 'crop_purchase'",
            (user_id,),
            fetch_one=True
        )
        
        stats['total_investment'] = planting_costs['total'] if planting_costs and planting_costs['total'] else 0
        
        # صافي الربح
        stats['net_profit'] = stats['total_harvest_income'] - stats['total_investment']
        
        return stats
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات المزرعة: {e}")
        return {}

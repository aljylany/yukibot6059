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
        
        # تحديث حالة المحاصيل أولاً
        await auto_update_crop_status()
        
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
            await message.reply("❌ يرجى كتابة نوع المحصول والكمية\n\nمثال: زراعة قمح 10")
            return
        
        crop_name = parts[1].lower()
        
        # قراءة الكمية إذا تم تحديدها
        quantity = 1  # كمية افتراضية
        if len(parts) >= 3:
            try:
                quantity = int(parts[2])
                if quantity <= 0:
                    await message.reply("❌ الكمية يجب أن تكون أكبر من صفر")
                    return
            except ValueError:
                await message.reply("❌ الكمية يجب أن تكون رقم صحيح\n\nمثال: زراعة قمح 10")
                return
        
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
        
        # التحقق من الحد الأقصى للكمية
        if quantity > crop_info['max_quantity']:
            await message.reply(f"❌ الكمية أكبر من الحد الأقصى!\n\n🌾 {crop_info['name']}\n📊 الحد الأقصى: {crop_info['max_quantity']} وحدة")
            return
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
        # تحديث حالة المحاصيل أولاً
        await auto_update_crop_status()
        
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
        # تحديث حالة المحاصيل أولاً
        await auto_update_crop_status()
        
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
            planting_text += f"   ⏰ وقت النمو: {crop_info['grow_time_minutes']} دقيقة\n"
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
            f"⏰ وقت النمو: {crop_info['grow_time_minutes']} دقيقة\n"
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
        harvest_time = datetime.now() + timedelta(minutes=crop_info['grow_time_minutes'])
        
        # إضافة المحصول إلى قاعدة البيانات
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
            f"🎉 **تمت الزراعة بنجاح!**\n\n"
            f"{crop_info['emoji']} المحصول: {crop_info['name']}\n"
            f"📊 الكمية: {quantity} وحدة\n"
            f"💰 التكلفة: {format_number(total_cost)}$\n"
            f"⏰ وقت الحصاد: {harvest_time.strftime('%Y-%m-%d %H:%M')}\n"
            f"💎 العائد المتوقع: {format_number(expected_yield)}$\n"
            f"📈 الربح المتوقع: {format_number(expected_profit)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"🌱 المحصول ينمو الآن... عد بعد {crop_info['grow_time_minutes']} دقيقة للحصاد!"
        )
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة كمية المحصول: {e}")
        await message.reply("❌ حدث خطأ في عملية الزراعة")
        await state.clear()


async def harvest_all_crops_command(message: Message):
    """حصاد جميع المحاصيل الجاهزة - أمر 'حصاد محاصيلي'"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # تحديث حالة المحاصيل أولاً
        await auto_update_crop_status()
        
        # الحصول على المحاصيل الجاهزة للحصاد
        ready_crops = await get_ready_crops(message.from_user.id)
        
        if not ready_crops:
            await message.reply(
                "🌱 **لا توجد محاصيل جاهزة للحصاد**\n\n"
                "تحقق من حالة محاصيلك باستخدام 'حالة المزرعة'"
            )
            return
        
        total_yield = 0
        total_crops = 0
        total_cost = 0
        harvest_summary = {}
        
        # حصاد جميع المحاصيل الجاهزة
        for crop in ready_crops:
            crop_info = CROP_TYPES.get(crop['crop_type'], {})
            yield_amount = crop_info.get('yield_per_unit', 0) * crop['quantity']
            cost_amount = crop_info.get('cost_per_unit', 0) * crop['quantity']
            total_yield += yield_amount
            total_cost += cost_amount
            total_crops += crop['quantity']
            
            # تجميع المحاصيل حسب النوع
            crop_name = crop_info.get('name', 'محصول مجهول')
            if crop_name not in harvest_summary:
                harvest_summary[crop_name] = {
                    'quantity': 0,
                    'yield': 0,
                    'cost': 0,
                    'profit': 0,
                    'emoji': crop_info.get('emoji', '🌾')
                }
            harvest_summary[crop_name]['quantity'] += crop['quantity']
            harvest_summary[crop_name]['yield'] += yield_amount
            harvest_summary[crop_name]['cost'] += cost_amount
            harvest_summary[crop_name]['profit'] += (yield_amount - cost_amount)
            
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
            description=f"حصاد جميع المحاصيل - {total_crops} وحدة"
        )
        
        # إعداد نص الحصاد المفصل
        total_profit = total_yield - total_cost
        profit_percentage = (total_profit / total_cost * 100) if total_cost > 0 else 0
        
        harvest_text = f"🎉 **تم حصاد جميع المحاصيل بنجاح!**\n\n"
        harvest_text += f"📊 **تفاصيل الحصاد:**\n"
        
        for crop_name, data in harvest_summary.items():
            profit_percent = (data['profit'] / data['cost'] * 100) if data['cost'] > 0 else 0
            harvest_text += f"{data['emoji']} **{crop_name}** ({data['quantity']} وحدة)\n"
            harvest_text += f"   💰 العائد: {format_number(data['yield'])}$\n"
            harvest_text += f"   💸 التكلفة: {format_number(data['cost'])}$\n"
            harvest_text += f"   📈 الربح: {format_number(data['profit'])}$ ({profit_percent:.1f}%)\n\n"
        
        harvest_text += f"💎 **ملخص الربح:**\n"
        harvest_text += f"🌾 إجمالي المحاصيل: {total_crops} وحدة\n"
        harvest_text += f"💰 إجمالي العائد: {format_number(total_yield)}$\n"
        harvest_text += f"💸 إجمالي التكلفة: {format_number(total_cost)}$\n"
        harvest_text += f"📈 إجمالي الربح: {format_number(total_profit)}$ ({profit_percentage:.1f}%)\n"
        harvest_text += f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
        harvest_text += f"🎯 تهانينا! استمر في الزراعة لزيادة أرباحك!"
        
        await message.reply(harvest_text)
        
    except Exception as e:
        logging.error(f"خطأ في حصاد جميع المحاصيل: {e}")
        await message.reply("❌ حدث خطأ في عملية الحصاد")


async def harvest_specific_crop_command(message: Message):
    """حصاد كمية معينة من نوع محدد - أمر 'حصاد [النوع] [العدد]'"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        if not message.text:
            await message.reply("❌ يرجى تحديد نوع المحصول والكمية")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply(
                "❌ يرجى كتابة نوع المحصول والكمية\n\n"
                "📝 **مثال:** حصاد قمح 5\n"
                "📝 **مثال:** حصاد طماطم 10"
            )
            return
        
        crop_name = parts[1].lower()
        
        # قراءة الكمية
        try:
            quantity = int(parts[2])
            if quantity <= 0:
                await message.reply("❌ الكمية يجب أن تكون أكبر من صفر")
                return
        except ValueError:
            await message.reply("❌ الكمية يجب أن تكون رقم صحيح")
            return
        
        # البحث عن نوع المحصول
        crop_type = None
        for key, crop_info in CROP_TYPES.items():
            if crop_name in crop_info['name'].lower():
                crop_type = key
                break
                
        if not crop_type:
            available_crops = ", ".join([crop['name'] for crop in CROP_TYPES.values()])
            await message.reply(
                f"❌ نوع المحصول غير متاح\n\n"
                f"📝 **المحاصيل المتاحة:** {available_crops}"
            )
            return
        
        # تحديث حالة المحاصيل أولاً
        await auto_update_crop_status()
        
        # الحصول على المحاصيل الجاهزة من النوع المحدد
        ready_crops = await execute_query(
            "SELECT * FROM farm WHERE user_id = ? AND crop_type = ? AND status = 'ready' ORDER BY plant_time ASC",
            (message.from_user.id, crop_type),
            fetch_all=True
        )
        
        if not ready_crops:
            crop_info = CROP_TYPES[crop_type]
            await message.reply(
                f"❌ لا توجد محاصيل {crop_info['emoji']} **{crop_info['name']}** جاهزة للحصاد\n\n"
                "استخدم 'حالة المزرعة' لمتابعة نمو محاصيلك"
            )
            return
        
        # حساب الكمية المتاحة
        available_quantity = sum(crop['quantity'] for crop in ready_crops)
        
        if quantity > available_quantity:
            crop_info = CROP_TYPES[crop_type]
            await message.reply(
                f"❌ الكمية المطلوبة أكبر من المتاح!\n\n"
                f"{crop_info['emoji']} **{crop_info['name']}**\n"
                f"📊 المتاح للحصاد: {available_quantity} وحدة\n"
                f"🔢 المطلوب: {quantity} وحدة"
            )
            return
        
        # حصاد الكمية المطلوبة
        remaining_to_harvest = quantity
        harvested_crops = []
        
        for crop in ready_crops:
            if remaining_to_harvest <= 0:
                break
                
            if crop['quantity'] <= remaining_to_harvest:
                # حصاد المحصول بالكامل
                harvested_crops.append({
                    'id': crop['id'],
                    'quantity': crop['quantity']
                })
                remaining_to_harvest -= crop['quantity']
                
                # تحديث حالة المحصول
                await execute_query(
                    "UPDATE farm SET status = 'harvested' WHERE id = ?",
                    (crop['id'],)
                )
            else:
                # حصاد جزء من المحصول
                harvested_crops.append({
                    'id': crop['id'],
                    'quantity': remaining_to_harvest
                })
                
                # تحديث كمية المحصول المتبقي
                new_quantity = crop['quantity'] - remaining_to_harvest
                await execute_query(
                    "UPDATE farm SET quantity = ? WHERE id = ?",
                    (new_quantity, crop['id'])
                )
                remaining_to_harvest = 0
        
        # حساب العائد والربح
        crop_info = CROP_TYPES[crop_type]
        yield_amount = crop_info['yield_per_unit'] * quantity
        cost_amount = crop_info['cost_per_unit'] * quantity
        profit_amount = yield_amount - cost_amount
        profit_percentage = (profit_amount / cost_amount * 100) if cost_amount > 0 else 0
        
        # إضافة العائد إلى رصيد المستخدم
        new_balance = user['balance'] + yield_amount
        await update_user_balance(message.from_user.id, new_balance)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=0,  # النظام
            to_user_id=message.from_user.id,
            transaction_type="crop_harvest",
            amount=yield_amount,
            description=f"حصاد {quantity} وحدة من {crop_info['name']}"
        )
        
        # إعداد نص الحصاد المفصل
        harvest_text = f"🎉 **تم الحصاد بنجاح!**\n\n"
        harvest_text += f"{crop_info['emoji']} **{crop_info['name']}**\n"
        harvest_text += f"📊 الكمية المحصودة: {quantity} وحدة\n\n"
        
        harvest_text += f"💎 **تفاصيل الربح:**\n"
        harvest_text += f"💰 إجمالي العائد: {format_number(yield_amount)}$\n"
        harvest_text += f"💸 إجمالي التكلفة: {format_number(cost_amount)}$\n"
        harvest_text += f"📈 صافي الربح: {format_number(profit_amount)}$ ({profit_percentage:.1f}%)\n"
        harvest_text += f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
        
        # عرض الكمية المتبقية إن وجدت
        remaining_quantity = available_quantity - quantity
        if remaining_quantity > 0:
            harvest_text += f"🌾 متبقي للحصاد: {remaining_quantity} وحدة من {crop_info['name']}\n\n"
        
        harvest_text += f"🎯 ممتاز! استمر في الزراعة والحصاد!"
        
        await message.reply(harvest_text)
        
    except Exception as e:
        logging.error(f"خطأ في حصاد المحصول المحدد: {e}")
        await message.reply("❌ حدث خطأ في عملية الحصاد")


async def harvest_crops(message: Message):
    """حصاد المحاصيل الجاهزة - الدالة القديمة للتوافق"""
    await harvest_all_crops_command(message)


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
        
        # إضافة أوامر الحصاد والزراعة النصية
        if ready_crops:
            status_text += "📝 **أوامر متاحة:**\n"
            status_text += "🌾 **حصاد محاصيلي** - لحصاد جميع المحاصيل الجاهزة\n"
            status_text += "🌾 **حصاد [النوع] [العدد]** - لحصاد كمية معينة من نوع محدد\n"
            status_text += "🌱 **زراعة** - لبدء زراعة محاصيل جديدة\n\n"
        else:
            status_text += "📝 **أوامر متاحة:**\n"
            status_text += "🌱 **زراعة** - لبدء زراعة محاصيل جديدة\n\n"
        
        await message.reply(status_text)
        
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


async def handle_harvest_callback(callback):
    """معالج زر حصاد الآن"""
    try:
        user_id = callback.from_user.id
        
        # الحصول على المحاصيل الجاهزة
        ready_crops = await get_ready_crops(user_id)
        
        if not ready_crops:
            await callback.answer("❌ لا توجد محاصيل جاهزة للحصاد!")
            return
        
        # حصاد جميع المحاصيل الجاهزة
        total_yield = 0
        harvested_count = 0
        
        for crop in ready_crops:
            crop_info = CROP_TYPES.get(crop['crop_type'], {})
            yield_amount = crop_info.get('yield_per_unit', 0) * crop['quantity']
            total_yield += yield_amount
            harvested_count += 1
            
            # تحديث حالة المحصول إلى محصود
            await execute_query(
                "UPDATE farm SET status = 'harvested' WHERE id = ?",
                (crop['id'],)
            )
        
        # إضافة المال للمستخدم
        from database.operations import update_user_balance
        await update_user_balance(user_id, total_yield)
        
        # إضافة XP للمستخدم
        from modules.leveling import add_xp
        await add_xp(user_id, harvested_count * 10)  # 10 XP لكل محصول
        
        await callback.answer(f"🎉 تم حصاد {harvested_count} محصول بقيمة {format_number(total_yield)}$!")
        
        # تحديث عرض حالة المزرعة
        await show_farm_status(callback.message)
        
    except Exception as e:
        logging.error(f"خطأ في حصاد المحاصيل: {e}")
        await callback.answer("❌ حدث خطأ أثناء الحصاد")


async def handle_plant_callback(callback):
    """معالج زر زراعة جديدة"""
    try:
        # عرض قائمة المحاصيل المتاحة للزراعة
        crops_text = "🌱 **اختر نوع المحصول للزراعة:**\n\n"
        
        keyboard_buttons = []
        row = []
        
        for crop_type, crop_info in CROP_TYPES.items():
            crops_text += f"{crop_info['emoji']} **{crop_info['name']}**\n"
            crops_text += f"   💰 التكلفة: {format_number(crop_info['cost_per_unit'])}$ للوحدة\n"
            crops_text += f"   ⏰ وقت النمو: {crop_info['grow_time_minutes']} دقيقة\n"
            crops_text += f"   💎 العائد: {format_number(crop_info['yield_per_unit'])}$ للوحدة\n"
            crops_text += f"   📊 الحد الأقصى: {crop_info['max_quantity']} وحدة\n\n"
            
            # إضافة زر للمحصول
            button = InlineKeyboardButton(
                text=f"{crop_info['emoji']} {crop_info['name']}", 
                callback_data=f"farm_plant_{crop_type}"
            )
            row.append(button)
            
            # إضافة صف جديد كل زرين
            if len(row) == 2:
                keyboard_buttons.append(row)
                row = []
        
        # إضافة أي أزرار متبقية
        if row:
            keyboard_buttons.append(row)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(crops_text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الزراعة: {e}")
        await callback.answer("❌ حدث خطأ أثناء عرض قائمة الزراعة")


async def handle_specific_plant_callback(callback):
    """معالج زر زراعة محصول محدد"""
    try:
        # استخراج نوع المحصول من callback_data
        crop_type = callback.data.split('farm_plant_')[1]
        
        if crop_type not in CROP_TYPES:
            await callback.answer("❌ نوع محصول غير صالح!")
            return
        
        crop_info = CROP_TYPES[crop_type]
        
        # عرض معلومات المحصول وطلب الكمية
        plant_text = f"🌱 **زراعة {crop_info['name']}**\n\n"
        plant_text += f"{crop_info['emoji']} **المحصول:** {crop_info['name']}\n"
        plant_text += f"💰 **التكلفة:** {format_number(crop_info['cost_per_unit'])}$ للوحدة\n"
        plant_text += f"⏰ **وقت النمو:** {crop_info['grow_time_minutes']} دقيقة\n"
        plant_text += f"💎 **العائد:** {format_number(crop_info['yield_per_unit'])}$ للوحدة\n"
        plant_text += f"📊 **الحد الأقصى:** {crop_info['max_quantity']} وحدة\n\n"
        plant_text += f"📝 **لزراعة هذا المحصول، استخدم الأمر:**\n"
        plant_text += f"`زراعة {crop_info['name'].split()[0]} [الكمية]`\n\n"
        plant_text += f"**مثال:** زراعة {crop_info['name'].split()[0]} 10"
        
        await callback.message.edit_text(plant_text)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في زراعة محصول محدد: {e}")
        await callback.answer("❌ حدث خطأ أثناء الزراعة")


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

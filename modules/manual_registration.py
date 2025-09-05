"""
نظام التسجيل اليدوي المطور
Enhanced Manual Registration System
"""

import logging
from datetime import datetime
from typing import Optional, Dict, Any
from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.operations import execute_query, get_user
from utils.helpers import format_number

# إعداد التوجيه
router = Router()

# حالات FSM للتسجيل
class RegistrationStates(StatesGroup):
    waiting_for_name = State()
    choosing_gender = State()
    choosing_country = State()
    choosing_bank = State()
    confirming_registration = State()

# قائمة البلدان العربية
ARAB_COUNTRIES = {
    "🇸🇦": "السعودية",
    "🇦🇪": "الإمارات",
    "🇪🇬": "مصر",
    "🇯🇴": "الأردن",
    "🇰🇼": "الكويت",
    "🇶🇦": "قطر",
    "🇧🇭": "البحرين",
    "🇴🇲": "عمان",
    "🇱🇧": "لبنان",
    "🇸🇾": "سوريا",
    "🇮🇶": "العراق",
    "🇾🇪": "اليمن",
    "🇱🇾": "ليبيا",
    "🇹🇳": "تونس",
    "🇩🇿": "الجزائر",
    "🇲🇦": "المغرب",
    "🇸🇩": "السودان",
    "🇸🇴": "الصومال",
    "🇩🇯": "جيبوتي",
    "🇰🇲": "جزر القمر",
    "🇲🇷": "موريتانيا",
    "🇵🇸": "فلسطين"
}

# خيارات الجنس
GENDER_OPTIONS = {
    "male": {"emoji": "👨", "text": "ذكر"},
    "female": {"emoji": "👩", "text": "أنثى"}
}

# أنواع البنوك مع مزاياها
BANK_TYPES = {
    "الأهلي": {
        "name": "البنك الأهلي",
        "emoji": "🏛️",
        "initial_bonus": 2000,
        "daily_salary": (100, 200),
        "interest_rate": 0.03,
        "description": "بنك تقليدي بمكافآت عالية"
    },
    "الراجحي": {
        "name": "مصرف الراجحي", 
        "emoji": "🏦",
        "initial_bonus": 1500,
        "daily_salary": (150, 250),
        "interest_rate": 0.025,
        "description": "مصرف إسلامي بأرباح ثابتة"
    },
    "سامبا": {
        "name": "بنك سامبا",
        "emoji": "💳",
        "initial_bonus": 1800,
        "daily_salary": (120, 180),
        "interest_rate": 0.035,
        "description": "بنك حديث بفوائد مرتفعة"
    },
    "الرياض": {
        "name": "بنك الرياض",
        "emoji": "🏢",
        "initial_bonus": 1600,
        "daily_salary": (130, 200),
        "interest_rate": 0.028,
        "description": "بنك متوازن للجميع"
    }
}


async def is_user_registered(user_id: int) -> bool:
    """التحقق من تسجيل المستخدم"""
    try:
        user = await get_user(user_id)
        return user.get('is_registered', False) if user else False
    except Exception as e:
        logging.error(f"خطأ في فحص تسجيل المستخدم {user_id}: {e}")
        return False


async def create_unregistered_user(user_id: int, username: str = "", first_name: str = "") -> bool:
    """إنشاء مستخدم غير مسجل (للتتبع الأساسي فقط)"""
    try:
        import aiosqlite
        # استخدام قاعدة البيانات المحلية مباشرة
        DATABASE_URL = "bot_database.db"
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, username, first_name, is_registered, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, username or "", first_name or "", False, 
                 datetime.now().isoformat(), datetime.now().isoformat())
            )
            await db.commit()
        return True
    except Exception as e:
        logging.error(f"خطأ في إنشاء المستخدم غير المسجل {user_id}: {e}")
        return False


async def complete_user_registration(user_id: int, full_name: str, gender: str, 
                                   country: str, bank_type: str) -> bool:
    """إكمال تسجيل المستخدم"""
    try:
        bank_info = BANK_TYPES[bank_type]
        
        import aiosqlite
        # استخدام قاعدة البيانات المحلية مباشرة
        DATABASE_URL = "bot_database.db"
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                UPDATE users SET 
                    first_name = ?, gender = ?, country = ?, bank_type = ?,
                    is_registered = ?, balance = ?, bank_balance = ?,
                    updated_at = ?
                WHERE user_id = ?
                """,
                (full_name, gender, country, bank_type, True, 
                 bank_info['initial_bonus'], 0, 
                 datetime.now().isoformat(), user_id)
            )
            await db.commit()
        
        # إضافة معاملة المكافأة
        try:
            from database.operations import add_transaction
            await add_transaction(
                user_id=user_id,
                transaction_type="registration_bonus", 
                amount=bank_info['initial_bonus'],
                description=f"مكافأة التسجيل - {bank_info['name']}"
            )
        except Exception as trans_error:
            logging.warning(f"تعذر إضافة معاملة التسجيل: {trans_error}")
        
        logging.info(f"تم إكمال تسجيل المستخدم: {user_id} - {full_name}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إكمال تسجيل المستخدم {user_id}: {e}")
        return False


async def update_user_missing_data(user_id: int, full_name: str = None, 
                                 gender: str = None, country: str = None) -> bool:
    """تحديث البيانات الناقصة للمستخدم الموجود"""
    try:
        # الحصول على البيانات الحالية
        from database.operations import get_user
        current_user = await get_user(user_id)
        if not current_user:
            return False
        
        # إعداد البيانات المحدثة
        updated_name = full_name if full_name else current_user.get('first_name', '')
        updated_gender = gender if gender else current_user.get('gender', '')
        updated_country = country if country else current_user.get('country', '')
        
        import aiosqlite
        # استخدام قاعدة البيانات المحلية مباشرة
        DATABASE_URL = "bot_database.db"
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                UPDATE users SET 
                    first_name = ?, gender = ?, country = ?, is_registered = ?, updated_at = ?
                WHERE user_id = ?
                """,
                (updated_name, updated_gender, updated_country, True, 
                 datetime.now().isoformat(), user_id)
            )
            await db.commit()
        
        logging.info(f"تم تحديث بيانات المستخدم: {user_id} - {updated_name}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في تحديث بيانات المستخدم {user_id}: {e}")
        return False


def create_registration_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح التسجيل"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 سجل حساب جديد", callback_data="start_registration")]
    ])


def create_gender_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح اختيار الجنس"""
    buttons = []
    for key, gender in GENDER_OPTIONS.items():
        buttons.append([InlineKeyboardButton(
            text=f"{gender['emoji']} {gender['text']}", 
            callback_data=f"gender_{key}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_country_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح اختيار البلد"""
    buttons = []
    row = []
    for flag, country in ARAB_COUNTRIES.items():
        row.append(InlineKeyboardButton(
            text=f"{flag} {country}", 
            callback_data=f"country_{country}"
        ))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def create_bank_keyboard() -> InlineKeyboardMarkup:
    """إنشاء لوحة مفاتيح اختيار البنك"""
    buttons = []
    for bank_key, bank_info in BANK_TYPES.items():
        buttons.append([InlineKeyboardButton(
            text=f"{bank_info['emoji']} {bank_info['name']}", 
            callback_data=f"bank_{bank_key}"
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def send_registration_required_message(message: Message):
    """إرسال رسالة تطلب التسجيل"""
    welcome_text = """
🔒 **مرحباً بك في بوت يوكي المطور!**

🚨 **للوصول لميزات البوت، يجب تسجيل حساب أولاً**

📋 **ما ستحتاج لتقديمه:**
• 📝 الاسم الكامل
• 👤 الجنس (ذكر/أنثى)
• 🌍 البلد
• 🏦 البنك المفضل

💰 **مزايا التسجيل:**
• مكافأة ترحيب تصل إلى 2000$
• راتب يومي من 100-250$
• إمكانية الوصول لجميع الألعاب
• نظام مصرفي متكامل
• إحصائيات شخصية مفصلة

🎯 **اضغط الزر أدناه لبدء التسجيل:**
    """
    
    await message.reply(welcome_text, reply_markup=create_registration_keyboard())


async def send_completion_required_message(message: Message, missing_data: list):
    """إرسال رسالة تطلب إكمال البيانات الناقصة"""
    completion_text = f"""
🔄 **إكمال بيانات حسابك البنكي**

📝 **البيانات الناقصة:** {', '.join(missing_data)}

💡 **لماذا نحتاج هذه البيانات؟**
• تخصيص تجربتك في البوت
• إتاحة المميزات الكاملة 
• أمان أفضل لحسابك
• إحصائيات شخصية دقيقة

✨ **المميزات بعد الإكمال:**
• وصول كامل لجميع الألعاب
• مكافآت إضافية حصرية
• نظام ترقية محسن
• تجربة شخصية مميزة

🎯 **اضغط الزر أدناه لإكمال بياناتك:**
    """
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 إكمال البيانات الناقصة", callback_data="complete_missing_data")]
    ])
    
    await message.reply(completion_text, reply_markup=keyboard)


@router.callback_query(F.data == "start_registration")
async def start_registration_process(callback: CallbackQuery, state: FSMContext):
    """بدء عملية التسجيل"""
    try:
        await callback.answer("🚀 بدء التسجيل...")
        
        await callback.message.edit_text(
            "📝 **خطوة 1/4: الاسم الكامل**\n\n"
            "🔤 **اكتب اسمك الكامل:**\n"
            "• يفضل الاسم الحقيقي\n"
            "• سيظهر في ملفك الشخصي\n"
            "• يمكن تغييره لاحقاً\n\n"
            "✍️ اكتب اسمك الآن:"
        )
        
        await state.set_state(RegistrationStates.waiting_for_name)
        
    except Exception as e:
        logging.error(f"خطأ في بدء التسجيل: {e}")


@router.message(RegistrationStates.waiting_for_name)
async def handle_name_input(message: Message, state: FSMContext):
    """معالجة إدخال الاسم"""
    try:
        if not message.text or len(message.text.strip()) < 2:
            await message.reply("❌ يرجى إدخال اسم صحيح (أكثر من حرفين)")
            return
        
        full_name = message.text.strip()
        await state.update_data(full_name=full_name)
        
        # التحقق إذا كان هذا إكمال بيانات أم تسجيل جديد
        data = await state.get_data()
        is_completion = data.get('is_completion', False)
        
        if is_completion:
            # إكمال البيانات - نحتاج للتحقق من البيانات الناقصة الأخرى
            user = await get_user(message.from_user.id)
            gender = user.get('gender', '') if user else ''
            country = user.get('country', '') if user else ''
            
            if not gender or str(gender).strip() == '':
                await message.reply(
                    f"✅ **تم حفظ الاسم:** {full_name}\n\n"
                    "👤 **البيانات الناقصة: الجنس**\n\n"
                    "🔽 اختر جنسك من الأزرار أدناه:",
                    reply_markup=create_gender_keyboard()
                )
                await state.set_state(RegistrationStates.choosing_gender)
            elif not country or str(country).strip() == '':
                # حفظ الاسم وانتقال للبلد
                success = await update_user_missing_data(message.from_user.id, full_name=full_name)
                if not success:
                    await message.reply("❌ حدث خطأ في حفظ البيانات")
                    await state.clear()
                    return
                await message.reply(
                    f"✅ **تم حفظ الاسم:** {full_name}\n\n"
                    "🌍 **البيانات الناقصة: البلد**\n\n"
                    "🔽 اختر بلدك من القائمة أدناه:",
                    reply_markup=create_country_keyboard()
                )
                await state.set_state(RegistrationStates.choosing_country)
            else:
                # فقط الاسم ناقص - تحديث وإنهاء
                success = await update_user_missing_data(message.from_user.id, full_name=full_name)
                if success:
                    await message.reply(
                        f"✅ **تم إكمال بياناتك بنجاح!**\n\n"
                        f"📝 **الاسم:** {full_name}\n"
                        f"{'👨' if gender == 'male' else '👩' if gender == 'female' else '🧑'} **الجنس:** {'ذكر' if gender == 'male' else 'أنثى' if gender == 'female' else gender}\n"
                        f"🌍 **البلد:** {country}\n\n"
                        "🎉 **الآن يمكنك استخدام جميع ميزات البوت!**"
                    )
                else:
                    await message.reply("❌ حدث خطأ في حفظ البيانات")
                await state.clear()
        else:
            # تسجيل جديد عادي
            await message.reply(
                f"✅ **تم حفظ الاسم:** {full_name}\n\n"
                "👤 **خطوة 2/4: الجنس**\n\n"
                "🔽 اختر جنسك من الأزرار أدناه:",
                reply_markup=create_gender_keyboard()
            )
            await state.set_state(RegistrationStates.choosing_gender)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة الاسم: {e}")


@router.callback_query(F.data.startswith("gender_"))
async def handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار الجنس"""
    try:
        gender_key = callback.data.split("_")[1]
        gender_info = GENDER_OPTIONS[gender_key]
        
        await state.update_data(gender=gender_key)
        await callback.answer(f"تم اختيار: {gender_info['text']}")
        
        await callback.message.edit_text(
            f"✅ **تم اختيار الجنس:** {gender_info['emoji']} {gender_info['text']}\n\n"
            "🌍 **خطوة 3/4: البلد**\n\n"
            "🔽 اختر بلدك من القائمة أدناه:",
            reply_markup=create_country_keyboard()
        )
        
        await state.set_state(RegistrationStates.choosing_country)
        
    except Exception as e:
        logging.error(f"خطأ في اختيار الجنس: {e}")


@router.callback_query(F.data.startswith("country_"))
async def handle_country_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار البلد"""
    try:
        country = callback.data.split("_", 1)[1]
        await state.update_data(country=country)
        
        # العثور على علم البلد
        country_flag = "🌍"
        for flag, name in ARAB_COUNTRIES.items():
            if name == country:
                country_flag = flag
                break
        
        await callback.answer(f"تم اختيار: {country}")
        
        # إنشاء نص معلومات البنوك
        banks_info = "🏦 **معلومات البنوك المتاحة:**\n\n"
        for bank_key, bank_info in BANK_TYPES.items():
            banks_info += f"{bank_info['emoji']} **{bank_info['name']}**\n"
            banks_info += f"• مكافأة التسجيل: {format_number(bank_info['initial_bonus'])}$\n"
            banks_info += f"• الراتب اليومي: {bank_info['daily_salary'][0]}-{bank_info['daily_salary'][1]}$\n"
            banks_info += f"• معدل الفائدة: {bank_info['interest_rate']*100:.1f}%\n"
            banks_info += f"• الوصف: {bank_info['description']}\n\n"
        
        await callback.message.edit_text(
            f"✅ **تم اختيار البلد:** {country_flag} {country}\n\n"
            "🏦 **خطوة 4/4: اختيار البنك**\n\n"
            f"{banks_info}"
            "🔽 اختر البنك المفضل لك:",
            reply_markup=create_bank_keyboard()
        )
        
        await state.set_state(RegistrationStates.choosing_bank)
        
    except Exception as e:
        logging.error(f"خطأ في اختيار البلد: {e}")


@router.callback_query(F.data.startswith("bank_"))
async def handle_bank_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار البنك وإتمام التسجيل"""
    try:
        bank_key = callback.data.split("_", 1)[1]
        bank_info = BANK_TYPES[bank_key]
        
        # الحصول على بيانات التسجيل
        data = await state.get_data()
        full_name = data.get('full_name', '')
        gender = data.get('gender', '')
        country = data.get('country', '')
        
        await callback.answer(f"تم اختيار: {bank_info['name']}")
        
        # إتمام التسجيل في قاعدة البيانات
        success = await complete_user_registration(
            user_id=callback.from_user.id,
            full_name=full_name,
            gender=gender,
            country=country,
            bank_type=bank_key
        )
        
        if success:
            # العثور على علم البلد
            country_flag = "🌍"
            for flag, name in ARAB_COUNTRIES.items():
                if name == country:
                    country_flag = flag
                    break
            
            gender_emoji = GENDER_OPTIONS.get(gender, {}).get('emoji', '🧑')
            gender_text = GENDER_OPTIONS.get(gender, {}).get('text', 'غير محدد')
            
            success_message = f"""
🎉 **تم إنشاء حسابك بنجاح!**

📋 **معلومات حسابك:**
• 📝 الاسم: {full_name}
• {gender_emoji} الجنس: {gender_text}
• {country_flag} البلد: {country}
• {bank_info['emoji']} البنك: {bank_info['name']}

💰 **المكافآت المستلمة:**
• 💵 مكافأة التسجيل: {format_number(bank_info['initial_bonus'])}$
• 📈 راتب يومي: {bank_info['daily_salary'][0]}-{bank_info['daily_salary'][1]}$
• 📊 معدل الفائدة: {bank_info['interest_rate']*100:.1f}%

🎮 **يمكنك الآن:**
• استخدام جميع ميزات البوت
• اللعب مع الأصدقاء
• تداول الأسهم والاستثمار
• إدارة أموالك وحسابك المصرفي

🚀 **مرحباً بك في عالم يوكي الاقتصادي!**

💡 اكتب "رصيد" لعرض رصيدك الحالي
            """
            
            await callback.message.edit_text(success_message)
            
            # إرسال إشعار للقناة الفرعية (إن وجدت)
            try:
                from modules.notification_manager import NotificationManager
                notification_manager = NotificationManager(callback.bot)
                await notification_manager.send_new_user_notification(
                    user_id=callback.from_user.id,
                    username=callback.from_user.username or "غير محدد",
                    full_name=full_name,
                    country=country,
                    bank=bank_info['name']
                )
            except Exception as notif_error:
                logging.warning(f"لم يتم إرسال إشعار المستخدم الجديد: {notif_error}")
        else:
            await callback.message.edit_text(
                "❌ **حدث خطأ في إنشاء الحساب**\n\n"
                "🔄 يرجى المحاولة مرة أخرى لاحقاً\n"
                "أو التواصل مع الدعم الفني"
            )
        
        # مسح حالة التسجيل
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في اختيار البنك: {e}")
        await callback.message.edit_text(
            "❌ حدث خطأ في إتمام التسجيل. يرجى المحاولة مرة أخرى."
        )


@router.callback_query(F.data == "complete_missing_data")
async def start_completion_process(callback: CallbackQuery, state: FSMContext):
    """بدء عملية إكمال البيانات الناقصة"""
    try:
        await callback.answer("🔄 بدء إكمال البيانات...")
        
        # الحصول على بيانات المستخدم الحالية
        user = await get_user(callback.from_user.id)
        
        if not user:
            await callback.message.edit_text("❌ لم يتم العثور على حسابك!")
            return
        
        # فحص البيانات الناقصة
        full_name = user.get('first_name', '') if user else ''
        gender = user.get('gender', '') if user else ''
        country = user.get('country', '') if user else ''
        
        # تحديد الخطوة الأولى المطلوبة
        if not full_name or str(full_name).strip() == '':
            # البدء بطلب الاسم
            await callback.message.edit_text(
                "📝 **إكمال البيانات - الاسم الكامل**\n\n"
                "🔤 **اكتب اسمك الكامل:**\n"
                "• يفضل الاسم الحقيقي\n"
                "• سيظهر في ملفك الشخصي\n"
                "• يمكن تغييره لاحقاً\n\n"
                "✍️ اكتب اسمك الآن:"
            )
            await state.set_data({'is_completion': True})
            await state.set_state(RegistrationStates.waiting_for_name)
        elif not gender or gender.strip() == '':
            # طلب الجنس
            await callback.message.edit_text(
                "👤 **إكمال البيانات - الجنس**\n\n"
                "🔽 اختر جنسك من الأزرار أدناه:",
                reply_markup=create_gender_keyboard()
            )
            await state.set_state(RegistrationStates.choosing_gender)
        elif not country or str(country).strip() == '':
            # طلب البلد
            await callback.message.edit_text(
                "🌍 **إكمال البيانات - البلد**\n\n"
                "🔽 اختر بلدك من القائمة أدناه:",
                reply_markup=create_country_keyboard()
            )
            await state.set_state(RegistrationStates.choosing_country)
        else:
            # جميع البيانات موجودة
            await callback.message.edit_text(
                "✅ **حسابك مكتمل بالفعل!**\n\n"
                "جميع بياناتك موجودة ولا تحتاج لإكمال أي شيء"
            )
        
    except Exception as e:
        logging.error(f"خطأ في بدء إكمال البيانات: {e}")
        await callback.message.edit_text("❌ حدث خطأ في بدء إكمال البيانات")


# تصدير الوظائف المهمة
__all__ = [
    'router',
    'is_user_registered', 
    'create_unregistered_user',
    'send_registration_required_message'
]
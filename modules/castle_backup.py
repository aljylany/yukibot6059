"""
وحدة القلعة المحدثة والمصلحة - نظام شامل للقلاع مع المتجر ونظام البحث المحدث
Updated and Fixed Castle Module with Shop System and Enhanced Features
"""

import logging
import random
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import CastleStates
from utils.helpers import format_number

# نظام مستويات اللاعبين
PLAYER_LEVELS = {
    "master": {"max_level": 1000, "auto_level": True},  # الأسياد مستوى 1000 تلقائياً
    "regular": {"max_level": 100, "auto_level": False}  # اللاعبين العاديين حد أقصى 100
}

# مراحل تطوير القلعة
CASTLE_DEVELOPMENT_STAGES = {
    1: {"name": "أساسات القلعة", "cost": 5000, "description": "بناء الأساسات الأولى للقلعة"},
    2: {"name": "بناء الجدران", "cost": 8000, "description": "بناء الجدران الدفاعية"},
    3: {"name": "تجهيز الحراس", "cost": 12000, "description": "توظيف الحراس والعمال"},
    4: {"name": "بناء الأبراج", "cost": 18000, "description": "بناء أبراج المراقبة والدفاع"},
    5: {"name": "حفر الخنادق", "cost": 25000, "description": "حفر خنادق دفاعية حول القلعة"},
    6: {"name": "تطوير المنطقة", "cost": 35000, "description": "توسيع منطقة القلعة"},
    7: {"name": "بناء القرى", "cost": 50000, "description": "بناء قرى تابعة للقلعة"},
    8: {"name": "تشييد المدينة", "cost": 75000, "description": "تطوير مدينة كاملة"},
    9: {"name": "إنشاء الإمارة", "cost": 100000, "description": "تأسيس إمارة تحت حكم القلعة"},
    10: {"name": "بناء المملكة", "cost": 150000, "description": "إنشاء مملكة كاملة"}
}

# الموارد المطلوبة للبناء
REQUIRED_RESOURCES = {
    "money": "المال",
    "gold": "الذهب", 
    "stones": "الحجارة",
    "workers": "العمال",
    "walls": "الأسوار",
    "towers": "الأبراج",
    "moats": "الخنادق"
}

# كنوز البحث
TREASURE_TYPES = {
    "money": {"min": 500, "max": 2000, "chance": 40, "emoji": "💰"},
    "gold": {"min": 100, "max": 800, "chance": 25, "emoji": "🏆"},
    "stones": {"min": 50, "max": 300, "chance": 20, "emoji": "🪨"},
    "workers": {"min": 10, "max": 50, "chance": 10, "emoji": "👷"},
    "nothing": {"chance": 5, "emoji": "❌"}
}

# أسعار متجر القلعة
CASTLE_SHOP_ITEMS = {
    "gold": {
        "name": "ذهب",
        "emoji": "🏆",
        "base_price": 100,  # سعر الوحدة الواحدة
        "currency": "money",
        "description": "ذهب نقي لتطوير القلعة",
        "max_purchase": 1000
    },
    "stones": {
        "name": "حجارة",
        "emoji": "🪨",
        "base_price": 50,
        "currency": "money",
        "description": "حجارة قوية للبناء والتشييد",
        "max_purchase": 2000
    },
    "workers": {
        "name": "عمال",
        "emoji": "👷",
        "base_price": 200,
        "currency": "money",
        "description": "عمال مهرة للعمل في القلعة",
        "max_purchase": 500
    },
    "money_upgrade": {
        "name": "تحسين المال",
        "emoji": "💰",
        "base_price": 10,
        "currency": "gold",
        "description": "زيادة دخل المال من البحث",
        "max_purchase": 100
    }
}

# ===== دوال قاعدة البيانات المساعدة =====

async def set_user_level(user_id: int, level: int) -> bool:
    """تعيين مستوى المستخدم"""
    try:
        await execute_query(
            "UPDATE users SET level = ? WHERE user_id = ?",
            (level, user_id)
        )
        return True
    except Exception:
        return False

async def get_user_level(user_id: int) -> int:
    """الحصول على مستوى المستخدم"""
    try:
        # التحقق من كون المستخدم سيداً أولاً
        from config.hierarchy import get_user_admin_level, AdminLevel
        
        admin_level = await get_user_admin_level(user_id)
        
        if admin_level in [AdminLevel.MASTER, AdminLevel.SUPER_MASTER]:
            # تعيين مستوى عالي للأسياد تلقائياً
            await set_user_level(user_id, 1000)
            return 1000
        
        # للمستخدمين العاديين
        user = await get_user(user_id)
        if user and 'level' in user:
            return user['level']
        return 1
    except Exception:
        return 1

async def create_castle(user_id: int, castle_name: str) -> bool:
    """إنشاء قلعة جديدة للمستخدم"""
    try:
        # التحقق من عدم وجود قلعة
        existing_castle = await get_user_castle(user_id)
        if existing_castle:
            return False
        
        # إنشاء castle_id فريد
        castle_id = f"castle_{user_id}_{random.randint(1000, 9999)}"
        
        await execute_query(
            """
            INSERT INTO user_castles 
            (user_id, name, castle_id, level, defense_points, attack_points, gold_storage, 
             walls_level, towers_level, moats_level, warriors_count, wins, losses, total_battles)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, castle_name, castle_id, 1, 100, 50, 0, 1, 1, 1, 10, 0, 0, 0)
        )
        
        # إنشاء موارد أولية
        await execute_query(
            """
            INSERT OR REPLACE INTO user_resources (user_id, money, gold, stones, workers)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, 0, 0, 0, 0)
        )
        
        logging.info(f"تم إنشاء قلعة جديدة للمستخدم {user_id}: {castle_name}")
        return True
    except Exception as e:
        logging.error(f"خطأ في إنشاء قلعة للمستخدم {user_id}: {e}")
        return False

async def get_user_castle(user_id: int):
    """الحصول على قلعة المستخدم"""
    try:
        return await execute_query(
            "SELECT * FROM user_castles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
    except Exception as e:
        logging.error(f"خطأ في الحصول على قلعة المستخدم {user_id}: {e}")
        return None

async def get_user_resources(user_id: int) -> dict:
    """الحصول على موارد المستخدم"""
    try:
        result = await execute_query(
            "SELECT * FROM user_resources WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        if result:
            return {
                'money': result['money'] if result['money'] else 0,
                'gold': result['gold'] if result['gold'] else 0,
                'stones': result['stones'] if result['stones'] else 0,
                'workers': result['workers'] if result['workers'] else 0
            }
        else:
            # إنشاء موارد جديدة إذا لم تكن موجودة
            await execute_query(
                """
                INSERT INTO user_resources (user_id, money, gold, stones, workers)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, 0, 0, 0, 0)
            )
            return {'money': 0, 'gold': 0, 'stones': 0, 'workers': 0}
    except Exception as e:
        logging.error(f"خطأ في الحصول على موارد المستخدم {user_id}: {e}")
        return {'money': 0, 'gold': 0, 'stones': 0, 'workers': 0}

async def add_resource_to_user(user_id: int, resource_type: str, amount: int) -> bool:
    """إضافة موارد للمستخدم"""
    try:
        # التأكد من وجود سجل الموارد
        await get_user_resources(user_id)
        
        # إضافة المورد
        await execute_query(
            f"UPDATE user_resources SET {resource_type} = {resource_type} + ? WHERE user_id = ?",
            (amount, user_id)
        )
        
        return True
    except Exception as e:
        logging.error(f"خطأ في إضافة المورد {resource_type} للمستخدم {user_id}: {e}")
        return False

async def get_last_treasure_hunt(user_id: int) -> str:
    """الحصول على آخر وقت بحث عن الكنز"""
    try:
        result = await execute_query(
            "SELECT last_treasure_hunt FROM user_castles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        if result and result['last_treasure_hunt']:
            return result['last_treasure_hunt']
        return None
    except Exception:
        return None

async def update_last_treasure_hunt(user_id: int) -> bool:
    """تحديث وقت آخر بحث عن الكنز"""
    try:
        await execute_query(
            "UPDATE user_castles SET last_treasure_hunt = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        return True
    except Exception:
        return False

async def perform_treasure_hunt(user_id: int) -> dict:
    """تنفيذ البحث عن الكنز"""
    try:
        # تحديد نوع الكنز باستخدام الاحتمالات
        total_chance = sum(treasure["chance"] for treasure in TREASURE_TYPES.values())
        random_num = random.randint(1, total_chance)
        
        current_chance = 0
        found_treasure = None
        
        for treasure_type, treasure_data in TREASURE_TYPES.items():
            current_chance += treasure_data["chance"]
            if random_num <= current_chance:
                found_treasure = treasure_type
                break
        
        if found_treasure == "nothing":
            return {"found": False, "type": None, "amount": 0}
        
        # حساب كمية الكنز
        treasure_info = TREASURE_TYPES[found_treasure]
        amount = random.randint(treasure_info["min"], treasure_info["max"])
        
        # تحديث إحصائيات البحث
        await update_treasure_hunt_stats(user_id, found_treasure, amount)
        
        return {"found": True, "type": found_treasure, "amount": amount}
        
    except Exception as e:
        logging.error(f"خطأ في البحث عن الكنز للمستخدم {user_id}: {e}")
        return {"found": False, "type": None, "amount": 0}

async def update_treasure_hunt_stats(user_id: int, treasure_type: str, amount: int) -> bool:
    """تحديث إحصائيات البحث عن الكنز"""
    try:
        # الحصول على الإحصائيات الحالية
        result = await execute_query(
            "SELECT treasure_hunt_stats FROM user_castles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        
        stats = {}
        if result and result['treasure_hunt_stats']:
            # تحليل الإحصائيات الموجودة
            stats_str = result['treasure_hunt_stats']
            if stats_str:
                for item in stats_str.split(','):
                    if ':' in item:
                        key, value = item.split(':')
                        stats[key] = int(value)
        
        # تحديث الإحصائيات
        stats[treasure_type] = stats.get(treasure_type, 0) + amount
        stats['total_hunts'] = stats.get('total_hunts', 0) + 1
        
        # تحويل الإحصائيات لنص
        stats_str = ','.join([f"{k}:{v}" for k, v in stats.items()])
        
        # حفظ الإحصائيات المحدثة
        await execute_query(
            "UPDATE user_castles SET treasure_hunt_stats = ? WHERE user_id = ?",
            (stats_str, user_id)
        )
        
        return True
    except Exception as e:
        logging.error(f"خطأ في تحديث إحصائيات البحث للمستخدم {user_id}: {e}")
        return False

async def delete_user_castle(user_id: int) -> bool:
    """حذف قلعة المستخدم"""
    try:
        # حذف القلعة
        await execute_query(
            "DELETE FROM user_castles WHERE user_id = ?",
            (user_id,)
        )
        
        # حذف الموارد
        await execute_query(
            "DELETE FROM user_resources WHERE user_id = ?",
            (user_id,)
        )
        
        logging.info(f"تم حذف قلعة المستخدم {user_id}")
        return True
    except Exception as e:
        logging.error(f"خطأ في حذف قلعة المستخدم {user_id}: {e}")
        return False

# ===== أوامر القلعة الأساسية =====

async def create_castle_command(message: Message, state: FSMContext = None):
    """أمر إنشاء قلعة جديدة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من المستوى المطلوب
        user_level = await get_user_level(message.from_user.id)
        if user_level < 5:
            await message.reply(
                f"❌ **المستوى غير كافي!**\n\n"
                f"📊 مستواك الحالي: {user_level}\n"
                f"📈 المستوى المطلوب: 5\n\n"
                f"💡 قم بالتفاعل أكثر في البوت لرفع مستواك!"
            )
            return
        
        # التحقق من الرصيد
        required_cost = 5000
        if user['balance'] < required_cost:
            await message.reply(
                f"❌ **الرصيد غير كافي!**\n\n"
                f"💰 رصيدك الحالي: {format_number(user['balance'])}$\n"
                f"💸 التكلفة المطلوبة: {format_number(required_cost)}$\n"
                f"💡 تحتاج: {format_number(required_cost - user['balance'])}$ إضافية"
            )
            return
        
        # التحقق من عدم وجود قلعة
        existing_castle = await get_user_castle(message.from_user.id)
        if existing_castle:
            await message.reply("❌ تملك قلعة بالفعل! لا يمكن إنشاء أكثر من قلعة واحدة.")
            return
        
        # إنشاء القلعة
        castle_name = f"قلعة {user['first_name'] or user['username'] or 'اللاعب'}"
        
        if await create_castle(message.from_user.id, castle_name):
            # خصم التكلفة
            await update_user_balance(message.from_user.id, -required_cost)
            await add_transaction(
                message.from_user.id, "castle_creation", required_cost,
                f"إنشاء القلعة: {castle_name}"
            )
            
            await message.reply(
                f"🎉 **تهانينا! تم إنشاء قلعتك بنجاح!**\n\n"
                f"🏰 **{castle_name}**\n"
                f"👑 المستوى: 1/10\n"
                f"💰 تم خصم: {format_number(required_cost)}$\n\n"
                f"💡 **الأوامر المتاحة:**\n"
                f"• قلعتي - لعرض القلعة\n"
                f"• بحث عن كنز - للبحث عن الموارد\n"
                f"• متجر القلعة - لشراء الموارد\n"
                f"• طور القلعة - لتطوير القلعة"
            )
        else:
            await message.reply("❌ حدث خطأ أثناء إنشاء القلعة")
            
    except Exception as e:
        logging.error(f"خطأ في إنشاء القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء القلعة")

async def show_castle_menu(message: Message):
    """عرض قائمة القلعة الرئيسية"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply(
                "❌ **لا تملك قلعة!**\n\n"
                "🏗️ لإنشاء قلعة جديدة، اكتب: **انشاء قلعة**\n"
                "📊 المستوى المطلوب: 5\n"
                "💰 التكلفة: 5,000$"
            )
            return
        
        # الحصول على موارد المستخدم
        resources = await get_user_resources(message.from_user.id)
        last_treasure_hunt = await get_last_treasure_hunt(message.from_user.id)
        
        # حساب الوقت المتبقي للبحث التالي
        next_hunt_time = ""
        if last_treasure_hunt:
            last_hunt = datetime.fromisoformat(last_treasure_hunt)
            next_hunt = last_hunt + timedelta(minutes=10)
            now = datetime.now()
            if now < next_hunt:
                time_diff = next_hunt - now
                minutes_left = int(time_diff.total_seconds() / 60)
                next_hunt_time = f"⏰ البحث التالي خلال: {minutes_left} دقيقة"
            else:
                next_hunt_time = "✅ يمكنك البحث عن الكنز الآن!"
        else:
            next_hunt_time = "✅ يمكنك البحث عن الكنز الآن!"
        
        castle_text = f"""
🏰 **قلعة {castle['name']}**

👑 المستوى: {castle['level']}/10
💰 رصيدك: {format_number(user['balance'])}$

📊 **الموارد:**
💰 المال: {format_number(resources.get('money', 0))}
🏆 الذهب: {format_number(resources.get('gold', 0))}
🪨 الحجارة: {format_number(resources.get('stones', 0))}
👷 العمال: {format_number(resources.get('workers', 0))}

🏗️ **مرحلة التطوير الحالية:**
{CASTLE_DEVELOPMENT_STAGES[castle['level']]['name']}

{next_hunt_time}

💡 **الأوامر المتاحة:**
• بحث عن كنز - للبحث عن الموارد
• طور القلعة - لتطوير القلعة للمستوى التالي
• احصائيات القلعة - لعرض تفاصيل القلعة
• متجر القلعة - لشراء الموارد
• حذف قلعتي - لحذف القلعة نهائياً
        """
        
        await message.reply(castle_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة القلعة")

async def show_castle_shop(message: Message):
    """عرض متجر القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة للوصول للمتجر! اكتب: **انشاء قلعة**")
            return
        
        # الحصول على موارد المستخدم
        resources = await get_user_resources(message.from_user.id)
        
        shop_text = f"""
🏪 **متجر القلعة**

💰 **رصيدك:** {format_number(user['balance'])}$
🏆 **ذهبك:** {format_number(resources.get('gold', 0))}

📦 **البضائع المتاحة:**

🏆 **الذهب**
• السعر: {CASTLE_SHOP_ITEMS['gold']['base_price']}$ للوحدة
• الحد الأقصى: {CASTLE_SHOP_ITEMS['gold']['max_purchase']} وحدة
• للشراء: **شراء ذهب [الكمية]**
• مثال: شراء ذهب 10

🪨 **الحجارة**
• السعر: {CASTLE_SHOP_ITEMS['stones']['base_price']}$ للوحدة  
• الحد الأقصى: {CASTLE_SHOP_ITEMS['stones']['max_purchase']} وحدة
• للشراء: **شراء حجارة [الكمية]**
• مثال: شراء حجارة 20

👷 **العمال**
• السعر: {CASTLE_SHOP_ITEMS['workers']['base_price']}$ للوحدة
• الحد الأقصى: {CASTLE_SHOP_ITEMS['workers']['max_purchase']} وحدة
• للشراء: **شراء عمال [الكمية]**
• مثال: شراء عمال 5

💰 **تحسين المال** (يدفع بالذهب)
• السعر: {CASTLE_SHOP_ITEMS['money_upgrade']['base_price']} ذهبة للوحدة
• الحد الأقصى: {CASTLE_SHOP_ITEMS['money_upgrade']['max_purchase']} وحدة
• للشراء: **شراء تحسين [الكمية]**
• مثال: شراء تحسين 3

💡 **متطلبات ترقية القلعة:**
• المستوى التالي ({castle['level'] + 1}): {castle['level'] + 1} ذهب، {(castle['level'] + 1) * 5} حجارة، {(castle['level'] + 1) * 6} عمال
        """
        
        await message.reply(shop_text)
        
    except Exception as e:
        logging.error(f"خطأ في متجر القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض متجر القلعة")

async def purchase_item_command(message: Message):
    """أمر شراء العناصر من المتجر"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة للشراء من المتجر!")
            return
        
        # تحليل الأمر
        text = message.text.strip()
        parts = text.split()
        
        if len(parts) < 3:
            await message.reply(
                "❌ **صيغة الأمر خاطئة!**\n\n"
                "📝 **الصيغة الصحيحة:**\n"
                "• شراء ذهب [الكمية]\n"
                "• شراء حجارة [الكمية]\n"
                "• شراء عمال [الكمية]\n"
                "• شراء تحسين [الكمية]\n\n"
                "💡 مثال: شراء ذهب 10"
            )
            return
        
        item_name = parts[1]
        try:
            quantity = int(parts[2])
        except ValueError:
            await message.reply("❌ الكمية يجب أن تكون رقماً صحيحاً!")
            return
        
        if quantity <= 0:
            await message.reply("❌ الكمية يجب أن تكون أكبر من صفر!")
            return
        
        # تحديد نوع العنصر
        item_key = None
        if item_name in ["ذهب", "الذهب"]:
            item_key = "gold"
        elif item_name in ["حجارة", "الحجارة"]:
            item_key = "stones"
        elif item_name in ["عمال", "العمال"]:
            item_key = "workers"
        elif item_name in ["تحسين", "المال"]:
            item_key = "money_upgrade"
        else:
            await message.reply(
                "❌ **عنصر غير متوفر!**\n\n"
                "📦 **العناصر المتاحة:**\n"
                "• ذهب\n"
                "• حجارة\n"
                "• عمال\n"
                "• تحسين (للمال)"
            )
            return
        
        # الحصول على معلومات العنصر
        item_info = CASTLE_SHOP_ITEMS[item_key]
        
        # التحقق من الحد الأقصى
        if quantity > item_info['max_purchase']:
            await message.reply(
                f"❌ **الكمية كبيرة جداً!**\n\n"
                f"📦 الحد الأقصى لـ{item_info['name']}: {item_info['max_purchase']} وحدة\n"
                f"🛒 الكمية المطلوبة: {quantity} وحدة"
            )
            return
        
        # حساب التكلفة الإجمالية
        total_cost = quantity * item_info['base_price']
        
        # التحقق من الرصيد
        if item_info['currency'] == "money":
            if user['balance'] < total_cost:
                await message.reply(
                    f"❌ **الرصيد غير كافي!**\n\n"
                    f"💰 رصيدك: {format_number(user['balance'])}$\n"
                    f"💸 التكلفة: {format_number(total_cost)}$\n"
                    f"💡 تحتاج: {format_number(total_cost - user['balance'])}$ إضافية"
                )
                return
        else:  # gold currency
            resources = await get_user_resources(message.from_user.id)
            user_gold = resources.get('gold', 0)
            if user_gold < total_cost:
                await message.reply(
                    f"❌ **الذهب غير كافي!**\n\n"
                    f"🏆 ذهبك: {format_number(user_gold)}\n"
                    f"💸 التكلفة: {format_number(total_cost)} ذهبة\n"
                    f"💡 تحتاج: {format_number(total_cost - user_gold)} ذهبة إضافية"
                )
                return
        
        # تنفيذ الشراء
        if item_info['currency'] == "money":
            await update_user_balance(message.from_user.id, -total_cost)
        else:
            await execute_query(
                "UPDATE user_resources SET gold = gold - ? WHERE user_id = ?",
                (total_cost, message.from_user.id)
            )
        
        # إضافة العنصر المشترى
        if item_key == "money_upgrade":
            # تحسين المال - زيادة رصيد المال في الموارد
            await add_resource_to_user(message.from_user.id, "money", quantity * 1000)
            item_received = f"{quantity * 1000} وحدة مال"
        else:
            await add_resource_to_user(message.from_user.id, item_key, quantity)
            item_received = f"{quantity} {item_info['name']}"
        
        # تسجيل المعاملة
        await add_transaction(
            message.from_user.id, "castle_shop_purchase", total_cost,
            f"شراء {item_received} من متجر القلعة"
        )
        
        currency_text = "$" if item_info['currency'] == "money" else " ذهبة"
        
        await message.reply(
            f"✅ **تم الشراء بنجاح!**\n\n"
            f"🛒 **المشتريات:**\n"
            f"{item_info['emoji']} {item_received}\n\n"
            f"💸 **التكلفة:** {format_number(total_cost)}{currency_text}\n"
            f"💰 **رصيدك الآن:** {format_number((await get_user(message.from_user.id))['balance'])}$\n\n"
            f"🎉 تم إضافة العناصر لمواردك!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في شراء العناصر: {e}")
        await message.reply("❌ حدث خطأ أثناء الشراء")

async def show_castle_stats(message: Message):
    """عرض إحصائيات القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة لعرض الإحصائيات!")
            return
        
        # الحصول على الموارد والإحصائيات
        resources = await get_user_resources(message.from_user.id)
        
        # تحليل إحصائيات البحث
        hunt_stats = {}
        if castle['treasure_hunt_stats']:
            for item in castle['treasure_hunt_stats'].split(','):
                if ':' in item:
                    key, value = item.split(':')
                    hunt_stats[key] = int(value)
        
        # حساب الطاقة الدفاعية والهجومية
        defense_power = castle['defense_points'] + (castle['walls_level'] * 50) + (castle['towers_level'] * 30)
        attack_power = castle['attack_points'] + (castle['warriors_count'] * 5)
        
        stats_text = f"""
📊 **إحصائيات قلعة {castle['name']}**

🏰 **معلومات القلعة:**
• 👑 المستوى: {castle['level']}/10
• 🆔 رمز القلعة: {castle['castle_id']}
• 📅 تاريخ الإنشاء: {castle['created_at'][:10]}

⚔️ **القوة العسكرية:**
• 🛡️ قوة الدفاع: {format_number(defense_power)}
• ⚔️ قوة الهجوم: {format_number(attack_power)}
• 👥 عدد المحاربين: {format_number(castle['warriors_count'])}

🏗️ **مستويات البناء:**
• 🧱 مستوى الأسوار: {castle['walls_level']}/10
• 🗼 مستوى الأبراج: {castle['towers_level']}/10
• 🕳️ مستوى الخنادق: {castle['moats_level']}/10

⚔️ **سجل المعارك:**
• 🏆 الانتصارات: {castle['wins']}
• 💀 الهزائم: {castle['losses']}
• 📊 إجمالي المعارك: {castle['total_battles']}
• 📈 نسبة الفوز: {(castle['wins'] / max(castle['total_battles'], 1) * 100):.1f}%

📦 **الموارد الحالية:**
• 💰 المال: {format_number(resources.get('money', 0))}
• 🏆 الذهب: {format_number(resources.get('gold', 0))}
• 🪨 الحجارة: {format_number(resources.get('stones', 0))}
• 👷 العمال: {format_number(resources.get('workers', 0))}

🔍 **إحصائيات البحث:**
• 🎯 إجمالي البحث: {hunt_stats.get('total_hunts', 0)}
• 💰 مال مجمع: {format_number(hunt_stats.get('money', 0))}
• 🏆 ذهب مجمع: {format_number(hunt_stats.get('gold', 0))}
• 🪨 حجارة مجمعة: {format_number(hunt_stats.get('stones', 0))}
• 👷 عمال مجمعون: {format_number(hunt_stats.get('workers', 0))}

💎 **القيمة الإجمالية للقلعة:**
{format_number(castle['level'] * 50000 + resources.get('gold', 0) * 100 + resources.get('stones', 0) * 50 + resources.get('workers', 0) * 200)}$
        """
        
        await message.reply(stats_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض إحصائيات القلعة")

async def show_player_profile(message: Message):
    """عرض حساب اللاعب الكامل"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # الحصول على معلومات إضافية
        castle = await get_user_castle(message.from_user.id)
        resources = await get_user_resources(message.from_user.id)
        
        # احصائيات المعاملات
        total_transactions = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE user_id = ?",
            (message.from_user.id,),
            fetch_one=True
        )
        
        # احصائيات النشاط
        activity_count = await execute_query(
            "SELECT COUNT(*) as count FROM activity_log WHERE user_id = ?",
            (message.from_user.id,),
            fetch_one=True
        )
        
        # تصنيف اللاعب
        rank_info = "لاعب عادي"
        try:
            from config.hierarchy import get_user_admin_level, AdminLevel
            admin_level = await get_user_admin_level(message.from_user.id)
            if admin_level == AdminLevel.SUPER_MASTER:
                rank_info = "السيد الأعظم ⭐"
            elif admin_level == AdminLevel.MASTER:
                rank_info = "سيد 👑"
            elif admin_level == AdminLevel.ADMIN:
                rank_info = "مشرف 🛡️"
        except:
            pass
        
        # معلومات الانجازات
        achievements = []
        if user['level'] >= 10:
            achievements.append("🌟 وصل للمستوى 10")
        if user['balance'] >= 100000:
            achievements.append("💰 جمع 100,000$")
        if castle and castle['level'] >= 5:
            achievements.append("🏰 طور القلعة للمستوى 5+")
        if user['total_earned'] >= 500000:
            achievements.append("📈 ربح أكثر من 500,000$")
        
        achievements_text = "\n".join(achievements) if achievements else "🔄 لا توجد إنجازات بعد"
        
        profile_text = f"""
👤 **حساب {user['first_name'] or user['username'] or 'اللاعب']}**

📋 **المعلومات الأساسية:**
• 🆔 الرقم التعريفي: {user['user_id']}
• 📛 اسم المستخدم: @{user['username'] or 'غير محدد'}
• 👑 التصنيف: {rank_info}
• 📊 المستوى: {user['level']}
• ⭐ نقاط الخبرة: {format_number(user['xp'])}

💰 **الوضع المالي:**
• 💵 الرصيد الحالي: {format_number(user['balance'])}$
• 🏦 رصيد البنك: {format_number(user['bank_balance'])}$
• 📈 إجمالي الأرباح: {format_number(user['total_earned'])}$
• 📉 إجمالي الإنفاق: {format_number(user['total_spent'])}$
• 🏛️ نوع البنك: {user['bank_type']}

📊 **إحصائيات النشاط:**
• 💳 عدد المعاملات: {total_transactions['count'] if total_transactions else 0}
• 📝 سجل الأنشطة: {activity_count['count'] if activity_count else 0}
• 📅 تاريخ التسجيل: {user['created_at'][:10]}
• 🕐 آخر نشاط: {user['updated_at'][:10]}

🏰 **معلومات القلعة:**"""
        
        if castle:
            profile_text += f"""
• 🏰 اسم القلعة: {castle['name']}
• 👑 مستوى القلعة: {castle['level']}/10
• 🏆 انتصارات: {castle['wins']}
• 💀 هزائم: {castle['losses']}
• 💎 موارد الذهب: {format_number(resources.get('gold', 0))}"""
        else:
            profile_text += """
• ❌ لا يملك قلعة بعد"""
        
        profile_text += f"""

🏆 **الإنجازات:**
{achievements_text}

🛡️ **الأمان:**
• 🔒 مستوى الحماية: {user['security_level']}/5
• ✅ محاولات السرقة الناجحة: {user['successful_thefts']}
• ❌ محاولات السرقة الفاشلة: {user['failed_thefts']}
• 🎯 تم سرقته: {user['times_stolen']} مرة

📈 **القيمة الإجمالية:**
{format_number(user['balance'] + user['bank_balance'] + (resources.get('gold', 0) * 100))}$
        """
        
        await message.reply(profile_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض حساب اللاعب: {e}")
        await message.reply("❌ حدث خطأ في عرض حساب اللاعب")

async def delete_castle_command(message: Message):
    """أمر حذف القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لحذفها!")
            return
        
        # تأكيد الحذف
        await message.reply(
            f"⚠️ **تحذير! حذف القلعة نهائي!**\n\n"
            f"🏰 ستفقد قلعة: **{castle['name']}**\n"
            f"👑 المستوى: {castle['level']}/10\n"
            f"💎 جميع الموارد والإحصائيات\n\n"
            f"❓ هل أنت متأكد من الحذف؟\n"
            f"✅ للتأكيد اكتب: **تأكيد حذف القلعة**\n"
            f"❌ لإلغاء العملية اكتب: **إلغاء**"
        )
        
    except Exception as e:
        logging.error(f"خطأ في أمر حذف القلعة: {e}")
        await message.reply("❌ حدث خطأ في أمر حذف القلعة")

async def confirm_delete_castle_command(message: Message):
    """تأكيد حذف القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لحذفها!")
            return
        
        # حذف القلعة
        if await delete_user_castle(message.from_user.id):
            await message.reply(
                f"✅ **تم حذف القلعة بنجاح!**\n\n"
                f"🗑️ تم حذف قلعة: **{castle['name']}**\n"
                f"💔 تم فقدان جميع الموارد والإحصائيات\n\n"
                f"🔄 يمكنك إنشاء قلعة جديدة باستخدام: **انشاء قلعة**"
            )
        else:
            await message.reply("❌ حدث خطأ أثناء حذف القلعة")
            
    except Exception as e:
        logging.error(f"خطأ في تأكيد حذف القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء حذف القلعة")

async def treasure_hunt_command(message: Message):
    """أمر البحث عن الكنز"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة للبحث عن الكنز! اكتب: **انشاء قلعة**")
            return
        
        # التحقق من وقت البحث الأخير
        last_hunt = await get_last_treasure_hunt(message.from_user.id)
        if last_hunt:
            last_hunt_time = datetime.fromisoformat(last_hunt)
            next_hunt_time = last_hunt_time + timedelta(minutes=10)
            now = datetime.now()
            
            if now < next_hunt_time:
                time_diff = next_hunt_time - now
                minutes_left = int(time_diff.total_seconds() / 60)
                await message.reply(
                    f"⏰ **انتظر قليلاً!**\n\n"
                    f"🔍 آخر بحث كان منذ: {10 - minutes_left} دقيقة\n"
                    f"⏳ الوقت المتبقي: {minutes_left} دقيقة\n\n"
                    f"💡 يمكنك البحث مرة واحدة كل 10 دقائق"
                )
                return
        
        # تنفيذ البحث عن الكنز
        treasure_result = await perform_treasure_hunt(message.from_user.id)
        
        if treasure_result["found"]:
            treasure_type = treasure_result["type"]
            amount = treasure_result["amount"]
            emoji = TREASURE_TYPES[treasure_type]["emoji"]
            
            # إضافة الكنز للمستخدم
            await add_resource_to_user(message.from_user.id, treasure_type, amount)
            
            await message.reply(
                f"🎉 **عثرت على كنز!**\n\n"
                f"{emoji} **{REQUIRED_RESOURCES.get(treasure_type, treasure_type)}**: {format_number(amount)}\n\n"
                f"💡 تم إضافة الكنز لمواردك بنجاح!\n"
                f"⏰ البحث التالي خلال: 10 دقائق"
            )
        else:
            await message.reply(
                f"❌ **لم تعثر على أي كنز هذه المرة**\n\n"
                f"🔍 حاول البحث مرة أخرى خلال 10 دقائق\n"
                f"💡 الحظ قد يحالفك في المرة القادمة!"
            )
        
        # تسجيل وقت البحث
        await update_last_treasure_hunt(message.from_user.id)
        
    except Exception as e:
        logging.error(f"خطأ في البحث عن الكنز: {e}")
        await message.reply("❌ حدث خطأ أثناء البحث عن الكنز")

async def upgrade_castle_command(message: Message):
    """أمر تطوير القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من وجود قلعة
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة أولاً! اكتب: **انشاء قلعة**")
            return
        
        current_level = castle['level']
        if current_level >= 10:
            await message.reply("🏆 **تهانينا!** قلعتك وصلت لأعلى مستوى - مملكة كاملة!")
            return
        
        next_level = current_level + 1
        stage_info = CASTLE_DEVELOPMENT_STAGES[next_level]
        required_cost = stage_info["cost"]
        
        # التحقق من الموارد المطلوبة
        resources = await get_user_resources(message.from_user.id)
        user_money = user['balance']
        user_gold = resources.get('gold', 0)
        user_stones = resources.get('stones', 0)
        user_workers = resources.get('workers', 0)
        
        # حساب الموارد المطلوبة بناءً على المستوى
        required_gold = next_level * 1  # 1 ذهب لكل مستوى
        required_stones = next_level * 5  # 5 حجارة لكل مستوى
        required_workers = next_level * 6  # 6 عمال لكل مستوى
        
        # التحقق من كفاية الموارد
        missing_resources = []
        if user_money < required_cost:
            missing_resources.append(f"💰 المال: {format_number(required_cost - user_money)}$ إضافية")
        if user_gold < required_gold:
            missing_resources.append(f"🏆 الذهب: {format_number(required_gold - user_gold)} إضافية")
        if user_stones < required_stones:
            missing_resources.append(f"🪨 الحجارة: {format_number(required_stones - user_stones)} إضافية")
        if user_workers < required_workers:
            missing_resources.append(f"👷 العمال: {format_number(required_workers - user_workers)} إضافية")
        
        if missing_resources:
            await message.reply(
                f"❌ **الموارد غير كافية للترقية!**\n\n"
                f"🎯 **الترقية إلى المستوى {next_level}:**\n"
                f"{stage_info['name']}\n\n"
                f"📋 **المطلوب:**\n"
                f"💰 المال: {format_number(required_cost)}$\n"
                f"🏆 الذهب: {format_number(required_gold)}\n"
                f"🪨 الحجارة: {format_number(required_stones)}\n"
                f"👷 العمال: {format_number(required_workers)}\n\n"
                f"❌ **ينقصك:**\n" + "\n".join(missing_resources) + "\n\n"
                f"💡 اشتر الموارد من: **متجر القلعة**"
            )
            return
        
        # تنفيذ الترقية
        # خصم الموارد
        await update_user_balance(message.from_user.id, -required_cost)
        await execute_query(
            "UPDATE user_resources SET gold = gold - ?, stones = stones - ?, workers = workers - ? WHERE user_id = ?",
            (required_gold, required_stones, required_workers, message.from_user.id)
        )
        
        # ترقية القلعة
        await execute_query(
            "UPDATE user_castles SET level = ?, defense_points = defense_points + 100, attack_points = attack_points + 50 WHERE user_id = ?",
            (next_level, message.from_user.id)
        )
        
        # تسجيل المعاملة
        await add_transaction(
            message.from_user.id, "castle_upgrade", required_cost,
            f"ترقية القلعة إلى المستوى {next_level}"
        )
        
        await message.reply(
            f"🎉 **تهانينا! تم ترقية القلعة بنجاح!**\n\n"
            f"🏰 **{stage_info['name']}**\n"
            f"👑 المستوى الجديد: {next_level}/10\n"
            f"📖 {stage_info['description']}\n\n"
            f"📊 **التحسينات:**\n"
            f"🛡️ قوة الدفاع: +100\n"
            f"⚔️ قوة الهجوم: +50\n\n"
            f"💸 **المواد المستخدمة:**\n"
            f"💰 المال: {format_number(required_cost)}$\n"
            f"🏆 الذهب: {format_number(required_gold)}\n"
            f"🪨 الحجارة: {format_number(required_stones)}\n"
            f"👷 العمال: {format_number(required_workers)}"
        )
        
    except Exception as e:
        logging.error(f"خطأ في ترقية القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء ترقية القلعة")
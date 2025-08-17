"""
وحدة القلعة المحدثة - نظام شامل للقلاع مع البحث عن الكنز
Updated Castle Module with Comprehensive Castle System and Treasure Hunt
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


# ===== دوال قاعدة البيانات المساعدة =====

async def get_user_level(user_id: int) -> int:
    """الحصول على مستوى المستخدم"""
    try:
        result = await execute_query(
            "SELECT level FROM users WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        return result['level'] if result else 1
    except Exception:
        return 1


async def is_master_user(user_id: int) -> bool:
    """التحقق من كون المستخدم سيد"""
    # هنا يمكن إضافة قائمة الأسياد أو التحقق من قاعدة البيانات
    MASTER_USERS = [8278493069]  # يمكن إضافة معرفات الأسياد هنا
    return user_id in MASTER_USERS


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


async def create_user_castle(user_id: int, castle_name: str) -> bool:
    """إنشاء قلعة جديدة للمستخدم"""
    try:
        await execute_query(
            """
            INSERT INTO user_castles (user_id, name, level, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, castle_name, 1, datetime.now().isoformat())
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في إنشاء قلعة للمستخدم {user_id}: {e}")
        return False


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
                'money': result.get('money', 0),
                'gold': result.get('gold', 0),
                'stones': result.get('stones', 0),
                'workers': result.get('workers', 0)
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
    """إضافة مورد للمستخدم"""
    try:
        # الحصول على الموارد الحالية
        current_resources = await get_user_resources(user_id)
        
        if resource_type == 'money':
            # إضافة المال للرصيد العادي
            user = await get_user(user_id)
            if user:
                new_balance = user['balance'] + amount
                return await update_user_balance(user_id, new_balance)
        else:
            # إضافة الموارد الأخرى
            new_amount = current_resources.get(resource_type, 0) + amount
            await execute_query(
                f"UPDATE user_resources SET {resource_type} = ? WHERE user_id = ?",
                (new_amount, user_id)
            )
        return True
    except Exception as e:
        logging.error(f"خطأ في إضافة مورد {resource_type} للمستخدم {user_id}: {e}")
        return False


async def subtract_resources_from_user(user_id: int, resources: dict) -> bool:
    """خصم موارد من المستخدم"""
    try:
        current_resources = await get_user_resources(user_id)
        
        for resource_type, amount in resources.items():
            if resource_type in current_resources:
                new_amount = max(0, current_resources[resource_type] - amount)
                await execute_query(
                    f"UPDATE user_resources SET {resource_type} = ? WHERE user_id = ?",
                    (new_amount, user_id)
                )
        return True
    except Exception as e:
        logging.error(f"خطأ في خصم الموارد من المستخدم {user_id}: {e}")
        return False


async def get_last_treasure_hunt(user_id: int) -> str:
    """الحصول على آخر وقت بحث عن الكنز"""
    try:
        result = await execute_query(
            "SELECT last_treasure_hunt FROM user_castles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        return result['last_treasure_hunt'] if result and result['last_treasure_hunt'] else None
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
    except Exception as e:
        logging.error(f"خطأ في تحديث وقت البحث للمستخدم {user_id}: {e}")
        return False


async def perform_treasure_hunt(user_id: int) -> dict:
    """تنفيذ البحث عن الكنز"""
    try:
        # حساب فرص العثور على كنز
        total_chance = sum(treasure['chance'] for treasure in TREASURE_TYPES.values())
        random_num = random.randint(1, total_chance)
        
        cumulative_chance = 0
        for treasure_type, treasure_info in TREASURE_TYPES.items():
            cumulative_chance += treasure_info['chance']
            if random_num <= cumulative_chance:
                if treasure_type == 'nothing':
                    return {"found": False, "type": None, "amount": 0}
                else:
                    amount = random.randint(treasure_info['min'], treasure_info['max'])
                    return {"found": True, "type": treasure_type, "amount": amount}
        
        return {"found": False, "type": None, "amount": 0}
    except Exception as e:
        logging.error(f"خطأ في البحث عن الكنز للمستخدم {user_id}: {e}")
        return {"found": False, "type": None, "amount": 0}


async def upgrade_castle_level(user_id: int, new_level: int) -> bool:
    """ترقية مستوى القلعة"""
    try:
        await execute_query(
            "UPDATE user_castles SET level = ? WHERE user_id = ?",
            (new_level, user_id)
        )
        return True
    except Exception as e:
        logging.error(f"خطأ في ترقية قلعة المستخدم {user_id}: {e}")
        return False


async def get_user_treasure_hunt_stats(user_id: int) -> dict:
    """الحصول على إحصائيات البحث عن الكنز"""
    try:
        result = await execute_query(
            "SELECT treasure_hunt_stats FROM user_castles WHERE user_id = ?",
            (user_id,),
            fetch_one=True
        )
        if result and result['treasure_hunt_stats']:
            import json
            return json.loads(result['treasure_hunt_stats'])
        else:
            return {'total_hunts': 0, 'successful_hunts': 0, 'total_treasure_value': 0}
    except Exception:
        return {'total_hunts': 0, 'successful_hunts': 0, 'total_treasure_value': 0}


# ===== دوال واجهة القلعة =====

async def create_castle_command(message: Message, state: FSMContext = None):
    """أمر إنشاء قلعة جديدة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من مستوى المستخدم
        user_level = await get_user_level(message.from_user.id)
        if user_level < 5:
            await message.reply(
                f"❌ **مستواك غير كافي!**\n\n"
                f"📊 مستواك الحالي: {user_level}\n"
                f"⚡ المستوى المطلوب: 5\n\n"
                f"💡 قم بالمشاركة في الأنشطة لرفع مستواك أولاً!"
            )
            return
        
        # التحقق من وجود قلعة بالفعل
        existing_castle = await get_user_castle(message.from_user.id)
        if existing_castle:
            await message.reply("❌ تملك قلعة بالفعل! لا يمكن إنشاء أكثر من قلعة واحدة.")
            return
        
        # التحقق من الرصيد
        castle_cost = 5000
        if user['balance'] < castle_cost:
            await message.reply(
                f"❌ **رصيد غير كافي!**\n\n"
                f"💰 تكلفة إنشاء القلعة: {format_number(castle_cost)}$\n"
                f"💵 رصيدك الحالي: {format_number(user['balance'])}$\n"
                f"💸 تحتاج إلى: {format_number(castle_cost - user['balance'])}$ إضافية"
            )
            return
        
        await message.reply(
            f"🏰 **إنشاء قلعة جديدة**\n\n"
            f"💰 التكلفة: {format_number(castle_cost)}$\n"
            f"💵 رصيدك: {format_number(user['balance'])}$\n\n"
            f"✏️ **اكتب اسم قلعتك:**\n"
            f"(سيتم خصم المبلغ عند تأكيد الاسم)"
        )
        
        # إعداد حالة انتظار اسم القلعة
        from utils.states import CastleStates
        await state.set_state(CastleStates.entering_castle_name)
        
    except Exception as e:
        logging.error(f"خطأ في أمر إنشاء القلعة: {e}")
        await message.reply("❌ حدث خطأ في إنشاء القلعة")


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
        """
        
        await message.reply(castle_text)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة القلعة")


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
        required_gold = next_level * 100
        required_stones = next_level * 50
        required_workers = next_level * 10
        
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
                f"❌ **موارد غير كافية للتطوير!**\n\n"
                f"🏗️ **المرحلة التالية:** {stage_info['name']}\n\n"
                f"📊 **المطلوب:**\n"
                f"💰 المال: {format_number(required_cost)}$\n"
                f"🏆 الذهب: {format_number(required_gold)}\n"
                f"🪨 الحجارة: {format_number(required_stones)}\n"
                f"👷 العمال: {format_number(required_workers)}\n\n"
                f"❌ **ينقصك:**\n" + "\n".join(missing_resources) + "\n\n"
                f"💡 ابحث عن الكنز لجمع المزيد من الموارد!"
            )
            return
        
        # تنفيذ التطوير
        await upgrade_castle_level(message.from_user.id, next_level)
        await update_user_balance(message.from_user.id, user_money - required_cost)
        await subtract_resources_from_user(message.from_user.id, {
            'gold': required_gold,
            'stones': required_stones,
            'workers': required_workers
        })
        
        await message.reply(
            f"🎉 **تم تطوير القلعة بنجاح!**\n\n"
            f"🏰 **{stage_info['name']}**\n"
            f"📖 {stage_info['description']}\n\n"
            f"👑 المستوى الجديد: {next_level}/10\n\n"
            f"💰 تم خصم: {format_number(required_cost)}$\n"
            f"🏆 تم خصم: {format_number(required_gold)} ذهب\n"
            f"🪨 تم خصم: {format_number(required_stones)} حجارة\n"
            f"👷 تم خصم: {format_number(required_workers)} عامل\n\n"
            f"{'🏆 تهانينا! قلعتك أصبحت مملكة كاملة!' if next_level == 10 else '💡 يمكنك الآن تطوير القلعة للمستوى التالي!'}"
        )
        
    except Exception as e:
        logging.error(f"خطأ في تطوير القلعة: {e}")
        await message.reply("❌ حدث خطأ في تطوير القلعة")


async def castle_stats_command(message: Message):
    """أمر عرض إحصائيات القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة! اكتب: **انشاء قلعة**")
            return
        
        resources = await get_user_resources(message.from_user.id)
        treasure_hunts = await get_user_treasure_hunt_stats(message.from_user.id)
        user_level = await get_user_level(message.from_user.id)
        
        current_stage = CASTLE_DEVELOPMENT_STAGES[castle['level']]
        next_stage = CASTLE_DEVELOPMENT_STAGES.get(castle['level'] + 1)
        
        # حساب حد المستوى للاعب
        max_level = '1000' if await is_master_user(message.from_user.id) else '100'
        
        # تحضير النص التالي
        next_stage_text = '🏆 **قلعتك في أعلى مستوى!**'
        if next_stage:
            next_stage_text = f'🎯 **المرحلة التالية:** {next_stage["name"]}\n💰 التكلفة: {format_number(next_stage["cost"])}$'
        
        stats_text = f"""
🏰 **إحصائيات قلعة {castle['name']}**

👑 **معلومات القلعة:**
📊 مستوى اللاعب: {user_level}/{max_level}
🏗️ مستوى القلعة: {castle['level']}/10
🏛️ المرحلة الحالية: {current_stage['name']}
📅 تاريخ الإنشاء: {castle['created_at'][:10]}

📊 **الموارد المتاحة:**
💰 المال: {format_number(user['balance'])}$
🏆 الذهب: {format_number(resources.get('gold', 0))}
🪨 الحجارة: {format_number(resources.get('stones', 0))}
👷 العمال: {format_number(resources.get('workers', 0))}

🔍 **إحصائيات البحث:**
📈 مرات البحث: {treasure_hunts.get('total_hunts', 0)}
🎯 كنوز عُثر عليها: {treasure_hunts.get('successful_hunts', 0)}
💎 إجمالي الكنوز: {format_number(treasure_hunts.get('total_treasure_value', 0))}

{next_stage_text}
        """
        
        await message.reply(stats_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض الإحصائيات")


# دالة لمعالجة أوامر إنشاء القلعة مع الاسم
async def handle_castle_name_input(message: Message, state: FSMContext):
    """معالجة إدخال اسم القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # التحقق من أن المستخدم لا يملك قلعة
        existing_castle = await get_user_castle(message.from_user.id)
        if existing_castle:
            await message.reply("❌ تملك قلعة بالفعل!")
            return
        
        castle_name = message.text.strip()
        if len(castle_name) < 3 or len(castle_name) > 30:
            await message.reply("❌ اسم القلعة يجب أن يكون بين 3 و 30 حرف")
            return
        
        # خصم التكلفة
        castle_cost = 5000
        if user['balance'] < castle_cost:
            await message.reply("❌ رصيد غير كافي لإنشاء القلعة")
            return
        
        # إنشاء القلعة
        success = await create_user_castle(message.from_user.id, castle_name)
        if success:
            await update_user_balance(message.from_user.id, user['balance'] - castle_cost)
            await message.reply(
                f"🎉 **تم إنشاء القلعة بنجاح!**\n\n"
                f"🏰 اسم القلعة: **{castle_name}**\n"
                f"💰 تم خصم: {format_number(castle_cost)}$\n"
                f"👑 مستوى القلعة: 1/10\n\n"
                f"💡 الآن يمكنك:\n"
                f"• **بحث عن كنز** - للحصول على موارد\n"
                f"• **طور القلعة** - لتطوير القلعة\n"
                f"• **احصائيات القلعة** - لعرض التفاصيل"
            )
            await state.clear()  # مسح الحالة بعد النجاح
        else:
            await message.reply("❌ حدث خطأ في إنشاء القلعة")
            await state.clear()  # مسح الحالة حتى في حالة الخطأ
    
    except Exception as e:
        logging.error(f"خطأ في معالجة اسم القلعة: {e}")
        await message.reply("❌ حدث خطأ في إنشاء القلعة")

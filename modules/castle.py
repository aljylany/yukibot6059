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
        admin_level = get_user_admin_level(user_id)
        
        if admin_level == AdminLevel.MASTER:
            # الأسياد لهم مستوى 1000 تلقائياً
            await set_user_level(user_id, 1000)
            return 1000
        
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


def generate_castle_id() -> str:
    """توليد معرف فريد للقلعة"""
    import random
    import string
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))


async def create_user_castle(user_id: int, castle_name: str) -> bool:
    """إنشاء قلعة جديدة للمستخدم"""
    try:
        castle_id = generate_castle_id()
        await execute_query(
            """
            INSERT INTO user_castles (user_id, name, castle_id, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, castle_name, castle_id, datetime.now().isoformat())
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # التحقق من مستوى المستخدم
        user_level = await get_user_level(message.from_user.id)
        
        # الأسياد لديهم مستوى 1000 تلقائياً - لا حاجة للتحقق من المستوى
        from config.hierarchy import get_user_admin_level, AdminLevel
        admin_level = get_user_admin_level(message.from_user.id)
        
        if admin_level != AdminLevel.MASTER and user_level < 5:
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
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
🆔 معرف القلعة: `{castle.get('castle_id', 'غير محدد')}`
📊 مستوى اللاعب: {user_level}/{max_level}
🏗️ مستوى القلعة: {castle['level']}/10
🏛️ المرحلة الحالية: {current_stage['name']}
📅 تاريخ الإنشاء: {castle['created_at'][:10]}

⚔️ **سجل المعارك:**
🏆 انتصارات: {castle.get('wins', 0)}
💔 هزائم: {castle.get('losses', 0)}
📊 إجمالي المعارك: {castle.get('total_battles', 0)}

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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
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
            # الحصول على معرف القلعة الجديدة
            new_castle = await get_user_castle(message.from_user.id)
            castle_id = new_castle.get('castle_id', 'غير محدد') if new_castle else 'غير محدد'
            
            await message.reply(
                f"🎉 **تم إنشاء القلعة بنجاح!**\n\n"
                f"🏰 اسم القلعة: **{castle_name}**\n"
                f"🆔 معرف القلعة: `{castle_id}`\n"
                f"💰 تم خصم: {format_number(castle_cost)}$\n"
                f"👑 مستوى القلعة: 1/10\n\n"
                f"💡 الآن يمكنك:\n"
                f"• **بحث عن كنز** - للحصول على موارد\n"
                f"• **طور القلعة** - لتطوير القلعة\n"
                f"• **احصائيات القلعة** - لعرض التفاصيل\n"
                f"• **هجوم [معرف القلعة]** - لمهاجمة قلعة أخرى\n"
                f"• **سجل المعارك** - لعرض تاريخ المعارك"
            )
            await state.clear()  # مسح الحالة بعد النجاح
        else:
            await message.reply("❌ حدث خطأ في إنشاء القلعة")
            await state.clear()  # مسح الحالة حتى في حالة الخطأ
    
    except Exception as e:
        logging.error(f"خطأ في معالجة اسم القلعة: {e}")
        await message.reply("❌ حدث خطأ في إنشاء القلعة")


# ===== نظام الحروب والهجمات =====

async def get_castle_by_id(castle_id: str):
    """الحصول على قلعة بالمعرف"""
    try:
        return await execute_query(
            "SELECT * FROM user_castles WHERE castle_id = ?",
            (castle_id,),
            fetch_one=True
        )
    except Exception as e:
        logging.error(f"خطأ في البحث عن القلعة {castle_id}: {e}")
        return None


async def calculate_battle_power(castle_data: dict) -> int:
    """حساب قوة القتال للقلعة"""
    base_power = castle_data.get('attack_points', 50)
    walls_bonus = castle_data.get('walls_level', 1) * 20
    towers_bonus = castle_data.get('towers_level', 1) * 15
    warriors_bonus = castle_data.get('warriors_count', 10) * 5
    level_bonus = castle_data.get('level', 1) * 10
    
    return base_power + walls_bonus + towers_bonus + warriors_bonus + level_bonus


async def calculate_defense_power(castle_data: dict) -> int:
    """حساب قوة الدفاع للقلعة"""
    base_defense = castle_data.get('defense_points', 100)
    walls_bonus = castle_data.get('walls_level', 1) * 25
    towers_bonus = castle_data.get('towers_level', 1) * 20
    moats_bonus = castle_data.get('moats_level', 1) * 15
    level_bonus = castle_data.get('level', 1) * 15
    
    return base_defense + walls_bonus + towers_bonus + moats_bonus + level_bonus


async def attack_castle_command(message: Message):
    """أمر مهاجمة قلعة"""
    try:
        # استخراج معرف القلعة المستهدفة
        text_parts = message.text.split()
        if len(text_parts) < 2:
            await message.reply(
                "❌ **استخدم الصيغة الصحيحة:**\n\n"
                "📝 `هجوم [معرف القلعة]`\n"
                "🔍 مثال: `هجوم ABC123DE`\n\n"
                "💡 للحصول على معرف قلعتك اكتب: **احصائيات القلعة**"
            )
            return
        
        target_castle_id = text_parts[1].upper()
        
        # التحقق من وجود قلعة للمهاجم
        attacker_castle = await get_user_castle(message.from_user.id)
        if not attacker_castle:
            await message.reply("❌ يجب أن تملك قلعة لتتمكن من الهجوم!")
            return
        
        # التحقق من وجود القلعة المستهدفة
        target_castle = await get_castle_by_id(target_castle_id)
        if not target_castle:
            await message.reply(f"❌ لم يتم العثور على قلعة بالمعرف: `{target_castle_id}`")
            return
        
        # منع مهاجمة القلعة الخاصة
        if target_castle['user_id'] == message.from_user.id:
            await message.reply("❌ لا يمكنك مهاجمة قلعتك الخاصة!")
            return
        
        # حساب قوة الطرفين
        attacker_power = await calculate_battle_power(attacker_castle)
        defender_power = await calculate_defense_power(target_castle)
        
        # محاكاة المعركة (مع عنصر العشوائية)
        import random
        attacker_final = attacker_power + random.randint(-20, 30)
        defender_final = defender_power + random.randint(-15, 25)
        
        # تحديد النتيجة
        attacker_wins = attacker_final > defender_final
        
        # حساب الذهب المسروق
        gold_stolen = 0
        if attacker_wins:
            max_gold = target_castle.get('gold_storage', 0)
            gold_stolen = min(max_gold * 0.3, attacker_final * 2)  # حد أقصى 30% من ذهب العدو
        
        # تحديث الإحصائيات
        if attacker_wins:
            await execute_query(
                "UPDATE user_castles SET wins = wins + 1, total_battles = total_battles + 1, gold_storage = gold_storage + ? WHERE user_id = ?",
                (gold_stolen, message.from_user.id)
            )
            await execute_query(
                "UPDATE user_castles SET losses = losses + 1, total_battles = total_battles + 1, gold_storage = gold_storage - ? WHERE user_id = ?",
                (gold_stolen, target_castle['user_id'])
            )
        else:
            await execute_query(
                "UPDATE user_castles SET losses = losses + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await execute_query(
                "UPDATE user_castles SET wins = wins + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (target_castle['user_id'],)
            )
        
        # تسجيل المعركة
        await execute_query(
            """
            INSERT INTO castle_battles (
                attacker_castle_id, defender_castle_id, attacker_user_id, defender_user_id,
                attacker_power, defender_power, winner, gold_stolen, battle_log, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attacker_castle['castle_id'], target_castle_id, message.from_user.id, target_castle['user_id'],
                attacker_final, defender_final, 'attacker' if attacker_wins else 'defender',
                gold_stolen, f"المهاجم: {attacker_final} vs المدافع: {defender_final}",
                datetime.now().isoformat()
            )
        )
        
        # عرض نتيجة المعركة
        result_icon = "🎉" if attacker_wins else "💔"
        result_text = "**انتصار!**" if attacker_wins else "**هزيمة!**"
        
        battle_report = f"""
{result_icon} **تقرير المعركة** {result_icon}

⚔️ **النتيجة:** {result_text}

🏰 **قلعتك:** {attacker_castle['name']}
🎯 **القلعة المستهدفة:** {target_castle['name']}

📊 **قوة القتال:**
   • قوتك: {attacker_final}
   • قوة العدو: {defender_final}

💰 **الغنائم:** {format_number(gold_stolen)} ذهب

📈 **إحصائيات محدثة:**
   • الانتصارات: {attacker_castle.get('wins', 0) + (1 if attacker_wins else 0)}
   • الهزائم: {attacker_castle.get('losses', 0) + (0 if attacker_wins else 1)}
        """
        
        await message.reply(battle_report)
        
    except Exception as e:
        logging.error(f"خطأ في هجوم القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء الهجوم")


async def castle_battles_log_command(message: Message):
    """عرض سجل معارك القلعة"""
    try:
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة!")
            return
        
        # الحصول على آخر 10 معارك
        battles = await execute_query(
            """
            SELECT * FROM castle_battles 
            WHERE attacker_user_id = ? OR defender_user_id = ?
            ORDER BY created_at DESC LIMIT 10
            """,
            (message.from_user.id, message.from_user.id),
            fetch_all=True
        )
        
        if not battles:
            await message.reply("📜 لا توجد معارك في سجلك!")
            return
        
        battles_text = "⚔️ **سجل المعارك** ⚔️\n\n"
        
        for battle in battles:
            is_attacker = battle['attacker_user_id'] == message.from_user.id
            role = "مهاجم" if is_attacker else "مدافع"
            won = (battle['winner'] == 'attacker' and is_attacker) or (battle['winner'] == 'defender' and not is_attacker)
            result = "🏆 انتصار" if won else "💔 هزيمة"
            
            battles_text += f"• {role} - {result}\n"
            battles_text += f"  💰 ذهب: {format_number(battle['gold_stolen'])}\n"
            battles_text += f"  📅 {battle['created_at'][:10]}\n\n"
        
        await message.reply(battles_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض سجل المعارك: {e}")
        await message.reply("❌ حدث خطأ في عرض سجل المعارك")


# ===== متجر القلعة والأوامر الجديدة =====

# أسعار متجر القلعة
CASTLE_SHOP_ITEMS = {
    "gold": {
        "name": "ذهب",
        "emoji": "🏆",
        "base_price": 100,
        "currency": "money",
        "description": "ذهب نقي لتطوير القلعة",
        "max_purchase": 1000
    },
    "stones": {
        "name": "حجارة", 
        "emoji": "🪨",
        "base_price": 50,
        "currency": "money",
        "description": "حجارة قوية للبناء",
        "max_purchase": 2000
    },
    "workers": {
        "name": "عمال",
        "emoji": "👷",
        "base_price": 200,
        "currency": "money", 
        "description": "عمال مهرة للعمل في القلعة",
        "max_purchase": 500
    }
}

async def show_castle_shop(message: Message):
    """عرض متجر القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة للوصول للمتجر! اكتب: **انشاء قلعة**")
            return
        
        resources = await get_user_resources(message.from_user.id)
        
        shop_text = f"""🏪 **متجر القلعة**

💰 **رصيدك:** {format_number(user['balance'])}$
🏆 **ذهبك:** {format_number(resources.get('gold', 0))}

📦 **البضائع المتاحة:**

🏆 **الذهب**
• السعر: {CASTLE_SHOP_ITEMS['gold']['base_price']}$ للوحدة
• للشراء: **شراء ذهب [الكمية]**
• مثال: شراء ذهب 10

🪨 **الحجارة**
• السعر: {CASTLE_SHOP_ITEMS['stones']['base_price']}$ للوحدة
• للشراء: **شراء حجارة [الكمية]**
• مثال: شراء حجارة 20

👷 **العمال**
• السعر: {CASTLE_SHOP_ITEMS['workers']['base_price']}$ للوحدة
• للشراء: **شراء عمال [الكمية]**
• مثال: شراء عمال 5

💡 **متطلبات ترقية القلعة:**
المستوى التالي ({castle['level'] + 1}): {castle['level'] + 1} ذهب، {(castle['level'] + 1) * 5} حجارة، {(castle['level'] + 1) * 6} عمال
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ تحتاج إلى قلعة للشراء من المتجر!")
            return
        
        text = message.text.strip()
        parts = text.split()
        
        if len(parts) < 3:
            await message.reply(
                "❌ **صيغة الأمر خاطئة!**\\n\\n"
                "📝 **الصيغة الصحيحة:**\\n"
                "• شراء ذهب [الكمية]\\n"
                "• شراء حجارة [الكمية]\\n"
                "• شراء عمال [الكمية]\\n\\n"
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
        else:
            await message.reply(
                "❌ **عنصر غير متوفر!**\\n\\n"
                "📦 **العناصر المتاحة:**\\n"
                "• ذهب\\n"
                "• حجارة\\n"
                "• عمال"
            )
            return
        
        item_info = CASTLE_SHOP_ITEMS[item_key]
        
        # التحقق من الحد الأقصى
        if quantity > item_info['max_purchase']:
            await message.reply(
                f"❌ **الكمية كبيرة جداً!**\\n\\n"
                f"📦 الحد الأقصى لـ{item_info['name']}: {item_info['max_purchase']} وحدة\\n"
                f"🛒 الكمية المطلوبة: {quantity} وحدة"
            )
            return
        
        total_cost = quantity * item_info['base_price']
        
        if user['balance'] < total_cost:
            await message.reply(
                f"❌ **الرصيد غير كافي!**\\n\\n"
                f"💰 رصيدك: {format_number(user['balance'])}$\\n"
                f"💸 التكلفة: {format_number(total_cost)}$\\n"
                f"💡 تحتاج: {format_number(total_cost - user['balance'])}$ إضافية"
            )
            return
        
        # تنفيذ الشراء
        await update_user_balance(message.from_user.id, -total_cost)
        await add_resource_to_user(message.from_user.id, item_key, quantity)
        
        # تسجيل المعاملة
        await add_transaction(
            message.from_user.id, "castle_shop_purchase", total_cost,
            f"شراء {quantity} {item_info['name']} من متجر القلعة"
        )
        
        await message.reply(
            f"✅ **تم الشراء بنجاح!**\\n\\n"
            f"🛒 **المشتريات:**\\n"
            f"{item_info['emoji']} {quantity} {item_info['name']}\\n\\n"
            f"💸 **التكلفة:** {format_number(total_cost)}$\\n"
            f"💰 **رصيدك الآن:** {format_number((await get_user(message.from_user.id))['balance'])}$\\n\\n"
            f"🎉 تم إضافة العناصر لمواردك!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في شراء العناصر: {e}")
        await message.reply("❌ حدث خطأ أثناء الشراء")

async def show_player_profile(message: Message):
    """عرض حساب اللاعب الكامل"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        resources = await get_user_resources(message.from_user.id)
        
        # احصائيات المعاملات
        total_transactions = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE user_id = ?",
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
        
        achievements_text = "\\n".join(achievements) if achievements else "🔄 لا توجد إنجازات بعد"
        
        user_name = user['first_name'] or user['username'] or 'اللاعب'
        user_username = user['username'] or 'غير محدد'
        
        profile_text = f"""👤 **حساب {user_name}**

📋 **المعلومات الأساسية:**
• 🆔 الرقم التعريفي: {user['user_id']}
• 📛 اسم المستخدم: @{user_username}
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لحذفها!")
            return
        
        await message.reply(
            f"⚠️ **تحذير! حذف القلعة نهائي!**\\n\\n"
            f"🏰 ستفقد قلعة: **{castle['name']}**\\n"
            f"👑 المستوى: {castle['level']}/10\\n"
            f"💎 جميع الموارد والإحصائيات\\n\\n"
            f"❓ هل أنت متأكد من الحذف؟\\n"
            f"✅ للتأكيد اكتب: **تأكيد** أو **نعم**\\n"
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
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لحذفها!")
            return
        
        # حذف القلعة
        await execute_query(
            "DELETE FROM user_castles WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        # حذف الموارد
        await execute_query(
            "DELETE FROM user_resources WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        await message.reply(
            f"✅ **تم حذف القلعة بنجاح!**\\n\\n"
            f"🗑️ تم حذف قلعة: **{castle['name']}**\\n"
            f"💔 تم فقدان جميع الموارد والإحصائيات\\n\\n"
            f"🔄 يمكنك إنشاء قلعة جديدة باستخدام: **انشاء قلعة**"
        )
            
    except Exception as e:
        logging.error(f"خطأ في تأكيد حذف القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء حذف القلعة")

# دالة مطابقة للاستدعاء من messages.py
async def show_castle_stats(message: Message):
    """عرض إحصائيات القلعة - دالة مطابقة"""
    await castle_stats_command(message)

# ===== أوامر إخفاء وإظهار القلعة =====

async def hide_castle_command(message: Message):
    """إخفاء القلعة من قائمة القلاع المتاحة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لإخفائها!")
            return
        
        # تحديث حالة القلعة لتصبح مخفية
        await execute_query(
            "UPDATE user_castles SET is_hidden = 1 WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        await message.reply(
            f"🔒 **تم إخفاء القلعة بنجاح!**\n\n"
            f"🏰 قلعة **{castle['name']}** أصبحت مخفية\n"
            f"🆔 معرف القلعة: `{castle.get('castle_id', 'غير محدد')}`\n"
            f"👁️ لن تظهر في قائمة القلاع المتاحة للهجوم\n\n"
            f"💡 لإظهارها مرة أخرى اكتب: **اظهار قلعتي**"
        )
        
    except Exception as e:
        logging.error(f"خطأ في إخفاء القلعة: {e}")
        await message.reply("❌ حدث خطأ في إخفاء القلعة")

async def show_castle_command(message: Message):
    """إظهار القلعة في قائمة القلاع المتاحة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لإظهارها!")
            return
        
        # تحديث حالة القلعة لتصبح ظاهرة
        await execute_query(
            "UPDATE user_castles SET is_hidden = 0 WHERE user_id = ?",
            (message.from_user.id,)
        )
        
        await message.reply(
            f"👁️ **تم إظهار القلعة بنجاح!**\n\n"
            f"🏰 قلعة **{castle['name']}** أصبحت ظاهرة\n"
            f"🆔 معرف القلعة: `{castle.get('castle_id', 'غير محدد')}`\n"
            f"⚔️ ستظهر في قائمة القلاع المتاحة للهجوم\n\n"
            f"💡 لإخفائها اكتب: **اخفاء قلعتي**"
        )
        
    except Exception as e:
        logging.error(f"خطأ في إظهار القلعة: {e}")
        await message.reply("❌ حدث خطأ في إظهار القلعة")

async def list_available_castles(message: Message):
    """عرض قائمة القلاع المتاحة للهجوم"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # التحقق من أن المستخدم يملك قلعة
        user_castle = await get_user_castle(message.from_user.id)
        if not user_castle:
            await message.reply("❌ تحتاج إلى قلعة لرؤية القلاع الأخرى! اكتب: **انشاء قلعة**")
            return
        
        # الحصول على القلاع الظاهرة (غير المخفية) باستثناء قلعة المستخدم
        castles = await execute_query(
            """
            SELECT uc.*, u.first_name, u.username 
            FROM user_castles uc 
            JOIN users u ON uc.user_id = u.user_id 
            WHERE uc.user_id != ? AND (uc.is_hidden IS NULL OR uc.is_hidden = 0)
            ORDER BY uc.level DESC, uc.wins DESC
            LIMIT 20
            """,
            (message.from_user.id,),
            fetch_all=True
        )
        
        if not castles:
            await message.reply(
                "🏰 **لا توجد قلاع متاحة للهجوم!**\n\n"
                "📋 جميع القلاع إما مخفية أو لا توجد قلاع أخرى\n"
                "🔄 جرب مرة أخرى لاحقاً"
            )
            return
        
        castles_text = "🏰 **القلاع المتاحة للهجوم:**\n\n"
        
        for castle in castles:
            owner_name = castle['first_name'] or castle['username'] or 'مجهول'
            castle_status = "🔒 محمية" if castle['level'] >= 5 else "🆓 متاحة"
            
            castles_text += f"⚔️ **{castle['name']}**\n"
            castles_text += f"👤 المالك: {owner_name}\n"
            castles_text += f"🆔 المعرف: `{castle['castle_id']}`\n"
            castles_text += f"👑 المستوى: {castle['level']}/10\n"
            castles_text += f"🏆 انتصارات: {castle.get('wins', 0)}\n"
            castles_text += f"💔 هزائم: {castle.get('losses', 0)}\n"
            castles_text += f"📊 الحالة: {castle_status}\n\n"
        
        castles_text += f"💡 **للهجوم:** اكتب **هجوم [معرف القلعة]**\n"
        castles_text += f"📋 مثال: هجوم ABC12345"
        
        await message.reply(castles_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة القلاع: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة القلاع")

# ===== تحديث نظام الهجوم =====

async def attack_castle_command(message: Message):
    """أمر مهاجمة القلعة مع تحسينات"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # التحقق من وجود قلعة للمستخدم
        attacker_castle = await get_user_castle(message.from_user.id)
        if not attacker_castle:
            await message.reply("❌ تحتاج إلى قلعة لمهاجمة الآخرين! اكتب: **انشاء قلعة**")
            return
        
        # استخراج معرف القلعة المستهدفة
        text = message.text.strip()
        parts = text.split()
        
        if len(parts) < 2:
            await message.reply(
                "❌ **صيغة الأمر خاطئة!**\n\n"
                "📝 **الصيغة الصحيحة:** هجوم [معرف القلعة]\n"
                "💡 مثال: هجوم ABC12345\n\n"
                "🔍 لرؤية القلاع المتاحة اكتب: **قائمة القلاع**"
            )
            return
        
        target_castle_id = parts[1].upper()
        
        # البحث عن القلعة المستهدفة
        target_castle = await execute_query(
            "SELECT * FROM user_castles WHERE castle_id = ? AND user_id != ?",
            (target_castle_id, message.from_user.id),
            fetch_one=True
        )
        
        if not target_castle:
            await message.reply(
                f"❌ **قلعة غير موجودة!**\n\n"
                f"🔍 معرف القلعة `{target_castle_id}` غير صحيح أو غير متاح\n"
                f"📋 لرؤية القلاع المتاحة اكتب: **قائمة القلاع**"
            )
            return
        
        # التحقق من أن القلعة غير مخفية
        if target_castle.get('is_hidden', 0) == 1:
            await message.reply(
                f"🔒 **القلعة محمية!**\n\n"
                f"🏰 هذه القلعة مخفية ولا يمكن مهاجمتها\n"
                f"🔍 جرب قلعة أخرى من **قائمة القلاع**"
            )
            return
        
        # التحقق من وقت آخر هجوم (منع الهجوم المتكرر)
        last_attack = await execute_query(
            """
            SELECT created_at FROM castle_battles 
            WHERE attacker_user_id = ? 
            ORDER BY created_at DESC LIMIT 1
            """,
            (message.from_user.id,),
            fetch_one=True
        )
        
        if last_attack:
            from datetime import datetime, timedelta
            last_attack_time = datetime.fromisoformat(last_attack['created_at'])
            now = datetime.now()
            cooldown_minutes = 30  # فترة انتظار 30 دقيقة
            
            if now - last_attack_time < timedelta(minutes=cooldown_minutes):
                remaining_time = cooldown_minutes - int((now - last_attack_time).total_seconds() / 60)
                await message.reply(
                    f"⏰ **فترة انتظار!**\n\n"
                    f"🛡️ يجب انتظار {remaining_time} دقيقة قبل الهجوم مرة أخرى\n"
                    f"💡 استخدم هذا الوقت في **بحث عن كنز** أو **طور القلعة**"
                )
                return
        
        # حساب قوة الهجوم والدفاع
        attacker_resources = await get_user_resources(message.from_user.id)
        defender_resources = await get_user_resources(target_castle['user_id'])
        
        # قوة المهاجم (مستوى القلعة + الموارد + العشوائية)
        attacker_power = (
            attacker_castle['level'] * 100 +
            attacker_resources.get('gold', 0) * 10 +
            attacker_resources.get('workers', 0) * 5 +
            random.randint(50, 150)
        )
        
        # قوة المدافع (مستوى القلعة + الموارد + مكافأة الدفاع + العشوائية)
        defender_power = (
            target_castle['level'] * 120 +  # مكافأة دفاع إضافية
            defender_resources.get('gold', 0) * 10 +
            defender_resources.get('workers', 0) * 5 +
            random.randint(75, 175)
        )
        
        # تحديد النتيجة
        attacker_wins = attacker_power > defender_power
        
        # حساب الغنائم
        if attacker_wins:
            # المهاجم ينتصر ويسرق جزء من الذهب
            defender_gold = defender_resources.get('gold', 0)
            max_steal = min(defender_gold // 2, 100)  # حد أقصى 100 ذهب أو نصف الذهب
            gold_stolen = random.randint(max_steal // 2, max_steal) if max_steal > 0 else 0
            
            if gold_stolen > 0:
                # خصم الذهب من المدافع
                await execute_query(
                    "UPDATE user_resources SET gold = CASE WHEN gold >= ? THEN gold - ? ELSE 0 END WHERE user_id = ?",
                    (gold_stolen, gold_stolen, target_castle['user_id'])
                )
                
                # إضافة الذهب للمهاجم
                await add_resource_to_user(message.from_user.id, 'gold', gold_stolen)
            
            # تحديث إحصائيات الانتصارات والهزائم
            await execute_query(
                "UPDATE user_castles SET wins = wins + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await execute_query(
                "UPDATE user_castles SET losses = losses + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (target_castle['user_id'],)
            )
            
            result_emoji = "🏆"
            result_text = "انتصار ساحق!"
        else:
            # المدافع ينتصر
            gold_stolen = 0
            await execute_query(
                "UPDATE user_castles SET losses = losses + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (message.from_user.id,)
            )
            await execute_query(
                "UPDATE user_castles SET wins = wins + 1, total_battles = total_battles + 1 WHERE user_id = ?",
                (target_castle['user_id'],)
            )
            
            result_emoji = "💔"
            result_text = "هزيمة مؤلمة!"
        
        # تسجيل المعركة
        from datetime import datetime
        await execute_query(
            """
            INSERT INTO castle_battles 
            (attacker_user_id, defender_user_id, attacker_castle_id, defender_castle_id, 
             winner, attacker_power, defender_power, gold_stolen, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message.from_user.id, target_castle['user_id'],
                attacker_castle['castle_id'], target_castle['castle_id'],
                'attacker' if attacker_wins else 'defender',
                attacker_power, defender_power, gold_stolen,
                datetime.now().isoformat()
            )
        )
        
        # الحصول على اسم المدافع
        defender = await get_user(target_castle['user_id'])
        defender_name = defender['first_name'] or defender['username'] or 'مجهول'
        
        # تقرير المعركة
        battle_report = f"""⚔️ **تقرير المعركة** ⚔️

{result_emoji} **النتيجة: {result_text}**

🏰 **المهاجم:** {attacker_castle['name']} (أنت)
🛡️ **المدافع:** {target_castle['name']} ({defender_name})

📊 **قوة القتال:**
• قوتك: {format_number(attacker_power)}
• قوة العدو: {format_number(defender_power)}

💰 **الغنائم:** {format_number(gold_stolen)} ذهب

📈 **إحصائيات محدثة:**
• انتصاراتك: {attacker_castle.get('wins', 0) + (1 if attacker_wins else 0)}
• هزائمك: {attacker_castle.get('losses', 0) + (0 if attacker_wins else 1)}

💡 **نصيحة:** {'جمع المزيد من الموارد يزيد قوتك!' if not attacker_wins else 'استمر في التطوير!'}
        """
        
        await message.reply(battle_report)
        
        # إشعار المدافع (اختياري)
        try:
            if attacker_wins and gold_stolen > 0:
                defender_notification = f"""🚨 **تم مهاجمة قلعتك!** 🚨

⚔️ المهاجم: {user['first_name'] or user['username'] or 'مجهول'}
🏰 قلعة: {attacker_castle['name']}
💔 النتيجة: هزيمة لقلعتك
💰 تم سرقة: {format_number(gold_stolen)} ذهب

🛡️ طور قلعتك وادافع عنها بشكل أفضل!
                """
                # إرسال إشعار للمدافع (يحتاج معالج خاص)
        except:
            pass
        
    except Exception as e:
        logging.error(f"خطأ في هجوم القلعة: {e}")
        await message.reply("❌ حدث خطأ أثناء الهجوم")

async def castle_battles_log_command(message: Message):
    """عرض سجل معارك القلعة"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        castle = await get_user_castle(message.from_user.id)
        if not castle:
            await message.reply("❌ لا تملك قلعة لعرض سجل معاركها!")
            return
        
        # الحصول على آخر 10 معارك للمستخدم
        battles = await execute_query(
            """
            SELECT cb.*, 
                   uc1.name as attacker_castle_name,
                   uc2.name as defender_castle_name,
                   u1.first_name as attacker_name,
                   u2.first_name as defender_name
            FROM castle_battles cb
            LEFT JOIN user_castles uc1 ON cb.attacker_castle_id = uc1.castle_id
            LEFT JOIN user_castles uc2 ON cb.defender_castle_id = uc2.castle_id
            LEFT JOIN users u1 ON cb.attacker_user_id = u1.user_id
            LEFT JOIN users u2 ON cb.defender_user_id = u2.user_id
            WHERE cb.attacker_user_id = ? OR cb.defender_user_id = ?
            ORDER BY cb.created_at DESC
            LIMIT 10
            """,
            (message.from_user.id, message.from_user.id),
            fetch_all=True
        )
        
        if not battles:
            await message.reply(
                f"⚔️ **سجل معارك قلعة {castle['name']}**\n\n"
                f"📋 لا توجد معارك بعد!\n"
                f"💡 ابدأ أول معركة باستخدام: **قائمة القلاع**"
            )
            return
        
        battles_text = f"⚔️ **سجل معارك قلعة {castle['name']}**\n\n"
        
        for battle in battles:
            # تحديد دور المستخدم في المعركة
            is_attacker = battle['attacker_user_id'] == message.from_user.id
            won = (is_attacker and battle['winner'] == 'attacker') or (not is_attacker and battle['winner'] == 'defender')
            
            # تحديد الأيقونات والألوان
            result_icon = "🏆" if won else "💔"
            role = "مهاجم" if is_attacker else "مدافع"
            
            # اسم الخصم
            opponent_name = battle['defender_name'] if is_attacker else battle['attacker_name']
            opponent_castle = battle['defender_castle_name'] if is_attacker else battle['attacker_castle_name']
            
            # تاريخ المعركة
            battle_date = battle['created_at'][:16].replace('T', ' ')
            
            battles_text += f"{result_icon} **{role}** ضد {opponent_name or 'مجهول'}\n"
            battles_text += f"🏰 القلعة: {opponent_castle or 'غير معروفة'}\n"
            battles_text += f"💰 الذهب المسروق: {format_number(battle['gold_stolen'])}\n"
            battles_text += f"📅 التاريخ: {battle_date}\n\n"
        
        # إحصائيات إجمالية
        wins = sum(1 for battle in battles if 
                  (battle['attacker_user_id'] == message.from_user.id and battle['winner'] == 'attacker') or
                  (battle['defender_user_id'] == message.from_user.id and battle['winner'] == 'defender'))
        losses = len(battles) - wins
        
        battles_text += f"📊 **الإحصائيات:**\n"
        battles_text += f"🏆 انتصارات: {wins}\n"
        battles_text += f"💔 هزائم: {losses}\n"
        battles_text += f"📈 معدل الفوز: {(wins/len(battles)*100):.1f}%"
        
        await message.reply(battles_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض سجل المعارك: {e}")
        await message.reply("❌ حدث خطأ في عرض سجل المعارك")

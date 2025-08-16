"""
وحدة القلعة
Castle Module
"""

import logging
import random
from datetime import datetime, timedelta
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from database.operations import get_user, update_user_balance, execute_query, add_transaction
from utils.states import CastleStates
from utils.helpers import format_number

# مستويات المباني وتكاليف الترقية
CASTLE_BUILDINGS = {
    "main_hall": {
        "name": "القاعة الرئيسية",
        "emoji": "🏰",
        "max_level": 10,
        "base_cost": 10000,
        "cost_multiplier": 1.5,
        "benefits": {
            "gold_production": 50,
            "defense_bonus": 20,
            "storage_capacity": 1000
        }
    },
    "barracks": {
        "name": "الثكنات",
        "emoji": "⚔️",
        "max_level": 8,
        "base_cost": 15000,
        "cost_multiplier": 1.6,
        "benefits": {
            "attack_power": 30,
            "defense_bonus": 15,
            "troop_capacity": 10
        }
    },
    "treasury": {
        "name": "الخزانة",
        "emoji": "💰",
        "max_level": 12,
        "base_cost": 8000,
        "cost_multiplier": 1.4,
        "benefits": {
            "gold_production": 75,
            "storage_capacity": 2000,
            "interest_rate": 0.01
        }
    },
    "walls": {
        "name": "الأسوار",
        "emoji": "🏛️",
        "max_level": 15,
        "base_cost": 12000,
        "cost_multiplier": 1.3,
        "benefits": {
            "defense_bonus": 40,
            "attack_resistance": 25
        }
    },
    "tower": {
        "name": "برج المراقبة",
        "emoji": "🗼",
        "max_level": 6,
        "base_cost": 20000,
        "cost_multiplier": 1.8,
        "benefits": {
            "vision_range": 1,
            "attack_power": 20,
            "early_warning": 5
        }
    },
    "market": {
        "name": "السوق",
        "emoji": "🏪",
        "max_level": 10,
        "base_cost": 25000,
        "cost_multiplier": 1.7,
        "benefits": {
            "gold_production": 100,
            "trade_bonus": 10,
            "tax_income": 50
        }
    }
}


async def show_castle_menu(message: Message):
    """عرض قائمة القلعة الرئيسية"""
    try:
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام /start")
            return
        
        # الحصول على أو إنشاء قلعة المستخدم
        castle = await get_or_create_castle(message.from_user.id)
        
        # حساب القوة الإجمالية
        total_power = await calculate_castle_power(castle)
        hourly_income = await calculate_hourly_income(castle)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🔨 ترقية المباني", callback_data="castle_upgrade"),
                InlineKeyboardButton(text="⚔️ مهاجمة قلعة", callback_data="castle_attack")
            ],
            [
                InlineKeyboardButton(text="🛡️ إدارة الدفاع", callback_data="castle_defend"),
                InlineKeyboardButton(text="💰 جمع الذهب", callback_data="castle_collect")
            ],
            [
                InlineKeyboardButton(text="📊 إحصائيات", callback_data="castle_stats"),
                InlineKeyboardButton(text="🏆 ترتيب القلاع", callback_data="castle_ranking")
            ]
        ])
        
        castle_text = f"""
🏰 **قلعتك العظيمة**

💰 رصيدك النقدي: {format_number(user['balance'])}$

🏰 **حالة القلعة:**
⭐ المستوى العام: {castle['level']}
⚔️ قوة الهجوم: {castle['attack_points']}
🛡️ قوة الدفاع: {castle['defense_points']}
💰 إنتاج الذهب: {castle['gold_production']}/ساعة
📊 القوة الإجمالية: {total_power}

💎 الدخل بالساعة: {format_number(hourly_income)}$

🕐 آخر ترقية: {castle['last_upgrade'][:10] if castle['last_upgrade'] else 'لم يتم'}

💡 قم بترقية مبانيك لزيادة قوة قلعتك!
اختر العملية المطلوبة:
        """
        
        await message.reply(castle_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة القلعة: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة القلعة")


async def show_upgrade_options(message: Message):
    """عرض خيارات ترقية المباني"""
    try:
        user = await get_user(message.from_user.id)
        castle = await get_or_create_castle(message.from_user.id)
        
        if not user or not castle:
            await message.reply("❌ خطأ في الحصول على بيانات القلعة")
            return
        
        # الحصول على مستويات المباني الحالية
        building_levels = await get_building_levels(message.from_user.id)
        
        keyboard_buttons = []
        upgrade_text = "🔨 **ترقية المباني المتاحة:**\n\n"
        
        for building_id, building_info in CASTLE_BUILDINGS.items():
            current_level = building_levels.get(building_id, 1)
            
            if current_level >= building_info['max_level']:
                continue  # المبنى وصل للحد الأقصى
            
            next_level = current_level + 1
            upgrade_cost = int(building_info['base_cost'] * (building_info['cost_multiplier'] ** (next_level - 1)))
            
            affordable = user['balance'] >= upgrade_cost
            button_text = f"{building_info['emoji']} {building_info['name']} (المستوى {next_level})"
            
            if not affordable:
                button_text = f"❌ {button_text}"
            
            # عرض تفاصيل المبنى
            upgrade_text += f"{'✅' if affordable else '❌'} {building_info['emoji']} **{building_info['name']}**\n"
            upgrade_text += f"   📊 المستوى الحالي: {current_level}/{building_info['max_level']}\n"
            upgrade_text += f"   💰 تكلفة الترقية: {format_number(upgrade_cost)}$\n"
            
            # عرض المنافع
            for benefit, value in building_info['benefits'].items():
                benefit_increase = value * next_level
                upgrade_text += f"   📈 {benefit}: +{benefit_increase}\n"
            
            upgrade_text += "\n"
            
            if affordable and current_level < building_info['max_level']:
                keyboard_buttons.append([InlineKeyboardButton(
                    text=f"{building_info['emoji']} ترقية {building_info['name']} - {format_number(upgrade_cost)}$",
                    callback_data=f"castle_upgrade_{building_id}"
                )])
        
        if not keyboard_buttons:
            await message.reply(
                "🏆 **تهانينا!**\n\n"
                "جميع مبانيك في أعلى مستوى!\n"
                "قلعتك أصبحت قوية جداً!"
            )
            return
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        upgrade_text += f"💰 رصيدك الحالي: {format_number(user['balance'])}$"
        
        await message.reply(upgrade_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الترقية: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الترقية")


async def upgrade_building(message: Message, building_id: str):
    """ترقية مبنى معين"""
    try:
        user = await get_user(message.from_user.id)
        castle = await get_or_create_castle(message.from_user.id)
        
        if not user or not castle:
            await message.reply("❌ خطأ في الحصول على البيانات")
            return
        
        if building_id not in CASTLE_BUILDINGS:
            await message.reply("❌ مبنى غير صحيح")
            return
        
        building_info = CASTLE_BUILDINGS[building_id]
        building_levels = await get_building_levels(message.from_user.id)
        current_level = building_levels.get(building_id, 1)
        
        # التحقق من إمكانية الترقية
        if current_level >= building_info['max_level']:
            await message.reply(f"❌ {building_info['name']} وصل للحد الأقصى!")
            return
        
        next_level = current_level + 1
        upgrade_cost = int(building_info['base_cost'] * (building_info['cost_multiplier'] ** (next_level - 1)))
        
        if user['balance'] < upgrade_cost:
            await message.reply(
                f"❌ رصيد غير كافٍ!\n\n"
                f"🏗️ {building_info['name']}\n"
                f"💰 تكلفة الترقية: {format_number(upgrade_cost)}$\n"
                f"💵 رصيدك: {format_number(user['balance'])}$"
            )
            return
        
        # تنفيذ الترقية
        new_balance = user['balance'] - upgrade_cost
        await update_user_balance(message.from_user.id, new_balance)
        
        # تحديث مستوى المبنى
        await update_building_level(message.from_user.id, building_id, next_level)
        
        # إعادة حساب إحصائيات القلعة
        await recalculate_castle_stats(message.from_user.id)
        
        # إضافة معاملة
        await add_transaction(
            from_user_id=message.from_user.id,
            to_user_id=0,  # النظام
            transaction_type="castle_upgrade",
            amount=upgrade_cost,
            description=f"ترقية {building_info['name']} إلى المستوى {next_level}"
        )
        
        # حساب المنافع الجديدة
        new_benefits = {}
        for benefit, value in building_info['benefits'].items():
            new_benefits[benefit] = value * next_level
        
        await message.reply(
            f"🎉 **تمت الترقية بنجاح!**\n\n"
            f"{building_info['emoji']} المبنى: {building_info['name']}\n"
            f"📊 المستوى الجديد: {next_level}/{building_info['max_level']}\n"
            f"💰 التكلفة: {format_number(upgrade_cost)}$\n"
            f"💵 رصيدك الجديد: {format_number(new_balance)}$\n\n"
            f"📈 **المنافع الجديدة:**\n" +
            "\n".join([f"   • {k}: +{v}" for k, v in new_benefits.items()]) +
            "\n\n🏰 قلعتك أصبحت أقوى!"
        )
        
    except Exception as e:
        logging.error(f"خطأ في ترقية المبنى: {e}")
        await message.reply("❌ حدث خطأ في عملية الترقية")


async def show_defense_menu(message: Message):
    """عرض قائمة الدفاع"""
    try:
        castle = await get_or_create_castle(message.from_user.id)
        
        # الحصول على إحصائيات الدفاع
        defense_stats = await get_defense_statistics(message.from_user.id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="🛡️ تقوية الدفاعات", callback_data="castle_strengthen_defense"),
                InlineKeyboardButton(text="👥 تجنيد جنود", callback_data="castle_recruit")
            ],
            [
                InlineKeyboardButton(text="🔍 تقرير الدفاع", callback_data="castle_defense_report"),
                InlineKeyboardButton(text="⚔️ سجل المعارك", callback_data="castle_battle_log")
            ]
        ])
        
        defense_text = f"""
🛡️ **إدارة دفاعات القلعة**

🏰 **حالة الدفاع:**
🛡️ قوة الدفاع: {castle['defense_points']}
⚔️ قوة الهجوم: {castle['attack_points']}
👥 عدد الجنود: {defense_stats.get('troop_count', 0)}
🏛️ مستوى الأسوار: {defense_stats.get('wall_level', 1)}

📊 **إحصائيات المعارك:**
✅ انتصارات الدفاع: {defense_stats.get('defense_wins', 0)}
❌ هزائم: {defense_stats.get('defense_losses', 0)}
⚔️ معارك اليوم: {defense_stats.get('battles_today', 0)}

💡 تقوية دفاعاتك تحمي ذهبك من اللصوص!
        """
        
        await message.reply(defense_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في قائمة الدفاع: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة الدفاع")


async def show_attack_options(message: Message):
    """عرض خيارات الهجوم"""
    try:
        castle = await get_or_create_castle(message.from_user.id)
        
        # العثور على قلاع أخرى للهجوم عليها
        potential_targets = await find_attack_targets(message.from_user.id, castle['attack_points'])
        
        if not potential_targets:
            await message.reply(
                "⚔️ **لا توجد أهداف متاحة**\n\n"
                "لا توجد قلاع مناسبة للهجوم عليها حالياً.\n"
                "قم بترقية قلعتك أو حاول مرة أخرى لاحقاً."
            )
            return
        
        keyboard_buttons = []
        for target in potential_targets[:5]:  # أعلى 5 أهداف
            target_power = target['attack_points'] + target['defense_points']
            potential_loot = min(target['gold_production'] * 24, 10000)  # أقصى نهب يومي
            
            button_text = f"⚔️ هجوم على قلعة {target.get('username', 'مجهول')} (قوة: {target_power})"
            keyboard_buttons.append([InlineKeyboardButton(
                text=button_text,
                callback_data=f"castle_attack_target_{target['user_id']}"
            )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        attack_text = f"""
⚔️ **خيارات الهجوم المتاحة**

🏰 قوة هجومك: {castle['attack_points']}
🛡️ قوة دفاعك: {castle['defense_points']}

🎯 **الأهداف المتاحة:**
        """
        
        for target in potential_targets[:5]:
            target_power = target['attack_points'] + target['defense_points']
            potential_loot = min(target['gold_production'] * 24, 10000)
            
            attack_text += f"\n🏰 قلعة {target.get('username', 'مجهول')}\n"
            attack_text += f"   💪 القوة: {target_power}\n"
            attack_text += f"   💰 النهب المحتمل: {format_number(potential_loot)}$\n"
        
        attack_text += f"\n⚠️ **تحذير:** الهجوم محفوف بالمخاطر!"
        
        await message.reply(attack_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض خيارات الهجوم: {e}")
        await message.reply("❌ حدث خطأ في عرض خيارات الهجوم")


async def attack_castle(message: Message, target_user_id: int):
    """مهاجمة قلعة أخرى"""
    try:
        if target_user_id == message.from_user.id:
            await message.reply("❌ لا يمكنك مهاجمة قلعتك الخاصة!")
            return
        
        attacker_castle = await get_or_create_castle(message.from_user.id)
        defender_castle = await get_or_create_castle(target_user_id)
        
        if not attacker_castle or not defender_castle:
            await message.reply("❌ خطأ في الحصول على بيانات القلاع")
            return
        
        # حساب احتمالية النجاح
        attack_power = attacker_castle['attack_points']
        defense_power = defender_castle['defense_points']
        
        # إضافة عنصر عشوائي للإثارة
        attack_roll = random.randint(80, 120) / 100  # 80% - 120%
        defense_roll = random.randint(80, 120) / 100
        
        final_attack = attack_power * attack_roll
        final_defense = defense_power * defense_roll
        
        success = final_attack > final_defense
        
        if success:
            # الهجوم نجح
            loot_percentage = random.uniform(0.1, 0.3)  # 10% - 30%
            max_loot = defender_castle['gold_production'] * 48  # إنتاج يومين كحد أقصى
            loot_amount = int(min(max_loot * loot_percentage, 5000))  # حد أقصى 5000$
            
            # تحديث الأرصدة
            attacker = await get_user(message.from_user.id)
            defender = await get_user(target_user_id)
            
            if attacker and defender:
                new_attacker_balance = attacker['balance'] + loot_amount
                new_defender_balance = max(0, defender['balance'] - loot_amount)
                
                await update_user_balance(message.from_user.id, new_attacker_balance)
                await update_user_balance(target_user_id, new_defender_balance)
                
                # إضافة معاملة
                await add_transaction(
                    from_user_id=target_user_id,
                    to_user_id=message.from_user.id,
                    transaction_type="castle_raid_success",
                    amount=loot_amount,
                    description=f"نهب قلعة {defender.get('username', 'مجهول')}"
                )
                
                # تحديث إحصائيات المعارك
                await update_battle_stats(message.from_user.id, 'attack_win')
                await update_battle_stats(target_user_id, 'defense_loss')
                
                await message.reply(
                    f"🎉 **انتصار عظيم!**\n\n"
                    f"⚔️ نجح هجومك على قلعة {defender.get('username', 'العدو')}!\n\n"
                    f"💰 الغنائم: {format_number(loot_amount)}$\n"
                    f"💵 رصيدك الجديد: {format_number(new_attacker_balance)}$\n\n"
                    f"📊 **تفاصيل المعركة:**\n"
                    f"⚔️ قوة هجومك: {final_attack:.0f}\n"
                    f"🛡️ قوة دفاع العدو: {final_defense:.0f}\n\n"
                    f"🏆 مبروك النصر!"
                )
                
                # إشعار المدافع
                try:
                    await message.bot.send_message(
                        target_user_id,
                        f"💥 **تعرضت قلعتك للهجوم!**\n\n"
                        f"⚔️ المهاجم: {message.from_user.username or 'غازي مجهول'}\n"
                        f"💸 الخسائر: {format_number(loot_amount)}$\n"
                        f"💰 رصيدك الجديد: {format_number(new_defender_balance)}$\n\n"
                        f"🛡️ قم بتقوية دفاعاتك لحماية أفضل!"
                    )
                except:
                    pass
        else:
            # الهجوم فشل
            penalty = random.randint(100, 500)
            attacker = await get_user(message.from_user.id)
            
            if attacker:
                new_balance = max(0, attacker['balance'] - penalty)
                await update_user_balance(message.from_user.id, new_balance)
                
                # تحديث إحصائيات المعارك
                await update_battle_stats(message.from_user.id, 'attack_loss')
                await update_battle_stats(target_user_id, 'defense_win')
                
                await message.reply(
                    f"💥 **هزيمة مُرة!**\n\n"
                    f"🛡️ فشل هجومك على القلعة!\n"
                    f"دفاعات العدو كانت أقوى من المتوقع.\n\n"
                    f"💸 الخسائر: {format_number(penalty)}$\n"
                    f"💰 رصيدك الجديد: {format_number(new_balance)}$\n\n"
                    f"📊 **تفاصيل المعركة:**\n"
                    f"⚔️ قوة هجومك: {final_attack:.0f}\n"
                    f"🛡️ قوة دفاع العدو: {final_defense:.0f}\n\n"
                    f"💡 قم بترقية جيشك وحاول مرة أخرى!"
                )
        
    except Exception as e:
        logging.error(f"خطأ في مهاجمة القلعة: {e}")
        await message.reply("❌ حدث خطأ في المعركة")


async def get_or_create_castle(user_id: int):
    """الحصول على قلعة المستخدم أو إنشاء واحدة جديدة"""
    try:
        castle = await execute_query(
            "SELECT * FROM castle WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        if not castle:
            # إنشاء قلعة جديدة
            await execute_query(
                "INSERT INTO castle (user_id, level, defense_points, attack_points, gold_production) VALUES (?, ?, ?, ?, ?)",
                (user_id, 1, 100, 50, 10)
            )
            
            castle = await execute_query(
                "SELECT * FROM castle WHERE user_id = ?",
                (user_id,),
                fetch=True
            )
        
        return castle
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على القلعة: {e}")
        return None


async def get_building_levels(user_id: int):
    """الحصول على مستويات المباني"""
    try:
        # يفترض وجود جدول castle_buildings
        buildings = await execute_query(
            "SELECT building_type, level FROM castle_buildings WHERE user_id = ?",
            (user_id,),
            fetch=True
        )
        
        if not buildings:
            return {building: 1 for building in CASTLE_BUILDINGS.keys()}
        
        if isinstance(buildings, list):
            return {building['building_type']: building['level'] for building in buildings}
        else:
            return {buildings['building_type']: buildings['level']}
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على مستويات المباني: {e}")
        return {building: 1 for building in CASTLE_BUILDINGS.keys()}


async def update_building_level(user_id: int, building_id: str, new_level: int):
    """تحديث مستوى مبنى"""
    try:
        # محاولة التحديث أولاً
        result = await execute_query(
            "UPDATE castle_buildings SET level = ? WHERE user_id = ? AND building_type = ?",
            (new_level, user_id, building_id)
        )
        
        # إذا لم يتم العثور على السجل، أنشئ واحداً جديداً
        if result == 0:
            await execute_query(
                "INSERT INTO castle_buildings (user_id, building_type, level) VALUES (?, ?, ?)",
                (user_id, building_id, new_level)
            )
        
    except Exception as e:
        logging.error(f"خطأ في تحديث مستوى المبنى: {e}")


async def recalculate_castle_stats(user_id: int):
    """إعادة حساب إحصائيات القلعة"""
    try:
        building_levels = await get_building_levels(user_id)
        
        total_attack = 50  # القيمة الأساسية
        total_defense = 100
        total_gold_production = 10
        
        # حساب المجاميع من جميع المباني
        for building_id, level in building_levels.items():
            if building_id in CASTLE_BUILDINGS:
                building_info = CASTLE_BUILDINGS[building_id]
                benefits = building_info['benefits']
                
                total_attack += benefits.get('attack_power', 0) * level
                total_defense += benefits.get('defense_bonus', 0) * level
                total_gold_production += benefits.get('gold_production', 0) * level
        
        # حساب المستوى العام للقلعة
        avg_level = sum(building_levels.values()) // len(building_levels)
        
        # تحديث إحصائيات القلعة
        await execute_query(
            "UPDATE castle SET level = ?, attack_points = ?, defense_points = ?, gold_production = ?, last_upgrade = ? WHERE user_id = ?",
            (avg_level, total_attack, total_defense, total_gold_production, datetime.now().isoformat(), user_id)
        )
        
    except Exception as e:
        logging.error(f"خطأ في إعادة حساب إحصائيات القلعة: {e}")


async def calculate_castle_power(castle):
    """حساب القوة الإجمالية للقلعة"""
    attack = castle.get('attack_points', 0)
    defense = castle.get('defense_points', 0)
    gold_prod = castle.get('gold_production', 0)
    
    # الصيغة: (هجوم + دفاع) * 2 + إنتاج الذهب
    return (attack + defense) * 2 + gold_prod


async def calculate_hourly_income(castle):
    """حساب الدخل بالساعة"""
    return castle.get('gold_production', 0)


async def find_attack_targets(attacker_id: int, attacker_power: int):
    """العثور على أهداف مناسبة للهجوم"""
    try:
        # البحث عن قلاع بقوة مماثلة أو أقل قليلاً
        min_power = max(1, attacker_power * 0.5)  # 50% من قوة المهاجم كحد أدنى
        max_power = attacker_power * 1.5  # 150% كحد أقصى
        
        targets = await execute_query(
            """
            SELECT c.*, u.username 
            FROM castle c 
            JOIN users u ON c.user_id = u.user_id 
            WHERE c.user_id != ? 
            AND (c.attack_points + c.defense_points) BETWEEN ? AND ?
            AND c.gold_production > 0
            ORDER BY RANDOM()
            LIMIT 10
            """,
            (attacker_id, min_power, max_power),
            fetch=True
        )
        
        return targets if targets else []
        
    except Exception as e:
        logging.error(f"خطأ في العثور على أهداف الهجوم: {e}")
        return []


async def get_defense_statistics(user_id: int):
    """الحصول على إحصائيات الدفاع"""
    try:
        stats = {}
        
        # حساب المعارك اليوم
        today = datetime.now().date()
        battles_today = await execute_query(
            "SELECT COUNT(*) as count FROM transactions WHERE (from_user_id = ? OR to_user_id = ?) AND transaction_type LIKE 'castle_%' AND DATE(created_at) = ?",
            (user_id, user_id, today),
            fetch=True
        )
        
        stats['battles_today'] = battles_today['count'] if battles_today else 0
        
        # إحصائيات وهمية للعرض (يمكن استبدالها بإحصائيات حقيقية)
        stats['troop_count'] = random.randint(10, 100)
        stats['wall_level'] = random.randint(1, 10)
        stats['defense_wins'] = random.randint(0, 20)
        stats['defense_losses'] = random.randint(0, 10)
        
        return stats
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على إحصائيات الدفاع: {e}")
        return {}


async def update_battle_stats(user_id: int, result_type: str):
    """تحديث إحصائيات المعارك"""
    try:
        await execute_query(
            "INSERT INTO stats (user_id, action_type, action_data) VALUES (?, ?, ?)",
            (user_id, f"castle_{result_type}", "")
        )
    except Exception as e:
        logging.error(f"خطأ في تحديث إحصائيات المعارك: {e}")


async def collect_castle_gold(user_id: int):
    """جمع ذهب القلعة (للتشغيل الدوري)"""
    try:
        castle = await get_or_create_castle(user_id)
        if not castle:
            return 0
        
        gold_amount = castle['gold_production']
        
        if gold_amount > 0:
            user = await get_user(user_id)
            if user:
                new_balance = user['balance'] + gold_amount
                await update_user_balance(user_id, new_balance)
                
                await add_transaction(
                    from_user_id=0,
                    to_user_id=user_id,
                    transaction_type="castle_gold_production",
                    amount=gold_amount,
                    description="إنتاج ذهب القلعة"
                )
        
        return gold_amount
        
    except Exception as e:
        logging.error(f"خطأ في جمع ذهب القلعة: {e}")
        return 0


# معالجات الحالات
async def process_upgrade_confirmation(message: Message, state: FSMContext):
    """معالجة تأكيد الترقية"""
    await message.reply("تم تأكيد الترقية")
    await state.clear()

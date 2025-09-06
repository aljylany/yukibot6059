"""
لعبة النقابة - نسخة مبسطة
Guild Game - Simplified Version
"""

import logging
import time
import random
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.operations import get_or_create_user, update_user_balance, add_transaction
from utils.helpers import format_number
from modules.guild_database import save_guild_player, load_guild_player

# حالات FSM للعبة النقابة
class GuildStates(StatesGroup):
    choosing_guild = State()
    choosing_gender = State()
    choosing_class = State()
    main_menu = State()
    missions_menu = State()
    shop_menu = State()

# تخزين بيانات لاعبي النقابة {user_id: GuildPlayer}
GUILD_PLAYERS: Dict[int, 'GuildPlayer'] = {}

# تخزين المهام النشطة {user_id: ActiveMission}
ACTIVE_MISSIONS: Dict[int, 'ActiveMission'] = {}

# كولداون المهام لمنع الإزعاج
MISSION_COOLDOWN: Dict[int, float] = {}

@dataclass
class GuildPlayer:
    """بيانات لاعب النقابة"""
    user_id: int
    username: str
    name: str
    guild: str
    gender: str
    character_class: str
    advanced_class: str
    level: int
    power: int
    experience: int
    experience_needed: int
    money: int  # إضافة حقل المال
    weapon: Optional[str]
    badge: Optional[str]
    title: Optional[str]
    potion: Optional[str]
    ring: Optional[str]
    animal: Optional[str]
    personal_code: str
    created_at: datetime
    
    def __post_init__(self):
        if not self.personal_code:
            self.personal_code = self.generate_personal_code()
    
    def generate_personal_code(self) -> str:
        """توليد رمز شخصي فريد"""
        chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
        return ''.join(random.choices(chars, k=6))
    
    def get_experience_for_next_level(self) -> int:
        """حساب الخبرة المطلوبة للمستوى التالي"""
        return self.level * 600  # 600 نقطة خبرة لكل مستوى
    
    def can_level_up(self) -> bool:
        """فحص إمكانية الترقية"""
        return self.experience >= self.get_experience_for_next_level()
    
    def level_up(self) -> bool:
        """ترقية المستوى"""
        if not self.can_level_up():
            return False
        
        needed_exp = self.get_experience_for_next_level()
        self.experience -= needed_exp
        self.level += 1
        self.power += 50  # زيادة القوة مع كل مستوى
        return True
    
    async def save_to_database(self):
        """حفظ بيانات اللاعب في قاعدة البيانات"""
        player_dict = {
            'user_id': self.user_id,
            'username': self.username,
            'name': self.name,
            'guild': self.guild,
            'gender': self.gender,
            'character_class': self.character_class,
            'advanced_class': self.advanced_class,
            'level': self.level,
            'power': self.power,
            'experience': self.experience,
            'money': self.money,
            'weapon': self.weapon,
            'badge': self.badge,
            'title': self.title,
            'potion': self.potion,
            'ring': self.ring,
            'animal': self.animal,
            'personal_code': self.personal_code
        }
        await save_guild_player(player_dict)

@dataclass  
class ActiveMission:
    """مهمة نشطة"""
    mission_id: str
    mission_name: str
    mission_type: str
    duration_minutes: int
    experience_reward: int
    money_reward: int
    start_time: datetime
    
    def is_completed(self) -> bool:
        """فحص إذا انتهت المهمة"""
        elapsed = datetime.now() - self.start_time
        return elapsed.total_seconds() >= (self.duration_minutes * 60)
    
    def time_remaining(self) -> str:
        """الوقت المتبقي للانتهاء"""
        elapsed = datetime.now() - self.start_time
        remaining_seconds = (self.duration_minutes * 60) - elapsed.total_seconds()
        
        if remaining_seconds <= 0:
            return "انتهت!"
        
        minutes = int(remaining_seconds // 60)
        seconds = int(remaining_seconds % 60)
        return f"{minutes}:{seconds:02d}"

# نقابات متاحة
GUILDS = {
    "heroes": "🏆 نقابة الأبطال",
    "demons": "😈 نقابة الشياطين", 
    "mysterious": "🌙 نقابة غامضة"
}

# أجناس متاحة
GENDERS = {
    "male": "👨 ذكر",
    "female": "👩 أنثى"
}

# فئات متاحة
CLASSES = {
    "warrior": "⚔️ محارب",
    "mage": "🧙‍♂️ ساحر",
    "healer": "💚 معالج",
    "ghoul": "👹 غول",
    "summoner": "🔮 مستدعي"
}

# فئات متقدمة (تحتاج مستويات عالية)
ADVANCED_CLASSES = {
    "demon": {"name": "😈 عفريت", "required_level": 20},
    "vampire": {"name": "🧛‍♂️ مصاص دماء", "required_level": 40},
    "devil": {"name": "👿 شيطان", "required_level": 60},
    "genie": {"name": "🧞‍♂️ جني", "required_level": 70},
    "angel": {"name": "😇 ملاك", "required_level": 80},
    "dark_lord": {"name": "🖤 ملك الظلام", "required_level": 90},
    "demon_king": {"name": "👑 ملك الشياطين", "required_level": 109}
}

# مهام متاحة
MISSIONS = {
    "normal": {
        "fruit_picking": {
            "name": "🍎 قطف الفاكهة",
            "description": "اجمع الفواكه من البستان المحلي",
            "duration": 12,
            "experience": 12000,
            "money": 5000,
            "required_level": 1,
            "power_requirement": 0
        },
        "guard_caravan": {
            "name": "🛡️ حارس القافلة", 
            "description": "احرس القافلة التجارية",
            "duration": 15,
            "experience": 15000,
            "money": 8000,
            "required_level": 2,
            "power_requirement": 150
        },
        "deliver_message": {
            "name": "📜 نقل رسالة",
            "description": "أوصل رسالة مهمة للمدينة المجاورة",
            "duration": 10,
            "experience": 10000,
            "money": 4000,
            "required_level": 1,
            "power_requirement": 0
        },
        "bridge_repair": {
            "name": "🌉 إصلاح الجسر",
            "description": "ساعد في إصلاح الجسر المدمر",
            "duration": 20,
            "experience": 18000,
            "money": 10000,
            "required_level": 3,
            "power_requirement": 200
        },
        "monster_watch": {
            "name": "👁️ رصد الوحوش",
            "description": "راقب تحركات الوحوش خارج المدينة",
            "duration": 18,
            "experience": 16000,
            "money": 7000,
            "required_level": 2,
            "power_requirement": 150
        }
    },
    "collect": {
        "phoenix_pearls": {
            "name": "🔥 درر العنقاء",
            "description": "استخرج 7 درر متوهجة من أعشاش العنقاء",
            "duration": 14,
            "experience": 9000,
            "money": 6000,
            "required_level": 1,
            "power_requirement": 16000
        },
        "light_crystals": {
            "name": "💎 بلورات الضوء",
            "description": "اجمع بلورات الضوء من الكهوف المقدسة",
            "duration": 25,
            "experience": 20000,
            "money": 15000,
            "required_level": 2,
            "power_requirement": 20000
        },
        "shark_eyes": {
            "name": "👁️ عيون القرش الفضية",
            "description": "اصطد أسماك القرش واحصل على عيونها",
            "duration": 30,
            "experience": 25000,
            "money": 18000,
            "required_level": 4,
            "power_requirement": 30000
        },
        "water_crystals": {
            "name": "💧 البلورات المائية",
            "description": "استخرج البلورات من قاع البحيرة",
            "duration": 22,
            "experience": 18000,
            "money": 12000,
            "required_level": 3,
            "power_requirement": 25000
        }
    },
    "medium": {
        "orc_battle": {
            "name": "⚔️ معركة الأوركس",
            "description": "قاتل قبيلة الأوركس الشرسة في جبال الشمال",
            "duration": 40,
            "experience": 35000,
            "money": 25000,
            "required_level": 15,
            "power_requirement": 50000
        },
        "cursed_tomb": {
            "name": "🏺 المقبرة الملعونة", 
            "description": "طهر المقبرة الملعونة من الأرواح الشريرة",
            "duration": 50,
            "experience": 45000,
            "money": 35000,
            "required_level": 20,
            "power_requirement": 75000
        },
        "troll_king": {
            "name": "👑 ملك العفاريت",
            "description": "واجه ملك العفاريت في قلعته المظلمة",
            "duration": 60,
            "experience": 60000,
            "money": 50000,
            "required_level": 25,
            "power_requirement": 100000
        },
        "demon_gate": {
            "name": "🚪 بوابة الشياطين",
            "description": "أغلق بوابة الشياطين قبل أن يغزوا العالم",
            "duration": 80,
            "experience": 80000,
            "money": 70000,
            "required_level": 30,
            "power_requirement": 150000
        },
        "shadow_lord": {
            "name": "👤 سيد الظلال",
            "description": "هزم سيد الظلال في مملكة الظلام",
            "duration": 100,
            "experience": 100000,
            "money": 100000,
            "required_level": 35,
            "power_requirement": 200000
        }
    },
    "legendary": {
        "red_dragon": {
            "name": "🐲 التنين الأحمر الأعظم",
            "description": "واجه التنين الأحمر الأعظم في عرينه الناري",
            "duration": 120,
            "experience": 200000,
            "money": 200000,
            "required_level": 40,
            "power_requirement": 300000
        },
        "dark_sorcerer": {
            "name": "🧙‍♂️ الساحر الأعظم المظلم",
            "description": "اكسر لعنة الساحر الأعظم وأنقذ المملكة",
            "duration": 150,
            "experience": 300000,
            "money": 300000,
            "required_level": 45,
            "power_requirement": 400000
        },
        "chaos_demon": {
            "name": "😈 شيطان الفوضى",
            "description": "امحق شيطان الفوضى قبل أن يدمر العالم",
            "duration": 180,
            "experience": 500000,
            "money": 500000,
            "required_level": 50,
            "power_requirement": 600000
        },
        "cosmic_entity": {
            "name": "🌌 الكائن الكوني",
            "description": "واجه الكائن الكوني في أعماق الفضاء",
            "duration": 240,
            "experience": 800000,
            "money": 800000,
            "required_level": 60,
            "power_requirement": 1000000
        },
        "god_slayer": {
            "name": "⚡ قاتل الآلهة",
            "description": "المعركة الأخيرة ضد إله الدمار نفسه",
            "duration": 300,
            "experience": 1500000,
            "money": 1500000,
            "required_level": 70,
            "power_requirement": 2000000
        }
    }
}

# متجر العناصر
SHOP_ITEMS = {
    "weapons": {
        "rage_sword": {
            "name": "⚔️ سيف الغضب",
            "price": 200,
            "power_bonus": 25,
            "description": "سيف حاد يزيد من قوة الهجوم"
        },
        "mirage_staff": {
            "name": "🪄 عصا السراب", 
            "price": 150,
            "power_bonus": 15,
            "description": "عصا سحرية تخدع الأعداء"
        },
        "demon_blade": {
            "name": "🗡️ نصل الشيطان",
            "price": 500,
            "power_bonus": 50,
            "description": "نصل ملعون بقوة شيطانية"
        }
    },
    "badges": {
        "white_pearl": {
            "name": "🤍 وسام اللؤلؤ الأبيض",
            "price": 400,
            "power_bonus": 20,
            "description": "وسام يرمز للنقاء والشرف"
        },
        "dark_shadow": {
            "name": "🖤 وسام الظل المظلم",
            "price": 250,
            "power_bonus": 15,
            "description": "وسام يمنح قوة الظلال"
        },
        "golden_eagle": {
            "name": "🦅 وسام النسر الذهبي",
            "price": 600,
            "power_bonus": 35,
            "description": "وسام الشجاعة والحرية"
        }
    },
    "titles": {
        "wind_soul": {
            "name": "💨 روح الريح",
            "price": 650,
            "power_bonus": 30,
            "description": "لقب يمنح سرعة البرق"
        },
        "sky_thunder": {
            "name": "⚡ صاعقة السماء",
            "price": 450,
            "power_bonus": 25,
            "description": "لقب القوة والرعد"
        },
        "fire_lord": {
            "name": "🔥 سيد النار",
            "price": 800,
            "power_bonus": 40,
            "description": "لقب يحكم عنصر النار"
        }
    },
    "potions": {
        "rage_elixir": {
            "name": "🧪 إكسير الغضب",
            "price": 1500,
            "power_bonus": 100,
            "description": "جرعة تضاعف قوتك مؤقتاً"
        },
        "poison_drop": {
            "name": "☠️ قطر السم السحري",
            "price": 600,
            "power_bonus": 50,
            "description": "جرعة سامة تضعف الأعداء"
        },
        "healing_potion": {
            "name": "💚 جرعة الشفاء الكبرى",
            "price": 800,
            "power_bonus": 60,
            "description": "تشفي الجروح وتقوي الجسد"
        }
    },
    "rings": {
        "broken_time": {
            "name": "⏰ خاتم الزمن المكسور",
            "price": 300,
            "power_bonus": 20,
            "description": "يتلاعب بالزمن ببطء"
        },
        "frost_ring": {
            "name": "🧊 خاتم الصقيع",
            "price": 900,
            "power_bonus": 70,
            "description": "يجمد أعداءك في مكانهم"
        },
        "destiny_ring": {
            "name": "✨ خاتم القدر",
            "price": 40000,
            "power_bonus": 500,
            "description": "خاتم أسطوري يغير المصير"
        }
    },
    "animals": {
        "dragondo": {
            "name": "🐉 دراجوندو",
            "price": 200,
            "power_bonus": 30,
            "description": "تنين صغير أليف وقوي"
        },
        "akila": {
            "name": "🦅 أكيلا",
            "price": 600,
            "power_bonus": 45,
            "description": "نسر ذهبي سريع ومخلص"
        },
        "ikoria": {
            "name": "🦄 إيكوريا",
            "price": 1200,
            "power_bonus": 80,
            "description": "وحيد القرن الأسطوري"
        }
    }
}

async def start_guild_registration(message: Message, state: FSMContext):
    """بدء تسجيل في لعبة النقابة"""
    try:
        user_id = message.from_user.id
        username = message.from_user.username or ""
        name = message.from_user.first_name or "اللاعب"
        
        # فحص إذا كان اللاعب مسجل بالفعل في الذاكرة
        if user_id in GUILD_PLAYERS:
            logging.info(f"🎮 GUILD DEBUG: اللاعب {user_id} مسجل بالفعل، عرض القائمة الرئيسية")
            await show_guild_main_menu(message, state)
            return
        
        # فحص إذا كان اللاعب مسجل في قاعدة البيانات
        player_data = await load_guild_player(user_id)
        if player_data:
            # تحميل البيانات إلى الذاكرة
            player = GuildPlayer(
                user_id=player_data['user_id'],
                username=player_data['username'],
                name=player_data['name'],
                guild=player_data['guild'],
                gender=player_data['gender'],
                character_class=player_data['character_class'],
                advanced_class=player_data['advanced_class'],
                level=player_data['level'],
                power=player_data['power'],
                experience=player_data['experience'],
                experience_needed=player_data['level'] * 600,
                money=player_data.get('money', 5000),  # قيمة افتراضية لو لم توجد
                weapon=player_data['weapon'],
                badge=player_data['badge'],
                title=player_data['title'],
                potion=player_data['potion'],
                ring=player_data['ring'],
                animal=player_data['animal'],
                personal_code=player_data['personal_code'],
                created_at=datetime.fromisoformat(player_data['created_at'])
            )
            GUILD_PLAYERS[user_id] = player
            await show_guild_main_menu(message, state)
            return
        
        # إنشاء لوحة مفاتيح النقابات
        keyboard = []
        for guild_id, guild_name in GUILDS.items():
            keyboard.append([InlineKeyboardButton(
                text=guild_name,
                callback_data=f"guild_select_{guild_id}"
            )])
        
        await message.reply(
            "⚡ **اختر نقابتك لتبدأ رحلتك البطولية:**\n\n"
            "🏆 **نقابة الأبطال** - للمحاربين الشرفاء\n"
            "😈 **نقابة الشياطين** - للمحاربين الأقوياء\n"
            "🌙 **نقابة غامضة** - للمحاربين الغامضين\n\n"
            "اختر نقابتك بحكمة!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await state.set_state(GuildStates.choosing_guild)
        
    except Exception as e:
        logging.error(f"خطأ في بدء تسجيل النقابة: {e}")
        await message.reply("❌ حدث خطأ في بدء اللعبة")

async def handle_guild_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار النقابة"""
    try:
        guild_id = callback.data.split("_")[2]
        await state.update_data(guild=guild_id)
        
        # إنشاء لوحة مفاتيح الأجناس
        keyboard = []
        for gender_id, gender_name in GENDERS.items():
            keyboard.append([InlineKeyboardButton(
                text=gender_name,
                callback_data=f"gender_select_{gender_id}"
            )])
        
        await callback.message.edit_text(
            f"✅ **اخترت {GUILDS[guild_id]}!**\n\n"
            "👶 **اختر جنسك لتجسد هويتك:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await state.set_state(GuildStates.choosing_gender)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في اختيار النقابة: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_gender_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار الجنس"""
    try:
        logging.info(f"🔍 GENDER DEBUG: استقبال بيانات الجنس: '{callback.data}'")
        
        # التحقق من أن البيانات تحتوي على gender_select
        if not callback.data.startswith("gender_select_"):
            logging.error(f"بيانات غير صحيحة في اختيار الجنس: {callback.data}")
            await callback.answer("❌ بيانات غير صحيحة")
            return
            
        parts = callback.data.split("_")
        if len(parts) < 3:
            logging.error(f"بيانات غير صحيحة في اختيار الجنس: {callback.data}")
            await callback.answer("❌ بيانات غير صحيحة")
            return
        gender_id = parts[2]
        logging.info(f"🔍 GENDER DEBUG: تم تحليل الجنس: '{gender_id}'")
        await state.update_data(gender=gender_id)
        
        # إنشاء لوحة مفاتيح الفئات
        keyboard = []
        for class_id, class_name in CLASSES.items():
            keyboard.append([InlineKeyboardButton(
                text=class_name,
                callback_data=f"class_select_{class_id}"
            )])
        
        await callback.message.edit_text(
            f"✅ **اخترت {GENDERS[gender_id]}!**\n\n"
            "🧙‍♂️ **اختر فئتك لتجسد قوتك:**\n\n"
            "⚔️ **محارب** - قوة في المعارك القريبة\n"
            "🧙‍♂️ **ساحر** - قوة السحر والعناصر\n"
            "💚 **معالج** - قوة الشفاء والدعم\n"
            "👹 **غول** - قوة الظلام والرعب\n"
            "🔮 **مستدعي** - قوة استدعاء المخلوقات",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
        await state.set_state(GuildStates.choosing_class)
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في اختيار الجنس: {e}")
        await callback.answer("❌ حدث خطأ")

async def handle_class_selection(callback: CallbackQuery, state: FSMContext):
    """معالجة اختيار الفئة وإنهاء التسجيل"""
    try:
        class_id = callback.data.split("_")[2]
        data = await state.get_data()
        
        user_id = callback.from_user.id
        username = callback.from_user.username or ""
        name = callback.from_user.first_name or "اللاعب"
        
        # إنشاء لاعب جديد
        player = GuildPlayer(
            user_id=user_id,
            username=username,
            name=name,
            guild=data['guild'],
            gender=data['gender'],
            character_class=class_id,
            advanced_class="غير متاح",
            level=1,
            power=100,
            experience=0,
            experience_needed=600,
            money=5000,  # مال ابتدائي
            weapon=None,
            badge=None,
            title=None,
            potion=None,
            ring=None,
            animal=None,
            personal_code="",
            created_at=datetime.now()
        )
        
        # حفظ اللاعب في الذاكرة وقاعدة البيانات
        GUILD_PLAYERS[user_id] = player
        
        # حفظ في قاعدة البيانات
        player_dict = {
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
            'money': player.money,
            'weapon': player.weapon,
            'badge': player.badge,
            'title': player.title,
            'potion': player.potion,
            'ring': player.ring,
            'animal': player.animal,
            'personal_code': player.personal_code
        }
        await save_guild_player(player_dict)
        
        # رسالة الترحيب
        guild_name = GUILDS[data['guild']]
        gender_name = GENDERS[data['gender']]
        class_name = CLASSES[class_id]
        
        await callback.message.edit_text(
            f"🎉 **مبروك! لقد انضممت إلى {guild_name} كـ {class_name}!**\n\n"
            f"🧙‍♂️ **معلوماتك الأسطورية:**\n"
            f"👶 الجنس: {gender_name}\n"
            f"⚡ الفئة: {class_name} - بداية رحلتك البطولية!\n"
            f"🔥 الفئة المتقدمة: غير متاح - ارتقِ لتكتشف قوتك الحقيقية!\n"
            f"🏅 المستوى: 1 - أولى خطواتك نحو الخلود!\n"
            f"⚔️ القوة: 100 - قوة تنتظر التحدي!\n"
            f"⭐ النقاط: 0 - دربك إلى الأسطورة!\n"
            f"🧪 الجرعة: غير متاح\n"
            f"🏷️ اللقب: غير متاح\n"
            f"🎖️ الوسام: غير متاح\n"
            f"🐾 الحيوان: غير متاح\n"
            f"💍 الخاتم: غير متاح\n"
            f"🗡️ السلاح: غير متاح\n\n"
            f"📜 اكتب 'رمزي' لعرض رمزك الشخصي!\n"
            f"📜 اكتب 'مهام' لبدء المغامرات!\n"
            f"🛒 اكتب 'متجر' لشراء العناصر!"
        )
        
        await state.clear()
        await callback.answer("🎉 مرحباً بك في لعبة النقابة!")
        
    except Exception as e:
        logging.error(f"خطأ في اختيار الفئة: {e}")
        await callback.answer("❌ حدث خطأ")

async def show_guild_main_menu(message: Message, state: FSMContext):
    """عرض القائمة الرئيسية للنقابة"""
    try:
        user_id = message.from_user.id
        
        # محاولة تحميل اللاعب من قاعدة البيانات إذا لم يكن في الذاكرة
        if user_id not in GUILD_PLAYERS:
            from modules.guild_database import load_guild_player
            player_data = await load_guild_player(user_id)
            if player_data:
                # إضافة اللاعب للذاكرة
                GUILD_PLAYERS[user_id] = player_data
                logging.info(f"✅ تم تحميل بيانات اللاعب {user_id} من قاعدة البيانات")
            else:
                # إذا لم يوجد في قاعدة البيانات، ابدأ التسجيل
                await start_guild_registration(message, state)
                return
        
        player = GUILD_PLAYERS[user_id]
        guild_name = GUILDS[player.guild]
        gender_name = GENDERS[player.gender]
        class_name = CLASSES[player.character_class]
        
        keyboard = [
            [InlineKeyboardButton(text="🎯 مهام", callback_data="guild_missions")],
            [InlineKeyboardButton(text="🛒 متجر", callback_data="guild_shop")],
            [InlineKeyboardButton(text="🏰 متاهات", callback_data="guild_mazes")],
            [InlineKeyboardButton(text="📊 ترقية", callback_data="guild_upgrade")],
            [InlineKeyboardButton(text="🆔 رمزي", callback_data="guild_code")],
            [InlineKeyboardButton(text="⚡ تغيير فئة", callback_data="guild_change_class")]
        ]
        
        await message.reply(
            f"🏰 **قائمة {guild_name}**\n\n"
            f"👤 **{player.name}** ({gender_name})\n"
            f"⚡ **الفئة:** {class_name}\n"
            f"🔥 **الفئة المتقدمة:** {player.advanced_class}\n"
            f"🏅 **المستوى:** {player.level}\n"
            f"⚔️ **القوة:** {format_number(player.power)}\n"
            f"⭐ **الخبرة:** {format_number(player.experience)}/{format_number(player.get_experience_for_next_level())}\n\n"
            f"🎮 **اختر ما تريد فعله:**",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=keyboard)
        )
        
    except Exception as e:
        logging.error(f"خطأ في عرض القائمة الرئيسية: {e}")
        await message.reply("❌ حدث خطأ في عرض القائمة")

async def show_personal_code(callback: CallbackQuery):
    """عرض الرمز الشخصي"""
    try:
        user_id = callback.from_user.id
        
        if user_id not in GUILD_PLAYERS:
            await callback.answer("❌ لست مسجل في النقابة!")
            return
        
        player = GUILD_PLAYERS[user_id]
        
        await callback.message.edit_text(
            f"🆔 **رمز {player.name}: {player.personal_code} - مفتاح هويته!**\n\n"
            f"💡 استخدم هذا الرمز للتعريف بنفسك في المهام الخاصة!",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(text="🔙 رجوع", callback_data="guild_main_menu")
            ]])
        )
        
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في عرض الرمز الشخصي: {e}")
        await callback.answer("❌ حدث خطأ")

async def create_new_player(user_id: int, name: str):
    """إنشاء لاعب جديد بالإعدادات الافتراضية"""
    try:
        # إنشاء لاعب بالإعدادات الافتراضية
        player = GuildPlayer(
            user_id=user_id,
            username=f"user_{user_id}",
            name=name,
            guild="heroes",  # نقابة افتراضية
            gender="male",   # جنس افتراضي
            character_class="warrior",  # فئة افتراضية
            advanced_class="غير متاح",
            level=1,
            power=100,
            experience=0,
            experience_needed=600,
            money=5000,  # مال ابتدائي
            weapon=None,
            badge=None,
            title=None,
            potion=None,
            ring=None,
            animal=None,
            personal_code="",
            created_at=datetime.now()
        )
        
        # حفظ اللاعب في الذاكرة وقاعدة البيانات
        GUILD_PLAYERS[user_id] = player
        await player.save_to_database()
        return player
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء لاعب جديد: {e}")
        return None

# تصدير الدوال المطلوبة
__all__ = [
    'start_guild_registration',
    'handle_guild_selection',
    'handle_gender_selection', 
    'handle_class_selection',
    'show_guild_main_menu',
    'show_personal_code',
    'create_new_player',
    'GUILD_PLAYERS',
    'ACTIVE_MISSIONS'
]
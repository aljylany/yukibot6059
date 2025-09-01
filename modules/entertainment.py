"""
وحدة التسلية والترفيه
Entertainment Module
"""

import logging
import random
import asyncio
from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import execute_query, get_user
from utils.helpers import format_number, format_user_mention
from utils.decorators import group_only

# رتب التسلية
ENTERTAINMENT_RANKS = [
    "هطف", "بثر", "حمار", "كلب", "كلبه", "عتوي", "عتويه", 
    "لحجي", "لحجيه", "خروف", "خفيفه", "خفيف"
]

# ردود التسلية
ENTERTAINMENT_RESPONSES = {
    "سيارتي": [
        "🚗 لديك سيارة BMW X6 فخمة!",
        "🚙 سيارتك هي تويوتا كامري 2023",
        "🏎 تملك لامبورغيني أفنتادور!",
        "🚌 سيارتك هي باص نقل عام 😂",
        "🛵 لديك دراجة نارية سريعة",
        "🚲 سيارتك هي... دراجة هوائية! 😅"
    ],
    
    "منزلي": [
        "🏰 تعيش في قصر فخم!",
        "🏠 منزلك جميل ومرتب",
        "🏘 لديك فيلا كبيرة",
        "🏚 منزلك... كوخ صغير 😂",
        "🏨 تعيش في فندق 5 نجوم!",
        "⛺ منزلك خيمة في الصحراء! 😄"
    ],
    
    "عمري": [
        f"🎂 عمرك {random.randint(18, 80)} سنة",
        f"👶 عمرك {random.randint(5, 17)} سنة (صغير!)",
        f"👴 عمرك {random.randint(60, 100)} سنة (كبير!)",
        f"🎈 عمرك {random.randint(20, 35)} سنة (شباب)"
    ],
    
    "طولي": [
        f"📏 طولك {random.randint(160, 190)} سم",
        f"📐 طولك {random.randint(140, 159)} سم (قصير)",
        f"📏 طولك {random.randint(190, 220)} سم (طويل!)",
        f"📏 طولك مثالي: {random.randint(170, 180)} سم"
    ],
    
    "وزني": [
        f"⚖️ وزنك {random.randint(60, 90)} كيلو",
        f"⚖️ وزنك {random.randint(40, 59)} كيلو (نحيف)",
        f"⚖️ وزنك {random.randint(90, 150)} كيلو (ثقيل!)",
        f"⚖️ وزنك مثالي: {random.randint(65, 80)} كيلو"
    ]
}

LOVE_RESPONSES = [
    "💕 نعم أحبك كثيراً!",
    "❤️ بالطبع أحبك!",
    "💖 أحبك أكثر من الشوكولاتة!",
    "💔 لا... لا أحبك",
    "😐 مش متأكد صراحة",
    "🤔 ممكن... ممكن لا",
    "😍 أحبك جداً جداً!",
    "💙 أحبك كصديق فقط"
]

HATE_RESPONSES = [
    "😠 نعم أكرهك!",
    "😡 أكرهك جداً!",
    "💔 للأسف نعم",
    "😌 لا، لا أكرهك",
    "🤗 مستحيل أكرهك!",
    "😊 أحبك أكثر مما أكرهك",
    "😤 أكرهك أحياناً فقط",
    "🙄 لا أكرهك ولا أحبك"
]

# رسائل رقص العرس 💃🕺
WEDDING_DANCE_MESSAGES = [
    "💃 *ترقص بحماس وسط الجمهور*\n🎵 الجميع يصفق لها!",
    "🕺 *يرقص رقصة شعبية تراثية*\n🎉 الحضور ينضم للرقص!", 
    "👫 *يرقصان معاً رقصة رومانسية*\n💕 منظر خلاب يسحر القلوب!",
    "🎭 *ترقص رقصة شرقية مذهلة*\n✨ الجميع مبهور بجمال الحركات!",
    "🎪 *يرقص رقصة بهلوانية مدهشة*\n🤹 الجميع يهتف ويصفق بقوة!",
    "💫 *ترقص كالفراشة بخفة ورشاقة*\n🦋 حركات شاعرية تأسر الأنظار!",
    "🔥 *يرقص رقصة حماسية مليئة بالطاقة*\n⚡ الجميع يشعر بالإثارة والحماس!",
    "🌟 *ترقص مع الأطفال رقصة مرحة*\n👶 ضحكات الأطفال تملأ المكان!",
    "🎨 *يرقص رقصة فنية معبرة*\n🖼️ كل حركة تحكي قصة جميلة!",
    "🎁 *ترقص وتوزع الحلوى على الحضور*\n🍬 فرحة مضاعفة للجميع!"
]

# إطارات الحركة المتقدمة للرسائل المتحركة الهستيرية 🎬
ANIMATED_DANCE_FRAMES = {
    # راقص متحرك بسيط
    "moving_dancer": [
        "    🕺     ",
        "   🕺      ",
        "  🕺       ",
        " 🕺        ",
        "🕺         ",
        " 🕺        ",
        "  🕺       ",
        "   🕺      ",
        "    🕺     "
    ],
    
    # رقصة دوارة
    "spinning_dancer": [
        "🕺",
        "🤸‍♂️",
        "🕺",
        "🤸‍♀️"
    ],
    
    # رقصة جماعية
    "group_dance": [
        "💃   🕺   💃",
        " 💃 🕺 💃 ",
        "  💃🕺💃  ",
        " 💃 🕺 💃 ",
        "💃   🕺   💃"
    ],
    
    # موكب ملكي
    "royal_procession": [
        "👑     🏰     👑",
        " 👑   🏰   👑 ",
        "  👑 🏰 👑  ",
        "   👑🏰👑   ",
        "  👑 🏰 👑  ",
        " 👑   🏰   👑 ",
        "👑     🏰     👑"
    ],
    
    # موجة احتفال
    "celebration_wave": [
        "🎉🎊🎉🎊🎉",
        "🎊🎉🎊🎉🎊",
        "🎉🎊🎉🎊🎉",
        "🎊🎉🎊🎉🎊"
    ],
    
    # شخصيات مضحكة معقدة مع رؤوس ايموجي وأجسام نصية
    "crazy_dancers": [
        "  😂    🤪    😵‍💫    🥳    🤡  \n /|\\   \\|/    \\o/   /|\\   <--| \n / \\   | |     |   / | \\   /\\  \nHAHA   LOL!   WOOO  PARTY CRAZY",
        "  🤡    😂    🥳    😵‍💫    🤪  \n<--|   /|\\   / | \\   \\o/   \\|/ \n /\\    / \\   /   \\    |    | | \nCRAZY  HAHA  PARTY  WOOO  LOL!",
        "  🥳    🤡    😂    🤪    😵‍💫  \n/ | \\  <--|   /|\\   \\|/    \\o/ \n/   \\   /\\    / \\   | |     |  \nPARTY CRAZY  HAHA   LOL!   WOOO",
        "  😵‍💫    🥳    🤡    😂    🤪  \n \\o/   / | \\  <--|   /|\\   \\|/ \n  |   /   \\   /\\    / \\   | | \nWOOO  PARTY CRAZY  HAHA   LOL!",
        "  🤪    😵‍💫    🥳    🤡    😂  \n \\|/    \\o/   / | \\  <--|   /|\\ \n | |     |   /   \\   /\\    / \\ \nLOL!   WOOO  PARTY CRAZY  HAHA"
    ],
    
    # راقصين هستيريين معقدين بحركات جنونية
    "hysterical_dance": [
        "😂🤪😵‍💫🥳🤡😁🥴😜🤩🤯\n|||/|||\\|||<|||>|||/|||\\|||/|||>|||\n| | | | | | | | | | | | | | | | | | | |\nHAHA LOL WOOO PARTY CRAZY YAY SILLY WILD COOL BOOM",
        "🤯🤩😜🥴😁🤡🥳😵‍💫🤪😂\n\\|||>|||/|||\\|||<|||>|||/|||\\|||/|||\n| | | | | | | | | | | | | | | | | | | |\nBOOM COOL WILD SILLY YAY CRAZY PARTY WOOO LOL HAHA",
        "🥳😂🤯🤪🤩😜😁🥴🤡😵‍💫\n<|||>|||\\|||/|||>|||/|||\\|||<|||>|||\n| | | | | | | | | | | | | | | | | | | |\nPARTY HAHA BOOM LOL COOL WILD YAY SILLY CRAZY WOOO",
        "😜🥳🤯😂🤩😁🤪🥴🤡😵‍💫\n|||/|||<|||>|||\\|||/|||>|||/|||\\|||<\n| | | | | | | | | | | | | | | | | | | |\nWILD PARTY BOOM HAHA COOL YAY LOL SILLY CRAZY WOOO"
    ],
    
    # بالي راقص معقد ومتطور
    "ballet_dancer": [
        "👸     👸     👸     👸     👸\n/|\\   \\|/   --|--   /|\\   /|\\\n| |    / \\    / \\   / | \\  /   \\\nGRACE  BEAUTY ELEGANT DIVINE ROYAL",
        "👸     👸     👸     👸     👸\n\\|/   --|--   /|\\   /   \\  \\|/\n/ \\    / \\   / | \\  /     \\  | |\nBEAUTY ELEGANT DIVINE ROYAL  GRACE",
        "👸     👸     👸     👸     👸\n--|--   /|\\   /   \\  \\|/   /|\\\n/ \\   / | \\  /     \\  | |   / \\\nELEGANT DIVINE ROYAL  GRACE  BEAUTY",
        "👸     👸     👸     👸     👸\n/|\\   /   \\  \\|/   /|\\   --|--\n/ | \\  /     \\  | |   / \\   / \\\nDIVINE ROYAL  GRACE  BEAUTY ELEGANT"
    ],
    
    # راقص بريك دانس
    "breakdancer": [
        "  🕺  \n /|\\ \n / \\ \n TOP ",
        "  🕺  \n<-|->\\n /\\ \nSPIN",
        "  🕺  \n \\|/ \n  |  \nFREEZE",
        "  🕺  \n/|||\\n/ | \\nFLOW"
    ],
    
    # رقصة الديسكو المجنونة والمعقدة
    "disco_fever": [
        "✨🕺✨🌟💃🌟💫🕺💫⭐💃⭐\n DISCO BOOGIE FUNKY GROOVY \n FEVER TIME MOVES VIBES \n🎵🎶🎵🎶🎵🎶🎵🎶🎵🎶",
        "⭐💃⭐💫🕺💫🌟💃🌟✨🕺✨\n GROOVY FUNKY BOOGIE DISCO \n VIBES MOVES TIME FEVER \n🎶🎵🎶🎵🎶🎵🎶🎵🎶🎵",
        "🌟💃🌟✨🕺✨⭐💃⭐💫🕺💫\n BOOGIE DISCO GROOVY FUNKY \n TIME FEVER VIBES MOVES \n🎵🎶🎵🎶🎵🎶🎵🎶🎵🎶",
        "💫🕺💫⭐💃⭐✨🕺✨🌟💃🌟\n FUNKY GROOVY DISCO BOOGIE \n MOVES VIBES FEVER TIME \n🎶🎵🎶🎵🎶🎵🎶🎵🎶🎵"
    ],
    
    # حيوانات ترقص بشكل معقد ومضحك
    "animal_party": [
        "🐵🐸🐱🐶🐷🐰🐯🐻🐼🦁🐺🐨\n|||||||||||||||||||||||||||\n| | | | | | | | | | | | | | | | | | | | | | | |\nOOK HOP MEW WOOF OINK HOP ROAR GROWL CHOMP ROAR HOWL CHILL",
        "🐨🐺🦁🐼🐻🐯🐰🐷🐶🐱🐸🐵\n|||||||||||||||||||||||||||\n| | | | | | | | | | | | | | | | | | | | | | | |\nCHILL HOWL ROAR CHOMP GROWL ROAR HOP OINK WOOF MEW HOP OOK",
        "🐸🐵🐺🐨🦁🐼🐻🐯🐰🐷🐶🐱\n|||||||||||||||||||||||||||\n| | | | | | | | | | | | | | | | | | | | | | | |\nHOP OOK HOWL CHILL ROAR CHOMP GROWL ROAR HOP OINK WOOF MEW",
        "🐱🐶🐷🐰🐯🐻🐼🦁🐺🐨🐵🐸\n|||||||||||||||||||||||||||\n| | | | | | | | | | | | | | | | | | | | | | | |\nMEW WOOF OINK HOP ROAR GROWL CHOMP ROAR HOWL CHILL OOK HOP"
    ],
    
    # رقصة الروبوت
    "robot_dance": [
        "🤖\n█▌█\n███\nBEEP",
        "🤖\n▐█▌\n███\nBOOP",
        "🤖\n█▌█\n▐█▌\nWHIR",
        "🤖\n▌█▐\n███\nBZZT"
    ],
    
    # مهرجان الألوان المعقد والضخم
    "color_festival": [
        "🌈🎨🌈🎭🌟🎭🎪💫🎪🎨🌈🎨\n COLOR PAINT RAINBOW BRIGHT SPLASH DANCE PARTY VIBES \n🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊",
        "🎨🌈🎨🎪💫🎪🎭🌟🎭🌈🎨🌈\n BRIGHT RAINBOW PARTY COLOR VIBES DANCE PAINT SPLASH \n🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉",
        "🎪💫🎪🌈🎨🌈🎨🌈🎨🎭🌟🎭\n PARTY COLOR BRIGHT PAINT RAINBOW SPLASH VIBES DANCE \n🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊",
        "🎭🌟🎭🎨🌈🎨🎪💫🎪🌈🎨🌈\n DANCE BRIGHT VIBES PARTY COLOR SPLASH PAINT RAINBOW \n🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉🎊🎉"
    ],
    
    # رقصات جديدة معقدة ومضحكة
    "super_complex_dance": [
        "🤪😂🥳🤡😵‍💫🥴😜🤩🤯😋\n/|||\\<>|||/|||\\><|||/|||\\<>|||/|||\\><|||/|||\\\n| | || || | | || || | | || || | | || || | | ||\nWOOHOO CRAZY PARTY SILLY DIZZY WILD FUNNY COOL MEGA AWESOME",
        "😋🤯🤩😜🥴😵‍💫🤡🥳😂🤪\n><|||/|||\\<>|||/|||\\><|||/|||\\<>|||/|||\\><|||/\n|| | | || || | | || || | | || || | | || || | |\nAWESOME MEGA COOL FUNNY WILD DIZZY SILLY PARTY CRAZY WOOHOO",
        "🥳🤪😋🤯😜🤩😵‍💫🥴🤡😂\n|||\\><|||/|||\\<>|||/|||\\><|||/|||\\<>|||/|||\\><\n| || || | | || || | | || || | | || || | | || |\nPARTY WOOHOO AWESOME MEGA FUNNY COOL DIZZY WILD SILLY CRAZY",
        "😂🤡🥴😵‍💫🤩😜🤯🤪🥳😋\n/|||\\<>|||/|||\\><|||/|||\\<>|||/|||\\><|||/|||\\\n|| | | || || | | || || | | || || | | || || | |\nCRAZY SILLY WILD DIZZY COOL FUNNY MEGA WOOHOO PARTY AWESOME"
    ],
    
    "mega_dance_explosion": [
        "🔥💥🎆🎉🎊🎉🎆💥🔥\n🕺💃🕺💃🕺💃🕺💃🕺\n<>||<>||<>||<>||<>||<>||<>||<>||<>\nEXPLOSION OF DANCE AND FUN!!!",
        "🎆🔥💥🎉🎊🎉💥🔥🎆\n💃🕺💃🕺💃🕺💃🕺💃\n||<>||<>||<>||<>||<>||<>||<>||<>||\nMASSIVE PARTY EXPLOSION TIME!!!",
        "💥🎆🔥🎊🎉🎊🔥🎆💥\n🕺💃🕺💃🕺💃🕺💃🕺\n<>||<>||<>||<>||<>||<>||<>||<>||<>\nULTRAA MEGA DANCE MADNESS!!!"
    ],
    
    "royal_mega_procession": [
        "👑🏰👑🏰👑🏰👑🏰👑\n⚜️✨⚜️✨⚜️✨⚜️✨⚜️\n👸🤴👸🤴👸🤴👸🤴👸\nROYAL MEGA ULTIMATE PROCESSION",
        "🏰👑🏰👑🏰👑🏰👑🏰\n✨⚜️✨⚜️✨⚜️✨⚜️✨\n🤴👸🤴👸🤴👸🤴👸🤴\nULTIMATE ROYAL MEGA PROCESSION",
        "👑🏰👑🏰👑🏰👑🏰👑\n⚜️✨⚜️✨⚜️✨⚜️✨⚜️\n👸🤴👸🤴👸🤴👸🤴👸\nMEGA ULTIMATE ROYAL PROCESSION"
    ]
}

# رسائل الاحتفال التلقائي للحاضرين 🎊
AUTO_CELEBRATION_MESSAGES = [
    "🎉 {name} ينضم للاحتفال!",
    "💃 {name} يرقص بفرح شديد!",
    "🕺 {name} يؤدي رقصة رائعة!",
    "🎊 {name} يصفق ويهتف بحماس!",
    "🌟 {name} يضيء الحفل بحضوره!",
    "✨ {name} يشارك الفرحة العامة!",
    "🎭 {name} يرقص كالمحترفين!",
    "💫 {name} يرقص مع الجميع!"
]

# رسائل مراسم العرس الملكي 👑
ROYAL_WEDDING_CEREMONIES = [
    "👑 **مراسم التتويج الملكية:**\n🎭 العرسان يرتديان التيجان الذهبية\n💎 مرصعة بأثمن الجواهر",
    "🏰 **موكب العرس الملكي:**\n🐎 العربات المزينة بالورود الذهبية\n🎺 عازفو البوق الملكي يعلنون الفرح",
    "⚔️ **حرس الشرف الملكي:**\n🛡️ 100 فارس بالخيول البيضاء\n🎖️ يرفعون السيوف تحية للعرسان",
    "🕯️ **إضاءة الشموع المقدسة:**\n✨ 1000 شمعة ذهبية تضيء القصر\n🌟 رمز للحب الأبدي والخلود",
    "🎵 **الأوركسترا الملكية:**\n🎼 50 عازف من أشهر موسيقيي المملكة\n🎹 سيمفونية الحب الخالدة",
    "🌹 **مطر الورود الملكي:**\n🌺 آلاف البتلات الذهبية من السماء\n💫 منظر خيالي يحبس الأنفاس"
]

# هدايا العرس الملكي 🎁
ROYAL_WEDDING_GIFTS = [
    {"name": "تاج الملكة الماسي", "value": 1000000, "description": "تاج مرصع بـ 500 ماسة نادرة"},
    {"name": "عقد اللؤلؤ الملكي", "value": 750000, "description": "عقد من اللؤلؤ الطبيعي النادر"},
    {"name": "خاتم الحب الأبدي", "value": 500000, "description": "خاتم ذهبي مرصع بالياقوت الأزرق"},
    {"name": "صولجان الملك الذهبي", "value": 800000, "description": "صولجان من الذهب الخالص مع الزمرد"},
    {"name": "عرش العرسان الملكي", "value": 2000000, "description": "عرش مصنوع من خشب الأبنوس والذهب"},
    {"name": "مفاتيح القصر الصيفي", "value": 5000000, "description": "قصر صيفي مطل على البحر"},
]

# رسائل احتفالية للعرس العادي 🎉
WEDDING_CELEBRATION_MESSAGES = [
    "🎊 الحمد لله الذي أتم لكم هذا الحب الجميل!",
    "💒 بارك الله لكما وبارك عليكما وجمع بينكما في خير!",
    "🌹 ألف مبروك! عقبال المولود الجديد إن شاء الله!",
    "🎭 فرحة القلب وسعادة الروح... كل عام وأنتم بخير!",
    "🎯 الحب انتصر والقلوب فرحت... مبروك للعرسان!",
    "💝 هدية الله لكما بعضكما البعض... دوموا بخير!",
    "🎪 يوم تاريخي في حياتكما... بداية رحلة العمر!",
    "🎈 بالرفاء والبنين... وعقبال الفرحة الكبيرة!",
]


async def handle_entertainment_rank(message: Message, rank: str, action: str):
    """معالج رتب التسلية"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص")
            return

        if action == "رفع":
            # رفع رتبة تسلية
            await execute_query(
                "INSERT OR REPLACE INTO entertainment_ranks (user_id, chat_id, rank_type, given_by, given_at) VALUES (?, ?, ?, ?, ?)",
                (target_user.id, message.chat.id, rank, message.from_user.id, datetime.now().isoformat())
            )
            
            await message.reply(f"😂 تم رفع {format_user_mention(target_user)} إلى رتبة {rank}")
            
        elif action == "تنزيل":
            # تنزيل رتبة تسلية
            result = await execute_query(
                "DELETE FROM entertainment_ranks WHERE user_id = ? AND chat_id = ? AND rank_type = ?",
                (target_user.id, message.chat.id, rank)
            )
            
            if result:
                await message.reply(f"✅ تم تنزيل {format_user_mention(target_user)} من رتبة {rank}")
            else:
                await message.reply(f"❌ {format_user_mention(target_user)} ليس لديه رتبة {rank}")

    except Exception as e:
        logging.error(f"خطأ في رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def show_entertainment_ranks(message: Message, rank_type: str = None):
    """عرض قوائم رتب التسلية"""
    try:
        if rank_type:
            # عرض رتبة محددة
            ranks = await execute_query(
                "SELECT user_id FROM entertainment_ranks WHERE chat_id = ? AND rank_type = ?",
                (message.chat.id, rank_type),
                fetch_all=True
            )
            
            if not ranks:
                await message.reply(f"📝 لا يوجد {rank_type} في المجموعة")
                return

            rank_text = f"😂 **قائمة {rank_type}:**\n\n"
            
            for i, rank in enumerate(ranks, 1):
                user_id = rank['user_id'] if isinstance(rank, dict) else rank[0]
                user = await get_user(user_id)
                if user:
                    user_mention = f"@{user['username']}" if user.get('username') else f"#{user_id}"
                    rank_text += f"{i}. {user_mention}\n"

            await message.reply(rank_text)
        
        else:
            # عرض جميع رتب التسلية
            await message.reply("😄 **رتب التسلية المتاحة:**\n" + 
                              "\n".join([f"• {rank}" for rank in ENTERTAINMENT_RANKS]))

    except Exception as e:
        logging.error(f"خطأ في عرض رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتب")


async def handle_custom_rank(message: Message, custom_rank: str):
    """معالج الرتب المخصصة"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص")
            return

        # رفع رتبة مخصصة
        await execute_query(
            "INSERT OR REPLACE INTO entertainment_ranks (user_id, chat_id, rank_type, given_by, given_at) VALUES (?, ?, ?, ?, ?)",
            (target_user.id, message.chat.id, custom_rank, message.from_user.id, datetime.now().isoformat())
        )
        
        await message.reply(f"🎭 تم رفع {format_user_mention(target_user)} إلى رتبة {custom_rank}")

    except Exception as e:
        logging.error(f"خطأ في الرتبة المخصصة: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def handle_marriage(message: Message, action: str):
    """معالج الزواج والطلاق"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        user_id = message.from_user.id
        
        # فحص إذا كان المستخدم من العائلة الملكية
        from config.hierarchy import is_royal, is_king, is_queen
        user_is_royal = is_royal(user_id)
        
        if action == "زواج":
            # معالجة خاصة للعائلة الملكية
            if user_is_royal:
                # الزواج الملكي مجاني تماماً!
                dowry_amount = 0
                royal_title = "الملك" if is_king(user_id) else "الملكة"
                await message.reply(
                    f"👑 **زواج ملكي مجاني!**\n\n"
                    f"🎭 {royal_title} لا يدفع مهراً - هذا شرف للطرف الآخر!\n"
                    f"💎 الزواج الملكي مجاني تماماً ومليء بالامتيازات\n"
                    f"🏰 ستحصل على حفل زفاف أسطوري!"
                )
            else:
                # تحليل الرسالة للحصول على المهر للمستخدمين العاديين
                text_parts = message.text.split()
                if len(text_parts) < 2:
                    await message.reply(
                        "❌ **طريقة الزواج الصحيحة:**\n\n"
                        "1️⃣ رد على رسالة من تريد/ين الزواج منه/ها\n"
                        "2️⃣ اكتب: زواج [مبلغ المهر]\n\n"
                        "**مثال:** زواج 5000\n"
                        "💰 المهر يجب أن يكون 1000 أو أكثر"
                    )
                    return
                
                try:
                    dowry_amount = int(text_parts[1])
                except ValueError:
                    await message.reply("❌ يرجى كتابة مبلغ مهر صحيح\n\n**مثال:** زواج 5000")
                    return
                
                if dowry_amount < 1000:
                    await message.reply("❌ مبلغ المهر يجب أن يكون 1,000 أو أكثر")
                    return
            
            target_user = None
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
            
            if not target_user:
                await message.reply("❌ يرجى الرد على رسالة الشخص الذي تريد الزواج منه")
                return

            if target_user.id == user_id:
                await message.reply("😅 لا يمكنك الزواج من نفسك!")
                return

            # التحقق من الزواج الحالي للطرفين
            current_marriage_proposer = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            current_marriage_target = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (target_user.id, target_user.id, message.chat.id),
                fetch_one=True
            )
            
            if current_marriage_proposer:
                await message.reply("💔 أنت متزوج بالفعل! اطلق أولاً")
                return
                
            if current_marriage_target:
                target_name = target_user.first_name or "الشخص"
                await message.reply(f"💔 {target_name} متزوج بالفعل!")
                return

            # التحقق من رصيد المتقدم للزواج (إذا لم يكن من العائلة الملكية)
            from database.operations import get_user
            proposer = await get_user(user_id)
            if not proposer:
                await message.reply("❌ يرجى إنشاء حساب بنكي أولاً")
                return
            
            # العائلة الملكية لا تحتاج لفحص الرصيد
            if not user_is_royal and proposer['balance'] < dowry_amount:
                from utils.helpers import format_number
                await message.reply(
                    f"❌ ليس لديك رصيد كافٍ للمهر!\n"
                    f"💰 رصيدك: {format_number(proposer['balance'])}$\n"
                    f"💎 المهر المطلوب: {format_number(dowry_amount)}$"
                )
                return

            # إنشاء طلب زواج في قاعدة البيانات
            await execute_query(
                "INSERT INTO marriage_proposals (proposer_id, target_id, chat_id, dowry_amount, proposed_at, status) VALUES (?, ?, ?, ?, ?, 'pending')",
                (user_id, target_user.id, message.chat.id, dowry_amount, datetime.now().isoformat())
            )
            
            proposer_name = message.from_user.first_name or "شخص"
            target_name = target_user.first_name or "شخص"
            
            from utils.helpers import format_number
            
            # رسالة طلب زواج مختلفة للعائلة الملكية
            if user_is_royal:
                royal_title = "الملك" if is_king(user_id) else "الملكة"
                target_is_royal = is_royal(target_user.id)
                target_royal_title = ""
                if target_is_royal:
                    target_royal_title = "الملك" if is_king(target_user.id) else "الملكة"
                
                # اختيار هدية ملكية عشوائية
                royal_gift = random.choice(ROYAL_WEDDING_GIFTS)
                ceremony = random.choice(ROYAL_WEDDING_CEREMONIES)
                
                marriage_message = (
                    f"👑 **طلب زواج ملكي أسطوري خالد!** 👑\n\n"
                    f"🎭 من: {royal_title} {proposer_name}\n"
                    f"🎭 إلى: {target_royal_title + ' ' if target_royal_title else ''}{target_name}\n"
                    f"💎 المهر: مجاني تماماً - شرف ملكي عظيم!\n"
                    f"🏰 نوع الزواج: **زواج ملكي أسطوري**\n\n"
                    f"🎁 **الهدايا الملكية المضمونة:**\n"
                    f"✨ {royal_gift['name']}\n"
                    f"💰 قيمة: {format_number(royal_gift['value'])}$\n"
                    f"📝 {royal_gift['description']}\n\n"
                    f"{ceremony}\n\n"
                    f"⏰ **في انتظار الموافقة الملكية من {target_name}**\n"
                    f"👑 يجب على {target_name} الرد بكلمة **موافقة** للحصول على الشرف الملكي الأبدي\n"
                    f"🚫 أو **رفض** لتفويت هذا الشرف العظيم والهدايا الثمينة"
                )
            else:
                marriage_message = (
                    f"💍 **طلب زواج جديد!**\n\n"
                    f"👤 من: {proposer_name}\n"
                    f"👤 إلى: {target_name}\n"
                    f"💰 المهر: {format_number(dowry_amount)}$\n\n"
                    f"⏰ **في انتظار موافقة {target_name}**\n"
                    f"📝 يجب على {target_name} الرد بكلمة **موافقة** للقبول\n"
                    f"🚫 أو **رفض** لرفض الطلب"
                )
            
            await message.reply(marriage_message)
        
        elif action == "طلاق" or action == "خلع":
            # البحث عن الزواج
            marriage = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            if not marriage:
                await message.reply("😔 أنت لست متزوجاً!")
                return

            # تحديد الطرفين - الآن نضمن أن نحصل على المعرفات بشكل صحيح
            if isinstance(marriage, dict):
                user1_id = marriage['user1_id']
                user2_id = marriage['user2_id']
                marriage_id = marriage['id']
            else:
                # إذا كانت النتيجة tuple أو list
                marriage_id = marriage[0]
                user1_id = marriage[1]
                user2_id = marriage[2]
            
            from database.operations import get_user, update_user_balance, add_transaction
            
            # جلب بيانات الطرفين
            user1 = await get_user(user1_id)
            user2 = await get_user(user2_id)
            
            if not user1 or not user2:
                await message.reply("❌ خطأ في الحصول على بيانات الأطراف")
                return
            
            # التحقق من أن كلا الطرفين لديهما 500 على الأقل
            divorce_fee = 500
            if user1['balance'] < divorce_fee:
                user1_name = user1.get('first_name', f'المستخدم #{user1_id}')
                await message.reply(f"❌ {user1_name} لا يملك {divorce_fee}$ للطلاق")
                return
                
            if user2['balance'] < divorce_fee:
                user2_name = user2.get('first_name', f'المستخدم #{user2_id}')
                await message.reply(f"❌ {user2_name} لا يملك {divorce_fee}$ للطلاق")
                return
            
            # معرف الشيخ
            JUDGE_ID = 7155814194
            JUDGE_USERNAME = "@Hacker20263"
            JUDGE_NAME = "ردفان"
            
            # خصم 500 من كل طرف
            new_user1_balance = user1['balance'] - divorce_fee
            new_user2_balance = user2['balance'] - divorce_fee
            
            await update_user_balance(user1_id, new_user1_balance)
            await update_user_balance(user2_id, new_user2_balance)
            
            # إعطاء الشيخ 1000 (500+500)
            judge = await get_user(JUDGE_ID)
            if judge:
                new_judge_balance = judge['balance'] + (divorce_fee * 2)
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي
                await add_transaction(
                    JUDGE_ID,
                    f"أتعاب طلاق {user1.get('first_name', 'مستخدم')} و {user2.get('first_name', 'مستخدم')}",
                    divorce_fee * 2,
                    "divorce_fee"
                )
            
            # إضافة المعاملات للطرفين
            divorce_type = "طلاق" if action == "طلاق" else "خلع"
            await add_transaction(
                user1_id,
                f"رسوم {divorce_type}",
                -divorce_fee,
                "divorce_fee"
            )
            await add_transaction(
                user2_id,
                f"رسوم {divorce_type}",
                -divorce_fee,
                "divorce_fee"
            )

            # حذف الزواج
            await execute_query(
                "DELETE FROM entertainment_marriages WHERE id = ?",
                (marriage_id,)
            )
            
            from utils.helpers import format_number
            divorce_message = (
                f"💔 **تم {divorce_type} بنجاح!**\n\n"
                f"👤 الطرف الأول: {user1.get('first_name', 'مستخدم')}\n"
                f"👤 الطرف الثاني: {user2.get('first_name', 'مستخدم')}\n"
                f"💰 رسوم {divorce_type}: {format_number(divorce_fee)}$ من كل طرف\n"
                f"⚖️ أتعاب الشيخ: {format_number(divorce_fee * 2)}$\n\n"
                f"🕌 **تم الطلاق بحضور فضيلة الشيخ:**\n"
                f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n\n"
                f"😢 وداعاً أيها الحب!"
            )
            
            await message.reply(divorce_message)
            
            # إشعار القاضي إذا كان متاح
            if judge:
                try:
                    await message.bot.send_message(
                        JUDGE_ID,
                        f"⚖️ **تم {divorce_type} جديد بحضرتكم**\n\n"
                        f"👤 الطرف الأول: {user1.get('first_name', 'مستخدم')}\n"
                        f"👤 الطرف الثاني: {user2.get('first_name', 'مستخدم')}\n"
                        f"💰 الأتعاب المستحقة: {format_number(divorce_fee * 2)}$\n"
                        f"💳 رصيدكم الجديد: {format_number(new_judge_balance)}$\n\n"
                        f"🌟 جزاكم الله خيراً على خدمة المسلمين"
                    )
                except:
                    pass  # إذا فشل إرسال الإشعار

    except Exception as e:
        logging.error(f"خطأ في الزواج/الطلاق: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def show_marriage_status(message: Message):
    """عرض حالة الزواج"""
    try:
        user_id = message.from_user.id
        
        marriage = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
            (user_id, user_id, message.chat.id),
            fetch_one=True
        )
        
        # تسجيل لمراقبة حالة الزواج
        logging.info(f"البحث عن زواج للمستخدم {user_id} في المجموعة {message.chat.id}: {marriage}")
        
        if not marriage:
            await message.reply("💔 أنت أعزب/عزباء حالياً")
            return

        # تحديد الشريك
        if isinstance(marriage, dict):
            partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        else:
            # إذا كانت النتيجة tuple أو list
            partner_id = marriage[2] if marriage[1] == user_id else marriage[1]
        
        partner = await get_user(partner_id)
        
        if partner:
            partner_name = partner.get('first_name', f'المستخدم #{partner_id}')
            married_date = marriage.get('married_at', '') if isinstance(marriage, dict) else marriage[6] if len(marriage) > 6 else ''
            dowry_amount = marriage.get('dowry_amount', 0) if isinstance(marriage, dict) else marriage[4] if len(marriage) > 4 else 0
            judge_commission = marriage.get('judge_commission', 0) if isinstance(marriage, dict) else marriage[5] if len(marriage) > 5 else 0
            
            marriage_info = (
                f"💕 **حالة الزواج:**\n"
                f"💍 الشريك: {partner_name}\n"
                f"📅 تاريخ الزواج: {married_date[:10] if married_date else 'غير محدد'}\n"
            )
            
            if dowry_amount > 0:
                from utils.helpers import format_number
                marriage_info += f"💎 المهر: {format_number(dowry_amount)}$\n"
            
            if judge_commission > 0:
                from utils.helpers import format_number
                marriage_info += f"⚖️ أتعاب الشيخ: {format_number(judge_commission)}$\n"
                marriage_info += f"🕌 كتب العقد: الشيخ المحترم ردفان @Hacker20263\n"
            
            marriage_info += f"❤️ دام الحب!"
            
            await message.reply(marriage_info)
        else:
            await message.reply("💔 لم أتمكن من العثور على معلومات الشريك")

    except Exception as e:
        logging.error(f"خطأ في عرض حالة الزواج: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الحالة")


async def handle_marriage_response(message: Message, response_type: str):
    """معالج موافقة أو رفض الزواج"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            return

        user_id = message.from_user.id
        
        # البحث عن طلب زواج معلق
        proposal = await execute_query(
            "SELECT * FROM marriage_proposals WHERE target_id = ? AND chat_id = ? AND status = 'pending' ORDER BY proposed_at DESC LIMIT 1",
            (user_id, message.chat.id),
            fetch_one=True
        )
        
        if not proposal:
            await message.reply("❌ لا يوجد طلب زواج معلق لك")
            return
        
        proposer_id = proposal['proposer_id'] if isinstance(proposal, dict) else proposal[1]
        dowry_amount = proposal['dowry_amount'] if isinstance(proposal, dict) else proposal[4]
        proposal_id = proposal['id'] if isinstance(proposal, dict) else proposal[0]
        
        from database.operations import get_user
        proposer = await get_user(proposer_id)
        target = await get_user(user_id)
        
        if not proposer or not target:
            await message.reply("❌ خطأ في الحصول على بيانات المستخدمين")
            return
        
        proposer_name = proposer.get('first_name', f'المستخدم #{proposer_id}')
        target_name = target.get('first_name', f'المستخدم #{user_id}')
        
        if response_type == "موافقة":
            # فحص إذا كان أحد الأطراف من العائلة الملكية
            from config.hierarchy import is_royal, is_king, is_queen
            proposer_is_royal = is_royal(proposer_id)
            target_is_royal = is_royal(user_id)
            
            # التحقق من أن المتقدم لا يزال لديه الرصيد (إلا إذا كان ملكياً)
            if not proposer_is_royal and proposer['balance'] < dowry_amount:
                await execute_query(
                    "UPDATE marriage_proposals SET status = 'cancelled' WHERE id = ?",
                    (proposal_id,)
                )
                from utils.helpers import format_number
                await message.reply(
                    f"❌ **تم إلغاء الطلب!**\n"
                    f"السبب: {proposer_name} لا يملك رصيد كافٍ للمهر\n"
                    f"💰 المهر المطلوب: {format_number(dowry_amount)}$"
                )
                return
            
            # الآن نحتاج للقاضي - معرف القاضي المحدد (الشيخ ردفان)
            JUDGE_ID = 7155814194
            JUDGE_USERNAME = "@Hacker20263"
            JUDGE_NAME = "ردفان"
            
            # معالجة مختلفة للزواج الملكي
            if proposer_is_royal or target_is_royal:
                # الزواج الملكي بدون رسوم أو عمولة
                judge_commission = 0
                total_cost = 0
                royal_wedding = True
            else:
                # حساب عمولة القاضي (بين 100-1000 حسب المهر)
                judge_commission = max(100, min(1000, int(dowry_amount * 0.05)))  # 5% من المهر
                total_cost = dowry_amount + judge_commission
                royal_wedding = False
                
                # التحقق من أن المتقدم يستطيع دفع المهر + العمولة
                if proposer['balance'] < total_cost:
                    from utils.helpers import format_number
                    await message.reply(
                        f"❌ **رصيد غير كافٍ!**\n"
                        f"💰 المهر: {format_number(dowry_amount)}$\n"
                        f"💼 عمولة القاضي: {format_number(judge_commission)}$\n"
                        f"💸 المطلوب: {format_number(total_cost)}$\n"
                        f"💰 الرصيد الحالي: {format_number(proposer['balance'])}$"
                    )
                    return
            
            # تنفيذ المعاملة المالية
            from database.operations import update_user_balance, add_transaction
            
            # معالجة مختلفة للزواج الملكي
            if royal_wedding:
                # الزواج الملكي - هدايا ملكية أسطورية فخمة
                royal_gift = 1000000  # هدية ملكية أسطورية 1 مليون!
                royal_bonus = 2000000  # مكافأة ملكية إضافية 2 مليون!
                total_royal_gift = royal_gift + royal_bonus
                
                new_proposer_balance = proposer['balance'] + total_royal_gift
                new_target_balance = target['balance'] + total_royal_gift
                await update_user_balance(proposer_id, new_proposer_balance)
                await update_user_balance(user_id, new_target_balance)
                
                # إضافة المعاملات الملكية الفخمة
                await add_transaction(
                    proposer_id,
                    "هدية زواج ملكي أسطوري",
                    royal_gift,
                    "royal_wedding_gift"
                )
                await add_transaction(
                    proposer_id,
                    "مكافأة العائلة الملكية الإمبراطورية",
                    royal_bonus,
                    "royal_wedding_bonus"
                )
                await add_transaction(
                    user_id,
                    "هدية زواج ملكي أسطوري",
                    royal_gift,
                    "royal_wedding_gift"
                )
                await add_transaction(
                    user_id,
                    "مكافأة العائلة الملكية الإمبراطورية",
                    royal_bonus,
                    "royal_wedding_bonus"
                )
            else:
                # الزواج العادي
                # خصم من المتقدم
                new_proposer_balance = proposer['balance'] - total_cost
                await update_user_balance(proposer_id, new_proposer_balance)
                
                # إعطاء المهر للعروس
                new_target_balance = target['balance'] + dowry_amount
                await update_user_balance(user_id, new_target_balance)
            
            # إعطاء العمولة للقاضي (إذا كان مسجل في البوت وليس زواج ملكي)
            judge = await get_user(JUDGE_ID)
            if judge and not royal_wedding:
                new_judge_balance = judge['balance'] + judge_commission
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي
                await add_transaction(
                    JUDGE_ID,
                    f"عمولة زواج {proposer_name} و {target_name}",
                    judge_commission,
                    "judge_commission"
                )
            elif judge and royal_wedding:
                # القاضي يحصل على هدية ملكية أسطورية فخمة
                royal_judge_gift = 10000000  # 10 مليون هدية القاضي الأعظم!
                new_judge_balance = judge['balance'] + royal_judge_gift
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي الأعظم
                await add_transaction(
                    JUDGE_ID,
                    f"هدية ملكية إمبراطورية لقاضي الزواج الملكي الأسطوري {proposer_name} و {target_name}",
                    royal_judge_gift,
                    "royal_judge_gift"
                )
            
            # إضافة المعاملات للزواج العادي فقط
            if not royal_wedding:
                await add_transaction(
                    proposer_id,
                    f"مهر زواج من {target_name}",
                    -dowry_amount,
                    "marriage_dowry"
                )
                await add_transaction(
                    proposer_id,
                    f"عمولة القاضي للزواج",
                    -judge_commission,
                    "judge_fee"
                )
                await add_transaction(
                    user_id,
                    f"مهر زواج من {proposer_name}",
                    dowry_amount,
                    "marriage_dowry"
                )
            
            # إجراء الزواج
            marriage_saved = await execute_query(
                "INSERT INTO entertainment_marriages (user1_id, user2_id, chat_id, dowry_amount, judge_commission, married_at) VALUES (?, ?, ?, ?, ?, ?)",
                (proposer_id, user_id, message.chat.id, dowry_amount, judge_commission, datetime.now().isoformat())
            )
            
            # تسجيل لوحظة حفظ الزواج
            logging.info(f"تم حفظ الزواج بين {proposer_id} و {user_id} في المجموعة {message.chat.id}: {marriage_saved}")
            
            # تحديث حالة الطلب
            await execute_query(
                "UPDATE marriage_proposals SET status = 'accepted' WHERE id = ?",
                (proposal_id,)
            )
            
            from utils.helpers import format_number
            
            # رسالة زواج مختلفة للعائلة الملكية
            if royal_wedding:
                # تحديد الألقاب الملكية
                proposer_title = "الملك" if is_king(proposer_id) else "الملكة" if is_queen(proposer_id) else "الأمير/ة"
                target_title = "الملك" if is_king(user_id) else "الملكة" if is_queen(user_id) else "الأمير/ة"
                
                # إضافة تأثيرات بصرية متحركة للزفاف الملكي
                royal_animations = [
                    "💫👑✨💎✨👑💫",
                    "🌟⚜️🏰⚜️🌟",
                    "✨💃🤴💃✨",
                    "🎭👸🎊👸🎭",
                    "💎🌟👑🌟💎"
                ]
                
                marriage_message = (
                    f"👑✨ **زفاف ملكي أسطوري إمبراطوري خالد!** ✨👑\n"
                    f"{random.choice(royal_animations)}\n\n"
                    f"🎭 **طقوس الزفاف الملكي الفخم الأسطوري:**\n"
                    f"👸 العروس الملكية: {target_title} {target_name}\n"
                    f"🤴 العريس الملكي: {proposer_title} {proposer_name}\n"
                    f"💎 المهر الملكي: مجاني - شرف ملكي إمبراطوري!\n"
                    f"🎁 الهدايا الملكية: {format_number(total_royal_gift)}$ لكل طرف\n"
                    f"👑 هدية القاضي الأعظم: {format_number(royal_judge_gift)}$\n\n"
                    f"🏰 **مراسم الزفاف الأسطوري الخالد:**\n"
                    f"🕌 **كتب العقد الملكي فضيلة الشيخ الأعظم:**\n"
                    f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n"
                    f"🎊 **إعلان لجميع الرعايا والممالك:** لقد تم الزفاف الملكي الأسطوري!\n"
                    f"🎭 **مراسم احتفالية خيالية:** موكب ملكي + هدايا للحضور + مهرجان ملكي\n"
                    f"{random.choice(royal_animations)}\n\n"
                    f"✨ **بارك الله في العائلة الملكية الجديدة!** ✨\n"
                    f"👑 عاشت العائلة الملكية الإمبراطورية! 👑\n"
                    f"🌟 دام الحب الملكي والهناء الأبدي! 🌟\n"
                    f"🏰 **هذا زفاف سيخلد في تاريخ الممالك!** 🏰\n"
                    f"{random.choice(royal_animations)}"
                )
            else:
                marriage_message = (
                    f"💒 **مبروك الزواج!** 🎉\n\n"
                    f"👰 العروس: {target_name}\n"
                    f"🤵 العريس: {proposer_name}\n"
                    f"💎 المهر: {format_number(dowry_amount)}$\n"
                    f"⚖️ أتعاب الشيخ: {format_number(judge_commission)}$\n\n"
                    f"🕌 **شهد على العقد وكتبه فضيلة الشيخ المحترم:**\n"
                    f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n"
                    f"🌟 بارك الله للعروسين وجمع بينهما في خير\n\n"
                    f"💕 ألف مبروك للعروسين!\n"
                    f"🌹 دام الحب والهناء!"
                )
            
            await message.reply(marriage_message)
            
            # تفعيل الاحتفال التلقائي مع الرسائل المتحركة
            try:
                await asyncio.sleep(1)  # انتظار قصير قبل بدء الاحتفال
                await start_wedding_celebration_with_animation(
                    message.bot, 
                    message.chat.id, 
                    marriage_saved, 
                    royal_wedding
                )
            except Exception as celebration_error:
                logging.error(f"خطأ في الاحتفال التلقائي: {celebration_error}")
            
            # إشعار القاضي إذا كان متاح
            if judge:
                try:
                    if royal_wedding:
                        await message.bot.send_message(
                            JUDGE_ID,
                            f"👑💫 **مبروك فضيلة الشيخ الأعظم الإمبراطوري** 💫👑\n"
                            f"✨💎🌟💎✨\n\n"
                            f"🎭 تم إتمام زفاف ملكي أسطوري خالد في التاريخ بحضرتكم المباركة!\n"
                            f"👸 العروس الملكية: {target_name}\n"
                            f"🤴 العريس الملكي: {proposer_name}\n"
                            f"👑 الهدية الملكية الإمبراطورية: {format_number(royal_judge_gift)}$\n"
                            f"💳 رصيدكم الملكي الأسطوري الجديد: {format_number(new_judge_balance)}$\n\n"
                            f"🏰 **شرف تاريخي:** أنتم قاضي الزفاف الملكي الأعظم!\n"
                            f"⚜️ **لقب خاص:** القاضي الإمبراطوري الأول للعائلة الملكية\n"
                            f"✨ جزاكم الله خيراً على خدمة العائلة الملكية والمسلمين\n"
                            f"🌟💎👑💎🌟"
                        )
                    else:
                        await message.bot.send_message(
                            JUDGE_ID,
                            f"🕌 **بارك الله في فضيلة الشيخ**\n\n"
                            f"📜 تم إتمام عقد زواج جديد بحضرتكم المباركة\n"
                            f"👰 العروس: {target_name}\n"
                            f"🤵 العريس: {proposer_name}\n"
                            f"💰 الأتعاب المستحقة: {format_number(judge_commission)}$\n"
                            f"💳 رصيدكم الجديد: {format_number(new_judge_balance)}$\n\n"
                            f"🌟 جزاكم الله خيراً على خدمة المسلمين"
                        )
                except:
                    pass  # إذا فشل إرسال الإشعار
        
        elif response_type == "رفض":
            # رفض الطلب
            await execute_query(
                "UPDATE marriage_proposals SET status = 'rejected' WHERE id = ?",
                (proposal_id,)
            )
            
            from utils.helpers import format_number
            await message.reply(
                f"💔 **تم رفض طلب الزواج**\n\n"
                f"👤 المرفوض: {proposer_name}\n"
                f"💰 المهر المرفوض: {format_number(dowry_amount)}$\n\n"
                f"😔 ربما في المرة القادمة!"
            )
    
    except Exception as e:
        logging.error(f"خطأ في معالجة رد الزواج: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الرد")


async def handle_entertainment_command(message: Message, command: str):
    """معالج أوامر التسلية المختلفة"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        if command in ENTERTAINMENT_RESPONSES:
            response = random.choice(ENTERTAINMENT_RESPONSES[command])
            await message.reply(response)
        
        elif command == "تحبني":
            response = random.choice(LOVE_RESPONSES)
            await message.reply(response)
        
        elif command == "تكرهني":
            response = random.choice(HATE_RESPONSES)
            await message.reply(response)
        
        elif command == "نسبه الحب":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                love_percentage = random.randint(0, 100)
                await message.reply(
                    f"💕 نسبة الحب بين {format_user_mention(message.from_user)} "
                    f"و {format_user_mention(target_user)} هي {love_percentage}%"
                )
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")
        
        elif command == "نسبه الغباء":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                stupidity_percentage = random.randint(0, 100)
                await message.reply(
                    f"🤪 نسبة الغباء لدى {format_user_mention(target_user)} "
                    f"هي {stupidity_percentage}%"
                )
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")
        
        elif command == "تحبه":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                response = random.choice(LOVE_RESPONSES)
                await message.reply(f"عن {format_user_mention(target_user)}: {response}")
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")

    except Exception as e:
        logging.error(f"خطأ في أوامر التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")


async def clear_entertainment_ranks(message: Message):
    """مسح رتب التسلية"""
    try:
        if not await has_admin_permission(message.from_user.id, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        await execute_query(
            "DELETE FROM entertainment_ranks WHERE chat_id = ?",
            (message.chat.id,)
        )
        
        await message.reply("✅ تم مسح جميع رتب التسلية من المجموعة")

    except Exception as e:
        logging.error(f"خطأ في مسح رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح الرتب")


async def handle_wedding_dance(message: Message):
    """معالج رقص العرس"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        user_id = message.from_user.id
        user_name = message.from_user.first_name or "شخص"
        
        # التحقق من وجود زواج في المجموعة
        marriage = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
            (user_id, user_id, message.chat.id),
            fetch_one=True
        )
        
        # اختيار رسالة رقص عشوائية
        dance_message = random.choice(WEDDING_DANCE_MESSAGES)
        
        if marriage:
            # إذا كان متزوج، رقص خاص للعرسان
            dance_response = (
                f"💃🕺 **رقص العروسين!** 💃🕺\n\n"
                f"👤 الراقص/ة: {user_name}\n"
                f"{dance_message}\n\n"
                f"🎊 **مبروك للعروسين مرة أخرى!**\n"
                f"💕 الحب يجعل كل شيء أجمل!"
            )
        else:
            # رقص عادي للحضور
            dance_response = (
                f"💃🕺 **رقص في العرس!** 💃🕺\n\n"
                f"👤 الراقص/ة: {user_name}\n"
                f"{dance_message}\n\n"
                f"🎉 الجميع يستمتع بالاحتفال!"
            )
        
        await message.reply(dance_response)

    except Exception as e:
        logging.error(f"خطأ في رقص العرس: {e}")
        await message.reply("❌ حدث خطأ أثناء الرقص")


async def show_group_weddings(message: Message):
    """عرض الأعراس في المجموعة"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        # الحصول على جميع الزيجات في المجموعة
        marriages = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not marriages:
            await message.reply("💔 لا توجد أعراس في هذه المجموعة حالياً")
            return

        wedding_list = "💒 **قائمة الأعراس في المجموعة:** 💒\n\n"
        
        from config.hierarchy import is_royal, is_king, is_queen
        
        for i, marriage in enumerate(marriages, 1):
            if isinstance(marriage, dict):
                user1_id = marriage['user1_id']
                user2_id = marriage['user2_id']
                married_date = marriage.get('married_at', '')
                dowry_amount = marriage.get('dowry_amount', 0)
            else:
                user1_id = marriage[1]
                user2_id = marriage[2]
                married_date = marriage[6] if len(marriage) > 6 else ''
                dowry_amount = marriage[4] if len(marriage) > 4 else 0
            
            # جلب بيانات الزوجين
            user1 = await get_user(user1_id)
            user2 = await get_user(user2_id)
            
            if user1 and user2:
                user1_name = user1.get('first_name', f'المستخدم #{user1_id}')
                user2_name = user2.get('first_name', f'المستخدم #{user2_id}')
                
                # تحديد نوع الزواج
                user1_royal = is_royal(user1_id)
                user2_royal = is_royal(user2_id)
                
                if user1_royal or user2_royal:
                    wedding_type = "👑 زواج ملكي"
                    user1_title = ("الملك" if is_king(user1_id) else "الملكة" if is_queen(user1_id) else "الأمير/ة") if user1_royal else ""
                    user2_title = ("الملك" if is_king(user2_id) else "الملكة" if is_queen(user2_id) else "الأمير/ة") if user2_royal else ""
                    
                    wedding_list += f"{i}. {wedding_type}\n"
                    wedding_list += f"   👸 {user2_title + ' ' if user2_title else ''}{user2_name}\n"
                    wedding_list += f"   🤴 {user1_title + ' ' if user1_title else ''}{user1_name}\n"
                    wedding_list += f"   💎 زواج ملكي مجاني\n"
                else:
                    wedding_type = "💍 زواج عادي"
                    wedding_list += f"{i}. {wedding_type}\n"
                    wedding_list += f"   👰 {user2_name}\n"
                    wedding_list += f"   🤵 {user1_name}\n"
                    
                    if dowry_amount > 0:
                        from utils.helpers import format_number
                        wedding_list += f"   💰 المهر: {format_number(dowry_amount)}$\n"
                
                wedding_list += f"   📅 التاريخ: {married_date[:10] if married_date else 'غير محدد'}\n\n"
        
        wedding_list += f"💕 **المجموع:** {len(marriages)} زواج\n"
        wedding_list += "🎉 مبروك لجميع الأزواج!"
        
        await message.reply(wedding_list)

    except Exception as e:
        logging.error(f"خطأ في عرض أعراس المجموعة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الأعراس")


async def start_royal_ceremony(message: Message):
    """بدء المراسم الملكية للعرس"""
    try:
        user_id = message.from_user.id
        
        from config.hierarchy import is_royal, is_king, is_queen
        
        if not is_royal(user_id):
            await message.reply("❌ هذا الأمر للعائلة الملكية فقط!")
            return

        # التحقق من وجود زواج ملكي للمستخدم
        marriage = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
            (user_id, user_id, message.chat.id),
            fetch_one=True
        )
        
        if not marriage:
            await message.reply("❌ يجب أن تكون متزوجاً لإقامة المراسم الملكية!")
            return

        # إقامة المراسم الملكية
        royal_title = "الملك" if is_king(user_id) else "الملكة"
        ceremony1 = random.choice(ROYAL_WEDDING_CEREMONIES)
        ceremony2 = random.choice(ROYAL_WEDDING_CEREMONIES)
        
        ceremony_message = (
            f"👑✨ **المراسم الملكية الكبرى** ✨👑\n\n"
            f"🎭 بأمر من {royal_title} الأعظم\n"
            f"🏰 تقام المراسم الملكية الفخمة\n\n"
            f"{ceremony1}\n\n"
            f"{ceremony2}\n\n"
            f"🎊 **دعوة عامة لجميع الرعايا:**\n"
            f"💃 اكتبوا **رقص** للانضمام للاحتفال\n"
            f"🎁 اكتبوا **هدية** لتقديم الهدايا الملكية\n"
            f"🎉 اكتبوا **تهنئة** للتهنئة بالزفاف الملكي\n\n"
            f"👑 **عاشت العائلة الملكية!** 👑"
        )
        
        await message.reply(ceremony_message)

    except Exception as e:
        logging.error(f"خطأ في المراسم الملكية: {e}")
        await message.reply("❌ حدث خطأ أثناء إقامة المراسم")


async def give_wedding_gift(message: Message):
    """تقديم هدية العرس"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        giver_id = message.from_user.id
        giver_name = message.from_user.first_name or "شخص"
        
        # التحقق من وجود أي زواج في المجموعة
        marriages = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not marriages:
            await message.reply("❌ لا توجد أعراس في المجموعة لتقديم الهدايا!")
            return

        # اختيار هدية عشوائية
        gifts = [
            {"name": "باقة ورود جميلة", "value": 100},
            {"name": "صندوق شوكولاتة فاخرة", "value": 200},
            {"name": "إطار صور ذهبي", "value": 300},
            {"name": "عطر فرنسي راقي", "value": 500},
            {"name": "مجوهرات فضية", "value": 1000},
            {"name": "ساعة يد أنيقة", "value": 1500},
        ]
        
        gift = random.choice(gifts)
        celebration_message = random.choice(WEDDING_CELEBRATION_MESSAGES)
        
        gift_message = (
            f"🎁 **هدية عرس جميلة!** 🎁\n\n"
            f"👤 مقدم الهدية: {giver_name}\n"
            f"💝 الهدية: {gift['name']}\n"
            f"💰 القيمة: {gift['value']}$\n\n"
            f"{celebration_message}\n\n"
            f"🌟 شكراً لكم على هذا الكرم!"
        )
        
        await message.reply(gift_message)

    except Exception as e:
        logging.error(f"خطأ في هدية العرس: {e}")
        await message.reply("❌ حدث خطأ أثناء تقديم الهدية")


# دوال مساعدة
async def is_entertainment_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل التسلية"""
    try:
        setting = await execute_query(
            "SELECT setting_value FROM group_settings WHERE chat_id = ? AND setting_key = 'enable_entertainment'",
            (chat_id,),
            fetch_one=True
        )
        
        if setting:
            return setting[0] == "True" if isinstance(setting, tuple) else setting['setting_value'] == "True"
        return True  # افتراضياً مفعل
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من تفعيل التسلية: {e}")
        return True


async def has_admin_permission(user_id: int, chat_id: int) -> bool:
    """التحقق من صلاحيات الإدارة"""
    try:
        from config.settings import ADMINS
        if user_id in ADMINS:
            return True
            
        user_rank = await execute_query(
            "SELECT rank_type FROM group_ranks WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        return user_rank is not None
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من الصلاحيات: {e}")
        return False


async def wedding_dance(message: Message):
    """الرقص في العرس مع رسائل متحركة حقيقية"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        dancer_name = message.from_user.first_name or "الراقص"
        
        # التحقق من وجود أي زواج في المجموعة
        marriages = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not marriages:
            await message.reply("❌ لا توجد أعراس في المجموعة للرقص فيها!")
            return

        from config.hierarchy import is_royal
        
        # تحديد نوع الرقصة حسب الرتبة
        if is_royal(message.from_user.id):
            # رقصة ملكية متحركة
            dance_frames = await create_custom_dance_animation(dancer_name, "royal")
            celebration = random.choice(ROYAL_WEDDING_CEREMONIES)
            
            # إرسال الرقصة المتحركة الملكية
            await animate_message(
                message.bot,
                message.chat.id,
                dance_frames,
                delay=0.5,
                title=f"👑 الرقصة الملكية الفخمة 👑"
            )
            
            await asyncio.sleep(1)
            dance_response = (
                f"👑✨ **عرض ملكي أسطوري من {dancer_name}** ✨👑\n\n"
                f"{celebration}\n\n"
                f"🎊 **الحضور يصفق بحماس للعرض الملكي الخيالي!**\n"
                f"👏 عاشت العائلة الملكية! عاش الحب!\n"
                f"🏰 **الرقصة الملكية تهز أركان القصر!** 🏰"
            )
        else:
            # رقصة عادية متحركة
            dance_frames = await create_custom_dance_animation(dancer_name, "normal")
            celebration = random.choice(WEDDING_CELEBRATION_MESSAGES)
            
            # إرسال الرقصة المتحركة العادية
            await animate_message(
                message.bot,
                message.chat.id,
                dance_frames,
                delay=0.4,
                title=f"💃🕺 رقصة {dancer_name} الرائعة 🕺💃"
            )
            
            await asyncio.sleep(1)
            dance_response = (
                f"💃🕺 **عرض رقص رائع من {dancer_name}** 🕺💃\n\n"
                f"{celebration}\n\n"
                f"🎉 **الجميع يشارك في الفرحة والمرح!**\n"
                f"👏 يا هلا يا هلا! مبروك للعرسان!"
            )
        
        await message.reply(dance_response)
        
        # إضافة رقص تلقائي للحاضرين
        try:
            await asyncio.sleep(2)
            recent_users = await get_recent_active_users(message.chat.id, 3)
            for user in recent_users:
                if user['user_id'] != message.from_user.id:  # تجنب الراقص نفسه
                    await asyncio.sleep(1)
                    celebration_msg = random.choice(AUTO_CELEBRATION_MESSAGES).format(
                        name=user.get('first_name', 'عضو')
                    )
                    await message.bot.send_message(message.chat.id, f"🎊 {celebration_msg}")
        except Exception as auto_dance_error:
            logging.error(f"خطأ في الرقص التلقائي للحاضرين: {auto_dance_error}")
        
        # إضافة XP للراقص
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, 15)  # XP إضافي للرقص
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP للرقص: {xp_error}")

    except Exception as e:
        logging.error(f"خطأ في رقص العرس: {e}")
        await message.reply("❌ حدث خطأ أثناء الرقص")


async def wedding_congratulation(message: Message):
    """التهنئة بالعرس"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        congratulator_name = message.from_user.first_name or "المهنئ"
        
        # التحقق من وجود أي زواج في المجموعة
        marriages = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE chat_id = ?",
            (message.chat.id,),
            fetch_all=True
        )
        
        if not marriages:
            await message.reply("❌ لا توجد أعراس في المجموعة للتهنئة!")
            return

        # رسائل التهنئة العادية
        congratulation_messages = [
            f"🎉 {congratulator_name} يهنئ العرسان بأجمل التهاني!",
            f"💐 {congratulator_name} يقدم أحر التهاني للعروسين!",
            f"🌹 {congratulator_name} يبارك للزوجين الجدد!",
            f"🎊 {congratulator_name} يهنئهم من القلب!",
            f"💕 {congratulator_name} يتمنى لهم حياة سعيدة!",
            f"✨ {congratulator_name} يدعو لهم بالسعادة الدائمة!",
        ]
        
        # رسائل تهنئة ملكية خاصة
        royal_congratulation_messages = [
            f"👑 {congratulator_name} يقدم التهاني الملكية للعرسان!",
            f"🏰 {congratulator_name} يبارك بالأسلوب الإمبراطوري النبيل!",
            f"⚜️ {congratulator_name} يهنئ بالطقوس الملكية المقدسة!",
            f"💎 {congratulator_name} يقدم تحية العائلة الملكية!",
            f"🎭 {congratulator_name} يبارك بلسان النبلاء والأمراء!",
        ]
        
        from config.hierarchy import is_royal
        
        # تحديد نوع التهنئة حسب الرتبة
        if is_royal(message.from_user.id):
            congrat_msg = random.choice(royal_congratulation_messages)
            blessing = random.choice(ROYAL_WEDDING_CEREMONIES)
            
            congratulation_response = (
                f"👑🎉 **تهنئة ملكية فخمة** 🎉👑\n\n"
                f"{congrat_msg}\n\n"
                f"{blessing}\n\n"
                f"🏰 **بركات العائلة الملكية على العرسان**\n"
                f"💎 عسى أن تدوم المحبة والسعادة\n"
                f"👑 **حفظكم الله ورعاكم بعنايته**"
            )
        else:
            congrat_msg = random.choice(congratulation_messages)
            blessing = random.choice(WEDDING_CELEBRATION_MESSAGES)
            
            congratulation_response = (
                f"🎉💕 **تهنئة حارة بالعرس** 💕🎉\n\n"
                f"{congrat_msg}\n\n"
                f"{blessing}\n\n"
                f"🌹 **دعوات خالصة بالسعادة**\n"
                f"✨ عقبال كل الشباب والبنات\n"
                f"🎊 **ألف مبروك للعروسين!**"
            )
        
        await message.reply(congratulation_response)
        
        # إضافة XP للمهنئ
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, 10)  # XP للتهنئة
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP للتهنئة: {xp_error}")

    except Exception as e:
        logging.error(f"خطأ في تهنئة العرس: {e}")
        await message.reply("❌ حدث خطأ أثناء التهنئة")


# وظائف الرسائل المتحركة والرقص التلقائي الجديدة 🎬

async def animate_message(bot, chat_id, frames, delay=0.5, title="", repeat_cycles=1):
    """إنشاء رسالة متحركة متقدمة بتحرير الرسالة مع تأثيرات بصرية"""
    try:
        if not frames:
            return None
            
        # إرسال الإطار الأول مع تحسينات بصرية
        if title:
            initial_text = f"🎬 **{title}** 🎬\n\n```\n{frames[0]}\n```\n\n⚡ *جاري التحميل...* ⚡"
        else:
            initial_text = f"```\n{frames[0]}\n```"
            
        message = await bot.send_message(chat_id, initial_text, parse_mode='Markdown')
        
        # تحريك الإطارات مع دورات التكرار
        for cycle in range(repeat_cycles):
            frame_list = frames[1:] if cycle == 0 else frames
            
            for i, frame in enumerate(frame_list):
                await asyncio.sleep(delay)
                
                # إضافة مؤشر التقدم والحالة
                progress_bar = "▓" * (i % 10 + 1) + "░" * (10 - (i % 10 + 1))
                cycle_indicator = f" [دورة {cycle + 1}/{repeat_cycles}]" if repeat_cycles > 1 else ""
                
                try:
                    if title:
                        new_text = (
                            f"🎬 **{title}** 🎬\n\n"
                            f"```\n{frame}\n```\n\n"
                            f"🎯 التقدم: {progress_bar}{cycle_indicator}\n"
                            f"✨ *يرقص بجنون...* ✨"
                        )
                    else:
                        new_text = f"```\n{frame}\n```"
                        
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message.message_id,
                        text=new_text,
                        parse_mode='Markdown'
                    )
                except Exception as edit_error:
                    logging.error(f"خطأ في تحرير الرسالة المتحركة: {edit_error}")
                    # إنشاء رسالة جديدة في حالة فشل التحرير
                    message = await bot.send_message(chat_id, new_text, parse_mode='Markdown')
        
        # إضافة رسالة نهاية الرسوم المتحركة
        if title:
            final_text = (
                f"🎬 **{title}** 🎬\n\n"
                f"```\n{frames[-1]}\n```\n\n"
                f"🎯 التقدم: ▓▓▓▓▓▓▓▓▓▓ [مكتمل!]\n"
                f"🎉 *انتهت الرسوم المتحركة بنجاح!* 🎉"
            )
            await asyncio.sleep(delay)
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message.message_id,
                    text=final_text,
                    parse_mode='Markdown'
                )
            except Exception:
                await bot.send_message(chat_id, final_text, parse_mode='Markdown')
                
        return message
        
    except Exception as e:
        logging.error(f"خطأ في الرسالة المتحركة: {e}")
        return None


async def trigger_automatic_wedding_celebration(bot, chat_id, marriage_data, royal_wedding=False):
    """حفلة زفاف هستيرية تدوم دقيقة كاملة مع أنشطة متنوعة ومضحكة"""
    try:
        # الحصول على قائمة أعضاء المجموعة النشطين
        recent_users = await get_recent_active_users(chat_id)
        
        if royal_wedding:
            # 🎭 حفلة ملكية فخمة مدتها دقيقة كاملة
            
            # 1. بداية الموكب الملكي (10 ثواني)
            await animate_message(
                bot, chat_id, 
                ANIMATED_DANCE_FRAMES["royal_procession"], 
                delay=0.3,
                title="🏰👑 بدء الموكب الملكي الأسطوري 👑🏰",
                repeat_cycles=2
            )
            await asyncio.sleep(1)
            
            # 2. رقصة البالي الملكية (8 ثواني)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["ballet_dancer"],
                delay=0.4,
                title="👸✨ رقصة البالي الملكية الساحرة ✨👸",
                repeat_cycles=2
            )
            await asyncio.sleep(1)
            
            # 3. مشاركة النبلاء والحاضرين (15 ثانية)
            for user in recent_users[:5]:
                await asyncio.sleep(1.5)
                celebration_msg = random.choice(AUTO_CELEBRATION_MESSAGES).format(
                    name=user.get('first_name', 'نبيل')
                )
                await bot.send_message(
                    chat_id, 
                    f"👑 **النبيل {user.get('first_name', 'عضو')}** يشارك في الفرحة الملكية!\n"
                    f"⚜️ {celebration_msg} مع التيجان والزهور الذهبية! ✨"
                )
            
            # 4. مهرجان الألوان الملكي (متقدم)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["color_festival"],
                delay=0.5,
                title="🌈👑 مهرجان الألوان الملكي الفخم 👑🌈",
                repeat_cycles=3
            )
            await asyncio.sleep(1)
            
            # 5. رقصة الديسكو الملكية (هستيرية)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["disco_fever"],
                delay=0.4,
                title="✨👑 ديسكو العائلة الملكية الأسطوري 👑✨",
                repeat_cycles=3
            )
            await asyncio.sleep(1)
            
            # 6. ختام بالحيوانات الملكية (مجنون)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["animal_party"],
                delay=0.5,
                title="🦁👑 حفلة الحيوانات الملكية المجنونة 👑🐯",
                repeat_cycles=2
            )
            
        else:
            # 🎉 حفلة عادية هستيرية مدتها دقيقة كاملة
            
            # 1. بداية مجنونة بالراقصين المضحكين (هستيرية!)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["crazy_dancers"],
                delay=0.6,
                title="🤪😂 بداية الحفلة المجنونة! 😂🤪",
                repeat_cycles=3
            )
            await asyncio.sleep(1)
            
            # 2. رقصة هستيرية جماعية (مجنونة جداً!)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["hysterical_dance"],
                delay=0.8,
                title="🤯🥳 الرقصة الهستيرية الجماعية! 🥳🤯",
                repeat_cycles=4
            )
            await asyncio.sleep(1)
            
            # 3. مشاركة الحاضرين مع رسائل مضحكة (12 ثانية)
            funny_messages = [
                "😂 {name} يرقص كأنه مجنون!",
                "🤪 {name} فقد عقله من الفرح!",
                "🥳 {name} يرقص رقصة الديك!",
                "😵‍💫 {name} دائخ من كثرة الدوران!",
                "🤡 {name} يقلد المهرجين!"
            ]
            for user in recent_users[:4]:
                await asyncio.sleep(1.5)
                funny_msg = random.choice(funny_messages).format(
                    name=user.get('first_name', 'عضو')
                )
                await bot.send_message(chat_id, f"😂🎊 {funny_msg} 🎊😂")
            
            # 4. رقصة البريك دانس (مجنونة!)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["breakdancer"],
                delay=0.5,
                title="🕺💫 عرض بريك دانس خرافي! 💫🕺",
                repeat_cycles=2
            )
            await asyncio.sleep(1)
            
            # 5. حفلة الحيوانات المضحكة (هستيرية!)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["animal_party"],
                delay=0.6,
                title="🐵🐸 حفلة الحيوانات المجنونة! 🐸🐵",
                repeat_cycles=3
            )
            await asyncio.sleep(1)
            
            # 6. رقصة الروبوت النهائية (مجنونة!)
            await animate_message(
                bot, chat_id,
                ANIMATED_DANCE_FRAMES["robot_dance"],
                delay=0.5,
                title="🤖⚡ رقصة الروبوت الختامية! ⚡🤖",
                repeat_cycles=2
            )
        
        # رسالة ختامية مضحكة ومميزة
        if royal_wedding:
            final_message = (
                "🏰✨ انتهت الحفلة الملكية الأسطورية! ✨🏰\n"
                "👑 العائلة الملكية راضية ومسرورة! 👑\n"
                "⚜️ كان هذا أعظم احتفال في تاريخ المملكة! ⚜️"
            )
        else:
            final_message = (
                "😂🎉 انتهت الحفلة المجنونة! 🎉😂\n"
                "🤪 الجميع تعب من كثرة الرقص! 🤪\n" 
                "🥳 هذه كانت أفضل حفلة على الإطلاق! 🥳"
            )
        
        await bot.send_message(chat_id, final_message)
        
    except Exception as e:
        logging.error(f"خطأ في الاحتفال التلقائي: {e}")


async def get_recent_active_users(chat_id, limit=10):
    """الحصول على المستخدمين النشطين مؤخراً في المجموعة"""
    try:
        # الحصول على المستخدمين الذين تفاعلوا مؤخراً
        users = await execute_query(
            """
            SELECT DISTINCT user_id, first_name, username 
            FROM users 
            WHERE chat_id = ? 
            ORDER BY last_seen DESC 
            LIMIT ?
            """,
            (chat_id, limit),
            fetch_all=True
        )
        
        if users:
            return [
                {
                    'user_id': user[0] if isinstance(user, tuple) else user['user_id'],
                    'first_name': user[1] if isinstance(user, tuple) else user['first_name'],
                    'username': user[2] if isinstance(user, tuple) else user.get('username')
                }
                for user in users
            ]
        
        # إذا لم توجد بيانات، إرجاع قائمة فارغة
        return []
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على المستخدمين النشطين: {e}")
        return []


async def start_wedding_celebration_with_animation(bot, chat_id, marriage_id, is_royal=False):
    """بدء احتفال العرس مع الرسائل المتحركة التلقائية"""
    try:
        # رسالة إعلان بداية الاحتفال
        if is_royal:
            announcement = "👑🎉 **بدء الاحتفال الملكي الفخم!** 🎉👑\n🏰 الجميع مدعو للمشاركة في الفرحة الملكية!"
        else:
            announcement = "🎉💍 **بدء احتفال العرس!** 💍🎉\n💃 الجميع مدعو للرقص والاحتفال!"
            
        await bot.send_message(chat_id, announcement)
        await asyncio.sleep(2)
        
        # تفعيل الاحتفال التلقائي
        await trigger_automatic_wedding_celebration(bot, chat_id, marriage_id, is_royal)
        
        # رسالة تذكير للمجموعة
        reminder = "✨ يمكن لأي عضو استخدام أوامر الرقص والتهنئة للمشاركة في الفرحة! ✨"
        await bot.send_message(chat_id, reminder)
        
    except Exception as e:
        logging.error(f"خطأ في بدء احتفال العرس المتحرك: {e}")


async def create_custom_dance_animation(dancer_name, dance_type="normal"):
    """إنشاء رقصة مخصصة متحركة"""
    try:
        if dance_type == "royal":
            frames = [
                f"      👑      \n   {dancer_name}   \n      🏰      ",
                f"    👑   👑    \n   {dancer_name}   \n    🏰   🏰    ",
                f"  👑   👑   👑  \n   {dancer_name}   \n  🏰   🏰   🏰  ",
                f"👑   👑   👑   👑\n   {dancer_name}   \n🏰   🏰   🏰   🏰"
            ]
        else:
            frames = [
                f"   {dancer_name}   \n     💃     ",
                f"   {dancer_name}   \n    💃🕺    ",
                f"   {dancer_name}   \n   💃🕺💃   ",
                f"   {dancer_name}   \n  💃🕺💃🕺  ",
                f"   {dancer_name}   \n 💃🕺💃🕺💃 "
            ]
            
        return frames
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء الرقصة المخصصة: {e}")
        return [f"{dancer_name} يرقص! 💃🕺"]
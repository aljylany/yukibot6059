"""
الأوامر الترفيهية والخدمية
Fun and Service Commands Module
"""

import logging
import random
from datetime import datetime
from aiogram.types import Message
from config.database import get_database_connection


# قوائم البيانات للأوامر الترفيهية
CARS = [
    "لامبورغيني أفينتادور", "فيراري F8", "بورش 911", "مكلارين 720S", "بوجاتي شيرون",
    "مرسيدس AMG GT", "BMW M8", "أودي R8", "جاغوار F-Type", "أستون مارتن DB11",
    "تويوتا كورولا", "هوندا سيفيك", "نيسان التيما", "هيونداي إلنترا", "كيا أوبتيما"
]

HOUSES = [
    "قصر فخم بإطلالة على البحر", "فيلا عصرية بحديقة واسعة", "بيت تراثي جميل",
    "شقة عصرية في ناطحة سحاب", "كوخ خشبي بجانب الغابة", "قلعة أثرية مرميمة",
    "بيت صغير في الريف", "شقة متواضعة", "استوديو في المدينة", "غرفة في سكن مشترك"
]

QUOTES = [
    "النجاح لا يأتي من الراحة، بل من العمل الجاد والمثابرة.",
    "كل يوم هو فرصة جديدة لتصبح نسخة أفضل من نفسك.",
    "الأحلام تتحقق لمن يؤمن بها ويعمل من أجلها.",
    "القوة الحقيقية تكمن في القدرة على النهوض بعد كل سقطة.",
    "التغيير صعب في البداية، فوضوي في المنتصف، جميل في النهاية."
]

POETRY = [
    "يا من هواه أعزه وأذلني... كيف السبيل إلى وصالك دلني",
    "إذا المرء لا يرعاك إلا تكلفاً... فدعه ولا تكثر عليه التأسفا",
    "ومن جعل الضرغام بازاً لصيده... تصيده الضرغام فيما تصيدا",
    "إذا أنت أكرمت الكريم ملكته... وإن أنت أكرمت اللئيم تمردا"
]


async def my_car(message: Message):
    """عرض السيارة العشوائية"""
    try:
        car = random.choice(CARS)
        await message.reply(f"🚗 سيارتك هي: {car}")
    except Exception as e:
        logging.error(f"خطأ في أمر سيارتي: {e}")


async def my_house(message: Message):
    """عرض المنزل العشوائي"""
    try:
        house = random.choice(HOUSES)
        await message.reply(f"🏠 منزلك هو: {house}")
    except Exception as e:
        logging.error(f"خطأ في أمر منزلي: {e}")


async def my_age(message: Message):
    """عرض العمر العشوائي"""
    try:
        age = random.randint(16, 65)
        await message.reply(f"🎂 عمرك هو: {age} سنة")
    except Exception as e:
        logging.error(f"خطأ في أمر عمري: {e}")


async def my_height(message: Message):
    """عرض الطول العشوائي"""
    try:
        height = random.randint(150, 190)
        await message.reply(f"📏 طولك هو: {height} سم")
    except Exception as e:
        logging.error(f"خطأ في أمر طولي: {e}")


async def my_weight(message: Message):
    """عرض الوزن العشوائي"""
    try:
        weight = random.randint(50, 120)
        await message.reply(f"⚖️ وزنك هو: {weight} كيلو")
    except Exception as e:
        logging.error(f"خطأ في أمر وزني: {e}")


async def do_you_love_me(message: Message):
    """هل تحبني؟"""
    try:
        responses = [
            "نعم أحبك كثيراً ❤️", "أحبك من كل قلبي 💕", "أنت الأفضل 💖",
            "لا أستطيع أن أحب، أنا بوت 🤖", "هذا سؤال صعب 🤔", "أحبك كصديق 😊"
        ]
        response = random.choice(responses)
        await message.reply(f"💭 {response}")
    except Exception as e:
        logging.error(f"خطأ في أمر تحبني: {e}")


async def do_you_hate_me(message: Message):
    """هل تكرهني؟"""
    try:
        responses = [
            "لا، لا أكرهك أبداً 😊", "كيف يمكنني أن أكرهك؟ 💕", "أنت رائع، لماذا أكرهك؟ 😄",
            "لا أستطيع أن أكره، أنا مجرد بوت 🤖", "الكراهية شعور سلبي لا أحمله 😇"
        ]
        response = random.choice(responses)
        await message.reply(f"💭 {response}")
    except Exception as e:
        logging.error(f"خطأ في أمر تكرهني: {e}")


async def love_percentage(message: Message, user1: str, user2: str):
    """نسبة الحب بين شخصين"""
    try:
        percentage = random.randint(1, 100)
        
        if percentage >= 90:
            result = "حب مثالي وأبدي! 💖"
        elif percentage >= 75:
            result = "حب قوي ومتين! 💕"
        elif percentage >= 50:
            result = "حب جيد! ❤️"
        elif percentage >= 25:
            result = "حب ضعيف 💔"
        else:
            result = "لا يوجد حب 💔"
            
        await message.reply(f"💝 نسبة الحب بين {user1} و {user2} هي: {percentage}%\n{result}")
    except Exception as e:
        logging.error(f"خطأ في أمر نسبة الحب: {e}")


async def stupidity_percentage(message: Message):
    """نسبة الغباء للشخص المرد عليه"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة شخص لمعرفة نسبة غبائه")
            return
            
        percentage = random.randint(1, 100)
        name = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else "الشخص"
        
        if percentage >= 90:
            result = "غبي جداً! 🤯"
        elif percentage >= 75:
            result = "غبي نوعاً ما 😅"
        elif percentage >= 50:
            result = "عادي 😐"
        elif percentage >= 25:
            result = "ذكي نسبياً 🤓"
        else:
            result = "عبقري! 🧠"
            
        await message.reply(f"🧠 نسبة غباء {name} هي: {percentage}%\n{result}")
    except Exception as e:
        logging.error(f"خطأ في أمر نسبة الغباء: {e}")


async def femininity_percentage(message: Message):
    """نسبة الانوثة للفتاة المرد عليها"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة فتاة لمعرفة نسبة أنوثتها")
            return
            
        percentage = random.randint(1, 100)
        name = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else "الفتاة"
        
        if percentage >= 90:
            result = "أنوثة راقية جداً! 👸"
        elif percentage >= 75:
            result = "أنوثة جميلة! 💃"
        elif percentage >= 50:
            result = "أنوثة طبيعية 🌸"
        else:
            result = "أنوثة قليلة 😅"
            
        await message.reply(f"🌹 نسبة أنوثة {name} هي: {percentage}%\n{result}")
    except Exception as e:
        logging.error(f"خطأ في أمر نسبة الانوثة: {e}")


async def masculinity_percentage(message: Message):
    """نسبة الرجولة للشاب المرد عليه"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة شاب لمعرفة نسبة رجولته")
            return
            
        percentage = random.randint(1, 100)
        name = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else "الشاب"
        
        if percentage >= 90:
            result = "رجولة حقيقية! 💪"
        elif percentage >= 75:
            result = "رجولة قوية! 🦁"
        elif percentage >= 50:
            result = "رجولة عادية 👨"
        else:
            result = "رجولة ضعيفة 😅"
            
        await message.reply(f"🦾 نسبة رجولة {name} هي: {percentage}%\n{result}")
    except Exception as e:
        logging.error(f"خطأ في أمر نسبة الرجولة: {e}")


async def magic_yuki(message: Message, question: str):
    """مايكي السحري للإجابة على الأسئلة"""
    try:
        answers = [
            "نعم بالتأكيد! ✨", "لا، لا أعتقد ذلك 🔮", "ربما، المستقبل غامض 🌟",
            "بالطبع! ⭐", "لا، مستحيل 🚫", "اسأل مرة أخرى لاحقاً 🔄",
            "نعم، ولكن ليس الآن ⏰", "الإجابة في قلبك 💖", "لا تعتمد على ذلك ❌",
            "أرى مستقبلاً مشرقاً! 🌈", "الطريق صعب لكن ممكن 🌙", "نعم، إذا آمنت بذلك 🙏"
        ]
        answer = random.choice(answers)
        await message.reply(f"🔮 مايكي السحري يقول:\n💫 {answer}")
    except Exception as e:
        logging.error(f"خطأ في مايكي السحري: {e}")


async def get_similar(message: Message):
    """البحث عن الشبيه العشوائي"""
    try:
        if not message.reply_to_message:
            # إذا لم يكن رد على رسالة، اختر شخص عشوائي من المجموعة
            similar_names = [
                "أحمد علي", "فاطمة محمد", "خالد حسن", "نور الدين", "سارة أحمد",
                "محمد عبدالله", "عائشة علي", "يوسف محمود", "زينب حسام", "عمر سالم"
            ]
            similar = random.choice(similar_names)
            await message.reply(f"👥 شبيهك هو: {similar}")
        else:
            # إذا كان رد على رسالة، ابحث عن شبيه للشخص المرد عليه
            name = message.reply_to_message.from_user.first_name if message.reply_to_message.from_user else "الشخص"
            similar_names = [
                "الممثل محمد رمضان", "الفنانة نانسي عجرم", "اللاعب محمد صلاح",
                "الشيف بوراك", "الفنان عمرو دياب", "الممثلة ياسمين عبدالعزيز"
            ]
            similar = random.choice(similar_names)
            await message.reply(f"👥 شبيه {name} هو: {similar}")
    except Exception as e:
        logging.error(f"خطأ في أمر الشبيه: {e}")


async def give_gift(message: Message):
    """إعطاء هدية عشوائية"""
    try:
        gifts = [
            "🎁 صندوق شوكولاتة فاخرة", "🌹 باقة ورد جميلة", "📱 هاتف ذكي جديد",
            "⌚ ساعة يد أنيقة", "🎮 جهاز ألعاب", "📚 مجموعة كتب مفيدة",
            "💎 قطعة مجوهرات", "🎧 سماعات عالية الجودة", "🖥️ جهاز كمبيوتر",
            "🚗 سيارة صغيرة", "✈️ تذكرة سفر", "🍰 كعكة لذيذة"
        ]
        gift = random.choice(gifts)
        await message.reply(f"🎉 مايكي يهديك: {gift}")
    except Exception as e:
        logging.error(f"خطأ في أمر الهدية: {e}")


async def avatar_opinion(message: Message):
    """رأي مايكي في الافتار"""
    try:
        opinions = [
            "افتار رائع جداً! 😍", "جميل ولكن يحتاج تحسين 😊", "افتار عادي 😐",
            "مميز وأنيق! ✨", "يمكنك اختيار أفضل 🤔", "افتار محترف! 👌",
            "جميل لكن قديم 😅", "افتار مثالي! 💯", "يعجبني كثيراً! 😄"
        ]
        opinion = random.choice(opinions)
        await message.reply(f"📸 رأيي في افتارك: {opinion}")
    except Exception as e:
        logging.error(f"خطأ في أمر رأي الافتار: {e}")


async def send_quote(message: Message):
    """إرسال اقتباس عشوائي"""
    try:
        quote = random.choice(QUOTES)
        await message.reply(f"💭 {quote}")
    except Exception as e:
        logging.error(f"خطأ في أمر الاقتباس: {e}")


async def send_poetry(message: Message):
    """إرسال شعر عشوائي"""
    try:
        poem = random.choice(POETRY)
        await message.reply(f"🖋️ {poem}")
    except Exception as e:
        logging.error(f"خطأ في أمر الشعر: {e}")


async def truth_dare(message: Message):
    """لعبة صراحة"""
    try:
        questions = [
            "ما هو أكبر كذبة قلتها؟",
            "من هو الشخص الذي تحبه سراً؟",
            "ما هو أكثر شيء تخجل منه؟",
            "ما هو حلمك الذي لم تحققه بعد؟",
            "من هو آخر شخص راسلته؟",
            "ما هو أغرب شيء فعلته؟",
            "من هو الشخص الذي تتمنى أن تكون مثله؟",
            "ما هو أكثر شيء تندم عليه؟"
        ]
        question = random.choice(questions)
        await message.reply(f"🎯 سؤال صراحة:\n❓ {question}")
    except Exception as e:
        logging.error(f"خطأ في لعبة الصراحة: {e}")


async def would_you_rather(message: Message):
    """لعبة لو خيروك"""
    try:
        choices = [
            ("أن تطير في السماء", "أن تتنفس تحت الماء"),
            ("أن تقرأ الأفكار", "أن تصبح غير مرئي"),
            ("أن تعيش في الماضي", "أن تعيش في المستقبل"),
            ("أن تكون غنياً وحيداً", "أن تكون فقيراً مع الأصدقاء"),
            ("أن تفقد الذاكرة", "أن تفقد القدرة على النوم"),
            ("أن تعيش 200 سنة", "أن تعيش حياة كاملة في يوم واحد")
        ]
        choice1, choice2 = random.choice(choices)
        await message.reply(f"🤔 لو خيروك:\n1️⃣ {choice1}\n2️⃣ {choice2}")
    except Exception as e:
        logging.error(f"خطأ في لعبة لو خيروك: {e}")


async def kit_tweet(message: Message):
    """كت تويت"""
    try:
        questions = [
            "أجمل لحظة عشتها؟",
            "كلمة تقولها كثيراً؟",
            "ماذا تفعل عندما تكون حزيناً؟",
            "أغنية تستمع لها دائماً؟",
            "مكان تحب أن تزوره؟",
            "أكلة لا تستطيع مقاومتها؟",
            "شيء تتمنى تغييره في نفسك؟",
            "أسعد ذكرى في حياتك؟"
        ]
        question = random.choice(questions)
        await message.reply(f"💬 كت تويت:\n❓ {question}")
    except Exception as e:
        logging.error(f"خطأ في كت تويت: {e}")


async def decorative_text(message: Message, text: str):
    """زخرفة النص"""
    try:
        # زخارف مختلفة للنص
        decorations = [
            f"✦ {text} ✦",
            f"◈ {text} ◈",
            f"❈ {text} ❈",
            f"✿ {text} ✿",
            f"⟐ {text} ⟐",
            f"◊ {text} ◊"
        ]
        
        decorated = random.choice(decorations)
        await message.reply(f"✨ النص المزخرف:\n{decorated}")
    except Exception as e:
        logging.error(f"خطأ في زخرفة النص: {e}")
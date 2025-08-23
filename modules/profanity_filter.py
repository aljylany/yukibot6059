"""
نظام كشف السباب والكتم التلقائي
يقوم بكتم المستخدمين الذين يسبون ويرسل رسالة من السيدة رهف
"""

import logging
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import TelegramBadRequest
# from utils.decorators import ensure_group_only  # مُعطل مؤقتاً
from datetime import datetime, timedelta

# قائمة الكلمات المحظورة (السباب)
BANNED_WORDS = [
    # سباب باللغة العربية العامة
    "كلب", "كلبة", "حمار", "حمارة", "غبي", "غبية", "أحمق", "أحمقة", 
    "وسخ", "وسخة", "قذر", "قذرة", "لعين", "لعينة", "خنزير", "خنزيرة",
    "حيوان", "بهيمة", "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
    "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
    "ابن الكلب", "بنت الكلب", "ابن الشرموطة", "بنت الشرموطة",
    "يا كلب", "يا كلبة", "يا حمار", "يا حمارة", "يا غبي", "يا غبية",
    "خرا", "خراء", "قرف", "تف", "يلعن", "اللعنة", "منحوس", "منحوسة",
    "حثالة", "زبالة", "قمامة", "خسيس", "خسيسة", "دنيء", "دنيئة",
    "ساقط", "ساقطة", "واطي", "واطية", "رخيص", "رخيصة",
    
    # كلمات إضافية مطلوبة
    "منيوك", "ايري", "انيك", "نيكك", "منيوكة", "ايرك", "ايرها",
    "انيكك", "انيكها", "منيوكو", "ايرو", "نيكو", "كسمك", "كسك",
    "كسها", "كسهم", "كسكم", "كسكن", "زبك", "زبها", "زبهم", "زبكم",
    
    # سباب يمني
    "قاوود", "قواد", "زومل", "زومله", "ثور", "ثوره", "جحش", "جحشه",
    "عفريت", "عفريته", "دبل", "دبله", "خرب", "خربه", "صلعه", "صلع",
    "قرعه", "قرع", "عجبه", "عجب", "حقير", "حقيره", "وغد", "وغده",
    "لقيط", "لقيطه", "حقر", "حقره", "نجس", "نجسه", "قرف", "قرفه",
    "عنتيل", "عنتيله", "صعلوك", "صعلوكه", "شحات", "شحاته", "متسول",
    "متسوله", "ذباح", "ذباحه", "سفاح", "سفاحه", "مجرم", "مجرمه",
    "حرامي", "حراميه", "لص", "لصه", "نصاب", "نصابه", "محتال", "محتاله",
    "مزور", "مزوره", "كذاب", "كذابه", "منافق", "منافقه", "خداع", "خداعه",
    "ملعون", "ملعونه", "شيطان", "شيطانه", "ابليس", "ابليسه",
    
    # تركيبات يمنية شائعة
    "يا قاوود", "يا قواد", "يا زومل", "يا زومله", "يا ثور", "يا ثوره",
    "يا جحش", "يا جحشه", "يا عفريت", "يا عفريته", "يا دبل", "يا دبله",
    "ابن القاوود", "بنت القواد", "ابن الزومل", "بنت الزومله",
    "كلب يمني", "كلبه يمنيه", "حمار يمني", "حماره يمنيه",
    
    # إضافات شائعة
    "احا", "اح", "تبا", "لعنة", "يلعن ابوك", "يلعن ابوكي", "روح مت",
    "كول خرا", "اكل خرا", "امك", "ابوك", "اختك", "اخوك", "اهلك",
    "عيلتك", "عائلتك", "بيتك", "دارك", "اصلك", "فصلك", "نسلك",
    
    # كلمات جنسية صريحة
    "جنس", "جماع", "مجامعه", "نكاح", "مناكه", "سكس", "ممارسه",
    "معاشره", "لواط", "لوطي", "لوطيه", "شاذ", "شاذه", "مثلي", "مثليه"
]

# كلمات إضافية بصيغ مختلفة
BANNED_VARIATIONS = [
    # صيغ مختلفة بالأرقام والرموز
    "كل8", "ك7ب", "حم4ر", "غ8ي", "@حمق", "وس5", "قذ7", 
    "ل3ين", "5نزير", "ح10ان", "8هيمة", "شرم0ط", "3اهرة",
    "من1ك", "ن1ك", "ك5", "ز8", "ط1ز", "58ن الكل8", "8نت الكل8ة",
    "من10ك", "@يري", "انن1ك", "من10وك", "@يرك", "ان1كك",
    "ق@وود", "ق0اد", "ز0مل", "ث0ر", "جح5", "عفر1ت",
    
    # صيغ بديلة للكلمات اليمنية
    "قوووود", "قااااد", "زوووومل", "ثوووور", "جحححش",
    "عفرييييت", "دببببل", "خرررب", "صلععععه", "قرععععه",
    
    # بديلات بالإنجليزية
    "fuck", "shit", "damn", "bitch", "asshole", "bastard", "whore", "slut",
    "motherfucker", "dickhead", "pussy", "cock", "penis", "vagina",
    
    # صيغ مختلطة
    "كs", "nيك", "fuck you", "انيكك", "kس", "zب", "tيز",
    "qاوود", "wغد", "lقيط", "hقير", "nجس", "qرف"
]

# دمج جميع الكلمات المحظورة
ALL_BANNED_WORDS = BANNED_WORDS + BANNED_VARIATIONS

def clean_text_for_profanity_check(text: str) -> str:
    """
    تنظيف النص لإزالة التشفير والتمويه
    """
    if not text:
        return ""
    
    # تحويل لأحرف صغيرة
    cleaned = text.lower().strip()
    
    # إزالة المسافات الزائدة
    cleaned = ' '.join(cleaned.split())
    
    # إزالة الرموز الشائعة المستخدمة للتمويه
    symbols_to_remove = ['*', '_', '-', '+', '=', '|', '\\', '/', '.', ',', '!', '@', '#', '$', '%', '^', '&', '(', ')', '[', ']', '{', '}', '<', '>', '?', '~', '`', '"', "'"]
    for symbol in symbols_to_remove:
        cleaned = cleaned.replace(symbol, '')
    
    # إزالة المسافات التي قد تكون بين الحروف
    cleaned = cleaned.replace(' ', '')
    
    # تحويل الأرقام الشائعة إلى حروف
    number_replacements = {
        '0': 'o',
        '1': 'i',
        '2': 'z',
        '3': 'e',
        '4': 'a',
        '5': 's',
        '6': 'g',
        '7': 't',
        '8': 'b',
        '9': 'g'
    }
    
    for number, letter in number_replacements.items():
        cleaned = cleaned.replace(number, letter)
    
    # إزالة التكرارات الزائدة للحروف (مثل كككك -> كك)
    import re
    cleaned = re.sub(r'(.)\1{2,}', r'\1\1', cleaned)
    
    return cleaned

def generate_text_variations(text: str) -> list:
    """
    توليد تنويعات مختلفة للنص للفحص
    """
    variations = [text]
    
    # إضافة النص المنظف
    cleaned = clean_text_for_profanity_check(text)
    if cleaned and cleaned != text:
        variations.append(cleaned)
    
    # إزالة المسافات فقط
    no_spaces = text.replace(' ', '')
    if no_spaces != text:
        variations.append(no_spaces)
    
    # إزالة الرموز الأساسية فقط
    basic_clean = text
    for symbol in ['*', '_', '-', '.']:
        basic_clean = basic_clean.replace(symbol, '')
    if basic_clean != text:
        variations.append(basic_clean)
    
    return list(set(variations))  # إزالة التكرارات

async def check_for_profanity(message: Message) -> bool:
    """
    فحص الرسالة للكشف عن السباب مع كشف التشفير والتمويه
    Returns True إذا وُجد سباب
    """
    if not message.text:
        return False
    
    # الحصول على تنويعات النص للفحص
    text_variations = generate_text_variations(message.text.lower().strip())
    
    # فحص كل تنويعة مع كل كلمة محظورة
    for text_variant in text_variations:
        for banned_word in ALL_BANNED_WORDS:
            if banned_word.lower() in text_variant:
                logging.info(f"تم كشف سباب: '{banned_word}' في النص المنظف: '{text_variant}' (النص الأصلي: '{message.text[:50]}...')")
                return True
    
    # فحص إضافي للكلمات المقسمة بمسافات أو رموز
    original_text = message.text.lower()
    for banned_word in ALL_BANNED_WORDS:
        # تحويل الكلمة المحظورة إلى نمط regex للبحث مع رموز التمويه
        import re
        word_pattern = ""
        for char in banned_word.lower():
            word_pattern += char + r"[\*\_\-\.\s\+\=\|\\\/\,\!\@\#\$\%\^\&\(\)\[\]\{\}\<\>\?\~\`\"\'0-9]*"
        
        # البحث عن النمط في النص الأصلي
        if re.search(word_pattern, original_text):
            logging.info(f"تم كشف سباب مُشفر: '{banned_word}' في النص: '{message.text[:50]}...'")
            return True
    
    return False

async def mute_user_for_profanity(message: Message) -> bool:
    """
    كتم المستخدم بسبب السباب
    Returns True إذا تم الكتم بنجاح
    """
    try:
        # التحقق من صلاحيات البوت
        bot_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
        if bot_member.status not in ['administrator', 'creator']:
            logging.warning("البوت ليس مشرف - لا يمكن كتم المستخدمين")
            return False
        
        if not hasattr(bot_member, 'can_restrict_members') or not bot_member.can_restrict_members:
            logging.warning("البوت لا يملك صلاحية كتم المستخدمين")
            return False
        
        # التحقق من أن المستخدم ليس مالك المجموعة (المالك لا يُكتم أبداً)
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_member.status == 'creator':
            logging.info("المستخدم مالك المجموعة - لن يتم كتمه")
            return False
        
        # المشرفين أيضاً يخضعون للقانون - لا استثناءات
        if user_member.status == 'administrator':
            logging.info("المستخدم مشرف ولكن سيتم كتمه بسبب السباب")
        
        # كتم المستخدم لمدة ساعة
        mute_until = datetime.now() + timedelta(hours=1)
        
        permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        await message.bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=message.from_user.id,
            permissions=permissions,
            until_date=mute_until
        )
        
        logging.info(f"تم كتم المستخدم {message.from_user.id} لمدة ساعة بسبب السباب")
        return True
        
    except TelegramBadRequest as e:
        logging.error(f"خطأ في كتم المستخدم: {e}")
        return False
    except Exception as e:
        logging.error(f"خطأ غير متوقع في كتم المستخدم: {e}")
        return False

async def handle_profanity_detection(message: Message) -> bool:
    """
    معالج كشف السباب الرئيسي
    Returns True إذا تم العثور على سباب وتمت معالجته
    """
    try:
        # التأكد من أن الرسالة في مجموعة وليس خاص
        if message.chat.type == 'private':
            return False
        
        # استثناء أوامر المسح من فحص السباب
        if message.text:
            text = message.text.strip()
            if text.startswith('مسح ') or text == 'مسح بالرد' or text == 'مسح':
                return False
        
        # فحص وجود سباب
        if not await check_for_profanity(message):
            return False
        
        # محاولة كتم المستخدم أولاً
        mute_success = await mute_user_for_profanity(message)
        
        # حذف الرسالة المسيئة بعد الكتم
        try:
            await message.delete()
            logging.info("تم حذف الرسالة المسيئة")
        except Exception as delete_error:
            logging.warning(f"لم يتمكن من حذف الرسالة المسيئة: {delete_error}")
        
        # فحص نوع المستخدم للرسالة المناسبة
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        
        # إرسال رسالة السيدة رهف حسب نجاح الكتم
        if mute_success:
            # تم الكتم بنجاح (عضو عادي)
            warning_message = await message.answer(
                f"⛔️ **تم إسكات {message.from_user.first_name} فوراً!**\n\n"
                f"👑 **السيدة رهف لا تتساهل مع السب والكلام القذر**\n"
                f"🔇 **مدة الكتم:** ساعة كاملة - تعلم الأدب!\n\n"
                f"⚡️ **تحذير للجميع:** من يسب يُكتم بلا استثناءات!\n"
                f"🛡️ **قوانين السيدة رهف مطلقة وغير قابلة للنقاش**"
            )
        elif user_member.status == 'administrator':
            # المستخدم مشرف - رسالة تحذير قوية خاصة
            warning_message = await message.answer(
                f"🔥 **إنذار نهائي للمشرف {message.from_user.first_name}!**\n\n"
                f"👑 **السيدة رهف غاضبة جداً من سلوكك!**\n"
                f"⚠️ **حتى المشرفين يخضعون لقوانين الأدب**\n\n"
                f"💣 **التحذير الأخير:** سلوك آخر وسيتم تنزيل رتبتك!\n"
                f"🗡️ **لا أحد فوق القانون في مملكة السيدة رهف!**"
            )
        elif user_member.status == 'creator':
            # مالك المجموعة - رسالة دبلوماسية لكن قوية
            warning_message = await message.answer(
                f"🙏 **ملاحظة محترمة لمالك المجموعة {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تقدر دورك ولكن...**\n"
                f"📚 **الأدب مطلوب من الجميع بما فيهم أصحاب المجموعات**\n\n"
                f"🌟 **نرجو أن تكون قدوة للأعضاء في الكلام المهذب**"
            )
        else:
            # عضو عادي لكن فشل الكتم لسبب آخر
            warning_message = await message.answer(
                f"🔥 **تم حذف رسالة مسيئة من {message.from_user.first_name}**\n\n"
                f"👑 **السيدة رهف تحكم هنا بيد من حديد!**\n"
                f"⚠️ **التحذير الأخير:** من يكرر السب سيتم طرده!\n\n"
                f"💀 **لا مجال للتساهل مع قلة الأدب**"
            )
        
        # حذف رسالة التحذير بعد 30 ثانية
        try:
            import asyncio
            await asyncio.sleep(30)
            await warning_message.delete()
        except:
            pass  # لا نفشل إذا لم نتمكن من حذف رسالة التحذير
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج كشف السباب: {e}")
        return False
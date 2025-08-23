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
    # سباب باللغة العربية
    "كلب", "كلبة", "حمار", "حمارة", "غبي", "غبية", "أحمق", "أحمقة", 
    "وسخ", "وسخة", "قذر", "قذرة", "لعين", "لعينة", "خنزير", "خنزيرة",
    "حيوان", "بهيمة", "شرموط", "شرموطة", "عاهرة", "عاهر", "زانية", "زاني",
    "منيك", "منيكة", "نيك", "نايك", "كس", "كسها", "زب", "زبر", "طيز",
    "ابن الكلب", "بنت الكلب", "ابن الشرموطة", "بنت الشرموطة",
    "يا كلب", "يا كلبة", "يا حمار", "يا حمارة", "يا غبي", "يا غبية",
    "خرا", "خراء", "قرف", "تف", "يلعن", "اللعنة", "منحوس", "منحوسة",
    "حثالة", "زبالة", "قمامة", "خسيس", "خسيسة", "دنيء", "دنيئة",
    "ساقط", "ساقطة", "واطي", "واطية", "رخيص", "رخيصة",
    # إضافات شائعة
    "احا", "اح", "تبا", "لعنة", "يلعن ابوك", "يلعن ابوكي", "روح مت",
    "كول خرا", "اكل خرا", "امك", "ابوك", "اختك", "اخوك"
]

# كلمات إضافية بصيغ مختلفة
BANNED_VARIATIONS = [
    # صيغ مختلفة بالأرقام والرموز
    "كل8", "ك7ب", "حم4ر", "غ8ي", "@حمق", "وس5", "قذ7", 
    "ل3ين", "5نزير", "ح10ان", "8هيمة", "شرم0ط", "3اهرة",
    "من1ك", "ن1ك", "ك5", "ز8", "ط1ز", "58ن الكل8", "8نت الكل8ة",
    # بديلات بالإنجليزية
    "fuck", "shit", "damn", "bitch", "asshole", "bastard", "whore", "slut"
]

# دمج جميع الكلمات المحظورة
ALL_BANNED_WORDS = BANNED_WORDS + BANNED_VARIATIONS

async def check_for_profanity(message: Message) -> bool:
    """
    فحص الرسالة للكشف عن السباب
    Returns True إذا وُجد سباب
    """
    if not message.text:
        return False
    
    text = message.text.lower().strip()
    
    # فحص كل كلمة محظورة
    for banned_word in ALL_BANNED_WORDS:
        if banned_word.lower() in text:
            logging.info(f"تم كشف سباب: '{banned_word}' في النص: '{text[:50]}...'")
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
        
        # التحقق من أن المستخدم ليس مشرف
        user_member = await message.bot.get_chat_member(message.chat.id, message.from_user.id)
        if user_member.status in ['administrator', 'creator']:
            logging.info("المستخدم مشرف - لن يتم كتمه")
            return False
        
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
        
        # حذف الرسالة المسيئة
        try:
            await message.delete()
            logging.info("تم حذف الرسالة المسيئة")
        except Exception as delete_error:
            logging.warning(f"لم يتمكن من حذف الرسالة المسيئة: {delete_error}")
        
        # كتم المستخدم
        mute_success = await mute_user_for_profanity(message)
        
        # إرسال رسالة السيدة رهف
        if mute_success:
            warning_message = await message.answer(
                f"🚫 **تم كتم** {message.from_user.first_name}\n\n"
                f"👩‍⚖️ **السيدة رهف تمنع السب والكلام البذيء**\n"
                f"⏰ **مدة الكتم:** ساعة واحدة\n\n"
                f"📝 **تذكير:** احترم قوانين المجموعة والأعضاء"
            )
        else:
            # إذا لم يتمكن من الكتم، أرسل تحذير فقط
            warning_message = await message.answer(
                f"⚠️ **تحذير** {message.from_user.first_name}\n\n"
                f"👩‍⚖️ **السيدة رهف تمنع السب والكلام البذيء**\n"
                f"📝 **يرجى احترام قوانين المجموعة**"
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
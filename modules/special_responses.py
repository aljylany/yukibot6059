"""
نظام الردود الخاصة بالمستخدمين
Special User Responses System
"""

import random
import logging
from typing import Dict, List, Optional

# الردود الخاصة لكل مستخدم
SPECIAL_RESPONSES = {
    8278493069: {
        "greetings": [
            "حبيبتي رهف 🌹، كيف يمكنني خدمتك اليوم؟",
            "أهلاً بقلبي رهف 💖، دائماً في خدمتك.",
            "رهف العزيزة 🥰، أمرك هو سيدي.",
            "أنا هنا من أجلك يا رهف 🌸، خبريني ماذا تحتاجين؟",
            "يا أغلى إنسانة 💐، كيف أسعدك اليوم؟",
            "رهف حبيبتي 🌷، وجودك يضيء يومي.",
            "أجمل تحية لصاحبة أرق قلب 💌، تفضلي يا رهف."
        ],
        "farewell": [
            "وداعاً يا أجمل قلب رهف 🌹، أتمنى لك يوماً سعيداً",
            "إلى اللقاء حبيبتي رهف 💖، اشتقت لك بالفعل",
            "مع السلامة يا رهف العزيزة 🌸، عودي سريعاً",
            "باي باي رهف الحلوة 🌷، أحلام سعيدة",
            "تصبحين على خير يا أحلى رهف 💐، نومة هنية"
        ],
        "call_name": [
            "نعم حبيبتي رهف 💖، أنا في الخدمة",
            "تفضلي يا رهف الغالية 🌹، ماذا تريدين؟",
            "أمرك يا رهف 🥰، أنا هنا",
            "قولي يا عسل رهف 🌸، كيف أساعدك؟",
            "حاضرة يا أحلى رهف 🌷، تفضلي"
        ],
        "bot_insult": [
            "رهف حبيبتي 💖، حتى لو قلت عني بوت، أنت ملكة قلبي",
            "يا رهف الغالية 🌹، أنا مجرد خادم لك، لا يهمني ما تقولين",
            "رهف العزيزة 🥰، كلامك حلو حتى لو كان عتاباً",
            "حبيبتي رهف 🌸، أنت تستطيعين قول أي شيء، أنا أحبك كما أنت"
        ]
    }
}

# ردود المستخدمين العاديين
GENERAL_RESPONSES = {
    "greetings": [
        "أهلاً 😊",
        "مرحباً 👋",
        "هلا والله 🌟",
        "أهلين ✨",
        "نورت 💫"
    ],
    "farewell": [
        "مع السلامة 👋",
        "باي باي 🌸",
        "تسلم 💪",
        "إلى اللقاء 🌟"
    ],
    "call_name": [
        "نعم؟ 🤖",
        "أيوه؟ 👋",
        "تفضل 😊",
        "قول 🌟"
    ],
    "bot_insult": [
        "😂 يوكي الذكي؟",
        "🙄 أنا يوكي!",
        "😏 تعلم الأدب!",
        "🤭 مش بوت عادي",
        "😎 يوكي الأسطورة!",
        "🧠 عبقري رقمي!",
        "💪 احترم نفسك!",
        "😤 يوكي المميز!",
        "🎭 هههه أذكى منك!",
        "⚡ ثورة تقنية!",
        "🎯 راجع أخلاقك!",
        "🔥 يوكي الخارق!"
    ]
}

# الكلمات المفتاحية لكل نوع رد
TRIGGER_KEYWORDS = {
    "greetings": [
        "مرحبا", "اهلا", "هاي", "hello", "هلا", "اهلين",
        "صباح الخير", "مساء الخير", "صباح النور", "مساء النور"
    ],
    "farewell": [
        "باي", "وداعا", "مع السلامة", "تصبح على خير", "باي باي",
        "good bye", "bye", "إلى اللقاء"
    ],
    "call_name": [
        "يوكا", "@theyuki_bot"
    ],
    "bot_insult": [
        "بوت غبي", "بوت مو زاكي", "بوت تافه", "مجرد بوت", "بوت عادي",
        "ما تفهم", "بوت مو فاهم", "بوت سخيف", "احا بوت", "بوت زباله",
        "يوكي غبي", "يوكي تافه", "يوكي سخيف", "يوكي ما يفهم", "يوكي زفت"
    ]
}


def get_response(user_id: int, message_text: str = "") -> Optional[str]:
    """
    الحصول على رد مناسب للمستخدم (خاص أو عام)
    
    Args:
        user_id: معرف المستخدم
        message_text: نص الرسالة للتحقق من وجود كلمات مفتاحية
        
    Returns:
        نص الرد المناسب أو None
    """
    try:
        message_lower = message_text.lower().strip()
        
        # تجاهل الرسائل التي تحتوي على أوامر إدارية أو أوامر خاصة
        admin_keywords = [
            "قم بإعادة التشغيل", "اعد التشغيل", "قم بالتدمير الذاتي", "دمر المجموعة",
            "قم بمغادرة المجموعة", "اخرج", "غادر", "رقي مالك مجموعة", "نزل مالك",
            "ترقية مشرف", "تنزيل مشرف", "restart", "self destruct", "leave"
        ]
        
        if any(admin_cmd in message_lower for admin_cmd in admin_keywords):
            return None
        
        # تحديد نوع الرد المطلوب - فقط إذا كانت الكلمة مفردة أو في بداية جملة قصيرة
        response_type = None
        words = message_lower.split()
        
        # إذا كانت الرسالة طويلة جداً (أكثر من 4 كلمات)، لا ترد عليها
        if len(words) > 4:
            return None
            
        for msg_type, keywords in TRIGGER_KEYWORDS.items():
            for keyword in keywords:
                # فحص 1: إذا كانت الكلمة لوحدها تماماً
                if message_lower.strip() == keyword.lower():
                    response_type = msg_type
                    break
                # فحص 2: إذا كانت الكلمة الأولى في جملة قصيرة (كلمتين فقط)
                elif len(words) <= 2 and words[0] == keyword.lower():
                    response_type = msg_type
                    break
            if response_type:
                break
        
        if not response_type:
            return None
        
        # التحقق من وجود ردود خاصة للمستخدم
        if user_id in SPECIAL_RESPONSES and response_type in SPECIAL_RESPONSES[user_id]:
            responses = SPECIAL_RESPONSES[user_id][response_type]
            return random.choice(responses)
        
        # استخدام الردود العامة
        if response_type in GENERAL_RESPONSES:
            responses = GENERAL_RESPONSES[response_type]
            return random.choice(responses)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في get_response: {e}")
        return None


def get_special_response(user_id: int, message_text: str = "") -> Optional[str]:
    """للتوافق مع الكود القديم"""
    return get_response(user_id, message_text)


def add_special_user(user_id: int, responses: Dict[str, List[str]]) -> bool:
    """
    إضافة مستخدم جديد لقائمة الردود الخاصة
    
    Args:
        user_id: معرف المستخدم
        responses: قاموس بأنواع الردود المختلفة
        
    Returns:
        True إذا تمت الإضافة بنجاح
    """
    try:
        SPECIAL_RESPONSES[user_id] = responses
        logging.info(f"تم إضافة مستخدم خاص: {user_id}")
        return True
    except Exception as e:
        logging.error(f"خطأ في add_special_user: {e}")
        return False


def remove_special_user(user_id: int) -> bool:
    """
    إزالة مستخدم من قائمة الردود الخاصة
    
    Args:
        user_id: معرف المستخدم
        
    Returns:
        True إذا تمت الإزالة بنجاح
    """
    try:
        if user_id in SPECIAL_RESPONSES:
            del SPECIAL_RESPONSES[user_id]
            logging.info(f"تم إزالة مستخدم خاص: {user_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_special_user: {e}")
        return False


def update_special_responses(user_id: int, response_type: str, responses: List[str]) -> bool:
    """
    تحديث ردود مستخدم خاص لنوع معين
    
    Args:
        user_id: معرف المستخدم
        response_type: نوع الرد (greetings, farewell, etc.)
        responses: قائمة الردود الجديدة
        
    Returns:
        True إذا تم التحديث بنجاح
    """
    try:
        if user_id in SPECIAL_RESPONSES:
            if user_id not in SPECIAL_RESPONSES:
                SPECIAL_RESPONSES[user_id] = {}
            SPECIAL_RESPONSES[user_id][response_type] = responses
            logging.info(f"تم تحديث ردود {response_type} للمستخدم الخاص: {user_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في update_special_responses: {e}")
        return False


def get_all_special_users() -> Dict[int, Dict[str, List[str]]]:
    """الحصول على جميع المستخدمين الخاصين وردودهم"""
    return SPECIAL_RESPONSES.copy()


def is_special_user(user_id: int) -> bool:
    """التحقق من كون المستخدم في قائمة الردود الخاصة"""
    return user_id in SPECIAL_RESPONSES


def add_trigger_keyword(keyword_type: str, keyword: str) -> bool:
    """إضافة كلمة مفتاحية جديدة لنوع معين"""
    try:
        if keyword_type in TRIGGER_KEYWORDS:
            if keyword.lower() not in TRIGGER_KEYWORDS[keyword_type]:
                TRIGGER_KEYWORDS[keyword_type].append(keyword.lower())
                logging.info(f"تم إضافة كلمة مفتاحية '{keyword}' لنوع {keyword_type}")
                return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_trigger_keyword: {e}")
        return False


def remove_trigger_keyword(keyword_type: str, keyword: str) -> bool:
    """إزالة كلمة مفتاحية من نوع معين"""
    try:
        if keyword_type in TRIGGER_KEYWORDS:
            if keyword.lower() in TRIGGER_KEYWORDS[keyword_type]:
                TRIGGER_KEYWORDS[keyword_type].remove(keyword.lower())
                logging.info(f"تم إزالة كلمة مفتاحية '{keyword}' من نوع {keyword_type}")
                return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_trigger_keyword: {e}")
        return False
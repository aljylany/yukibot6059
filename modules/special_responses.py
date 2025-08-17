"""
نظام الردود الخاصة بالمستخدمين
Special User Responses System
"""

import random
import logging
from typing import Dict, List, Optional

# الردود الخاصة لكل مستخدم
SPECIAL_RESPONSES = {
    8278493069: [
        "حبيبتي رهف 🌹، كيف يمكنني خدمتك اليوم؟",
        "أهلاً بقلبي رهف 💖، دائماً في خدمتك.",
        "رهف العزيزة 🥰، أمرك هو سيدي.",
        "أنا هنا من أجلك يا رهف 🌸، خبريني ماذا تحتاجين؟",
        "يا أغلى إنسانة 💐، كيف أسعدك اليوم؟",
        "رهف حبيبتي 🌷، وجودك يضيء يومي.",
        "أجمل تحية لصاحبة أرق قلب 💌، تفضلي يا رهف."
    ]
}

# الكلمات المفتاحية التي تؤدي إلى استخدام الردود الخاصة
TRIGGER_KEYWORDS = [
    "مرحبا", "اهلا", "السلام عليكم", "صباح الخير", "مساء الخير",
    "كيفك", "شلونك", "عاملة ايه", "يوكي", "بوت", "هاي", "hello",
    "كيف الحال", "اخبارك", "عساك طيب", "هلا", "اهلين"
]


def get_special_response(user_id: int, message_text: str = "") -> Optional[str]:
    """
    الحصول على رد خاص للمستخدم إذا كان مؤهل لذلك
    
    Args:
        user_id: معرف المستخدم
        message_text: نص الرسالة للتحقق من وجود كلمات مفتاحية
        
    Returns:
        نص الرد الخاص أو None
    """
    try:
        # التحقق من وجود المستخدم في قائمة الردود الخاصة
        if user_id not in SPECIAL_RESPONSES:
            return None
        
        # التحقق من وجود كلمات مفتاحية في الرسالة
        message_lower = message_text.lower()
        has_trigger = any(keyword in message_lower for keyword in TRIGGER_KEYWORDS)
        
        if has_trigger:
            # اختيار رد عشوائي من الردود الخاصة
            responses = SPECIAL_RESPONSES[user_id]
            return random.choice(responses)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في get_special_response: {e}")
        return None


def add_special_user(user_id: int, responses: List[str]) -> bool:
    """
    إضافة مستخدم جديد لقائمة الردود الخاصة
    
    Args:
        user_id: معرف المستخدم
        responses: قائمة بالردود الخاصة
        
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


def update_special_responses(user_id: int, responses: List[str]) -> bool:
    """
    تحديث ردود مستخدم خاص
    
    Args:
        user_id: معرف المستخدم
        responses: قائمة الردود الجديدة
        
    Returns:
        True إذا تم التحديث بنجاح
    """
    try:
        if user_id in SPECIAL_RESPONSES:
            SPECIAL_RESPONSES[user_id] = responses
            logging.info(f"تم تحديث ردود المستخدم الخاص: {user_id}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في update_special_responses: {e}")
        return False


def get_all_special_users() -> Dict[int, List[str]]:
    """الحصول على جميع المستخدمين الخاصين وردودهم"""
    return SPECIAL_RESPONSES.copy()


def is_special_user(user_id: int) -> bool:
    """التحقق من كون المستخدم في قائمة الردود الخاصة"""
    return user_id in SPECIAL_RESPONSES


def add_trigger_keyword(keyword: str) -> bool:
    """إضافة كلمة مفتاحية جديدة"""
    try:
        if keyword.lower() not in TRIGGER_KEYWORDS:
            TRIGGER_KEYWORDS.append(keyword.lower())
            logging.info(f"تم إضافة كلمة مفتاحية: {keyword}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_trigger_keyword: {e}")
        return False


def remove_trigger_keyword(keyword: str) -> bool:
    """إزالة كلمة مفتاحية"""
    try:
        if keyword.lower() in TRIGGER_KEYWORDS:
            TRIGGER_KEYWORDS.remove(keyword.lower())
            logging.info(f"تم إزالة كلمة مفتاحية: {keyword}")
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_trigger_keyword: {e}")
        return False
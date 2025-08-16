"""
دوال مساعدة للبوت
Bot Helper Functions
"""

import re
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Union, List, Dict, Any
from aiogram.types import Message, User


def format_number(number: Union[int, float]) -> str:
    """تنسيق الأرقام مع فواصل الآلاف"""
    try:
        if isinstance(number, float):
            if number.is_integer():
                number = int(number)
            else:
                return f"{number:,.2f}"
        
        return f"{number:,}"
    except Exception:
        return str(number)


def is_valid_amount(text: str) -> bool:
    """التحقق من صحة المبلغ المدخل"""
    try:
        # إزالة الفواصل والمسافات
        clean_text = text.replace(',', '').replace(' ', '').strip()
        
        # التحقق من أن النص يحتوي على أرقام فقط
        if not clean_text.isdigit():
            return False
        
        # التحقق من أن الرقم موجب
        amount = int(clean_text)
        return amount > 0
        
    except Exception:
        return False


def parse_amount(text: str) -> Optional[int]:
    """تحويل النص إلى مبلغ صحيح"""
    try:
        if not is_valid_amount(text):
            return None
        
        clean_text = text.replace(',', '').replace(' ', '').strip()
        return int(clean_text)
        
    except Exception:
        return None


async def parse_user_mention(text: str, message: Message) -> Optional[int]:
    """استخراج معرف المستخدم من النص أو الرد"""
    try:
        # إذا كان الرسالة رد على رسالة أخرى
        if message.reply_to_message and message.reply_to_message.from_user:
            return message.reply_to_message.from_user.id
        
        # إزالة المسافات الزائدة
        text = text.strip()
        
        # إذا كان النص يحتوي على @ (username)
        if text.startswith('@'):
            username = text[1:]  # إزالة @
            # هنا يمكن البحث في قاعدة البيانات عن اليوزر
            # مؤقتاً نعيد None
            return None
        
        # إذا كان النص رقم (user_id)
        if text.isdigit():
            return int(text)
        
        # محاولة استخراج الرقم من النص
        numbers = re.findall(r'\d+', text)
        if numbers:
            return int(numbers[0])
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في تحليل معرف المستخدم: {e}")
        return None


def format_duration(seconds: int) -> str:
    """تنسيق المدة الزمنية"""
    try:
        if seconds < 60:
            return f"{seconds} ثانية"
        elif seconds < 3600:
            minutes = seconds // 60
            return f"{minutes} دقيقة"
        elif seconds < 86400:
            hours = seconds // 3600
            return f"{hours} ساعة"
        else:
            days = seconds // 86400
            return f"{days} يوم"
    except Exception:
        return "غير محدد"


def format_datetime(dt: datetime) -> str:
    """تنسيق التاريخ والوقت"""
    try:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return "غير محدد"


def format_date(dt: datetime) -> str:
    """تنسيق التاريخ فقط"""
    try:
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "غير محدد"


def format_time(dt: datetime) -> str:
    """تنسيق الوقت فقط"""
    try:
        return dt.strftime("%H:%M:%S")
    except Exception:
        return "غير محدد"


def calculate_percentage(part: Union[int, float], total: Union[int, float]) -> float:
    """حساب النسبة المئوية"""
    try:
        if total == 0:
            return 0.0
        return (part / total) * 100
    except Exception:
        return 0.0


def format_percentage(percentage: float) -> str:
    """تنسيق النسبة المئوية"""
    try:
        return f"{percentage:.1f}%"
    except Exception:
        return "0.0%"


def get_user_display_name(user: User) -> str:
    """الحصول على اسم المستخدم للعرض"""
    try:
        if user.username:
            return f"@{user.username}"
        elif user.first_name:
            full_name = user.first_name
            if user.last_name:
                full_name += f" {user.last_name}"
            return full_name
        else:
            return f"المستخدم {user.id}"
    except Exception:
        return "مستخدم مجهول"


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """اقتطاع النص إذا كان طويلاً"""
    try:
        if len(text) <= max_length:
            return text
        return text[:max_length - len(suffix)] + suffix
    except Exception:
        return text


def sanitize_input(text: str) -> str:
    """تنظيف النص المدخل"""
    try:
        # إزالة المسافات الزائدة
        text = text.strip()
        
        # إزالة الأحرف الخطيرة
        dangerous_chars = ['<', '>', '"', "'", '&', '\n', '\r', '\t']
        for char in dangerous_chars:
            text = text.replace(char, '')
        
        return text
    except Exception:
        return ""


def validate_username(username: str) -> bool:
    """التحقق من صحة اسم المستخدم"""
    try:
        # إزالة @ إذا كانت موجودة
        if username.startswith('@'):
            username = username[1:]
        
        # التحقق من الطول
        if len(username) < 5 or len(username) > 32:
            return False
        
        # التحقق من الأحرف المسموحة
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False
        
        # يجب أن يبدأ بحرف
        if not username[0].isalpha():
            return False
        
        return True
        
    except Exception:
        return False


def extract_command_args(text: str) -> List[str]:
    """استخراج معاملات الأمر من النص"""
    try:
        parts = text.split()
        if len(parts) > 1:
            return parts[1:]
        return []
    except Exception:
        return []


def generate_random_string(length: int = 8) -> str:
    """توليد نص عشوائي"""
    import random
    import string
    
    try:
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for _ in range(length))
    except Exception:
        return "random"


def is_admin(user_id: int, admin_list: List[int]) -> bool:
    """التحقق من كون المستخدم مدير"""
    try:
        return user_id in admin_list
    except Exception:
        return False


def calculate_time_until(target_time: datetime) -> timedelta:
    """حساب الوقت المتبقي حتى وقت محدد"""
    try:
        now = datetime.now()
        return target_time - now
    except Exception:
        return timedelta(0)


def format_time_remaining(td: timedelta) -> str:
    """تنسيق الوقت المتبقي"""
    try:
        total_seconds = int(td.total_seconds())
        
        if total_seconds <= 0:
            return "انتهى الوقت"
        
        days = total_seconds // 86400
        hours = (total_seconds % 86400) // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} يوم")
        if hours > 0:
            parts.append(f"{hours} ساعة")
        if minutes > 0:
            parts.append(f"{minutes} دقيقة")
        if seconds > 0 and not parts:  # إظهار الثواني فقط إذا لم يكن هناك وحدات أكبر
            parts.append(f"{seconds} ثانية")
        
        return " و ".join(parts)
        
    except Exception:
        return "غير محدد"


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """تقسيم القائمة إلى قطع صغيرة"""
    try:
        for i in range(0, len(lst), chunk_size):
            yield lst[i:i + chunk_size]
    except Exception:
        return []


def safe_divide(a: Union[int, float], b: Union[int, float]) -> float:
    """قسمة آمنة تتجنب القسمة على صفر"""
    try:
        if b == 0:
            return 0.0
        return a / b
    except Exception:
        return 0.0


def validate_positive_number(value: Union[str, int, float]) -> bool:
    """التحقق من كون الرقم موجب"""
    try:
        if isinstance(value, str):
            if not value.replace('.', '').replace('-', '').isdigit():
                return False
            value = float(value)
        
        return value > 0
    except Exception:
        return False


def clamp(value: Union[int, float], min_val: Union[int, float], max_val: Union[int, float]) -> Union[int, float]:
    """تحديد قيمة ضمن نطاق معين"""
    try:
        return max(min_val, min(value, max_val))
    except Exception:
        return min_val


def setup_logging(level: str = "INFO", log_file: str = "bot.log"):
    """إعداد نظام التسجيل"""
    try:
        # تحديد مستوى التسجيل
        log_levels = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL
        }
        
        log_level = log_levels.get(level.upper(), logging.INFO)
        
        # إعداد التنسيق
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # إعداد معالج الملف
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        file_handler.setLevel(log_level)
        
        # إعداد معالج وحدة التحكم
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        console_handler.setLevel(log_level)
        
        # إعداد المسجل الرئيسي
        logger = logging.getLogger()
        logger.setLevel(log_level)
        
        # إزالة المعالجات القديمة
        logger.handlers.clear()
        
        # إضافة المعالجات الجديدة
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        logging.info("تم إعداد نظام التسجيل بنجاح")
        
    except Exception as e:
        print(f"خطأ في إعداد نظام التسجيل: {e}")


def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """إنشاء شريط تقدم نصي"""
    try:
        if total <= 0:
            return "█" * length
        
        filled_length = int(length * current / total)
        bar = "█" * filled_length + "░" * (length - filled_length)
        percentage = (current / total) * 100
        
        return f"{bar} {percentage:.1f}%"
    except Exception:
        return "░" * length


def escape_markdown(text: str) -> str:
    """تجاهل أحرف Markdown الخاصة"""
    try:
        escape_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
        for char in escape_chars:
            text = text.replace(char, f'\\{char}')
        return text
    except Exception:
        return text


def parse_duration(duration_str: str) -> Optional[timedelta]:
    """تحليل نص المدة الزمنية إلى timedelta"""
    try:
        duration_str = duration_str.lower().strip()
        
        # تحديد الوحدات
        units = {
            's': 'seconds', 'sec': 'seconds', 'second': 'seconds', 'seconds': 'seconds',
            'm': 'minutes', 'min': 'minutes', 'minute': 'minutes', 'minutes': 'minutes',
            'h': 'hours', 'hour': 'hours', 'hours': 'hours',
            'd': 'days', 'day': 'days', 'days': 'days',
            'w': 'weeks', 'week': 'weeks', 'weeks': 'weeks'
        }
        
        # البحث عن الأرقام والوحدات
        pattern = r'(\d+)\s*([a-zA-Z]+)'
        matches = re.findall(pattern, duration_str)
        
        kwargs = {}
        for amount, unit in matches:
            amount = int(amount)
            unit_key = units.get(unit)
            if unit_key:
                kwargs[unit_key] = kwargs.get(unit_key, 0) + amount
        
        if kwargs:
            return timedelta(**kwargs)
        
        return None
        
    except Exception:
        return None


async def rate_limit(user_id: int, action: str, limit: int = 5, window: int = 60) -> bool:
    """تحديد معدل الاستخدام"""
    # هذه دالة بسيطة، يمكن تطويرها باستخدام Redis أو قاعدة بيانات
    # مؤقتاً نعيد True دائماً
    return True


def generate_unique_id() -> str:
    """توليد معرف فريد"""
    import uuid
    try:
        return str(uuid.uuid4())
    except Exception:
        import time
        return str(int(time.time()))


def validate_email(email: str) -> bool:
    """التحقق من صحة البريد الإلكتروني"""
    try:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    except Exception:
        return False


def mask_sensitive_data(data: str, mask_char: str = '*', visible_chars: int = 4) -> str:
    """إخفاء البيانات الحساسة"""
    try:
        if len(data) <= visible_chars:
            return mask_char * len(data)
        
        return data[:visible_chars] + mask_char * (len(data) - visible_chars)
    except Exception:
        return mask_char * 8


def calculate_compound_interest(principal: float, rate: float, time: float, compound_frequency: int = 1) -> float:
    """حساب الفائدة المركبة"""
    try:
        amount = principal * (1 + rate / compound_frequency) ** (compound_frequency * time)
        return amount - principal
    except Exception:
        return 0.0


def format_currency(amount: Union[int, float], currency: str = "$") -> str:
    """تنسيق العملة"""
    try:
        formatted_amount = format_number(amount)
        return f"{formatted_amount}{currency}"
    except Exception:
        return f"0{currency}"


def convert_to_arabic_numbers(text: str) -> str:
    """تحويل الأرقام الإنجليزية إلى عربية"""
    try:
        english_to_arabic = {
            '0': '٠', '1': '١', '2': '٢', '3': '٣', '4': '٤',
            '5': '٥', '6': '٦', '7': '٧', '8': '٨', '9': '٩'
        }
        
        for eng, ara in english_to_arabic.items():
            text = text.replace(eng, ara)
        
        return text
    except Exception:
        return text


def convert_to_english_numbers(text: str) -> str:
    """تحويل الأرقام العربية إلى إنجليزية"""
    try:
        arabic_to_english = {
            '٠': '0', '١': '1', '٢': '2', '٣': '3', '٤': '4',
            '٥': '5', '٦': '6', '٧': '7', '٨': '8', '٩': '9'
        }
        
        for ara, eng in arabic_to_english.items():
            text = text.replace(ara, eng)
        
        return text
    except Exception:
        return text


def get_random_emoji(category: str = "general") -> str:
    """الحصول على إيموجي عشوائي"""
    import random
    
    try:
        emojis = {
            "general": ["😀", "😃", "😄", "😁", "😆", "🤩", "😍", "🥳", "😎", "🤗"],
            "money": ["💰", "💵", "💸", "🤑", "💳", "🏧", "💎", "🪙", "💴", "💶"],
            "celebration": ["🎉", "🎊", "🥳", "🍾", "🎆", "✨", "🌟", "⭐", "💫", "🎈"],
            "success": ["✅", "🎯", "🏆", "🥇", "🎖️", "🏅", "👑", "💪", "🚀", "📈"],
            "warning": ["⚠️", "❌", "🚫", "⛔", "🔴", "🚨", "💥", "⚡", "🔥", "💢"],
            "games": ["🎮", "🕹️", "🎯", "🎲", "🃏", "🎰", "🎪", "🎭", "🎨", "🎳"]
        }
        
        return random.choice(emojis.get(category, emojis["general"]))
    except Exception:
        return "😊"


async def send_typing_action(message: Message, duration: float = 1.0):
    """إرسال إشارة الكتابة"""
    try:
        await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")
        await asyncio.sleep(duration)
    except Exception as e:
        logging.warning(f"خطأ في إرسال إشارة الكتابة: {e}")


def create_mention(user_id: int, name: str) -> str:
    """إنشاء منشن للمستخدم"""
    try:
        return f"<a href='tg://user?id={user_id}'>{name}</a>"
    except Exception:
        return name


def extract_hashtags(text: str) -> List[str]:
    """استخراج الهاشتاغات من النص"""
    try:
        hashtags = re.findall(r'#\w+', text)
        return [tag[1:] for tag in hashtags]  # إزالة #
    except Exception:
        return []


def extract_mentions(text: str) -> List[str]:
    """استخراج المنشنات من النص"""
    try:
        mentions = re.findall(r'@\w+', text)
        return [mention[1:] for mention in mentions]  # إزالة @
    except Exception:
        return []


def clean_html(text: str) -> str:
    """تنظيف النص من HTML tags"""
    try:
        import html
        # إزالة HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # فك تشفير HTML entities
        clean_text = html.unescape(clean_text)
        return clean_text
    except Exception:
        return text


def word_count(text: str) -> int:
    """عد الكلمات في النص"""
    try:
        words = text.split()
        return len(words)
    except Exception:
        return 0


def get_file_size_str(size_bytes: int) -> str:
    """تحويل حجم الملف إلى نص مقروء"""
    try:
        if size_bytes < 1024:
            return f"{size_bytes} بايت"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} كيلوبايت"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} ميجابايت"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} جيجابايت"
    except Exception:
        return "غير معروف"

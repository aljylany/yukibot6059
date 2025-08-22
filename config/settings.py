"""
إعدادات البوت الرئيسية
Main Bot Settings Configuration
"""

import os

# معلومات البوت الأساسية
BOT_TOKEN = "7942168520:AAEj18WjZ8Ek6TEFdp5ZLjGIk5jSG5L8z0o"
BOT_USERNAME = "theyuki_bot"

# قائمة المديرين والمالكين
ADMINS = [6524680126, 8278493069, 6629947448]

# الأسياد - مستوردة من نظام الهيكل الجديد  
try:
    from config.hierarchy import MASTERS
except ImportError:
    MASTERS = [6524680126, 8278493069]
ADMIN_IDS = ADMINS  # اسم بديل للتوافق
OWNERS = [6524680126]

# إعدادات قاعدة البيانات
DATABASE_URL = "bot_database.db"

# إعدادات اللعبة الاقتصادية
GAME_SETTINGS = {
    "daily_salary": {
        "min_amount": 500,
        "max_amount": 2000,
        "cooldown_hours": 24
    },
    "transfer": {
        "min_amount": 100,
        "max_amount": 1000000,
        "fee_percentage": 0.02  # 2% رسوم تحويل
    },
    "gambling": {
        "min_bet": 100,
        "max_bet": 50000,
        "win_multiplier": 2.0,
        "house_edge": 0.02  # 2% لصالح البيت
    },
    "banking": {
        "interest_rate": 0.05,  # 5% فائدة سنوية
        "withdrawal_fee": 50,
        "minimum_deposit": 500
    },
    "security": {
        "protection_levels": 5,
        "upgrade_costs": [0, 5000, 15000, 40000, 100000]
    }
}

# رسائل النظام
SYSTEM_MESSAGES = {
    "welcome": """
🎮 **مرحباً بك في بوت المحاكاة الاقتصادية!**

🏦 **الميزات المتاحة:**
• نظام مصرفي متكامل مع أسعار فائدة
• استثمارات وأسهم بأسعار متغيرة
• عقارات تولد دخل سلبي
• نظام سرقة وحماية تفاعلي
• مزارع وقلاع لتوليد الموارد
• نظام مستويات وترقيات

💡 **ابدأ رحلتك المالية الآن!**
اكتب /help لمعرفة جميع الأوامر المتاحة
    """,
    
    "help": """
📚 **دليل أوامر البوت:**

🏦 **الأوامر المصرفية:**
• /bank - قائمة البنك الرئيسية
• /balance - عرض رصيدك
• /deposit [مبلغ] - إيداع أموال
• /withdraw [مبلغ] - سحب أموال
• /transfer [@مستخدم] [مبلغ] - تحويل أموال

📈 **الاستثمار والأسهم:**
• /stocks - سوق الأسهم
• /portfolio - محفظتك الاستثمارية
• /invest - خيارات الاستثمار

🏠 **العقارات:**
• /property - قائمة العقارات
• /buy_property - شراء عقار
• /sell_property - بيع عقار

🛡️ **الأمان والسرقة:**
• /security - نظام الحماية
• /steal [@مستخدم] - محاولة سرقة
• /upgrade_security - ترقية الحماية

🌾 **المزارع والقلاع:**
• /farm - إدارة المزرعة
• /castle - إدارة القلعة
• /harvest - حصاد المحاصيل

📊 **الإحصائيات:**
• /stats - إحصائياتك الشخصية
• /leaderboard - لوحة الصدارة
• /rank - ترتيبك

⚙️ **أوامر أخرى:**
• /start - بدء استخدام البوت
• /help - عرض هذه المساعدة
• /settings - إعدادات الحساب
    """,
    
    "not_registered": "❌ يرجى التسجيل أولاً باستخدام الأمر /start",
    "insufficient_balance": "❌ رصيدك غير كافي لهذه العملية",
    "invalid_amount": "❌ المبلغ المدخل غير صحيح",
    "user_not_found": "❌ المستخدم غير موجود",
    "cooldown_active": "⏰ يجب الانتظار قبل استخدام هذا الأمر مرة أخرى",
    "transaction_success": "✅ تم إنجاز العملية بنجاح",
    "transaction_failed": "❌ فشل في إنجاز العملية",
    "error": "❌ حدث خطأ، يرجى المحاولة مرة أخرى",
    "maintenance": "🔧 البوت تحت الصيانة، يرجى المحاولة لاحقاً"
}

# إعدادات نظام المستويات
LEVEL_SYSTEM = {
    "xp_per_action": {
        "transaction": 10,
        "investment": 25,
        "property_deal": 50,
        "successful_theft": 30,
        "farm_harvest": 15,
        "castle_upgrade": 40
    },
    "level_benefits": {
        1: {"bonus_income": 0.05, "unlock": "basic_features"},
        5: {"bonus_income": 0.10, "unlock": "advanced_banking"},
        10: {"bonus_income": 0.15, "unlock": "premium_investments"},
        15: {"bonus_income": 0.20, "unlock": "elite_properties"},
        20: {"bonus_income": 0.25, "unlock": "master_trader"}
    }
}

# إعدادات التنبيهات والإشعارات
NOTIFICATION_SETTINGS = {
    "daily_bonus_reminder": True,
    "investment_maturity": True,
    "property_income": True,
    "security_alerts": True,
    "level_up": True
}

# حدود الأمان والحماية
SECURITY_LIMITS = {
    "max_daily_transactions": 50,
    "max_single_transfer": 500000,
    "suspicious_activity_threshold": 10,
    "auto_ban_threshold": 20
}

# إعدادات الدفع
PAYMENT_SETTINGS = {
    "enabled": False,  # تعطيل الدفع حالياً
    "currency": "USD",
    "minimum_amount": 1.0,
    "maximum_amount": 10000.0,
    "fee_percentage": 0.03,  # 3% رسوم
    "supported_methods": ["card", "crypto"],
    "webhook_url": None,
    "api_key": None
}

# إعدادات قناة الإشعارات
NOTIFICATION_CHANNEL = {
    "enabled": True,
    "chat_id": "-1002477409722",  # معرف القناة الفرعية
    "send_new_group_notifications": True,
    "send_bot_updates": True,
    "send_admin_alerts": True
}

# إعدادات نظام المستويات
LEVELS = [
  {
    "name": "عالم النجوم",
    "icon": "⭐",
    "desc": "البداية الحقيقية لمسار القوة. يتدرج من نجم 1 حتى نجم 9، وكل نجم يمثل زيادة كبيرة في قوة الجسد والطاقة القتالية. المحارب في هذا العالم يطور أساسياته في التحكم بالطاقة، والمهارات القتالية الأساسية، ويبدأ بمواجهة وحوش ضعيفة.",
    "sub_levels": ["نجم 1", "نجم 2", "نجم 3", "نجم 4", "نجم 5", "نجم 6", "نجم 7", "نجم 8", "نجم 9"],
    "xp_required": 0,
    "xp_per_action": 10,
    "abilities_unlocked": ["هالة الطاقة الأساسية", "ضربات محسنة", "تحمل أفضل"]
  },
  {
    "name": "عالم القمر",
    "icon": "🌙",
    "desc": "يتكون من ثلاث مراحل رئيسية: القمر الجديد، النصف قمر، والقمر المكتمل. كل مرحلة تنقسم إلى (منخفض، متوسط، عالٍ، ذروة) وكل منها من مستوى 1 إلى 9. في هذا العالم يبدأ المقاتل باستخدام الطاقة في تعزيز السرعة والقوة الهجومية، والسيطرة على نطاق أكبر من المعركة.",
    "stages": {
      "القمر الجديد": ["منخفض", "متوسط", "عالٍ", "ذروة"],
      "النصف قمر": ["منخفض", "متوسط", "عالٍ", "ذروة"],
      "القمر المكتمل": ["منخفض", "متوسط", "عالٍ", "ذروة"]
    },
    "xp_required": 1000,
    "xp_per_action": 20,
    "abilities_unlocked": ["تعزيز السرعة", "ضربات بطاقة أعلى", "تحمل مضاعف"]
  },
  {
    "name": "عالم الشمس",
    "icon": "☀",
    "desc": "ثلاث مراحل: شمس الصباح، شمس الصعود، وشمس الاحتراق. كل مرحلة تنقسم إلى (منخفض، متوسط، عالٍ، ذروة)، ويظهر في هذه المرحلة طور الجحيم كاختبار خاص للقوة. في هذا العالم يصبح المحارب قادراً على استخدام هجمات عن بعد، والسيطرة على عناصر معينة مثل النار أو الرياح.",
    "stages": {
      "شمس الصباح": ["منخفض", "متوسط", "عالٍ", "ذروة"],
      "شمس الصعود": ["منخفض", "متوسط", "عالٍ", "ذروة"],
      "شمس الاحتراق": ["منخفض", "متوسط", "عالٍ", "ذروة"]
    },
    "xp_required": 3000,
    "xp_per_action": 30,
    "abilities_unlocked": ["هجمات بعيدة المدى", "تعزيز عنصري", "دفاعات متقدمة"]
  },
  {
    "name": "عالم الأسطورة",
    "icon": "🐉",
    "desc": "يتكون من 9 مستويات متصاعدة، وهو المرحلة التي تسبق الوصول إلى السيطرة المطلقة على القوانين. المقاتل في هذا العالم يمتلك قوة هائلة، ومرونة تكتيكية عالية، وقدرة على مواجهة جيوش كاملة بمفرده.",
    "sub_levels": ["المستوى 1", "المستوى 2", "المستوى 3", "المستوى 4", "المستوى 5", "المستوى 6", "المستوى 7", "المستوى 8", "المستوى 9"],
    "xp_required": 7000,
    "xp_per_action": 40,
    "abilities_unlocked": ["التحكم بمجال المعركة", "تعطيل خصوم متعددين", "تجديد طاقة سريع"]
  },
  {
    "name": "العالم السيادي",
    "icon": "👑",
    "desc": "مرحلة السيطرة شبه المطلقة على الطاقة والقوانين، حيث يصبح المحارب قادراً على إعادة تشكيل بيئة المعركة بالكامل، وتغيير مسار القتال بلمسة واحدة.",
    "xp_required": 15000,
    "xp_per_action": 50,
    "abilities_unlocked": ["السيطرة على القوانين", "إيقاف الزمن لثوانٍ", "تعزيز الحلفاء"]
  },
  {
    "name": "العالم النهائي",
    "icon": "✨",
    "desc": "القمة المطلقة للطاقة. المقاتل هنا قادر على إعادة تشكيل الواقع نفسه، والتحكم الكامل في كل العناصر والقوانين، والوصول لمرحلة الخلود القتالي.",
    "xp_required": 30000,
    "xp_per_action": 60,
    "abilities_unlocked": ["إعادة تشكيل الواقع", "تحكم كامل بالقوانين", "قدرات لامحدودة"]
  }
]

# إعدادات API الخارجية
API_SETTINGS = {
    "stock_api": {
        "enabled": False,
        "api_key": None,
        "base_url": "https://api.example.com",
        "endpoints": {
            "stock_prices": "/stocks/prices",
            "market_data": "/market/data"
        }
    },
    "weather_api": {
        "enabled": False,
        "api_key": None,
        "base_url": "https://api.openweathermap.org"
    },
    "crypto_api": {
        "enabled": False,
        "api_key": None,
        "base_url": "https://api.coinbase.com"
    }
}
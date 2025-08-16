"""
إعدادات البوت الرئيسية
Main Bot Settings Configuration
"""

import os

# معلومات البوت الأساسية
BOT_TOKEN = os.getenv("BOT_TOKEN", "7942168520:AAEj18WjZ8Ek6TEFdp5ZLjGIk5jSG5L8z0o")
BOT_USERNAME = "theyuki_bot"

# قائمة المديرين والمالكين
ADMINS = [6524680126, 8278493069, 6629947448]
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
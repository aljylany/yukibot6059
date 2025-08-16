"""
أدوات إنشاء لوحات المفاتيح
Keyboard Utilities
"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton


def get_main_keyboard():
    """لوحة المفاتيح الرئيسية"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="💰 الرصيد"),
                KeyboardButton(text="🏦 البنك"),
                KeyboardButton(text="🏠 العقارات")
            ],
            [
                KeyboardButton(text="📈 الأسهم"),
                KeyboardButton(text="💼 الاستثمار"),
                KeyboardButton(text="🔓 السرقة")
            ],
            [
                KeyboardButton(text="🌾 المزرعة"),
                KeyboardButton(text="🏰 القلعة"),
                KeyboardButton(text="🏆 الترتيب")
            ],
            [
                KeyboardButton(text="📊 إحصائياتي"),
                KeyboardButton(text="⚙️ الإعدادات"),
                KeyboardButton(text="❓ مساعدة")
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=False
    )
    return keyboard


def get_admin_keyboard():
    """لوحة مفاتيح المديرين"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 إحصائيات البوت", callback_data="admin_stats"),
            InlineKeyboardButton(text="👥 إدارة المستخدمين", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="📢 رسالة جماعية", callback_data="admin_broadcast"),
            InlineKeyboardButton(text="💾 نسخة احتياطية", callback_data="admin_backup")
        ],
        [
            InlineKeyboardButton(text="🔧 صيانة البوت", callback_data="admin_maintenance"),
            InlineKeyboardButton(text="📈 تقارير مفصلة", callback_data="admin_reports")
        ]
    ])
    return keyboard


def get_banks_keyboard():
    """لوحة مفاتيح البنوك"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💵 إيداع", callback_data="bank_deposit"),
            InlineKeyboardButton(text="🏧 سحب", callback_data="bank_withdraw")
        ],
        [
            InlineKeyboardButton(text="💰 رصيد البنك", callback_data="bank_balance"),
            InlineKeyboardButton(text="💳 تحويل أموال", callback_data="bank_transfer")
        ],
        [
            InlineKeyboardButton(text="📊 كشف حساب", callback_data="bank_statement"),
            InlineKeyboardButton(text="📈 معلومات الفوائد", callback_data="bank_interest")
        ]
    ])
    return keyboard


def get_property_keyboard():
    """لوحة مفاتيح العقارات"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🛒 شراء عقار", callback_data="property_buy"),
            InlineKeyboardButton(text="💰 بيع عقار", callback_data="property_sell")
        ],
        [
            InlineKeyboardButton(text="🏠 عقاراتي", callback_data="property_manage"),
            InlineKeyboardButton(text="📊 إحصائيات", callback_data="property_stats")
        ],
        [
            InlineKeyboardButton(text="💎 تطوير عقار", callback_data="property_upgrade"),
            InlineKeyboardButton(text="🏘️ السوق العقاري", callback_data="property_market")
        ]
    ])
    return keyboard


def get_stocks_keyboard():
    """لوحة مفاتيح الأسهم"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📈 شراء أسهم", callback_data="stocks_buy"),
            InlineKeyboardButton(text="📉 بيع أسهم", callback_data="stocks_sell")
        ],
        [
            InlineKeyboardButton(text="💼 محفظتي", callback_data="stocks_portfolio"),
            InlineKeyboardButton(text="📊 أسعار السوق", callback_data="stocks_market")
        ],
        [
            InlineKeyboardButton(text="📈 تحليل الأسهم", callback_data="stocks_analysis"),
            InlineKeyboardButton(text="📰 أخبار السوق", callback_data="stocks_news")
        ]
    ])
    return keyboard


def get_investment_keyboard():
    """لوحة مفاتيح الاستثمار"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💼 استثمار جديد", callback_data="investment_create"),
            InlineKeyboardButton(text="📊 محفظة الاستثمار", callback_data="investment_portfolio")
        ],
        [
            InlineKeyboardButton(text="💰 سحب استثمار", callback_data="investment_withdraw"),
            InlineKeyboardButton(text="📈 تقرير الأرباح", callback_data="investment_report")
        ],
        [
            InlineKeyboardButton(text="💡 نصائح استثمارية", callback_data="investment_tips"),
            InlineKeyboardButton(text="🎯 حاسبة الأرباح", callback_data="investment_calculator")
        ]
    ])
    return keyboard


def get_theft_keyboard():
    """لوحة مفاتيح السرقة"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔓 سرقة لاعب", callback_data="theft_steal"),
            InlineKeyboardButton(text="🛡️ تحسين الأمان", callback_data="theft_security")
        ],
        [
            InlineKeyboardButton(text="📊 إحصائيات السرقة", callback_data="theft_stats"),
            InlineKeyboardButton(text="🏆 أفضل اللصوص", callback_data="theft_leaderboard")
        ],
        [
            InlineKeyboardButton(text="🕵️ تدريب اللصوص", callback_data="theft_training"),
            InlineKeyboardButton(text="🔒 نظام الحماية", callback_data="theft_protection")
        ]
    ])
    return keyboard


def get_farm_keyboard():
    """لوحة مفاتيح المزرعة"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🌱 زراعة محاصيل", callback_data="farm_plant"),
            InlineKeyboardButton(text="🌾 حصاد", callback_data="farm_harvest")
        ],
        [
            InlineKeyboardButton(text="📊 حالة المزرعة", callback_data="farm_status"),
            InlineKeyboardButton(text="🚜 ترقية المعدات", callback_data="farm_upgrade")
        ],
        [
            InlineKeyboardButton(text="🌦️ تقرير الطقس", callback_data="farm_weather"),
            InlineKeyboardButton(text="📈 تقرير الأرباح", callback_data="farm_report")
        ]
    ])
    return keyboard


def get_castle_keyboard():
    """لوحة مفاتيح القلعة"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔨 ترقية المباني", callback_data="castle_upgrade"),
            InlineKeyboardButton(text="⚔️ مهاجمة قلعة", callback_data="castle_attack")
        ],
        [
            InlineKeyboardButton(text="🛡️ إدارة الدفاع", callback_data="castle_defend"),
            InlineKeyboardButton(text="💰 جمع الذهب", callback_data="castle_collect")
        ],
        [
            InlineKeyboardButton(text="👥 إدارة الجيش", callback_data="castle_army"),
            InlineKeyboardButton(text="🏆 ترتيب القلاع", callback_data="castle_ranking")
        ]
    ])
    return keyboard


def get_ranking_keyboard():
    """لوحة مفاتيح الترتيب"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 الأغنى", callback_data="ranking_wealth"),
            InlineKeyboardButton(text="🏦 أكبر مودع", callback_data="ranking_bank")
        ],
        [
            InlineKeyboardButton(text="🏠 أكثر عقارات", callback_data="ranking_properties"),
            InlineKeyboardButton(text="📈 أفضل مستثمر", callback_data="ranking_investor")
        ],
        [
            InlineKeyboardButton(text="🔓 أمهر لص", callback_data="ranking_thief"),
            InlineKeyboardButton(text="🏰 أقوى قلعة", callback_data="ranking_castle")
        ]
    ])
    return keyboard


def get_confirmation_keyboard(confirm_data: str, cancel_data: str = "cancel"):
    """لوحة مفاتيح التأكيد"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأكيد", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ إلغاء", callback_data=cancel_data)
        ]
    ])
    return keyboard


def get_pagination_keyboard(page: int, total_pages: int, callback_prefix: str):
    """لوحة مفاتيح التصفح بين الصفحات"""
    buttons = []
    
    # زر الصفحة السابقة
    if page > 1:
        buttons.append(InlineKeyboardButton(
            text="◀️ السابقة", 
            callback_data=f"{callback_prefix}_page_{page-1}"
        ))
    
    # رقم الصفحة الحالية
    buttons.append(InlineKeyboardButton(
        text=f"{page}/{total_pages}",
        callback_data="current_page"
    ))
    
    # زر الصفحة التالية
    if page < total_pages:
        buttons.append(InlineKeyboardButton(
            text="▶️ التالية",
            callback_data=f"{callback_prefix}_page_{page+1}"
        ))
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons])
    return keyboard


def get_number_keyboard(callback_prefix: str, max_number: int = 10):
    """لوحة مفاتيح الأرقام"""
    buttons = []
    row = []
    
    for i in range(1, max_number + 1):
        row.append(InlineKeyboardButton(
            text=str(i),
            callback_data=f"{callback_prefix}_{i}"
        ))
        
        # إنشاء صف جديد كل 3 أرقام
        if len(row) == 3:
            buttons.append(row)
            row = []
    
    # إضافة الصف الأخير إذا كان غير مكتمل
    if row:
        buttons.append(row)
    
    # إضافة زر الإلغاء
    buttons.append([InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_back_keyboard(back_data: str = "back"):
    """لوحة مفاتيح العودة"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 العودة", callback_data=back_data)]
    ])
    return keyboard


def get_share_keyboard(text: str, url: str = None):
    """لوحة مفاتيح المشاركة"""
    buttons = []
    
    # زر مشاركة في تليجرام
    share_text = f"https://t.me/share/url?url={url or ''}&text={text}"
    buttons.append([InlineKeyboardButton(
        text="📤 مشاركة",
        url=share_text
    )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_contact_keyboard():
    """لوحة مفاتيح جهة الاتصال"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 مشاركة رقم الهاتف", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def get_location_keyboard():
    """لوحة مفاتيح الموقع"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📍 مشاركة الموقع", request_location=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard


def create_dynamic_keyboard(buttons_data: list, columns: int = 2):
    """إنشاء لوحة مفاتيح ديناميكية"""
    keyboard_buttons = []
    row = []
    
    for button_data in buttons_data:
        if isinstance(button_data, dict):
            button = InlineKeyboardButton(
                text=button_data.get('text', ''),
                callback_data=button_data.get('callback_data', ''),
                url=button_data.get('url')
            )
        else:
            # إذا كان مجرد نص
            button = InlineKeyboardButton(
                text=str(button_data),
                callback_data=f"dynamic_{button_data}"
            )
        
        row.append(button)
        
        if len(row) == columns:
            keyboard_buttons.append(row)
            row = []
    
    # إضافة الصف الأخير إذا كان غير مكتمل
    if row:
        keyboard_buttons.append(row)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    return keyboard


def get_settings_keyboard():
    """لوحة مفاتيح الإعدادات"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔔 الإشعارات", callback_data="settings_notifications"),
            InlineKeyboardButton(text="🌐 اللغة", callback_data="settings_language")
        ],
        [
            InlineKeyboardButton(text="🔐 الخصوصية", callback_data="settings_privacy"),
            InlineKeyboardButton(text="🎨 المظهر", callback_data="settings_theme")
        ],
        [
            InlineKeyboardButton(text="📊 إحصائياتي", callback_data="settings_stats"),
            InlineKeyboardButton(text="🔄 إعادة تعيين", callback_data="settings_reset")
        ],
        [
            InlineKeyboardButton(text="❓ مساعدة", callback_data="settings_help"),
            InlineKeyboardButton(text="📞 تواصل معنا", callback_data="settings_contact")
        ]
    ])
    return keyboard


def get_help_keyboard():
    """لوحة مفاتيح المساعدة"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🚀 البدء السريع", callback_data="help_quickstart"),
            InlineKeyboardButton(text="💡 نصائح", callback_data="help_tips")
        ],
        [
            InlineKeyboardButton(text="❓ الأسئلة الشائعة", callback_data="help_faq"),
            InlineKeyboardButton(text="📖 دليل المستخدم", callback_data="help_guide")
        ],
        [
            InlineKeyboardButton(text="🐛 الإبلاغ عن خطأ", callback_data="help_bug_report"),
            InlineKeyboardButton(text="💬 الدعم الفني", callback_data="help_support")
        ]
    ])
    return keyboard

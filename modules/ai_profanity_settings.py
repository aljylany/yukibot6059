"""
إعدادات نظام كشف السباب الذكي
"""

# إعدادات النظام الذكي
AI_SETTINGS = {
    # مستوى الحساسية (0.1 - 1.0)
    'sensitivity_level': 0.7,
    
    # تفعيل التعلم التلقائي
    'auto_learning': True,
    
    # حفظ الأنماط الجديدة
    'save_new_patterns': True,
    
    # استخدام تحليل السياق
    'use_context_analysis': True,
    
    # مستوى الثقة المطلوب للكشف
    'confidence_threshold': 0.65,
    
    # تفعيل كشف التمويه المتقدم
    'advanced_obfuscation_detection': True,
    
    # حد أقصى لحفظ الأنماط (لمنع امتلاء قاعدة البيانات)
    'max_stored_patterns': 10000,
    
    # فترة مسح البيانات القديمة (بالأيام)
    'cleanup_old_data_days': 30,
    
    # تفعيل الإحصائيات التفصيلية
    'detailed_statistics': True,
}

# رسائل النظام الذكي
AI_MESSAGES = {
    'detection_high_confidence': "🎯 كشف عالي الدقة",
    'detection_medium_confidence': "⚠️ كشف متوسط الدقة", 
    'detection_low_confidence': "❓ كشف منخفض الدقة",
    'obfuscation_detected': "🎭 تم اكتشاف تمويه",
    'new_pattern_learned': "🧠 تم تعلم نمط جديد",
    'context_analysis_used': "📝 تم استخدام تحليل السياق",
    'ai_fallback': "🔄 تم استخدام النظام الاحتياطي",
}

# أوزان أساليب التمويه المختلفة
OBFUSCATION_WEIGHTS = {
    'number_substitution': 0.8,
    'symbol_obfuscation': 0.9,
    'letter_spacing': 0.95,
    'letter_repetition': 0.7,
    'mixed_languages': 0.8,
    'potential_reversal': 0.5,
    'case_variation': 0.6,
}

# قائمة الاستثناءات - كلمات قد تبدو مشبوهة لكنها غير مسيئة
EXCEPTION_WORDS = [
    "كسر", "كسل", "كسب", "اكسر", "اكسب", "كسور", "كسوف", "كاسر",
    "زبدة", "زبيب", "زبور", "زبوردة",
    "نيكل", "انيكو", "نيك_نيم", 
    "كمامة", "كمال", "كمان", "اكمال", "كم", "كما",
    "طير", "طيران", "طيور", "طيار",
]

def get_setting(key, default=None):
    """الحصول على إعداد معين"""
    return AI_SETTINGS.get(key, default)

def update_setting(key, value):
    """تحديث إعداد معين"""
    if key in AI_SETTINGS:
        AI_SETTINGS[key] = value
        return True
    return False

def get_obfuscation_weight(method):
    """الحصول على وزن أسلوب التمويه"""
    return OBFUSCATION_WEIGHTS.get(method, 0.5)

def is_exception_word(word):
    """فحص إذا كانت الكلمة من الاستثناءات"""
    return word.lower() in [w.lower() for w in EXCEPTION_WORDS]
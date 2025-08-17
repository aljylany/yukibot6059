"""
اختبار نظام الردود
Response System Tester
"""

import logging
from aiogram.types import Message
from modules.special_responses import get_response, TRIGGER_KEYWORDS, GENERAL_RESPONSES, SPECIAL_RESPONSES
from utils.decorators import admin_required


@admin_required
async def test_response_system(message: Message):
    """اختبار نظام الردود لجميع الأنواع"""
    try:
        if not message.from_user:
            return
        
        user_id = message.from_user.id
        test_results = []
        
        # اختبار كل نوع من أنواع الردود
        for response_type, keywords in TRIGGER_KEYWORDS.items():
            test_keyword = keywords[0] if keywords else ""
            if test_keyword:
                response = get_response(user_id, test_keyword)
                if response:
                    test_results.append(f"✅ {response_type}: {response[:50]}...")
                else:
                    test_results.append(f"❌ {response_type}: لا يوجد رد")
        
        # معلومات إضافية
        is_special = user_id in SPECIAL_RESPONSES
        special_status = "مستخدم خاص ✨" if is_special else "مستخدم عادي 👤"
        
        result_message = f"""
🧪 **نتائج اختبار نظام الردود**

👤 **المستخدم:** {message.from_user.first_name or 'غير محدد'}
🆔 **المعرف:** `{user_id}`
⭐ **النوع:** {special_status}

📊 **نتائج الاختبار:**
{chr(10).join(test_results)}

📈 **إحصائيات النظام:**
• أنواع الردود: {len(TRIGGER_KEYWORDS)}
• المستخدمين الخاصين: {len(SPECIAL_RESPONSES)}
• الكلمات المفتاحية: {sum(len(keywords) for keywords in TRIGGER_KEYWORDS.values())}
        """
        
        await message.reply(result_message)
        
    except Exception as e:
        logging.error(f"خطأ في test_response_system: {e}")
        await message.reply("❌ حدث خطأ أثناء اختبار النظام")


@admin_required 
async def show_response_stats(message: Message):
    """عرض إحصائيات مفصلة عن نظام الردود"""
    try:
        stats = []
        
        # إحصائيات الكلمات المفتاحية
        stats.append("🔑 **الكلمات المفتاحية:**")
        for response_type, keywords in TRIGGER_KEYWORDS.items():
            type_name = {
                "greetings": "ترحيب", 
                "farewell": "وداع",
                "call_name": "مناداة", 
                "bot_insult": "إهانة"
            }.get(response_type, response_type)
            
            stats.append(f"• {type_name}: {len(keywords)} كلمة")
            stats.append(f"  └─ {', '.join(keywords[:3])}{'...' if len(keywords) > 3 else ''}")
        
        # إحصائيات الردود العامة
        stats.append("\n💬 **الردود العامة:**")
        for response_type, responses in GENERAL_RESPONSES.items():
            type_name = {
                "greetings": "ترحيب", 
                "farewell": "وداع",
                "call_name": "مناداة", 
                "bot_insult": "إهانة"
            }.get(response_type, response_type)
            stats.append(f"• {type_name}: {len(responses)} رد")
        
        # إحصائيات المستخدمين الخاصين
        stats.append("\n⭐ **المستخدمين الخاصين:**")
        for user_id, user_responses in SPECIAL_RESPONSES.items():
            total_responses = sum(len(responses) for responses in user_responses.values())
            stats.append(f"• المستخدم `{user_id}`: {total_responses} رد خاص")
            for resp_type, responses in user_responses.items():
                type_name = {
                    "greetings": "ترحيب", 
                    "farewell": "وداع",
                    "call_name": "مناداة", 
                    "bot_insult": "إهانة"
                }.get(resp_type, resp_type)
                stats.append(f"  └─ {type_name}: {len(responses)} رد")
        
        result_message = "\n".join(stats)
        await message.reply(result_message)
        
    except Exception as e:
        logging.error(f"خطأ في show_response_stats: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الإحصائيات")


async def handle_response_tester_commands(message: Message) -> bool:
    """معالج أوامر اختبار نظام الردود"""
    if not message.text or not message.from_user:
        return False
    
    # التحقق من صلاحية المدير
    from config.settings import ADMINS
    if message.from_user.id not in ADMINS:
        return False
    
    text = message.text.lower()
    
    if text in ['اختبار الردود', 'تجربة الردود', 'test responses']:
        await test_response_system(message)
        return True
    elif text in ['إحصائيات الردود', 'احصائيات الردود', 'response stats']:
        await show_response_stats(message)
        return True
    
    return False
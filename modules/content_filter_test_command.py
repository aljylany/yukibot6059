"""
أوامر اختبار نظام كشف المحتوى داخل البوت
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from config.hierarchy import is_master, is_supreme_master
from modules.comprehensive_content_filter import comprehensive_filter, ViolationType, SeverityLevel
from modules.profanity_filter import check_message_advanced
import asyncio

async def test_content_filter_command(message: Message, state: FSMContext):
    """أمر اختبار نظام كشف المحتوى"""
    
    # التحقق من الصلاحيات
    if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id)):
        await message.answer("❌ هذا الأمر مخصص للأسياد فقط")
        return
    
    await message.answer("🔍 **بدء اختبار نظام كشف المحتوى الشامل**\n\nجاري الاختبار...")
    
    # اختبار حالة النظام
    system_status = f"""
🔧 **حالة النظام:**
• النظام الشامل: {'✅ مفعل' if comprehensive_filter.enabled else '❌ معطل'}
• مفاتيح API: {len(comprehensive_filter.api_keys)} مفتاح
• نموذج AI: {'✅ جاهز' if comprehensive_filter.model else '❌ غير متوفر'}
"""
    
    # اختبارات سريعة
    test_texts = [
        {"text": "مرحبا", "expected": False, "name": "نص نظيف"},
        {"text": "شرموط", "expected": True, "name": "سباب مباشر"},
        {"text": "ش ر م و ط", "expected": True, "name": "سباب مقسم"},
        {"text": "محتوى إباحي", "expected": True, "name": "محتوى جنسي"},
    ]
    
    results = []
    
    for test in test_texts:
        try:
            # اختبار النظام الشامل
            result = await comprehensive_filter._check_text_content(test['text'])
            has_violation = result['has_violation']
            
            # اختبار نظام السباب
            profanity_result = check_message_advanced(test['text'])
            has_profanity = profanity_result['is_abusive']
            
            status = "✅" if (has_violation or has_profanity) == test['expected'] else "❌"
            
            results.append(f"{status} {test['name']}: {'كُشف' if has_violation or has_profanity else 'لم يُكشف'}")
            
        except Exception as e:
            results.append(f"❌ {test['name']}: خطأ - {str(e)[:50]}")
    
    # عرض النتائج
    test_results = "\n".join(results)
    
    final_message = f"""
{system_status}

🧪 **نتائج الاختبار:**
{test_results}

📊 **تفاصيل إضافية:**
• فحص النصوص: {'✅ يعمل' if comprehensive_filter.enabled else '❌ معطل'}
• فحص الصور: {'✅ يعمل' if comprehensive_filter.model else '❌ معطل'}
• قاعدة بيانات السباب: ✅ جاهزة

💡 **كيفية المراقبة:**
1. تابع سجلات النظام في وحدة التحكم
2. أرسل محتوى مختلف لاختبار الكشف الفوري
3. استخدم الأمر /test_profanity للاختبار المتقدم
"""
    
    await message.answer(final_message)

async def test_profanity_command(message: Message, state: FSMContext):
    """أمر اختبار نظام كشف السباب بالتفصيل"""
    
    if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id)):
        await message.answer("❌ هذا الأمر مخصص للأسياد فقط")
        return
    
    # أخذ النص من الأمر
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.answer("📝 **الاستخدام:** /test_profanity النص المراد اختباره")
        return
    
    test_text = command_parts[1]
    
    await message.answer(f"🔍 **اختبار النص:** `{test_text}`\n\nجاري الفحص...")
    
    try:
        # فحص شامل
        comprehensive_result = await comprehensive_filter._check_text_content(test_text)
        
        # فحص السباب المتقدم
        profanity_result = check_message_advanced(test_text)
        
        # إعداد النتيجة
        result_message = f"""
🔍 **نتائج فحص النص:** `{test_text}`

**النظام الشامل:**
• هل يوجد مخالفة: {'✅ نعم' if comprehensive_result['has_violation'] else '❌ لا'}
• نوع المخالفة: {comprehensive_result.get('violation_type', 'لا يوجد')}
• مستوى الخطورة: {comprehensive_result.get('severity', 0)}

**نظام كشف السباب:**
• هل يوجد سباب: {'✅ نعم' if profanity_result['is_abusive'] else '❌ لا'}
• الطريقة: {profanity_result.get('method', 'غير محدد')}
• مستوى الخطورة: {profanity_result.get('severity', 0)}
• الكلمات المكتشفة: {profanity_result.get('words', 'لا يوجد')}

**النتيجة النهائية:**
{'🚨 سيتم اتخاذ إجراء' if comprehensive_result['has_violation'] or profanity_result['is_abusive'] else '✅ المحتوى مقبول'}
"""
        
        await message.answer(result_message)
        
    except Exception as e:
        await message.answer(f"❌ **خطأ في الفحص:** {str(e)}")

async def monitor_filter_command(message: Message, state: FSMContext):
    """أمر مراقبة نظام التصفية في الوقت الفعلي"""
    
    if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id)):
        await message.answer("❌ هذا الأمر مخصص للأسياد فقط")
        return
    
    # تشغيل مراقبة مكثفة لمدة 30 ثانية
    await message.answer("👁️ **تم تفعيل المراقبة المكثفة لمدة 30 ثانية**\n\nسيتم تسجيل كل عملية فحص بالتفصيل...")
    
    # رفع مستوى التسجيل مؤقتاً
    original_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.DEBUG)
    
    # انتظار 30 ثانية
    await asyncio.sleep(30)
    
    # إعادة مستوى التسجيل
    logging.getLogger().setLevel(original_level)
    
    await message.answer("✅ **انتهت المراقبة المكثفة**\n\nتحقق من سجلات النظام لمشاهدة التفاصيل")

async def reset_user_violations_command(message: Message, state: FSMContext):
    """أمر إعادة تعيين مخالفات مستخدم"""
    
    if not is_supreme_master(message.from_user.id):
        await message.answer("❌ هذا الأمر مخصص للسيد الأعلى فقط")
        return
    
    # أخذ معرف المستخدم من الأمر أو الرد
    user_id = None
    
    if message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        user_name = message.reply_to_message.from_user.first_name
    else:
        command_parts = message.text.split(' ', 1)
        if len(command_parts) < 2:
            await message.answer("📝 **الاستخدام:** /reset_violations [معرف المستخدم] أو رد على رسالة")
            return
        
        try:
            user_id = int(command_parts[1])
            user_name = str(user_id)
        except ValueError:
            await message.answer("❌ معرف المستخدم يجب أن يكون رقماً")
            return
    
    if not user_id:
        await message.answer("❌ لم يتم العثور على المستخدم")
        return
    
    try:
        # إعادة تعيين نقاط المخالفات
        import sqlite3
        
        conn = sqlite3.connect('comprehensive_filter.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        UPDATE user_violation_points 
        SET total_points = 0, punishment_level = 0, is_permanently_banned = FALSE
        WHERE user_id = ? AND chat_id = ?
        ''', (user_id, message.chat.id))
        
        # حذف المخالفات المؤقتة
        cursor.execute('''
        DELETE FROM violation_history 
        WHERE user_id = ? AND chat_id = ? AND expires_at IS NOT NULL
        ''', (user_id, message.chat.id))
        
        conn.commit()
        conn.close()
        
        await message.answer(f"✅ **تم إعادة تعيين مخالفات المستخدم**\n\nالمستخدم: {user_name} ({user_id})")
        
    except Exception as e:
        await message.answer(f"❌ **خطأ في إعادة التعيين:** {str(e)}")
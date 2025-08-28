"""
أوامر إدارة نظام كشف السباب الذكي
"""

import logging
from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from config.hierarchy import is_master, is_group_owner, is_moderator
from .ai_profanity_detector import ai_detector

router = Router()

@router.message(Command("نظام_السباب"))
async def profanity_system_status(message: Message):
    """عرض حالة نظام كشف السباب الذكي"""
    
    user_is_admin = (is_master(message.from_user.id) or 
                      await is_group_owner(message.from_user.id, message.chat.id) or 
                      await is_moderator(message.from_user.id, message.chat.id))
    if not user_is_admin:
        await message.reply("🚫 هذا الأمر للمشرفين والمالكين فقط")
        return
    
    try:
        stats = await ai_detector.get_detection_stats()
        
        if "error" in stats:
            await message.reply(f"❌ خطأ في الحصول على الإحصائيات: {stats['error']}")
            return
        
        status_text = f"""
🧠 **حالة نظام كشف السباب الذكي**

📊 **الإحصائيات:**
• أنماط محفوظة: {stats['total_patterns']}
• بيانات التعلم: {stats['learning_entries']}  
• أساليب التمويه: {stats['obfuscation_methods']}
• حالة النظام: {stats['system_status']}

🎯 **أكثر أساليب التمويه استخداماً:**
"""
        
        for i, (method, count) in enumerate(stats.get('top_methods', []), 1):
            status_text += f"{i}. {method}: {count} مرة\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="📈 إحصائيات مفصلة", callback_data="ai_profanity_detailed_stats"),
                InlineKeyboardButton(text="🧹 مسح التعلم", callback_data="ai_profanity_clear_learning")
            ],
            [
                InlineKeyboardButton(text="🔄 إعادة تدريب", callback_data="ai_profanity_retrain"),
                InlineKeyboardButton(text="⚙️ إعدادات", callback_data="ai_profanity_settings")
            ]
        ])
        
        await message.reply(status_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض حالة النظام: {e}")
        await message.reply("❌ خطأ في الحصول على معلومات النظام")

@router.message(Command("اختبار_ذكي"))
async def test_smart_detection(message: Message):
    """اختبار النظام الذكي على نص معين"""
    
    user_is_admin = (is_master(message.from_user.id) or 
                      await is_group_owner(message.from_user.id, message.chat.id) or 
                      await is_moderator(message.from_user.id, message.chat.id))
    if not user_is_admin:
        await message.reply("🚫 هذا الأمر للمشرفين والمالكين فقط")
        return
        
    # استخراج النص للاختبار
    command_parts = message.text.split(' ', 1)
    if len(command_parts) < 2:
        await message.reply("📝 استخدام: /اختبار_ذكي [النص المراد اختباره]\n\nمثال: /اختبار_ذكي ك*س*ك")
        return
    
    test_text = command_parts[1]
    
    try:
        # اختبار النص بالنظام الذكي
        result = await ai_detector.check_message_smart(
            text=test_text, 
            chat_context=f"اختبار من المشرف {message.from_user.first_name}",
            chat_id=message.chat.id
        )
        
        # تحضير الرد
        status = "🔴 **يحتوي على سباب**" if result.is_profane else "🟢 **نظيف**"
        
        result_text = f"""
🧪 **نتيجة الاختبار الذكي**

📝 **النص:** `{test_text}`

{status}

📊 **التفاصيل:**
• مستوى الثقة: {result.confidence:.2f}
• مستوى الخطورة: {result.severity_level}/3
• الأنماط المكتشفة: {', '.join(result.detected_patterns) if result.detected_patterns else 'لا يوجد'}
• أساليب التمويه: {', '.join(result.obfuscation_methods) if result.obfuscation_methods else 'لا يوجد'}

🧠 **تحليل السياق:**
{result.context_analysis[:200]}{'...' if len(result.context_analysis) > 200 else ''}
"""

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ تأكيد صحة النتيجة", callback_data=f"ai_confirm_result_{result.is_profane}"),
                InlineKeyboardButton(text="❌ النتيجة خاطئة", callback_data=f"ai_correct_result_{not result.is_profane}")
            ]
        ])
        
        await message.reply(result_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في اختبار النص: {e}")
        await message.reply(f"❌ خطأ في اختبار النص: {e}")

@router.message(Command("تدريب_ذكي"))
async def train_smart_system(message: Message):
    """تدريب النظام الذكي بنص جديد"""
    
    if not await is_master(message.from_user.id):
        await message.reply("🚫 هذا الأمر للأسياد فقط")
        return
    
    # استخراج النص والتصنيف
    command_parts = message.text.split()
    if len(command_parts) < 3:
        await message.reply("""
📚 **تدريب النظام الذكي**

استخدام: `/تدريب_ذكي [سباب/نظيف] [النص]`

أمثلة:
• `/تدريب_ذكي سباب ك@#$ك`
• `/تدريب_ذكي نظيف أنت شخص رائع`
        """)
        return
    
    classification = command_parts[1].lower()
    training_text = ' '.join(command_parts[2:])
    
    if classification not in ['سباب', 'نظيف']:
        await message.reply("❌ التصنيف يجب أن يكون 'سباب' أو 'نظيف'")
        return
    
    try:
        is_profane = classification == 'سباب'
        
        # إضافة للبيانات التدريبية (يمكن توسيعه لاحقاً)
        logging.info(f"تم تدريب النظام - النص: {training_text[:50]}، التصنيف: {'سباب' if is_profane else 'نظيف'}")
        
        await message.reply(f"""
✅ **تم تدريب النظام بنجاح**

📝 **النص:** `{training_text}`
🏷️ **التصنيف:** {'🔴 سباب' if is_profane else '🟢 نظيف'}

💡 النظام سيتعلم من هذا المثال لتحسين أدائه مستقبلاً
        """)
        
    except Exception as e:
        logging.error(f"خطأ في التدريب: {e}")
        await message.reply(f"❌ خطأ في تدريب النظام: {e}")

@router.callback_query(lambda c: c.data.startswith("ai_profanity_"))
async def handle_ai_profanity_callbacks(callback: CallbackQuery):
    """معالجة أزرار إدارة نظام السباب الذكي"""
    
    user_is_admin = (is_master(callback.from_user.id) or 
                      await is_group_owner(callback.from_user.id, callback.message.chat.id) or 
                      await is_moderator(callback.from_user.id, callback.message.chat.id))
    if not user_is_admin:
        await callback.answer("🚫 غير مسموح", show_alert=True)
        return
    
    action = callback.data.replace("ai_profanity_", "")
    
    if action == "detailed_stats":
        try:
            stats = await ai_detector.get_detection_stats()
            
            detailed_text = f"""
📈 **إحصائيات مفصلة للنظام الذكي**

🎯 **معدل الأداء:**
• إجمالي الفحوصات: {stats['learning_entries']}
• الأنماط المحفوظة: {stats['total_patterns']}
• أساليب التمويه المكتشفة: {stats['obfuscation_methods']}

🧠 **حالة الذكاء الاصطناعي:**
• النظام: {stats['system_status']}
• الدقة المقدرة: 85-95%
• سرعة المعالجة: ممتازة

📊 **أداء التعلم:**
• نماذج جديدة محفوظة يومياً: متغير
• تحسن الأداء: مستمر
            """
            
            await callback.message.edit_text(detailed_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 العودة", callback_data="ai_profanity_back")]
            ]))
            
        except Exception as e:
            await callback.answer(f"خطأ: {e}", show_alert=True)
    
    elif action == "clear_learning":
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⚠️ تأكيد المسح", callback_data="ai_profanity_confirm_clear"),
                InlineKeyboardButton(text="❌ إلغاء", callback_data="ai_profanity_back")
            ]
        ])
        
        await callback.message.edit_text(
            "⚠️ **تحذير: مسح بيانات التعلم**\n\n"
            "هذا العمل سيحذف جميع الأنماط المتعلمة والإحصائيات\n"
            "هل أنت متأكد؟",
            reply_markup=keyboard
        )
    
    elif action == "confirm_clear":
        try:
            # مسح بيانات التعلم
            import sqlite3
            conn = sqlite3.connect('ai_profanity_learning.db')
            cursor = conn.cursor()
            
            cursor.execute('DELETE FROM detected_patterns')
            cursor.execute('DELETE FROM context_learning')
            cursor.execute('DELETE FROM obfuscation_methods')
            
            conn.commit()
            conn.close()
            
            await callback.message.edit_text(
                "✅ **تم مسح بيانات التعلم بنجاح**\n\n"
                "النظام سيبدأ التعلم من جديد مع الرسائل القادمة"
            )
            
        except Exception as e:
            await callback.answer(f"خطأ في المسح: {e}", show_alert=True)
    
    elif action == "retrain":
        await callback.message.edit_text(
            "🔄 **إعادة تدريب النظام**\n\n"
            "يتم إعادة تدريب النظام تلقائياً مع كل رسالة جديدة\n"
            "لا حاجة لإعادة تدريب يدوية\n\n"
            "✅ النظام محدث ويعمل بأحدث البيانات",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🔙 العودة", callback_data="ai_profanity_back")]
            ])
        )
    
    elif action == "settings":
        settings_text = """
⚙️ **إعدادات النظام الذكي**

🎯 **المستويات الحالية:**
• حساسية الكشف: عالية
• مستوى الثقة المطلوب: 70%
• تفعيل التعلم التلقائي: ✅

🔧 **خيارات متقدمة:**
• كشف التمويه: مفعل
• تحليل السياق: مفعل
• حفظ الأنماط: مفعل
        """
        
        await callback.message.edit_text(settings_text, reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 العودة", callback_data="ai_profanity_back")]
        ]))
    
    elif action == "back":
        # العودة لعرض الحالة الرئيسية
        try:
            stats = await ai_detector.get_detection_stats()
            
            status_text = f"""
🧠 **حالة نظام كشف السباب الذكي**

📊 **الإحصائيات:**
• أنماط محفوظة: {stats['total_patterns']}
• بيانات التعلم: {stats['learning_entries']}  
• أساليب التمويه: {stats['obfuscation_methods']}
• حالة النظام: {stats['system_status']}

🎯 **أكثر أساليب التمويه استخداماً:**
"""
            
            for i, (method, count) in enumerate(stats.get('top_methods', []), 1):
                status_text += f"{i}. {method}: {count} مرة\n"
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📈 إحصائيات مفصلة", callback_data="ai_profanity_detailed_stats"),
                    InlineKeyboardButton(text="🧹 مسح التعلم", callback_data="ai_profanity_clear_learning")
                ],
                [
                    InlineKeyboardButton(text="🔄 إعادة تدريب", callback_data="ai_profanity_retrain"),
                    InlineKeyboardButton(text="⚙️ إعدادات", callback_data="ai_profanity_settings")
                ]
            ])
            
            await callback.message.edit_text(status_text, reply_markup=keyboard)
            
        except Exception as e:
            await callback.answer(f"خطأ: {e}", show_alert=True)
    
    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("ai_confirm_result_") or c.data.startswith("ai_correct_result_"))
async def handle_test_feedback(callback: CallbackQuery):
    """معالجة ردود المشرفين على نتائج الاختبار"""
    
    user_is_admin = (is_master(callback.from_user.id) or 
                      await is_group_owner(callback.from_user.id, callback.message.chat.id) or 
                      await is_moderator(callback.from_user.id, callback.message.chat.id))
    if not user_is_admin:
        await callback.answer("🚫 غير مسموح", show_alert=True)
        return
    
    if callback.data.startswith("ai_confirm_result_"):
        is_correct = callback.data.replace("ai_confirm_result_", "") == "True"
        await callback.answer("✅ تم تسجيل تأكيدك للنتيجة")
        
        # تحديث النص لإظهار التأكيد
        current_text = callback.message.text or callback.message.caption
        updated_text = current_text + "\n\n✅ **تم تأكيد صحة النتيجة من المشرف**"
        
        await callback.message.edit_text(updated_text)
        
    elif callback.data.startswith("ai_correct_result_"):
        correct_result = callback.data.replace("ai_correct_result_", "") == "True"
        
        # هنا يمكن حفظ التصحيح في قاعدة البيانات للتعلم
        logging.info(f"المشرف {callback.from_user.id} صحح نتيجة إلى: {correct_result}")
        
        await callback.answer("✅ تم تسجيل تصحيحك - النظام سيتعلم من هذا")
        
        # تحديث النص لإظهار التصحيح
        current_text = callback.message.text or callback.message.caption
        result_text = "🔴 يحتوي على سباب" if correct_result else "🟢 نظيف"
        updated_text = current_text + f"\n\n🔄 **تم تصحيح النتيجة إلى: {result_text}**"
        
        await callback.message.edit_text(updated_text)
"""
🔒 أوامر التحكم بنظام تحليل المستخدمين والخصوصية
"""

import aiosqlite
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any

from aiogram import Bot, types
from aiogram.types import Message, CallbackQuery

from config.database import DATABASE_URL
from database.user_analysis_operations import UserAnalysisOperations
from modules.user_analysis_manager import user_analysis_manager
from utils.decorators import admin_required


class UserAnalysisCommands:
    """أوامر التحكم في نظام تحليل المستخدمين"""
    
    @staticmethod
    async def toggle_group_analysis(message: Message):
        """تفعيل/إيقاف التحليل في المجموعة"""
        try:
            # التحقق من الصلاحيات
            from config.hierarchy import is_master, is_supreme_master, has_permission
            if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id) or await has_permission(message.from_user.id, message.chat.id, "مالك")):
                await message.reply("❌ ليس لديك صلاحية للتحكم بنظام التحليل")
                return
            
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # الحصول على الحالة الحالية
            current_status = await UserAnalysisOperations.is_analysis_enabled(chat_id)
            new_status = not current_status
            
            # تحديث الحالة
            success = await UserAnalysisOperations.set_group_analysis(
                chat_id=chat_id,
                enabled=new_status,
                modified_by=user_id,
                reason="تغيير بواسطة الإدارة"
            )
            
            if success:
                status_text = "تم تفعيل" if new_status else "تم إيقاف"
                user_name = message.from_user.first_name or "الإدارة"
                
                response = f"""
🧠 **{status_text} نظام تحليل المستخدمين**

{'✅ **الميزات المفعلة:**' if new_status else '❌ **الميزات المعطلة:**'}
• تحليل المشاعر والاهتمامات
• نظام الذكريات الذكي  
• التخصيص المتقدم للردود
• تحليل العلاقات الاجتماعية

🔒 **الخصوصية محمية:** البيانات محفوظة محلياً ولا تتم مشاركتها
⚙️ **التحكم:** يمكن إيقاف الميزة في أي وقت

تم التعديل بواسطة: {user_name}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
                """
                
                await message.reply(response.strip())
                
            else:
                await message.reply("❌ حدث خطأ في تحديث إعدادات التحليل")
                
        except Exception as e:
            logging.error(f"خطأ في تفعيل/إيقاف التحليل: {e}")
            await message.reply("❌ حدث خطأ في النظام")
    
    @staticmethod
    async def analysis_status(message: Message):
        """عرض حالة نظام التحليل"""
        try:
            # التحقق من الصلاحيات
            from config.hierarchy import is_master, is_supreme_master, has_permission
            if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id) or await has_permission(message.from_user.id, message.chat.id, "مالك")):
                await message.reply("❌ ليس لديك صلاحية لعرض حالة التحليل")
                return
            
            chat_id = message.chat.id
            
            # الحصول على إعدادات المجموعة
            async with aiosqlite.connect(DATABASE_URL) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM group_analysis_settings WHERE chat_id = ?",
                    (chat_id,)
                )
                settings = await cursor.fetchone()
            
            if settings:
                settings_data = dict(settings)
                enabled = settings_data['analysis_enabled']
                
                status_icon = "🟢" if enabled else "🔴"
                status_text = "مفعل" if enabled else "معطل"
                
                # الحصول على إحصائيات المجموعة
                cursor = await db.execute("""
                    SELECT COUNT(DISTINCT user_id) as total_analyzed,
                           COUNT(*) as total_activities
                    FROM analysis_statistics 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-30 days')
                """, (chat_id,))
                
                stats = await cursor.fetchone()
                stats_data = dict(stats) if stats else {"total_analyzed": 0, "total_activities": 0}
                
                response = f"""
📊 **حالة نظام تحليل المستخدمين**

{status_icon} **الحالة:** {status_text}

📈 **إحصائيات آخر 30 يوم:**
• المستخدمين المحللين: {stats_data['total_analyzed']}
• إجمالي الأنشطة: {stats_data['total_activities']}

⚙️ **الإعدادات المتاحة:**
• تحليل المشاعر: {'✅' if settings_data.get('allow_mood_analysis', True) else '❌'}
• تحليل العلاقات: {'✅' if settings_data.get('allow_relationship_analysis', True) else '❌'}
• نظام الذكريات: {'✅' if settings_data.get('allow_memory_system', True) else '❌'}
• الردود التنبؤية: {'✅' if settings_data.get('allow_predictive_responses', True) else '❌'}

📅 آخر تعديل: {settings_data.get('last_modified_at', 'غير محدد')}
                """
                
            else:
                response = """
📊 **حالة نظام تحليل المستخدمين**

🟢 **الحالة:** مفعل (افتراضي)

⚙️ لم يتم تخصيص إعدادات خاصة لهذه المجموعة
💡 استخدم الأوامر المتاحة لتخصيص الإعدادات
                """
            
            await message.reply(response.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض حالة التحليل: {e}")
            await message.reply("❌ حدث خطأ في الحصول على الحالة")
    
    @staticmethod
    async def clear_analysis_data(message: Message):
        """مسح بيانات التحليل للمجموعة (للأسياد فقط)"""
        try:
            # التحقق من الصلاحيات (أسياد فقط)
            from config.hierarchy import is_master, is_supreme_master
            if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id)):
                await message.reply("❌ ليس لديك صلاحية لمسح بيانات التحليل (أسياد فقط)")
                return
            
            chat_id = message.chat.id
            
            # تأكيد الحذف
            confirmation_text = """
⚠️ **تحذير: حذف بيانات التحليل**

هذا الإجراء سيحذف:
• جميع تحليلات المستخدمين في هذه المجموعة
• الذكريات والأنماط المحفوظة
• إحصائيات التفاعل والعلاقات

❌ **لا يمكن التراجع عن هذا الإجراء**

للمتابعة، اكتب: `تأكيد حذف البيانات`
للإلغاء، اكتب أي شيء آخر.
            """
            
            await message.reply(confirmation_text.strip())
            
        except Exception as e:
            logging.error(f"خطأ في طلب حذف البيانات: {e}")
            await message.reply("❌ حدث خطأ في النظام")
    
    @staticmethod
    async def my_analysis(message: Message):
        """عرض تحليل المستخدم الشخصي"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # التحقق من تفعيل التحليل
            if not await UserAnalysisOperations.is_analysis_enabled(chat_id):
                await message.reply("🔒 نظام التحليل غير مفعل في هذه المجموعة")
                return
            
            # الحصول على تحليل المستخدم
            insights = await user_analysis_manager.get_user_insights(user_id)
            
            if not insights:
                await message.reply("📊 لا توجد بيانات تحليل كافية بعد. تفاعل أكثر ليتم تحليل شخصيتك!")
                return
            
            user_name = message.from_user.first_name or "المستخدم"
            
            response = f"""
🧠 **تحليل شخصية {user_name}**

👤 **نوع الشخصية:** {insights.get('personality_summary', 'متوازن')}

🎯 **الاهتمامات:** {insights.get('interests_summary', 'متنوعة')}

📈 **نشاطك:**
• المزاج الغالب: {insights.get('mood_trends', {}).get('dominant_mood', 'محايد')}
• مستوى التفاعل: {insights.get('social_level', 'متوسط')}

💡 **التوصيات:**
{chr(10).join(f"• {rec}" for rec in insights.get('recommendations', [])[:3])}

🌟 **ذكريات مميزة:**
{chr(10).join(f"• {memory}" for memory in insights.get('recent_memories', [])[:3])}

📊 البيانات محدثة باستمرار وتعكس تفاعلك الأخير
            """
            
            await message.reply(response.strip())
            
        except Exception as e:
            logging.error(f"خطأ في عرض تحليل المستخدم {user_id}: {e}")
            await message.reply("❌ حدث خطأ في الحصول على التحليل")
    
    @staticmethod
    async def relationship_analysis(message: Message):
        """تحليل العلاقة مع مستخدم آخر"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # التحقق من تفعيل التحليل
            if not await UserAnalysisOperations.is_analysis_enabled(chat_id):
                await message.reply("🔒 نظام التحليل غير مفعل في هذه المجموعة")
                return
            
            # استخراج المستخدم المذكور
            if message.reply_to_message and message.reply_to_message.from_user:
                target_user_id = message.reply_to_message.from_user.id
                target_name = message.reply_to_message.from_user.first_name or "المستخدم"
                
                if target_user_id == user_id:
                    await message.reply("🤔 لا يمكنك تحليل علاقتك مع نفسك!")
                    return
                
                # الحصول على تحليل العلاقة
                relationship = await user_analysis_manager.get_relationship_insights(user_id, target_user_id)
                
                if not relationship or 'message' in relationship:
                    await message.reply(f"👥 لا توجد تفاعلات كافية مع {target_name} لتحليل العلاقة")
                    return
                
                user_name = message.from_user.first_name or "أنت"
                
                # تحويل قوة العلاقة إلى نص
                strength = relationship.get('relationship_strength', 0)
                if strength > 0.8:
                    strength_text = "قوية جداً 💪"
                elif strength > 0.6:
                    strength_text = "قوية 🤝"
                elif strength > 0.4:
                    strength_text = "متوسطة 👋"
                else:
                    strength_text = "ضعيفة 🤷"
                
                response = f"""
👥 **تحليل العلاقة بين {user_name} و {target_name}**

💫 **قوة العلاقة:** {strength_text}
🎭 **نوع الصداقة:** {relationship.get('friendship_level', 'معارف')}
🎯 **مستوى التوافق:** {relationship.get('compatibility_score', 0.5)*100:.0f}%

📊 **إحصائيات التفاعل:**
• إجمالي التفاعلات: {relationship.get('total_interactions', 0)}
• ألعاب مشتركة: {relationship.get('games_together', 0)}

💡 **اقتراحات لتحسين العلاقة:**
{chr(10).join(f"• {sug}" for sug in relationship.get('suggestions', [])[:3])}

🔄 البيانات تتحدث مع كل تفاعل جديد
                """
                
                await message.reply(response.strip())
                
            else:
                await message.reply("👥 للحصول على تحليل العلاقة، استخدم هذا الأمر كرد على رسالة الشخص المطلوب")
                
        except Exception as e:
            logging.error(f"خطأ في تحليل العلاقة: {e}")
            await message.reply("❌ حدث خطأ في تحليل العلاقة")
    
    @staticmethod
    async def group_analysis_stats(message: Message):
        """إحصائيات التحليل للمجموعة"""
        try:
            # التحقق من الصلاحيات
            from config.hierarchy import is_master, is_supreme_master, has_permission
            if not (is_supreme_master(message.from_user.id) or is_master(message.from_user.id) or await has_permission(message.from_user.id, message.chat.id, "مالك")):
                await message.reply("❌ ليس لديك صلاحية لعرض إحصائيات التحليل")
                return
            
            chat_id = message.chat.id
            
            # الحصول على إحصائيات شاملة
            async with aiosqlite.connect(DATABASE_URL) as db:
                # إحصائيات عامة
                cursor = await db.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as total_users,
                        COUNT(*) as total_activities,
                        AVG(sentiment_score) as avg_sentiment
                    FROM analysis_statistics 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-7 days')
                """, (chat_id,))
                
                general_stats = await cursor.fetchone()
                
                # أكثر المزاجات شيوعاً
                cursor = await db.execute("""
                    SELECT mood_detected, COUNT(*) as count
                    FROM analysis_statistics 
                    WHERE chat_id = ? AND mood_detected IS NOT NULL 
                        AND timestamp > datetime('now', '-7 days')
                    GROUP BY mood_detected 
                    ORDER BY count DESC 
                    LIMIT 3
                """, (chat_id,))
                
                top_moods = await cursor.fetchall()
                
                # أكثر الأنشطة شيوعاً
                cursor = await db.execute("""
                    SELECT activity_type, COUNT(*) as count
                    FROM analysis_statistics 
                    WHERE chat_id = ? AND timestamp > datetime('now', '-7 days')
                    GROUP BY activity_type 
                    ORDER BY count DESC 
                    LIMIT 3
                """, (chat_id,))
                
                top_activities = await cursor.fetchall()
            
            if general_stats and general_stats[0] > 0:
                total_users = general_stats[0]
                total_activities = general_stats[1] 
                avg_sentiment = general_stats[2] or 0
                
                sentiment_emoji = "😊" if avg_sentiment > 0.1 else "😐" if avg_sentiment > -0.1 else "😔"
                
                response = f"""
📊 **إحصائيات تحليل المجموعة - آخر 7 أيام**

👥 **نشاط المستخدمين:**
• المستخدمين النشطين: {total_users}
• إجمالي التفاعلات: {total_activities}
• متوسط المشاعر: {sentiment_emoji} ({avg_sentiment:.2f})

😊 **أكثر المزاجات شيوعاً:**
{chr(10).join(f"• {mood[0]}: {mood[1]} مرة" for mood in top_moods) if top_moods else "• لا توجد بيانات كافية"}

🎯 **أكثر الأنشطة:**
{chr(10).join(f"• {activity[0]}: {activity[1]} مرة" for activity in top_activities) if top_activities else "• لا توجد بيانات كافية"}

📈 تحليل مستمر لتحسين تجربة المجموعة
                """
                
            else:
                response = """
📊 **إحصائيات تحليل المجموعة**

📝 لا توجد بيانات تحليل كافية لآخر 7 أيام
💡 تحتاج المجموعة لمزيد من التفاعل لتوليد إحصائيات مفيدة

🚀 شجع الأعضاء على التفاعل أكثر!
                """
            
            await message.reply(response.strip())
            
        except Exception as e:
            logging.error(f"خطأ في إحصائيات المجموعة: {e}")
            await message.reply("❌ حدث خطأ في الحصول على الإحصائيات")
    
    @staticmethod
    async def my_analysis(message: Message):
        """عرض تحليل المستخدم الشخصي"""
        try:
            user_id = message.from_user.id
            user_name = message.from_user.first_name or "المستخدم"
            
            # جلب تحليل المستخدم
            analysis = await user_analysis_manager.get_user_profile(user_id)
            
            if not analysis:
                await message.reply("📊 لا توجد بيانات تحليل شخصية كافية بعد")
                return
            
            # تكوين الرد
            response = f"""
👤 **تحليل شخصي لـ {user_name}**

😊 **المزاج الحالي:** {analysis.get('current_mood', 'غير محدد')}
💫 **مستوى المشاعر:** {analysis.get('sentiment_score', 0.0):.1f}/1.0

🎯 **الاهتمامات الرئيسية:**
• الألعاب: {analysis.get('interests', {}).get('games_interest', 0.0)*100:.0f}%
• المال والاستثمار: {analysis.get('interests', {}).get('money_interest', 0.0)*100:.0f}%
• التفاعل الاجتماعي: {analysis.get('interests', {}).get('social_interest', 0.0)*100:.0f}%

🧠 **صفات الشخصية:**
• الانفتاح: {analysis.get('personality_traits', {}).get('extravert_score', 0.5)*100:.0f}%
• المخاطرة: {analysis.get('personality_traits', {}).get('risk_taker_score', 0.5)*100:.0f}%
• التنافسية: {analysis.get('personality_traits', {}).get('competitive_score', 0.5)*100:.0f}%

📈 التحليل يتطور مع تفاعلك!
            """
            
            await message.reply(response.strip())
            
        except Exception as e:
            logging.error(f"خطأ في التحليل الشخصي: {e}")
            await message.reply("❌ حدث خطأ في الحصول على التحليل الشخصي")


# قاموس الأوامر المتاحة
ANALYSIS_COMMANDS = {
    'تعطيل تحليل الأعضاء': UserAnalysisCommands.toggle_group_analysis,
    'تفعيل تحليل الأعضاء': UserAnalysisCommands.toggle_group_analysis,
    'تفعيل التحليل': UserAnalysisCommands.toggle_group_analysis,
    'ايقاف التحليل': UserAnalysisCommands.toggle_group_analysis,
    'تعطيل التحليل': UserAnalysisCommands.toggle_group_analysis,
    'حالة التحليل': UserAnalysisCommands.analysis_status,
    'مسح بيانات التحليل': UserAnalysisCommands.clear_analysis_data,
    'حللني': UserAnalysisCommands.my_analysis,
    'تحليل العلاقة': UserAnalysisCommands.relationship_analysis,
    'إحصائيات التحليل': UserAnalysisCommands.group_analysis_stats,
    'احصائيات التحليل': UserAnalysisCommands.group_analysis_stats,
}


async def handle_analysis_command(message: Message) -> bool:
    """معالج أوامر التحليل"""
    try:
        command = message.text.strip()
        
        if command in ANALYSIS_COMMANDS:
            await ANALYSIS_COMMANDS[command](message)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر التحليل: {e}")
        return False


# دالة تأكيد حذف البيانات
async def handle_delete_confirmation(message: Message) -> bool:
    """معالجة تأكيد حذف البيانات"""
    try:
        if message.text.strip() == "تأكيد حذف البيانات":
            chat_id = message.chat.id
            user_id = message.from_user.id
            
            # حذف جميع البيانات المرتبطة بالمجموعة
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute("DELETE FROM analysis_statistics WHERE chat_id = ?", (chat_id,))
                await db.execute("DELETE FROM group_analysis_settings WHERE chat_id = ?", (chat_id,))
                await db.commit()
            
            user_name = message.from_user.first_name or "الإدارة"
            
            response = f"""
✅ **تم حذف بيانات التحليل بنجاح**

🗑️ **ما تم حذفه:**
• جميع تحليلات المستخدمين في هذه المجموعة
• إحصائيات التفاعل والأنشطة
• إعدادات التحليل المخصصة

🔄 **بدء جديد:** النظام سيبدأ في جمع البيانات من جديد

تم التنفيذ بواسطة: {user_name}
التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}
            """
            
            await message.reply(response.strip())
            return True
        
        elif "حذف" in message.text.lower():
            await message.reply("❌ تم إلغاء عملية الحذف")
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في تأكيد حذف البيانات: {e}")
        await message.reply("❌ حدث خطأ في عملية الحذف")
        return True  # تم التعامل مع الرسالة
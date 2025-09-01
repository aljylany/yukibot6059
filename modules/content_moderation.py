"""
نظام الإشراف على المحتوى والحذف التلقائي للمخالفات
Content Moderation and Auto-deletion System
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.types import Message
from config.hierarchy import MASTERS, GROUP_OWNERS


class ContentModerator:
    """مشرف المحتوى التلقائي"""
    
    def __init__(self):
        """تهيئة مشرف المحتوى"""
        self.violation_log = []
        
    async def handle_violation(self, message: Message, bot: Bot, analysis_result: Dict[str, Any]) -> bool:
        """معالجة المخالفة المكتشفة"""
        try:
            # التحقق من وجود مخالفة
            if analysis_result.get("is_safe", True):
                return False  # لا توجد مخالفة
            
            violations = analysis_result.get("violations", [])
            severity = analysis_result.get("severity", "low")
            confidence = analysis_result.get("confidence", 0.0)
            
            # فقط احذف إذا كانت الثقة عالية والخطورة متوسطة أو عالية
            if confidence >= 0.7 and severity in ["medium", "high"]:
                # حذف الرسالة
                await self.delete_violating_message(message, bot)
                
                # إرسال إشعار للمستخدم
                await self.notify_user_violation(message, bot, violations, severity)
                
                # إشعار السيد الأعلى ومالك المجموعة
                await self.notify_authorities(message, bot, analysis_result)
                
                # تسجيل المخالفة
                await self.log_violation(message, analysis_result)
                
                return True  # تم الحذف
            
            return False  # لم يتم الحذف
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة المخالفة: {e}")
            return False
    
    async def delete_violating_message(self, message: Message, bot: Bot):
        """حذف الرسالة المخالفة"""
        try:
            await bot.delete_message(
                chat_id=message.chat.id,
                message_id=message.message_id
            )
            logging.info(f"🗑️ تم حذف رسالة مخالفة من المستخدم {message.from_user.id}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في حذف الرسالة: {e}")
    
    async def notify_user_violation(self, message: Message, bot: Bot, violations: list, severity: str):
        """إشعار المستخدم بالمخالفة"""
        try:
            user_name = message.from_user.first_name or "المستخدم"
            
            severity_text = {
                "low": "بسيطة",
                "medium": "متوسطة", 
                "high": "خطيرة"
            }.get(severity, "غير محددة")
            
            violations_text = "، ".join(violations) if violations else "محتوى غير مناسب"
            
            notification = (
                f"⚠️ **تحذير - مخالفة المحتوى**\n\n"
                f"👤 {user_name}, تم حذف رسالتك لاحتوائها على مخالفة.\n\n"
                f"📋 **نوع المخالفة:** {violations_text}\n"
                f"⚖️ **درجة الخطورة:** {severity_text}\n\n"
                f"🔒 يرجى الالتزام بقوانين المجموعة وتجنب نشر المحتوى المخالف.\n"
                f"💡 في حالة الاعتراض، تواصل مع إدارة المجموعة."
            )
            
            # إرسال رسالة خاصة للمستخدم
            try:
                await bot.send_message(
                    chat_id=message.from_user.id,
                    text=notification
                )
            except:
                # إذا فشل الإرسال الخاص، أرسل في المجموعة (مع منشن)
                await bot.send_message(
                    chat_id=message.chat.id,
                    text=f"@{message.from_user.username or message.from_user.first_name}\n\n{notification}",
                    reply_to_message_id=None
                )
                
        except Exception as e:
            logging.error(f"❌ خطأ في إشعار المستخدم: {e}")
    
    async def notify_authorities(self, message: Message, bot: Bot, analysis_result: Dict[str, Any]):
        """إشعار السيد الأعلى ومالك المجموعة"""
        try:
            # معلومات المخالفة
            user_info = message.from_user
            user_name = user_info.first_name or "مجهول"
            username = f"@{user_info.username}" if user_info.username else "لا يوجد معرف"
            
            violations = analysis_result.get("violations", [])
            severity = analysis_result.get("severity", "غير محدد")
            confidence = analysis_result.get("confidence", 0.0)
            description = analysis_result.get("description", "لا يوجد وصف")
            
            # تجهيز رسالة الإشعار
            violation_report = (
                f"🚨 **تقرير مخالفة محتوى تلقائي**\n\n"
                f"👤 **المستخدم:** {user_name}\n"
                f"🆔 **المعرف:** {username}\n"
                f"🔢 **ID:** `{user_info.id}`\n"
                f"🏠 **المجموعة:** {message.chat.title}\n"
                f"📍 **معرف المجموعة:** `{message.chat.id}`\n\n"
                f"⚠️ **المخالفات المكتشفة:**\n"
            )
            
            if violations:
                for i, violation in enumerate(violations, 1):
                    violation_report += f"  {i}. {violation}\n"
            else:
                violation_report += "  • محتوى غير مناسب\n"
            
            violation_report += (
                f"\n📊 **تفاصيل التحليل:**\n"
                f"🎯 درجة الثقة: {confidence:.1%}\n"
                f"⚖️ مستوى الخطورة: {severity}\n"
                f"📝 الوصف: {description[:100]}...\n\n"
                f"🗑️ **الإجراء المتخذ:** تم حذف المحتوى تلقائياً\n"
                f"⏰ **التوقيت:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            
            # قائمة المسؤولين للإشعار
            authorities_to_notify = set()
            
            # إضافة السيد الأعلى (من MASTERS)
            if hasattr(MASTERS, '__iter__'):
                authorities_to_notify.update(MASTERS)
            
            # إضافة مالكي المجموعة
            try:
                group_owners = GROUP_OWNERS.get(message.chat.id, [])
                if group_owners:
                    authorities_to_notify.update(group_owners)
            except:
                pass
            
            # إضافة مشرفين معروفين
            known_admins = [6524680126]  # السيد الأعلى المعروف
            authorities_to_notify.update(known_admins)
            
            # إرسال الإشعار لكل مسؤول
            for admin_id in authorities_to_notify:
                try:
                    await bot.send_message(
                        chat_id=admin_id,
                        text=violation_report,
                        parse_mode="Markdown"
                    )
                    logging.info(f"📤 تم إرسال تقرير المخالفة للمشرف {admin_id}")
                except Exception as send_error:
                    logging.error(f"❌ فشل إرسال الإشعار للمشرف {admin_id}: {send_error}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إشعار المسؤولين: {e}")
    
    async def log_violation(self, message: Message, analysis_result: Dict[str, Any]):
        """تسجيل المخالفة في قاعدة البيانات"""
        try:
            from database.operations import execute_query
            
            # بيانات المخالفة
            user_id = message.from_user.id
            chat_id = message.chat.id
            violations_json = str(analysis_result.get("violations", []))
            severity = analysis_result.get("severity", "unknown")
            confidence = analysis_result.get("confidence", 0.0)
            timestamp = datetime.now().isoformat()
            
            # إدراج المخالفة في قاعدة البيانات
            await execute_query(
                """
                INSERT OR IGNORE INTO content_violations 
                (user_id, chat_id, violations, severity, confidence, timestamp)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (user_id, chat_id, violations_json, severity, confidence, timestamp)
            )
            
            logging.info(f"📝 تم تسجيل المخالفة للمستخدم {user_id} في المجموعة {chat_id}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تسجيل المخالفة: {e}")
    
    async def init_violations_database(self):
        """تهيئة جدول المخالفات في قاعدة البيانات"""
        try:
            from database.operations import execute_query
            
            await execute_query(
                """
                CREATE TABLE IF NOT EXISTS content_violations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    violations TEXT,
                    severity TEXT,
                    confidence REAL,
                    timestamp TEXT,
                    UNIQUE(user_id, chat_id, timestamp)
                )
                """
            )
            
            logging.info("✅ تم تهيئة جدول المخالفات")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة جدول المخالفات: {e}")


# إنشاء مثيل مشرف المحتوى
content_moderator = ContentModerator()
"""
مدير الإشعارات للقناة الفرعية
Notification Manager for Sub-channel
"""

import logging
from datetime import datetime
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config.settings import NOTIFICATION_CHANNEL, ADMINS


class NotificationManager:
    """مدير الإشعارات المتقدم"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.channel_id = NOTIFICATION_CHANNEL["chat_id"]
        self.enabled = NOTIFICATION_CHANNEL["enabled"]
    
    async def send_notification(self, message: str, parse_mode: str = "HTML") -> bool:
        """إرسال إشعار أساسي إلى القناة"""
        if not self.enabled:
            return False
            
        try:
            await self.bot.send_message(
                chat_id=self.channel_id,
                text=message,
                parse_mode=parse_mode
            )
            logging.info("✅ تم إرسال الإشعار إلى القناة الفرعية")
            return True
        except TelegramForbiddenError:
            logging.error("❌ البوت محظور من إرسال الرسائل للقناة الفرعية")
            return False
        except TelegramBadRequest as e:
            logging.error(f"❌ خطأ في إرسال الإشعار للقناة: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ خطأ غير متوقع في إرسال الإشعار: {e}")
            return False
    
    async def send_new_group_notification(self, group_info: Dict[str, Any], 
                                        admins_info: list) -> bool:
        """إشعار إضافة البوت لمجموعة جديدة"""
        if not NOTIFICATION_CHANNEL["send_new_group_notifications"]:
            return False
        
        # تنسيق قائمة المشرفين
        admins_text = "\n".join(admins_info) if admins_info else "❌ لا يمكن جلب معلومات المشرفين"
        
        message = f"""
🎉 <b>تم إضافة البوت إلى مجموعة جديدة!</b>

📊 <b>معلومات المجموعة:</b>
🏷️ <b>الاسم:</b> {group_info['title']}
🆔 <b>المعرف:</b> <code>{group_info['id']}</code>
📱 <b>اسم المستخدم:</b> {group_info['username']}
👥 <b>عدد الأعضاء:</b> {group_info['members_count']}
📝 <b>النوع:</b> {group_info['type']}
📄 <b>الوصف:</b> {group_info['description']}

👥 <b>مشرفو المجموعة:</b>
{admins_text}

⏰ <b>تاريخ الإضافة:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
🤖 <b>البوت جاهز للعمل في هذه المجموعة!</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_bot_promotion_notification(self, group_info: Dict[str, Any]) -> bool:
        """إشعار ترقية البوت لمشرف"""
        if not NOTIFICATION_CHANNEL["send_bot_updates"]:
            return False
        
        message = f"""
⬆️ <b>تم ترقية البوت لمشرف!</b>

🏷️ <b>المجموعة:</b> {group_info['title']}
🆔 <b>المعرف:</b> <code>{group_info['id']}</code>
⏰ <b>تاريخ الترقية:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🎯 <b>الآن البوت يمتلك صلاحيات إدارية أكبر!</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_bot_removal_notification(self, group_info: Dict[str, Any]) -> bool:
        """إشعار إزالة البوت من المجموعة"""
        if not NOTIFICATION_CHANNEL["send_bot_updates"]:
            return False
        
        message = f"""
😢 <b>تم إزالة البوت من المجموعة</b>

🏷️ <b>المجموعة:</b> {group_info['title']}
🆔 <b>المعرف:</b> <code>{group_info['id']}</code>
⏰ <b>تاريخ الإزالة:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

👋 <b>وداعاً أيها الأصدقاء!</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_error_alert(self, error_type: str, error_details: str, 
                             group_id: Optional[int] = None) -> bool:
        """إشعار تنبيه بالأخطاء المهمة"""
        if not NOTIFICATION_CHANNEL["send_admin_alerts"]:
            return False
        
        group_text = f"\n🆔 <b>معرف المجموعة:</b> <code>{group_id}</code>" if group_id else ""
        
        message = f"""
⚠️ <b>تنبيه: حدث خطأ في البوت</b>

🔍 <b>نوع الخطأ:</b> {error_type}
📝 <b>تفاصيل الخطأ:</b> 
<code>{error_details}</code>{group_text}

⏰ <b>وقت الخطأ:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🔧 <b>يرجى مراجعة السجلات لمزيد من التفاصيل</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_daily_stats(self, stats: Dict[str, Any]) -> bool:
        """إشعار الإحصائيات اليومية"""
        message = f"""
📊 <b>إحصائيات البوت اليومية</b>

📅 <b>التاريخ:</b> {datetime.now().strftime("%Y-%m-%d")}

📈 <b>إحصائيات اليوم:</b>
👥 <b>المجموعات النشطة:</b> {stats.get('active_groups', 0)}
👤 <b>المستخدمين النشطين:</b> {stats.get('active_users', 0)}
💬 <b>الرسائل المعالجة:</b> {stats.get('messages_processed', 0)}
🎮 <b>الأوامر المنفذة:</b> {stats.get('commands_executed', 0)}

🆕 <b>النشاط الجديد:</b>
➕ <b>مجموعات جديدة:</b> {stats.get('new_groups', 0)}
👤 <b>مستخدمين جدد:</b> {stats.get('new_users', 0)}

---
🤖 <b>البوت يعمل بشكل طبيعي</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_maintenance_notification(self, maintenance_type: str, 
                                          duration: str = "غير محدد") -> bool:
        """إشعار صيانة البوت"""
        message = f"""
🔧 <b>إشعار صيانة البوت</b>

🛠️ <b>نوع الصيانة:</b> {maintenance_type}
⏱️ <b>المدة المتوقعة:</b> {duration}
⏰ <b>وقت البدء:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📢 <b>سيتم إيقاف البوت مؤقتاً لإجراء الصيانة اللازمة</b>

🙏 <b>نعتذر عن أي إزعاج</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def send_startup_notification(self, version: str = "1.0") -> bool:
        """إشعار بدء تشغيل البوت"""
        message = f"""
🚀 <b>تم بدء تشغيل البوت بنجاح!</b>

📱 <b>اسم البوت:</b> Yuki Economic Bot
🔖 <b>الإصدار:</b> {version}
⏰ <b>وقت التشغيل:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

✅ <b>جميع الأنظمة تعمل بشكل طبيعي</b>
🎮 <b>البوت جاهز لاستقبال الأوامر</b>

---
💡 <b>نظام الإشعارات نشط ويعمل بكفاءة</b>
        """
        
        return await self.send_notification(message.strip())
    
    async def test_notification_channel(self) -> bool:
        """اختبار اتصال القناة الفرعية"""
        try:
            test_message = f"""
🧪 <b>اختبار نظام الإشعارات</b>

✅ <b>القناة الفرعية متصلة بنجاح!</b>
⏰ <b>وقت الاختبار:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

🔗 <b>معرف القناة:</b> <code>{self.channel_id}</code>
🤖 <b>البوت يمكنه إرسال الإشعارات بنجاح</b>
            """
            
            return await self.send_notification(test_message.strip())
        except Exception as e:
            logging.error(f"خطأ في اختبار القناة الفرعية: {e}")
            return False


# دالات مساعدة للاستخدام السريع
async def send_quick_notification(bot: Bot, message: str) -> bool:
    """إرسال إشعار سريع"""
    manager = NotificationManager(bot)
    return await manager.send_notification(message)


async def send_admin_alert(bot: Bot, error_msg: str, group_id: Optional[int] = None) -> bool:
    """إرسال تنبيه للمديرين"""
    manager = NotificationManager(bot)
    return await manager.send_error_alert("خطأ عام", error_msg, group_id)
"""
مدير الإشعارات للقناة الفرعية
Notification Manager for Sub-channel
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config.settings import NOTIFICATION_CHANNEL, ADMINS


class NotificationManager:
    """مدير الإشعارات المتقدم"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        # تحديث الإعدادات في كل مرة لضمان استخدام أحدث قيم
        from config.settings import NOTIFICATION_CHANNEL
        self.channel_id = NOTIFICATION_CHANNEL["chat_id"]
        self.enabled = NOTIFICATION_CHANNEL["enabled"]
    
    async def send_notification(self, message: str, parse_mode: str = "HTML") -> bool:
        """إرسال إشعار أساسي إلى القناة"""
        # تحديث الإعدادات في كل مرة
        from config.settings import NOTIFICATION_CHANNEL
        self.channel_id = NOTIFICATION_CHANNEL["chat_id"]
        self.enabled = NOTIFICATION_CHANNEL["enabled"]
        
        if not self.enabled or not self.channel_id:
            logging.warning("نظام الإشعارات معطل أو معرف القناة غير محدد")
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
        """إشعار إضافة البوت لمجموعة جديدة مع تفاصيل شاملة"""
        if not NOTIFICATION_CHANNEL["send_new_group_notifications"]:
            return False
        
        # تنسيق قائمة المشرفين مع تفاصيل أكثر
        if admins_info and len(admins_info) > 0:
            admins_text = "\n".join(admins_info)
            admin_count = len([admin for admin in admins_info if not admin.startswith("❌")])
        else:
            admins_text = "❌ لا يمكن جلب معلومات المشرفين"
            admin_count = 0
        
        # إنشاء رابط المجموعة إذا كان متاحاً
        group_link = f"https://t.me/{group_info['username']}" if group_info.get('username') else "❌ لا يوجد رابط عام"
        
        message = f"""
🎉 <b>تم إضافة البوت إلى مجموعة جديدة!</b>

📊 <b>معلومات المجموعة الكاملة:</b>
🏷️ <b>الاسم:</b> {group_info['title']}
🆔 <b>المعرف:</b> <code>{group_info['id']}</code>
📱 <b>اسم المستخدم:</b> @{group_info.get('username', 'غير متاح')}
🔗 <b>رابط المجموعة:</b> {group_link}
👥 <b>عدد الأعضاء:</b> {group_info.get('members_count', 'غير محدد')}
👑 <b>عدد المشرفين:</b> {admin_count}
📝 <b>النوع:</b> {group_info.get('type', 'مجموعة')}
📄 <b>الوصف:</b> {group_info.get('description', 'لا يوجد وصف')}

👥 <b>قائمة المشرفين (الأسماء واليوزرات):</b>
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
        """إشعار بدء تشغيل البوت مع حساب وقت التشغيل"""
        # حساب وقت التشغيل
        try:
            from main import BOT_START_TIME
            if BOT_START_TIME:
                uptime = datetime.now() - BOT_START_TIME
                uptime_text = self._format_uptime(uptime)
            else:
                uptime_text = "غير محدد"
        except:
            uptime_text = "غير محدد"
        
        message = f"""
🚀 <b>تم بدء تشغيل البوت بنجاح!</b>

📱 <b>اسم البوت:</b> Yuki Economic Bot
🔖 <b>الإصدار:</b> {version}
⏰ <b>وقت التشغيل:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
⏱️ <b>مدة التشغيل الحالية:</b> {uptime_text}

✅ <b>جميع الأنظمة تعمل بشكل طبيعي</b>
🎮 <b>البوت جاهز لاستقبال الأوامر</b>
🔄 <b>آخر إعادة تشغيل:</b> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

---
💡 <b>نظام الإشعارات نشط ويعمل بكفاءة</b>
        """
        
        return await self.send_notification(message.strip())
    
    def _format_uptime(self, uptime: timedelta) -> str:
        """تنسيق وقت التشغيل بشكل مقروء"""
        try:
            total_seconds = int(uptime.total_seconds())
            days = total_seconds // 86400
            hours = (total_seconds % 86400) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            if days > 0:
                return f"{days} يوم، {hours} ساعة، {minutes} دقيقة"
            elif hours > 0:
                return f"{hours} ساعة، {minutes} دقيقة، {seconds} ثانية"
            elif minutes > 0:
                return f"{minutes} دقيقة، {seconds} ثانية"
            else:
                return f"{seconds} ثانية"
        except:
            return "غير محدد"
    
    async def get_uptime(self) -> str:
        """حساب وقت التشغيل الحالي"""
        try:
            from main import BOT_START_TIME
            if BOT_START_TIME:
                uptime = datetime.now() - BOT_START_TIME
                return self._format_uptime(uptime)
            else:
                return "غير محدد"
        except:
            return "غير محدد"
    
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
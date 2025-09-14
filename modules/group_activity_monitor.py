"""
نظام مراقبة نشاط المجموعات - Group Activity Monitor
يراقب نشاط المجموعات ويحدد الأوقات المناسبة للتفاعل التلقائي
"""

import logging
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from aiogram.types import Message
from database.operations import execute_query


@dataclass
class GroupActivity:
    """معلومات نشاط مجموعة واحدة"""
    chat_id: int
    last_message_time: datetime
    messages_count_1h: int  # عدد الرسائل في آخر ساعة
    messages_count_24h: int  # عدد الرسائل في آخر 24 ساعة
    active_users_1h: Set[int]  # المستخدمين النشطين في آخر ساعة
    active_users_24h: Set[int]  # المستخدمين النشطين في آخر 24 ساعة
    last_yuki_message: Optional[datetime]  # آخر رسالة من يوكي
    silence_duration: float  # مدة الصمت بالدقائق
    interaction_attempts_today: int  # عدد محاولات التفاعل اليوم


class GroupActivityMonitor:
    """نظام مراقبة نشاط المجموعات"""
    
    def __init__(self):
        self.groups_activity: Dict[int, GroupActivity] = {}
        self.bot_user_id = None
        
        # إعدادات المراقبة
        self.settings = {
            # حد الصمت للتفاعل التلقائي (بالدقائق)
            'silence_threshold_minutes': 30,
            
            # الحد الأدنى لعدد الرسائل قبل السماح بالتفاعل
            'min_messages_24h': 10,
            
            # الحد الأقصى لمحاولات التفاعل في اليوم
            'max_interactions_per_day': 3,
            
            # ساعات النوم (لا تفاعل تلقائي)
            'sleep_hours': [0, 1, 2, 3, 4, 5],  # منتصف الليل حتى 6 صباحاً
            
            # الحد الأدنى للمستخدمين النشطين
            'min_active_users': 2,
            
            # فترة تنظيف البيانات (بالدقائق)
            'cleanup_interval': 60
        }
        
        # آخر تنظيف للبيانات
        self.last_cleanup = datetime.now()
        
        logging.info("🎯 تم تهيئة نظام مراقبة نشاط المجموعات")
    
    def set_bot_user_id(self, bot_user_id: int):
        """تحديد معرف البوت"""
        self.bot_user_id = bot_user_id
        logging.info(f"🤖 تم تحديد معرف البوت: {bot_user_id}")
    
    async def track_message(self, message: Message):
        """تتبع رسالة جديدة في المجموعة"""
        try:
            if not message.chat or message.chat.type not in ['group', 'supergroup']:
                return  # فقط المجموعات
            
            chat_id = message.chat.id
            user_id = message.from_user.id if message.from_user else 0
            current_time = datetime.now()
            
            # إنشاء أو تحديث معلومات المجموعة
            if chat_id not in self.groups_activity:
                self.groups_activity[chat_id] = GroupActivity(
                    chat_id=chat_id,
                    last_message_time=current_time,
                    messages_count_1h=0,
                    messages_count_24h=0,
                    active_users_1h=set(),
                    active_users_24h=set(),
                    last_yuki_message=None,
                    silence_duration=0,
                    interaction_attempts_today=0
                )
            
            activity = self.groups_activity[chat_id]
            
            # تحديث معلومات النشاط
            previous_time = activity.last_message_time
            activity.last_message_time = current_time
            
            # حساب مدة الصمت قبل هذه الرسالة
            if previous_time:
                silence_minutes = (current_time - previous_time).total_seconds() / 60
                activity.silence_duration = max(0, silence_minutes)
            
            # تتبع رسائل يوكي
            if user_id == self.bot_user_id:
                activity.last_yuki_message = current_time
            else:
                # إضافة للإحصائيات (فقط رسائل المستخدمين، ليس البوت)
                activity.messages_count_1h += 1
                activity.messages_count_24h += 1
                activity.active_users_1h.add(user_id)
                activity.active_users_24h.add(user_id)
            
            # تنظيف البيانات القديمة إذا احتجنا
            await self._cleanup_old_data()
            
        except Exception as e:
            logging.error(f"خطأ في تتبع رسالة المجموعة: {e}")
    
    async def _cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        try:
            current_time = datetime.now()
            
            # تنظيف كل ساعة
            if (current_time - self.last_cleanup).total_seconds() < self.settings['cleanup_interval'] * 60:
                return
            
            self.last_cleanup = current_time
            logging.info("🧹 بدء تنظيف بيانات مراقبة المجموعات القديمة")
            
            for chat_id, activity in self.groups_activity.items():
                # إعادة تعيين العدادات اليومية إذا مر يوم جديد
                if activity.last_yuki_message:
                    if (current_time.date() - activity.last_yuki_message.date()).days >= 1:
                        activity.interaction_attempts_today = 0
                
                # تنظيف قوائم المستخدمين والعدادات (مؤقتاً - في تطبيق حقيقي نحتاج تتبع الوقت)
                # هنا سنقوم بتقدير تقريبي
                activity.messages_count_1h = max(0, activity.messages_count_1h - 10)  # تقليل تدريجي
                activity.messages_count_24h = max(0, activity.messages_count_24h - 1)  # تقليل تدريجي
                
                # تنظيف قوائم المستخدمين النشطين (تقدير تقريبي)
                if len(activity.active_users_1h) > 20:
                    # الحفاظ على 10 مستخدمين فقط من الأحدث
                    activity.active_users_1h = set(list(activity.active_users_1h)[-10:])
                
                if len(activity.active_users_24h) > 50:
                    # الحفاظ على 30 مستخدم فقط من الأحدث
                    activity.active_users_24h = set(list(activity.active_users_24h)[-30:])
            
            logging.info(f"✅ تم تنظيف بيانات {len(self.groups_activity)} مجموعة")
            
        except Exception as e:
            logging.error(f"خطأ في تنظيف البيانات: {e}")
    
    def is_group_quiet(self, chat_id: int) -> bool:
        """فحص ما إذا كانت المجموعة هادئة وتحتاج تفاعل"""
        try:
            if chat_id not in self.groups_activity:
                return False
            
            activity = self.groups_activity[chat_id]
            current_time = datetime.now()
            
            # فحص الشروط الأساسية
            conditions = {
                'silence_duration': activity.silence_duration >= self.settings['silence_threshold_minutes'],
                'has_enough_activity': activity.messages_count_24h >= self.settings['min_messages_24h'],
                'not_too_many_attempts': activity.interaction_attempts_today < self.settings['max_interactions_per_day'],
                'enough_users': len(activity.active_users_24h) >= self.settings['min_active_users'],
                'not_sleep_time': current_time.hour not in self.settings['sleep_hours'],
                'not_recent_yuki': True
            }
            
            # فحص ما إذا كان يوكي تكلم مؤخراً
            if activity.last_yuki_message:
                minutes_since_yuki = (current_time - activity.last_yuki_message).total_seconds() / 60
                conditions['not_recent_yuki'] = minutes_since_yuki >= 15  # على الأقل 15 دقيقة منذ آخر رسالة ليوكي
            
            # تسجيل تفصيلي لأغراض التطوير
            failed_conditions = [cond for cond, result in conditions.items() if not result]
            if failed_conditions:
                logging.debug(f"🔍 المجموعة {chat_id} لا تحتاج تفاعل - الشروط الفاشلة: {failed_conditions}")
            
            return all(conditions.values())
            
        except Exception as e:
            logging.error(f"خطأ في فحص هدوء المجموعة: {e}")
            return False
    
    def get_interaction_context(self, chat_id: int) -> Dict:
        """الحصول على سياق للتفاعل مع المجموعة"""
        try:
            if chat_id not in self.groups_activity:
                return {}
            
            activity = self.groups_activity[chat_id]
            current_time = datetime.now()
            
            # تحديد نوع التفاعل المناسب
            interaction_type = self._determine_interaction_type(activity, current_time)
            
            context = {
                'chat_id': chat_id,
                'silence_duration': activity.silence_duration,
                'messages_24h': activity.messages_count_24h,
                'active_users_count': len(activity.active_users_24h),
                'interaction_type': interaction_type,
                'current_hour': current_time.hour,
                'is_weekend': current_time.weekday() >= 5,  # السبت والأحد
                'attempts_today': activity.interaction_attempts_today
            }
            
            return context
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على سياق التفاعل: {e}")
            return {}
    
    def _determine_interaction_type(self, activity: GroupActivity, current_time: datetime) -> str:
        """تحديد نوع التفاعل المناسب"""
        try:
            # على أساس الوقت
            hour = current_time.hour
            
            if 6 <= hour < 12:
                return 'morning'  # صباح
            elif 12 <= hour < 17:
                return 'afternoon'  # بعد الظهر
            elif 17 <= hour < 22:
                return 'evening'  # مساء
            else:
                return 'night'  # ليل
                
        except Exception as e:
            logging.error(f"خطأ في تحديد نوع التفاعل: {e}")
            return 'general'
    
    def mark_interaction_attempt(self, chat_id: int):
        """تسجيل محاولة تفاعل تلقائي"""
        try:
            if chat_id in self.groups_activity:
                self.groups_activity[chat_id].interaction_attempts_today += 1
                logging.info(f"📊 تم تسجيل محاولة تفاعل للمجموعة {chat_id} - العدد اليومي: {self.groups_activity[chat_id].interaction_attempts_today}")
        except Exception as e:
            logging.error(f"خطأ في تسجيل محاولة التفاعل: {e}")
    
    def get_quiet_groups(self) -> List[int]:
        """الحصول على قائمة المجموعات الهادئة التي تحتاج تفاعل"""
        try:
            quiet_groups = []
            for chat_id in self.groups_activity:
                if self.is_group_quiet(chat_id):
                    quiet_groups.append(chat_id)
            
            return quiet_groups
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على المجموعات الهادئة: {e}")
            return []
    
    def get_activity_stats(self, chat_id: int) -> Dict:
        """الحصول على إحصائيات نشاط مجموعة"""
        try:
            if chat_id not in self.groups_activity:
                return {}
            
            activity = self.groups_activity[chat_id]
            
            return {
                'silence_duration': round(activity.silence_duration, 1),
                'messages_1h': activity.messages_count_1h,
                'messages_24h': activity.messages_count_24h,
                'active_users_1h': len(activity.active_users_1h),
                'active_users_24h': len(activity.active_users_24h),
                'interactions_today': activity.interaction_attempts_today,
                'last_message': activity.last_message_time.strftime("%H:%M") if activity.last_message_time else None,
                'last_yuki_message': activity.last_yuki_message.strftime("%H:%M") if activity.last_yuki_message else None
            }
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على إحصائيات النشاط: {e}")
            return {}


# إنشاء نسخة مشتركة من النظام
group_activity_monitor = GroupActivityMonitor()
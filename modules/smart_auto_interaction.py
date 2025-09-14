"""
نظام التفاعل التلقائي الذكي ليوكي - Smart Auto Interaction System
النظام الرئيسي الذي يدمج مراقبة النشاط مع التفاعل التلقائي الطبيعي
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from aiogram import Bot
from aiogram.types import Message

from modules.group_activity_monitor import group_activity_monitor
from modules.real_ai import real_yuki_ai


class SmartAutoInteraction:
    """النظام الذكي للتفاعل التلقائي"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.is_running = False
        self.task = None
        
        # إعدادات النظام
        self.settings = {
            # كم مرة نفحص المجموعات (بالدقائق)
            'check_interval_minutes': 5,
            
            # نسبة احتمال التفاعل عند تحقق الشروط (0.0 - 1.0)
            'interaction_probability': 0.3,  # 30% احتمال
            
            # تأخير عشوائي قبل الرد (بالثواني)
            'random_delay_min': 30,
            'random_delay_max': 180,  # من 30 ثانية إلى 3 دقائق
            
            # أقصى عدد مجموعات للتفاعل معها في كل دورة
            'max_groups_per_cycle': 2,
            
            # فترة الراحة بين التفاعلات (بالدقائق)
            'rest_between_interactions': 10,
            
            # تمكين/تعطيل النظام
            'enabled': True
        }
        
        # متتبع آخر تفاعل
        self.last_interaction_time = None
        self.interaction_count_today = 0
        self.daily_reset_date = datetime.now().date()
        
        logging.info("🎯 تم تهيئة نظام التفاعل التلقائي الذكي")
    
    async def start_service(self):
        """بدء خدمة التفاعل التلقائي في الخلفية"""
        if self.is_running:
            logging.warning("⚠️ خدمة التفاعل التلقائي تعمل بالفعل")
            return
        
        if not self.settings['enabled']:
            logging.info("ℹ️ نظام التفاعل التلقائي معطل")
            return
        
        self.is_running = True
        self.task = asyncio.create_task(self._interaction_service_loop())
        logging.info("🚀 تم بدء خدمة التفاعل التلقائي")
    
    async def stop_service(self):
        """إيقاف خدمة التفاعل التلقائي"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        
        logging.info("🛑 تم إيقاف خدمة التفاعل التلقائي")
    
    async def _interaction_service_loop(self):
        """الحلقة الرئيسية لخدمة التفاعل التلقائي"""
        try:
            while self.is_running:
                await self._check_and_interact()
                
                # انتظار قبل الفحص التالي
                await asyncio.sleep(self.settings['check_interval_minutes'] * 60)
                
        except asyncio.CancelledError:
            logging.info("تم إلغاء خدمة التفاعل التلقائي")
        except Exception as e:
            logging.error(f"خطأ في خدمة التفاعل التلقائي: {e}")
            self.is_running = False
    
    async def _check_and_interact(self):
        """فحص المجموعات والتفاعل إذا احتجت"""
        try:
            # إعادة تعيين العداد اليومي
            self._reset_daily_counter()
            
            # فحص ما إذا كان يجب أن نستريح
            if not self._should_check_now():
                return
            
            # الحصول على المجموعات الهادئة
            quiet_groups = group_activity_monitor.get_quiet_groups()
            
            if not quiet_groups:
                logging.debug("🔍 لا توجد مجموعات هادئة تحتاج تفاعل")
                return
            
            logging.info(f"🎯 تم العثور على {len(quiet_groups)} مجموعة هادئة")
            
            # اختيار مجموعات للتفاعل معها (محدود العدد)
            selected_groups = self._select_groups_for_interaction(quiet_groups)
            
            for group_id in selected_groups:
                # فرصة عشوائية للتفاعل
                if random.random() > self.settings['interaction_probability']:
                    logging.debug(f"🎲 تم تخطي المجموعة {group_id} بسبب الاحتمالية")
                    continue
                
                # تفاعل مع المجموعة
                success = await self._interact_with_group(group_id)
                
                if success:
                    self.interaction_count_today += 1
                    self.last_interaction_time = datetime.now()
                    
                    # راحة بين التفاعلات
                    if len(selected_groups) > 1:
                        wait_time = self.settings['rest_between_interactions'] * 60
                        logging.info(f"⏱️ راحة {self.settings['rest_between_interactions']} دقائق قبل التفاعل التالي")
                        await asyncio.sleep(wait_time)
                
        except Exception as e:
            logging.error(f"خطأ في فحص والتفاعل: {e}")
    
    def _should_check_now(self) -> bool:
        """فحص ما إذا كان يجب التحقق من المجموعات الآن"""
        current_time = datetime.now()
        
        # فحص الراحة بين التفاعلات
        if self.last_interaction_time:
            minutes_since_last = (current_time - self.last_interaction_time).total_seconds() / 60
            if minutes_since_last < self.settings['rest_between_interactions']:
                return False
        
        # فحص إذا تم التفاعل كثيراً اليوم
        if self.interaction_count_today >= 10:  # حد أقصى يومي
            return False
        
        # فحص ساعات النوم
        if current_time.hour in [0, 1, 2, 3, 4, 5]:
            return False
        
        return True
    
    def _reset_daily_counter(self):
        """إعادة تعيين العداد اليومي"""
        current_date = datetime.now().date()
        if current_date != self.daily_reset_date:
            self.interaction_count_today = 0
            self.daily_reset_date = current_date
            logging.info(f"🔄 تم إعادة تعيين العداد اليومي - يوم جديد: {current_date}")
    
    def _select_groups_for_interaction(self, quiet_groups: List[int]) -> List[int]:
        """اختيار مجموعات محددة للتفاعل معها"""
        try:
            # خلط القائمة وأخذ عدد محدود
            selected = random.sample(
                quiet_groups, 
                min(len(quiet_groups), self.settings['max_groups_per_cycle'])
            )
            
            # إعطاء أولوية للمجموعات الأكثر نشاطاً
            selected_with_priority = []
            for group_id in selected:
                stats = group_activity_monitor.get_activity_stats(group_id)
                if stats.get('messages_24h', 0) > 20:  # مجموعات نشيطة أولوية
                    selected_with_priority.insert(0, group_id)
                else:
                    selected_with_priority.append(group_id)
            
            return selected_with_priority
            
        except Exception as e:
            logging.error(f"خطأ في اختيار المجموعات: {e}")
            return quiet_groups[:self.settings['max_groups_per_cycle']]
    
    async def _interact_with_group(self, group_id: int) -> bool:
        """التفاعل مع مجموعة واحدة"""
        try:
            # الحصول على سياق المجموعة
            context = group_activity_monitor.get_interaction_context(group_id)
            if not context:
                logging.warning(f"⚠️ لا يمكن الحصول على سياق المجموعة {group_id}")
                return False
            
            # اختيار نوع التفاعل
            message = await self._generate_interaction_message(context)
            if not message:
                logging.warning(f"⚠️ لا يمكن إنشاء رسالة للمجموعة {group_id}")
                return False
            
            # تأخير عشوائي لمحاكاة التفكير الطبيعي
            delay = random.randint(
                self.settings['random_delay_min'], 
                self.settings['random_delay_max']
            )
            
            logging.info(f"⏳ انتظار {delay} ثانية قبل التفاعل مع المجموعة {group_id}")
            await asyncio.sleep(delay)
            
            # إرسال الرسالة
            success = await self._send_interaction_message(group_id, message)
            
            if success:
                # تسجيل التفاعل في مراقب النشاط
                group_activity_monitor.mark_interaction_attempt(group_id)
                logging.info(f"✅ تم التفاعل التلقائي مع المجموعة {group_id}: '{message[:50]}...'")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"خطأ في التفاعل مع المجموعة {group_id}: {e}")
            return False
    
    async def _generate_interaction_message(self, context: Dict) -> Optional[str]:
        """إنشاء رسالة تفاعل مناسبة للسياق باستخدام الذكاء الاصطناعي"""
        try:
            # إنشاء prompt للذكاء الاصطناعي ليبدأ محادثة طبيعية
            ai_prompt = self._build_ai_prompt_for_auto_interaction(context)
            
            # إنشاء رسالة مؤقتة للذكاء الاصطناعي
            class FakeMessage:
                def __init__(self):
                    self.text = ai_prompt
                    self.from_user = None
                    self.chat = None
            
            fake_message = FakeMessage()
            
            # استخدام نظام الذكاء الاصطناعي لإنشاء الرد
            ai_response = await real_yuki_ai.generate_smart_response(
                user_message=ai_prompt,
                user_id=None,  # لا يوجد مستخدم محدد
                chat_id=context.get('chat_id'),
                user_name="",
                message=fake_message,
                bot=self.bot
            )
            
            if ai_response and ai_response.strip():
                # تنظيف الرد من أي مراجع للـ prompt
                cleaned_response = self._clean_ai_response(ai_response)
                return cleaned_response
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء رسالة التفاعل بالذكاء الاصطناعي: {e}")
            return None
    
    def _build_ai_prompt_for_auto_interaction(self, context: Dict) -> str:
        """بناء prompt للذكاء الاصطناعي لبدء محادثة تلقائية"""
        try:
            current_hour = context.get('current_hour', datetime.now().hour)
            silence_duration = context.get('silence_duration', 0)
            messages_24h = context.get('messages_24h', 0)
            active_users = context.get('active_users_count', 0)
            is_weekend = context.get('is_weekend', False)
            
            # تحديد الوقت من اليوم
            if 6 <= current_hour < 12:
                time_context = "الصباح"
            elif 12 <= current_hour < 17:
                time_context = "بعد الظهر"
            elif 17 <= current_hour < 22:
                time_context = "المساء"
            else:
                time_context = "الليل"
            
            # بناء السياق
            situation_prompt = f"""الوضع الحالي:
- الوقت: {time_context} (الساعة {current_hour})
- المجموعة هادئة لمدة {silence_duration:.0f} دقيقة
- عدد الرسائل في 24 ساعة: {messages_24h}
- عدد المستخدمين النشطين: {active_users}
- {'نهاية الأسبوع' if is_weekend else 'يوم عادي'}

أريدك تبدأ محادثة طبيعية مع أعضاء المجموعة. تحدث كشاب ياباني عادي عمره 23 سنة يريد يكسر الجو الهادئ بطريقة لطيفة ومرحة.

لا تذكر أبداً أنك بوت أو أنك جاي تكسر الجو. تكلم بطبيعية كأنك صديق عادي بدأ يتكلم. استخدم شخصيتك اليابانية وتجاربك كطالب.

ابدأ رسالة واحدة قصيرة ومرحة:"""
            
            return situation_prompt
            
        except Exception as e:
            logging.error(f"خطأ في بناء prompt التفاعل: {e}")
            return "أريدك تبدأ محادثة طبيعية ومرحة مع أعضاء المجموعة"
    
    def _clean_ai_response(self, ai_response: str) -> str:
        """تنظيف رد الذكاء الاصطناعي من المراجع غير المرغوبة"""
        try:
            # إزالة أي إشارات للـ prompt أو التعليمات
            unwanted_phrases = [
                "الوضع الحالي:",
                "أريدك تبدأ",
                "ابدأ رسالة",
                "تحدث كشاب",
                "لا تذكر أبداً",
                "استخدم شخصيتك"
            ]
            
            cleaned = ai_response.strip()
            
            for phrase in unwanted_phrases:
                if phrase in cleaned:
                    # إزالة السطر الذي يحتوي على العبارة
                    lines = cleaned.split('\n')
                    cleaned_lines = [line for line in lines if phrase not in line]
                    cleaned = '\n'.join(cleaned_lines)
            
            # إزالة الأسطر الفارغة الزائدة
            while '\n\n\n' in cleaned:
                cleaned = cleaned.replace('\n\n\n', '\n\n')
            
            return cleaned.strip()
            
        except Exception as e:
            logging.error(f"خطأ في تنظيف رد الذكاء الاصطناعي: {e}")
            return ai_response
    
    async def _send_interaction_message(self, group_id: int, message: str) -> bool:
        """إرسال رسالة التفاعل للمجموعة"""
        try:
            # التحقق من صحة المجموعة
            try:
                chat = await self.bot.get_chat(group_id)
                if not chat:
                    logging.warning(f"⚠️ لا يمكن الوصول للمجموعة {group_id}")
                    return False
            except Exception as chat_error:
                logging.warning(f"⚠️ خطأ في الوصول للمجموعة {group_id}: {chat_error}")
                return False
            
            # إرسال الرسالة
            sent_message = await self.bot.send_message(
                chat_id=group_id,
                text=message,
                parse_mode=None  # نص عادي لتجنب مشاكل التنسيق
            )
            
            if sent_message:
                # تحديث مراقب النشاط بمعرف البوت
                if not group_activity_monitor.bot_user_id:
                    me = await self.bot.get_me()
                    group_activity_monitor.set_bot_user_id(me.id)
                
                # تتبع رسالة البوت في النشاط
                await group_activity_monitor.track_message(sent_message)
                
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"خطأ في إرسال رسالة التفاعل للمجموعة {group_id}: {e}")
            return False
    
    def get_service_status(self) -> Dict:
        """الحصول على حالة الخدمة"""
        return {
            'is_running': self.is_running,
            'enabled': self.settings['enabled'],
            'interactions_today': self.interaction_count_today,
            'last_interaction': self.last_interaction_time.strftime("%H:%M") if self.last_interaction_time else None,
            'check_interval': self.settings['check_interval_minutes'],
            'probability': self.settings['interaction_probability']
        }
    
    def update_settings(self, new_settings: Dict):
        """تحديث إعدادات النظام"""
        for key, value in new_settings.items():
            if key in self.settings:
                old_value = self.settings[key]
                self.settings[key] = value
                logging.info(f"🔧 تم تحديث إعداد {key} من {old_value} إلى {value}")
    
    async def manual_trigger_check(self) -> Dict:
        """فحص يدوي للمجموعات (لأغراض الاختبار)"""
        try:
            quiet_groups = group_activity_monitor.get_quiet_groups()
            
            result = {
                'quiet_groups_count': len(quiet_groups),
                'quiet_groups': [],
                'service_status': self.get_service_status()
            }
            
            for group_id in quiet_groups[:5]:  # أول 5 مجموعات
                stats = group_activity_monitor.get_activity_stats(group_id)
                context = group_activity_monitor.get_interaction_context(group_id)
                
                result['quiet_groups'].append({
                    'group_id': group_id,
                    'stats': stats,
                    'context': context
                })
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في الفحص اليدوي: {e}")
            return {'error': str(e)}


# متغير عام سيتم تهيئته عند بدء البوت
smart_auto_interaction: Optional[SmartAutoInteraction] = None


async def initialize_auto_interaction_system(bot: Bot):
    """تهيئة نظام التفاعل التلقائي"""
    global smart_auto_interaction
    
    try:
        smart_auto_interaction = SmartAutoInteraction(bot)
        await smart_auto_interaction.start_service()
        logging.info("🎯 تم تهيئة وبدء نظام التفاعل التلقائي الذكي")
        return True
        
    except Exception as e:
        logging.error(f"❌ خطأ في تهيئة نظام التفاعل التلقائي: {e}")
        return False


async def shutdown_auto_interaction_system():
    """إغلاق نظام التفاعل التلقائي"""
    global smart_auto_interaction
    
    if smart_auto_interaction:
        await smart_auto_interaction.stop_service()
        smart_auto_interaction = None
        logging.info("🛑 تم إغلاق نظام التفاعل التلقائي")
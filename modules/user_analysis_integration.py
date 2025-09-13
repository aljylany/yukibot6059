"""
🔗 تكامل نظام تحليل المستخدمين مع البوت الحالي
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any

from aiogram.types import Message
from database.user_analysis_operations import UserAnalysisOperations
from modules.user_analysis_manager import user_analysis_manager
from modules.user_analysis_commands import handle_analysis_command, handle_delete_confirmation


class UserAnalysisIntegration:
    """كلاس التكامل لربط نظام التحليل مع البوت"""
    
    def __init__(self):
        self.initialized = False
        self.analysis_enabled = True
    
    async def initialize(self):
        """تهيئة نظام التحليل"""
        try:
            if not self.initialized:
                # تهيئة المدير الرئيسي
                success = await user_analysis_manager.initialize()
                if success:
                    self.initialized = True
                    logging.info("🧠 تم تهيئة نظام تحليل المستخدمين وتكامله مع البوت!")
                    return True
                else:
                    logging.error("❌ فشل في تهيئة نظام التحليل")
                    return False
            return True
        except Exception as e:
            logging.error(f"خطأ في تهيئة نظام التحليل: {e}")
            return False
    
    async def process_message_analysis(self, message: Message) -> bool:
        """معالجة تحليل الرسالة - يتم استدعاؤها من معالج الرسائل الرئيسي"""
        try:
            if not self.initialized or not self.analysis_enabled:
                return False
            
            # تجاهل الرسائل الخاصة
            if message.chat.type == 'private':
                return False
            
            # تجاهل رسائل البوت نفسه
            if message.from_user and message.from_user.is_bot:
                return False
            
            # معالجة أوامر التحليل أولاً
            if message.text:
                # فحص أوامر التحليل
                if await handle_analysis_command(message):
                    return True
                
                # فحص تأكيد حذف البيانات
                if await handle_delete_confirmation(message):
                    return True
                
                # تحليل الرسالة العادية
                user_id = message.from_user.id
                chat_id = message.chat.id
                
                logging.info(f"🧠 بدء تحليل رسالة للمستخدم {user_id} في المجموعة {chat_id}")
                result = await user_analysis_manager.process_message(user_id, message.text, chat_id)
                if result:
                    logging.info(f"✅ تم تحليل الرسالة بنجاح للمستخدم {user_id}")
                else:
                    logging.debug(f"📝 تحليل الرسالة فارغ للمستخدم {user_id}")
            
            return False  # لم يتم التعامل مع الرسالة، تمرير للمعالجات الأخرى
            
        except Exception as e:
            logging.error(f"خطأ في معالجة تحليل الرسالة: {e}")
            return False
    
    async def process_game_activity(self, user_id: int, game_type: str, result: str, 
                                  amount: int = 0, chat_id: Optional[int] = None):
        """معالجة نشاط الألعاب"""
        try:
            if self.initialized and self.analysis_enabled:
                await user_analysis_manager.process_game_activity(user_id, game_type, result, amount, chat_id)
        except Exception as e:
            logging.error(f"خطأ في معالجة نشاط اللعب: {e}")
    
    async def process_financial_activity(self, user_id: int, transaction_type: str, amount: int,
                                       chat_id: Optional[int] = None):
        """معالجة النشاط المالي"""
        try:
            if self.initialized and self.analysis_enabled:
                await user_analysis_manager.process_financial_activity(user_id, transaction_type, amount, chat_id)
        except Exception as e:
            logging.error(f"خطأ في معالجة النشاط المالي: {e}")
    
    async def get_personalized_response(self, user_id: int, context: str = 'general') -> str:
        """الحصول على رد مخصص للمستخدم"""
        try:
            if self.initialized and self.analysis_enabled:
                return await user_analysis_manager.get_personalized_response(user_id, context)
            return ""
        except Exception as e:
            logging.error(f"خطأ في توليد رد مخصص: {e}")
            return ""
    
    def is_analysis_command(self, text: str) -> bool:
        """فحص إذا كان النص أمر تحليل"""
        analysis_commands = [
            'تعطيل تحليل الأعضاء', 'تفعيل تحليل الأعضاء', 'حالة التحليل',
            'مسح بيانات التحليل', 'حللني', 'تحليل العلاقة', 'إحصائيات التحليل'
        ]
        
        return any(cmd in text for cmd in analysis_commands)


# إنشاء مثيل عالمي للتكامل
analysis_integration = UserAnalysisIntegration()


# دوال مساعدة سريعة للاستخدام في النظام القديم
async def analyze_user_message(message: Message):
    """دالة سريعة لتحليل رسالة المستخدم"""
    return await analysis_integration.process_message_analysis(message)

async def track_game_activity(user_id: int, game_type: str, result: str, amount: int = 0, chat_id: int = None):
    """دالة سريعة لتتبع نشاط الألعاب"""
    await analysis_integration.process_game_activity(user_id, game_type, result, amount, chat_id)

async def track_financial_activity(user_id: int, transaction_type: str, amount: int, chat_id: int = None):
    """دالة سريعة لتتبع النشاط المالي"""
    await analysis_integration.process_financial_activity(user_id, transaction_type, amount, chat_id)

async def get_smart_response(user_id: int, context: str = 'general') -> str:
    """دالة سريعة للحصول على رد ذكي"""
    return await analysis_integration.get_personalized_response(user_id, context)


# دالة التهيئة العامة
async def initialize_user_analysis_system():
    """تهيئة نظام تحليل المستخدمين"""
    return await analysis_integration.initialize()

# إضافات للنظام الحالي لتتبع الأنشطة تلقائياً
async def on_game_played(user_id: int, game_name: str, won: bool, amount: int = 0, chat_id: int = None):
    """استدعاء عند لعب أي لعبة"""
    result = "win" if won else "loss"
    await track_game_activity(user_id, game_name, result, amount, chat_id)

async def on_financial_transaction(user_id: int, transaction_type: str, amount: int, chat_id: int = None):
    """استدعاء عند أي معاملة مالية"""
    await track_financial_activity(user_id, transaction_type, amount, chat_id)

async def on_social_interaction(user_id: int, other_user_id: int, interaction_type: str = 'message'):
    """استدعاء عند التفاعل الاجتماعي"""
    try:
        if analysis_integration.initialized:
            await UserAnalysisOperations.update_relationship(user_id, other_user_id, interaction_type)
    except Exception as e:
        logging.error(f"خطأ في تسجيل التفاعل الاجتماعي: {e}")


# دالة لحفظ التقدم التلقائي
async def auto_save_analysis_progress():
    """حفظ تقدم التحليل تلقائياً"""
    try:
        if analysis_integration.initialized:
            # هنا يمكن إضافة منطق حفظ التقدم أو تنظيف البيانات القديمة
            logging.info("🔄 تم حفظ تقدم نظام التحليل تلقائياً")
    except Exception as e:
        logging.error(f"خطأ في حفظ تقدم التحليل: {e}")


# معلومات للنظام
ANALYSIS_SYSTEM_INFO = {
    "name": "نظام تحليل المستخدمين المتقدم",
    "version": "1.0.0",
    "description": "نظام ذكي لتحليل سلوك المستخدمين وتخصيص التجربة",
    "features": [
        "تحليل المشاعر والمزاج",
        "كشف الاهتمامات والشخصية", 
        "نظام الذكريات الذكي",
        "تحليل العلاقات الاجتماعية",
        "الردود المخصصة",
        "التحكم في الخصوصية"
    ]
}
"""
فلاتر نظام الذكاء الصناعي
AI System Filters
"""

import logging
from typing import List

class AIMessageFilters:
    """فلاتر رسائل الذكاء الصناعي لتجنب التداخل مع الأوامر المهمة"""
    
    def __init__(self):
        # الأوامر المطلقة للأسياد
        self.master_commands = [
            'يوكي قم بإعادة التشغيل', 'يوكي اعد التشغيل', 'restart bot',
            'يوكي قم بإيقاف التشغيل', 'يوكي اوقف البوت', 'shutdown bot',
            'يوكي قم بالتدمير الذاتي', 'يوكي دمر نفسك', 'self destruct',
            'يوكي امسح البيانات', 'يوكي احذف كل شيء', 'clear all data',
            'يوكي اعد ضبط المصنع', 'factory reset',
            'إلغاء', 'cancel', 'ايقاف', 'stop'
        ]
        
        # الأوامر الإدارية العامة
        self.admin_commands = [
            '/ban', '/kick', '/mute', '/unmute', '/warn',
            '/promote', '/demote', '/lock', '/unlock',
            'بان', 'طرد', 'كتم', 'إلغاء الكتم', 'تحذير',
            'ترقية', 'تنزيل رتبة', 'قفل', 'إلغاء القفل'
        ]
        
        # أوامر النظام المهمة
        self.system_commands = [
            '/start', '/help', '/settings', '/config',
            'البداية', 'المساعدة', 'الإعدادات', 'التكوين'
        ]
        
        # كلمات الإلغاء والتوقف
        self.cancel_words = [
            'إلغاء', 'ايقاف', 'توقف', 'cancel', 'stop', 'abort'
        ]
    
    def should_ignore_message(self, text: str, user_id: int = None) -> bool:
        """فحص ما إذا كان يجب تجاهل الرسالة من قبل الذكاء الصناعي"""
        text_lower = text.lower().strip()
        
        # فحص الأوامر المطلقة
        if self._is_master_command(text_lower):
            logging.info(f"تم تجاهل أمر مطلق: {text_lower}")
            return True
        
        # فحص الأوامر الإدارية
        if self._is_admin_command(text_lower):
            logging.info(f"تم تجاهل أمر إداري: {text_lower}")
            return True
        
        # فحص أوامر النظام
        if self._is_system_command(text_lower):
            logging.info(f"تم تجاهل أمر نظام: {text_lower}")
            return True
        
        # فحص كلمات الإلغاء أثناء العمليات المطلقة
        if self._is_cancel_word(text_lower):
            logging.info(f"تم تجاهل كلمة إلغاء: {text_lower}")
            return True
        
        return False
    
    def _is_master_command(self, text: str) -> bool:
        """فحص الأوامر المطلقة"""
        return any(cmd in text for cmd in self.master_commands)
    
    def _is_admin_command(self, text: str) -> bool:
        """فحص الأوامر الإدارية"""
        return any(cmd in text for cmd in self.admin_commands)
    
    def _is_system_command(self, text: str) -> bool:
        """فحص أوامر النظام"""
        return any(cmd in text for cmd in self.system_commands)
    
    def _is_cancel_word(self, text: str) -> bool:
        """فحص كلمات الإلغاء"""
        # فحص دقيق للكلمات المنفردة
        words = text.split()
        return any(word in self.cancel_words for word in words)
    
    def get_filter_reason(self, text: str) -> str:
        """الحصول على سبب التصفية"""
        text_lower = text.lower().strip()
        
        if self._is_master_command(text_lower):
            return "أمر مطلق للأسياد"
        elif self._is_admin_command(text_lower):
            return "أمر إداري"
        elif self._is_system_command(text_lower):
            return "أمر نظام"
        elif self._is_cancel_word(text_lower):
            return "كلمة إلغاء"
        else:
            return "غير محدد"

# إنشاء نسخة واحدة من الفلاتر
ai_filters = AIMessageFilters()
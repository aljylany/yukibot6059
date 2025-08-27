"""
معالج الرسائل الذكي - Smart Message Processor
يدمج جميع أنظمة البوت مع الذكاء الاصطناعي لمعالجة أكثر ذكاءً
"""

import logging
import asyncio
import re
from typing import Dict, Any, Optional, List
from aiogram.types import Message
from datetime import datetime

# استيراد النظام الشامل
from modules.comprehensive_ai_system import comprehensive_ai

# استيراد الأنظمة الموجودة
from modules.yuki_ai import YukiAI
from modules.special_responses import get_response
from modules.profanity_handler_new import handle_new_profanity_system

class SmartMessageProcessor:
    """معالج الرسائل الذكي الذي يدمج جميع الأنظمة"""
    
    def __init__(self):
        self.comprehensive_ai = comprehensive_ai
        self.basic_ai = YukiAI()
        self.special_responses = get_response
        self.profanity_handler = handle_new_profanity_system
        
        # إعدادات المعالج
        self.processing_settings = {
            'ai_response_probability': 0.3,  # احتمال الرد بالذكاء الاصطناعي
            'smart_detection': True,         # التشخيص الذكي للرسائل
            'context_memory': True,          # استخدام الذاكرة السياقية
            'learning_mode': True,           # وضع التعلم
            'personality_protection': True   # حماية الشخصية
        }
        
        # أنماط الرسائل التي تحتاج رد فوري
        self.priority_patterns = [
            r'\b(يوكي|yuki)\b',              # منشن البوت
            r'\b(مساعدة|ساعدني|help)\b',      # طلب مساعدة
            r'\b(كيف|ماذا|متى|أين|لماذا|من)\b', # أسئلة
            r'\?$',                          # ينتهي بعلامة استفهام
            r'\b(شكرا|مشكور|تسلم)\b',         # شكر
            r'\b(مرحبا|هلا|السلام|أهلا)\b'   # تحية
        ]
        
        # الكلمات المفتاحية للأنظمة المختلفة
        self.system_keywords = {
            'banking': ['بنك', 'راتب', 'ايداع', 'سحب', 'حساب', 'رصيد'],
            'gaming': ['لعبة', 'العاب', 'كويز', 'معركة', 'اكس او'],
            'economy': ['استثمار', 'أسهم', 'عقار', 'مزرعة', 'قلعة'],
            'social': ['ترقية', 'ترتيب', 'احصائيات', 'معلوماتي'],
            'admin': ['بان', 'كتم', 'طرد', 'حماية', 'قفل']
        }
    
    async def process_message(self, message: Message) -> Optional[str]:
        """معالجة الرسالة الرئيسية"""
        try:
            # فحص الحماية من الكلام البذيء
            if await self._check_profanity(message):
                return None  # تم التعامل مع الرسالة البذيئة
            
            # تحليل نية الرسالة
            intent = await self._analyze_message_intent(message)
            
            # تحديد نوع المعالجة المطلوبة
            processing_type = await self._determine_processing_type(message, intent)
            
            # معالجة الرسالة حسب النوع
            if processing_type == 'ai_comprehensive':
                return await self._process_with_comprehensive_ai(message, intent)
            elif processing_type == 'ai_basic':
                return await self._process_with_basic_ai(message)
            elif processing_type == 'special_response':
                return await self._process_with_special_response(message)
            elif processing_type == 'system_command':
                return await self._process_system_command(message, intent)
            else:
                return None  # لا حاجة للرد
                
        except Exception as e:
            logging.error(f"خطأ في معالجة الرسالة: {e}")
            return None
    
    async def _check_profanity(self, message: Message) -> bool:
        """فحص والتعامل مع الكلام البذيء"""
        try:
            is_profane = await self.profanity_handler.check_message(message)
            if is_profane:
                # تم التعامل مع الرسالة داخل معالج الكلام البذيء
                logging.info(f"تم اكتشاف والتعامل مع رسالة بذيئة من {message.from_user.id}")
                return True
            return False
        except Exception as e:
            logging.error(f"خطأ في فحص الكلام البذيء: {e}")
            return False
    
    async def _analyze_message_intent(self, message: Message) -> Dict[str, Any]:
        """تحليل نية الرسالة بذكاء"""
        intent = {
            'type': 'general',
            'priority': 'low',
            'system_related': [],
            'keywords': [],
            'needs_ai': False,
            'confidence': 0.0
        }
        
        message_text = message.text.lower() if message.text else ""
        
        # فحص الأولوية العالية
        priority_score = 0
        for pattern in self.priority_patterns:
            if re.search(pattern, message_text, re.IGNORECASE):
                priority_score += 1
                intent['keywords'].extend(re.findall(pattern, message_text, re.IGNORECASE))
        
        if priority_score > 0:
            intent['priority'] = 'high' if priority_score >= 2 else 'medium'
            intent['needs_ai'] = True
        
        # فحص الأنظمة ذات الصلة
        for system, keywords in self.system_keywords.items():
            matches = [kw for kw in keywords if kw in message_text]
            if matches:
                intent['system_related'].append(system)
                intent['keywords'].extend(matches)
        
        # تحديد النوع الأساسي
        if any(kw in message_text for kw in ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'من', '؟']):
            intent['type'] = 'question'
            intent['needs_ai'] = True
        elif any(kw in message_text for kw in ['مرحبا', 'هلا', 'السلام', 'أهلا']):
            intent['type'] = 'greeting'
            intent['needs_ai'] = True
        elif any(kw in message_text for kw in ['شكرا', 'مشكور', 'تسلم']):
            intent['type'] = 'gratitude'
            intent['needs_ai'] = True
        elif 'مساعدة' in message_text or 'ساعدني' in message_text:
            intent['type'] = 'help_request'
            intent['needs_ai'] = True
            intent['priority'] = 'high'
        
        # حساب مستوى الثقة
        intent['confidence'] = min((priority_score + len(intent['system_related'])) * 0.2, 1.0)
        
        return intent
    
    async def _determine_processing_type(self, message: Message, intent: Dict[str, Any]) -> str:
        """تحديد نوع المعالجة المطلوبة"""
        
        # رد مضمون للأولوية العالية
        if intent['priority'] == 'high':
            return 'ai_comprehensive'
        
        # رد على الأسئلة والمساعدة
        if intent['type'] in ['question', 'help_request']:
            return 'ai_comprehensive'
        
        # فحص الردود الخاصة
        if self.special_responses(message.from_user.id, message.text):
            return 'special_response'
        
        # رد على الرسائل المرتبطة بالأنظمة
        if intent['system_related']:
            return 'ai_comprehensive'
        
        # رد بالذكاء الأساسي للتفاعل الاجتماعي
        if intent['type'] in ['greeting', 'gratitude']:
            return 'ai_basic'
        
        # فحص الرد العشوائي للتفاعل
        if await self.comprehensive_ai.should_respond_with_ai(message):
            return 'ai_basic'
        
        return 'none'
    
    async def _process_with_comprehensive_ai(self, message: Message, intent: Dict[str, Any]) -> str:
        """معالجة باستخدام النظام الذكي الشامل"""
        try:
            # جمع بيانات المستخدم الشاملة
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(
                message.from_user.id, message.chat.id
            )
            
            # بناء سياق إضافي بناءً على النية
            additional_context = ""
            if intent['system_related']:
                additional_context = f"🎯 النظم ذات الصلة: {', '.join(intent['system_related'])}\n"
            
            if intent['keywords']:
                additional_context += f"🔑 الكلمات المفتاحية: {', '.join(set(intent['keywords']))}\n"
            
            additional_context += f"⚡ نوع الرسالة: {intent['type']}\n"
            additional_context += f"📊 مستوى الأولوية: {intent['priority']}"
            
            # توليد الرد الذكي
            response = await self.comprehensive_ai.generate_smart_response(
                message, user_data, additional_context
            )
            
            return response
            
        except Exception as e:
            logging.error(f"خطأ في المعالجة الشاملة: {e}")
            return await self._process_with_basic_ai(message)
    
    async def _process_with_basic_ai(self, message: Message) -> str:
        """معالجة باستخدام الذكاء الأساسي"""
        try:
            user_name = message.from_user.first_name or "صديقي"
            response = await self.basic_ai.get_smart_response(message.text, user_name)
            return response
        except Exception as e:
            logging.error(f"خطأ في الذكاء الأساسي: {e}")
            return f"🤖 مرحباً {message.from_user.first_name}! يوكي هنا للمساعدة، كيف يمكنني خدمتك؟"
    
    async def _process_with_special_response(self, message: Message) -> str:
        """معالجة الردود الخاصة"""
        try:
            response = self.special_responses(message.from_user.id, message.text)
            return response
        except Exception as e:
            logging.error(f"خطأ في الردود الخاصة: {e}")
            return None
    
    async def _process_system_command(self, message: Message, intent: Dict[str, Any]) -> str:
        """معالجة أوامر النظام"""
        # هذه الدالة ستوسع لاحقاً للتعامل مع أوامر النظام المختلفة
        return None
    
    async def get_processing_stats(self) -> Dict[str, Any]:
        """إحصائيات المعالجة"""
        ai_status = self.comprehensive_ai.get_system_status()
        
        return {
            'comprehensive_ai_available': ai_status['anthropic_available'] or ai_status['gemini_available'],
            'current_ai_provider': ai_status['current_provider'],
            'basic_ai_available': True,
            'special_responses_loaded': True,
            'profanity_protection': True,
            'processing_settings': self.processing_settings
        }
    
    async def update_settings(self, new_settings: Dict[str, Any]):
        """تحديث إعدادات المعالج"""
        self.processing_settings.update(new_settings)
        logging.info(f"تم تحديث إعدادات المعالج: {new_settings}")


# إنشاء معالج الرسائل الذكي
smart_processor = SmartMessageProcessor()
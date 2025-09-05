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
from modules.enhanced_yuki_system import enhanced_yuki

class SmartMessageProcessor:
    """معالج الرسائل الذكي الذي يدمج جميع الأنظمة"""
    
    def __init__(self):
        self.comprehensive_ai = comprehensive_ai
        self.basic_ai = YukiAI()
        self.enhanced_yuki = enhanced_yuki
        self.special_responses = get_response
        
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
            # تحليل نية الرسالة
            intent = await self._analyze_message_intent(message)
            
            # تحديد نوع المعالجة المطلوبة
            processing_type = await self._determine_processing_type(message, intent)
            
            # معالجة الرسالة حسب النوع
            if processing_type == 'memory_response':
                return await self._process_memory_query(message)
            elif processing_type == 'ai_comprehensive':
                return await self._process_with_comprehensive_ai(message, intent)
            elif processing_type == 'ai_basic':
                # استخدام النظام المحسن أولاً
                return await self._process_with_enhanced_yuki(message)
            elif processing_type == 'special_response':
                return await self._process_with_special_response(message)
            elif processing_type == 'system_command':
                return await self._process_system_command(message, intent)
            else:
                return None  # لا حاجة للرد
                
        except Exception as e:
            logging.error(f"خطأ في معالجة الرسالة: {e}")
            return None
    
    
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
        
        # التحقق من وجود النص أولاً
        if not message.text:
            return intent
            
        message_text = message.text.lower()
        
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
        # أسئلة الذاكرة المحلية - ردود سريعة بدون AI
        if 'ماذا تعرف عن' in message_text or 'تعرف فلان' in message_text:
            intent['type'] = 'memory_query'
            intent['needs_ai'] = False
        elif any(kw in message_text for kw in ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'من', '؟']):
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
    
    async def _process_memory_query(self, message: Message) -> str:
        """معالجة أسئلة الذاكرة المحلية - رد سريع بدون AI"""
        try:
            if not message.text:
                return "🤔 لا أفهم السؤال"
                
            message_text = message.text.lower()
            
            # استخراج اسم الشخص من السؤال
            person_name = None
            if 'عن ' in message_text:
                # استخراج الاسم بعد "عن"
                parts = message_text.split('عن ')
                if len(parts) > 1:
                    person_name = parts[1].split()[0].strip()
            elif 'تعرف ' in message_text:
                # استخراج الاسم بعد "تعرف"
                parts = message_text.split('تعرف ')
                if len(parts) > 1:
                    person_name = parts[1].split()[0].strip()
            
            if person_name:
                # البحث في الذاكرة المشتركة
                try:
                    # أولاً، محاولة البحث في النظام الجديد
                    if self.shared_memory:
                        memory_info = await self.shared_memory.search_shared_memory(
                            message.chat.id, person_name
                        )
                        if memory_info:
                            return f"📋 **معلومات عن {person_name}:**\n\n{memory_info}\n\n✨ هذا ما أتذكره!"
                    
                    # محاولة البحث في النظام القديم كاحتياط
                    try:
                        from modules.shared_memory_sqlite import shared_group_memory_sqlite as shared_memory_db
                        memory_info = await shared_memory_db.get_group_memory(message.chat.id, person_name)
                        if memory_info:
                            return f"📋 **معلومات عن {person_name}:**\n\n{memory_info}\n\n✨ هذا ما أتذكره!"
                    except ImportError:
                        pass
                    
                    return f"🤔 لا أجد معلومات محفوظة عن {person_name} في ذاكرتي حالياً"
                    
                except Exception as e:
                    logging.error(f"خطأ في البحث في الذاكرة المشتركة: {e}")
                    return f"🤔 لا أجد معلومات محفوظة عن {person_name} في ذاكرتي حالياً"
            
            return "🤔 لا أفهم عن من تسأل تحديداً. جرب: 'ماذا تعرف عن [اسم الشخص]'"
            
        except Exception as e:
            logging.error(f"خطأ في معالج الذاكرة: {e}")
            return "❌ حدث خطأ في البحث في الذاكرة"
    
    async def _determine_processing_type(self, message: Message, intent: Dict[str, Any]) -> str:
        """تحديد نوع المعالجة المطلوبة"""
        
        # رد مضمون للأولوية العالية
        if intent['priority'] == 'high':
            return 'ai_comprehensive'
        
        # أسئلة الذاكرة المحلية - رد سريع
        if intent['type'] == 'memory_query':
            return 'memory_response'
        
        # رد على الأسئلة والمساعدة
        if intent['type'] in ['question', 'help_request']:
            return 'ai_comprehensive'
        
        # فحص الردود الخاصة
        if message.from_user and message.text and self.special_responses(message.from_user.id, message.text):
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
    
    async def _process_with_enhanced_yuki(self, message: Message) -> str:
        """معالجة باستخدام نظام يوكي المحسن مع الوصول الكامل لقاعدة البيانات"""
        try:
            if not message.from_user:
                return "🤖 مرحباً! يوكي هنا للمساعدة، كيف يمكنني خدمتك؟"
            
            user_id = message.from_user.id
            chat_id = message.chat.id
            message_text = message.text or ""
            
            # استخدام النظام المحسن
            response = await self.enhanced_yuki.generate_contextual_response(
                message_text, user_id, chat_id
            )
            
            return response
            
        except Exception as e:
            logging.error(f"خطأ في النظام المحسن: {e}")
            return await self._process_with_basic_ai(message)
    
    async def _process_with_basic_ai(self, message: Message) -> str:
        """معالجة باستخدام الذكاء الأساسي"""
        try:
            if not message.from_user:
                return "🤖 مرحباً! يوكي هنا للمساعدة، كيف يمكنني خدمتك؟"
                
            user_name = message.from_user.first_name or "صديقي"
            message_text = message.text or ""
            
            # تحقق من وجود الطريقة في basic_ai
            if hasattr(self.basic_ai, 'get_smart_response'):
                response = await self.basic_ai.get_smart_response(message_text, user_name)
            else:
                # استخدام طريقة بديلة
                response = f"🤖 مرحباً {user_name}! يوكي هنا وجاهز للمساعدة!"
            
            return response
        except Exception as e:
            logging.error(f"خطأ في الذكاء الأساسي: {e}")
            user_name = message.from_user.first_name if message.from_user else "صديقي"
            return f"🤖 مرحباً {user_name}! يوكي هنا للمساعدة، كيف يمكنني خدمتك؟"
    
    async def _process_with_special_response(self, message: Message) -> Optional[str]:
        """معالجة الردود الخاصة"""
        try:
            if not message.from_user or not message.text:
                return None
                
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
            'processing_settings': self.processing_settings
        }
    
    async def update_settings(self, new_settings: Dict[str, Any]):
        """تحديث إعدادات المعالج"""
        self.processing_settings.update(new_settings)
        logging.info(f"تم تحديث إعدادات المعالج: {new_settings}")


# إنشاء معالج الرسائل الذكي
smart_processor = SmartMessageProcessor()
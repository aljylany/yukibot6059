"""
نظام عبيد الذكي - Obaid Smart System
نظام ذكي متطور يجعل عبيد يتفاعل كعضو حقيقي في المجموعة
"""

import logging
import asyncio
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from aiogram.types import Message

class ObaidSmartSystem:
    """نظام عبيد الذكي للتفاعل الطبيعي"""
    
    def __init__(self):
        # تتبع رسائل عبيد والردود عليها
        self.obaid_messages: Dict[int, Dict] = {}  # message_id -> message_data
        self.reply_tracking: Dict[int, int] = {}  # reply_message_id -> original_message_id
        
        # معرف عبيد (براندون)
        self.OBAID_USER_ID = 6524680126
        
        # ردود يوكي بالنيابة عن عبيد
        self.smart_responses = {
            'greetings': [
                "أهلاً! عبيد قال يسلم عليك، عمره 7 سنوات ويحب الجولف! 🏌️‍♂️",
                "مرحبا! عبيد الصغير يرد عليك، يحب ألعاب الجولف كثيراً! ⛳",
                "أهلاً وسهلاً! عبيد مشغول بس قال أسلم عليك، عنده 7 سنين ويحب الرياضة! 🎮"
            ],
            'questions': [
                "عبيد يقول: إيش تقصد؟ ما فهمت! 🤔",
                "عبيد يسأل: ممكن توضح أكثر؟ أنا صغير! 😅", 
                "عبيد قال: أقدر أساعد بس وضح أكثر! 👦"
            ],
            'thanks': [
                "عبيد يقول: العفو! دائماً مستعد أساعد! 😊",
                "عبيد قال: لا شكر على واجب، أنا الولد الطيب! 🌟",
                "عبيد يقول: أهلاً وسهلاً، أنا في خدمتك! 💪"
            ],
            'compliments': [
                "عبيد يقول: شكراً! بحب لما الناس تمدحني! 😄",
                "عبيد قال: يسلمو! أنا المتفائل! ✨",
                "عبيد يقول: أي والله، أنا ولد طيب! 🥰"
            ],
            'golf_talk': [
                "عبيد يصرخ: وااااي! انت تحب الجولف مثلي؟! 🏌️‍♂️⛳",
                "عبيد يقول: الجولف رياضة رائعة! أنا ألعب كل يوم! 🏆",
                "عبيد متحمس: يللا نلعب جولف مع بعض! أنا محترف! 💪⛳"
            ],
            'age_talk': [
                "عبيد يقول: أي صح، عمري 7 سنين! كبرت شوي! 😎",
                "عبيد يقول: أنا الصغير، بس ذكي! 🧠✨", 
                "عبيد فخور: 7 سنين وما زلت أتعلم أشياء جديدة! 📚"
            ],
            'random': [
                "عبيد يسأل: وين أصدقائي؟ 👀",
                "عبيد يقول: أحب أكون مع الجماعة هنا! 🤗",
                "عبيد موجود ومستعد للمرح! 🎉",
                "عبيد يسأل: أي شخص يبي يلعب معي؟ 🎮",
                "عبيد يقول: الحمدلله على يوم جديد! 🌅"
            ]
        }
        
        # كلمات مفتاحية للردود الذكية
        self.response_triggers = {
            'greetings': ['أهلاً', 'مرحبا', 'هلا', 'أهلا', 'سلام', 'السلام'],
            'questions': ['ليش', 'كيف', 'وين', 'متى', 'مين', 'إيش', 'شو', 'ماذا'],
            'thanks': ['شكرا', 'شكراً', 'تسلم', 'مشكور', 'يعطيك العافية'],
            'compliments': ['حلو', 'جميل', 'رائع', 'ممتاز', 'حبيبي', 'طيب', 'ذكي'],
            'golf_talk': ['جولف', 'golf', 'رياضة', 'لعب', 'ملعب'],
            'age_talk': ['عمر', 'سنة', 'سنين', 'كبير', 'صغير', '7']
        }
    
    def is_obaid_message(self, user_id: int) -> bool:
        """فحص إذا كانت الرسالة من عبيد"""
        return user_id == self.OBAID_USER_ID
    
    async def track_obaid_message(self, message: Message):
        """تتبع رسائل عبيد لمعرفة الردود عليها لاحقاً"""
        if self.is_obaid_message(message.from_user.id):
            self.obaid_messages[message.message_id] = {
                'text': message.text,
                'chat_id': message.chat.id,
                'timestamp': datetime.now(),
                'user_name': message.from_user.first_name or "عبيد"
            }
            
            # حذف الرسائل القديمة (أكثر من ساعة)
            current_time = datetime.now()
            old_messages = []
            for msg_id, data in self.obaid_messages.items():
                if current_time - data['timestamp'] > timedelta(hours=1):
                    old_messages.append(msg_id)
            
            for old_msg in old_messages:
                del self.obaid_messages[old_msg]
    
    async def handle_reply_to_obaid(self, message: Message) -> Optional[str]:
        """معالجة الردود على رسائل عبيد وإرجاع رد ذكي"""
        # فحص إذا كانت الرسالة رد على رسالة عبيد
        if not message.reply_to_message:
            return None
            
        replied_message_id = message.reply_to_message.message_id
        
        # فحص إذا كانت الرسالة المردود عليها من عبيد
        if replied_message_id not in self.obaid_messages:
            return None
        
        # فحص إذا كان الرد من عبيد نفسه (تجاهل)
        if self.is_obaid_message(message.from_user.id):
            return None
            
        # تتبع الرد
        self.reply_tracking[message.message_id] = replied_message_id
        
        # تحليل محتوى الرد وإنتاج رد ذكي
        reply_text = message.text.lower() if message.text else ""
        replier_name = message.from_user.first_name or "صديق"
        
        # اختيار نوع الرد بناءً على المحتوى
        response_type = self.analyze_reply_content(reply_text)
        responses = self.smart_responses.get(response_type, self.smart_responses['random'])
        
        # إنتاج رد شخصي
        base_response = random.choice(responses)
        personal_response = f"@{replier_name} {base_response}"
        
        # إضافة سياق إضافي أحياناً
        if random.random() < 0.3:  # 30% احتمال
            extras = [
                "\nعبيد قال: بس أنا عبيد براندون! 👦",
                "\nعبيد يقول: أحب ألعب جولف! تيجي نلعب؟ ⛳",
                "\nعبيد قال: أنا ولد طيب ومؤدب! 😇",
                "\nعبيد يشكر: يوكي علمني أكون ذكي! 🤖"
            ]
            personal_response += random.choice(extras)
        
        return personal_response
    
    def analyze_reply_content(self, text: str) -> str:
        """تحليل محتوى الرد لاختيار نوع الاستجابة المناسب"""
        text = text.lower()
        
        # فحص كل نوع من المحفزات
        for response_type, triggers in self.response_triggers.items():
            for trigger in triggers:
                if trigger in text:
                    return response_type
        
        # الرد الافتراضي
        return 'random'
    
    async def should_obaid_respond_to_mention(self, message: Message) -> Optional[str]:
        """فحص إذا كان عبيد يجب أن يرد على ذكر اسمه"""
        if not message.text:
            return None
            
        # فحص إذا تم ذكر عبيد أو براندون
        text_lower = message.text.lower()
        obaid_mentions = ['عبيد', 'عبيدة', 'براندون', 'brandon', 'يوكي براندون']
        
        mentioned = False
        for mention in obaid_mentions:
            if mention in text_lower:
                mentioned = True
                break
        
        if not mentioned:
            return None
            
        # لا يرد على نفسه
        if self.is_obaid_message(message.from_user.id):
            return None
            
        # الحصول على معلومات المستخدم من الذاكرة المشتركة
        replier_name = message.from_user.first_name or "صديق"
        user_info = await self.get_user_memory_info(message.from_user.id, message.chat.id)
        
        # ردود خاصة حسب السياق
        if any(word in text_lower for word in ['أين', 'وين', 'موجود']):
            return f"عبيد يقول: أنا هنا! موجود! 👋 أهلاً {replier_name}!"
            
        elif any(word in text_lower for word in ['كيف', 'شلون', 'كيفك']):
            if user_info and 'last_interaction' in user_info:
                return f"عبيد يجيب: أنا بخير {replier_name}! آخر مرة تكلمنا كان عن {user_info.get('topic', 'أشياء حلوة')}! 😊 وانت كيفك؟"
            else:
                return f"عبيد يقول: أنا بخير {replier_name}! متفائل ونشيط! 😊 وانت كيفك؟"
            
        elif any(word in text_lower for word in ['جولف', 'golf', 'لعب', 'رياضة']):
            return f"عبيد متحمس: واااي {replier_name}! تحب الجولف مثلي؟ يللا نلعب! 🏌️‍♂️⛳"
            
        elif any(word in text_lower for word in ['عمر', 'سنة', 'كبير', 'صغير']):
            return f"عبيد يقول: أنا عمري 7 سنين {replier_name}! بس ذكي وأحب أتعلم! 🧠✨"
            
        elif any(word in text_lower for word in ['من', 'مين', 'تعرف']):
            if user_info:
                interests = user_info.get('interests', [])
                if interests:
                    return f"عبيد يقول: أنا أعرف {replier_name}! انت تحب {', '.join(interests[:2])}! أنا صديقك! 🤗"
                else:
                    return f"عبيد يقول: أنا عبيد! انت {replier_name} صديقي! تعال نتعرف أكثر! 👦✨"
            else:
                return f"عبيد يقول: أنا عبيد! انت {replier_name}، صح؟ يللا نصير أصدقاء! 🤝"
            
        else:
            # رد عام مع استخدام معلومات المستخدم إن وُجدت
            if user_info and random.random() < 0.4:  # 40% احتمال لاستخدام المعلومات
                return f"عبيد يقول: أهلاً {replier_name}! أتذكرك! نتكلم مرة ثانية؟ 😊"
            else:
                general_responses = [
                    f"عبيد يسأل: أيوه {replier_name}؟ إيش تبي؟ 😊",
                    f"عبيد يقول: نعم {replier_name}! في الخدمة! 🌟",
                    f"عبيد يرحب: أهلاً {replier_name}! قل لي إيش تريد! 👦",
                    f"عبيد يسلم: مرحبا {replier_name}! كيف أساعدك؟ 🤝"
                ]
                return random.choice(general_responses)
    
    async def random_obaid_interaction(self, chat_id: int) -> Optional[str]:
        """تفاعل عشوائي من عبيد لجعله أكثر حيوية"""
        # احتمال 2% للتفاعل العشوائي
        if random.random() > 0.02:
            return None
            
        interactions = [
            "أي أصدقاء جدد هنا؟ أنا عبيد! 👋",
            "أحد يبي يلعب جولف معي؟ 🏌️‍♂️",
            "أنا عبيد! كيفكم اليوم؟ 😊",
            "وين الجماعة؟ عبيد يدور على أصدقاء! 👀",
            "أنا مبسوط اليوم! عبيد متفائل! ✨"
        ]
        
        return random.choice(interactions)
    
    async def get_user_memory_info(self, user_id: int, chat_id: int) -> Optional[dict]:
        """الحصول على معلومات المستخدم من الذاكرة المشتركة"""
        try:
            from modules.shared_memory_pg import shared_memory
            
            # الحصول على معلومات المستخدم
            user_memory = await shared_memory.get_user_memory(user_id, chat_id)
            if user_memory:
                # تحليل المعلومات واستخراج الأهتمامات
                memory_text = user_memory.lower()
                interests = []
                
                # كلمات مفتاحية للاهتمامات
                interest_keywords = {
                    'جولف': ['جولف', 'golf'],
                    'رياضة': ['رياضة', 'لعب', 'كرة', 'تمرين'],
                    'تقنية': ['برمجة', 'كمبيوتر', 'تقنية', 'تطوير'],
                    'طعام': ['طعام', 'أكل', 'طبخ', 'مطعم'],
                    'موسيقى': ['موسيقى', 'أغنية', 'عزف'],
                    'قراءة': ['كتاب', 'قراءة', 'رواية'],
                    'سفر': ['سفر', 'رحلة', 'مكان', 'بلد']
                }
                
                for interest, keywords in interest_keywords.items():
                    if any(keyword in memory_text for keyword in keywords):
                        interests.append(interest)
                
                return {
                    'interests': interests,
                    'last_interaction': user_memory[:100] + '...' if len(user_memory) > 100 else user_memory,
                    'topic': interests[0] if interests else 'أشياء متنوعة'
                }
                
        except Exception as e:
            logging.error(f"خطأ في الحصول على معلومات المستخدم: {e}")
            
        return None

# إنشاء نسخة واحدة من النظام
obaid_smart = ObaidSmartSystem()
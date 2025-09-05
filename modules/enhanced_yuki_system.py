"""
نظام يوكي المحسن مع الوصول الشامل لقاعدة البيانات
Enhanced Yuki System with Comprehensive Database Access
"""

import asyncio
import logging
import random
from typing import Dict, Any, Optional, List
from datetime import datetime

class EnhancedYukiSystem:
    """نظام يوكي المحسن مع الذكاء الاصطناعي والوصول الكامل للبيانات"""
    
    def __init__(self):
        self.yuki_personality = {
            'identity': {
                'name': 'يوكي',
                'age': 23,
                'nationality': 'ياباني',
                'occupation': 'طالب جامعي',
                'interests': ['الألعاب', 'التكنولوجيا', 'مساعدة الأصدقاء', 'اللغات'],
                'background': 'طالب من اليابان يحب يساعد الناس ويتكلم معهم'
            },
            'personality': {
                'friendly': True,
                'helpful': True,
                'casual': True,
                'curious': True,
                'respectful': True
            }
        }
    
    async def get_full_user_context(self, user_id: int, chat_id: int = None) -> Dict[str, Any]:
        """الحصول على السياق الكامل للمستخدم من جميع جداول قاعدة البيانات"""
        context = {
            'basic_info': {},
            'financial_status': {},
            'gaming_progress': {},
            'social_connections': {},
            'achievements': {},
            'recent_activity': {}
        }
        
        try:
            # استيراد الوظائف المطلوبة
            from database.operations import get_user
            from database.config.database import execute_query
            
            # المعلومات الأساسية
            user = await get_user(user_id)
            if user:
                context['basic_info'] = {
                    'name': user.get('first_name', 'صديقي'),
                    'gender': user.get('gender', ''),
                    'country': user.get('country', ''),
                    'is_registered': user.get('is_registered', False),
                    'join_date': user.get('created_at', ''),
                    'level': user.get('level', 1),
                    'xp': user.get('xp', 0)
                }
                
                # الحالة المالية
                context['financial_status'] = {
                    'cash_balance': user.get('balance', 0),
                    'bank_balance': user.get('bank_balance', 0),
                    'total_wealth': user.get('balance', 0) + user.get('bank_balance', 0),
                    'bank_type': user.get('bank_type', 'الأهلي'),
                    'daily_salary': user.get('daily_salary', 0)
                }
            
            # معلومات الزواج والعلاقات
            if chat_id:
                marriage = await execute_query(
                    "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                    (user_id, user_id, chat_id),
                    fetch_one=True
                )
                
                context['social_connections']['marriage_status'] = 'متزوج' if marriage else 'أعزب'
                
                if marriage:
                    partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
                    partner = await get_user(partner_id)
                    context['social_connections']['partner_name'] = partner.get('first_name', 'شريك الحياة') if partner else 'غير محدد'
            
            # العقارات والاستثمارات
            try:
                properties = await execute_query(
                    "SELECT COUNT(*) as count, SUM(price) as total_value FROM user_properties WHERE user_id = ?",
                    (user_id,),
                    fetch_one=True
                )
                
                if properties:
                    context['achievements']['properties'] = {
                        'count': properties.get('count', 0),
                        'total_value': properties.get('total_value', 0)
                    }
            except:
                context['achievements']['properties'] = {'count': 0, 'total_value': 0}
            
            # إحصائيات النشاط الأخيرة
            try:
                recent_transactions = await execute_query(
                    "SELECT COUNT(*) as count FROM transactions WHERE user_id = ? AND date(created_at) = date('now')",
                    (user_id,),
                    fetch_one=True
                )
                
                context['recent_activity']['daily_transactions'] = recent_transactions.get('count', 0) if recent_transactions else 0
            except:
                context['recent_activity']['daily_transactions'] = 0
                
        except Exception as e:
            logging.error(f"خطأ في جلب سياق المستخدم {user_id}: {e}")
        
        return context
    
    def get_personalized_greeting(self, user_context: Dict[str, Any]) -> str:
        """إنشاء تحية شخصية بناءً على معلومات المستخدم"""
        basic = user_context.get('basic_info', {})
        name = basic.get('name', 'صديقي')
        gender = basic.get('gender', '')
        country = basic.get('country', '')
        
        # مخاطبة حسب الجنس
        gender_address = self._get_gender_address(gender)
        
        # السياق الثقافي للبلد
        country_context = self._get_country_context(country)
        
        greetings = [
            f"مرحبا {gender_address} {name}! شو أخبارك اليوم؟ 😊",
            f"أهلين {name}! {gender_address} العزيز {country_context}، كيف الحال؟ ✨",
            f"هلا {gender_address} {name}! وحشتني، شلونك؟ 🌟",
            f"يا أهلا بـ{name}! {gender_address} الغالي، شو مخططلك اليوم؟ 💫",
        ]
        
        return random.choice(greetings)
    
    def _get_gender_address(self, gender: str) -> str:
        """الحصول على طريقة المخاطبة حسب الجنس"""
        if gender == 'male':
            return random.choice(['أخي', 'أخوي', 'يا أخ', 'صديقي', 'حبيبي'])
        elif gender == 'female':
            return random.choice(['أختي', 'أختي الكريمة', 'يا أخت', 'صديقتي', 'حبيبتي'])
        else:
            return random.choice(['صديقي', 'حبيبي', 'عزيزي'])
    
    def _get_country_context(self, country: str) -> str:
        """الحصول على السياق الثقافي حسب البلد"""
        country_phrases = {
            'السعودية': ['من أرض الحرمين', 'من بلاد النخل والتمر', 'من المملكة الكريمة'],
            'الإمارات': ['من دولة الخير', 'من أرض زايد', 'من الإمارات الطيبة'],
            'الكويت': ['من الكويت الطيبة', 'من بلاد الضيافة', 'من الكويت العزيزة'],
            'قطر': ['من قطر الكريمة', 'من الدوحة الجميلة', 'من بلاد الخير'],
            'البحرين': ['من البحرين الطيبة', 'من اللؤلؤة الخليجية', 'من البحرين العزيزة'],
            'عمان': ['من السلطنة الكريمة', 'من عمان الجميلة', 'من بلاد السلام'],
            'الأردن': ['من الأردن الهاشمية', 'من بلاد الكرم', 'من الأردن الطيبة'],
            'مصر': ['من أم الدنيا', 'من مصر العزيزة', 'من بلاد النيل'],
            'المغرب': ['من المملكة المغربية', 'من المغرب الجميل', 'من بلاد الأطلس']
        }
        
        if country in country_phrases:
            return random.choice(country_phrases[country])
        else:
            return 'من بلدك الجميل'
    
    async def generate_contextual_response(self, message: str, user_id: int, chat_id: int = None) -> str:
        """توليد رد ذكي بناءً على السياق الكامل للمستخدم"""
        
        # الحصول على السياق الكامل للمستخدم
        user_context = await self.get_full_user_context(user_id, chat_id)
        
        basic = user_context.get('basic_info', {})
        financial = user_context.get('financial_status', {})
        social = user_context.get('social_connections', {})
        
        name = basic.get('name', 'صديقي')
        gender = basic.get('gender', '')
        country = basic.get('country', '')
        
        # تحليل الرسالة لفهم النوايا
        message_lower = message.lower()
        
        # ردود ذكية بناءً على السياق
        if any(word in message_lower for word in ['مرحبا', 'هلا', 'السلام', 'أهلا']):
            return self.get_personalized_greeting(user_context)
        
        elif any(word in message_lower for word in ['رصيد', 'فلوس', 'مال', 'حساب']):
            gender_address = self._get_gender_address(gender)
            total_wealth = financial.get('total_wealth', 0)
            
            if total_wealth > 50000:
                return f"ماشاء الله {gender_address} {name}! رصيدك ممتاز، واضح إنك شاطر في إدارة الأموال! 💰✨"
            elif total_wealth > 10000:
                return f"{gender_address} {name}، رصيدك حلو، بس ما رأيك نستثمر أكثر؟ 📈💡"
            else:
                return f"لا تشيل هم {gender_address} {name}، البداية صعبة بس بالتدريج راح نوصل للهدف! 💪😊"
        
        elif any(word in message_lower for word in ['زواج', 'متزوج', 'زوج']):
            gender_address = self._get_gender_address(gender)
            marriage_status = social.get('marriage_status', 'أعزب')
            
            if marriage_status == 'متزوج':
                partner_name = social.get('partner_name', 'شريك الحياة')
                return f"ماشاء الله {gender_address} {name}! متزوج من {partner_name}، الله يسعدكم! 💕👫"
            else:
                return f"{gender_address} {name}، لسا عازب؟ إن شاء الله قريب تلاقي النصف التاني! 😊💝"
        
        elif any(word in message_lower for word in ['شكرا', 'تسلم', 'يعطيك']):
            gender_address = self._get_gender_address(gender)
            country_context = self._get_country_context(country)
            
            thanks_responses = [
                f"عفواً {gender_address} {name}! دايماً في الخدمة {country_context}! 😊",
                f"ولا يهمك {gender_address} {name}! هاي أقل واجباتي معك! ✨",
                f"الله يسلمك {gender_address} {name}! أي وقت تحتاجني أنا هنا! 💫"
            ]
            
            return random.choice(thanks_responses)
        
        else:
            # ردود عامة مع السياق الشخصي
            gender_address = self._get_gender_address(gender)
            
            general_responses = [
                f"شو رأيك {gender_address} {name}؟ أحب أسمع وجهة نظرك في هالموضوع! 🤔💭",
                f"صراحة {gender_address} {name}، هالسؤال يحتاج تفكير، شو تتوقع؟ 💡",
                f"حلو هالكلام {gender_address} {name}! دايماً عندك أفكار مثيرة للاهتمام! 🌟",
                f"أكيد {gender_address} {name}، خل نشوف إيش رأي الباقين برضو! 😊👥"
            ]
            
            return random.choice(general_responses)
    
    async def get_user_summary_for_ai(self, user_id: int, chat_id: int = None) -> str:
        """الحصول على ملخص المستخدم للاستخدام مع الذكاء الاصطناعي"""
        context = await self.get_full_user_context(user_id, chat_id)
        
        basic = context.get('basic_info', {})
        financial = context.get('financial_status', {})
        social = context.get('social_connections', {})
        achievements = context.get('achievements', {})
        
        summary = f"""
        معلومات المستخدم:
        - الاسم: {basic.get('name', 'غير محدد')}
        - الجنس: {basic.get('gender', 'غير محدد')}
        - البلد: {basic.get('country', 'غير محدد')}
        - المستوى: {basic.get('level', 1)}
        - نقاط الخبرة: {basic.get('xp', 0)}
        - الرصيد النقدي: {financial.get('cash_balance', 0)}
        - رصيد البنك: {financial.get('bank_balance', 0)}
        - إجمالي الثروة: {financial.get('total_wealth', 0)}
        - حالة الزواج: {social.get('marriage_status', 'أعزب')}
        """
        
        if social.get('partner_name'):
            summary += f"- اسم الشريك: {social.get('partner_name')}\n"
        
        if achievements.get('properties', {}).get('count', 0) > 0:
            summary += f"- عدد العقارات: {achievements['properties']['count']}\n"
            summary += f"- قيمة العقارات: {achievements['properties']['total_value']}\n"
        
        return summary.strip()

# إنشاء مثيل النظام المحسن
enhanced_yuki = EnhancedYukiSystem()
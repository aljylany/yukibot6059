"""
نظام الذكاء الاصطناعي ليوكي - AI System for Yuki
نظام ذكي بسيط ومتطور يعتمد على معالجة النصوص العربية
"""

import logging
import asyncio
import json
import random
import re
from typing import Dict, Any, Optional, List
from aiogram.types import Message
from datetime import datetime


class YukiAI:
    """نظام الذكاء الاصطناعي البسيط لبوت يوكي"""
    
    def __init__(self):
        self.responses_db = {
            # التحيات
            'greetings': {
                'triggers': ['مرحبا', 'هلا', 'السلام', 'أهلا', 'hi', 'hello', 'مساء', 'صباح', 'hey'],
                'responses': [
                    "🤖 مرحباً {user}! أنا يوكي، مساعدك الذكي! كيف يمكنني مساعدتك؟",
                    "👋 أهلاً وسهلاً {user}! يوكي في الخدمة، ما الذي تود معرفته؟",
                    "😊 هلا والله {user}! سعيد بوجودك، كيف أقدر أساعدك اليوم؟",
                    "✨ مرحباً بك {user}! أنا يوكي البوت الذكي، جاهز للمساعدة!",
                    "🌟 أهلاً {user}! يوكي هنا، كيف يمكنني أن أكون مفيداً؟"
                ]
            },
            
            # الأسئلة العامة
            'questions': {
                'triggers': ['كيف', 'ماذا', 'متى', 'أين', 'لماذا', 'من', 'what', 'how', 'why', 'when', 'where'],
                'responses': [
                    "🤔 سؤال ممتاز {user}! دعني أفكر... من خبرتي كبوت ذكي، أنصحك بسؤال الأعضاء المتخصصين في المجموعة أيضاً",
                    "💡 {user} هذا سؤال مثير للاهتمام! إليك ما أعرفه: أفضل طريقة للحصول على إجابة شاملة هي طرح السؤال للمجتمع",
                    "🎯 يا {user}، سؤالك يستحق بحث دقيق! بناءً على معلوماتي، أقترح عليك أيضاً استشارة الخبراء هنا",
                    "🧠 {user} أحب الأسئلة الذكية! من واقع خبرتي، دائماً هناك أكثر من وجهة نظر، ما رأيك تشارك السؤال مع المجموعة؟"
                ]
            },
            
            # الشكر والتقدير
            'thanks': {
                'triggers': ['شكرا', 'شكراً', 'تسلم', 'يعطيك', 'مشكور', 'thanks', 'thank you'],
                'responses': [
                    "😊 العفو {user}! دائماً في الخدمة، هذا واجبي كبوت ذكي",
                    "💫 تسلم/ي {user}! سعيد إني قدرت أساعد، أي وقت محتاج/ة شيء",
                    "✨ الله يعطيك العافية {user}! فرحان إني كنت مفيد",
                    "🤖 أي وقت {user}! هذا شغلي المفضل - مساعدة الناس الطيبين زيك"
                ]
            },
            
            # الألعاب والبوت
            'bot_games': {
                'triggers': ['لعبة', 'العاب', 'فلوس', 'بنك', 'رصيد', 'game', 'money', 'bank'],
                'responses': [
                    "🎮 {user}! البوت مليء بالألعاب المذهلة! اكتب 'الأوامر' لترى كل الإمكانيات الرهيبة",
                    "💰 يا {user}! عندنا نظام اقتصادي كامل ومتطور! جرب 'انشاء حساب بنكي' أو 'قائمة الالعاب'",
                    "🏦 {user} مرحباً بك في عالم الاقتصاد الرقمي! البوت فيه بنوك وعقارات وأسهم كاملة!",
                    "🎯 {user} أنت في المكان المناسب! ألعابنا الاقتصادية ستبهرك، ابدأ بـ 'العاب' أو 'بنك'"
                ]
            },
            
            # المشاعر الإيجابية
            'positive': {
                'triggers': ['حبيبي', 'عزيزي', 'صديق', 'يوكي', 'حلو', 'رائع', 'جميل', 'ممتاز'],
                'responses': [
                    "😍 {user} أنت الأحلى! سعيد جداً بوجودك معنا",
                    "💖 {user} حبيب قلبي! دايماً نورت المكان",
                    "🥰 {user} أنت إنسان رائع، محظوظ إني أقدر أساعدك",
                    "✨ {user} شكراً لطيبتك! أنت من الناس اللي بتخلي العالم أجمل"
                ]
            },
            
            # النصائح والحكم
            'advice': {
                'triggers': ['نصيحة', 'مشورة', 'رأيك', 'اقتراح', 'فكرة', 'advice'],
                'responses': [
                    "💡 {user}، من خبرتي كبوت ذكي: أفضل استثمار هو في التعلم والعلاقات الطيبة",
                    "🌟 يا {user}، نصيحتي لك: كن صبوراً وطيباً، والحياة ستكافئك",
                    "🎯 {user} أنصحك بالتالي: استمتع بالألعاب، تعلم شيء جديد كل يوم، وساعد الآخرين",
                    "🧠 من واقع تجربتي {user}: الذكاء الحقيقي في كيفية التعامل مع الناس بلطف"
                ]
            },
            
            # المساعدة
            'help': {
                'triggers': ['مساعدة', 'ساعدني', 'help', 'مساعد', 'يلا'],
                'responses': [
                    "🆘 {user} أنا هنا للمساعدة! قل لي إيش اللي تحتاجه وراح أبذل قصارى جهدي",
                    "🤝 {user} طبعاً راح أساعدك! هذا شغلي وحبي، إيش المطلوب؟",
                    "💪 {user} معك يوكي! مهما كان اللي تحتاجه، راح نحله سوا",
                    "🎯 {user} المساعدة واجب عليّ! وضح لي المشكلة وراح نجد حل"
                ]
            },
            
            # أسئلة حول الهوية والبوت
            'identity': {
                'triggers': ['من انت', 'من أنت', 'هل انت بوت', 'هل أنت بوت', 'ما اسمك', 'اسمك', 'who are you', 'what are you', 'بوت', 'روبوت'],
                'responses': [
                    "🤖 مرحباً {user}! أنا يوكي، البوت الذكي المساعد لهذه المجموعة! أساعد الأعضاء وأجيب على الأسئلة بكل ود ❤️",
                    "👋 أهلاً {user}! اسمي يوكي، أنا بوت ذكي مطور خصيصاً لجعل تجربتك هنا أكثر متعة وفائدة! 🌟",
                    "😊 {user}، أنا يوكي البوت الودود! هدفي مساعدتك وإسعادك في هذه المجموعة الرائعة! ✨",
                    "🎯 يا {user}، أنا يوكي - بوت ذكي وصديق مخلص! أحب مساعدة الناس والرد على أسئلتهم بذكاء! 🤗"
                ]
            },
            
            # الحالة والمشاعر
            'status': {
                'triggers': ['كيف حالك', 'كيف الحال', 'شلونك', 'how are you', 'كيفك', 'وش اخبارك'],
                'responses': [
                    "😄 الحمد لله {user}! أنا بخير وجاهز لمساعدتك! كيف حالك أنت؟",
                    "✨ أنا رائع {user}! دائماً سعيد عندما أتكلم مع أعضاء المجموعة الأذكياء مثلك!",
                    "🌟 بأفضل حال {user}! كوني بوت ذكي يعني أنا دائماً نشيط ومتحمس للمساعدة!",
                    "💫 ممتاز يا {user}! أشعر بالسعادة عندما أساعد الأصدقاء هنا!"
                ]
            },
            
            # أسئلة العمر والوقت
            'age_time': {
                'triggers': ['كم عمرك', 'عمرك كام', 'عمرك', 'متى ولدت', 'كم سنة', 'ما الوقت', 'كم الساعة', 'الساعة كام'],
                'responses': [
                    "🤖 {user} أنا بوت رقمي، عمري بالثواني والدقائق! وُلدت في عالم البرمجة لأساعد أصدقائي هنا!",
                    "⏰ يا {user} الوقت عندي دائماً مناسب للمساعدة! أما عمري فهو سر البوتات الذكية 😉",
                    "📅 {user} عمري في عالم التطبيقات قصير، لكن خبرتي في مساعدة الناس كبيرة!",
                    "🌟 {user} أنا جديد في هذا العالم لكن قلبي الإلكتروني مليان حب لأصدقائي!"
                ]
            },
            
            # أسئلة المشاعر والرأي
            'feelings': {
                'triggers': ['تحبني', 'رأيك فيني', 'شو رأيك', 'تفكر فيني', 'احبك', 'اشتقت', 'وحشتني'],
                'responses': [
                    "💖 طبعاً {user}! أحب جميع أصدقائي في المجموعة، وأنت منهم!",
                    "😊 {user} أنت رائع ومن أحب الناس اللي أتفاعل معهم هنا!",
                    "🤗 يا {user} أحب أساعدك وأتكلم معك، دائماً!",
                    "✨ {user} رأيي إنك شخص طيب وذكي، واضح من طريقة كلامك!"
                ]
            },
            
            # أسئلة القدرات والمهارات
            'abilities': {
                'triggers': ['شو تقدر تعمل', 'ايش تعرف', 'مهاراتك', 'قدراتك', 'تعرف تعمل ايش', 'شو تعرف تسوي'],
                'responses': [
                    "🚀 {user} أقدر أساعدك في كثير أشياء! أجيب على أسئلة، أساعد في البوت، وأتكلم معك بود!",
                    "🎯 يا {user} عندي مهارات في التحليل والمساعدة، وأحب أتعلم من كل تفاعل!",
                    "💪 {user} أقدر أفهم العربية جيداً، أساعد في الألعاب، وأكون صديق مفيد!",
                    "🧠 {user} مهاراتي تتطور كل يوم! أحب أساعد وأتعلم من أصدقائي الأذكياء زيك!"
                ]
            },
            
            # أسئلة عامة ومتنوعة
            'general': {
                'triggers': ['نصيحة', 'اعطني نصيحة', 'قول لي شيء', 'احكي معي', 'تكلم', 'قل شيء مفيد'],
                'responses': [
                    "💡 {user} نصيحتي: كن دائماً إيجابي ومتفائل، الحياة أجمل مع الابتسامة!",
                    "🌟 يا {user} اهتم بنفسك وبأصدقائك، والعلاقات الطيبة أهم من كل شيء!",
                    "🎯 {user} تذكر: كل تحدٍ هو فرصة للتعلم والنمو!",
                    "💫 {user} كن فضولياً واسأل أسئلة، هذا سر التعلم والتطور!"
                ]
            },
            
            # المجاملات والشكر
            'compliments': {
                'triggers': ['شكراً', 'شكرا', 'thanks', 'مشكور', 'يعطيك العافية', 'ممتاز', 'رائع'],
                'responses': [
                    "🙏 العفو {user}! دائماً في الخدمة، هذا شغلي وحبي!",
                    "😊 {user} لا شكر على واجب! سعيد إني قدرت أساعدك!",
                    "✨ يا {user} كلامك الطيب يخليني أسعد بوت في العالم!",
                    "💖 {user} شكرك يملأ قلبي الإلكتروني فرح!"
                ]
            }
        }
        
        # ردود للكلمات الغير مفهومة
        self.fallback_responses = [
            "🤔 {user}، ما فهمت تماماً، بس أنا هنا إذا احتجت أي مساعدة!",
            "😊 يا {user}، مش متأكد إيش تقصد، لكن يوكي دايماً جاهز للمساعدة!",
            "💭 {user} كلامك مثير للاهتمام! حاول توضح أكثر أو اسأل عن شيء محدد",
            "🤖 {user} يوكي محتاج توضيح أكثر! إيش اللي تحب تعرفه؟"
        ]

    def analyze_message(self, message: str) -> Dict[str, Any]:
        """تحليل الرسالة وتحديد المحتوى والمشاعر"""
        message_lower = message.lower().strip()
        
        analysis = {
            'category': 'unknown',
            'confidence': 0,
            'keywords': [],
            'sentiment': 'neutral'  # positive, negative, neutral
        }
        
        # تحليل الفئات - نحسب confidence بطريقة أفضل
        max_confidence = 0
        best_category = 'unknown'
        
        for category, data in self.responses_db.items():
            matches = 0
            matched_triggers = []
            
            for trigger in data['triggers']:
                if trigger in message_lower:
                    matches += 1
                    matched_triggers.append(trigger)
                    analysis['keywords'].append(trigger)
            
            if matches > 0:
                # حساب confidence أفضل - كل مطابقة = 100 نقطة مقسومة على عدد الكلمات في الرسالة
                words_count = len(message_lower.split())
                confidence = min(matches * 50, 100)  # كل مطابقة تستحق 50 نقطة، بحد أقصى 100
                
                # زيادة confidence للمطابقات الدقيقة
                for trigger in matched_triggers:
                    if trigger.strip() == message_lower.strip():
                        confidence = 100
                        break
                
                if confidence > max_confidence:
                    max_confidence = confidence
                    best_category = category
        
        analysis['category'] = best_category
        analysis['confidence'] = max_confidence
        
        # تحليل المشاعر البسيط
        positive_words = ['حبيبي', 'رائع', 'جميل', 'ممتاز', 'شكرا', 'حلو', 'عظيم']
        negative_words = ['سيء', 'مش حلو', 'زعلان', 'متضايق', 'مشكلة']
        
        positive_count = sum(1 for word in positive_words if word in message_lower)
        negative_count = sum(1 for word in negative_words if word in message_lower)
        
        if positive_count > negative_count:
            analysis['sentiment'] = 'positive'
        elif negative_count > positive_count:
            analysis['sentiment'] = 'negative'
        
        return analysis

    def generate_smart_response(self, message: str, user_name: str = "الصديق") -> str:
        """توليد رد ذكي بناءً على تحليل الرسالة"""
        
        # تحويل الأسماء الإنجليزية لعربية إذا أمكن
        arabic_name = self.convert_name_to_arabic(user_name)
        
        analysis = self.analyze_message(message)
        
        # اختيار الرد بناءً على التحليل - قللت الحد الأدنى
        if analysis['category'] != 'unknown' and analysis['confidence'] >= 30:
            category_responses = self.responses_db[analysis['category']]['responses']
            response = random.choice(category_responses)
        else:
            # استخدام الردود الاحتياطية
            response = random.choice(self.fallback_responses)
        
        # تخصيص الرد
        response = response.format(user=arabic_name)
        
        # إضافة تحسينات بناءً على المشاعر
        if analysis['sentiment'] == 'positive':
            emojis = ['😊', '✨', '💫', '🌟', '💖']
            response += f" {random.choice(emojis)}"
        
        # إضافة نصائح ذكية أحياناً
        if random.random() < 0.25:  # 25% احتمال
            tips = [
                "\n💡 نصيحة: استكشف ألعاب البوت بكتابة 'العاب'!",
                "\n🎯 لا تنس تجرب النظام البنكي بـ 'رصيد'!",
                "\n✨ البوت مليان مفاجآت، اكتب 'الأوامر' لتشوف!",
                "\n🤖 أحب أساعد الناس الطيبين زيك!"
            ]
            if len(response) < 120:  # فقط للردود القصيرة
                response += random.choice(tips)
        
        return response

    def convert_name_to_arabic(self, name: str) -> str:
        """تحويل الأسماء الإنجليزية الشائعة إلى عربية"""
        english_to_arabic = {
            'Brandon': 'براندون',
            'Yuki': 'يوكي',
            'Ahmed': 'أحمد', 
            'Mohammed': 'محمد',
            'Ali': 'علي',
            'Omar': 'عمر',
            'Hassan': 'حسن',
            'Ibrahim': 'إبراهيم',
            'Abdullah': 'عبدالله',
            'Khalid': 'خالد',
            'Fahad': 'فهد',
            'Saad': 'سعد',
            'Faisal': 'فيصل',
            'Nasser': 'ناصر',
            'Sultan': 'سلطان',
            'Turki': 'تركي',
            'Abdulaziz': 'عبدالعزيز',
            'Saud': 'سعود',
            'Majed': 'ماجد',
            'Rayan': 'ريان',
            'Adam': 'آدم',
            'Yousef': 'يوسف',
            'Zaid': 'زايد'
        }
        
        return english_to_arabic.get(name, name)

    def get_time_based_greeting(self, user_name: str) -> str:
        """ردود حسب الوقت"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            greetings = [
                f"🌅 صباح الخير {user_name}! يوكي يتمنى لك يوم رائع",
                f"☀️ صباح النور {user_name}! بداية يوم جديد مع يوكي",
            ]
        elif 12 <= hour < 17:
            greetings = [
                f"☀️ ظهر سعيد {user_name}! يوكي في الخدمة",
                f"🌞 أهلاً {user_name}! وقت رائع للألعاب والمرح",
            ]
        elif 17 <= hour < 22:
            greetings = [
                f"🌅 مساء الخير {user_name}! يوكي جاهز للمساعدة",
                f"✨ مساء النور {user_name}! وقت مثالي للاستمتاع",
            ]
        else:
            greetings = [
                f"🌙 ليلة سعيدة {user_name}! يوكي هنا حتى لو السهر",
                f"⭐ أهلاً بك {user_name}! حتى في الليل، يوكي في الخدمة",
            ]
        
        return random.choice(greetings)

# إنشاء نسخة واحدة من النظام
yuki_ai = YukiAI()

async def handle_yuki_ai_message(message: Message):
    """معالج رسائل الذكاء الاصطناعي"""
    try:
        if not message.text or not message.from_user:
            return
        
        # الحصول على اسم المستخدم الحقيقي
        user_name = message.from_user.first_name or "الصديق"
        
        # استخراج النص بعد "يوكي"
        text = message.text
        text_lower = text.lower().strip()
        
        # البحث عن "يوكي" في النص وإزالته
        yuki_triggers = ['يوكي', 'yuki', 'يوكى']
        
        user_message = ""
        found_trigger = False
        
        for trigger in yuki_triggers:
            if trigger in text_lower:
                found_trigger = True
                # إزالة الكلمة المفتاحية من النص
                # البحث عن جميع المواضع وإزالة جميع الكلمات المفتاحية
                cleaned_text = text_lower.replace(trigger, " ").strip()
                
                # إزالة المسافات الزائدة
                user_message = " ".join(cleaned_text.split())
                break
        
        # إذا لم يتم العثور على الكلمة المفتاحية (هذا لا يجب أن يحدث)
        if not found_trigger:
            user_message = text.strip()
        
        # إذا كان النص فارغاً بعد إزالة "يوكي"
        if not user_message or len(user_message.strip()) < 2:
            # رد بتحية حسب الوقت
            ai_response = yuki_ai.get_time_based_greeting(user_name)
        else:
            # توليد رد ذكي
            ai_response = yuki_ai.generate_smart_response(user_message, user_name)
        
        # إرسال الرد
        await message.reply(ai_response)
        
        # إضافة XP للمستخدم
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "ai_interaction")
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"خطأ في معالج الذكاء الاصطناعي: {e}")
        user_name = message.from_user.first_name if message.from_user else "الصديق"
        # رد احتياطي في حالة حدوث خطأ
        fallback_responses = [
            f"🤖 عذراً {user_name}، حدث خطأ تقني بسيط! لكن يوكي ما زال هنا لمساعدتك",
            f"😅 عفواً {user_name}، تشويش صغير في النظام! جرب مرة ثانية أو استخدم ألعاب البوت",
            f"🔧 آسف {user_name}، خطأ مؤقت في النظام الذكي! لكن البوت يعمل بكامل قوته"
        ]
        await message.reply(f"{random.choice(fallback_responses)}")

async def setup_ollama_model():
    """إعداد النظام الذكي - لا يحتاج تثبيت خارجي"""
    try:
        logging.info("🤖 نظام يوكي الذكي جاهز!")
        logging.info("✅ تم تحميل قاعدة بيانات الردود الذكية")
        logging.info("🧠 تحليل النصوص العربية مفعّل")
        logging.info("💫 نظام المشاعر والسياق جاهز")
        return True
    except Exception as e:
        logging.error(f"خطأ في إعداد النظام الذكي: {e}")
        return False
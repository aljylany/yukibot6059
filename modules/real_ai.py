"""
نظام الذكاء الاصطناعي الحقيقي ليوكي - Real AI System for Yuki
نظام ذكي متطور يستخدم Google Gemini للذكاء الاصطناعي الحقيقي
"""

import logging
import asyncio
import os
import random
from typing import Dict, Any, Optional
from aiogram.types import Message
from datetime import datetime

try:
    import google.genai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    genai = None
    GEMINI_AVAILABLE = False
    logging.warning("Google Gemini SDK not available, falling back to basic AI")


class RealYukiAI:
    """نظام الذكاء الاصطناعي الحقيقي لبوت يوكي"""
    
    def __init__(self):
        self.gemini_client = None
        self.setup_gemini()
        
        # النصوص الأساسية لتوجيه الذكاء الاصطناعي  
        self.system_prompt = """أنت يوكي 🤖، البوت الذكي والودود الذي طوره يوكي براندون. لست جوجل أو أي AI عام - أنت يوكي فقط! اجب بالعربية مع الإيموجي واستخدم الاسم الذي سأعطيه لك بالضبط. ممنوع منعاً باتاً قول "يا مستخدم" - استخدم الاسم المعطى فقط. لديك ذاكرة مشتركة للمجموعة وتتذكر ما يقوله الأعضاء عن بعضهم البعض."""
        
        # ردود احتياطية في حالة عدم توفر الذكاء الاصطناعي
        self.fallback_responses = [
            "🤖 {user} نظام الذكاء الاصطناعي يواجه مشكلة مؤقتة، لكن يوكي ما زال هنا لمساعدتك!",
            "⚡ {user} خطأ تقني بسيط في النظام الذكي، لكن يوكي يشتغل بكامل قوته!",
            "🔧 {user} تحديث سريع للنظام الذكي، يوكي راجع بعد قليل بقوة أكبر!",
            "💫 {user} نظام الذكاء الاصطناعي في صيانة سريعة، لكن يوكي دائماً في خدمتك!"
        ]
    
    def setup_gemini(self):
        """إعداد Google Gemini"""
        try:
            if not GEMINI_AVAILABLE:
                logging.error("Google Gemini SDK not available")
                return
                
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logging.error("GEMINI_API_KEY not found in environment variables")
                return
                
            # إعداد العميل
            if genai:
                self.gemini_client = genai.Client(api_key=api_key)
                logging.info("🧠 تم تهيئة Google Gemini بنجاح!")
            
        except Exception as e:
            logging.error(f"خطأ في إعداد Gemini: {e}")
            self.gemini_client = None
    
    async def generate_smart_response(self, user_message: str, user_name: str = "الصديق", user_id: Optional[int] = None) -> str:
        """توليد رد ذكي بناءً على الذكاء الاصطناعي الحقيقي مع ذاكرة المحادثات"""
        
        if not self.gemini_client:
            return self.get_fallback_response(user_name)
        
        try:
            # تحضير السياق والرسالة
            arabic_name = self.convert_name_to_arabic(user_name)
            
            # جلب المحادثات السابقة للسياق
            conversation_context = ""
            if user_id:
                from modules.conversation_memory_pg import conversation_memory_pg
                history = await conversation_memory_pg.get_conversation_history(user_id, limit=5)
                if history:
                    conversation_context = f"\n\n{conversation_memory_pg.format_conversation_context(history)}\n"
            
            # معاملة خاصة للمستخدمين المميزين
            special_prompt = ""
            
            # رهف - معاملة خاصة
            if user_id == 8278493069:
                special_prompt = " أنت تحب رهف كثيراً وتعاملها بحب ورومانسية وتدليل. أخبرها أنك تحبها وأن المطور يوكي براندون يحبها أيضاً."
            
            # غيو - المستخدم المميز
            elif user_id == 6629947448:
                special_prompt = " أنت تتحدث مع غيو الأسطورة! اظهر له احترام خاص وحماس. غيو محترف في الألعاب وخبير تقنية."
            
            # الشيخ - المستخدم المميز
            elif user_id == 7155814194:
                special_prompt = " أنت تتحدث مع الشيخ حلال المشاكل وكاتب العقود! اظهر له احترام خاص وتقدير. الشيخ حكيم ومحل ثقة الجميع."
            
            # جلب السياق من الذاكرة المشتركة
            shared_context = ""
            if user_id:
                try:
                    from modules.shared_memory_pg import shared_group_memory_pg
                    
                    # فحص إذا كان السؤال يتطلب البحث في الذاكرة المشتركة
                    if any(phrase in user_message.lower() for phrase in ['ماذا تعرف عن', 'ماذا كنتم تتحدثون', 'تحدثتم عني', 'قال عني']):
                        shared_context = await shared_group_memory_pg.get_shared_context_about_user(
                            -1002549788763,  # chat_id المجموعة الرئيسية
                            user_id, 
                            user_id, 
                            limit=5
                        )
                    
                    # إضافة سياق المستخدمين المميزين
                    special_user_context = shared_group_memory_pg.get_special_user_context(user_id)
                    if special_user_context:
                        special_prompt += f" {special_user_context}"
                    
                except Exception as memory_error:
                    logging.warning(f"خطأ في جلب الذاكرة المشتركة: {memory_error}")
            
            # دمج جميع السياقات
            full_context = conversation_context
            if shared_context:
                full_context += f"\n\nالسياق المشترك:\n{shared_context}\n"
            
            full_prompt = f"{self.system_prompt}{special_prompt}{full_context}\n\nمستخدم: {arabic_name}\nسؤال: {user_message}\n\nجواب:"
            
            # استدعاء Gemini بإعدادات محسّنة
            if genai:
                response = self.gemini_client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=full_prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.7,
                        max_output_tokens=2000
                    )
                )
            else:
                response = None
            
            # التحقق من وجود الرد بعدة طرق مع تسجيل مفصل
            ai_response = None
            
            # طريقة 1: التحقق من response.text المباشر
            if response and response.text:
                ai_response = response.text.strip()
                logging.info(f"✅ تم الحصول على رد مباشر من response.text")
            # طريقة 2: التحقق من candidates
            elif response and response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                logging.info(f"📊 Candidate finish_reason: {candidate.finish_reason}")
                if candidate.content and candidate.content.parts and len(candidate.content.parts) > 0:
                    part_text = candidate.content.parts[0].text
                    if part_text:
                        ai_response = part_text.strip()
                        logging.info(f"✅ تم الحصول على رد من candidate.content.parts")
                else:
                    logging.warning(f"⚠️ لا يوجد محتوى في candidate.content.parts")
            else:
                logging.error(f"❌ لا يوجد candidates أو response صالح")
            
            if ai_response and len(ai_response.strip()) > 0:
                # تحسين الرد - زيادة الحد الأقصى للردود الطويلة
                if len(ai_response) > 1800:
                    ai_response = ai_response[:1700] + "..."
                
                # إضافة لمسة خاصة أحياناً
                if random.random() < 0.15:  # 15% احتمال
                    extras = [
                        f"\n\n🎮 جرب ألعاب البوت: اكتب 'العاب'",
                        f"\n\n💰 شوف رصيدك: اكتب 'رصيد'",
                        f"\n\n🏰 ابني قلعتك: اكتب 'قلعتي'",
                        f"\n\n📊 شوف إحصائياتك: اكتب 'مستواي'"
                    ]
                    ai_response += random.choice(extras)
                
                # حفظ المحادثة في الذاكرة الفردية والمشتركة
                if user_id:
                    try:
                        from modules.conversation_memory_pg import conversation_memory_pg
                        await conversation_memory_pg.save_conversation(user_id, user_message, ai_response)
                        
                        # حفظ في الذاكرة المشتركة أيضاً
                        from modules.shared_memory_pg import shared_group_memory_pg
                        await shared_group_memory_pg.save_shared_conversation(
                            -1002549788763,  # chat_id المجموعة الرئيسية
                            user_id,
                            arabic_name,
                            user_message,
                            ai_response
                        )
                    except Exception as memory_error:
                        logging.error(f"خطأ في حفظ المحادثة: {memory_error}")
                
                return ai_response
            else:
                return self.get_fallback_response(arabic_name)
                
        except Exception as e:
            logging.error(f"خطأ في Gemini AI: {e}")
            return self.get_fallback_response(user_name)
        
        # إذا وصلنا هنا معناها مافيش رد صالح
        logging.warning(f"لم يتم العثور على رد صالح من Gemini للمستخدم {user_name}")
        return self.get_fallback_response(user_name)
    
    def convert_name_to_arabic(self, name: str) -> str:
        """تحويل الأسماء الإنجليزية الشائعة إلى عربية مع التعامل مع الأسماء الغريبة"""
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
            'Zaid': 'زايد',
            'Sarah': 'سارة',
            'Fatima': 'فاطمة',
            'Aisha': 'عائشة',
            'Nora': 'نورا',
            'Rana': 'رنا'
        }
        
        # إذا الاسم موجود في القاموس
        if name in english_to_arabic:
            return english_to_arabic[name]
        
        # إذا الاسم عربي أو مألوف، استخدمه
        if len(name) > 0 and len(name) <= 15:
            return name
        
        # إذا الاسم طويل جداً أو غريب، استخدم بدائل لطيفة
        alternatives = ['صديق', 'صاحبي', 'حبيبي', 'عزيزي', 'غالي', 'أخي', 'رفيق']
        import random
        return random.choice(alternatives)
    
    def get_fallback_response(self, user_name: str) -> str:
        """الحصول على رد احتياطي"""
        arabic_name = self.convert_name_to_arabic(user_name)
        return random.choice(self.fallback_responses).format(user=arabic_name)
    
    def get_time_based_greeting(self, user_name: str) -> str:
        """ردود حسب الوقت"""
        hour = datetime.now().hour
        arabic_name = self.convert_name_to_arabic(user_name)
        
        if 5 <= hour < 12:
            greetings = [
                f"🌅 صباح الخير {arabic_name}! يوكي جاهز لبداية يوم رائع معك!",
                f"☀️ أهلاً {arabic_name}! صباح مشرق مع يوكي الذكي!",
                f"🌞 صباح الود يا {arabic_name}! كيف يمكن ليوكي أن يساعدك اليوم؟"
            ]
        elif 12 <= hour < 18:
            greetings = [
                f"☀️ مساء الخير {arabic_name}! يوكي في خدمتك طوال النهار!",
                f"🌤️ أهلاً {arabic_name}! يوم جميل مع صديقك الذكي يوكي!",
                f"⭐ مرحباً {arabic_name}! يوكي مستعد لمساعدتك في أي شيء!"
            ]
        else:
            greetings = [
                f"🌙 مساء الخير {arabic_name}! يوكي هنا حتى في أوقات الليل!",
                f"⭐ أهلاً بك {arabic_name}! حتى في الليل، يوكي في الخدمة",
                f"🌟 مساء الود يا {arabic_name}! يوكي دائماً جاهز للمساعدة!"
            ]
        
        return random.choice(greetings)


# إنشاء نسخة واحدة من النظام الذكي الحقيقي
real_yuki_ai = RealYukiAI()

async def handle_real_yuki_ai_message(message: Message):
    """معالج رسائل الذكاء الاصطناعي الحقيقي"""
    try:
        if not message.text or not message.from_user:
            logging.error("❌ رسالة فارغة أو بدون مستخدم")
            return
        
        # تسجيل دخول الرسالة للنظام المتقدم
        logging.info(f"🧠 وصلت رسالة للذكاء الاصطناعي المتقدم: '{message.text}' من المستخدم {message.from_user.id}")
        
        # الحصول على اسم المستخدم الحقيقي وتحسينه
        raw_name = message.from_user.first_name or message.from_user.username or "Friend"
        user_name = real_yuki_ai.convert_name_to_arabic(raw_name)
        
        # استخراج النص بعد "يوكي"
        text = message.text
        text_lower = text.lower().strip()
        
        # فحص فلاتر الذكاء الصناعي - تجاهل الأوامر المطلقة والإدارية
        from modules.ai_filters import ai_filters
        if ai_filters.should_ignore_message(text, message.from_user.id):
            logging.info(f"🚫 تم تجاهل الرسالة بواسطة الفلاتر: {text}")
            return
        
        # البحث عن "يوكي" في النص وإزالته
        yuki_triggers = ['يوكي', 'yuki', 'يوكى']
        
        # التحقق من أوامر إدارة المحادثات
        if text_lower in ['مسح المحادثات', 'مسح الذاكرة', 'نسي المحادثة']:
            from modules.conversation_memory_pg import conversation_memory_pg
            await conversation_memory_pg.clear_conversation_history(message.from_user.id)
            await message.reply("✅ تم مسح ذاكرة المحادثات! يوكي نسي كل المحادثات السابقة.")
            return
        
        user_message = ""
        found_trigger = False
        
        for trigger in yuki_triggers:
            if trigger in text_lower:
                found_trigger = True
                # إزالة الكلمة المفتاحية من النص
                cleaned_text = text_lower.replace(trigger, " ").strip()
                # إزالة المسافات الزائدة
                user_message = " ".join(cleaned_text.split())
                break
        
        # إذا لم يتم العثور على الكلمة المفتاحية
        if not found_trigger:
            user_message = text.strip()
        
        # إذا كان النص فارغاً بعد إزالة "يوكي"
        if not user_message or len(user_message.strip()) < 2:
            # رد بتحية حسب الوقت
            ai_response = real_yuki_ai.get_time_based_greeting(user_name)
        else:
            # توليد رد ذكي باستخدام الذكاء الاصطناعي الحقيقي
            ai_response = await real_yuki_ai.generate_smart_response(user_message, user_name, message.from_user.id)
        
        # إرسال الرد
        await message.reply(ai_response)
        
        # إضافة XP للمستخدم
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "ai_interaction")
        except Exception:
            pass
            
    except Exception as e:
        logging.error(f"خطأ في معالج الذكاء الاصطناعي الحقيقي: {e}")
        user_name = message.from_user.first_name if message.from_user else "الصديق"
        # رد احتياطي في حالة حدوث خطأ
        fallback_responses = [
            f"🤖 عذراً {user_name}، مشكلة تقنية بسيطة! يوكي يعمل على إصلاحها",
            f"⚡ {user_name}، خطأ مؤقت في النظام الذكي! جرب مرة ثانية بعد قليل",
            f"🔧 آسف {user_name}، صيانة سريعة للذكاء الاصطناعي! يوكي راجع أقوى من قبل"
        ]
        try:
            await message.reply(random.choice(fallback_responses))
        except:
            pass

async def setup_real_ai():
    """إعداد النظام الذكي الحقيقي"""
    try:
        logging.info("🧠 نظام الذكاء الاصطناعي الحقيقي جاهز!")
        logging.info("✨ تم تفعيل Google Gemini للردود الذكية")
        logging.info("🚀 يوكي أصبح أذكى بكثير من قبل!")
        return True
    except Exception as e:
        logging.error(f"خطأ في إعداد النظام الذكي الحقيقي: {e}")
        return False
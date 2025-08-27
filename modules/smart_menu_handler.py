"""
معالج القوائم الذكية المرقمة - Smart Menu Handler
يتعامل مع الخيارات المرقمة للأوامر الذكية
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.states import SmartCommandStates
from modules.ai_integration_handler import ai_integration


class SmartMenuHandler:
    """معالج القوائم الذكية المرقمة"""
    
    def __init__(self):
        self.menu_options = {
            'main_smart_menu': {
                1: 'economic_analysis',
                2: 'investment_strategy', 
                3: 'smart_games',
                4: 'adaptive_quiz',
                5: 'economic_challenge',
                6: 'interactive_story',
                7: 'ai_battle',
                8: 'system_status'
            },
            'games_menu': {
                1: 'number_guess',
                2: 'xo_game',
                3: 'royal_battle',
                4: 'death_arena',
                5: 'wheel_of_luck',
                6: 'word_guess',
                7: 'symbols_puzzle',
                8: 'quick_quiz'
            }
        }
    
    async def handle_smart_menu_choice(self, message: Message, state: FSMContext, menu_type: str = 'main_smart_menu') -> bool:
        """معالجة اختيار من القائمة الذكية الرئيسية"""
        try:
            user_input = message.text.strip()
            
            # التحقق من أن الإدخال رقم
            if not user_input.isdigit():
                await message.reply("❌ يرجى إدخال رقم صحيح من القائمة")
                return False
            
            choice = int(user_input)
            menu_options = self.menu_options.get(menu_type, {})
            
            # التحقق من أن الرقم موجود في القائمة
            if choice not in menu_options:
                max_options = len(menu_options)
                await message.reply(f"❌ يرجى اختيار رقم من 1 إلى {max_options}")
                return False
            
            # تنفيذ الخيار المختار
            selected_option = menu_options[choice]
            await self.execute_smart_option(message, state, selected_option)
            return True
            
        except Exception as e:
            logging.error(f"خطأ في معالجة اختيار القائمة الذكية: {e}")
            await message.reply("❌ حدث خطأ أثناء معالجة اختيارك")
            return False
    
    async def execute_smart_option(self, message: Message, state: FSMContext, option: str):
        """تنفيذ الخيار الذكي المختار"""
        try:
            user_id = message.from_user.id
            chat_id = message.chat.id
            user_name = message.from_user.first_name or "صديقي"
            
            # مسح الحالة الحالية
            await state.clear()
            
            if option == 'economic_analysis':
                await self.handle_economic_analysis(message, user_id, chat_id, user_name)
                
            elif option == 'investment_strategy':
                await self.handle_investment_strategy(message, user_id, chat_id, user_name)
                
            elif option == 'smart_games':
                await self.handle_smart_games(message, user_id, chat_id, user_name, state)
                
            elif option == 'adaptive_quiz':
                await self.handle_adaptive_quiz(message, user_id, chat_id, user_name, state)
                
            elif option == 'economic_challenge':
                await self.handle_economic_challenge(message, user_id, chat_id, user_name, state)
                
            elif option == 'interactive_story':
                await self.handle_interactive_story(message, user_id, chat_id, user_name, state)
                
            elif option == 'ai_battle':
                await self.handle_ai_battle(message, user_id, chat_id, user_name, state)
                
            elif option == 'system_status':
                await self.handle_system_status(message, user_id, chat_id, user_name)
                
        except Exception as e:
            logging.error(f"خطأ في تنفيذ الخيار الذكي {option}: {e}")
            await message.reply("❌ حدث خطأ أثناء تنفيذ الخيار المطلوب")
    
    async def handle_economic_analysis(self, message: Message, user_id: int, chat_id: int, user_name: str):
        """التحليل الاقتصادي الذكي"""
        try:
            loading_msg = await message.reply("🔄 جارٍ تحليل وضعك المالي...")
            
            analysis = await ai_integration.generate_economic_analysis(user_id, chat_id)
            
            await loading_msg.edit_text(f"📊 **التحليل الاقتصادي الذكي لـ {user_name}**\n\n{analysis}")
            
        except Exception as e:
            logging.error(f"خطأ في التحليل الاقتصادي: {e}")
            await message.reply("❌ حدث خطأ في توليد التحليل الاقتصادي")
    
    async def handle_investment_strategy(self, message: Message, user_id: int, chat_id: int, user_name: str):
        """استراتيجية الاستثمار الذكية"""
        try:
            loading_msg = await message.reply("🧠 جارٍ تطوير استراتيجية استثمار مخصصة...")
            
            strategy = await ai_integration.suggest_investment_strategy(user_id, chat_id)
            
            await loading_msg.edit_text(f"💡 **استراتيجية الاستثمار الذكية لـ {user_name}**\n\n{strategy}")
            
        except Exception as e:
            logging.error(f"خطأ في استراتيجية الاستثمار: {e}")
            await message.reply("❌ حدث خطأ في تطوير استراتيجية الاستثمار")
    
    async def handle_smart_games(self, message: Message, user_id: int, chat_id: int, user_name: str, state: FSMContext):
        """اقتراح الألعاب الذكية"""
        try:
            games_text = await ai_integration.get_game_suggestions(user_id, chat_id)
            
            # عرض قائمة الألعاب مع خيارات مرقمة
            games_menu = """
🎮 **الألعاب المتاحة:**

1️⃣ خمن الرقم - لعبة تخمين ذكية
2️⃣ اكس اوه - تحدي استراتيجي
3️⃣ الرويال - معركة ملكية
4️⃣ ساحة الموت الأخيرة - معركة جماعية
5️⃣ عجلة الحظ - دوار المكافآت
6️⃣ خمن الكلمة - تحدي لغوي
7️⃣ حل الرموز - ألغاز مشفرة
8️⃣ مسابقة سريعة - أسئلة عامة

⚡ اكتب رقم اللعبة للبدء:
"""
            
            await message.reply(games_menu)
            await state.set_state(SmartCommandStates.waiting_smart_games_choice)
            
        except Exception as e:
            logging.error(f"خطأ في اقتراح الألعاب: {e}")
            await message.reply("❌ حدث خطأ في اقتراح الألعاب")
    
    async def handle_adaptive_quiz(self, message: Message, user_id: int, chat_id: int, user_name: str, state: FSMContext):
        """الكويز الذكي التكيفي"""
        try:
            loading_msg = await message.reply("🧠 جارٍ إعداد كويز مخصص لمستواك...")
            
            quiz_data = await ai_integration.start_adaptive_quiz(user_id, chat_id)
            
            if quiz_data:
                question = quiz_data.get('question', '')
                options = quiz_data.get('options', [])
                
                quiz_text = f"🧠 **كويز ذكي تكيفي**\n\n❓ {question}\n\n"
                for i, option in enumerate(options, 1):
                    quiz_text += f"{i}️⃣ {option}\n"
                
                quiz_text += "\n💭 اكتب رقم الإجابة:"
                
                await loading_msg.edit_text(quiz_text)
                await state.set_state(SmartCommandStates.waiting_quiz_answer)
                await state.update_data(quiz_data=quiz_data)
            else:
                await loading_msg.edit_text("❌ لم أستطع إعداد كويز في الوقت الحالي")
                
        except Exception as e:
            logging.error(f"خطأ في الكويز التكيفي: {e}")
            await message.reply("❌ حدث خطأ في إعداد الكويز")
    
    async def handle_economic_challenge(self, message: Message, user_id: int, chat_id: int, user_name: str, state: FSMContext):
        """التحدي الاقتصادي الذكي"""
        try:
            loading_msg = await message.reply("💼 جارٍ إعداد تحدي اقتصادي...")
            
            challenge_data = await ai_integration.start_economic_challenge(user_id, chat_id)
            
            if challenge_data:
                scenario = challenge_data.get('scenario', '')
                options = challenge_data.get('options', [])
                
                challenge_text = f"💼 **التحدي الاقتصادي الذكي**\n\n🎯 {scenario}\n\n"
                for i, option in enumerate(options, 1):
                    challenge_text += f"{i}️⃣ {option}\n"
                
                challenge_text += "\n🤔 ما قرارك؟ اكتب الرقم:"
                
                await loading_msg.edit_text(challenge_text)
                await state.set_state(SmartCommandStates.waiting_challenge_answer)
                await state.update_data(challenge_data=challenge_data)
            else:
                await loading_msg.edit_text("❌ لم أستطع إعداد تحدي في الوقت الحالي")
                
        except Exception as e:
            logging.error(f"خطأ في التحدي الاقتصادي: {e}")
            await message.reply("❌ حدث خطأ في إعداد التحدي")
    
    async def handle_interactive_story(self, message: Message, user_id: int, chat_id: int, user_name: str, state: FSMContext):
        """القصة التفاعلية الذكية"""
        try:
            loading_msg = await message.reply("📖 جارٍ إعداد قصة تفاعلية...")
            
            story_data = await ai_integration.start_interactive_story(user_id, chat_id)
            
            if story_data:
                story_text = story_data.get('story_text', '')
                choices = story_data.get('choices', [])
                
                story_display = f"📖 **القصة التفاعلية الذكية**\n\n{story_text}\n\n"
                for i, choice in enumerate(choices, 1):
                    story_display += f"{i}️⃣ {choice}\n"
                
                story_display += "\n✨ اختر مسارك، اكتب الرقم:"
                
                await loading_msg.edit_text(story_display)
                await state.set_state(SmartCommandStates.waiting_story_choice)
                await state.update_data(story_data=story_data)
            else:
                await loading_msg.edit_text("❌ لم أستطع إعداد قصة في الوقت الحالي")
                
        except Exception as e:
            logging.error(f"خطأ في القصة التفاعلية: {e}")
            await message.reply("❌ حدث خطأ في إعداد القصة")
    
    async def handle_ai_battle(self, message: Message, user_id: int, chat_id: int, user_name: str, state: FSMContext):
        """معركة الذكاء مع يوكي"""
        try:
            loading_msg = await message.reply("⚔️ يوكي يستعد للمعركة...")
            
            battle_data = await ai_integration.start_ai_battle(user_id, chat_id)
            
            if battle_data:
                challenge = battle_data.get('challenge', '')
                options = battle_data.get('options', [])
                
                battle_text = f"⚔️ **معركة الذكاء مع يوكي**\n\n🤖 يوكي: {challenge}\n\n"
                for i, option in enumerate(options, 1):
                    battle_text += f"{i}️⃣ {option}\n"
                
                battle_text += f"\n🔥 تحداني يا {user_name}! اكتب رقم إجابتك:"
                
                await loading_msg.edit_text(battle_text)
                await state.set_state(SmartCommandStates.waiting_battle_answer)
                await state.update_data(battle_data=battle_data)
            else:
                await loading_msg.edit_text("❌ يوكي لا يستطيع المعركة الآن")
                
        except Exception as e:
            logging.error(f"خطأ في معركة الذكاء: {e}")
            await message.reply("❌ حدث خطأ في إعداد المعركة")
    
    async def handle_system_status(self, message: Message, user_id: int, chat_id: int, user_name: str):
        """حالة الأنظمة الذكية"""
        try:
            loading_msg = await message.reply("🔧 جارٍ فحص الأنظمة...")
            
            status = await ai_integration.get_ai_system_status()
            
            if 'error' in status:
                await loading_msg.edit_text("❌ خطأ في فحص الأنظمة")
                return
            
            status_text = f"🔧 **حالة الأنظمة الذكية**\n\n"
            
            # نظام الذكاء الاصطناعي الشامل
            ai_status = status.get('comprehensive_ai', {})
            ai_icon = "🟢" if ai_status.get('available') else "🔴"
            status_text += f"{ai_icon} الذكاء الاصطناعي الشامل\n"
            status_text += f"   🤖 المزود: {ai_status.get('provider', 'غير متاح')}\n"
            status_text += f"   🧠 الذاكرة: {'✅' if ai_status.get('memory_enabled') else '❌'}\n"
            
            # معالج الرسائل الذكي
            processor_status = status.get('smart_processor', {})
            processor_icon = "🟢" if processor_status.get('available') else "🔴" 
            status_text += f"\n{processor_icon} معالج الرسائل الذكي\n"
            status_text += f"   🛡️ الحماية من البذاءة: {'✅' if processor_status.get('profanity_protection') else '❌'}\n"
            
            # النظام الاقتصادي الذكي
            econ_status = status.get('intelligent_economics', {})
            econ_icon = "🟢" if econ_status.get('available') else "🔴"
            status_text += f"\n{econ_icon} النظام الاقتصادي الذكي\n"
            status_text += f"   📊 استراتيجيات محملة: {econ_status.get('strategies_loaded', 0)}\n"
            
            # نظام الألعاب الذكية
            games_status = status.get('intelligent_games', {})
            games_icon = "🟢" if games_status.get('available') else "🔴"
            status_text += f"\n{games_icon} نظام الألعاب الذكية\n"
            status_text += f"   🎮 ألعاب متاحة: {games_status.get('games_loaded', 0)}\n"
            status_text += f"   📖 قصص تفاعلية: {games_status.get('stories_loaded', 0)}\n"
            
            status_text += f"\n⚡ جميع الأنظمة تعمل بكامل طاقتها!"
            
            await loading_msg.edit_text(status_text)
            
        except Exception as e:
            logging.error(f"خطأ في فحص حالة الأنظمة: {e}")
            await message.reply("❌ حدث خطأ في فحص الأنظمة")


# إنشاء معالج القوائم الذكية العام
smart_menu_handler = SmartMenuHandler()
"""
معالج تكامل الذكاء الاصطناعي - AI Integration Handler
يدمج جميع أنظمة الذكاء الاصطناعي مع handlers البوت الموجودة
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from aiogram.types import Message

# استيراد الأنظمة الذكية
from modules.comprehensive_ai_system import comprehensive_ai
from modules.smart_message_processor import smart_processor
from modules.intelligent_economics import intelligent_economics
from modules.intelligent_games import intelligent_games


class AIIntegrationHandler:
    """معالج تكامل جميع أنظمة الذكاء الاصطناعي مع البوت"""
    
    def __init__(self):
        self.comprehensive_ai = comprehensive_ai
        self.smart_processor = smart_processor
        self.intelligent_economics = intelligent_economics
        self.intelligent_games = intelligent_games
        
        # إعدادات التكامل
        self.integration_settings = {
            'ai_responses_enabled': True,
            'smart_economics_enabled': True,
            'intelligent_games_enabled': True,
            'learning_mode': True,
            'auto_suggestions': True
        }
    
    async def handle_message_with_ai(self, message: Message) -> Optional[str]:
        """معالجة الرسالة مع الذكاء الاصطناعي"""
        try:
            # استخدام المعالج الذكي للرسائل
            ai_response = await self.smart_processor.process_message(message)
            
            if ai_response:
                # إضافة اقتراحات ذكية إضافية إذا أمكن
                if self.integration_settings['auto_suggestions']:
                    enhanced_response = await self._enhance_response_with_suggestions(
                        message, ai_response
                    )
                    return enhanced_response
                
                return ai_response
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في معالجة الرسالة بالذكاء الاصطناعي: {e}")
            return None
    
    async def _enhance_response_with_suggestions(self, message: Message, base_response: str) -> str:
        """تحسين الرد بإضافة اقتراحات ذكية"""
        try:
            if not message.from_user or not message.text:
                return base_response
                
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # جلب بيانات المستخدم
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            
            # إضافة اقتراحات اقتصادية
            if 'استثمار' in message.text.lower() or 'فلوس' in message.text.lower():
                suggestions = await self.intelligent_economics.get_personalized_recommendations(user_data)
                if suggestions:
                    base_response += f"\n\n💡 **نصائحي الذكية:**\n"
                    base_response += f"• {suggestions[0]}\n"
                    if len(suggestions) > 1:
                        base_response += f"• {suggestions[1]}"
            
            # إضافة اقتراحات الألعاب
            elif 'لعبة' in message.text.lower() or 'العاب' in message.text.lower():
                game_suggestions = await self.intelligent_games.get_personalized_game_suggestions(user_data)
                if game_suggestions:
                    base_response += f"\n\n🎮 **ألعاب مناسبة لك:**\n"
                    base_response += f"• {game_suggestions[0]['name']}: {game_suggestions[0]['description']}"
            
            return base_response
            
        except Exception as e:
            logging.error(f"خطأ في تحسين الرد: {e}")
            return base_response
    
    async def generate_economic_analysis(self, user_id: int, chat_id: int) -> str:
        """توليد تحليل اقتصادي شامل للمستخدم"""
        try:
            # جلب بيانات المستخدم والمجموعة
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            group_analytics = await self.comprehensive_ai.get_group_analytics(chat_id)
            
            # توليد التحليل الاقتصادي
            analysis = await self.intelligent_economics.generate_economic_insights(
                user_data, group_analytics
            )
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في توليد التحليل الاقتصادي: {e}")
            return "🤖 عذراً، لا يمكنني توليد التحليل الاقتصادي في الوقت الحالي. حاول لاحقاً!"
    
    async def suggest_investment_strategy(self, user_id: int, chat_id: int) -> str:
        """اقتراح استراتيجية استثمار مخصصة"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            strategy = await self.intelligent_economics.suggest_investment_strategy(user_data)
            
            strategy_text = f"""
🎯 **{strategy['name']}**

📊 **التوزيع المقترح:**
• نقد: {strategy['cash_allocation']}%
• بنك: {strategy['bank_allocation']}%
• عقارات: {strategy['real_estate_allocation']}%
• أسهم: {strategy['stocks_allocation']}%
• زراعة: {strategy['farming_allocation']}%

🏰 **القلعة:** {'مُوصى بها' if strategy['castle_investment'] else 'غير ضرورية حالياً'}

⏰ **الإطار الزمني:** {strategy['timeline']}
📈 **العائد المتوقع:** {strategy['expected_return']}

💡 هذه الاستراتيجية مصممة خصيصاً لوضعك المالي الحالي!
"""
            
            return strategy_text
            
        except Exception as e:
            logging.error(f"خطأ في اقتراح استراتيجية الاستثمار: {e}")
            return "🤖 عذراً، لا يمكنني اقتراح استراتيجية في الوقت الحالي. حاول لاحقاً!"
    
    async def get_game_suggestions(self, user_id: int, chat_id: int) -> str:
        """الحصول على اقتراحات الألعاب المخصصة"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            suggestions = await self.intelligent_games.get_personalized_game_suggestions(user_data)
            
            if not suggestions:
                return "🎮 لا توجد ألعاب مناسبة لمستواك حالياً. استمر في التطوير!"
            
            games_text = "🎮 **الألعاب المناسبة لك:**\n\n"
            
            for i, game in enumerate(suggestions[:3], 1):
                games_text += f"{i}. **{game['name']}**\n"
                games_text += f"   {game['description']}\n"
                games_text += f"   🏆 مكافأة: {game['estimated_xp']} XP\n"
                games_text += f"   📊 الصعوبة: {game['difficulty']['name']}\n"
                games_text += f"   💭 السبب: {game['recommended_reason']}\n\n"
            
            games_text += "💡 اكتب اسم اللعبة للبدء!"
            
            return games_text
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على اقتراحات الألعاب: {e}")
            return "🤖 عذراً، لا يمكنني اقتراح ألعاب في الوقت الحالي. حاول لاحقاً!"
    
    async def start_adaptive_quiz(self, user_id: int, chat_id: int, category: str = 'general') -> Optional[Dict[str, Any]]:
        """بدء كويز تكيفي"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            quiz_data = await self.intelligent_games.generate_adaptive_quiz(user_data, category)
            return quiz_data
            
        except Exception as e:
            logging.error(f"خطأ في بدء الكويز التكيفي: {e}")
            return None
    
    async def start_economic_challenge(self, user_id: int, chat_id: int) -> Optional[Dict[str, Any]]:
        """بدء تحدي اقتصادي"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            challenge_data = await self.intelligent_games.generate_economic_challenge(user_data)
            return challenge_data
            
        except Exception as e:
            logging.error(f"خطأ في بدء التحدي الاقتصادي: {e}")
            return None
    
    async def start_interactive_story(self, user_id: int, chat_id: int, story_id: str = 'merchant_journey') -> Optional[Dict[str, Any]]:
        """بدء قصة تفاعلية"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            story_data = await self.intelligent_games.start_interactive_story(user_data, story_id)
            return story_data
            
        except Exception as e:
            logging.error(f"خطأ في بدء القصة التفاعلية: {e}")
            return None
    
    async def start_ai_battle(self, user_id: int, chat_id: int) -> Optional[Dict[str, Any]]:
        """بدء معركة ذكية مع يوكي"""
        try:
            user_data = await self.comprehensive_ai.get_comprehensive_user_data(user_id, chat_id)
            battle_data = await self.intelligent_games.generate_ai_battle_challenge(user_data)
            return battle_data
            
        except Exception as e:
            logging.error(f"خطأ في بدء معركة الذكاء: {e}")
            return None
    
    async def get_ai_system_status(self) -> Dict[str, Any]:
        """الحصول على حالة جميع أنظمة الذكاء الاصطناعي"""
        try:
            ai_status = self.comprehensive_ai.get_system_status()
            processor_stats = await self.smart_processor.get_processing_stats()
            
            status = {
                'comprehensive_ai': {
                    'available': ai_status['anthropic_available'] or ai_status['gemini_available'],
                    'provider': ai_status['current_provider'],
                    'memory_enabled': ai_status['memory_enabled'],
                    'personality_protection': ai_status['personality_protection']
                },
                'smart_processor': {
                    'available': processor_stats['comprehensive_ai_available'],
                    'basic_ai': processor_stats['basic_ai_available'],
                    'special_responses': processor_stats['special_responses_loaded'],
                    'profanity_protection': processor_stats['profanity_protection']
                },
                'intelligent_economics': {
                    'available': True,
                    'strategies_loaded': len(self.intelligent_economics.economic_strategies),
                    'market_patterns': len(self.intelligent_economics.market_patterns)
                },
                'intelligent_games': {
                    'available': True,
                    'games_loaded': len(self.intelligent_games.smart_games),
                    'stories_loaded': len(self.intelligent_games.interactive_stories)
                },
                'integration_settings': self.integration_settings
            }
            
            return status
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على حالة الأنظمة: {e}")
            return {'error': str(e)}
    
    async def update_integration_settings(self, settings: Dict[str, Any]):
        """تحديث إعدادات التكامل"""
        try:
            self.integration_settings.update(settings)
            
            # تحديث إعدادات الأنظمة الفرعية
            if 'ai_responses_enabled' in settings:
                await self.smart_processor.update_settings({
                    'ai_response_probability': 0.5 if settings['ai_responses_enabled'] else 0.1
                })
            
            logging.info(f"تم تحديث إعدادات التكامل: {settings}")
            
        except Exception as e:
            logging.error(f"خطأ في تحديث إعدادات التكامل: {e}")


# إنشاء معالج التكامل الرئيسي
ai_integration = AIIntegrationHandler()
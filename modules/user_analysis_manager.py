"""
🧠 مدير نظام تحليل المستخدمين - المكون الرئيسي
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta

from database.user_analysis_operations import UserAnalysisOperations
from modules.user_analysis_engine import UserAnalysisEngine, AdvancedUserAnalyzer


class UserAnalysisManager:
    """مدير نظام تحليل المستخدمين الرئيسي"""
    
    def __init__(self):
        self.is_initialized = False
        self.analysis_queue = asyncio.Queue()
        self.processing = False
    
    async def initialize(self):
        """تهيئة نظام التحليل"""
        try:
            # إنشاء جداول قاعدة البيانات
            from database.user_analysis_schema import create_user_analysis_tables
            await create_user_analysis_tables()
            
            self.is_initialized = True
            logging.info("🧠 تم تهيئة نظام تحليل المستخدمين بنجاح!")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نظام التحليل: {e}")
            return False
    
    async def process_message(self, user_id: int, message_text: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """معالجة وتحليل رسالة مستخدم"""
        try:
            # التحقق من تفعيل التحليل في المجموعة
            if chat_id and not await UserAnalysisOperations.is_analysis_enabled(chat_id):
                return {}
            
            # تحليل الرسالة
            analysis = await UserAnalysisEngine.analyze_message(user_id, message_text, chat_id)
            
            if analysis:
                # تحديث ملف المستخدم
                await AdvancedUserAnalyzer.update_user_profile(user_id, analysis)
                
                # معالجة العلاقات الاجتماعية إذا كانت مجموعة
                if chat_id and analysis.get('social_indicators', {}).get('mentions_others'):
                    await self._process_social_interactions(user_id, chat_id, analysis)
                
                # إضافة ذكرى المحادثة إذا كانت مهمة
                if len(message_text) > 50 or analysis.get('sentiment_score', 0) != 0:
                    await self._add_conversation_memory(user_id, message_text, analysis, chat_id)
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في معالجة رسالة المستخدم {user_id}: {e}")
            return {}
    
    async def process_game_activity(self, user_id: int, game_type: str, result: str, 
                                  amount: int = 0, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """معالجة نشاط الألعاب"""
        try:
            # التحقق من تفعيل التحليل
            if chat_id and not await UserAnalysisOperations.is_analysis_enabled(chat_id):
                return {}
            
            # تحليل سلوك اللعب
            analysis = await AdvancedUserAnalyzer.analyze_game_behavior(user_id, game_type, result, amount)
            
            # تحديث إحصائيات المستخدم
            await self._update_user_stats(user_id, 'game', {'game_type': game_type, 'result': result, 'amount': amount})
            
            # توليد تنبؤات مستقبلية
            await self._generate_game_predictions(user_id, game_type, result)
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في معالجة نشاط الألعاب للمستخدم {user_id}: {e}")
            return {}
    
    async def process_financial_activity(self, user_id: int, transaction_type: str, amount: int,
                                       chat_id: Optional[int] = None) -> Dict[str, Any]:
        """معالجة النشاط المالي"""
        try:
            # التحقق من تفعيل التحليل
            if chat_id and not await UserAnalysisOperations.is_analysis_enabled(chat_id):
                return {}
            
            # تحليل السلوك المالي
            analysis = await AdvancedUserAnalyzer.analyze_financial_behavior(user_id, transaction_type, amount)
            
            # تحديث إحصائيات المستخدم
            await self._update_user_stats(user_id, 'financial', {'transaction_type': transaction_type, 'amount': amount})
            
            # توليد توصيات مالية
            await self._generate_financial_recommendations(user_id, transaction_type, amount)
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في معالجة النشاط المالي للمستخدم {user_id}: {e}")
            return {}
    
    async def get_personalized_response(self, user_id: int, context: str = 'general') -> str:
        """توليد رد مخصص بناءً على تحليل المستخدم"""
        try:
            # الحصول على تحليل المستخدم
            analysis = await UserAnalysisOperations.get_user_analysis(user_id)
            if not analysis:
                return ""
            
            # الحصول على الذكريات المهمة
            memories = await UserAnalysisOperations.get_user_memories(user_id, limit=5, min_importance=0.6)
            
            # توليد رد مخصص بناءً على الشخصية والذكريات
            response = await self._generate_personalized_response(analysis, memories, context)
            
            return response
            
        except Exception as e:
            logging.error(f"خطأ في توليد رد مخصص للمستخدم {user_id}: {e}")
            return ""
    
    async def get_user_insights(self, user_id: int) -> Dict[str, Any]:
        """الحصول على إحصائيات وتحليلات المستخدم"""
        try:
            analysis = await UserAnalysisOperations.get_user_analysis(user_id)
            if not analysis:
                return {}
            
            memories = await UserAnalysisOperations.get_user_memories(user_id, limit=10)
            
            insights = {
                'personality_summary': await self._get_personality_summary(analysis),
                'interests_summary': await self._get_interests_summary(analysis),
                'activity_patterns': analysis.get('activity_pattern', {}),
                'mood_trends': await self._analyze_mood_trends(analysis.get('mood_history', [])),
                'recent_memories': [memory['memory_summary'] for memory in memories[:5]],
                'social_level': await self._calculate_social_level(user_id),
                'recommendations': await self._generate_user_recommendations(user_id, analysis)
            }
            
            return insights
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على إحصائيات المستخدم {user_id}: {e}")
            return {}
    
    async def get_relationship_insights(self, user1_id: int, user2_id: int) -> Dict[str, Any]:
        """تحليل العلاقة بين مستخدمين"""
        try:
            # ترتيب المستخدمين
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
            
            # الحصول على بيانات العلاقة
            async with aiosqlite.connect(DATABASE_URL) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("""
                    SELECT * FROM user_relationships 
                    WHERE user1_id = ? AND user2_id = ?
                """, (user1_id, user2_id))
                
                relationship = await cursor.fetchone()
                
                if relationship:
                    relationship_data = dict(relationship)
                    if relationship_data.get('interaction_type'):
                        relationship_data['interaction_type'] = json.loads(relationship_data['interaction_type'])
                    
                    insights = {
                        'relationship_strength': relationship_data['relationship_strength'],
                        'friendship_level': relationship_data['friendship_level'],
                        'total_interactions': relationship_data['total_interactions'],
                        'games_together': relationship_data['games_together'],
                        'interaction_style': relationship_data.get('interaction_type', {}),
                        'compatibility_score': await self._calculate_compatibility(user1_id, user2_id),
                        'suggestions': await self._get_relationship_suggestions(user1_id, user2_id, relationship_data)
                    }
                    
                    return insights
                
                return {'message': 'لا توجد تفاعلات كافية لتحليل العلاقة'}
            
        except Exception as e:
            logging.error(f"خطأ في تحليل العلاقة بين {user1_id} و {user2_id}: {e}")
            return {}
    
    # ======================== دوال مساعدة خاصة ========================
    
    async def _process_social_interactions(self, user_id: int, chat_id: int, analysis: Dict[str, Any]):
        """معالجة التفاعلات الاجتماعية"""
        # هذه دالة مبسطة - يمكن تطويرها لكشف التفاعلات مع مستخدمين آخرين
        pass
    
    async def _add_conversation_memory(self, user_id: int, message: str, analysis: Dict[str, Any], chat_id: Optional[int]):
        """إضافة ذكرى محادثة"""
        if analysis.get('mood') and analysis['mood'] != 'محايد':
            importance = 0.6 if abs(analysis.get('sentiment_score', 0)) > 0.3 else 0.3
            
            await UserAnalysisOperations.add_user_memory(
                user_id=user_id,
                memory_type='conversation',
                memory_data={
                    'message_preview': message[:100],
                    'mood': analysis['mood'],
                    'sentiment': analysis.get('sentiment_score', 0),
                    'keywords': analysis.get('keywords', [])
                },
                importance_score=importance,
                emotional_impact=analysis.get('sentiment_score', 0),
                context_location=str(chat_id) if chat_id else None
            )
    
    async def _update_user_stats(self, user_id: int, activity_type: str, details: Dict[str, Any]):
        """تحديث إحصائيات المستخدم"""
        current_analysis = await UserAnalysisOperations.get_user_analysis(user_id)
        if current_analysis:
            updates = {}
            
            if activity_type == 'game':
                updates['games_played'] = current_analysis.get('games_played', 0) + 1
            elif activity_type == 'financial':
                updates['investments_made'] = current_analysis.get('investments_made', 0) + 1
            
            # تحديث نوع اللعبة المفضل
            if activity_type == 'game' and details.get('game_type'):
                updates['favorite_game_type'] = details['game_type']
            
            if updates:
                # تحديث قاعدة البيانات (تحتاج دالة محددة)
                pass
    
    async def _generate_game_predictions(self, user_id: int, game_type: str, result: str):
        """توليد تنبؤات الألعاب"""
        # منطق توليد التنبؤات بناءً على التاريخ
        pass
    
    async def _generate_financial_recommendations(self, user_id: int, transaction_type: str, amount: int):
        """توليد توصيات مالية"""
        # منطق توليد التوصيات المالية
        pass
    
    async def _generate_personalized_response(self, analysis: Dict[str, Any], memories: List[Dict[str, Any]], context: str) -> str:
        """توليد رد مخصص"""
        personality = analysis
        
        # رد بناءً على الشخصية
        if personality.get('extravert_score', 0.5) > 0.7:
            base_response = "يلا بينا! "
        elif personality.get('risk_taker_score', 0.5) > 0.7:
            base_response = "تجرب حاجة جديدة؟ "
        else:
            base_response = "إيه رأيك؟ "
        
        # إضافة ذكرى إذا وجدت
        if memories and context == 'game':
            recent_memory = memories[0]
            if recent_memory.get('memory_type') == 'game_win':
                base_response += f"أتذكر فوزك الرائع في {recent_memory.get('memory_summary', '')}! "
        
        return base_response
    
    async def _get_personality_summary(self, analysis: Dict[str, Any]) -> str:
        """ملخص الشخصية"""
        traits = []
        
        if analysis.get('extravert_score', 0.5) > 0.6:
            traits.append("اجتماعي")
        if analysis.get('risk_taker_score', 0.5) > 0.6:
            traits.append("مغامر")
        if analysis.get('leader_score', 0.5) > 0.6:
            traits.append("قيادي")
        if analysis.get('competitive_score', 0.5) > 0.6:
            traits.append("تنافسي")
        if analysis.get('patient_score', 0.5) > 0.6:
            traits.append("صبور")
        
        return "، ".join(traits) if traits else "شخصية متوازنة"
    
    async def _get_interests_summary(self, analysis: Dict[str, Any]) -> str:
        """ملخص الاهتمامات"""
        interests = []
        
        if analysis.get('games_interest', 0) > 0.4:
            interests.append("الألعاب")
        if analysis.get('money_interest', 0) > 0.4:
            interests.append("المال والاستثمار")
        if analysis.get('social_interest', 0) > 0.4:
            interests.append("التفاعل الاجتماعي")
        if analysis.get('entertainment_interest', 0) > 0.4:
            interests.append("التسلية")
        
        return "، ".join(interests) if interests else "اهتمامات متنوعة"
    
    async def _analyze_mood_trends(self, mood_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """تحليل اتجاهات المزاج"""
        if not mood_history:
            return {"trend": "غير محدد", "dominant_mood": "محايد"}
        
        moods = [entry.get('mood', 'محايد') for entry in mood_history[-10:]]
        mood_counts = {}
        
        for mood in moods:
            mood_counts[mood] = mood_counts.get(mood, 0) + 1
        
        dominant_mood = max(mood_counts.keys(), key=lambda k: mood_counts[k]) if mood_counts else "محايد"
        
        return {
            "trend": "إيجابي" if dominant_mood in ['سعيد', 'متحمس', 'متفائل'] else "محايد",
            "dominant_mood": dominant_mood,
            "variety": len(set(moods))
        }
    
    async def _calculate_social_level(self, user_id: int) -> str:
        """حساب مستوى التفاعل الاجتماعي"""
        # عدد التفاعلات والعلاقات
        try:
            from config.database import DATABASE_URL
            import aiosqlite
            
            async with aiosqlite.connect(DATABASE_URL) as db:
                # عدد العلاقات
                cursor = await db.execute("""
                    SELECT COUNT(*) FROM user_relationships 
                    WHERE user1_id = ? OR user2_id = ?
                """, (user_id, user_id))
                
                relationship_count = await cursor.fetchone()
                count = relationship_count[0] if relationship_count else 0
                
                if count > 10:
                    return "اجتماعي جداً"
                elif count > 5:
                    return "اجتماعي"
                elif count > 2:
                    return "متوسط التفاعل"
                else:
                    return "هادئ"
                
        except Exception:
            return "غير محدد"
    
    async def _generate_user_recommendations(self, user_id: int, analysis: Dict[str, Any]) -> List[str]:
        """توليد توصيات للمستخدم"""
        recommendations = []
        
        # توصيات بناءً على الاهتمامات
        if analysis.get('games_interest', 0) > 0.5:
            recommendations.append("جرب لعبة الرموز الجديدة!")
        
        if analysis.get('money_interest', 0) > 0.5:
            recommendations.append("تحقق من فرص الاستثمار المتاحة")
        
        # توصيات بناءً على الشخصية
        if analysis.get('competitive_score', 0.5) > 0.6:
            recommendations.append("شارك في منافسة مع الأصدقاء")
        
        if analysis.get('social_interest', 0) > 0.5:
            recommendations.append("انضم إلى المحادثات الجماعية")
        
        return recommendations[:3]  # أفضل 3 توصيات
    
    async def _calculate_compatibility(self, user1_id: int, user2_id: int) -> float:
        """حساب التوافق بين مستخدمين"""
        try:
            analysis1 = await UserAnalysisOperations.get_user_analysis(user1_id)
            analysis2 = await UserAnalysisOperations.get_user_analysis(user2_id)
            
            if not analysis1 or not analysis2:
                return 0.5
            
            # حساب التوافق بناءً على الاهتمامات والشخصية
            compatibility = 0.0
            
            # توافق الاهتمامات
            interests1 = [analysis1.get('games_interest', 0), analysis1.get('money_interest', 0)]
            interests2 = [analysis2.get('games_interest', 0), analysis2.get('money_interest', 0)]
            
            interest_similarity = 1 - sum(abs(i1 - i2) for i1, i2 in zip(interests1, interests2)) / len(interests1)
            compatibility += interest_similarity * 0.4
            
            # توافق الشخصية
            if analysis1.get('competitive_score', 0.5) > 0.6 and analysis2.get('competitive_score', 0.5) > 0.6:
                compatibility += 0.3  # كلاهما تنافسي
            
            if analysis1.get('social_interest', 0) > 0.5 and analysis2.get('social_interest', 0) > 0.5:
                compatibility += 0.3  # كلاهما اجتماعي
            
            return min(1.0, compatibility)
            
        except Exception as e:
            logging.error(f"خطأ في حساب التوافق: {e}")
            return 0.5
    
    async def _get_relationship_suggestions(self, user1_id: int, user2_id: int, relationship_data: Dict[str, Any]) -> List[str]:
        """توصيات لتحسين العلاقة"""
        suggestions = []
        
        strength = relationship_data.get('relationship_strength', 0)
        games_together = relationship_data.get('games_together', 0)
        
        if strength < 0.5:
            suggestions.append("جربوا لعب ألعاب جماعية أكثر")
        
        if games_together < 5:
            suggestions.append("شاركوا في منافسات ودية")
        
        suggestions.append("تبادلوا الرسائل أكثر")
        
        return suggestions


# إنشاء مدير عام للنظام
user_analysis_manager = UserAnalysisManager()
"""
🧠 محرك تحليل المستخدمين المتقدم
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from database.user_analysis_operations import UserAnalysisOperations, quick_personality_update, quick_interest_update


class UserAnalysisEngine:
    """محرك تحليل المستخدمين الذكي"""
    
    # 📝 كلمات مفتاحية للمشاعر والمزاج
    MOOD_KEYWORDS = {
        'سعيد': ['سعيد', 'فرحان', 'مبسوط', 'رائع', 'ممتاز', 'حلو', 'جميل', '😊', '😄', '😁', '🥰', '❤️'],
        'حزين': ['حزين', 'زعلان', 'مكتئب', 'تعبان', 'مش حلو', 'سيء', '😢', '😭', '💔', '😞'],
        'غاضب': ['غاضب', 'زعلان', 'عصبي', 'متنرفز', 'محبط', 'مش عاجبني', '😠', '😡', '🤬'],
        'متحمس': ['متحمس', 'متشوق', 'حماس', 'يلا', 'هيا', 'جاهز', 'تعال', '🔥', '⚡', '💪'],
        'ملول': ['ملول', 'مضجر', 'تعبان', 'مش عارف اعمل ايه', 'مافيش حاجة', '😴', '😑'],
        'متفائل': ['متفائل', 'ان شاء الله', 'هيكون حلو', 'اكيد', 'مؤكد', '🌟', '✨'],
        'قلقان': ['قلقان', 'خايف', 'مش متأكد', 'محتار', 'مش عارف', '😰', '😟']
    }
    
    # 🎮 كلمات مفتاحية للاهتمامات
    INTEREST_KEYWORDS = {
        'games': ['لعبة', 'العب', 'فوز', 'خسارة', 'نقاط', 'مستوى', 'تحدي', 'منافسة'],
        'money': ['فلوس', 'مال', 'استثمار', 'بنك', 'رصيد', 'ارباح', 'خسارة', 'اسهم'],
        'social': ['صديق', 'اصحاب', 'مع', 'معايا', 'احنا', 'خلاص نلعب', 'يلا بينا'],
        'entertainment': ['مزح', 'ضحك', 'نكتة', 'كوميديا', 'تسلية', 'ترفيه']
    }
    
    # 🎯 أنماط الشخصية
    PERSONALITY_PATTERNS = {
        'extravert': ['مع الكل', 'احنا', 'يلا بينا', 'تعالوا', 'جماعي'],
        'risk_taker': ['مغامرة', 'جرب', 'يلا نشوف', 'ممكن', 'مش مشكلة'],
        'leader': ['يلا', 'تعالوا', 'هنعمل', 'انا هعمل', 'خلاص كده'],
        'patient': ['استنى', 'بتأني', 'مش عجلان', 'خلاص نستنى', 'بكرة'],
        'competitive': ['فوز', 'اكسب', 'احسن', 'الأول', 'منافسة', 'تحدي']
    }
    
    # 🎲 أنواع الألعاب
    GAME_TYPES = {
        'strategy': ['رموز', 'كلمات', 'صح خطأ', 'معلومات'],
        'luck': ['عجلة الحظ', 'حظ', 'عشوائي'],
        'competitive': ['منافسة', 'مع', 'ضد'],
        'puzzle': ['ألغاز', 'تفكير', 'ذكاء']
    }
    
    @staticmethod
    async def analyze_message(user_id: int, message_text: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """تحليل رسالة المستخدم شامل"""
        try:
            analysis_result = {
                'mood': await UserAnalysisEngine._detect_mood(message_text),
                'sentiment_score': await UserAnalysisEngine._calculate_sentiment(message_text),
                'interests': await UserAnalysisEngine._detect_interests(message_text),
                'personality_traits': await UserAnalysisEngine._detect_personality_traits(message_text),
                'keywords': await UserAnalysisEngine._extract_keywords(message_text),
                'activity_type': await UserAnalysisEngine._classify_activity(message_text),
                'social_indicators': await UserAnalysisEngine._detect_social_indicators(message_text, chat_id)
            }
            
            # تسجيل النشاط
            await UserAnalysisOperations.record_activity(
                user_id=user_id,
                activity_type=analysis_result['activity_type'],
                activity_details={
                    'message_length': len(message_text),
                    'keywords': analysis_result['keywords'],
                    'interests_detected': analysis_result['interests']
                },
                chat_id=chat_id,
                mood_detected=analysis_result['mood'],
                sentiment_score=analysis_result['sentiment_score']
            )
            
            return analysis_result
            
        except Exception as e:
            logging.error(f"خطأ في تحليل الرسالة للمستخدم {user_id}: {e}")
            return {}
    
    @staticmethod
    async def _detect_mood(text: str) -> str:
        """كشف المزاج من النص"""
        text_lower = text.lower()
        mood_scores = {}
        
        for mood, keywords in UserAnalysisEngine.MOOD_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            mood_scores[mood] = score
        
        # العثور على أعلى نقاط
        if mood_scores and max(mood_scores.values()) > 0:
            return max(mood_scores.keys(), key=lambda k: mood_scores[k])
        
        return 'محايد'
    
    @staticmethod
    async def _calculate_sentiment(text: str) -> float:
        """حساب نقاط المشاعر (-1.0 إلى 1.0)"""
        positive_words = ['حلو', 'رائع', 'ممتاز', 'جميل', 'احب', 'سعيد', 'فرحان']
        negative_words = ['سيء', 'وحش', 'مش حلو', 'تعبان', 'حزين', 'زعلان']
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        total_words = len(text.split())
        if total_words == 0:
            return 0.0
        
        sentiment = (positive_count - negative_count) / max(total_words, 1)
        return max(-1.0, min(1.0, sentiment))
    
    @staticmethod
    async def _detect_interests(text: str) -> Dict[str, float]:
        """كشف الاهتمامات من النص"""
        text_lower = text.lower()
        interests = {}
        
        for interest, keywords in UserAnalysisEngine.INTEREST_KEYWORDS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                interests[interest] = min(1.0, score * 0.2)  # تطبيع النقاط
        
        return interests
    
    @staticmethod
    async def _detect_personality_traits(text: str) -> Dict[str, float]:
        """كشف صفات الشخصية من النص"""
        text_lower = text.lower()
        traits = {}
        
        for trait, keywords in UserAnalysisEngine.PERSONALITY_PATTERNS.items():
            score = 0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 1
            
            if score > 0:
                traits[trait] = min(1.0, score * 0.1)  # تطبيع النقاط
        
        return traits
    
    @staticmethod
    async def _extract_keywords(text: str) -> List[str]:
        """استخراج الكلمات المفتاحية"""
        # إزالة كلمات الوصل والأدوات
        stop_words = ['في', 'من', 'إلى', 'على', 'عن', 'مع', 'هذا', 'هذه', 'التي', 'الذي']
        
        words = re.findall(r'[\u0600-\u06FF\w]+', text.lower())
        keywords = [word for word in words if len(word) > 2 and word not in stop_words]
        
        return list(set(keywords))[:10]  # أهم 10 كلمات
    
    @staticmethod
    async def _classify_activity(text: str) -> str:
        """تصنيف نوع النشاط"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['لعبة', 'العب', 'فوز', 'خسارة']):
            return 'game'
        elif any(word in text_lower for word in ['فلوس', 'استثمار', 'بنك', 'اسهم']):
            return 'financial'
        elif any(word in text_lower for word in ['صديق', 'معايا', 'احنا', 'تعالوا']):
            return 'social'
        elif len(text) > 100:
            return 'conversation'
        else:
            return 'message'
    
    @staticmethod
    async def _detect_social_indicators(text: str, chat_id: Optional[int] = None) -> Dict[str, Any]:
        """كشف مؤشرات التفاعل الاجتماعي"""
        text_lower = text.lower()
        
        indicators = {
            'mentions_others': bool(re.search(r'@\w+', text)),
            'group_activity': bool(chat_id and chat_id < 0),  # المجموعات لها معرف سالب
            'cooperative_language': any(word in text_lower for word in ['معايا', 'احنا', 'تعالوا', 'يلا بينا']),
            'competitive_language': any(word in text_lower for word in ['ضد', 'منافسة', 'تحدي', 'اكسب'])
        }
        
        return indicators


class AdvancedUserAnalyzer:
    """محلل المستخدمين المتقدم للأنماط والسلوكيات"""
    
    @staticmethod
    async def update_user_profile(user_id: int, analysis_result: Dict[str, Any]) -> bool:
        """تحديث ملف المستخدم بناءً على التحليل"""
        try:
            # تحديث المزاج
            if analysis_result.get('mood') and analysis_result['mood'] != 'محايد':
                await UserAnalysisOperations.update_user_mood(
                    user_id, 
                    analysis_result['mood'],
                    analysis_result.get('sentiment_score', 0.0)
                )
            
            # تحديث الاهتمامات
            interests = analysis_result.get('interests', {})
            if interests:
                await UserAnalysisEngine.quick_interest_update(user_id, interests)
            
            # تحديث صفات الشخصية
            traits = analysis_result.get('personality_traits', {})
            if traits:
                await UserAnalysisEngine.quick_personality_update(user_id, traits)
            
            return True
            
        except Exception as e:
            logging.error(f"خطأ في تحديث ملف المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def analyze_game_behavior(user_id: int, game_type: str, result: str, amount: int = 0) -> Dict[str, Any]:
        """تحليل سلوك اللعب"""
        try:
            analysis = {
                'game_preference': await AdvancedUserAnalyzer._determine_game_preference(game_type),
                'risk_assessment': await AdvancedUserAnalyzer._assess_risk_taking(game_type, amount),
                'competitive_level': await AdvancedUserAnalyzer._measure_competitiveness(result),
                'patience_indicator': await AdvancedUserAnalyzer._measure_patience(game_type)
            }
            
            # إضافة ذكرى اللعبة
            memory_data = {
                'game_type': game_type,
                'result': result,
                'amount': amount,
                'timestamp': datetime.now().isoformat()
            }
            
            importance = 0.7 if result == 'win' else 0.4
            emotional_impact = 0.8 if result == 'win' else -0.3
            
            await UserAnalysisOperations.add_user_memory(
                user_id=user_id,
                memory_type='game_win' if result == 'win' else 'game_loss',
                memory_data=memory_data,
                importance_score=importance,
                emotional_impact=emotional_impact
            )
            
            # تحديث إحصائيات الألعاب
            await AdvancedUserAnalyzer._update_game_stats(user_id, analysis)
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في تحليل سلوك اللعب للمستخدم {user_id}: {e}")
            return {}
    
    @staticmethod
    async def analyze_financial_behavior(user_id: int, transaction_type: str, amount: int) -> Dict[str, Any]:
        """تحليل السلوك المالي"""
        try:
            analysis = {
                'investment_style': await AdvancedUserAnalyzer._determine_investment_style(transaction_type, amount),
                'risk_tolerance': await AdvancedUserAnalyzer._assess_financial_risk_tolerance(amount),
                'financial_planning': await AdvancedUserAnalyzer._assess_financial_planning(transaction_type)
            }
            
            # إضافة ذكرى مالية
            memory_data = {
                'transaction_type': transaction_type,
                'amount': amount,
                'timestamp': datetime.now().isoformat()
            }
            
            await UserAnalysisOperations.add_user_memory(
                user_id=user_id,
                memory_type='investment',
                memory_data=memory_data,
                importance_score=min(1.0, amount / 10000),  # الأهمية حسب المبلغ
                emotional_impact=0.5
            )
            
            # تحديث الاهتمامات المالية
            await quick_interest_update(user_id, 'money', 0.1)
            
            return analysis
            
        except Exception as e:
            logging.error(f"خطأ في تحليل السلوك المالي للمستخدم {user_id}: {e}")
            return {}
    
    @staticmethod
    async def _determine_game_preference(game_type: str) -> str:
        """تحديد تفضيل نوع اللعبة"""
        strategy_games = ['رموز', 'كلمات', 'صح_خطأ', 'معلومات']
        luck_games = ['عجلة_الحظ', 'حظ']
        
        if game_type in strategy_games:
            return 'استراتيجي'
        elif game_type in luck_games:
            return 'حظ'
        else:
            return 'متنوع'
    
    @staticmethod
    async def _assess_risk_taking(game_type: str, amount: int) -> float:
        """تقييم مستوى المخاطرة"""
        if amount > 5000:
            return 0.8  # مخاطر عالية
        elif amount > 1000:
            return 0.6  # مخاطر متوسطة
        else:
            return 0.3  # مخاطر منخفضة
    
    @staticmethod
    async def _measure_competitiveness(result: str) -> float:
        """قياس مستوى التنافسية"""
        if result == 'win':
            return 0.7
        else:
            return 0.4
    
    @staticmethod
    async def _measure_patience(game_type: str) -> float:
        """قياس مستوى الصبر"""
        patient_games = ['رموز', 'كلمات', 'معلومات']
        if game_type in patient_games:
            return 0.8
        else:
            return 0.4
    
    @staticmethod
    async def _determine_investment_style(transaction_type: str, amount: int) -> str:
        """تحديد أسلوب الاستثمار"""
        if transaction_type == 'آمن' or amount < 1000:
            return 'محافظ'
        elif amount > 10000:
            return 'مغامر'
        else:
            return 'متوازن'
    
    @staticmethod
    async def _assess_financial_risk_tolerance(amount: int) -> float:
        """تقييم تحمل المخاطر المالية"""
        if amount > 50000:
            return 0.9
        elif amount > 10000:
            return 0.7
        elif amount > 1000:
            return 0.5
        else:
            return 0.2
    
    @staticmethod
    async def _assess_financial_planning(transaction_type: str) -> float:
        """تقييم التخطيط المالي"""
        planning_indicators = ['آمن', 'طويل_المدى', 'استثمار']
        if transaction_type in planning_indicators:
            return 0.8
        else:
            return 0.3
    
    @staticmethod
    async def _update_game_stats(user_id: int, analysis: Dict[str, Any]) -> bool:
        """تحديث إحصائيات الألعاب"""
        try:
            # تحديث إحصائيات في قاعدة البيانات
            current_analysis = await UserAnalysisOperations.get_user_analysis(user_id)
            
            if current_analysis:
                # تحديث عدد الألعاب
                new_games_count = current_analysis.get('games_played', 0) + 1
                
                # تحديث الصفات بناءً على التحليل
                personality_updates = {}
                
                if analysis.get('competitive_level', 0) > 0.5:
                    personality_updates['competitive_score'] = min(1.0, 
                        current_analysis.get('competitive_score', 0.5) + 0.05)
                
                if analysis.get('patience_indicator', 0) > 0.6:
                    personality_updates['patient_score'] = min(1.0,
                        current_analysis.get('patient_score', 0.5) + 0.05)
                
                if analysis.get('risk_assessment', 0) > 0.6:
                    personality_updates['risk_taker_score'] = min(1.0,
                        current_analysis.get('risk_taker_score', 0.5) + 0.05)
                
                # تطبيق التحديثات
                if personality_updates:
                    await UserAnalysisOperations.update_user_personality(user_id, personality_updates)
                
                return True
            return False
            
        except Exception as e:
            logging.error(f"خطأ في تحديث إحصائيات الألعاب للمستخدم {user_id}: {e}")
            return False
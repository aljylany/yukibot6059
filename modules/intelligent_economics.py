"""
النظام الاقتصادي الذكي - Intelligent Economics System
نظام ذكي يحلل البيانات الاقتصادية ويقدم نصائح واستراتيجيات مخصصة
"""

import logging
import asyncio
import random
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
import json

class IntelligentEconomicsSystem:
    """نظام ذكي لتحليل البيانات الاقتصادية وتقديم النصائح"""
    
    def __init__(self):
        # قاعدة بيانات الاستراتيجيات الذكية
        self.economic_strategies = {
            'beginner': {
                'min_wealth': 0,
                'max_wealth': 10000,
                'recommendations': [
                    'ابدأ بفتح حساب بنكي لحفظ أموالك',
                    'احصل على راتبك اليومي بانتظام',
                    'جرب الاستثمار البسيط بمبالغ صغيرة',
                    'ازرع محاصيل سريعة النمو في مزرعتك'
                ]
            },
            'intermediate': {
                'min_wealth': 10001,
                'max_wealth': 100000,
                'recommendations': [
                    'نوع استثماراتك بين العقارات والأسهم',
                    'ابني قلعة لحماية ثروتك',
                    'استثمر في محاصيل عالية الربح',
                    'شارك في الأسواق بحذر'
                ]
            },
            'advanced': {
                'min_wealth': 100001,
                'max_wealth': 1000000,
                'recommendations': [
                    'طور استراتيجية استثمار متقدمة',
                    'استخدم القلعة للتجارة والدفاع',
                    'استثمر في الشركات طويلة المدى',
                    'كن رائد أعمال في المجموعة'
                ]
            },
            'expert': {
                'min_wealth': 1000001,
                'max_wealth': float('inf'),
                'recommendations': [
                    'قد المجتمع الاقتصادي',
                    'طور استراتيجيات متقدمة للآخرين',
                    'استثمر في مشاريع مبتكرة',
                    'كن مستشاراً اقتصادياً للأعضاء الجدد'
                ]
            }
        }
        
        # تحليل أنماط السوق
        self.market_patterns = {
            'stocks': {
                'trends': ['صاعد', 'نازل', 'مستقر'],
                'volatility_levels': ['منخفض', 'متوسط', 'عالي'],
                'recommendation_factors': ['الوقت', 'المخاطرة', 'العائد']
            },
            'real_estate': {
                'property_types': ['شقة', 'فيلا', 'عمارة', 'أرض'],
                'location_factors': ['الموقع', 'التطوير', 'الطلب'],
                'roi_periods': ['قصير', 'متوسط', 'طويل']
            },
            'farming': {
                'crop_categories': ['سريع', 'متوسط', 'بطيء'],
                'profit_margins': ['منخفض', 'متوسط', 'عالي'],
                'risk_levels': ['آمن', 'متوسط', 'مخاطر']
            }
        }
        
        # نصائح ذكية حسب الوقت
        self.time_based_advice = {
            'morning': [
                'صباح الخير! وقت مثالي لجمع محاصيلك الناضجة',
                'ابدأ يومك بفحص استثماراتك',
                'الصباح وقت جيد للقرارات المالية الهادئة'
            ],
            'afternoon': [
                'وقت الغداء مثالي لمراجعة محفظتك',
                'فترة ما بعد الظهر مناسبة للاستثمارات الجديدة',
                'تفقد أسعار الأسهم في هذا الوقت'
            ],
            'evening': [
                'المساء وقت مثالي لتخطيط استراتيجيتك',
                'راجع أرباحك اليومية قبل النوم',
                'المساء مناسب لقرارات الاستثمار طويل المدى'
            ]
        }
    
    async def analyze_user_economic_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """تحليل الملف الاقتصادي للمستخدم"""
        
        financial = user_data.get('financial', {})
        total_wealth = financial.get('total_wealth', 0)
        
        # تحديد مستوى الخبرة
        experience_level = self._determine_experience_level(total_wealth)
        
        # تحليل التوزيع المالي
        cash_balance = financial.get('cash_balance', 0)
        bank_balance = financial.get('bank_balance', 0)
        
        cash_ratio = (cash_balance / max(total_wealth, 1)) * 100
        bank_ratio = (bank_balance / max(total_wealth, 1)) * 100
        
        # تحليل الاستثمارات
        investments = user_data.get('investments', {})
        properties_value = investments.get('properties_value', 0)
        stocks_count = investments.get('stocks_count', 0)
        
        investment_ratio = (properties_value / max(total_wealth, 1)) * 100
        
        # تحليل المخاطرة
        risk_profile = self._calculate_risk_profile(user_data)
        
        # نقاط القوة والضعف
        strengths, weaknesses = self._analyze_strengths_weaknesses(user_data)
        
        return {
            'experience_level': experience_level,
            'total_wealth': total_wealth,
            'wealth_distribution': {
                'cash_ratio': round(cash_ratio, 2),
                'bank_ratio': round(bank_ratio, 2),
                'investment_ratio': round(investment_ratio, 2)
            },
            'risk_profile': risk_profile,
            'diversification_score': self._calculate_diversification_score(user_data),
            'strengths': strengths,
            'weaknesses': weaknesses,
            'growth_potential': self._assess_growth_potential(user_data)
        }
    
    def _determine_experience_level(self, wealth: int) -> str:
        """تحديد مستوى الخبرة بناءً على الثروة"""
        for level, data in self.economic_strategies.items():
            if data['min_wealth'] <= wealth <= data['max_wealth']:
                return level
        return 'beginner'
    
    def _calculate_risk_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب ملف المخاطرة"""
        financial = user_data.get('financial', {})
        total_wealth = financial.get('total_wealth', 0)
        cash_balance = financial.get('cash_balance', 0)
        
        # نسبة السيولة (مؤشر المخاطرة المنخفضة)
        liquidity_ratio = (cash_balance / max(total_wealth, 1)) * 100
        
        # عدد الاستثمارات (مؤشر التنويع)
        investments = user_data.get('investments', {})
        total_investments = investments.get('properties_count', 0) + investments.get('stocks_count', 0)
        
        # حساب نقاط المخاطرة
        risk_score = 0
        
        if liquidity_ratio > 70:
            risk_score += 1  # محافظ جداً
        elif liquidity_ratio > 50:
            risk_score += 2  # محافظ
        elif liquidity_ratio > 30:
            risk_score += 3  # متوازن
        else:
            risk_score += 4  # مخاطر
        
        if total_investments > 10:
            risk_score += 1  # متنوع جداً
        elif total_investments > 5:
            risk_score += 2  # متنوع
        else:
            risk_score += 3  # تنويع محدود
        
        # تصنيف المخاطرة
        if risk_score <= 3:
            risk_category = 'محافظ جداً'
            risk_advice = 'يمكنك زيادة المخاطرة قليلاً لتحسين العوائد'
        elif risk_score <= 5:
            risk_category = 'محافظ'
            risk_advice = 'ملف مخاطرة متوازن، فكر في بعض الاستثمارات المتقدمة'
        elif risk_score <= 7:
            risk_category = 'متوازن'
            risk_advice = 'ملف مخاطرة جيد، تأكد من الحفاظ على التوازن'
        else:
            risk_category = 'مخاطر عالية'
            risk_advice = 'فكر في تقليل المخاطرة وزيادة السيولة'
        
        return {
            'category': risk_category,
            'score': risk_score,
            'liquidity_ratio': round(liquidity_ratio, 2),
            'diversification_count': total_investments,
            'advice': risk_advice
        }
    
    def _calculate_diversification_score(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """حساب نقاط التنويع"""
        score = 0
        categories = []
        
        financial = user_data.get('financial', {})
        if financial.get('bank_balance', 0) > 0:
            score += 20
            categories.append('ادخار بنكي')
        
        investments = user_data.get('investments', {})
        if investments.get('properties_count', 0) > 0:
            score += 25
            categories.append('عقارات')
        
        if investments.get('stocks_count', 0) > 0:
            score += 25
            categories.append('أسهم')
        
        farming = user_data.get('farming', {})
        if farming.get('crops_count', 0) > 0:
            score += 15
            categories.append('زراعة')
        
        castle = user_data.get('castle', {})
        if castle.get('has_castle', False):
            score += 15
            categories.append('قلعة')
        
        # تقييم التنويع
        if score >= 80:
            level = 'ممتاز'
            advice = 'تنويع مثالي! استمر في هذا النهج'
        elif score >= 60:
            level = 'جيد'
            advice = 'تنويع جيد، يمكنك إضافة فئة أو اثنين'
        elif score >= 40:
            level = 'متوسط'
            advice = 'تحتاج لتنويع أكثر في استثماراتك'
        else:
            level = 'ضعيف'
            advice = 'ركز على تنويع محفظتك الاستثمارية'
        
        return {
            'score': score,
            'level': level,
            'categories': categories,
            'advice': advice
        }
    
    def _analyze_strengths_weaknesses(self, user_data: Dict[str, Any]) -> Tuple[List[str], List[str]]:
        """تحليل نقاط القوة والضعف"""
        strengths = []
        weaknesses = []
        
        financial = user_data.get('financial', {})
        total_wealth = financial.get('total_wealth', 0)
        bank_balance = financial.get('bank_balance', 0)
        
        # نقاط القوة
        if bank_balance > 0:
            strengths.append('لديك ادخار في البنك - هذا ممتاز!')
        
        if total_wealth > 50000:
            strengths.append('ثروة جيدة تتيح لك فرص استثمار متقدمة')
        
        investments = user_data.get('investments', {})
        if investments.get('properties_count', 0) > 0:
            strengths.append('تستثمر في العقارات - استثمار ذكي!')
        
        if investments.get('stocks_count', 0) > 0:
            strengths.append('لديك محفظة أسهم - تنويع جيد')
        
        gaming = user_data.get('gaming', {})
        if gaming.get('level', 1) > 10:
            strengths.append('مستوى عالي يدل على خبرة ونشاط')
        
        # نقاط الضعف
        cash_ratio = (financial.get('cash_balance', 0) / max(total_wealth, 1)) * 100
        
        if cash_ratio > 80:
            weaknesses.append('أموال كثيرة خارج البنك - خطر السرقة عالي')
        
        if investments.get('properties_count', 0) == 0:
            weaknesses.append('لا تستثمر في العقارات - فرصة مفقودة')
        
        if total_wealth < 10000:
            weaknesses.append('ثروة محدودة - ركز على زيادة الدخل')
        
        farming = user_data.get('farming', {})
        if farming.get('crops_count', 0) == 0:
            weaknesses.append('لا تستخدم المزرعة - دخل إضافي مفقود')
        
        castle = user_data.get('castle', {})
        if not castle.get('has_castle', False):
            weaknesses.append('بدون قلعة - أموالك غير محمية')
        
        return strengths, weaknesses
    
    def _assess_growth_potential(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """تقييم إمكانية النمو"""
        financial = user_data.get('financial', {})
        gaming = user_data.get('gaming', {})
        
        factors = {
            'wealth_level': min((financial.get('total_wealth', 0) / 100000) * 25, 25),
            'activity_level': min((gaming.get('level', 1) / 20) * 25, 25),
            'diversification': self._calculate_diversification_score(user_data)['score'] / 4,
            'banking_usage': 25 if financial.get('bank_balance', 0) > 0 else 0
        }
        
        total_potential = sum(factors.values())
        
        if total_potential >= 80:
            potential_level = 'عالي جداً'
            recommendations = ['استمر في استراتيجيتك الحالية', 'فكر في مشاريع كبيرة']
        elif total_potential >= 60:
            potential_level = 'عالي'
            recommendations = ['نوع استثماراتك أكثر', 'زد من نشاطك اليومي']
        elif total_potential >= 40:
            potential_level = 'متوسط'
            recommendations = ['ركز على زيادة ثروتك', 'ابني قاعدة صلبة']
        else:
            potential_level = 'محدود'
            recommendations = ['ابدأ بالأساسيات', 'احصل على راتبك يومياً']
        
        return {
            'level': potential_level,
            'score': round(total_potential, 2),
            'factors': factors,
            'recommendations': recommendations
        }
    
    async def get_personalized_recommendations(self, user_data: Dict[str, Any]) -> List[str]:
        """الحصول على توصيات مخصصة"""
        profile = await self.analyze_user_economic_profile(user_data)
        
        recommendations = []
        
        # توصيات حسب مستوى الخبرة
        experience_recs = self.economic_strategies[profile['experience_level']]['recommendations']
        recommendations.extend(random.sample(experience_recs, min(2, len(experience_recs))))
        
        # توصيات حسب نقاط الضعف
        if profile['weaknesses']:
            weakness_based_recs = self._get_weakness_based_recommendations(profile['weaknesses'])
            recommendations.extend(weakness_based_recs[:2])
        
        # توصيات حسب الوقت
        current_time = datetime.now().hour
        if 6 <= current_time < 12:
            time_period = 'morning'
        elif 12 <= current_time < 18:
            time_period = 'afternoon'
        else:
            time_period = 'evening'
        
        time_recs = self.time_based_advice[time_period]
        recommendations.append(random.choice(time_recs))
        
        # توصيات المخاطرة
        recommendations.append(profile['risk_profile']['advice'])
        
        return list(set(recommendations))  # إزالة التكرار
    
    def _get_weakness_based_recommendations(self, weaknesses: List[str]) -> List[str]:
        """توصيات مبنية على نقاط الضعف"""
        weakness_solutions = {
            'أموال كثيرة خارج البنك': 'انقل أموالك للبنك لحمايتها من السرقة',
            'لا تستثمر في العقارات': 'ابدأ بشراء عقار صغير للاستثمار',
            'ثروة محدودة': 'احصل على راتبك اليومي وجرب الألعاب',
            'لا تستخدم المزرعة': 'ازرع بعض المحاصيل لدخل إضافي',
            'بدون قلعة': 'ابني قلعة لحماية ثروتك والدفاع'
        }
        
        solutions = []
        for weakness in weaknesses:
            for key, solution in weakness_solutions.items():
                if key in weakness:
                    solutions.append(solution)
                    break
        
        return solutions
    
    async def generate_economic_insights(self, user_data: Dict[str, Any], chat_analytics: Dict[str, Any]) -> str:
        """توليد رؤى اقتصادية شخصية"""
        profile = await self.analyze_user_economic_profile(user_data)
        recommendations = await self.get_personalized_recommendations(user_data)
        
        # مقارنة مع المجموعة
        group_avg_wealth = chat_analytics.get('economic_stats', {}).get('average_wealth', 0)
        user_wealth = profile['total_wealth']
        
        if user_wealth > group_avg_wealth * 1.5:
            wealth_comparison = "أداء ممتاز! ثروتك أعلى من متوسط المجموعة بكثير 🏆"
        elif user_wealth > group_avg_wealth:
            wealth_comparison = "أداء جيد! ثروتك أعلى من متوسط المجموعة 📈"
        elif user_wealth > group_avg_wealth * 0.8:
            wealth_comparison = "أداء متوسط، قريب من متوسط المجموعة ⚖️"
        else:
            wealth_comparison = "هناك مجال للتحسن مقارنة بالمجموعة 💪"
        
        insight_report = f"""
📊 **تحليلك الاقتصادي الشخصي**

💰 **الوضع المالي:**
• إجمالي الثروة: {user_wealth:,}$
• مستوى الخبرة: {profile['experience_level']}
• نقاط التنويع: {profile['diversification_score']['score']}/100

📈 **توزيع الأصول:**
• نقد: {profile['wealth_distribution']['cash_ratio']}%
• بنك: {profile['wealth_distribution']['bank_ratio']}%
• استثمارات: {profile['wealth_distribution']['investment_ratio']}%

🎯 **ملف المخاطرة:** {profile['risk_profile']['category']}

🏆 **مقارنة مع المجموعة:**
{wealth_comparison}

✅ **نقاط القوة:**
{chr(10).join([f"• {s}" for s in profile['strengths'][:3]])}

⚠️ **للتطوير:**
{chr(10).join([f"• {w}" for w in profile['weaknesses'][:2]])}

🚀 **توصياتي الذكية:**
{chr(10).join([f"• {r}" for r in recommendations[:3]])}

🔮 **إمكانية النمو:** {profile['growth_potential']['level']} ({profile['growth_potential']['score']:.1f}/100)
"""
        
        return insight_report.strip()
    
    async def suggest_investment_strategy(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """اقتراح استراتيجية استثمار مخصصة"""
        profile = await self.analyze_user_economic_profile(user_data)
        total_wealth = profile['total_wealth']
        risk_category = profile['risk_profile']['category']
        
        strategy = {
            'name': '',
            'cash_allocation': 0,
            'bank_allocation': 0,
            'real_estate_allocation': 0,
            'stocks_allocation': 0,
            'farming_allocation': 0,
            'castle_investment': False,
            'timeline': '',
            'expected_return': ''
        }
        
        if risk_category == 'محافظ جداً':
            strategy.update({
                'name': 'الاستراتيجية المحافظة',
                'cash_allocation': 20,
                'bank_allocation': 50,
                'real_estate_allocation': 20,
                'stocks_allocation': 5,
                'farming_allocation': 5,
                'castle_investment': total_wealth > 50000,
                'timeline': 'طويل المدى (6+ أشهر)',
                'expected_return': '8-12% سنوياً'
            })
        elif risk_category == 'محافظ':
            strategy.update({
                'name': 'الاستراتيجية المتوازنة',
                'cash_allocation': 15,
                'bank_allocation': 40,
                'real_estate_allocation': 25,
                'stocks_allocation': 15,
                'farming_allocation': 5,
                'castle_investment': total_wealth > 30000,
                'timeline': 'متوسط المدى (3-6 أشهر)',
                'expected_return': '12-18% سنوياً'
            })
        elif risk_category == 'متوازن':
            strategy.update({
                'name': 'استراتيجية النمو',
                'cash_allocation': 10,
                'bank_allocation': 30,
                'real_estate_allocation': 30,
                'stocks_allocation': 20,
                'farming_allocation': 10,
                'castle_investment': total_wealth > 20000,
                'timeline': 'متوسط المدى (2-4 أشهر)',
                'expected_return': '18-25% سنوياً'
            })
        else:  # مخاطر عالية
            strategy.update({
                'name': 'استراتيجية المخاطر العالية',
                'cash_allocation': 5,
                'bank_allocation': 25,
                'real_estate_allocation': 25,
                'stocks_allocation': 35,
                'farming_allocation': 10,
                'castle_investment': total_wealth > 15000,
                'timeline': 'قصير المدى (1-3 أشهر)',
                'expected_return': '25-40% سنوياً (مخاطر عالية)'
            })
        
        return strategy


# إنشاء نظام الاقتصاد الذكي
intelligent_economics = IntelligentEconomicsSystem()
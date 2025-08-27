"""
نظام الألعاب الذكية التفاعلية - Intelligent Interactive Games
أنظمة ألعاب ذكية تتكيف مع مستوى اللاعب وتوفر تحديات مخصصة
"""

import logging
import asyncio
import random
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta

class IntelligentGamesSystem:
    """نظام الألعاب الذكية والتفاعلية"""
    
    def __init__(self):
        # قاعدة الألعاب الذكية
        self.smart_games = {
            'adaptive_quiz': {
                'name': 'الكويز التكيفي',
                'description': 'أسئلة تتكيف مع مستوى ذكائك',
                'min_level': 1,
                'xp_reward': lambda level: min(50 + (level * 10), 200),
                'difficulty_scaling': True
            },
            'economic_challenge': {
                'name': 'تحدي الاقتصاد',
                'description': 'تحديات اقتصادية مبنية على وضعك المالي',
                'min_level': 5,
                'xp_reward': lambda level: min(75 + (level * 15), 300),
                'difficulty_scaling': True
            },
            'story_adventure': {
                'name': 'المغامرة التفاعلية',
                'description': 'قصة تتغير حسب قراراتك',
                'min_level': 10,
                'xp_reward': lambda level: min(100 + (level * 20), 400),
                'difficulty_scaling': False
            },
            'ai_battle': {
                'name': 'معركة الأذكياء',
                'description': 'تحدي مع يوكي في معركة ذكاء',
                'min_level': 15,
                'xp_reward': lambda level: min(150 + (level * 25), 500),
                'difficulty_scaling': True
            }
        }
        
        # بنك الأسئلة التكيفي
        self.adaptive_questions = {
            'beginner': {
                'math': [
                    {'q': 'كم يساوي 5 + 3؟', 'a': '8', 'options': ['7', '8', '9', '10']},
                    {'q': 'كم يساوي 12 - 4؟', 'a': '8', 'options': ['6', '7', '8', '9']},
                    {'q': 'كم يساوي 6 × 2؟', 'a': '12', 'options': ['10', '11', '12', '13']}
                ],
                'general': [
                    {'q': 'ما هي عاصمة السعودية؟', 'a': 'الرياض', 'options': ['جدة', 'الرياض', 'الدمام', 'مكة']},
                    {'q': 'كم عدد أيام الأسبوع؟', 'a': '7', 'options': ['5', '6', '7', '8']},
                    {'q': 'في أي قارة تقع مصر؟', 'a': 'أفريقيا', 'options': ['آسيا', 'أفريقيا', 'أوروبا', 'أمريكا']}
                ],
                'gaming': [
                    {'q': 'ما هو أول شيء يجب فعله في البوت؟', 'a': 'فتح حساب بنكي', 'options': ['شراء عقار', 'فتح حساب بنكي', 'اللعب', 'بناء قلعة']},
                    {'q': 'أي بنك يعطي أعلى فوائد؟', 'a': 'الاستثمار', 'options': ['الأهلي', 'الراجحي', 'الاستثمار', 'سامبا']}
                ]
            },
            'intermediate': {
                'math': [
                    {'q': 'كم يساوي 15 × 7؟', 'a': '105', 'options': ['103', '104', '105', '106']},
                    {'q': 'كم يساوي 144 ÷ 12؟', 'a': '12', 'options': ['10', '11', '12', '13']},
                    {'q': 'ما هو مربع العدد 9؟', 'a': '81', 'options': ['79', '80', '81', '82']}
                ],
                'general': [
                    {'q': 'من هو مخترع المصباح الكهربائي؟', 'a': 'إديسون', 'options': ['نيوتن', 'إديسون', 'أينشتاين', 'تسلا']},
                    {'q': 'ما هي أكبر محيطات العالم؟', 'a': 'الهادي', 'options': ['الأطلسي', 'الهندي', 'الهادي', 'المتجمد']},
                    {'q': 'في أي عام وصل الإنسان للقمر؟', 'a': '1969', 'options': ['1967', '1968', '1969', '1970']}
                ],
                'gaming': [
                    {'q': 'ما هي أفضل استراتيجية للاستثمار؟', 'a': 'التنويع', 'options': ['التركيز', 'التنويع', 'المخاطرة', 'الحذر']},
                    {'q': 'متى يجب حصاد المحاصيل؟', 'a': 'عند النضج', 'options': ['يومياً', 'عند النضج', 'أسبوعياً', 'شهرياً']}
                ]
            },
            'advanced': {
                'math': [
                    {'q': 'كم يساوي 2^8؟', 'a': '256', 'options': ['254', '255', '256', '257']},
                    {'q': 'ما هو جذر العدد 169؟', 'a': '13', 'options': ['11', '12', '13', '14']},
                    {'q': 'كم يساوي log₁₀(1000)؟', 'a': '3', 'options': ['2', '3', '4', '5']}
                ],
                'general': [
                    {'q': 'ما هي عاصمة أستراليا؟', 'a': 'كانبرا', 'options': ['سيدني', 'ملبورن', 'كانبرا', 'بيرث']},
                    {'q': 'من كتب رواية "الحرب والسلام"؟', 'a': 'تولستوي', 'options': ['دوستويفسكي', 'تولستوي', 'تشيخوف', 'غوغول']},
                    {'q': 'ما هو أصغر كوكب في النظام الشمسي؟', 'a': 'عطارد', 'options': ['الزهرة', 'عطارد', 'المريخ', 'بلوتو']}
                ],
                'gaming': [
                    {'q': 'ما هي أفضل نسبة للتوزيع الاستثماري؟', 'a': '40% بنك، 30% عقار، 30% أسهم', 'options': ['كلها بنك', '50% نقد، 50% بنك', '40% بنك، 30% عقار، 30% أسهم', 'كلها أسهم']},
                    {'q': 'متى يجب الاستثمار في القلاع؟', 'a': 'عند تجاوز 50000$', 'options': ['من البداية', 'عند 10000$', 'عند تجاوز 50000$', 'لا حاجة لها']}
                ]
            }
        }
        
        # تحديات اقتصادية ذكية
        self.economic_challenges = {
            'budget_master': {
                'title': 'سيد الميزانية',
                'description': 'خطط ميزانيتك بذكاء',
                'scenarios': [
                    {
                        'situation': 'لديك 10000$ وتريد مضاعفة أموالك في شهر',
                        'options': [
                            'استثمار كل المبلغ في الأسهم',
                            'توزيع المبلغ: 40% بنك، 30% عقار، 30% أسهم',
                            'الاحتفاظ بالمال نقداً',
                            'استثمار كل شيء في العقارات'
                        ],
                        'correct': 1,
                        'explanation': 'التنويع يقلل المخاطر ويضمن نمو مستقر'
                    }
                ]
            },
            'investment_genius': {
                'title': 'عبقري الاستثمار',
                'description': 'اتخذ القرارات الاستثمارية الصحيحة',
                'scenarios': [
                    {
                        'situation': 'أسعار الأسهم منخفضة والسوق متقلب',
                        'options': [
                            'شراء أسهم بكميات كبيرة',
                            'انتظار استقرار السوق',
                            'شراء تدريجي بكميات صغيرة',
                            'تجنب الأسهم تماماً'
                        ],
                        'correct': 2,
                        'explanation': 'الشراء التدريجي يقلل من مخاطر التذبذب'
                    }
                ]
            }
        }
        
        # قصص تفاعلية
        self.interactive_stories = {
            'merchant_journey': {
                'title': 'رحلة التاجر',
                'start_chapter': 'beginning',
                'chapters': {
                    'beginning': {
                        'text': 'أنت تاجر شاب بدأت للتو. لديك 5000$ ومتجر صغير. رجل يعرض عليك صفقة...',
                        'choices': [
                            {'text': 'اقبل الصفقة فوراً', 'next': 'risk_taken'},
                            {'text': 'ادرس الصفقة أولاً', 'next': 'careful_study'},
                            {'text': 'ارفض الصفقة', 'next': 'safe_path'}
                        ]
                    },
                    'risk_taken': {
                        'text': 'قبلت الصفقة بسرعة. اتضح أنها احتيال! خسرت 2000$. ماذا تفعل؟',
                        'choices': [
                            {'text': 'أبحث عن فرص أخرى', 'next': 'recovery_attempt'},
                            {'text': 'أعيد بناء أعمالي ببطء', 'next': 'slow_rebuild'},
                            {'text': 'أستسلم وأبحث عن وظيفة', 'next': 'give_up'}
                        ]
                    }
                }
            }
        }
    
    async def get_personalized_game_suggestions(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """اقتراح ألعاب مخصصة بناءً على ملف المستخدم"""
        suggestions = []
        
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        xp = gaming.get('xp', 0)
        
        financial = user_data.get('financial', {})
        wealth = financial.get('total_wealth', 0)
        
        # اقتراحات بناءً على المستوى
        for game_id, game_data in self.smart_games.items():
            if level >= game_data['min_level']:
                xp_reward = game_data['xp_reward'](level)
                
                suggestion = {
                    'game_id': game_id,
                    'name': game_data['name'],
                    'description': game_data['description'],
                    'estimated_xp': xp_reward,
                    'difficulty': self._calculate_game_difficulty(game_id, level, wealth),
                    'recommended_reason': self._get_recommendation_reason(game_id, user_data)
                }
                suggestions.append(suggestion)
        
        # ترتيب حسب الملاءمة
        suggestions.sort(key=lambda x: x['difficulty']['match_score'], reverse=True)
        
        return suggestions[:4]  # أفضل 4 اقتراحات
    
    def _calculate_game_difficulty(self, game_id: str, level: int, wealth: int) -> Dict[str, Any]:
        """حساب صعوبة اللعبة والملاءمة"""
        base_difficulty = {
            'adaptive_quiz': level * 0.1,
            'economic_challenge': (wealth / 10000) * 0.2,
            'story_adventure': level * 0.05,
            'ai_battle': level * 0.15
        }
        
        difficulty_score = base_difficulty.get(game_id, 0.1)
        
        # تحويل لمقياس من 1 إلى 5
        difficulty_level = min(max(int(difficulty_score * 5), 1), 5)
        
        # حساب مدى الملاءمة (كلما قل الفرق، زادت الملاءمة)
        ideal_difficulty = 3  # المستوى المثالي
        match_score = 5 - abs(difficulty_level - ideal_difficulty)
        
        difficulty_names = {1: 'سهل جداً', 2: 'سهل', 3: 'متوسط', 4: 'صعب', 5: 'صعب جداً'}
        
        return {
            'level': difficulty_level,
            'name': difficulty_names[difficulty_level],
            'match_score': match_score
        }
    
    def _get_recommendation_reason(self, game_id: str, user_data: Dict[str, Any]) -> str:
        """الحصول على سبب التوصية"""
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        
        financial = user_data.get('financial', {})
        wealth = financial.get('total_wealth', 0)
        
        reasons = {
            'adaptive_quiz': [
                f'مناسب لمستواك ({level})',
                'يطور مهاراتك المعرفية',
                'مكافآت XP جيدة'
            ],
            'economic_challenge': [
                f'يناسب ثروتك ({wealth:,}$)',
                'يطور مهاراتك الاقتصادية',
                'يعلمك استراتيجيات جديدة'
            ],
            'story_adventure': [
                'تجربة ممتعة ومسلية',
                'تطور مهارات اتخاذ القرار',
                'قصص متغيرة حسب اختياراتك'
            ],
            'ai_battle': [
                'تحدي ذكي مع يوكي',
                'يطور التفكير الاستراتيجي',
                'مكافآت عالية للفائزين'
            ]
        }
        
        game_reasons = reasons.get(game_id, ['مناسب لك'])
        return random.choice(game_reasons)
    
    async def generate_adaptive_quiz(self, user_data: Dict[str, Any], category: str = 'general') -> Dict[str, Any]:
        """توليد كويز تكيفي بناءً على مستوى المستخدم"""
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        
        # تحديد مستوى الصعوبة
        if level <= 5:
            difficulty = 'beginner'
        elif level <= 15:
            difficulty = 'intermediate'
        else:
            difficulty = 'advanced'
        
        # اختيار أسئلة مناسبة
        questions_pool = self.adaptive_questions[difficulty].get(category, 
                                                               self.adaptive_questions[difficulty]['general'])
        
        # اختيار 3-5 أسئلة عشوائياً
        num_questions = min(random.randint(3, 5), len(questions_pool))
        selected_questions = random.sample(questions_pool, num_questions)
        
        quiz_data = {
            'quiz_id': f"adaptive_{category}_{datetime.now().strftime('%H%M%S')}",
            'category': category,
            'difficulty': difficulty,
            'questions': selected_questions,
            'total_questions': len(selected_questions),
            'xp_reward': self.smart_games['adaptive_quiz']['xp_reward'](level),
            'time_limit': 30 * len(selected_questions),  # 30 ثانية لكل سؤال
            'created_at': datetime.now().isoformat()
        }
        
        return quiz_data
    
    async def generate_economic_challenge(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """توليد تحدي اقتصادي مخصص"""
        financial = user_data.get('financial', {})
        wealth = financial.get('total_wealth', 0)
        
        # اختيار التحدي المناسب
        if wealth < 50000:
            challenge_type = 'budget_master'
        else:
            challenge_type = 'investment_genius'
        
        challenge_data = self.economic_challenges[challenge_type]
        selected_scenario = random.choice(challenge_data['scenarios'])
        
        # تخصيص السيناريو بناءً على وضع المستخدم
        if '{wealth}' in selected_scenario['situation']:
            selected_scenario['situation'] = selected_scenario['situation'].replace('{wealth}', f'{wealth:,}$')
        
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        
        challenge = {
            'challenge_id': f"econ_{challenge_type}_{datetime.now().strftime('%H%M%S')}",
            'title': challenge_data['title'],
            'description': challenge_data['description'],
            'scenario': selected_scenario,
            'xp_reward': self.smart_games['economic_challenge']['xp_reward'](level),
            'wealth_bonus': max(100, wealth // 1000),  # مكافأة إضافية بناءً على الثروة
            'created_at': datetime.now().isoformat()
        }
        
        return challenge
    
    async def start_interactive_story(self, user_data: Dict[str, Any], story_id: str = 'merchant_journey') -> Dict[str, Any]:
        """بدء قصة تفاعلية"""
        if story_id not in self.interactive_stories:
            story_id = 'merchant_journey'  # القصة الافتراضية
        
        story_data = self.interactive_stories[story_id]
        start_chapter = story_data['start_chapter']
        first_chapter = story_data['chapters'][start_chapter]
        
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        
        story_session = {
            'story_id': story_id,
            'session_id': f"story_{story_id}_{datetime.now().strftime('%H%M%S')}",
            'title': story_data['title'],
            'current_chapter': start_chapter,
            'chapter_data': first_chapter,
            'choices_made': [],
            'xp_reward': self.smart_games['story_adventure']['xp_reward'](level),
            'started_at': datetime.now().isoformat()
        }
        
        return story_session
    
    async def continue_story(self, story_session: Dict[str, Any], choice_index: int) -> Dict[str, Any]:
        """متابعة القصة التفاعلية"""
        story_id = story_session['story_id']
        current_chapter = story_session['current_chapter']
        
        story_data = self.interactive_stories[story_id]
        chapter_data = story_data['chapters'][current_chapter]
        
        # تسجيل الاختيار
        if 0 <= choice_index < len(chapter_data['choices']):
            choice = chapter_data['choices'][choice_index]
            story_session['choices_made'].append({
                'chapter': current_chapter,
                'choice': choice['text'],
                'timestamp': datetime.now().isoformat()
            })
            
            # الانتقال للفصل التالي
            next_chapter = choice['next']
            if next_chapter in story_data['chapters']:
                story_session['current_chapter'] = next_chapter
                story_session['chapter_data'] = story_data['chapters'][next_chapter]
                story_session['status'] = 'continuing'
            else:
                # نهاية القصة
                story_session['status'] = 'completed'
                story_session['completed_at'] = datetime.now().isoformat()
        else:
            story_session['status'] = 'invalid_choice'
        
        return story_session
    
    async def generate_ai_battle_challenge(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """توليد تحدي معركة ذكية مع يوكي"""
        gaming = user_data.get('gaming', {})
        level = gaming.get('level', 1)
        
        # أنواع التحديات المختلفة
        battle_types = {
            'logic_puzzle': 'ألغاز منطقية',
            'quick_math': 'رياضيات سريعة', 
            'word_game': 'لعبة الكلمات',
            'strategy_game': 'لعبة استراتيجية'
        }
        
        selected_type = random.choice(list(battle_types.keys()))
        
        # توليد التحدي حسب النوع
        if selected_type == 'logic_puzzle':
            challenge = self._generate_logic_puzzle(level)
        elif selected_type == 'quick_math':
            challenge = self._generate_quick_math(level)
        elif selected_type == 'word_game':
            challenge = self._generate_word_game(level)
        else:
            challenge = self._generate_strategy_game(level)
        
        battle_data = {
            'battle_id': f"ai_battle_{selected_type}_{datetime.now().strftime('%H%M%S')}",
            'type': selected_type,
            'type_name': battle_types[selected_type],
            'challenge': challenge,
            'xp_reward': self.smart_games['ai_battle']['xp_reward'](level),
            'difficulty_level': min(max(level // 3, 1), 5),
            'time_limit': 60 + (level * 5),  # وقت أكثر للمستويات العليا
            'ai_difficulty': 'متكيف مع مستواك',
            'created_at': datetime.now().isoformat()
        }
        
        return battle_data
    
    def _generate_logic_puzzle(self, level: int) -> Dict[str, Any]:
        """توليد لغز منطقي"""
        puzzles = [
            {
                'question': 'إذا كان A = 1، B = 2، C = 3... فكم يساوي LOVE؟',
                'answer': '54',
                'hint': 'L=12, O=15, V=22, E=5'
            },
            {
                'question': 'ما هو الرقم التالي في السلسلة: 2, 6, 12, 20, 30, ؟',
                'answer': '42',
                'hint': 'الفرق بين الأرقام يزداد بـ2 كل مرة'
            }
        ]
        
        return random.choice(puzzles)
    
    def _generate_quick_math(self, level: int) -> Dict[str, Any]:
        """توليد تحدي رياضيات سريع"""
        if level <= 5:
            a, b = random.randint(10, 50), random.randint(10, 50)
            operation = random.choice(['+', '-'])
            if operation == '+':
                answer = a + b
                question = f"{a} + {b}"
            else:
                answer = a - b
                question = f"{a} - {b}"
        else:
            a, b = random.randint(10, 20), random.randint(5, 15)
            operation = random.choice(['×', '÷'])
            if operation == '×':
                answer = a * b
                question = f"{a} × {b}"
            else:
                a = a * b  # للتأكد من القسمة الصحيحة
                answer = a // b
                question = f"{a} ÷ {b}"
        
        return {
            'question': f"احسب: {question}",
            'answer': str(answer),
            'hint': f'فكر في {operation} بعناية'
        }
    
    def _generate_word_game(self, level: int) -> Dict[str, Any]:
        """توليد لعبة كلمات"""
        words = ['تطوير', 'ذكاء', 'استثمار', 'تحدي', 'نجاح', 'إبداع']
        selected_word = random.choice(words)
        
        # خلط أحرف الكلمة
        shuffled = list(selected_word)
        random.shuffle(shuffled)
        shuffled_word = ''.join(shuffled)
        
        return {
            'question': f'رتب الأحرف لتكوين كلمة مفيدة: {shuffled_word}',
            'answer': selected_word,
            'hint': f'الكلمة تتكون من {len(selected_word)} أحرف'
        }
    
    def _generate_strategy_game(self, level: int) -> Dict[str, Any]:
        """توليد لعبة استراتيجية"""
        scenarios = [
            {
                'question': 'لديك 1000$ وتريد أفضل عائد في أسبوع. ما هي الاستراتيجية الأفضل؟',
                'options': [
                    'استثمار كل المبلغ في الأسهم',
                    'توزيع المبلغ بين البنك والأسهم',
                    'شراء عقار صغير',
                    'الاحتفاظ بالنقد'
                ],
                'answer': '1',
                'explanation': 'التوزيع يقلل المخاطر ويضمن عائد معقول'
            }
        ]
        
        return random.choice(scenarios)


# إنشاء نظام الألعاب الذكية
intelligent_games = IntelligentGamesSystem()
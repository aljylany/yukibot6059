"""
🧠 عمليات قاعدة البيانات لنظام تحليل المستخدمين
"""

import aiosqlite
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from config.database import DATABASE_URL


class UserAnalysisOperations:
    """عمليات قاعدة البيانات لنظام تحليل المستخدمين"""
    
    @staticmethod
    async def get_user_analysis(user_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على تحليل المستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    "SELECT * FROM user_analysis WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                if result:
                    data = dict(result)
                    # تحويل JSON strings إلى dict
                    if data.get('activity_pattern'):
                        data['activity_pattern'] = json.loads(data['activity_pattern'])
                    if data.get('mood_history'):
                        data['mood_history'] = json.loads(data['mood_history'])
                    return data
                return None
                
        except Exception as e:
            logging.error(f"خطأ في الحصول على تحليل المستخدم {user_id}: {e}")
            return None
    
    @staticmethod
    async def create_user_analysis(user_id: int) -> bool:
        """إنشاء ملف تحليل جديد للمستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # إنشاء تحليل أساسي للمستخدم
                await db.execute("""
                    INSERT OR IGNORE INTO user_analysis (
                        user_id, activity_pattern, mood_history,
                        first_analysis, last_updated
                    ) VALUES (?, ?, ?, ?, ?)
                """, (
                    user_id,
                    json.dumps({"morning": 0.0, "afternoon": 0.0, "evening": 0.0, "night": 0.0}),
                    json.dumps([]),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في إنشاء تحليل المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def update_user_personality(user_id: int, personality_updates: Dict[str, float]) -> bool:
        """تحديث نقاط الشخصية للمستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # التأكد من وجود التحليل
                await UserAnalysisOperations.create_user_analysis(user_id)
                
                # تحديث نقاط الشخصية
                set_clauses = []
                values = []
                
                for trait, score in personality_updates.items():
                    if trait in ['extravert_score', 'risk_taker_score', 'leader_score', 'patient_score', 'competitive_score']:
                        set_clauses.append(f"{trait} = ?")
                        values.append(max(0.0, min(1.0, score)))  # تحديد النطاق بين 0-1
                
                if set_clauses:
                    values.append(datetime.now().isoformat())
                    values.append(user_id)
                    
                    query = f"""
                        UPDATE user_analysis 
                        SET {', '.join(set_clauses)}, last_updated = ?
                        WHERE user_id = ?
                    """
                    await db.execute(query, values)
                    await db.commit()
                    return True
                return False
                    
        except Exception as e:
            logging.error(f"خطأ في تحديث شخصية المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def update_user_interests(user_id: int, interest_updates: Dict[str, float]) -> bool:
        """تحديث اهتمامات المستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # التأكد من وجود التحليل
                await UserAnalysisOperations.create_user_analysis(user_id)
                
                # تحديث نقاط الاهتمامات
                set_clauses = []
                values = []
                
                for interest, score in interest_updates.items():
                    if interest in ['games_interest', 'money_interest', 'social_interest', 'entertainment_interest']:
                        set_clauses.append(f"{interest} = ?")
                        values.append(max(0.0, min(1.0, score)))  # تحديد النطاق بين 0-1
                
                if set_clauses:
                    values.append(datetime.now().isoformat())
                    values.append(user_id)
                    
                    query = f"""
                        UPDATE user_analysis 
                        SET {', '.join(set_clauses)}, last_updated = ?
                        WHERE user_id = ?
                    """
                    await db.execute(query, values)
                    await db.commit()
                    return True
                return False
                    
        except Exception as e:
            logging.error(f"خطأ في تحديث اهتمامات المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def update_user_mood(user_id: int, mood: str, sentiment_score: float = 0.0) -> bool:
        """تحديث الحالة المزاجية للمستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                # التأكد من وجود التحليل
                await UserAnalysisOperations.create_user_analysis(user_id)
                
                # الحصول على تاريخ المزاج الحالي
                cursor = await db.execute(
                    "SELECT mood_history FROM user_analysis WHERE user_id = ?",
                    (user_id,)
                )
                result = await cursor.fetchone()
                
                mood_history = []
                if result and result[0]:
                    mood_history = json.loads(result[0])
                
                # إضافة المزاج الجديد
                mood_entry = {
                    "mood": mood,
                    "sentiment_score": sentiment_score,
                    "timestamp": datetime.now().isoformat()
                }
                mood_history.append(mood_entry)
                
                # الاحتفاظ بآخر 20 حالة مزاجية فقط
                if len(mood_history) > 20:
                    mood_history = mood_history[-20:]
                
                # تحديث المزاج في قاعدة البيانات
                await db.execute("""
                    UPDATE user_analysis 
                    SET current_mood = ?, mood_history = ?, last_updated = ?
                    WHERE user_id = ?
                """, (mood, json.dumps(mood_history), datetime.now().isoformat(), user_id))
                
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في تحديث مزاج المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def add_user_memory(user_id: int, memory_type: str, memory_data: Dict[str, Any], 
                            importance_score: float = 0.5, emotional_impact: float = 0.0,
                            context_users: Optional[List[int]] = None, context_location: Optional[str] = None) -> bool:
        """إضافة ذكرى جديدة للمستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                memory_summary = UserAnalysisOperations._generate_memory_summary(memory_type, memory_data)
                
                await db.execute("""
                    INSERT INTO user_memories (
                        user_id, memory_type, memory_data, memory_summary,
                        importance_score, emotional_impact, context_users,
                        context_location, memory_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, memory_type, json.dumps(memory_data), memory_summary,
                    importance_score, emotional_impact, 
                    json.dumps(context_users) if context_users else None,
                    context_location, datetime.now().isoformat()
                ))
                
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في إضافة ذكرى للمستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def get_user_memories(user_id: int, memory_type: Optional[str] = None, 
                              limit: int = 10, min_importance: float = 0.0) -> List[Dict[str, Any]]:
        """الحصول على ذكريات المستخدم"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                db.row_factory = aiosqlite.Row
                
                query = """
                    SELECT * FROM user_memories 
                    WHERE user_id = ? AND importance_score >= ?
                """
                params = [user_id, min_importance]
                
                if memory_type:
                    query += " AND memory_type = ?"
                    params.append(memory_type)
                
                query += " ORDER BY importance_score DESC, memory_date DESC LIMIT ?"
                params.append(limit)
                
                cursor = await db.execute(query, params)
                results = await cursor.fetchall()
                
                memories = []
                for row in results:
                    memory = dict(row)
                    if memory.get('memory_data'):
                        memory['memory_data'] = json.loads(memory['memory_data'])
                    if memory.get('context_users'):
                        memory['context_users'] = json.loads(memory['context_users'])
                    memories.append(memory)
                
                return memories
                
        except Exception as e:
            logging.error(f"خطأ في الحصول على ذكريات المستخدم {user_id}: {e}")
            return []
    
    @staticmethod
    async def update_relationship(user1_id: int, user2_id: int, interaction_type: str = 'neutral') -> bool:
        """تحديث العلاقة بين مستخدمين"""
        try:
            # ترتيب المستخدمين لضمان الثبات
            if user1_id > user2_id:
                user1_id, user2_id = user2_id, user1_id
            
            async with aiosqlite.connect(DATABASE_URL) as db:
                # البحث عن العلاقة الموجودة
                cursor = await db.execute("""
                    SELECT * FROM user_relationships 
                    WHERE user1_id = ? AND user2_id = ?
                """, (user1_id, user2_id))
                
                existing = await cursor.fetchone()
                
                if existing:
                    # تحديث العلاقة الموجودة
                    new_strength = min(1.0, existing[3] + 0.1)  # زيادة قوة العلاقة
                    
                    await db.execute("""
                        UPDATE user_relationships 
                        SET relationship_strength = ?, total_interactions = total_interactions + 1,
                            last_interaction = ?
                        WHERE user1_id = ? AND user2_id = ?
                    """, (new_strength, datetime.now().isoformat(), user1_id, user2_id))
                else:
                    # إنشاء علاقة جديدة
                    await db.execute("""
                        INSERT INTO user_relationships (
                            user1_id, user2_id, relationship_strength,
                            total_interactions, first_interaction, last_interaction
                        ) VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        user1_id, user2_id, 0.1, 1,
                        datetime.now().isoformat(), datetime.now().isoformat()
                    ))
                
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في تحديث العلاقة بين {user1_id} و {user2_id}: {e}")
            return False
    
    @staticmethod
    async def record_activity(user_id: int, activity_type: str, activity_details: Optional[Dict[str, Any]] = None,
                            chat_id: Optional[int] = None, mood_detected: Optional[str] = None, 
                            sentiment_score: Optional[float] = None) -> bool:
        """تسجيل نشاط المستخدم للتحليل"""
        try:
            now = datetime.now()
            hour_of_day = now.hour
            day_of_week = now.weekday()
            
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute("""
                    INSERT INTO analysis_statistics (
                        user_id, chat_id, activity_type, activity_details,
                        mood_detected, sentiment_score, hour_of_day, day_of_week,
                        timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    user_id, chat_id, activity_type,
                    json.dumps(activity_details) if activity_details else None,
                    mood_detected, sentiment_score, hour_of_day, day_of_week,
                    now.isoformat()
                ))
                
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في تسجيل نشاط المستخدم {user_id}: {e}")
            return False
    
    @staticmethod
    async def is_analysis_enabled(chat_id: int) -> bool:
        """التحقق من تفعيل التحليل في المجموعة"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                cursor = await db.execute(
                    "SELECT analysis_enabled FROM group_analysis_settings WHERE chat_id = ?",
                    (chat_id,)
                )
                result = await cursor.fetchone()
                
                # إذا لم توجد إعدادات، التحليل مفعل افتراضياً
                return result[0] if result else True
                
        except Exception as e:
            logging.error(f"خطأ في التحقق من تفعيل التحليل للمجموعة {chat_id}: {e}")
            return True  # افتراضياً مفعل
    
    @staticmethod
    async def set_group_analysis(chat_id: int, enabled: bool, modified_by: int, 
                               reason: Optional[str] = None) -> bool:
        """تفعيل/إيقاف التحليل في المجموعة"""
        try:
            async with aiosqlite.connect(DATABASE_URL) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO group_analysis_settings (
                        chat_id, analysis_enabled, last_modified_by,
                        last_modified_at, disable_reason, notification_sent
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    chat_id, enabled, modified_by,
                    datetime.now().isoformat(), reason, False
                ))
                
                await db.commit()
                return True
                
        except Exception as e:
            logging.error(f"خطأ في تعديل إعدادات التحليل للمجموعة {chat_id}: {e}")
            return False
    
    @staticmethod
    def _generate_memory_summary(memory_type: str, memory_data: Dict[str, Any]) -> str:
        """توليد ملخص نصي للذكرى"""
        try:
            if memory_type == 'game_win':
                game = memory_data.get('game', 'لعبة')
                return f"فوز في لعبة {game}"
            elif memory_type == 'game_loss':
                game = memory_data.get('game', 'لعبة')
                return f"خسارة في لعبة {game}"
            elif memory_type == 'investment':
                amount = memory_data.get('amount', 0)
                return f"استثمار بقيمة {amount}"
            elif memory_type == 'achievement':
                achievement = memory_data.get('achievement', 'إنجاز')
                return f"تحقيق {achievement}"
            else:
                return f"حدث من نوع {memory_type}"
                
        except Exception:
            return f"ذكرى من نوع {memory_type}"


# دوال مساعدة سريعة
async def quick_personality_update(user_id: int, trait: str, change: float):
    """تحديث سريع لصفة شخصية معينة"""
    current = await UserAnalysisOperations.get_user_analysis(user_id)
    if current:
        current_score = current.get(f"{trait}_score", 0.5)
        new_score = max(0.0, min(1.0, current_score + change))
        await UserAnalysisOperations.update_user_personality(user_id, {f"{trait}_score": new_score})

async def quick_interest_update(user_id: int, interest: str, change: float):
    """تحديث سريع لاهتمام معين"""
    current = await UserAnalysisOperations.get_user_analysis(user_id)
    if current:
        current_score = current.get(f"{interest}_interest", 0.0)
        new_score = max(0.0, min(1.0, current_score + change))
        await UserAnalysisOperations.update_user_interests(user_id, {f"{interest}_interest": new_score})
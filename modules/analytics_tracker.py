"""
وحدة تتبع الأنشطة والتحليلات في الوقت الفعلي
Real-time Analytics Tracking Module
"""

import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import json

from config.database import execute_query


class AnalyticsTracker:
    """متتبع التحليلات في الوقت الفعلي"""
    
    @staticmethod
    async def track_user_activity(user_id: int, chat_id: int, activity_type: str, data: Dict[str, Any] = None):
        """تتبع نشاط المستخدم"""
        try:
            activity_data = json.dumps(data) if data else None
            date_only = datetime.now().date().isoformat()
            
            await execute_query("""
                INSERT INTO activity_logs (user_id, chat_id, activity_type, activity_data, date_only)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, chat_id, activity_type, activity_data, date_only))
            
        except Exception as e:
            logging.error(f"خطأ في تتبع النشاط: {e}")

    @staticmethod
    async def update_daily_stats(chat_id: int, stat_type: str, increment: int = 1):
        """تحديث الإحصائيات اليومية"""
        try:
            today = datetime.now().date().isoformat()
            
            # إنشاء أو تحديث الإحصائيات اليومية
            await execute_query(f"""
                INSERT INTO daily_stats (chat_id, date, {stat_type})
                VALUES (?, ?, ?)
                ON CONFLICT(chat_id, date) DO UPDATE SET
                {stat_type} = {stat_type} + ?
            """, (chat_id, today, increment, increment))
            
        except Exception as e:
            logging.error(f"خطأ في تحديث الإحصائيات اليومية: {e}")

    @staticmethod
    async def track_performance_metric(chat_id: int, metric_name: str, value: float):
        """تتبع مقياس الأداء"""
        try:
            date_only = datetime.now().date().isoformat()
            
            await execute_query("""
                INSERT INTO performance_metrics (chat_id, metric_name, metric_value, date_only)
                VALUES (?, ?, ?, ?)
            """, (chat_id, metric_name, value, date_only))
            
        except Exception as e:
            logging.error(f"خطأ في تتبع مقياس الأداء: {e}")

    @staticmethod
    async def track_financial_activity(user_id: int, chat_id: int, activity_type: str, amount: float, details: Dict = None):
        """تتبع النشاط المالي"""
        try:
            # تتبع النشاط العام
            await AnalyticsTracker.track_user_activity(
                user_id, chat_id, f"financial_{activity_type}", 
                {"amount": amount, "details": details}
            )
            
            # تحديث الإحصائيات المالية اليومية
            await AnalyticsTracker.update_daily_stats(chat_id, "total_transactions", 1)
            await AnalyticsTracker.update_daily_stats(chat_id, "total_money_flow", int(amount))
            
        except Exception as e:
            logging.error(f"خطأ في تتبع النشاط المالي: {e}")

    @staticmethod
    async def track_moderation_action(moderator_id: int, chat_id: int, action_type: str, target_user_id: int, details: Dict = None):
        """تتبع إجراءات الإشراف"""
        try:
            # تتبع الإجراء
            await AnalyticsTracker.track_user_activity(
                moderator_id, chat_id, f"moderation_{action_type}",
                {"target_user": target_user_id, "details": details}
            )
            
            # تحديث إحصائيات الإشراف
            await AnalyticsTracker.update_daily_stats(chat_id, "moderation_actions", 1)
            
        except Exception as e:
            logging.error(f"خطأ في تتبع إجراء الإشراف: {e}")

    @staticmethod
    async def track_new_user(user_id: int, chat_id: int, user_data: Dict):
        """تتبع مستخدم جديد"""
        try:
            # تتبع التسجيل
            await AnalyticsTracker.track_user_activity(
                user_id, chat_id, "user_registration", user_data
            )
            
            # تحديث إحصائيات المستخدمين الجدد
            await AnalyticsTracker.update_daily_stats(chat_id, "new_users", 1)
            
        except Exception as e:
            logging.error(f"خطأ في تتبع المستخدم الجديد: {e}")

    @staticmethod
    async def track_message_activity(user_id: int, chat_id: int):
        """تتبع نشاط الرسائل"""
        try:
            # تحديث آخر نشاط للمستخدم
            await execute_query("""
                UPDATE users SET updated_at = CURRENT_TIMESTAMP 
                WHERE user_id = ? AND chat_id = ?
            """, (user_id, chat_id))
            
            # تحديث عدد الرسائل اليومية
            await AnalyticsTracker.update_daily_stats(chat_id, "messages_count", 1)
            
            # تتبع المستخدم النشط
            today = datetime.now().date().isoformat()
            
            # التحقق إذا كان المستخدم نشط اليوم
            active_today = await execute_query("""
                SELECT COUNT(*) FROM activity_logs 
                WHERE user_id = ? AND chat_id = ? AND date_only = ? AND activity_type = 'daily_active'
            """, (user_id, chat_id, today), fetch_one=True)
            
            if not active_today or active_today[0] == 0:
                await AnalyticsTracker.track_user_activity(user_id, chat_id, "daily_active")
                await AnalyticsTracker.update_daily_stats(chat_id, "active_users", 1)
            
        except Exception as e:
            logging.error(f"خطأ في تتبع نشاط الرسالة: {e}")


class DashboardMetrics:
    """مقاييس لوحة التحكم المتقدمة"""
    
    @staticmethod
    async def calculate_engagement_rate(chat_id: int, days: int = 7) -> float:
        """حساب معدل التفاعل"""
        try:
            # إجمالي الأعضاء
            total_members = await execute_query(
                "SELECT COUNT(*) FROM users WHERE chat_id = ?",
                (chat_id,), fetch_one=True
            )
            total_count = total_members[0] if total_members else 0
            
            if total_count == 0:
                return 0.0
            
            # الأعضاء النشطين في الفترة المحددة
            date_threshold = (datetime.now() - timedelta(days=days)).date().isoformat()
            active_members = await execute_query("""
                SELECT COUNT(DISTINCT user_id) FROM activity_logs 
                WHERE chat_id = ? AND date_only >= ?
            """, (chat_id, date_threshold), fetch_one=True)
            
            active_count = active_members[0] if active_members else 0
            return (active_count / total_count) * 100
            
        except Exception as e:
            logging.error(f"خطأ في حساب معدل التفاعل: {e}")
            return 0.0

    @staticmethod
    async def calculate_growth_trend(chat_id: int, days: int = 30) -> Dict[str, float]:
        """حساب اتجاه النمو"""
        try:
            # المستخدمين الجدد في الفترة الحالية
            current_period_start = (datetime.now() - timedelta(days=days)).date().isoformat()
            current_new_users = await execute_query("""
                SELECT COUNT(*) FROM users 
                WHERE chat_id = ? AND date(created_at) >= ?
            """, (chat_id, current_period_start), fetch_one=True)
            
            # المستخدمين الجدد في الفترة السابقة
            previous_period_start = (datetime.now() - timedelta(days=days*2)).date().isoformat()
            previous_period_end = current_period_start
            previous_new_users = await execute_query("""
                SELECT COUNT(*) FROM users 
                WHERE chat_id = ? AND date(created_at) >= ? AND date(created_at) < ?
            """, (chat_id, previous_period_start, previous_period_end), fetch_one=True)
            
            current_count = current_new_users[0] if current_new_users else 0
            previous_count = previous_new_users[0] if previous_new_users else 0
            
            # حساب معدل النمو
            if previous_count > 0:
                growth_rate = ((current_count - previous_count) / previous_count) * 100
            else:
                growth_rate = 100.0 if current_count > 0 else 0.0
            
            return {
                "current_period": current_count,
                "previous_period": previous_count,
                "growth_rate": growth_rate,
                "trend": "صاعد" if growth_rate > 0 else "هابط" if growth_rate < 0 else "ثابت"
            }
            
        except Exception as e:
            logging.error(f"خطأ في حساب اتجاه النمو: {e}")
            return {"current_period": 0, "previous_period": 0, "growth_rate": 0.0, "trend": "غير محدد"}

    @staticmethod
    async def get_top_activities(chat_id: int, limit: int = 10, days: int = 7) -> List[Dict]:
        """الحصول على أهم الأنشطة"""
        try:
            date_threshold = (datetime.now() - timedelta(days=days)).date().isoformat()
            
            activities = await execute_query("""
                SELECT activity_type, COUNT(*) as count
                FROM activity_logs 
                WHERE chat_id = ? AND date_only >= ?
                GROUP BY activity_type
                ORDER BY count DESC
                LIMIT ?
            """, (chat_id, date_threshold, limit), fetch_all=True)
            
            result = []
            for activity_type, count in activities:
                # ترجمة أنواع الأنشطة
                activity_names = {
                    "daily_active": "النشاط اليومي",
                    "user_registration": "التسجيل",
                    "financial_transaction": "المعاملات المالية",
                    "financial_deposit": "الإيداع",
                    "financial_withdrawal": "السحب",
                    "moderation_ban": "الحظر",
                    "moderation_mute": "الكتم",
                    "moderation_kick": "الطرد",
                    "moderation_warn": "التحذير"
                }
                
                result.append({
                    "activity": activity_names.get(activity_type, activity_type),
                    "count": count
                })
            
            return result
            
        except Exception as e:
            logging.error(f"خطأ في الحصول على أهم الأنشطة: {e}")
            return []

    @staticmethod
    async def calculate_health_score(chat_id: int) -> Dict[str, Any]:
        """حساب نقاط صحة المجموعة"""
        try:
            # عوامل صحة المجموعة
            scores = {}
            
            # معدل التفاعل (40% من النقاط)
            engagement_rate = await DashboardMetrics.calculate_engagement_rate(chat_id)
            scores['engagement'] = min(engagement_rate, 100) * 0.4
            
            # معدل النمو (30% من النقاط)
            growth_data = await DashboardMetrics.calculate_growth_trend(chat_id)
            growth_score = max(0, min(growth_data['growth_rate'] + 50, 100))  # تطبيع النتيجة
            scores['growth'] = growth_score * 0.3
            
            # النشاط المالي (20% من النقاط)
            today = datetime.now().date().isoformat()
            financial_activity = await execute_query("""
                SELECT COUNT(*) FROM activity_logs 
                WHERE chat_id = ? AND date_only = ? AND activity_type LIKE 'financial_%'
            """, (chat_id, today), fetch_one=True)
            
            financial_score = min((financial_activity[0] if financial_activity else 0) * 10, 100)
            scores['financial'] = financial_score * 0.2
            
            # جودة الإشراف (10% من النقاط)
            moderation_activity = await execute_query("""
                SELECT COUNT(*) FROM activity_logs 
                WHERE chat_id = ? AND date_only >= ? AND activity_type LIKE 'moderation_%'
            """, (chat_id, (datetime.now() - timedelta(days=7)).date().isoformat()), fetch_one=True)
            
            # إشراف معتدل يعني صحة جيدة
            mod_count = moderation_activity[0] if moderation_activity else 0
            moderation_score = 100 - min(mod_count * 5, 50)  # كلما قل الإشراف المطلوب، كانت الصحة أفضل
            scores['moderation'] = moderation_score * 0.1
            
            # النتيجة الإجمالية
            total_score = sum(scores.values())
            
            # تصنيف الصحة
            if total_score >= 80:
                health_grade = "ممتاز"
                health_color = "🟢"
            elif total_score >= 60:
                health_grade = "جيد"
                health_color = "🟡"
            elif total_score >= 40:
                health_grade = "متوسط"
                health_color = "🟠"
            else:
                health_grade = "ضعيف"
                health_color = "🔴"
            
            return {
                "total_score": round(total_score, 1),
                "grade": health_grade,
                "color": health_color,
                "breakdown": {
                    "engagement": round(scores['engagement'], 1),
                    "growth": round(scores['growth'], 1),
                    "financial": round(scores['financial'], 1),
                    "moderation": round(scores['moderation'], 1)
                }
            }
            
        except Exception as e:
            logging.error(f"خطأ في حساب نقاط الصحة: {e}")
            return {
                "total_score": 0.0,
                "grade": "غير محدد",
                "color": "⚪",
                "breakdown": {"engagement": 0, "growth": 0, "financial": 0, "moderation": 0}
            }


# دوال مساعدة للاستخدام السريع
async def track_command_usage(user_id: int, chat_id: int, command: str):
    """تتبع استخدام الأوامر"""
    await AnalyticsTracker.track_user_activity(
        user_id, chat_id, "command_usage", {"command": command}
    )

async def track_economy_action(user_id: int, chat_id: int, action: str, amount: float = 0):
    """تتبع إجراءات الاقتصاد"""
    await AnalyticsTracker.track_financial_activity(
        user_id, chat_id, action, amount
    )

async def track_admin_action(admin_id: int, chat_id: int, action: str, target_id: int = None):
    """تتبع إجراءات الإدارة"""
    await AnalyticsTracker.track_moderation_action(
        admin_id, chat_id, action, target_id or 0
    )
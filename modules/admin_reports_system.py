"""
نظام تقارير المشرفين المتقدم
Advanced Admin Reports System
"""

import logging
import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram import Bot

class AdminReportsSystem:
    """نظام تقارير المشرفين المتقدم"""
    
    def __init__(self):
        self.reports_db = 'comprehensive_filter.db'
        self._init_reports_database()
    
    def _init_reports_database(self):
        """تهيئة قاعدة بيانات التقارير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # جدول تقارير مفصلة للمشرفين
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS detailed_admin_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                admin_id INTEGER,
                violation_type TEXT NOT NULL,
                severity_level INTEGER NOT NULL,
                content_summary TEXT,
                action_taken TEXT,
                report_status TEXT DEFAULT 'pending',
                ai_confidence REAL,
                evidence_data TEXT,
                admin_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reviewed_at TIMESTAMP,
                resolved_at TIMESTAMP
            )
            ''')
            
            # جدول إحصائيات المجموعات
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS group_statistics (
                chat_id INTEGER PRIMARY KEY,
                total_violations INTEGER DEFAULT 0,
                total_warnings INTEGER DEFAULT 0,
                total_mutes INTEGER DEFAULT 0,
                total_bans INTEGER DEFAULT 0,
                last_violation TIMESTAMP,
                risk_level TEXT DEFAULT 'low',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # جدول اشتراكات التقارير
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS report_subscriptions (
                admin_id INTEGER,
                chat_id INTEGER,
                report_types TEXT,
                notification_enabled BOOLEAN DEFAULT TRUE,
                daily_summary BOOLEAN DEFAULT TRUE,
                instant_alerts BOOLEAN DEFAULT TRUE,
                PRIMARY KEY (admin_id, chat_id)
            )
            ''')
            
            conn.commit()
            conn.close()
            
            logging.info("✅ تم تهيئة نظام تقارير المشرفين")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة نظام التقارير: {e}")
    
    async def generate_violation_report(self, message: Message, violations: List[Dict], 
                                      action_taken: str, ai_data: Dict = None) -> int:
        """إنشاء تقرير مخالفة مفصل"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # تحضير بيانات الأدلة
            evidence_data = {
                'message_id': message.message_id,
                'timestamp': datetime.now().isoformat(),
                'user_info': {
                    'id': message.from_user.id,
                    'first_name': message.from_user.first_name,
                    'username': message.from_user.username,
                    'language_code': message.from_user.language_code
                },
                'chat_info': {
                    'id': message.chat.id,
                    'title': message.chat.title,
                    'type': message.chat.type
                },
                'violations_details': violations,
                'ai_analysis': ai_data or {}
            }
            
            # حساب متوسط الثقة من الذكاء الاصطناعي
            ai_confidence = 0.0
            if ai_data and 'confidence' in ai_data:
                ai_confidence = ai_data['confidence']
            elif violations:
                confidences = [v.get('details', {}).get('ai_confidence', 0) for v in violations]
                ai_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            
            # تحديد مستوى الخطورة الإجمالي
            max_severity = max([v['severity'] for v in violations]) if violations else 1
            
            # إدراج التقرير
            cursor.execute('''
            INSERT INTO detailed_admin_reports 
            (chat_id, user_id, violation_type, severity_level, content_summary, 
             action_taken, ai_confidence, evidence_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                message.chat.id,
                message.from_user.id,
                ', '.join([v['violation_type'] for v in violations]),
                max_severity,
                self._create_content_summary(message, violations),
                action_taken,
                ai_confidence,
                str(evidence_data)
            ))
            
            report_id = cursor.lastrowid
            
            # تحديث إحصائيات المجموعة
            await self._update_group_statistics(message.chat.id, action_taken)
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ تم إنشاء تقرير مخالفة رقم {report_id}")
            return report_id
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء تقرير المخالفة: {e}")
            return 0
    
    def _create_content_summary(self, message: Message, violations: List[Dict]) -> str:
        """إنشاء ملخص المحتوى"""
        summary_parts = []
        
        if message.text:
            summary_parts.append(f"نص: {message.text[:50]}...")
        if message.photo:
            summary_parts.append("صورة")
        if message.video:
            summary_parts.append("فيديو")
        if message.sticker:
            summary_parts.append(f"ملصق: {message.sticker.emoji or 'غير محدد'}")
        if message.document:
            summary_parts.append(f"ملف: {message.document.file_name or 'غير محدد'}")
        
        violation_types = [v['violation_type'] for v in violations]
        summary_parts.append(f"المخالفات: {', '.join(violation_types)}")
        
        return " | ".join(summary_parts)
    
    async def _update_group_statistics(self, chat_id: int, action_taken: str):
        """تحديث إحصائيات المجموعة"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # جلب الإحصائيات الحالية
            cursor.execute('''
            SELECT total_violations, total_warnings, total_mutes, total_bans 
            FROM group_statistics WHERE chat_id = ?
            ''', (chat_id,))
            
            result = cursor.fetchone()
            if result:
                total_violations, total_warnings, total_mutes, total_bans = result
            else:
                total_violations = total_warnings = total_mutes = total_bans = 0
            
            # تحديث العدادات
            total_violations += 1
            
            if 'warning' in action_taken.lower():
                total_warnings += 1
            elif 'mute' in action_taken.lower():
                total_mutes += 1
            elif 'ban' in action_taken.lower():
                total_bans += 1
            
            # حساب مستوى المخاطر
            risk_level = self._calculate_risk_level(total_violations, total_mutes, total_bans)
            
            # تحديث قاعدة البيانات
            cursor.execute('''
            INSERT OR REPLACE INTO group_statistics 
            (chat_id, total_violations, total_warnings, total_mutes, total_bans, 
             last_violation, risk_level, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                chat_id, total_violations, total_warnings, total_mutes, total_bans,
                datetime.now(), risk_level, datetime.now()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث إحصائيات المجموعة: {e}")
    
    def _calculate_risk_level(self, violations: int, mutes: int, bans: int) -> str:
        """حساب مستوى المخاطر للمجموعة"""
        total_score = violations + (mutes * 2) + (bans * 5)
        
        if total_score <= 5:
            return 'low'
        elif total_score <= 15:
            return 'medium'
        elif total_score <= 30:
            return 'high'
        else:
            return 'critical'
    
    async def send_instant_admin_alert(self, bot: Bot, chat_id: int, report_id: int):
        """إرسال تنبيه فوري للمشرفين"""
        try:
            # جلب تفاصيل التقرير
            report_data = await self.get_report_details(report_id)
            if not report_data:
                return
            
            # جلب المشرفين المشتركين في التنبيهات
            subscribed_admins = await self.get_subscribed_admins(chat_id, 'instant_alerts')
            
            # إنشاء رسالة التنبيه
            alert_message = self._create_instant_alert_message(report_data)
            
            # إنشاء أزرار التحكم
            keyboard = self._create_alert_keyboard(report_id)
            
            # إرسال للمشرفين
            for admin_id in subscribed_admins:
                try:
                    await bot.send_message(
                        admin_id,
                        alert_message,
                        reply_markup=keyboard,
                        parse_mode='Markdown'
                    )
                except Exception as send_error:
                    logging.debug(f"لم يتمكن من إرسال تنبيه للمشرف {admin_id}: {send_error}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال التنبيه الفوري: {e}")
    
    def _create_instant_alert_message(self, report_data: Dict) -> str:
        """إنشاء رسالة التنبيه الفوري"""
        msg = f"🚨 **تنبيه أمني فوري**\n\n"
        msg += f"📊 **رقم التقرير:** {report_data['id']}\n"
        msg += f"👤 **المخالف:** {report_data['user_name']}\n"
        msg += f"🏠 **المجموعة:** {report_data['chat_title']}\n"
        msg += f"⚠️ **نوع المخالفة:** {report_data['violation_type']}\n"
        msg += f"📈 **مستوى الخطورة:** {self._get_severity_emoji(report_data['severity_level'])}\n"
        msg += f"⚖️ **الإجراء المتخذ:** {report_data['action_taken']}\n"
        
        if report_data.get('ai_confidence', 0) > 0:
            msg += f"🤖 **ثقة الذكاء الاصطناعي:** {report_data['ai_confidence']:.2f}\n"
        
        msg += f"🕐 **الوقت:** {report_data['created_at']}\n\n"
        msg += f"📝 **ملخص المحتوى:**\n{report_data['content_summary']}"
        
        return msg
    
    def _get_severity_emoji(self, severity: int) -> str:
        """الحصول على رمز مستوى الخطورة"""
        emojis = {
            1: "🟢 منخفض",
            2: "🟡 متوسط", 
            3: "🟠 عالي",
            4: "🔴 شديد",
            5: "🚫 متطرف"
        }
        return emojis.get(severity, "⚪ غير محدد")
    
    def _create_alert_keyboard(self, report_id: int) -> InlineKeyboardMarkup:
        """إنشاء لوحة مفاتيح التحكم بالتقرير"""
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 عرض التفاصيل",
                    callback_data=f"report_details:{report_id}"
                ),
                InlineKeyboardButton(
                    text="✅ موافق",
                    callback_data=f"report_approve:{report_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ رفض الإجراء",
                    callback_data=f"report_reject:{report_id}"
                ),
                InlineKeyboardButton(
                    text="📝 إضافة ملاحظة",
                    callback_data=f"report_note:{report_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="📈 إحصائيات المجموعة",
                    callback_data=f"group_stats:{report_id}"
                )
            ]
        ])
        
        return keyboard
    
    async def get_report_details(self, report_id: int) -> Optional[Dict]:
        """الحصول على تفاصيل التقرير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT id, chat_id, user_id, violation_type, severity_level, 
                   content_summary, action_taken, ai_confidence, evidence_data,
                   report_status, admin_notes, created_at
            FROM detailed_admin_reports 
            WHERE id = ?
            ''', (report_id,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return {
                    'id': result[0],
                    'chat_id': result[1],
                    'user_id': result[2],
                    'violation_type': result[3],
                    'severity_level': result[4],
                    'content_summary': result[5],
                    'action_taken': result[6],
                    'ai_confidence': result[7],
                    'evidence_data': result[8],
                    'report_status': result[9],
                    'admin_notes': result[10],
                    'created_at': result[11],
                    'user_name': 'المستخدم',  # يمكن تحسينه لاحقاً
                    'chat_title': 'المجموعة'  # يمكن تحسينه لاحقاً
                }
            
            return None
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب تفاصيل التقرير: {e}")
            return None
    
    async def get_subscribed_admins(self, chat_id: int, report_type: str) -> List[int]:
        """الحصول على المشرفين المشتركين في نوع معين من التقارير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            if report_type == 'instant_alerts':
                cursor.execute('''
                SELECT admin_id FROM report_subscriptions 
                WHERE chat_id = ? AND instant_alerts = TRUE
                ''', (chat_id,))
            elif report_type == 'daily_summary':
                cursor.execute('''
                SELECT admin_id FROM report_subscriptions 
                WHERE chat_id = ? AND daily_summary = TRUE
                ''', (chat_id,))
            else:
                cursor.execute('''
                SELECT admin_id FROM report_subscriptions 
                WHERE chat_id = ? AND notification_enabled = TRUE
                ''', (chat_id,))
            
            results = cursor.fetchall()
            conn.close()
            
            return [admin_id[0] for admin_id in results]
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب المشرفين المشتركين: {e}")
            return []
    
    async def subscribe_admin_to_reports(self, admin_id: int, chat_id: int, 
                                       report_types: List[str] = None):
        """اشتراك مشرف في التقارير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # إعدادات افتراضية
            instant_alerts = True
            daily_summary = True
            notification_enabled = True
            
            # تخصيص الإعدادات حسب الطلب
            if report_types:
                instant_alerts = 'instant_alerts' in report_types
                daily_summary = 'daily_summary' in report_types
                notification_enabled = len(report_types) > 0
            
            cursor.execute('''
            INSERT OR REPLACE INTO report_subscriptions 
            (admin_id, chat_id, report_types, notification_enabled, 
             daily_summary, instant_alerts)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                admin_id, chat_id, ','.join(report_types or []),
                notification_enabled, daily_summary, instant_alerts
            ))
            
            conn.commit()
            conn.close()
            
            logging.info(f"✅ تم اشتراك المشرف {admin_id} في تقارير المجموعة {chat_id}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في اشتراك المشرف: {e}")
    
    async def generate_daily_summary(self, chat_id: int, date: datetime = None) -> str:
        """إنشاء ملخص يومي للمجموعة"""
        try:
            if date is None:
                date = datetime.now()
            
            start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=1)
            
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # إحصائيات اليوم
            cursor.execute('''
            SELECT COUNT(*), 
                   SUM(CASE WHEN severity_level >= 3 THEN 1 ELSE 0 END),
                   COUNT(DISTINCT user_id)
            FROM detailed_admin_reports 
            WHERE chat_id = ? AND created_at BETWEEN ? AND ?
            ''', (chat_id, start_date, end_date))
            
            daily_stats = cursor.fetchone()
            total_violations = daily_stats[0] or 0
            high_severity = daily_stats[1] or 0
            unique_users = daily_stats[2] or 0
            
            # أنواع المخالفات
            cursor.execute('''
            SELECT violation_type, COUNT(*) 
            FROM detailed_admin_reports 
            WHERE chat_id = ? AND created_at BETWEEN ? AND ?
            GROUP BY violation_type
            ORDER BY COUNT(*) DESC
            ''', (chat_id, start_date, end_date))
            
            violation_types = cursor.fetchall()
            
            # الإجراءات المتخذة
            cursor.execute('''
            SELECT action_taken, COUNT(*) 
            FROM detailed_admin_reports 
            WHERE chat_id = ? AND created_at BETWEEN ? AND ?
            GROUP BY action_taken
            ORDER BY COUNT(*) DESC
            ''', (chat_id, start_date, end_date))
            
            actions_taken = cursor.fetchall()
            
            conn.close()
            
            # إنشاء التقرير
            summary = f"📊 **ملخص الأمان اليومي**\n"
            summary += f"📅 **التاريخ:** {date.strftime('%Y-%m-%d')}\n\n"
            
            summary += f"📈 **الإحصائيات العامة:**\n"
            summary += f"• إجمالي المخالفات: {total_violations}\n"
            summary += f"• المخالفات عالية الخطورة: {high_severity}\n"
            summary += f"• عدد المستخدمين المخالفين: {unique_users}\n\n"
            
            if violation_types:
                summary += f"🚨 **أنواع المخالفات:**\n"
                for vtype, count in violation_types[:5]:
                    summary += f"• {vtype}: {count}\n"
                summary += "\n"
            
            if actions_taken:
                summary += f"⚖️ **الإجراءات المتخذة:**\n"
                for action, count in actions_taken[:5]:
                    summary += f"• {action}: {count}\n"
                summary += "\n"
            
            # تقييم الوضع العام
            risk_assessment = self._assess_daily_risk(total_violations, high_severity, unique_users)
            summary += f"🎯 **تقييم الوضع:** {risk_assessment}\n"
            
            return summary
            
        except Exception as e:
            logging.error(f"❌ خطأ في إنشاء الملخص اليومي: {e}")
            return "❌ حدث خطأ في إنشاء الملخص اليومي"
    
    def _assess_daily_risk(self, total_violations: int, high_severity: int, unique_users: int) -> str:
        """تقييم مخاطر اليوم"""
        if total_violations == 0:
            return "🟢 يوم آمن - لا توجد مخالفات"
        elif total_violations <= 3 and high_severity == 0:
            return "🟡 وضع طبيعي - مخالفات قليلة"
        elif total_violations <= 10 and high_severity <= 2:
            return "🟠 يتطلب متابعة - نشاط مشبوه"
        else:
            return "🔴 تحذير عالي - يتطلب تدخل فوري"
    
    async def send_daily_summaries(self, bot: Bot):
        """إرسال الملخصات اليومية لجميع المجموعات"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # جلب جميع المجموعات التي لها تقارير
            cursor.execute('''
            SELECT DISTINCT chat_id FROM detailed_admin_reports 
            WHERE DATE(created_at) = DATE('now')
            ''')
            
            chat_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            for chat_id in chat_ids:
                try:
                    # إنشاء الملخص اليومي
                    summary = await self.generate_daily_summary(chat_id)
                    
                    # جلب المشرفين المشتركين
                    subscribed_admins = await self.get_subscribed_admins(chat_id, 'daily_summary')
                    
                    # إرسال للمشرفين
                    for admin_id in subscribed_admins:
                        try:
                            await bot.send_message(admin_id, summary, parse_mode='Markdown')
                        except Exception as send_error:
                            logging.debug(f"لم يتمكن من إرسال ملخص للمشرف {admin_id}: {send_error}")
                
                except Exception as chat_error:
                    logging.error(f"خطأ في إرسال ملخص للمجموعة {chat_id}: {chat_error}")
            
        except Exception as e:
            logging.error(f"❌ خطأ في إرسال الملخصات اليومية: {e}")
    
    async def handle_report_callback(self, callback_query: CallbackQuery, bot: Bot):
        """معالجة استجابات المشرفين على التقارير"""
        try:
            callback_data = callback_query.data
            admin_id = callback_query.from_user.id
            
            if callback_data.startswith('report_details:'):
                report_id = int(callback_data.split(':')[1])
                await self._show_detailed_report(callback_query, report_id)
                
            elif callback_data.startswith('report_approve:'):
                report_id = int(callback_data.split(':')[1])
                await self._approve_report(callback_query, report_id, admin_id)
                
            elif callback_data.startswith('report_reject:'):
                report_id = int(callback_data.split(':')[1])
                await self._reject_report(callback_query, report_id, admin_id)
                
            elif callback_data.startswith('report_note:'):
                report_id = int(callback_data.split(':')[1])
                await self._request_admin_note(callback_query, report_id)
                
            elif callback_data.startswith('group_stats:'):
                report_id = int(callback_data.split(':')[1])
                await self._show_group_statistics(callback_query, report_id)
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة استجابة التقرير: {e}")
            await callback_query.answer("❌ حدث خطأ في معالجة الطلب")
    
    async def _show_detailed_report(self, callback_query: CallbackQuery, report_id: int):
        """عرض تفاصيل التقرير المفصلة"""
        try:
            report_data = await self.get_report_details(report_id)
            if not report_data:
                await callback_query.answer("❌ لم يتم العثور على التقرير")
                return
            
            details_msg = f"📊 **تقرير مفصل رقم {report_id}**\n\n"
            details_msg += f"👤 **معرف المستخدم:** `{report_data['user_id']}`\n"
            details_msg += f"🏠 **معرف المجموعة:** `{report_data['chat_id']}`\n"
            details_msg += f"⚠️ **نوع المخالفة:** {report_data['violation_type']}\n"
            details_msg += f"📈 **مستوى الخطورة:** {self._get_severity_emoji(report_data['severity_level'])}\n"
            details_msg += f"⚖️ **الإجراء المتخذ:** {report_data['action_taken']}\n"
            details_msg += f"📊 **حالة التقرير:** {report_data['report_status']}\n"
            
            if report_data.get('ai_confidence'):
                details_msg += f"🤖 **ثقة الذكاء الاصطناعي:** {report_data['ai_confidence']:.2f}\n"
            
            details_msg += f"🕐 **تاريخ الإنشاء:** {report_data['created_at']}\n\n"
            details_msg += f"📝 **ملخص المحتوى:**\n{report_data['content_summary']}\n\n"
            
            if report_data.get('admin_notes'):
                details_msg += f"📌 **ملاحظات المشرف:**\n{report_data['admin_notes']}"
            
            await callback_query.message.edit_text(details_msg, parse_mode='Markdown')
            await callback_query.answer()
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض تفاصيل التقرير: {e}")
            await callback_query.answer("❌ حدث خطأ في عرض التفاصيل")
    
    async def _approve_report(self, callback_query: CallbackQuery, report_id: int, admin_id: int):
        """الموافقة على التقرير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE detailed_admin_reports 
            SET report_status = 'approved', admin_id = ?, reviewed_at = ?
            WHERE id = ?
            ''', (admin_id, datetime.now(), report_id))
            
            conn.commit()
            conn.close()
            
            await callback_query.answer("✅ تم الموافقة على التقرير")
            
            # تحديث الرسالة
            updated_msg = callback_query.message.text + f"\n\n✅ **تمت الموافقة بواسطة المشرف**"
            await callback_query.message.edit_text(updated_msg, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في الموافقة على التقرير: {e}")
            await callback_query.answer("❌ حدث خطأ في الموافقة")
    
    async def _reject_report(self, callback_query: CallbackQuery, report_id: int, admin_id: int):
        """رفض التقرير"""
        try:
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            cursor.execute('''
            UPDATE detailed_admin_reports 
            SET report_status = 'rejected', admin_id = ?, reviewed_at = ?
            WHERE id = ?
            ''', (admin_id, datetime.now(), report_id))
            
            conn.commit()
            conn.close()
            
            await callback_query.answer("❌ تم رفض التقرير")
            
            # تحديث الرسالة
            updated_msg = callback_query.message.text + f"\n\n❌ **تم رفض التقرير بواسطة المشرف**"
            await callback_query.message.edit_text(updated_msg, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في رفض التقرير: {e}")
            await callback_query.answer("❌ حدث خطأ في الرفض")
    
    async def _request_admin_note(self, callback_query: CallbackQuery, report_id: int):
        """طلب ملاحظة من المشرف"""
        await callback_query.answer("📝 يرجى إرسال ملاحظتك في رسالة منفصلة مع إشارة لرقم التقرير")
    
    async def _show_group_statistics(self, callback_query: CallbackQuery, report_id: int):
        """عرض إحصائيات المجموعة"""
        try:
            # جلب معرف المجموعة من التقرير
            report_data = await self.get_report_details(report_id)
            if not report_data:
                await callback_query.answer("❌ لم يتم العثور على التقرير")
                return
            
            chat_id = report_data['chat_id']
            
            conn = sqlite3.connect(self.reports_db)
            cursor = conn.cursor()
            
            # جلب إحصائيات المجموعة
            cursor.execute('''
            SELECT total_violations, total_warnings, total_mutes, total_bans, 
                   last_violation, risk_level 
            FROM group_statistics WHERE chat_id = ?
            ''', (chat_id,))
            
            stats = cursor.fetchone()
            conn.close()
            
            if stats:
                stats_msg = f"📊 **إحصائيات المجموعة**\n\n"
                stats_msg += f"📈 **إجمالي المخالفات:** {stats[0]}\n"
                stats_msg += f"⚠️ **التحذيرات:** {stats[1]}\n"
                stats_msg += f"🔇 **الكتم:** {stats[2]}\n"
                stats_msg += f"🚫 **الطرد:** {stats[3]}\n"
                stats_msg += f"🕐 **آخر مخالفة:** {stats[4]}\n"
                stats_msg += f"🎯 **مستوى المخاطر:** {self._get_risk_level_emoji(stats[5])}"
            else:
                stats_msg = "📊 لا توجد إحصائيات متوفرة لهذه المجموعة"
            
            await callback_query.message.edit_text(stats_msg, parse_mode='Markdown')
            await callback_query.answer()
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض إحصائيات المجموعة: {e}")
            await callback_query.answer("❌ حدث خطأ في عرض الإحصائيات")
    
    def _get_risk_level_emoji(self, risk_level: str) -> str:
        """الحصول على رمز مستوى المخاطر"""
        emojis = {
            'low': '🟢 منخفض',
            'medium': '🟡 متوسط',
            'high': '🟠 عالي',
            'critical': '🔴 حرج'
        }
        return emojis.get(risk_level, '⚪ غير محدد')

# إنشاء كائن نظام التقارير
admin_reports = AdminReportsSystem()
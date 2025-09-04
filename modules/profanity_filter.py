"""
نظام فلترة الألفاظ المسيئة المتطور
Advanced Profanity Filter System with Smart Punishment Control
"""

import logging
import re
import asyncio
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Set
from aiogram import Bot
from aiogram.types import Message, ChatPermissions
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from config.hierarchy import has_permission, AdminLevel, get_user_admin_level
from database.operations import execute_query


class ProfanityFilter:
    """نظام فلترة الألفاظ المسيئة المتطور مع معالجة ذكية للعقوبات"""
    
    def __init__(self):
        self.enabled_groups: Set[int] = set()
        self.warning_counts: Dict[str, int] = {}  # "user_id:chat_id" -> count
        self.active_punishments: Dict[str, datetime] = {}  # "user_id:chat_id" -> end_time
        self.processing_lock: Set[str] = set()  # منع المعالجة المتكررة
        
        # تعابير منتظمة لاكتشاف الاختلافات في الكتابة
        self.bad_patterns = [
            # الكلمات الأكثر شيوعاً والأكثر إساءة
            r'(?i)كس\s*(ام|امك|امها|اختك|اخوك)',  # كس امك، كس اختك، إلخ
            r'(?i)(انيك|نيك|ناك)\s*(ام|امك|امها|اختك|اخوك)',  # انيك امك، نيك اختك، إلخ
            r'(?i)(زب|عير)\s*(ابوك|اباك|امك)',  # زب ابوك، عير امك، إلخ
            r'(?i)ابن\s*(الشرموط[هة]|القحب[هة]|الكلب[هة]|الزان[ي])',  # ابن الشرموطة، ابن القحبة، إلخ
            
            # كلمات عامة مع تنويع الأحرف
            r'(?i)\b(س[ب٨])\b', r'(?i)\b(ش[ت٥]م)\b', r'(?i)\b(ق[ذ٨]ف)\b',
            r'(?i)\b(ط[ع٥]ن)\b', r'(?i)\b(ك[ل٤]ب)\b',
            
            # كلمات مسيئة مع تهجئات مختلفة
            r'(?i)\b(ع[اٲ]ه[ر٤])\b', r'(?i)\b(ز[اٲ]ن[ي٨])\b',
            r'(?i)\b(ف[ح٨]ل)\b', r'(?i)\b(ش[ر٤]م[و٦]ط[هة]?)\b',
            r'(?i)\b(ق[ح٨]ب[هة])\b', r'(?i)\b(م[ن٥][ي٨][و٦]ك[هة]?)\b',
            
            # كلمات أخرى
            r'(?i)\b(خ[و٦]ل)\b', r'(?i)\b(خ[ن٥]ي[ث٨])\b',
            r'(?i)\b(ن[ذ٨]ل)\b', r'(?i)\b(ل[ع٥]ي[ن٥])\b',
            r'(?i)\b(ح[ق٥]ي[ر٤])\b', r'(?i)\b(و[س٥]خ)\b',
            r'(?i)\b(ح[ث٨]ال[هة])\b', r'(?i)\b(ب[و٦]ي)\b',
            r'(?i)\b(م[اٲ]د[ر٤])\b',
            
            # اختصارات وكتابات بديلة
            r'(?i)\b(كسم)\b', r'(?i)\b(كسختك)\b', r'(?i)\b(عير)\b',
            r'(?i)\b(ابن?\s*ال?\w{2,4})\b',  # لاكتشاف "ابن..." مع اختلافات
        ]
        
        # قائمة الكلمات المسيئة الأساسية
        self.base_bad_words = {
            'كس', 'انيك', 'نيك', 'ناك', 'زب', 'عير', 'كسم', 'كسمك',
            'سب', 'شتم', 'قذف', 'طعن', 'كلب', 'عاهر', 'زاني', 'فحل', 'شرموط',
            'قحبه', 'منيوك', 'منيوكه', 'زباله', 'خول', 'خنيث', 'داعر', 'داعره',
            'سافل', 'سافله', 'وسخ', 'قذر', 'حقير', 'حثاله', 'نذل', 'لعين'
        }
        
        # صلاحيات المستخدم المقيد
        self.restricted_permissions = ChatPermissions(
            can_send_messages=False,
            can_send_media_messages=False,
            can_send_polls=False,
            can_send_other_messages=False,
            can_add_web_page_previews=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False
        )
        
        # سيتم تهيئة قاعدة البيانات عند أول استخدام
        self._database_initialized = False
    
    async def init_database(self):
        """تهيئة جداول قاعدة البيانات"""
        try:
            # جدول إعدادات الفلتر لكل مجموعة
            await execute_query('''
                CREATE TABLE IF NOT EXISTS profanity_filter_settings (
                    chat_id INTEGER PRIMARY KEY,
                    enabled BOOLEAN DEFAULT TRUE,
                    warning_limit INTEGER DEFAULT 3,
                    mute_duration INTEGER DEFAULT 3600,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # جدول التحذيرات والعقوبات
            await execute_query('''
                CREATE TABLE IF NOT EXISTS profanity_warnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    warning_count INTEGER DEFAULT 0,
                    last_warning TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    punishment_end_time TIMESTAMP,
                    is_punished BOOLEAN DEFAULT FALSE,
                    UNIQUE(user_id, chat_id)
                )
            ''')
            
            # جدول الكلمات المسيئة المخصصة
            await execute_query('''
                CREATE TABLE IF NOT EXISTS custom_bad_words (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    word TEXT NOT NULL,
                    severity INTEGER DEFAULT 1,
                    added_by INTEGER,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            logging.info("✅ تم تهيئة قاعدة بيانات فلتر الألفاظ المسيئة")
            
            # تحميل الإعدادات الحالية
            await self.load_settings()
            
        except Exception as e:
            logging.error(f"❌ خطأ في تهيئة قاعدة بيانات فلتر الألفاظ: {e}")
    
    async def load_settings(self):
        """تحميل إعدادات الفلتر من قاعدة البيانات"""
        try:
            settings = await execute_query(
                "SELECT chat_id FROM profanity_filter_settings WHERE enabled = TRUE",
                fetch_all=True
            )
            
            if settings:
                self.enabled_groups = {row[0] if isinstance(row, tuple) else row['chat_id'] for row in settings}
                logging.info(f"تم تحميل إعدادات الفلتر: {len(self.enabled_groups)} مجموعة مفعلة")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحميل إعدادات الفلتر: {e}")
    
    def is_enabled(self, chat_id: int) -> bool:
        """التحقق من تفعيل الفلتر في المجموعة"""
        return chat_id in self.enabled_groups
    
    async def enable_filter(self, chat_id: int) -> bool:
        """تفعيل فلتر الألفاظ المسيئة في المجموعة"""
        try:
            # تهيئة قاعدة البيانات إذا لم تكن مهيأة
            if not self._database_initialized:
                await self.init_database()
                self._database_initialized = True
            
            await execute_query(
                "INSERT OR REPLACE INTO profanity_filter_settings (chat_id, enabled) VALUES (?, TRUE)",
                (chat_id,)
            )
            self.enabled_groups.add(chat_id)
            logging.info(f"✅ تم تفعيل فلتر الألفاظ في المجموعة {chat_id}")
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في تفعيل الفلتر: {e}")
            return False
    
    async def disable_filter(self, chat_id: int) -> bool:
        """تعطيل فلتر الألفاظ المسيئة في المجموعة"""
        try:
            await execute_query(
                "UPDATE profanity_filter_settings SET enabled = FALSE WHERE chat_id = ?",
                (chat_id,)
            )
            self.enabled_groups.discard(chat_id)
            logging.info(f"✅ تم تعطيل فلتر الألفاظ في المجموعة {chat_id}")
            return True
        except Exception as e:
            logging.error(f"❌ خطأ في تعطيل الفلتر: {e}")
            return False
    
    async def check_user_status(self, bot: Bot, chat_id: int, user_id: int) -> Dict[str, any]:
        """فحص حالة المستخدم الحقيقية في المجموعة"""
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            
            return {
                'status': member.status,
                'can_send_messages': getattr(member, 'can_send_messages', True),
                'is_restricted': member.status == 'restricted',
                'is_banned': member.status in ['kicked', 'left'],
                'until_date': getattr(member, 'until_date', None)
            }
        except Exception as e:
            logging.error(f"❌ خطأ في فحص حالة المستخدم: {e}")
            return {'status': 'unknown', 'can_send_messages': True, 'is_restricted': False}
    
    def contains_profanity(self, text: str) -> Tuple[bool, List[str]]:
        """فحص النص لوجود ألفاظ مسيئة"""
        if not text:
            return False, []
        
        text_lower = text.lower()
        found_words = []
        
        logging.info(f"🔍 فحص النص: '{text}' (محول إلى صغير: '{text_lower}')")
        
        # فحص الكلمات الأساسية
        for word in self.base_bad_words:
            if word in text_lower:
                found_words.append(word)
                logging.info(f"⚠️ تم اكتشاف كلمة مسيئة أساسية: '{word}'")
        
        # فحص التعابير المنتظمة
        for pattern in self.bad_patterns:
            matches = re.findall(pattern, text)
            if matches:
                found_words.extend([match[0] if isinstance(match, tuple) else match for match in matches])
                logging.info(f"⚠️ تم اكتشاف نمط مسيء: '{pattern}' - النتائج: {matches}")
        
        result = len(found_words) > 0
        logging.info(f"🎯 نتيجة فحص الألفاظ المسيئة: {result} - كلمات مكتشفة: {found_words}")
        
        return result, found_words
    
    async def get_user_warnings(self, user_id: int, chat_id: int) -> Dict[str, any]:
        """الحصول على معلومات تحذيرات المستخدم"""
        try:
            result = await execute_query(
                "SELECT warning_count, punishment_end_time, is_punished FROM profanity_warnings WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id),
                fetch_one=True
            )
            
            if result:
                if isinstance(result, tuple):
                    warning_count, punishment_end_str, is_punished = result
                else:
                    warning_count = result.get('warning_count', 0)
                    punishment_end_str = result.get('punishment_end_time')
                    is_punished = result.get('is_punished', False)
                
                punishment_end = None
                if punishment_end_str:
                    try:
                        punishment_end = datetime.fromisoformat(punishment_end_str)
                    except:
                        punishment_end = None
                
                return {
                    'warning_count': warning_count,
                    'punishment_end_time': punishment_end,
                    'is_punished': bool(is_punished)
                }
            
            return {'warning_count': 0, 'punishment_end_time': None, 'is_punished': False}
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب تحذيرات المستخدم: {e}")
            return {'warning_count': 0, 'punishment_end_time': None, 'is_punished': False}
    
    async def add_warning(self, user_id: int, chat_id: int) -> int:
        """إضافة تحذير للمستخدم وإرجاع العدد الجديد"""
        try:
            # الحصول على العدد الحالي
            current_warnings = await self.get_user_warnings(user_id, chat_id)
            new_count = current_warnings['warning_count'] + 1
            
            # تحديث قاعدة البيانات
            await execute_query('''
                INSERT OR REPLACE INTO profanity_warnings 
                (user_id, chat_id, warning_count, last_warning, is_punished)
                VALUES (?, ?, ?, ?, FALSE)
            ''', (user_id, chat_id, new_count, datetime.now().isoformat()))
            
            # تحديث الذاكرة المؤقتة
            key = f"{user_id}:{chat_id}"
            self.warning_counts[key] = new_count
            
            logging.info(f"تم إضافة تحذير للمستخدم {user_id} في المجموعة {chat_id}، العدد الجديد: {new_count}")
            return new_count
            
        except Exception as e:
            logging.error(f"❌ خطأ في إضافة التحذير: {e}")
            return 0
    
    async def apply_punishment(self, bot: Bot, user_id: int, chat_id: int, duration_minutes: int = 60) -> bool:
        """تطبيق عقوبة الكتم مع التحقق من الحالة"""
        try:
            # فحص حالة المستخدم أولاً
            user_status = await self.check_user_status(bot, chat_id, user_id)
            
            # إذا كان المستخدم مكتوم بالفعل، لا نطبق عقوبة إضافية
            if user_status['is_restricted'] and not user_status['can_send_messages']:
                logging.info(f"المستخدم {user_id} مكتوم بالفعل في المجموعة {chat_id}")
                return False
            
            # تطبيق الكتم
            until_date = datetime.now() + timedelta(minutes=duration_minutes)
            
            await bot.restrict_chat_member(
                chat_id=chat_id,
                user_id=user_id,
                permissions=self.restricted_permissions,
                until_date=until_date
            )
            
            # تسجيل العقوبة في قاعدة البيانات
            await execute_query('''
                UPDATE profanity_warnings 
                SET punishment_end_time = ?, is_punished = TRUE
                WHERE user_id = ? AND chat_id = ?
            ''', (until_date.isoformat(), user_id, chat_id))
            
            # تحديث الذاكرة المؤقتة
            key = f"{user_id}:{chat_id}"
            self.active_punishments[key] = until_date
            
            logging.info(f"تم كتم المستخدم {user_id} في المجموعة {chat_id} حتى {until_date}")
            return True
            
        except TelegramForbiddenError:
            logging.warning(f"البوت لا يملك صلاحية كتم المستخدم {user_id} في المجموعة {chat_id}")
            return False
        except TelegramBadRequest as e:
            logging.warning(f"خطأ في كتم المستخدم {user_id}: {e}")
            return False
        except Exception as e:
            logging.error(f"❌ خطأ في تطبيق العقوبة: {e}")
            return False
    
    async def check_punishment_expired(self, user_id: int, chat_id: int) -> bool:
        """التحقق من انتهاء مدة العقوبة"""
        try:
            warnings_info = await self.get_user_warnings(user_id, chat_id)
            
            if not warnings_info['is_punished'] or not warnings_info['punishment_end_time']:
                return True  # لا توجد عقوبة نشطة
            
            # التحقق من انتهاء الوقت
            if datetime.now() >= warnings_info['punishment_end_time']:
                # إزالة العقوبة من قاعدة البيانات
                await execute_query('''
                    UPDATE profanity_warnings 
                    SET is_punished = FALSE, punishment_end_time = NULL
                    WHERE user_id = ? AND chat_id = ?
                ''', (user_id, chat_id))
                
                # إزالة من الذاكرة المؤقتة
                key = f"{user_id}:{chat_id}"
                self.active_punishments.pop(key, None)
                
                logging.info(f"انتهت مدة عقوبة المستخدم {user_id} في المجموعة {chat_id}")
                return True
            
            return False  # العقوبة ما زالت نشطة
            
        except Exception as e:
            logging.error(f"❌ خطأ في فحص انتهاء العقوبة: {e}")
            return True  # في حالة الخطأ، نسمح بالمعالجة
    
    async def process_message(self, message: Message, bot: Bot) -> bool:
        """معالجة الرسالة الرئيسية مع الحماية من إعادة الكتم"""
        try:
            logging.info(f"🔎 بدأ معالجة رسالة من {message.from_user.id} في المجموعة {message.chat.id}")
            
            # تهيئة قاعدة البيانات إذا لم تكن مهيأة
            if not self._database_initialized:
                await self.init_database()
                self._database_initialized = True
                logging.info("✅ تم تهيئة قاعدة بيانات فلتر الألفاظ المسيئة")
            
            # التحقق من تفعيل الفلتر
            if not self.is_enabled(message.chat.id):
                logging.info(f"ℹ️ فلتر الألفاظ المسيئة غير مفعل في المجموعة {message.chat.id}")
                return False
            
            # التحقق من وجود نص
            if not message.text and not message.caption:
                return False
            
            text = message.text or message.caption
            user_id = message.from_user.id
            chat_id = message.chat.id
            
            # تجاهل رسائل المديرين
            user_level = get_user_admin_level(user_id, chat_id)
            if user_level.value >= AdminLevel.MODERATOR.value:
                return False
            
            # منع المعالجة المتكررة
            processing_key = f"{user_id}:{chat_id}:{message.message_id}"
            if processing_key in self.processing_lock:
                return False
            
            self.processing_lock.add(processing_key)
            
            try:
                # التحقق من انتهاء العقوبة أولاً
                punishment_expired = await self.check_punishment_expired(user_id, chat_id)
                if not punishment_expired:
                    # المستخدم ما زال تحت العقوبة، لا نفعل شيء
                    return False
                
                # فحص وجود ألفاظ مسيئة
                has_profanity, found_words = self.contains_profanity(text)
                
                if has_profanity:
                    # حذف الرسالة
                    try:
                        await message.delete()
                    except Exception as delete_error:
                        logging.warning(f"لم يتم حذف الرسالة: {delete_error}")
                    
                    # إضافة تحذير
                    warning_count = await self.add_warning(user_id, chat_id)
                    
                    # إرسال رسالة تحذير
                    warning_msg = f"⚠️ **تحذير لـ** {message.from_user.mention_html()}\n\n"
                    warning_msg += f"🚫 **تم حذف رسالتك لاحتوائها على ألفاظ غير لائقة**\n"
                    warning_msg += f"📊 **عدد تحذيراتك:** {warning_count}/3\n\n"
                    
                    if len(found_words) > 0:
                        warning_msg += f"🔍 **الكلمات المكتشفة:** {', '.join(found_words[:3])}\n\n"
                    
                    # تطبيق العقوبة عند الوصول للحد الأقصى
                    if warning_count >= 3:
                        punishment_applied = await self.apply_punishment(bot, user_id, chat_id, 60)
                        
                        if punishment_applied:
                            warning_msg += f"⛔ **تم كتمك لمدة ساعة واحدة** بسبب تخطي الحد الأقصى للتحذيرات\n"
                            warning_msg += f"⏰ **سيتم إلغاء الكتم تلقائياً بعد انتهاء المدة**"
                        else:
                            warning_msg += f"⚠️ **تحذير أخير!** المرة القادمة ستتم معاقبتك"
                    else:
                        remaining = 3 - warning_count
                        warning_msg += f"⏳ **باقي {remaining} تحذيرات قبل المعاقبة**"
                    
                    # إرسال الرسالة
                    try:
                        await bot.send_message(
                            chat_id=chat_id,
                            text=warning_msg,
                            parse_mode='HTML'
                        )
                    except Exception as send_error:
                        logging.warning(f"لم يتم إرسال رسالة التحذير: {send_error}")
                    
                    return True
                
                return False
                
            finally:
                # إزالة القفل
                self.processing_lock.discard(processing_key)
                
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة الرسالة للفلتر: {e}")
            return False
    
    async def reset_user_warnings(self, user_id: int, chat_id: int) -> bool:
        """إعادة تعيين تحذيرات المستخدم"""
        try:
            await execute_query('''
                UPDATE profanity_warnings 
                SET warning_count = 0, is_punished = FALSE, punishment_end_time = NULL
                WHERE user_id = ? AND chat_id = ?
            ''', (user_id, chat_id))
            
            # إزالة من الذاكرة المؤقتة
            key = f"{user_id}:{chat_id}"
            self.warning_counts.pop(key, None)
            self.active_punishments.pop(key, None)
            
            logging.info(f"تم إعادة تعيين تحذيرات المستخدم {user_id} في المجموعة {chat_id}")
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعادة تعيين التحذيرات: {e}")
            return False
    
    async def get_filter_stats(self, chat_id: int) -> Dict[str, any]:
        """الحصول على إحصائيات الفلتر للمجموعة"""
        try:
            # عدد المستخدمين مع تحذيرات
            users_with_warnings = await execute_query(
                "SELECT COUNT(*) FROM profanity_warnings WHERE chat_id = ? AND warning_count > 0",
                (chat_id,),
                fetch_one=True
            )
            
            # عدد المستخدمين المعاقبين حالياً
            punished_users = await execute_query(
                "SELECT COUNT(*) FROM profanity_warnings WHERE chat_id = ? AND is_punished = TRUE",
                (chat_id,),
                fetch_one=True
            )
            
            # إجمالي التحذيرات
            total_warnings = await execute_query(
                "SELECT SUM(warning_count) FROM profanity_warnings WHERE chat_id = ?",
                (chat_id,),
                fetch_one=True
            )
            
            return {
                'enabled': self.is_enabled(chat_id),
                'users_with_warnings': users_with_warnings[0] if users_with_warnings else 0,
                'punished_users': punished_users[0] if punished_users else 0,
                'total_warnings': total_warnings[0] if total_warnings and total_warnings[0] else 0
            }
            
        except Exception as e:
            logging.error(f"❌ خطأ في جلب إحصائيات الفلتر: {e}")
            return {'enabled': False, 'users_with_warnings': 0, 'punished_users': 0, 'total_warnings': 0}


# إنشاء مثيل عالي من الفلتر
profanity_filter = ProfanityFilter()
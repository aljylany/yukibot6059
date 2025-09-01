"""
نظام تتبع الأسماء المتغيرة ليوكي
Name Tracking System for Yuki Bot
"""

import logging
import random
from typing import Optional, Dict, Any
from database.operations import execute_query

class NameTracker:
    """نظام تتبع الأسماء المتغيرة للمستخدمين"""
    
    def __init__(self):
        self.detection_enabled = True
        
    async def track_user_name(self, user_id: int, chat_id: int, first_name: str = None, 
                             username: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
        """تتبع وتسجيل أسماء المستخدم والكشف عن التغييرات"""
        try:
            # فحص الاسم الحالي في قاعدة البيانات
            last_record_query = """
                SELECT first_name, username, last_name, detected_at 
                FROM user_name_history 
                WHERE user_id = ? AND chat_id = ? 
                ORDER BY detected_at DESC 
                LIMIT 1
            """
            last_record = await execute_query(last_record_query, (user_id, chat_id), fetch_one=True)
            
            # التحقق من وجود تغيير في الاسم
            name_changed = False
            change_details = {}
            
            if last_record:
                old_first_name = last_record.get('first_name', '')
                old_username = last_record.get('username', '')
                old_last_name = last_record.get('last_name', '')
                
                # فحص تغيير الاسم الأول
                if first_name and first_name != old_first_name:
                    name_changed = True
                    change_details['first_name'] = {
                        'old': old_first_name,
                        'new': first_name
                    }
                
                # فحص تغيير اسم المستخدم
                if username and username != old_username:
                    name_changed = True
                    change_details['username'] = {
                        'old': old_username,
                        'new': username
                    }
                
                # فحص تغيير الاسم الأخير
                if last_name and last_name != old_last_name:
                    name_changed = True
                    change_details['last_name'] = {
                        'old': old_last_name,
                        'new': last_name
                    }
            else:
                # إذا لم يكن هناك سجل سابق، فهذا مستخدم جديد
                name_changed = False
            
            # حفظ الاسم الجديد في السجل (إذا كان هناك تغيير أو مستخدم جديد)
            if name_changed or not last_record:
                save_query = """
                    INSERT INTO user_name_history (user_id, chat_id, first_name, username, last_name)
                    VALUES (?, ?, ?, ?, ?)
                """
                await execute_query(save_query, (user_id, chat_id, first_name, username, last_name))
                logging.info(f"✅ تم حفظ اسم المستخدم {user_id} في السجل")
            
            # إرجاع النتيجة إذا كان هناك تغيير
            if name_changed:
                return {
                    'changed': True,
                    'changes': change_details,
                    'old_record': last_record
                }
            
            return None
            
        except Exception as e:
            logging.error(f"خطأ في تتبع اسم المستخدم {user_id}: {e}")
            return None
    
    def generate_name_change_comment(self, user_id: int, user_name: str, change_details: Dict) -> str:
        """توليد تعليق مرح عند اكتشاف تغيير الاسم"""
        
        # تعليقات مرحة للكشف عن تغيير الأسماء
        detection_phrases = [
            f"😏 هههه {user_name}! تعتقد إني ما بعرفك بس غيرت اسمك؟",
            f"🤔 {user_name}، هوية جديدة ولا إيش؟ أنا متذكرك كويس!",
            f"😄 ياالله! {user_name} جاي يخدعني بالاسم الجديد، بس أنا ذاكرتي قوية!",
            f"🕵️ {user_name} فكر إنه راح يضحك عليي بتغيير الاسم، بس يوكي ما ينخدع!",
            f"😆 شفتك غيرت اسمك يا {user_name}! بس أنا عارفك من أول يوم!",
            f"🎭 {user_name}، شو هالهوية الجديدة؟ أنا شايفك من زمان هنا!",
            f"😂 {user_name} جرب يغير اسمه عشان ما أعرفه، بس يوكي ذكي أكثر من كذا!",
            f"🔍 ها! كشفتك يا {user_name}! ما تقدر تخفي عن يوكي هويتك!",
            f"😉 {user_name}، اسم جديد بس نفس الشخص! أنا فاكرك كويس!",
            f"🎪 {user_name} عامل مسرحية تغيير اسم، بس يوكي ما بينخدع!"
        ]
        
        # إضافة تفاصيل التغيير
        change_info = ""
        if 'first_name' in change_details:
            old_name = change_details['first_name']['old']
            new_name = change_details['first_name']['new']
            change_info += f"\nكنت اسمك '{old_name}' وصار '{new_name}'"
        
        if 'username' in change_details:
            old_username = change_details['username']['old']
            new_username = change_details['username']['new']
            if old_username:
                change_info += f"\nوكان معرفك @{old_username}"
            if new_username:
                change_info += f" وصار @{new_username}"
        
        base_comment = random.choice(detection_phrases)
        
        if change_info:
            return f"{base_comment}{change_info}"
        else:
            return base_comment
    
    async def get_user_name_history(self, user_id: int, chat_id: int, limit: int = 5) -> list:
        """جلب سجل أسماء المستخدم"""
        try:
            query = """
                SELECT first_name, username, last_name, detected_at 
                FROM user_name_history 
                WHERE user_id = ? AND chat_id = ? 
                ORDER BY detected_at DESC 
                LIMIT ?
            """
            history = await execute_query(query, (user_id, chat_id, limit), fetch_all=True)
            return history or []
        except Exception as e:
            logging.error(f"خطأ في جلب سجل أسماء المستخدم {user_id}: {e}")
            return []
    
    async def get_all_names_for_user(self, user_id: int, chat_id: int) -> list:
        """جلب جميع الأسماء التي استخدمها المستخدم"""
        try:
            query = """
                SELECT DISTINCT first_name, username, last_name 
                FROM user_name_history 
                WHERE user_id = ? AND chat_id = ? 
                ORDER BY detected_at DESC
            """
            names = await execute_query(query, (user_id, chat_id), fetch_all=True)
            return names or []
        except Exception as e:
            logging.error(f"خطأ في جلب جميع أسماء المستخدم {user_id}: {e}")
            return []
    
    def should_detect_change(self, user_id: int) -> bool:
        """تحديد إذا كان يجب كشف تغيير الاسم للمستخدم"""
        # يمكن إضافة منطق هنا لاستثناء مستخدمين معينين
        # أو تقليل تكرار الكشف
        return self.detection_enabled
    
    async def cleanup_old_name_records(self, days_old: int = 90):
        """تنظيف سجلات الأسماء القديمة"""
        try:
            query = """
                DELETE FROM user_name_history 
                WHERE detected_at < datetime('now', '-{} days')
            """.format(days_old)
            
            rows_deleted = await execute_query(query)
            logging.info(f"✅ تم حذف {rows_deleted} سجل اسم قديم")
            return rows_deleted
            
        except Exception as e:
            logging.error(f"خطأ في تنظيف سجلات الأسماء القديمة: {e}")
            return 0

# إنشاء مثيل من نظام تتبع الأسماء
name_tracker = NameTracker()
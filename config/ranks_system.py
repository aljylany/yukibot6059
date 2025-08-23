"""
نظام الرتب المتقدم للبوت
يفصل بين الرتب الإدارية والترفيهية مع صلاحيات محددة
"""

import logging
import asyncio
from typing import List, Dict, Optional, Set
from enum import Enum
from dataclasses import dataclass
from database.operations import execute_query


class RankType(Enum):
    """نوع الرتبة"""
    ADMINISTRATIVE = "administrative"  # رتبة إدارية
    ENTERTAINMENT = "entertainment"   # رتبة ترفيهية


class Permission(Enum):
    """الصلاحيات المتاحة"""
    # صلاحيات الإدارة الأساسية
    MUTE_USERS = "mute_users"                   # كتم المستخدمين
    UNMUTE_USERS = "unmute_users"               # إلغاء كتم المستخدمين
    WARN_USERS = "warn_users"                   # تحذير المستخدمين
    DELETE_MESSAGES = "delete_messages"         # حذف الرسائل
    
    # صلاحيات الإدارة المتوسطة
    KICK_USERS = "kick_users"                   # طرد المستخدمين
    RESTRICT_USERS = "restrict_users"           # تقييد المستخدمين
    PIN_MESSAGES = "pin_messages"               # تثبيت الرسائل
    CHANGE_GROUP_INFO = "change_group_info"     # تغيير معلومات المجموعة
    
    # صلاحيات الإدارة المتقدمة
    BAN_USERS = "ban_users"                     # حظر المستخدمين
    UNBAN_USERS = "unban_users"                 # إلغاء حظر المستخدمين
    PROMOTE_MODERATORS = "promote_moderators"   # ترقية مشرفين
    DEMOTE_MODERATORS = "demote_moderators"     # تخفيض رتبة مشرفين
    MANAGE_RANKS = "manage_ranks"               # إدارة الرتب
    
    # صلاحيات الإدارة العالية
    ADD_ADMINS = "add_admins"                   # إضافة إداريين
    REMOVE_ADMINS = "remove_admins"             # إزالة إداريين
    MANAGE_BOT_SETTINGS = "manage_bot_settings" # إدارة إعدادات البوت
    ACCESS_ADMIN_PANEL = "access_admin_panel"   # الوصول للوحة الإدارة
    
    # صلاحيات خاصة
    VIEW_ANALYTICS = "view_analytics"           # عرض التحليلات
    MANAGE_CUSTOM_COMMANDS = "manage_custom_commands"  # إدارة الأوامر المخصصة
    BROADCAST_MESSAGES = "broadcast_messages"   # إرسال رسائل جماعية


@dataclass
class RankInfo:
    """معلومات الرتبة"""
    name: str                    # اسم الرتبة
    display_name: str           # الاسم المعروض
    rank_type: RankType         # نوع الرتبة
    level: int                  # مستوى الرتبة (للترتيب)
    permissions: Set[Permission] # الصلاحيات
    color: str                  # لون الرتبة (للعرض)
    description: str            # وصف الرتبة


# تعريف الرتب الإدارية
ADMINISTRATIVE_RANKS = {
    "مشرف_مساعد": RankInfo(
        name="مشرف_مساعد",
        display_name="🟢 مشرف مساعد",
        rank_type=RankType.ADMINISTRATIVE,
        level=1,
        permissions={
            Permission.MUTE_USERS,
            Permission.UNMUTE_USERS,
            Permission.WARN_USERS,
            Permission.DELETE_MESSAGES
        },
        color="🟢",
        description="مساعد في الإدارة الأساسية - كتم وتحذير المستخدمين"
    ),
    
    "مشرف": RankInfo(
        name="مشرف",
        display_name="🔵 مشرف",
        rank_type=RankType.ADMINISTRATIVE,
        level=2,
        permissions={
            Permission.MUTE_USERS,
            Permission.UNMUTE_USERS,
            Permission.WARN_USERS,
            Permission.DELETE_MESSAGES,
            Permission.KICK_USERS,
            Permission.RESTRICT_USERS,
            Permission.PIN_MESSAGES
        },
        color="🔵",
        description="مشرف متوسط - طرد وتقييد المستخدمين"
    ),
    
    "مشرف_أول": RankInfo(
        name="مشرف_أول",
        display_name="🟡 مشرف أول",
        rank_type=RankType.ADMINISTRATIVE,
        level=3,
        permissions={
            Permission.MUTE_USERS,
            Permission.UNMUTE_USERS,
            Permission.WARN_USERS,
            Permission.DELETE_MESSAGES,
            Permission.KICK_USERS,
            Permission.RESTRICT_USERS,
            Permission.PIN_MESSAGES,
            Permission.BAN_USERS,
            Permission.UNBAN_USERS,
            Permission.PROMOTE_MODERATORS,
            Permission.CHANGE_GROUP_INFO
        },
        color="🟡",
        description="مشرف متقدم - حظر وترقية المشرفين"
    ),
    
    "نائب_المالك": RankInfo(
        name="نائب_المالك",
        display_name="🟠 نائب المالك",
        rank_type=RankType.ADMINISTRATIVE,
        level=4,
        permissions={
            Permission.MUTE_USERS,
            Permission.UNMUTE_USERS,
            Permission.WARN_USERS,
            Permission.DELETE_MESSAGES,
            Permission.KICK_USERS,
            Permission.RESTRICT_USERS,
            Permission.PIN_MESSAGES,
            Permission.BAN_USERS,
            Permission.UNBAN_USERS,
            Permission.PROMOTE_MODERATORS,
            Permission.DEMOTE_MODERATORS,
            Permission.CHANGE_GROUP_INFO,
            Permission.MANAGE_RANKS,
            Permission.VIEW_ANALYTICS,
            Permission.MANAGE_CUSTOM_COMMANDS
        },
        color="🟠",
        description="نائب المالك - إدارة عالية للمجموعة"
    ),
    
    "مالك": RankInfo(
        name="مالك",
        display_name="🔴 مالك",
        rank_type=RankType.ADMINISTRATIVE,
        level=5,
        permissions=set(Permission),  # جميع الصلاحيات
        color="🔴",
        description="مالك المجموعة - صلاحيات كاملة"
    )
}

# تعريف الرتب الترفيهية
ENTERTAINMENT_RANKS = {
    "مميز": RankInfo(
        name="مميز",
        display_name="⭐ مميز",
        rank_type=RankType.ENTERTAINMENT,
        level=1,
        permissions=set(),
        color="⭐",
        description="عضو مميز في المجموعة"
    ),
    
    "نشط": RankInfo(
        name="نشط",
        display_name="🌟 نشط",
        rank_type=RankType.ENTERTAINMENT,
        level=2,
        permissions=set(),
        color="🌟",
        description="عضو نشط ومتفاعل"
    ),
    
    "محترف": RankInfo(
        name="محترف",
        display_name="💎 محترف",
        rank_type=RankType.ENTERTAINMENT,
        level=3,
        permissions=set(),
        color="💎",
        description="عضو محترف في الألعاب"
    ),
    
    "أسطورة": RankInfo(
        name="أسطورة",
        display_name="👑 أسطورة",
        rank_type=RankType.ENTERTAINMENT,
        level=4,
        permissions=set(),
        color="👑",
        description="لاعب أسطوري"
    )
}

# جميع الرتب
ALL_RANKS = {**ADMINISTRATIVE_RANKS, **ENTERTAINMENT_RANKS}


class RankManager:
    """مدير النظام المتقدم للرتب"""
    
    def __init__(self):
        # تخزين رتب المستخدمين في الذاكرة
        self.user_ranks: Dict[int, Dict[int, str]] = {}  # {group_id: {user_id: rank_name}}
    
    async def init_database_tables(self):
        """تهيئة جداول الرتب في قاعدة البيانات"""
        try:
            # جدول الرتب الجديد
            await execute_query("""
                CREATE TABLE IF NOT EXISTS user_ranks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    rank_name TEXT NOT NULL,
                    rank_type TEXT NOT NULL,
                    promoted_by INTEGER,
                    promoted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, chat_id)
                )
            """)
            
            # جدول تاريخ الترقيات
            await execute_query("""
                CREATE TABLE IF NOT EXISTS rank_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    chat_id INTEGER NOT NULL,
                    old_rank TEXT,
                    new_rank TEXT NOT NULL,
                    changed_by INTEGER,
                    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reason TEXT
                )
            """)
            
            logging.info("✅ تم إنشاء جداول نظام الرتب المتقدم")
            
        except Exception as e:
            logging.error(f"خطأ في تهيئة جداول الرتب: {e}")
    
    async def load_ranks_from_database(self):
        """تحميل الرتب من قاعدة البيانات"""
        try:
            ranks = await execute_query(
                "SELECT user_id, chat_id, rank_name FROM user_ranks",
                fetch_all=True
            )
            
            if ranks and isinstance(ranks, (list, tuple)):
                for rank in ranks:
                    try:
                        # التعامل مع dict أو Row objects من قاعدة البيانات
                        if isinstance(rank, dict):
                            user_id = rank.get('user_id')
                            chat_id = rank.get('chat_id') 
                            rank_name = rank.get('rank_name')
                        elif hasattr(rank, 'user_id'):  # Row object
                            user_id = rank.user_id
                            chat_id = rank.chat_id
                            rank_name = rank.rank_name
                        elif isinstance(rank, (tuple, list)) and len(rank) >= 3:
                            user_id = rank[0] if rank[0] is not None else None
                            chat_id = rank[1] if rank[1] is not None else None
                            rank_name = rank[2] if rank[2] is not None else None
                        else:
                            continue
                        
                        # تحويل إلى الأنواع الصحيحة
                        if user_id is not None:
                            user_id = int(user_id)
                        if chat_id is not None:
                            chat_id = int(chat_id)
                        if rank_name is not None:
                            rank_name = str(rank_name)
                            
                    except (ValueError, TypeError, AttributeError):
                        continue
                    
                    if user_id and chat_id and rank_name:
                        if chat_id not in self.user_ranks:
                            self.user_ranks[chat_id] = {}
                        
                        self.user_ranks[chat_id][user_id] = rank_name
            
            rank_count = len(ranks) if ranks and isinstance(ranks, (list, tuple)) else 0
            logging.info(f"تم تحميل {rank_count} رتبة من قاعدة البيانات")
            
        except Exception as e:
            logging.error(f"خطأ في تحميل الرتب: {e}")
    
    def get_user_rank(self, user_id: int, chat_id: int) -> Optional[RankInfo]:
        """الحصول على رتبة المستخدم"""
        try:
            if chat_id in self.user_ranks and user_id in self.user_ranks[chat_id]:
                rank_name = self.user_ranks[chat_id][user_id]
                return ALL_RANKS.get(rank_name)
            return None
        except Exception as e:
            logging.error(f"خطأ في الحصول على رتبة المستخدم: {e}")
            return None
    
    def user_has_permission(self, user_id: int, chat_id: int, permission: Permission) -> bool:
        """التحقق من امتلاك المستخدم لصلاحية معينة"""
        try:
            # فحص إذا كان المستخدم Master (من النظام القديم)
            from config.hierarchy import is_master
            if is_master(user_id):
                return True
            
            rank = self.get_user_rank(user_id, chat_id)
            if rank and rank.rank_type == RankType.ADMINISTRATIVE:
                return permission in rank.permissions
            
            return False
        except Exception as e:
            logging.error(f"خطأ في فحص الصلاحية: {e}")
            return False
    
    async def promote_user(self, user_id: int, chat_id: int, rank_name: str, promoted_by: int, reason: Optional[str] = None) -> bool:
        """ترقية مستخدم لرتبة جديدة"""
        try:
            if rank_name not in ALL_RANKS:
                return False
            
            # الحصول على الرتبة القديمة
            old_rank = None
            if chat_id in self.user_ranks and user_id in self.user_ranks[chat_id]:
                old_rank = self.user_ranks[chat_id][user_id]
            
            # تحديث في قاعدة البيانات
            await execute_query("""
                INSERT OR REPLACE INTO user_ranks 
                (user_id, chat_id, rank_name, rank_type, promoted_by) 
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, chat_id, rank_name, ALL_RANKS[rank_name].rank_type.value, promoted_by))
            
            # إضافة للتاريخ
            reason_value = reason if reason is not None else "ترقية عادية"
            old_rank_value = old_rank if old_rank is not None else "عضو عادي"
            await execute_query("""
                INSERT INTO rank_history 
                (user_id, chat_id, old_rank, new_rank, changed_by, reason) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, old_rank_value, rank_name, promoted_by, reason_value))
            
            # تحديث في الذاكرة
            if chat_id not in self.user_ranks:
                self.user_ranks[chat_id] = {}
            self.user_ranks[chat_id][user_id] = rank_name
            
            logging.info(f"تم ترقية المستخدم {user_id} للرتبة {rank_name} في المجموعة {chat_id}")
            return True
            
        except Exception as e:
            logging.error(f"خطأ في ترقية المستخدم: {e}")
            return False
    
    async def demote_user(self, user_id: int, chat_id: int, demoted_by: int, reason: Optional[str] = None) -> bool:
        """تخفيض رتبة المستخدم"""
        try:
            # الحصول على الرتبة الحالية
            old_rank = None
            if chat_id in self.user_ranks and user_id in self.user_ranks[chat_id]:
                old_rank = self.user_ranks[chat_id][user_id]
            
            # حذف من قاعدة البيانات
            await execute_query(
                "DELETE FROM user_ranks WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            )
            
            # إضافة للتاريخ
            reason_value = reason if reason is not None else "تخفيض رتبة"
            old_rank_value = old_rank if old_rank is not None else "غير محدد"
            await execute_query("""
                INSERT INTO rank_history 
                (user_id, chat_id, old_rank, new_rank, changed_by, reason) 
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, chat_id, old_rank_value, "عضو عادي", demoted_by, reason_value))
            
            # حذف من الذاكرة
            if chat_id in self.user_ranks and user_id in self.user_ranks[chat_id]:
                del self.user_ranks[chat_id][user_id]
            
            logging.info(f"تم تخفيض رتبة المستخدم {user_id} في المجموعة {chat_id}")
            return True
            
        except Exception as e:
            logging.error(f"خطأ في تخفيض الرتبة: {e}")
            return False
    
    def get_group_ranks(self, chat_id: int, rank_type: Optional[RankType] = None) -> Dict[int, RankInfo]:
        """الحصول على رتب المجموعة"""
        result = {}
        if chat_id in self.user_ranks:
            for user_id, rank_name in self.user_ranks[chat_id].items():
                rank_info = ALL_RANKS.get(rank_name)
                if rank_info and (rank_type is None or rank_info.rank_type == rank_type):
                    result[user_id] = rank_info
        return result
    
    def get_available_ranks(self, rank_type: Optional[RankType] = None) -> Dict[str, RankInfo]:
        """الحصول على الرتب المتاحة"""
        if rank_type is None:
            return ALL_RANKS
        return {name: info for name, info in ALL_RANKS.items() if info.rank_type == rank_type}


# إنشاء مدير الرتب العام
rank_manager = RankManager()
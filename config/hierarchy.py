"""
نظام الهرم الإداري للبوت
Administrative Hierarchy System
"""

import logging
import asyncio
from typing import List, Dict, Optional
from enum import Enum


class AdminLevel(Enum):
    """مستويات الإدارة"""
    MEMBER = 0  # عضو عادي
    MODERATOR = 1  # مشرف
    GROUP_OWNER = 2  # مالك المجموعة
    MASTER = 3  # السيد - صلاحيات مطلقة


# الأسياد - صلاحيات مطلقة في جميع المجموعات
MASTERS = [5524680126, 8278493069, 6629947448, 7988917983, 7155814194]

# مالكي المجموعات (يتم إدارتهم ديناميكياً)
GROUP_OWNERS: Dict[int, List[int]] = {}  # {group_id: [owner_ids]}

# المشرفين (يتم إدارتهم ديناميكياً)
MODERATORS: Dict[int, List[int]] = {}  # {group_id: [moderator_ids]}


def get_user_admin_level(user_id: int, group_id: Optional[int] = None) -> AdminLevel:
    """
    الحصول على مستوى الإدارة للمستخدم في المجموعة المحددة
    
    Args:
        user_id: معرف المستخدم
        group_id: معرف المجموعة (اختياري)
        
    Returns:
        مستوى الإدارة
    """
    try:
        # فحص الأسياد أولاً - لهم صلاحيات مطلقة
        if user_id in MASTERS:
            return AdminLevel.MASTER

        # إذا لم يتم تحديد المجموعة، عضو عادي
        if not group_id:
            return AdminLevel.MEMBER

        # فحص مالكي المجموعات
        if group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]:
            return AdminLevel.GROUP_OWNER

        # فحص المشرفين
        if group_id in MODERATORS and user_id in MODERATORS[group_id]:
            return AdminLevel.MODERATOR

        return AdminLevel.MEMBER

    except Exception as e:
        logging.error(f"خطأ في get_user_admin_level: {e}")
        return AdminLevel.MEMBER


def is_master(user_id: int) -> bool:
    """التحقق من كون المستخدم سيد"""
    return user_id in MASTERS

def is_supreme_master(user_id: int) -> bool:
    """التحقق من أن المستخدم هو السيد الأعلى (الأول) - محمي من جميع الأوامر"""
    return user_id == 5524680126  # السيد الأعلى الوحيد المحمي من جميع الأوامر


async def is_group_owner(user_id: int, group_id: int) -> bool:
    """التحقق من كون المستخدم مالك للمجموعة"""
    return group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]


async def is_moderator(user_id: int, group_id: int) -> bool:
    """التحقق من كون المستخدم مشرف في المجموعة"""
    return group_id in MODERATORS and user_id in MODERATORS[group_id]


def has_permission(user_id: int,
                   required_level: AdminLevel,
                   group_id: Optional[int] = None) -> bool:
    """
    التحقق من امتلاك المستخدم للصلاحية المطلوبة
    
    Args:
        user_id: معرف المستخدم
        required_level: المستوى المطلوب
        group_id: معرف المجموعة
        
    Returns:
        True إذا كان لديه الصلاحية
    """
    user_level = get_user_admin_level(user_id, group_id)
    return user_level.value >= required_level.value


def add_group_owner(group_id: int, user_id: int) -> bool:
    """إضافة مالك جديد للمجموعة"""
    try:
        if group_id not in GROUP_OWNERS:
            GROUP_OWNERS[group_id] = []

        if user_id not in GROUP_OWNERS[group_id]:
            GROUP_OWNERS[group_id].append(user_id)
            logging.info(f"تم إضافة مالك جديد {user_id} للمجموعة {group_id}")

            # حفظ في قاعدة البيانات أيضاً
            asyncio.create_task(
                sync_rank_to_database(user_id, group_id, "مالك"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_group_owner: {e}")
        return False


def remove_group_owner(group_id: int, user_id: int) -> bool:
    """إزالة مالك من المجموعة"""
    try:
        if group_id in GROUP_OWNERS and user_id in GROUP_OWNERS[group_id]:
            GROUP_OWNERS[group_id].remove(user_id)
            if not GROUP_OWNERS[group_id]:
                del GROUP_OWNERS[group_id]
            logging.info(f"تم إزالة المالك {user_id} من المجموعة {group_id}")

            # إزالة من قاعدة البيانات أيضاً
            asyncio.create_task(
                remove_rank_from_database(user_id, group_id, "مالك"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_group_owner: {e}")
        return False


def add_moderator(group_id: int, user_id: int) -> bool:
    """إضافة مشرف جديد للمجموعة"""
    try:
        if group_id not in MODERATORS:
            MODERATORS[group_id] = []

        if user_id not in MODERATORS[group_id]:
            MODERATORS[group_id].append(user_id)
            logging.info(f"تم إضافة مشرف جديد {user_id} للمجموعة {group_id}")

            # حفظ في قاعدة البيانات أيضاً
            asyncio.create_task(
                sync_rank_to_database(user_id, group_id, "مشرف"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في add_moderator: {e}")
        return False


def remove_moderator(group_id: int, user_id: int) -> bool:
    """إزالة مشرف من المجموعة"""
    try:
        if group_id in MODERATORS and user_id in MODERATORS[group_id]:
            MODERATORS[group_id].remove(user_id)
            if not MODERATORS[group_id]:
                del MODERATORS[group_id]
            logging.info(f"تم إزالة المشرف {user_id} من المجموعة {group_id}")

            # إزالة من قاعدة البيانات أيضاً
            asyncio.create_task(
                remove_rank_from_database(user_id, group_id, "مشرف"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في remove_moderator: {e}")
        return False


async def sync_rank_to_database(user_id: int, group_id: int, rank_type: str):
    """مزامنة الرتبة مع قاعدة البيانات"""
    try:
        from database.operations import execute_query
        from datetime import datetime

        await execute_query(
            "INSERT OR REPLACE INTO group_ranks (user_id, chat_id, rank_type, promoted_at) VALUES (?, ?, ?, ?)",
            (user_id, group_id, rank_type, datetime.now().isoformat()))
        logging.info(
            f"تم مزامنة رتبة {rank_type} للمستخدم {user_id} في المجموعة {group_id}"
        )
    except Exception as e:
        logging.error(f"خطأ في مزامنة الرتبة: {e}")


async def remove_rank_from_database(user_id: int, group_id: int,
                                    rank_type: str):
    """إزالة الرتبة من قاعدة البيانات"""
    try:
        from database.operations import execute_query

        await execute_query(
            "DELETE FROM group_ranks WHERE user_id = ? AND chat_id = ? AND rank_type = ?",
            (user_id, group_id, rank_type))
        logging.info(
            f"تم حذف رتبة {rank_type} للمستخدم {user_id} من المجموعة {group_id}"
        )
    except Exception as e:
        logging.error(f"خطأ في حذف الرتبة: {e}")


async def load_ranks_from_database():
    """تحميل الرتب من قاعدة البيانات"""
    try:
        from database.operations import execute_query

        # تحميل المالكين (مالك، مالك اساسي، ادمن)
        owners = await execute_query(
            "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مالك', 'مالك اساسي', 'ادمن')",
            fetch_all=True)

        if owners:
            for owner in owners:
                if isinstance(owner, tuple):
                    user_id = owner[0]
                    chat_id = owner[1]
                elif hasattr(owner, 'get'):
                    user_id = owner.get('user_id')
                    chat_id = owner.get('chat_id')
                else:
                    continue
                
                if user_id is None or chat_id is None:
                    continue

                if chat_id not in GROUP_OWNERS:
                    GROUP_OWNERS[chat_id] = []
                if user_id not in GROUP_OWNERS[chat_id]:
                    GROUP_OWNERS[chat_id].append(user_id)

        # تحميل المشرفين (مشرف، مميز)
        moderators = await execute_query(
            "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مشرف', 'مميز')",
            fetch_all=True)

        if moderators:
            for moderator in moderators:
                if isinstance(moderator, tuple):
                    user_id = moderator[0]
                    chat_id = moderator[1]
                elif hasattr(moderator, 'get'):
                    user_id = moderator.get('user_id')
                    chat_id = moderator.get('chat_id')
                else:
                    continue
                
                if user_id is None or chat_id is None:
                    continue

                if chat_id not in MODERATORS:
                    MODERATORS[chat_id] = []
                if user_id not in MODERATORS[chat_id]:
                    MODERATORS[chat_id].append(user_id)

        logging.info("تم تحميل الرتب من قاعدة البيانات بنجاح")
        logging.info(f"المالكين المحملين: {GROUP_OWNERS}")
        logging.info(f"المشرفين المحملين: {MODERATORS}")
    except Exception as e:
        logging.error(f"خطأ في تحميل الرتب من قاعدة البيانات: {e}")


def get_group_admins(group_id: int) -> Dict[str, List[int]]:
    """الحصول على جميع المديرين في المجموعة"""
    return {
        "masters": MASTERS,
        "owners": GROUP_OWNERS.get(group_id, []),
        "moderators": MODERATORS.get(group_id, [])
    }


def get_admin_level_name(level: AdminLevel) -> str:
    """الحصول على اسم المستوى بالعربية"""
    names = {
        AdminLevel.MEMBER: "عضو عادي",
        AdminLevel.MODERATOR: "مشرف",
        AdminLevel.GROUP_OWNER: "مالك المجموعة",
        AdminLevel.MASTER: "السيد"
    }
    return names.get(level, "غير محدد")


def get_user_permissions(user_id: int, group_id: Optional[int] = None) -> List[str]:
    """الحصول على قائمة بصلاحيات المستخدم"""
    level = get_user_admin_level(user_id, group_id)

    permissions = ["استخدام الأوامر العادية"]

    if level.value >= AdminLevel.MODERATOR.value:
        permissions.extend([
            "إدارة المجموعة الأساسية", "كتم وإلغاء كتم الأعضاء",
            "تحذير الأعضاء"
        ])

    if level.value >= AdminLevel.GROUP_OWNER.value:
        permissions.extend([
            "حظر وإلغاء حظر الأعضاء", "إضافة وإزالة المشرفين",
            "إدارة إعدادات المجموعة", "مسح الرسائل"
        ])

    if level.value >= AdminLevel.MASTER.value:
        permissions.extend([
            "🔴 أوامر السيد المطلقة:", "إعادة تشغيل البوت",
            "التدمير الذاتي للمجموعة", "مغادرة المجموعات",
            "إدارة مالكي المجموعات", "الوصول لجميع الأوامر الإدارية"
        ])

    return permissions

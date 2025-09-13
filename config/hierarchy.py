"""
نظام الهرم الإداري للبوت
Administrative Hierarchy System
"""

import logging
import asyncio
from typing import List, Dict, Optional, Any
from enum import Enum
from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError


class AdminLevel(Enum):
    """مستويات الإدارة"""
    MEMBER = 0  # عضو عادي
    MODERATOR = 1  # مشرف
    GROUP_OWNER = 2  # مالك المجموعة
    MASTER = 3  # السيد - صلاحيات مطلقة
    KING = 4  # الملك - أعلى مستوى في التسلسل الهرمي
    QUEEN = 5  # الملكة - أعلى مستوى في التسلسل الهرمي


# الأسياد - صلاحيات مطلقة في جميع المجموعات
MASTERS = [6524680126, 8278493069, 6629947448, 7988917983, 7155814194, 6154647949, 6770426467]

# الملوك والملكات - أعلى مستوى في التسلسل الهرمي مع امتيازات خاصة
ROYALTY = {
    "KINGS": [6524680126],  # قائمة الملوك - السيد الأعلى ملك دائم
    "QUEENS": [8278493069]  # قائمة الملكات
}

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
        # السيد الأعلى الدائم - له صلاحيات مطلقة دائماً
        if is_supreme_master(user_id):
            # إذا كان ملك أيضاً، أعطه صلاحيات الملك
            if user_id in ROYALTY["KINGS"]:
                return AdminLevel.KING
            # إذا كان ملكة أيضاً، أعطيها صلاحيات الملكة  
            elif user_id in ROYALTY["QUEENS"]:
                return AdminLevel.QUEEN
            else:
                return AdminLevel.MASTER
        
        # فحص الملكات أولاً - أعلى مستوى
        if user_id in ROYALTY["QUEENS"]:
            return AdminLevel.QUEEN
            
        # فحص الملوك - أعلى مستوى
        if user_id in ROYALTY["KINGS"]:
            return AdminLevel.KING

        # فحص الأسياد - صلاحيات مطلقة
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
    # السيد الأعلى دائماً سيد مهما كانت رتبته
    if is_supreme_master(user_id):
        return True
    return user_id in MASTERS

def is_king(user_id: int) -> bool:
    """التحقق من كون المستخدم ملك"""
    return user_id in ROYALTY["KINGS"]

def is_queen(user_id: int) -> bool:
    """التحقق من كون المستخدم ملكة"""
    return user_id in ROYALTY["QUEENS"]

def is_royal(user_id: int) -> bool:
    """التحقق من كون المستخدم من العائلة الملكية"""
    return is_king(user_id) or is_queen(user_id)

def is_supreme_master(user_id: int) -> bool:
    """التحقق من أن المستخدم هو السيد الأعلى (الأول) - محمي من جميع الأوامر"""
    return user_id == 6524680126  # السيد الأعلى الوحيد المحمي من جميع الأوامر


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


async def get_telegram_admin_level(bot: Bot, user_id: int, group_id: int) -> AdminLevel:
    """
    الحصول على مستوى الإدارة للمستخدم من تليجرام API مباشرة
    
    Args:
        bot: كائن البوت
        user_id: معرف المستخدم
        group_id: معرف المجموعة
        
    Returns:
        مستوى الإدارة الفعلي من تليجرام
    """
    try:
        # فحص الأسياد والملوك أولاً (لهم صلاحيات مطلقة)
        if is_supreme_master(user_id):
            if user_id in ROYALTY["KINGS"]:
                return AdminLevel.KING
            elif user_id in ROYALTY["QUEENS"]:
                return AdminLevel.QUEEN
            else:
                return AdminLevel.MASTER
        
        # فحص الملكات والملوك
        if user_id in ROYALTY["QUEENS"]:
            return AdminLevel.QUEEN
        if user_id in ROYALTY["KINGS"]:
            return AdminLevel.KING
        if user_id in MASTERS:
            return AdminLevel.MASTER
        
        # فحص صلاحيات تليجرام الفعلية
        try:
            member = await bot.get_chat_member(group_id, user_id)
            
            # مالك المجموعة
            if member.status == ChatMemberStatus.CREATOR:
                return AdminLevel.GROUP_OWNER
            
            # مشرف مع صلاحيات
            elif member.status == ChatMemberStatus.ADMINISTRATOR:
                return AdminLevel.MODERATOR
                
        except TelegramAPIError as e:
            logging.warning(f"فشل في الحصول على معلومات العضو من تليجرام: {e}")
        
        # عضو عادي
        return AdminLevel.MEMBER
        
    except Exception as e:
        logging.error(f"خطأ في get_telegram_admin_level: {e}")
        return AdminLevel.MEMBER


async def has_telegram_permission(bot: Bot, user_id: int, required_level: AdminLevel, group_id: Optional[int] = None) -> bool:
    """
    التحقق من امتلاك المستخدم للصلاحية المطلوبة باستخدام تليجرام API مع مزامنة تلقائية
    
    Args:
        bot: كائن البوت
        user_id: معرف المستخدم
        required_level: المستوى المطلوب
        group_id: معرف المجموعة
        
    Returns:
        True إذا كان لديه الصلاحية
    """
    try:
        if not group_id:
            # إذا لم تُحدد المجموعة، فحص الصلاحيات العامة فقط
            user_level = get_user_admin_level(user_id)
        else:
            # فحص النظام المحلي أولاً
            local_level = get_user_admin_level(user_id, group_id)
            
            # إذا كان المستخدم ليس أدمن في النظام المحلي، جرب مزامنة الصلاحيات من تليجرام
            if local_level == AdminLevel.MEMBER:
                try:
                    # فحص صلاحيات تليجرام مباشرة
                    member = await bot.get_chat_member(group_id, user_id)
                    if member.status in [ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR]:
                        # المستخدم أدمن في تليجرام لكن ليس في النظام المحلي - نحتاج مزامنة
                        logging.info(f"اكتشاف أدمن جديد في تليجرام - مزامنة المجموعة {group_id}")
                        await sync_telegram_admins_to_local(bot, group_id)
                        # إعادة فحص المستوى بعد المزامنة
                        local_level = get_user_admin_level(user_id, group_id)
                except Exception as sync_error:
                    logging.warning(f"فشل في مزامنة صلاحيات المجموعة {group_id}: {sync_error}")
            
            # فحص الصلاحيات من تليجرام + النظام المحلي
            telegram_level = await get_telegram_admin_level(bot, user_id, group_id)
            
            # أخذ أعلى مستوى من الاثنين
            user_level = max(telegram_level, local_level, key=lambda x: x.value)
        
        return user_level.value >= required_level.value
        
    except Exception as e:
        logging.error(f"خطأ في has_telegram_permission: {e}")
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


async def get_real_telegram_admins(bot: Bot, group_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    الحصول على قائمة المالكين والمشرفين الفعليين من تليجرام
    
    Args:
        bot: كائن البوت
        group_id: معرف المجموعة
        
    Returns:
        قاموس يحتوي على المالكين والمشرفين مع تفاصيلهم
    """
    try:
        admins = await bot.get_chat_administrators(group_id)
        
        owners = []
        moderators = []
        
        for admin in admins:
            user_info = {
                "id": admin.user.id,
                "first_name": admin.user.first_name or "",
                "last_name": admin.user.last_name or "",
                "username": admin.user.username or "",
                "is_bot": admin.user.is_bot
            }
            
            # تجاهل البوتات (عدا البوت نفسه إذا كان أدمن)
            if admin.user.is_bot and admin.user.id != bot.id:
                continue
                
            if admin.status == ChatMemberStatus.CREATOR:
                owners.append(user_info)
            elif admin.status == ChatMemberStatus.ADMINISTRATOR:
                moderators.append(user_info)
        
        return {
            "owners": owners,
            "moderators": moderators
        }
        
    except Exception as e:
        logging.error(f"خطأ في الحصول على أدمن تليجرام للمجموعة {group_id}: {e}")
        return {"owners": [], "moderators": []}


async def sync_telegram_admins_to_local(bot: Bot, group_id: int) -> None:
    """
    مزامنة أدمن تليجرام مع النظام المحلي
    
    Args:
        bot: كائن البوت
        group_id: معرف المجموعة
    """
    try:
        # الحصول على قائمة الأدمن من تليجرام
        admins = await bot.get_chat_administrators(group_id)
        
        # مسح الأدمن السابقين لهذه المجموعة من النظام المحلي
        if group_id in GROUP_OWNERS:
            GROUP_OWNERS[group_id].clear()
        else:
            GROUP_OWNERS[group_id] = []
            
        if group_id in MODERATORS:
            MODERATORS[group_id].clear()
        else:
            MODERATORS[group_id] = []
        
        # إضافة الأدمن الجدد
        for admin in admins:
            user_id = admin.user.id
            
            # تجاهل البوتات (عدا البوت نفسه إذا كان أدمن)
            if admin.user.is_bot and user_id != bot.id:
                continue
                
            if admin.status == ChatMemberStatus.CREATOR:
                # مالك المجموعة
                GROUP_OWNERS[group_id].append(user_id)
                # حفظ في قاعدة البيانات
                await sync_rank_to_database(user_id, group_id, "مالك")
                logging.info(f"تم تحديد مالك المجموعة {group_id}: {user_id}")
                
            elif admin.status == ChatMemberStatus.ADMINISTRATOR:
                # مشرف
                MODERATORS[group_id].append(user_id)
                # حفظ في قاعدة البيانات
                await sync_rank_to_database(user_id, group_id, "مشرف")
                logging.info(f"تم تحديد مشرف في المجموعة {group_id}: {user_id}")
        
        logging.info(f"تم تحديث صلاحيات المجموعة {group_id} من تليجرام")
        logging.info(f"المالكون: {GROUP_OWNERS.get(group_id, [])}")
        logging.info(f"المشرفون: {MODERATORS.get(group_id, [])}")
        
    except Exception as e:
        logging.error(f"خطأ في مزامنة أدمن تليجرام للمجموعة {group_id}: {e}")


async def load_ranks_from_database():
    """تحميل الرتب من قاعدة البيانات"""
    try:
        from database.operations import execute_query

        # مسح القواميس أولاً لضمان التحديث الصحيح
        GROUP_OWNERS.clear()
        MODERATORS.clear()
        
        # تحميل المالكين (مالك، مالك اساسي، ادمن)
        owners = await execute_query(
            "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مالك', 'مالك اساسي', 'ادمن')",
            fetch_all=True)

        owners_count = 0
        if owners and isinstance(owners, (list, tuple)):
            for owner in owners:
                user_id = None
                chat_id = None
                
                if isinstance(owner, tuple) and len(owner) >= 2:
                    user_id = owner[0]
                    chat_id = owner[1]
                elif hasattr(owner, 'get') and callable(getattr(owner, 'get')):
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
                    owners_count += 1

        # تحميل المشرفين (مشرف، مميز)
        moderators = await execute_query(
            "SELECT user_id, chat_id FROM group_ranks WHERE rank_type IN ('مشرف', 'مميز')",
            fetch_all=True)

        moderators_count = 0
        if moderators and isinstance(moderators, (list, tuple)):
            for moderator in moderators:
                user_id = None
                chat_id = None
                
                if isinstance(moderator, tuple) and len(moderator) >= 2:
                    user_id = moderator[0]
                    chat_id = moderator[1]
                elif hasattr(moderator, 'get') and callable(getattr(moderator, 'get')):
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
                    moderators_count += 1

        logging.info("تم تحميل الرتب من قاعدة البيانات بنجاح")
        logging.info(f"تم تحميل {owners_count} مالك في {len(GROUP_OWNERS)} مجموعة")
        logging.info(f"تم تحميل {moderators_count} مشرف في {len(MODERATORS)} مجموعة")
        logging.info(f"المالكين المحملين: {GROUP_OWNERS}")
        logging.info(f"المشرفين المحملين: {MODERATORS}")
    except Exception as e:
        logging.error(f"خطأ في تحميل الرتب من قاعدة البيانات: {e}")
        import traceback
        logging.error(f"تفاصيل الخطأ: {traceback.format_exc()}")


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
        AdminLevel.MASTER: "السيد",
        AdminLevel.KING: "الملك",
        AdminLevel.QUEEN: "الملكة"
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
        
    if level.value >= AdminLevel.KING.value:
        permissions.extend([
            "👑 امتيازات الملك الحصرية:", "ترقية وتنزيل الأسياد",
            "إدارة العائلة الملكية", "زواج ملكي مجاني", "حفلات زفاف أسطورية",
            "امتيازات اقتصادية خاصة", "صلاحيات مطلقة في جميع الأنظمة"
        ])
    
    if level.value >= AdminLevel.QUEEN.value:
        permissions.extend([
            "👸 امتيازات الملكة الحصرية:", "ترقية وتنزيل الأسياد", 
            "إدارة العائلة الملكية", "زواج ملكي مجاني", "حفلات زفاف أسطورية",
            "امتيازات اقتصادية خاصة", "صلاحيات مطلقة في جميع الأنظمة"
        ])

    return permissions


def promote_to_king(user_id: int) -> bool:
    """ترقية مستخدم إلى ملك"""
    try:
        if user_id not in ROYALTY["KINGS"]:
            ROYALTY["KINGS"].append(user_id)
            # إزالة من قوائم أخرى إذا كان موجود
            if user_id in ROYALTY["QUEENS"]:
                ROYALTY["QUEENS"].remove(user_id)
            # لا نزيل السيد الأعلى من قائمة الأسياد أبداً
            if user_id in MASTERS and not is_supreme_master(user_id):
                MASTERS.remove(user_id)
            
            logging.info(f"تم ترقية المستخدم {user_id} إلى ملك")
            # حفظ في قاعدة البيانات
            asyncio.create_task(
                sync_rank_to_database(user_id, 0, "ملك"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في promote_to_king: {e}")
        return False


def promote_to_queen(user_id: int) -> bool:
    """ترقية مستخدم إلى ملكة"""
    try:
        if user_id not in ROYALTY["QUEENS"]:
            ROYALTY["QUEENS"].append(user_id)
            # إزالة من قوائم أخرى إذا كان موجود
            if user_id in ROYALTY["KINGS"]:
                ROYALTY["KINGS"].remove(user_id)
            if user_id in MASTERS:
                MASTERS.remove(user_id)
            
            logging.info(f"تم ترقية المستخدم {user_id} إلى ملكة")
            # حفظ في قاعدة البيانات
            asyncio.create_task(
                sync_rank_to_database(user_id, 0, "ملكة"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في promote_to_queen: {e}")
        return False


def demote_from_royalty(user_id: int) -> bool:
    """تنزيل مستخدم من المستوى الملكي"""
    try:
        removed = False
        if user_id in ROYALTY["KINGS"]:
            ROYALTY["KINGS"].remove(user_id)
            removed = True
        if user_id in ROYALTY["QUEENS"]:
            ROYALTY["QUEENS"].remove(user_id)
            removed = True
        
        if removed:
            # إعادة إضافة إلى قائمة الأسياد
            if user_id not in MASTERS:
                MASTERS.append(user_id)
            
            logging.info(f"تم تنزيل المستخدم {user_id} من المستوى الملكي")
            # إزالة من قاعدة البيانات
            asyncio.create_task(
                remove_rank_from_database(user_id, 0, "ملك"))
            asyncio.create_task(
                remove_rank_from_database(user_id, 0, "ملكة"))
            return True
        return False
    except Exception as e:
        logging.error(f"خطأ في demote_from_royalty: {e}")
        return False

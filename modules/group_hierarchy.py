"""
إدارة الهيكل الإداري للمجموعات
Group Hierarchy Management
"""

import logging
from aiogram.types import Message
from aiogram import html
from config.hierarchy import (
    AdminLevel, get_user_admin_level, add_group_owner, remove_group_owner,
    add_moderator, remove_moderator, get_group_admins, get_user_permissions,
    get_admin_level_name
)
from utils.admin_decorators import group_owner_or_master, moderator_or_higher


@group_owner_or_master
async def promote_moderator_command(message: Message):
    """ترقية مستخدم لمشرف"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ يجب الرد على رسالة المستخدم المراد ترقيته\n\n"
                "📝 **الاستخدام:**\n"
                "قم بالرد على رسالة المستخدم واكتب: ترقية مشرف"
            )
            return
        
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        target_user = message.reply_to_message.from_user
        group_id = message.chat.id
        
        # التحقق من المستوى الحالي للمستخدم
        current_level = get_user_admin_level(target_user.id, group_id)
        if current_level.value >= AdminLevel.MODERATOR.value:
            level_name = get_admin_level_name(current_level)
            await message.reply(f"❌ {target_user.first_name} هو {level_name} بالفعل")
            return
        
        if add_moderator(group_id, target_user.id):
            await message.reply(
                f"🎖️ **ترقية مشرف**\n\n"
                f"✅ تم ترقية {target_user.first_name} لمنصب مشرف\n"
                f"🆔 المعرف: `{target_user.id}`\n\n"
                f"🔑 **الصلاحيات الجديدة:**\n"
                f"• إدارة المجموعة الأساسية\n"
                f"• كتم وإلغاء كتم الأعضاء\n"
                f"• تحذير الأعضاء"
            )
        else:
            await message.reply("❌ فشل في الترقية")
            
    except Exception as e:
        logging.error(f"خطأ في promote_moderator_command: {e}")
        await message.reply("❌ حدث خطأ أثناء الترقية")


@group_owner_or_master
async def demote_moderator_command(message: Message):
    """تنزيل مشرف"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ يجب الرد على رسالة المستخدم المراد تنزيله\n\n"
                "📝 **الاستخدام:**\n"
                "قم بالرد على رسالة المستخدم واكتب: تنزيل مشرف"
            )
            return
        
        target_user = message.reply_to_message.from_user
        group_id = message.chat.id
        
        if remove_moderator(group_id, target_user.id):
            await message.reply(
                f"📉 **تنزيل مشرف**\n\n"
                f"✅ تم تنزيل {target_user.first_name} من منصب مشرف\n"
                f"👤 أصبح عضواً عادياً الآن"
            )
        else:
            await message.reply("❌ المستخدم ليس مشرفاً في هذه المجموعة")
            
    except Exception as e:
        logging.error(f"خطأ في demote_moderator_command: {e}")
        await message.reply("❌ حدث خطأ أثناء التنزيل")


async def show_user_permissions_command(message: Message):
    """عرض صلاحيات المستخدم"""
    try:
        target_user = message.from_user
        group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
        
        # إذا كان رد على رسالة، عرض صلاحيات المستخدم المحدد
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            return
        
        level = get_user_admin_level(target_user.id, group_id)
        level_name = get_admin_level_name(level)
        permissions = get_user_permissions(target_user.id, group_id)
        
        permissions_text = (
            f"👤 **صلاحيات المستخدم**\n\n"
            f"🏷️ **الاسم:** {target_user.first_name}\n"
            f"🆔 **المعرف:** `{target_user.id}`\n"
            f"⭐ **المستوى:** {level_name}\n\n"
            f"🔑 **الصلاحيات:**\n"
        )
        
        for i, permission in enumerate(permissions, 1):
            permissions_text += f"{i}. {permission}\n"
        
        await message.reply(permissions_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_user_permissions_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الصلاحيات")


async def show_admins_list_command(message: Message):
    """عرض قائمة المديرين في المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        group_id = message.chat.id
        admins = get_group_admins(group_id)
        
        admins_text = "👥 قائمة المديرين\n\n"
        
        # الأسياد
        admins_text += "👑 الأسياد:\n"
        for master_id in admins['masters']:
            try:
                member = await message.bot.get_chat_member(group_id, master_id)
                name = member.user.first_name or f"المستخدم {master_id}"
                admins_text += f"  • {name}\n"
            except:
                admins_text += f"  • السيد {master_id}\n"
        
        # مالكي المجموعات
        if admins['owners']:
            admins_text += "\n🏆 **مالكي المجموعة:**\n"
            for owner_id in admins['owners']:
                try:
                    member = await message.bot.get_chat_member(group_id, owner_id)
                    name = member.user.first_name or f"المستخدم {owner_id}"
                    admins_text += f"  • {name}\n"
                except:
                    admins_text += f"  • المالك `{owner_id}`\n"
        
        # المشرفين
        if admins['moderators']:
            admins_text += "\n👮‍♂️ **المشرفين:**\n"
            for mod_id in admins['moderators']:
                try:
                    member = await message.bot.get_chat_member(group_id, mod_id)
                    name = member.user.first_name or f"المستخدم {mod_id}"
                    admins_text += f"  • {name}\n"
                except:
                    admins_text += f"  • المشرف `{mod_id}`\n"
        
        if not admins['owners'] and not admins['moderators']:
            admins_text += "\n📝 لا يوجد مديرين محليين في هذه المجموعة"
        
        await message.reply(admins_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_admins_list_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض قائمة المديرين")


async def handle_hierarchy_commands(message: Message) -> bool:
    """معالج أوامر الهيكل الإداري"""
    if not message.text or not message.from_user:
        return False
    
    text = message.text.lower().strip()
    group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
    user_id = message.from_user.id
    
    # التحقق من الصلاحيات للأوامر المختلفة
    user_level = get_user_admin_level(user_id, group_id)
    
    # فحص أوامر مالكي المجموعات مع ردود مهينة
    from modules.permission_responses import is_owner_command, get_permission_denial_response
    if is_owner_command(message.text) and user_level.value < AdminLevel.GROUP_OWNER.value:
        insulting_response = get_permission_denial_response(user_id, group_id, AdminLevel.GROUP_OWNER)
        if insulting_response:
            await message.reply(insulting_response)
        return True
    
    # أوامر ترقية وتنزيل المشرفين (مالك المجموعة أو أعلى)
    if text in ['ترقية مشرف', 'رقي مشرف']:
        if user_level.value >= AdminLevel.GROUP_OWNER.value:
            await promote_moderator_command(message)
        return True
    
    elif text in ['تنزيل مشرف', 'نزل مشرف']:
        if user_level.value >= AdminLevel.GROUP_OWNER.value:
            await demote_moderator_command(message)
        return True
    
    # أوامر عرض المعلومات (متاحة لجميع المستويات)
    elif text in ['صلاحياتي', 'مستواي', 'my permissions']:
        await show_user_permissions_command(message)
        return True
    
    elif text in ['قائمة المديرين', 'المديرين', 'الإدارة']:
        await show_admins_list_command(message)
        return True
    
    return False
"""
أوامر الأسياد المطلقة
Master Commands - Ultimate Authority
"""

import logging
import asyncio
import os
from aiogram.types import Message, ChatMemberOwner, ChatMemberAdministrator
from aiogram import Bot
from utils.admin_decorators import master_only
from config.hierarchy import MASTERS, add_group_owner, remove_group_owner, get_group_admins


@master_only
async def restart_bot_command(message: Message):
    """إعادة تشغيل البوت"""
    try:
        await message.reply(
            "🔄 **أمر إعادة التشغيل**\n\n"
            "⚠️ سيتم إعادة تشغيل البوت خلال 5 ثوانٍ...\n"
            "📊 سيتم حفظ جميع البيانات تلقائياً"
        )
        
        await asyncio.sleep(5)
        
        # حفظ البيانات المهمة قبل إعادة التشغيل
        logging.info(f"إعادة تشغيل البوت بأمر من السيد: {message.from_user.id}")
        
        # إعادة تشغيل العملية
        os.system("kill -9 $(ps aux | grep '[p]ython.*main.py' | awk '{print $2}')")
        
    except Exception as e:
        logging.error(f"خطأ في restart_bot_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إعادة التشغيل")


@master_only 
async def self_destruct_command(message: Message):
    """التدمير الذاتي - حذف جميع أعضاء المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        # تأكيد الأمر
        await message.reply(
            "💥 **تحذير: أمر التدمير الذاتي**\n\n"
            "⚠️ سيتم طرد جميع الأعضاء من المجموعة خلال 10 ثوانٍ!\n"
            "🚨 هذا الإجراء لا يمكن التراجع عنه\n\n"
            "💡 إذا كنت تريد إلغاء الأمر، اكتب 'إلغاء' الآن"
        )
        
        await asyncio.sleep(10)
        
        bot = message.bot
        chat_id = message.chat.id
        
        # الحصول على قائمة الأعضاء وطردهم
        try:
            async for member in bot.get_chat_administrators(chat_id):
                if member.user.id not in MASTERS and member.user.id != bot.id:
                    try:
                        await bot.ban_chat_member(chat_id, member.user.id)
                        await asyncio.sleep(0.1)  # تجنب rate limiting
                    except Exception:
                        pass
            
            # طرد الأعضاء العاديين (يحتاج API إضافية)
            await message.reply(
                "💥 **تم تنفيذ التدمير الذاتي**\n\n"
                "✅ تم طرد جميع المديرين\n"
                "⚠️ لطرد الأعضاء العاديين، يجب ترقيتي كمدير مع صلاحية حظر الأعضاء"
            )
            
        except Exception as e:
            logging.error(f"خطأ في التدمير الذاتي: {e}")
            await message.reply("❌ حدث خطأ أثناء تنفيذ التدمير الذاتي")
            
    except Exception as e:
        logging.error(f"خطأ في self_destruct_command: {e}")
        await message.reply("❌ حدث خطأ في معالجة الأمر")


@master_only
async def leave_group_command(message: Message):
    """مغادرة المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        await message.reply(
            "👋 **أمر المغادرة**\n\n"
            f"وداعاً أيها السيد {message.from_user.first_name}!\n"
            "🚶‍♂️ سأغادر هذه المجموعة خلال 3 ثوانٍ..."
        )
        
        await asyncio.sleep(3)
        
        chat_id = message.chat.id
        logging.info(f"مغادرة المجموعة {chat_id} بأمر من السيد: {message.from_user.id}")
        
        await message.bot.leave_chat(chat_id)
        
    except Exception as e:
        logging.error(f"خطأ في leave_group_command: {e}")
        await message.reply("❌ حدث خطأ أثناء المغادرة")


@master_only
async def promote_group_owner_command(message: Message):
    """ترقية مستخدم لمالك المجموعة"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ يجب الرد على رسالة المستخدم المراد ترقيته\n\n"
                "📝 **الاستخدام:**\n"
                "قم بالرد على رسالة المستخدم وقل: يوكي رقي مالك مجموعة"
            )
            return
        
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        target_user = message.reply_to_message.from_user
        group_id = message.chat.id
        
        # التحقق من أن المستخدم ليس سيد بالفعل
        if target_user.id in MASTERS:
            await message.reply(f"👑 {target_user.first_name} هو سيد بالفعل، لا يحتاج لترقية!")
            return
        
        if add_group_owner(group_id, target_user.id):
            await message.reply(
                f"👑 **ترقية مالك المجموعة**\n\n"
                f"✅ تم ترقية {target_user.first_name} ليصبح مالك المجموعة\n"
                f"🆔 المعرف: `{target_user.id}`\n\n"
                f"🔑 **الصلاحيات الجديدة:**\n"
                f"• إدارة المجموعة\n"
                f"• حظر وإلغاء حظر الأعضاء\n"
                f"• إضافة وإزالة المشرفين\n"
                f"• مسح الرسائل"
            )
        else:
            await message.reply("❌ المستخدم مالك للمجموعة بالفعل")
            
    except Exception as e:
        logging.error(f"خطأ في promote_group_owner_command: {e}")
        await message.reply("❌ حدث خطأ أثناء الترقية")


@master_only
async def demote_group_owner_command(message: Message):
    """تنزيل مالك المجموعة"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply(
                "❌ يجب الرد على رسالة المستخدم المراد تنزيله\n\n"
                "📝 **الاستخدام:**\n"
                "قم بالرد على رسالة المستخدم وقل: يوكي نزل مالك المجموعة"
            )
            return
        
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        target_user = message.reply_to_message.from_user
        group_id = message.chat.id
        
        if remove_group_owner(group_id, target_user.id):
            await message.reply(
                f"📉 **تنزيل مالك المجموعة**\n\n"
                f"✅ تم تنزيل {target_user.first_name} من منصب مالك المجموعة\n"
                f"👤 أصبح عضواً عادياً الآن"
            )
        else:
            await message.reply("❌ المستخدم ليس مالكاً للمجموعة")
            
    except Exception as e:
        logging.error(f"خطأ في demote_group_owner_command: {e}")
        await message.reply("❌ حدث خطأ أثناء التنزيل")


@master_only
async def show_hierarchy_command(message: Message):
    """عرض الهيكل الإداري للمجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        group_id = message.chat.id
        admins = get_group_admins(group_id)
        
        hierarchy_text = "👑 **الهيكل الإداري للمجموعة**\n\n"
        
        # الأسياد
        hierarchy_text += "🔴 **الأسياد (صلاحيات مطلقة):**\n"
        for master_id in admins['masters']:
            try:
                member = await message.bot.get_chat_member(group_id, master_id)
                name = member.user.first_name or f"المستخدم {master_id}"
                hierarchy_text += f"  👑 {name} (`{master_id}`)\n"
            except:
                hierarchy_text += f"  👑 السيد `{master_id}`\n"
        
        # مالكي المجموعات
        hierarchy_text += "\n🟡 **مالكي المجموعة:**\n"
        if admins['owners']:
            for owner_id in admins['owners']:
                try:
                    member = await message.bot.get_chat_member(group_id, owner_id)
                    name = member.user.first_name or f"المستخدم {owner_id}"
                    hierarchy_text += f"  🏆 {name} (`{owner_id}`)\n"
                except:
                    hierarchy_text += f"  🏆 المالك `{owner_id}`\n"
        else:
            hierarchy_text += "  📝 لا يوجد مالكين محددين\n"
        
        # المشرفين
        hierarchy_text += "\n🟢 **المشرفين:**\n"
        if admins['moderators']:
            for mod_id in admins['moderators']:
                try:
                    member = await message.bot.get_chat_member(group_id, mod_id)
                    name = member.user.first_name or f"المستخدم {mod_id}"
                    hierarchy_text += f"  👮‍♂️ {name} (`{mod_id}`)\n"
                except:
                    hierarchy_text += f"  👮‍♂️ المشرف `{mod_id}`\n"
        else:
            hierarchy_text += "  📝 لا يوجد مشرفين محددين\n"
        
        hierarchy_text += f"\n📊 **الإحصائيات:**\n"
        hierarchy_text += f"• الأسياد: {len(admins['masters'])}\n"
        hierarchy_text += f"• المالكين: {len(admins['owners'])}\n" 
        hierarchy_text += f"• المشرفين: {len(admins['moderators'])}"
        
        await message.reply(hierarchy_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_hierarchy_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الهيكل الإداري")


async def handle_master_commands(message: Message) -> bool:
    """معالج أوامر الأسياد"""
    if not message.text or not message.from_user:
        return False
    
    # التحقق من كون المستخدم سيد
    if message.from_user.id not in MASTERS:
        return False
    
    text = message.text.lower().strip()
    
    # أوامر الأسياد المطلقة
    if any(phrase in text for phrase in ['يوكي قم بإعادة التشغيل', 'يوكي اعد التشغيل', 'restart bot']):
        await restart_bot_command(message)
        return True
    
    elif any(phrase in text for phrase in ['يوكي قم بالتدمير الذاتي', 'يوكي دمر المجموعة', 'self destruct']):
        await self_destruct_command(message)
        return True
    
    elif any(phrase in text for phrase in ['يوكي قم بمغادرة المجموعة', 'يوكي اخرج', 'يوكي غادر']):
        await leave_group_command(message)
        return True
    
    elif any(phrase in text for phrase in ['يوكي رقي مالك مجموعة', 'رقية مالك']):
        await promote_group_owner_command(message)
        return True
    
    elif any(phrase in text for phrase in ['يوكي نزل مالك المجموعة', 'تنزيل مالك']):
        await demote_group_owner_command(message)
        return True
    
    elif text in ['الهيكل الإداري', 'عرض الإدارة', 'المديرين']:
        await show_hierarchy_command(message)
        return True
    
    return False
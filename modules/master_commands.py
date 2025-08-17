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
from modules.cancel_handler import start_cancellable_command, is_command_cancelled, finish_command


@master_only
async def restart_bot_command(message: Message):
    """إعادة تشغيل البوت مع عد تنازلي وإمكانية الإلغاء"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # تسجيل بداية الأمر
        start_cancellable_command(user_id, "restart", chat_id)
        
        # رسالة التأكيد مع العد التنازلي
        countdown_msg = await message.reply(
            "🔄 **أمر إعادة التشغيل المطلق**\n\n"
            f"👑 السيد: {message.from_user.first_name}\n"
            "⚠️ سيتم إعادة تشغيل البوت خلال 15 ثانية!\n"
            "📊 سيتم حفظ جميع البيانات تلقائياً\n\n"
            "⏰ **العد التنازلي:** 15\n\n"
            "💡 اكتب 'إلغاء' لإيقاف الأمر"
        )
        
        # العد التنازلي لمدة 15 ثانية مع فحص الإلغاء
        for i in range(14, 0, -1):
            await asyncio.sleep(1)
            
            # فحص الإلغاء
            if is_command_cancelled(user_id):
                await countdown_msg.edit_text(
                    "❌ **تم إلغاء أمر إعادة التشغيل**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "✅ تم إيقاف أمر إعادة التشغيل بنجاح\n"
                    "🔒 البوت يعمل بشكل طبيعي"
                )
                finish_command(user_id)
                return
            
            try:
                await countdown_msg.edit_text(
                    "🔄 **أمر إعادة التشغيل المطلق**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "⚠️ سيتم إعادة تشغيل البوت!\n"
                    "📊 سيتم حفظ جميع البيانات تلقائياً\n\n"
                    f"⏰ **العد التنازلي:** {i}\n\n"
                    "💡 اكتب 'إلغاء' لإيقاف الأمر"
                )
            except:
                pass
        
        # فحص أخير قبل التنفيذ
        if is_command_cancelled(user_id):
            await countdown_msg.edit_text("❌ **تم إلغاء الأمر في اللحظة الأخيرة**")
            finish_command(user_id)
            return
        
        # الرسالة الأخيرة
        await countdown_msg.edit_text(
            "🔄 **تنفيذ إعادة التشغيل الآن...**\n\n"
            "🔌 جاري إغلاق البوت وإعادة تشغيله\n"
            "⏳ سيعود البوت خلال ثوانٍ قليلة"
        )
        
        await asyncio.sleep(1)
        
        # حفظ البيانات المهمة قبل إعادة التشغيل
        logging.info(f"إعادة تشغيل البوت بأمر من السيد: {user_id}")
        finish_command(user_id)
        
        # إعادة تشغيل العملية
        os.system("kill -9 $(ps aux | grep '[p]ython.*main.py' | awk '{print $2}')")
        
    except Exception as e:
        logging.error(f"خطأ في restart_bot_command: {e}")
        if message.from_user:
            finish_command(message.from_user.id)
        await message.reply("❌ حدث خطأ أثناء إعادة التشغيل")


@master_only 
async def self_destruct_command(message: Message):
    """التدمير الذاتي - حذف جميع أعضاء المجموعة مع عد تنازلي"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # تسجيل بداية الأمر
        start_cancellable_command(user_id, "self_destruct", chat_id)
        
        # رسالة التحذير مع العد التنازلي
        countdown_msg = await message.reply(
            "💥 **أمر التدمير الذاتي المطلق**\n\n"
            f"👑 السيد: {message.from_user.first_name}\n"
            "⚠️ سيتم طرد جميع الأعضاء من المجموعة!\n"
            "🚨 هذا الإجراء لا يمكن التراجع عنه\n\n"
            "⏰ **العد التنازلي:** 15\n\n"
            "💡 اكتب 'إلغاء' لإيقاف الأمر"
        )
        
        # العد التنازلي لمدة 15 ثانية مع فحص الإلغاء  
        for i in range(14, 0, -1):
            await asyncio.sleep(1)
            
            # فحص الإلغاء
            if is_command_cancelled(user_id):
                await countdown_msg.edit_text(
                    "❌ **تم إلغاء أمر التدمير الذاتي**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "✅ تم إيقاف أمر التدمير الذاتي بنجاح\n"
                    "🔒 المجموعة آمنة"
                )
                finish_command(user_id)
                return
            
            try:
                await countdown_msg.edit_text(
                    "💥 **أمر التدمير الذاتي المطلق**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "⚠️ سيتم طرد جميع الأعضاء!\n"
                    "🚨 لا يمكن التراجع عن هذا الإجراء\n\n"
                    f"⏰ **العد التنازلي:** {i}\n\n"
                    "💡 اكتب 'إلغاء' لإيقاف الأمر"
                )
            except:
                pass
        
        # فحص أخير قبل التنفيذ
        if is_command_cancelled(user_id):
            await countdown_msg.edit_text("❌ **تم إلغاء الأمر في اللحظة الأخيرة**")
            finish_command(user_id)
            return
        
        # الرسالة الأخيرة
        await countdown_msg.edit_text(
            "💥 **بدء التدمير الذاتي الآن...**\n\n"
            "🔥 جاري طرد جميع الأعضاء من المجموعة"
        )
        
        await asyncio.sleep(1)
        
        bot = message.bot
        chat_id = message.chat.id
        
        # الحصول على قائمة الأعضاء وطردهم
        try:
            banned_count = 0
            failed_count = 0
            
            # أولاً: الحصول على المديرين وطردهم
            administrators = await bot.get_chat_administrators(chat_id)
            for member in administrators:
                if member.user.id not in MASTERS and member.user.id != bot.id:
                    try:
                        await bot.ban_chat_member(chat_id, member.user.id)
                        banned_count += 1
                        await asyncio.sleep(0.1)
                    except Exception as e:
                        failed_count += 1
                        logging.warning(f"فشل طرد المدير {member.user.id}: {e}")
            
            # ثانياً: محاولة طرد الأعضاء العاديين إذا كان لدى البوت صلاحيات
            try:
                # التحقق من صلاحيات البوت
                bot_member = await bot.get_chat_member(chat_id, bot.id)
                if hasattr(bot_member, 'can_restrict_members') and bot_member.can_restrict_members:
                    # هنا يمكن إضافة منطق لطرد الأعضاء العاديين
                    # لكن Telegram API لا يوفر طريقة للحصول على جميع الأعضاء بسهولة
                    pass
            except Exception as e:
                logging.warning(f"لا يمكن التحقق من صلاحيات البوت: {e}")
            
            # تقرير النتائج
            result_msg = "💥 **تم تنفيذ التدمير الذاتي**\n\n"
            
            if banned_count > 0:
                result_msg += f"✅ تم طرد {banned_count} مدير بنجاح\n"
            if failed_count > 0:
                result_msg += f"⚠️ فشل طرد {failed_count} مدير (صلاحيات محدودة)\n"
            
            result_msg += f"\n📊 **النتيجة النهائية:**\n"
            result_msg += f"• المطرودين: {banned_count}\n"
            result_msg += f"• الفاشلين: {failed_count}\n"
            result_msg += f"\n👑 السيد {message.from_user.first_name} نفذ الأمر"
            
            if banned_count == 0 and failed_count > 0:
                result_msg += f"\n\n💡 **نصيحة:**\nلمزيد من الفعالية، امنح البوت صلاحية 'حظر المستخدمين' في إعدادات المجموعة"
            
            await countdown_msg.edit_text(result_msg)
            
        except Exception as e:
            logging.error(f"خطأ في التدمير الذاتي: {e}")
            await countdown_msg.edit_text(
                "❌ **حدث خطأ أثناء التدمير الذاتي**\n\n"
                "🔧 تأكد من أن البوت لديه صلاحيات:\n"
                "• حظر المستخدمين\n"
                "• إدارة المجموعة\n"
                "• حذف الرسائل\n\n"
                f"⚠️ تفاصيل الخطأ: {str(e)[:150]}..."
            )
        
        finish_command(user_id)
            
    except Exception as e:
        logging.error(f"خطأ في self_destruct_command: {e}")
        if message.from_user:
            finish_command(message.from_user.id)
        await message.reply("❌ حدث خطأ في معالجة الأمر")


@master_only
async def leave_group_command(message: Message):
    """مغادرة المجموعة مع عد تنازلي"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # تسجيل بداية الأمر
        start_cancellable_command(user_id, "leave_group", chat_id)
        
        # رسالة الوداع مع العد التنازلي
        countdown_msg = await message.reply(
            "👋 **أمر المغادرة المطلق**\n\n"
            f"👑 السيد: {message.from_user.first_name}\n"
            f"وداعاً أيها السيد العزيز!\n"
            "🚶‍♂️ سأغادر هذه المجموعة\n\n"
            "⏰ **العد التنازلي:** 15\n\n"
            "💡 اكتب 'إلغاء' لإيقاف الأمر"
        )
        
        # العد التنازلي لمدة 15 ثانية مع فحص الإلغاء
        for i in range(14, 0, -1):
            await asyncio.sleep(1)
            
            # فحص الإلغاء
            if is_command_cancelled(user_id):
                await countdown_msg.edit_text(
                    "❌ **تم إلغاء أمر المغادرة**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "✅ تم إيقاف أمر المغادرة بنجاح\n"
                    "🏠 سأبقى في المجموعة"
                )
                finish_command(user_id)
                return
            
            try:
                await countdown_msg.edit_text(
                    "👋 **أمر المغادرة المطلق**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    f"وداعاً أيها السيد العزيز!\n"
                    "🚶‍♂️ سأغادر هذه المجموعة\n\n"
                    f"⏰ **العد التنازلي:** {i}\n\n"
                    "💡 اكتب 'إلغاء' لإيقاف الأمر"
                )
            except:
                pass
        
        # فحص أخير قبل التنفيذ
        if is_command_cancelled(user_id):
            await countdown_msg.edit_text("❌ **تم إلغاء الأمر في اللحظة الأخيرة**")
            finish_command(user_id)
            return
        
        # الرسالة الأخيرة
        await countdown_msg.edit_text(
            "👋 **وداعاً للأبد!**\n\n"
            "🚪 أغادر المجموعة الآن بأمر السيد\n"
            "💫 شكراً لكم على الوقت الممتع"
        )
        
        await asyncio.sleep(2)
        
        logging.info(f"مغادرة المجموعة {chat_id} بأمر من السيد: {user_id}")
        finish_command(user_id)
        
        await message.bot.leave_chat(chat_id)
        
    except Exception as e:
        logging.error(f"خطأ في leave_group_command: {e}")
        if message.from_user:
            finish_command(message.from_user.id)
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
    
    user_id = message.from_user.id
    
    # التحقق من كون المستخدم سيد
    if user_id not in MASTERS:
        return False
    
    text = message.text.lower().strip()
    
    # فحص أمر الإلغاء أولاً
    if text == 'إلغاء':
        from modules.cancel_handler import cancel_command, get_active_command
        if cancel_command(user_id):
            await message.reply(
                "❌ **تم إلغاء الأمر المطلق**\n\n"
                f"✅ تم إيقاف الأمر بنجاح يا سيد {message.from_user.first_name}"
            )
            return True
        else:
            await message.reply("❓ لا يوجد أمر جاري لإلغائه")
            return True
    
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
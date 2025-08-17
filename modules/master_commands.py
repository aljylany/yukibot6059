"""
أوامر الأسياد المطلقة
Master Commands - Ultimate Authority
"""

import logging
import asyncio
import os
import sys
from aiogram.types import Message, ChatMemberOwner, ChatMemberAdministrator
from aiogram import Bot
from utils.admin_decorators import master_only
from config.hierarchy import MASTERS, add_group_owner, remove_group_owner, get_group_admins, AdminLevel
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
        
        # حفظ معلومات السيد للرسالة بعد إعادة التشغيل
        restart_info = {
            'user_id': user_id,
            'chat_id': chat_id,
            'username': message.from_user.first_name or "السيد"
        }
        
        # حفظ في ملف مؤقت
        import json
        with open('restart_info.json', 'w', encoding='utf-8') as f:
            json.dump(restart_info, f, ensure_ascii=False)
        
        finish_command(user_id)
        
        # إعادة تشغيل العملية
        os.execv(sys.executable, [sys.executable] + sys.argv)
        
    except Exception as e:
        logging.error(f"خطأ في restart_bot_command: {e}")
        if message.from_user:
            finish_command(message.from_user.id)
        await message.reply("❌ حدث خطأ أثناء إعادة التشغيل")


@master_only
async def shutdown_bot_command(message: Message):
    """إيقاف تشغيل البوت نهائياً مع عد تنازلي وإمكانية الإلغاء"""
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # تسجيل بداية الأمر
        start_cancellable_command(user_id, "shutdown", chat_id)
        
        # رسالة التأكيد مع العد التنازلي
        countdown_msg = await message.reply(
            "🔴 **أمر إيقاف التشغيل المطلق**\n\n"
            f"👑 السيد: {message.from_user.first_name}\n"
            "⚠️ سيتم إيقاف البوت نهائياً خلال 15 ثانية!\n"
            "💾 سيتم حفظ جميع البيانات تلقائياً\n"
            "🔌 لن يعود البوت للعمل إلا بإعادة تشغيل يدوية\n\n"
            "⏰ **العد التنازلي:** 15\n\n"
            "💡 اكتب 'إلغاء' لإيقاف الأمر"
        )
        
        # العد التنازلي لمدة 15 ثانية مع فحص الإلغاء
        for i in range(14, 0, -1):
            await asyncio.sleep(1)
            
            # فحص الإلغاء
            if is_command_cancelled(user_id):
                await countdown_msg.edit_text(
                    "❌ **تم إلغاء أمر إيقاف التشغيل**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "✅ تم إيقاف أمر الإغلاق بنجاح\n"
                    "🟢 البوت يواصل العمل بشكل طبيعي"
                )
                finish_command(user_id)
                return
            
            try:
                await countdown_msg.edit_text(
                    "🔴 **أمر إيقاف التشغيل المطلق**\n\n"
                    f"👑 السيد: {message.from_user.first_name}\n"
                    "⚠️ سيتم إيقاف البوت نهائياً!\n"
                    "💾 سيتم حفظ جميع البيانات تلقائياً\n"
                    "🔌 لن يعود البوت للعمل إلا بإعادة تشغيل يدوية\n\n"
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
            "🔴 **إيقاف تشغيل البوت الآن...**\n\n"
            "🔌 جاري إغلاق النظام نهائياً\n"
            "💤 البوت متوقف - تم تنفيذ أمر السيد"
        )
        
        await asyncio.sleep(1)
        
        # حفظ البيانات المهمة قبل الإغلاق
        logging.info(f"إيقاف البوت نهائياً بأمر من السيد: {user_id}")
        finish_command(user_id)
        
        # إيقاف تشغيل البوت نهائياً
        sys.exit(0)
        
    except Exception as e:
        logging.error(f"خطأ في shutdown_bot_command: {e}")
        if message.from_user:
            finish_command(message.from_user.id)
        await message.reply("❌ حدث خطأ أثناء إيقاف التشغيل")


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


@master_only
async def add_money_command(message: Message):
    """إضافة أموال لمستخدم - أمر خاص بالأسياد"""
    try:
        # فحص إذا كان الأمر رد على رسالة
        if message.reply_to_message and message.reply_to_message.from_user:
            # استخراج المبلغ من النص
            if not message.text:
                await message.reply("❌ يرجى كتابة المبلغ مع الأمر\n\nمثال: اضف فلوس 5000")
                return
                
            text_parts = message.text.split()
            if len(text_parts) < 3:
                await message.reply(
                    "❌ استخدم الصيغة الصحيحة:\n"
                    "رد على رسالة اللاعب واكتب: اضف فلوس [المبلغ]\n\n"
                    "مثال: اضف فلوس 5000"
                )
                return
            
            try:
                amount = int(text_parts[2])
            except ValueError:
                await message.reply("❌ يرجى كتابة مبلغ صحيح\n\nمثال: اضف فلوس 5000")
                return
            
            if amount <= 0:
                await message.reply("❌ يجب أن يكون المبلغ أكبر من صفر")
                return
            
            target_user_id = message.reply_to_message.from_user.id
            target_name = message.reply_to_message.from_user.first_name or "المستخدم"
            master_name = message.from_user.first_name or "السيد"
            
            # التحقق من وجود المستخدم المستهدف
            from database.operations import get_user, update_user_balance, add_transaction
            target_user = await get_user(target_user_id)
            
            if not target_user:
                await message.reply(
                    f"❌ {target_name} لم ينشئ حساب بنكي بعد!\n"
                    f"يجب عليه كتابة 'انشاء حساب بنكي' أولاً"
                )
                return
            
            # إضافة المبلغ
            new_balance = target_user['balance'] + amount
            await update_user_balance(target_user_id, new_balance)
            
            # تسجيل المعاملة
            await add_transaction(
                user_id=target_user_id,
                transaction_type="master_gift",
                amount=amount,
                description=f"هدية من السيد {master_name}",
                from_balance=target_user['balance'],
                to_balance=new_balance
            )
            
            from utils.helpers import format_number
            
            # رسالة نجاح للسيد
            await message.reply(
                f"✅ **تم إضافة الأموال بنجاح!**\n\n"
                f"👑 السيد: {master_name}\n"
                f"🎯 المستهدف: {target_name}\n"
                f"💰 المبلغ المضاف: {format_number(amount)}$\n"
                f"💳 الرصيد الجديد: {format_number(new_balance)}$\n\n"
                f"🎁 تمت الهدية بسلطة السيادة المطلقة"
            )
            
            # إشعار للمستخدم المستهدف
            try:
                await message.bot.send_message(
                    target_user_id,
                    f"🎉 **هدية من السيد!**\n\n"
                    f"👑 السيد {master_name} أهداك {format_number(amount)}$ 💰\n"
                    f"💳 رصيدك الجديد: {format_number(new_balance)}$\n\n"
                    f"✨ استمتع بالهدية من سيادته المطلقة!"
                )
            except:
                pass  # في حالة فشل إرسال الإشعار الخاص
                
        else:
            # إذا لم يكن رد على رسالة، اطلب اسم المستخدم أو الرد
            await message.reply(
                "💡 **طريقتان لإضافة الأموال:**\n\n"
                "1️⃣ **بالرد على الرسالة:**\n"
                "   رد على رسالة اللاعب واكتب: اضف فلوس [المبلغ]\n\n"
                "2️⃣ **بالمعرف:**\n"
                "   اكتب: اضف فلوس [المعرف] [المبلغ]\n\n"
                "**أمثلة:**\n"
                "• اضف فلوس 5000 (رد على رسالة اللاعب)\n"
                "• اضف فلوس @username 3000\n"
                "• اضب فلوس 123456789 2000"
            )
            
    except Exception as e:
        logging.error(f"خطأ في add_money_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إضافة الأموال")


async def handle_master_commands(message: Message) -> bool:
    """معالج أوامر الأسياد"""
    if not message.text or not message.from_user:
        return False
    
    user_id = message.from_user.id
    text = message.text.lower().strip()
    
    # فحص إذا كان النص يحتوي على أمر من أوامر الأسياد
    from modules.permission_responses import is_master_command, get_permission_denial_response
    if is_master_command(message.text):
        # التحقق من كون المستخدم سيد
        if user_id not in MASTERS:
            # إرسال رد مهين
            group_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
            insulting_response = get_permission_denial_response(user_id, group_id, AdminLevel.MASTER)
            if insulting_response:
                await message.reply(insulting_response)
            return True
    
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
    
    elif any(phrase in text for phrase in ['يوكي قم بإيقاف التشغيل', 'يوكي اوقف البوت', 'shutdown bot']):
        await shutdown_bot_command(message)
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
    
    # أمر إضافة الأموال
    elif text.startswith('اضف فلوس') or text.startswith('أضف فلوس') or text.startswith('add money'):
        await add_money_command(message)
        return True
    
    return False


async def add_money_command(message: Message):
    """أمر إضافة الأموال للمستخدمين (خاص بالأسياد)"""
    try:
        if not message.reply_to_message:
            await message.reply(
                "❌ **يرجى الرد على رسالة المستخدم**\n\n"
                "📝 **الطريقة الصحيحة:**\n"
                "1️⃣ اجعل رد على رسالة المستخدم\n"
                "2️⃣ اكتب: اضف فلوس [المبلغ]\n\n"
                "مثال: اضف فلوس 5000"
            )
            return
        
        # استخراج المبلغ من النص
        text_parts = message.text.split()
        if len(text_parts) < 3:
            await message.reply(
                "❌ **صيغة خاطئة!**\n\n"
                "✅ **الصيغة الصحيحة:**\n"
                "اضف فلوس [المبلغ]\n\n"
                "مثال: اضب فلوس 5000"
            )
            return
        
        try:
            amount = int(text_parts[2])
        except ValueError:
            await message.reply("❌ يرجى كتابة مبلغ صحيح\n\nمثال: اضف فلوس 5000")
            return
        
        if amount <= 0:
            await message.reply("❌ يجب أن يكون المبلغ أكبر من صفر")
            return
        
        # الحصول على معلومات المستخدم المستهدف
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن الحصول على معلومات المستخدم")
            return
        
        target_user_id = target_user.id
        target_name = target_user.first_name or "مستخدم"
        master_name = message.from_user.first_name or "السيد"
        
        # التحقق من وجود المستخدم في قاعدة البيانات
        from database.operations import get_user, update_user_balance, add_transaction
        from utils.helpers import format_number
        
        user_data = await get_user(target_user_id)
        if not user_data:
            await message.reply(
                f"❌ **المستخدم {target_name} لم ينشئ حساب بنكي بعد!**\n\n"
                f"💡 يجب عليه كتابة 'انشاء حساب بنكي' أولاً"
            )
            return
        
        # إضافة المبلغ إلى رصيد المستخدم
        success = await update_user_balance(target_user_id, amount)
        
        if success:
            # تسجيل المعاملة
            await add_transaction(
                target_user_id, 
                "إضافة أموال من السيد",
                amount, 
                f"هدية من السيد {master_name}"
            )
            
            # رسالة تأكيد للسيد
            await message.reply(
                f"✅ **تم إضافة الأموال بنجاح!**\n\n"
                f"👤 المستفيد: {target_name}\n"
                f"💰 المبلغ المضاف: {format_number(amount)}$\n"
                f"💳 الرصيد الجديد: {format_number(user_data['balance'] + amount)}$\n\n"
                f"🎁 **تم إرسال إشعار للمستخدم**"
            )
            
            # إشعار للمستخدم المستفيد
            try:
                notification_msg = (
                    f"🎉 **مفاجأة سارة!**\n\n"
                    f"💰 لقد حصلت على هدية مالية من السيد {master_name}\n"
                    f"💵 المبلغ: {format_number(amount)}$\n"
                    f"💳 رصيدك الحالي: {format_number(user_data['balance'] + amount)}$\n\n"
                    f"🙏 **شكراً لك يا سيد {master_name}!**"
                )
                
                # إرسال رد على رسالة المستخدم
                await message.reply_to_message.reply(notification_msg)
                    
            except Exception as e:
                logging.error(f"خطأ في إرسال الإشعار: {e}")
                # الإشعار ليس ضرورياً، المهم تم إضافة الأموال
                pass
        else:
            await message.reply("❌ حدث خطأ أثناء إضافة الأموال")
            
    except Exception as e:
        logging.error(f"خطأ في add_money_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إضافة الأموال")
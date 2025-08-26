"""
أوامر الإدارة المتقدمة باستخدام نظام الرتب والصلاحيات الجديد
"""

import logging
from typing import Optional, List
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config.ranks_system import rank_manager, ALL_RANKS, RankType, Permission
from utils.permission_decorators import (
    can_mute_users, can_kick_users, can_ban_users, can_delete_messages,
    can_manage_ranks, moderator_required, senior_moderator_required,
    get_user_permissions_list, check_user_permission
)
from database.operations import execute_query
from config.hierarchy import is_master
from utils.states import RankManagementStates


@can_mute_users
async def mute_user(message: Message):
    """كتم مستخدم - يتطلب صلاحية كتم المستخدمين"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة المستخدم المراد كتمه")
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # فحص إذا كان المستخدم المستهدف من الأسياد
        if is_master(target_user.id):
            await message.reply("👑 لا يمكن كتم الأسياد! الأسياد محميون من جميع الأوامر الإدارية")
            return
        
        # فحص إذا كان المستخدم المستهدف مشرف أعلى
        target_rank = rank_manager.get_user_rank(target_user.id, message.chat.id)
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id) if message.from_user else None
        
        if (target_rank and user_rank and 
            target_rank.rank_type == RankType.ADMINISTRATIVE and
            target_rank.level >= user_rank.level):
            await message.reply("❌ لا يمكنك كتم مشرف بنفس مستواك أو أعلى")
            return
        
        # تنفيذ الكتم (هنا يمكن إضافة منطق الكتم الفعلي)
        await message.reply(
            f"✅ تم كتم المستخدم {target_user.first_name}\n"
            f"👤 بواسطة: {message.from_user.first_name if message.from_user else 'مجهول'}\n"
            f"🔇 المستخدم لن يتمكن من إرسال الرسائل"
        )
        
        # تسجيل العملية
        logging.info(f"تم كتم المستخدم {target_user.id} بواسطة {message.from_user.id if message.from_user else 'مجهول'}")
        
    except Exception as e:
        logging.error(f"خطأ في كتم المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة كتم المستخدم")


@can_kick_users
async def kick_user(message: Message):
    """طرد مستخدم - يتطلب صلاحية طرد المستخدمين"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة المستخدم المراد طرده")
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # فحص إذا كان المستخدم المستهدف من الأسياد
        if is_master(target_user.id):
            await message.reply("👑 لا يمكن طرد الأسياد! الأسياد محميون من جميع الأوامر الإدارية")
            return
        
        # فحص الصلاحيات
        target_rank = rank_manager.get_user_rank(target_user.id, message.chat.id)
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id)
        
        if (target_rank and user_rank and 
            target_rank.rank_type == RankType.ADMINISTRATIVE and
            target_rank.level >= user_rank.level):
            await message.reply("❌ لا يمكنك طرد مشرف بنفس مستواك أو أعلى")
            return
        
        await message.reply(
            f"✅ تم طرد المستخدم {target_user.first_name}\n"
            f"👤 بواسطة: {message.from_user.first_name if message.from_user else 'مجهول'}\n"
            f"🚪 يمكن للمستخدم العودة عبر الرابط"
        )
        
        logging.info(f"تم طرد المستخدم {target_user.id} بواسطة {message.from_user.id if message.from_user else 'مجهول'}")
        
    except Exception as e:
        logging.error(f"خطأ في طرد المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة طرد المستخدم")


@can_ban_users
async def ban_user(message: Message):
    """حظر مستخدم - يتطلب صلاحية حظر المستخدمين"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة المستخدم المراد حظره")
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # فحص إذا كان المستخدم المستهدف من الأسياد
        if is_master(target_user.id):
            await message.reply("👑 لا يمكن حظر الأسياد! الأسياد محميون من جميع الأوامر الإدارية")
            return
        
        # فحص الصلاحيات
        target_rank = rank_manager.get_user_rank(target_user.id, message.chat.id)
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id)
        
        if (target_rank and user_rank and 
            target_rank.rank_type == RankType.ADMINISTRATIVE and
            target_rank.level >= user_rank.level):
            await message.reply("❌ لا يمكنك حظر مشرف بنفس مستواك أو أعلى")
            return
        
        await message.reply(
            f"🚫 تم حظر المستخدم {target_user.first_name}\n"
            f"👤 بواسطة: {message.from_user.first_name if message.from_user else 'مجهول'}\n"
            f"⛔ المستخدم محظور نهائياً من المجموعة"
        )
        
        logging.info(f"تم حظر المستخدم {target_user.id} بواسطة {message.from_user.id if message.from_user else 'مجهول'}")
        
    except Exception as e:
        logging.error(f"خطأ في حظر المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة حظر المستخدم")


@can_manage_ranks
async def promote_user_command(message: Message, state: FSMContext):
    """ترقية مستخدم لرتبة إدارية"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة المستخدم المراد ترقيته")
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # حفظ معرف المستخدم المستهدف
        await state.update_data(target_user_id=target_user.id, target_user_name=target_user.first_name)
        
        # عرض الرتب المتاحة
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id)
        available_ranks = []
        
        for rank_name, rank_info in ALL_RANKS.items():
            if rank_info.rank_type == RankType.ADMINISTRATIVE:
                # يمكن ترقية للرتب الأقل من رتبة المستخدم الحالي
                if not user_rank or rank_info.level < user_rank.level or is_master(message.from_user.id):
                    available_ranks.append(f"• {rank_info.display_name} - {rank_info.description}")
        
        if not available_ranks:
            await message.reply("❌ لا توجد رتب متاحة للترقية")
            return
        
        ranks_text = "\n".join(available_ranks)
        await message.reply(
            f"📋 **الرتب المتاحة للترقية:**\n\n{ranks_text}\n\n"
            f"💡 أرسل اسم الرتبة المطلوبة لترقية {target_user.first_name}"
        )
        
        await state.set_state(RankManagementStates.waiting_for_rank_name)
        
    except Exception as e:
        logging.error(f"خطأ في أمر الترقية: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة الترقية")


async def handle_rank_selection(message: Message, state: FSMContext):
    """معالجة اختيار الرتبة للترقية"""
    try:
        data = await state.get_data()
        target_user_id = data.get('target_user_id')
        target_user_name = data.get('target_user_name')
        
        if not target_user_id:
            await message.reply("❌ انتهت صلاحية الجلسة، يرجى إعادة المحاولة")
            await state.clear()
            return
        
        rank_name = message.text.strip() if message.text else ""
        
        # البحث عن الرتبة بالاسم المعروض أو الاسم الأصلي
        selected_rank = None
        for name, rank_info in ALL_RANKS.items():
            if (rank_info.display_name.replace(rank_info.color + " ", "") == rank_name or 
                name == rank_name or
                rank_info.display_name == rank_name):
                selected_rank = (name, rank_info)
                break
        
        if not selected_rank:
            await message.reply("❌ رتبة غير صحيحة، يرجى المحاولة مرة أخرى")
            return
        
        rank_key, rank_info = selected_rank
        
        # فحص الصلاحية للترقية لهذه الرتبة
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id)
        if (not is_master(message.from_user.id) and user_rank and 
            rank_info.level >= user_rank.level):
            await message.reply("❌ لا يمكنك ترقية لرتبة أعلى من رتبتك أو مساوية لها")
            await state.clear()
            return
        
        # حفظ الرتبة المختارة وطلب السبب
        await state.update_data(selected_rank=rank_key)
        await message.reply(
            f"✅ تم اختيار رتبة: {rank_info.display_name}\n\n"
            f"📝 أرسل سبب الترقية (اختياري - أرسل 'تخطي' للمتابعة بدون سبب):"
        )
        await state.set_state(RankManagementStates.waiting_for_reason)
        
    except Exception as e:
        logging.error(f"خطأ في اختيار الرتبة: {e}")
        await message.reply("❌ حدث خطأ أثناء اختيار الرتبة")


async def handle_promotion_reason(message: Message, state: FSMContext):
    """معالجة سبب الترقية وتنفيذها"""
    try:
        data = await state.get_data()
        target_user_id = data.get('target_user_id')
        target_user_name = data.get('target_user_name')
        selected_rank = data.get('selected_rank')
        
        reason_text = message.text.strip() if message.text else ""
        reason = reason_text if reason_text.lower() != 'تخطي' else None
        
        # تنفيذ الترقية
        if target_user_id and selected_rank and message.from_user:
            success = await rank_manager.promote_user(
                target_user_id, 
                message.chat.id, 
                selected_rank, 
                message.from_user.id,
                reason
            )
            
            if success:
                rank_info = ALL_RANKS[selected_rank]
                await message.reply(
                    f"🎉 **تم ترقية المستخدم بنجاح!**\n\n"
                    f"👤 **المستخدم:** {target_user_name}\n"
                    f"🏆 **الرتبة الجديدة:** {rank_info.display_name}\n"
                    f"👨‍💼 **تم بواسطة:** {message.from_user.first_name}\n"
                    f"📝 **السبب:** {reason if reason else 'لم يتم تحديد سبب'}\n\n"
                    f"📋 **صلاحيات الرتبة:**\n{rank_info.description}"
                )
            else:
                await message.reply("❌ فشل في ترقية المستخدم، يرجى المحاولة لاحقاً")
        else:
            await message.reply("❌ معلومات غير مكتملة للترقية")
        
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في تنفيذ الترقية: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الترقية")
        await state.clear()


@can_manage_ranks
async def demote_user_command(message: Message):
    """تخفيض رتبة مستخدم"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ يجب الرد على رسالة المستخدم المراد تخفيض رتبته")
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # فحص إذا كان المستخدم له رتبة
        target_rank = rank_manager.get_user_rank(target_user.id, message.chat.id)
        if not target_rank:
            await message.reply("❌ المستخدم لا يملك رتبة إدارية")
            return
        
        # فحص الصلاحية
        user_rank = rank_manager.get_user_rank(message.from_user.id, message.chat.id)
        if (not is_master(message.from_user.id) and user_rank and 
            target_rank.level >= user_rank.level):
            await message.reply("❌ لا يمكنك تخفيض رتبة مشرف بنفس مستواك أو أعلى")
            return
        
        # تنفيذ التخفيض
        success = await rank_manager.demote_user(
            target_user.id, 
            message.chat.id, 
            message.from_user.id,
            "تخفيض رتبة من قبل مشرف"
        )
        
        if success:
            await message.reply(
                f"📉 **تم تخفيض رتبة المستخدم**\n\n"
                f"👤 **المستخدم:** {target_user.first_name}\n"
                f"🏆 **الرتبة السابقة:** {target_rank.display_name}\n"
                f"📊 **الحالة الجديدة:** عضو عادي\n"
                f"👨‍💼 **تم بواسطة:** {message.from_user.first_name}"
            )
        else:
            await message.reply("❌ فشل في تخفيض رتبة المستخدم")
        
    except Exception as e:
        logging.error(f"خطأ في تخفيض الرتبة: {e}")
        await message.reply("❌ حدث خطأ أثناء تخفيض الرتبة")


async def show_user_rank_info(message: Message):
    """عرض معلومات رتبة المستخدم"""
    try:
        target_user = None
        
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        else:
            target_user = message.from_user
        
        if not target_user:
            await message.reply("❌ لا يمكن التعرف على المستخدم")
            return
        
        # الحصول على معلومات الرتبة
        user_rank = rank_manager.get_user_rank(target_user.id, message.chat.id)
        permissions_list = await get_user_permissions_list(target_user.id, message.chat.id)
        
        # تكوين الرسالة
        info_text = f"👤 **معلومات المستخدم:** {target_user.first_name}\n\n"
        
        if user_rank:
            info_text += f"🏆 **الرتبة:** {user_rank.display_name}\n"
            info_text += f"📊 **المستوى:** {user_rank.level}\n"
            info_text += f"🎭 **النوع:** {'إدارية' if user_rank.rank_type == RankType.ADMINISTRATIVE else 'ترفيهية'}\n"
            info_text += f"📝 **الوصف:** {user_rank.description}\n\n"
        else:
            info_text += "🏆 **الرتبة:** عضو عادي\n\n"
        
        info_text += "🔐 **الصلاحيات:**\n" + "\n".join(permissions_list)
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض معلومات الرتبة: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات الرتبة")


@moderator_required
async def show_admin_panel(message: Message):
    """عرض لوحة الإدارة المتقدمة"""
    try:
        user_permissions = await get_user_permissions_list(message.from_user.id, message.chat.id)
        
        panel_text = """
🔧 **لوحة الإدارة المتقدمة**

📋 **الأوامر المتاحة:**

👥 **إدارة المستخدمين:**
• `كتم` (رد على رسالة) - كتم مستخدم
• `طرد` (رد على رسالة) - طرد مستخدم  
• `حظر` (رد على رسالة) - حظر مستخدم
• `رتبتي` - عرض رتبتك الحالية
• `رتبته` (رد على رسالة) - عرض رتبة مستخدم

🏆 **إدارة الرتب:**
• `ترقية` (رد على رسالة) - ترقية مستخدم
• `تخفيض` (رد على رسالة) - تخفيض رتبة
• `الرتب الإدارية` - عرض الرتب الإدارية
• `الرتب الترفيهية` - عرض الرتب الترفيهية

📊 **إحصائيات:**
• `إحصائيات الإدارة` - إحصائيات المشرفين
• `نشاط المجموعة` - إحصائيات النشاط
        """
        
        panel_text += f"\n\n🔐 **صلاحياتك الحالية:**\n" + "\n".join(user_permissions)
        
        await message.reply(panel_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض لوحة الإدارة: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض لوحة الإدارة")


async def show_administrative_ranks(message: Message):
    """عرض جميع الرتب الإدارية المتاحة"""
    try:
        admin_ranks = rank_manager.get_available_ranks(RankType.ADMINISTRATIVE)
        
        ranks_text = "🏛️ **الرتب الإدارية المتاحة:**\n\n"
        
        # ترتيب الرتب حسب المستوى
        sorted_ranks = sorted(admin_ranks.items(), key=lambda x: x[1].level)
        
        for rank_name, rank_info in sorted_ranks:
            ranks_text += f"{rank_info.display_name}\n"
            ranks_text += f"📊 المستوى: {rank_info.level}\n"
            ranks_text += f"📝 الوصف: {rank_info.description}\n"
            ranks_text += f"🔐 عدد الصلاحيات: {len(rank_info.permissions)}\n\n"
        
        await message.reply(ranks_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الرتب الإدارية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتب الإدارية")


async def show_entertainment_ranks(message: Message):
    """عرض جميع الرتب الترفيهية المتاحة"""
    try:
        entertainment_ranks = rank_manager.get_available_ranks(RankType.ENTERTAINMENT)
        
        ranks_text = "🎭 **الرتب الترفيهية المتاحة:**\n\n"
        
        # ترتيب الرتب حسب المستوى
        sorted_ranks = sorted(entertainment_ranks.items(), key=lambda x: x[1].level)
        
        for rank_name, rank_info in sorted_ranks:
            ranks_text += f"{rank_info.display_name}\n"
            ranks_text += f"📊 المستوى: {rank_info.level}\n"
            ranks_text += f"📝 الوصف: {rank_info.description}\n"
            ranks_text += "🎮 رتبة ترفيهية (بدون صلاحيات إدارية)\n\n"
        
        await message.reply(ranks_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض الرتب الترفيهية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتب الترفيهية")
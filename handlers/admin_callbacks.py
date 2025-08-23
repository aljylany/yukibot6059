"""
معالج callbacks للأوامر الإدارية المتقدمة
Admin Callbacks Handler for Advanced Administrative Commands
"""

import logging
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from config.ranks_system import ALL_RANKS, rank_manager
from utils.states import RankManagementStates


async def handle_promotion_callback(callback: CallbackQuery, state: FSMContext):
    """معالجة callbacks الترقية"""
    try:
        callback_data = callback.data
        
        if not callback_data:
            await callback.answer("❌ خطأ في البيانات")
            return
        
        # إلغاء الترقية
        if callback_data == "cancel_promotion":
            await state.clear()
            await callback.message.edit_text("❌ تم إلغاء عملية الترقية")
            await callback.answer()
            return
        
        # عرض الرتب الترفيهية
        if callback_data == "show_entertainment_ranks":
            await callback.answer("📋 الرتب الترفيهية معروضة أدناه")
            return
        
        # معالجة اختيار الرتبة
        if callback_data.startswith("promote_"):
            rank_type = callback_data.split("_")[1]  # admin أو ent
            rank_name = "_".join(callback_data.split("_")[2:])  # اسم الرتبة
            
            # التحقق من وجود الرتبة
            if rank_name not in ALL_RANKS:
                await callback.answer("❌ رتبة غير صحيحة")
                return
            
            rank_info = ALL_RANKS[rank_name]
            
            # التحقق من صلاحية الترقية
            if callback.from_user:
                user_rank = rank_manager.get_user_rank(callback.from_user.id, callback.message.chat.id)
                from config.hierarchy import is_master
                
                if (not is_master(callback.from_user.id) and user_rank and 
                    rank_info.level >= user_rank.level):
                    await callback.answer("❌ لا يمكنك ترقية لرتبة أعلى من رتبتك أو مساوية لها")
                    return
            
            # حفظ الرتبة المختارة
            await state.update_data(selected_rank=rank_name)
            
            await callback.message.edit_text(
                f"✅ **تم اختيار الرتبة:** {rank_info.display_name}\n\n"
                f"📝 **الوصف:** {rank_info.description}\n\n"
                f"💬 أرسل سبب الترقية (اختياري - أرسل 'تخطي' للمتابعة بدون سبب):"
            )
            
            await state.set_state(RankManagementStates.waiting_for_reason)
            await callback.answer(f"✅ تم اختيار رتبة {rank_info.display_name}")
        
    except Exception as e:
        logging.error(f"خطأ في معالجة callback الترقية: {e}")
        await callback.answer("❌ حدث خطأ أثناء معالجة العملية")


async def handle_rank_info_callback(callback: CallbackQuery):
    """معالجة callbacks معلومات الرتب"""
    try:
        callback_data = callback.data
        
        if callback_data == "show_all_admin_ranks":
            # عرض تفاصيل الرتب الإدارية
            from config.ranks_system import ADMINISTRATIVE_RANKS, RankType
            
            admin_ranks = rank_manager.get_available_ranks(RankType.ADMINISTRATIVE)
            ranks_text = "🏛️ **الرتب الإدارية المتاحة:**\n\n"
            
            sorted_ranks = sorted(admin_ranks.items(), key=lambda x: x[1].level)
            
            for rank_name, rank_info in sorted_ranks:
                ranks_text += f"{rank_info.display_name}\n"
                ranks_text += f"📊 المستوى: {rank_info.level}\n"
                ranks_text += f"📝 الوصف: {rank_info.description}\n"
                ranks_text += f"🔐 عدد الصلاحيات: {len(rank_info.permissions)}\n\n"
            
            await callback.message.edit_text(ranks_text)
            await callback.answer()
            
        elif callback_data == "show_all_ent_ranks":
            # عرض تفاصيل الرتب الترفيهية
            from config.ranks_system import ENTERTAINMENT_RANKS, RankType
            
            ent_ranks = rank_manager.get_available_ranks(RankType.ENTERTAINMENT)
            ranks_text = "🎭 **الرتب الترفيهية المتاحة:**\n\n"
            
            sorted_ranks = sorted(ent_ranks.items(), key=lambda x: x[1].level)
            
            for rank_name, rank_info in sorted_ranks:
                ranks_text += f"{rank_info.display_name}\n"
                ranks_text += f"📊 المستوى: {rank_info.level}\n"
                ranks_text += f"📝 الوصف: {rank_info.description}\n"
                ranks_text += "🎮 رتبة ترفيهية (بدون صلاحيات إدارية)\n\n"
            
            await callback.message.edit_text(ranks_text)
            await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في معالجة callback معلومات الرتب: {e}")
        await callback.answer("❌ حدث خطأ أثناء عرض المعلومات")


# تصدير المعالجات
__all__ = ['handle_promotion_callback', 'handle_rank_info_callback']
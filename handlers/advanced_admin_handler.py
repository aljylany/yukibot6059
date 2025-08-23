"""
معالج الأوامر الإدارية المتقدمة
Advanced Administrative Commands Handler
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from modules.advanced_admin import (
    handle_rank_selection, handle_promotion_reason,
    show_user_rank_info, show_admin_panel, show_administrative_ranks, 
    show_entertainment_ranks
)
from utils.states import RankManagementStates


async def handle_advanced_admin_commands(message: Message, state: FSMContext) -> bool:
    """معالج الأوامر الإدارية المتقدمة حسب الحالة"""
    try:
        current_state = await state.get_state()
        
        # إذا لم تكن هناك حالة، لا نتعامل مع الرسالة
        if not current_state:
            return False
        
        # التحقق من أنها حالة إدارية متقدمة
        if not current_state.startswith("RankManagement"):
            return False
        
        if current_state == RankManagementStates.waiting_for_rank_name.state:
            await handle_rank_selection(message, state)
            return True
        elif current_state == RankManagementStates.waiting_for_reason.state:
            await handle_promotion_reason(message, state)
            return True
        elif current_state == RankManagementStates.waiting_for_target_user.state:
            await message.reply("❌ انتهت صلاحية الجلسة، يرجى إعادة المحاولة")
            await state.clear()
            return True
        elif current_state == RankManagementStates.waiting_for_confirmation.state:
            await message.reply("❌ انتهت صلاحية الجلسة، يرجى إعادة المحاولة")
            await state.clear()
            return True
        else:
            # حالة RankManagement غير معروفة
            await message.reply("❌ حدث خطأ في نظام الرتب، يرجى إعادة المحاولة")
            await state.clear()
            return True
            
    except Exception as e:
        logging.error(f"خطأ في معالج الأوامر الإدارية المتقدمة: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الأمر الإداري")
        await state.clear()
        return True


# تصدير المعالج
__all__ = ['handle_advanced_admin_commands']
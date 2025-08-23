"""
معالج callbacks للبوت
Bot Callbacks Handler
"""

import logging
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query()
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج شامل لجميع الـ callbacks"""
    try:
        data = callback.data
        
        # معالجة callbacks نطاق الردود المخصصة
        if data in ["scope_group", "scope_global", "scope_cancel"]:
            from modules.custom_replies import handle_scope_callback
            await handle_scope_callback(callback, state)
            return
        
        # معالجة callbacks الهمسة
        if data.startswith('view_whisper_') or data.startswith('reply_whisper_'):
            from modules.utility_commands import handle_whisper_callback
            await handle_whisper_callback(callback)
            return
        
        # معالجة callbacks أخرى
        await callback.answer("⚠️ هذا الزر غير نشط حالياً")
        
    except Exception as e:
        logging.error(f"خطأ في معالج الـ callbacks: {e}")
        try:
            await callback.answer("❌ حدث خطأ")
        except:
            pass
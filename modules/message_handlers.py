"""
معالجات الرسائل المساعدة
Helper Message Handlers
"""

import logging
import random
from aiogram.types import Message
from aiogram.fsm.context import FSMContext


async def handle_banks_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل البنوك"""
    try:
        # إعادة توجيه إلى وحدة البنوك المناسبة
        from modules import banks
        if hasattr(banks, 'handle_state_message'):
            await banks.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام البنوك")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل البنوك: {e}")
        await message.reply("❌ حدث خطأ في نظام البنوك")
        await state.clear()


async def handle_property_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل العقارات"""
    try:
        from modules import real_estate
        if hasattr(real_estate, 'handle_state_message'):
            await real_estate.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام العقارات")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل العقارات: {e}")
        await message.reply("❌ حدث خطأ في نظام العقارات")
        await state.clear()


async def handle_theft_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل السرقة"""
    try:
        from modules import theft
        if hasattr(theft, 'handle_state_message'):
            await theft.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام السرقة")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل السرقة: {e}")
        await message.reply("❌ حدث خطأ في نظام السرقة")
        await state.clear()


async def handle_stocks_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل الأسهم"""
    try:
        from modules import stocks
        if hasattr(stocks, 'handle_state_message'):
            await stocks.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام الأسهم")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل الأسهم: {e}")
        await message.reply("❌ حدث خطأ في نظام الأسهم")
        await state.clear()


async def handle_investment_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل الاستثمار"""
    try:
        from modules import investment
        if hasattr(investment, 'handle_state_message'):
            await investment.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام الاستثمار")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل الاستثمار: {e}")
        await message.reply("❌ حدث خطأ في نظام الاستثمار")
        await state.clear()


async def handle_farm_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل المزرعة"""
    try:
        from modules import farm
        if hasattr(farm, 'handle_state_message'):
            await farm.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام المزرعة")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل المزرعة: {e}")
        await message.reply("❌ حدث خطأ في نظام المزرعة")
        await state.clear()


async def handle_castle_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل القلعة"""
    try:
        from modules import castle
        if hasattr(castle, 'handle_state_message'):
            await castle.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام القلعة")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل القلعة: {e}")
        await message.reply("❌ حدث خطأ في نظام القلعة")
        await state.clear()


async def handle_admin_message(message: Message, state: FSMContext, current_state: str):
    """معالج رسائل الإدارة"""
    try:
        from modules import administration
        if hasattr(administration, 'handle_state_message'):
            await administration.handle_state_message(message, state, current_state)
        else:
            await message.reply("❌ هناك مشكلة في نظام الإدارة")
            await state.clear()
            
    except Exception as e:
        logging.error(f"خطأ في معالج رسائل الإدارة: {e}")
        await message.reply("❌ حدث خطأ في نظام الإدارة")
        await state.clear()


async def handle_admin_command(message: Message, text: str):
    """معالج أوامر الرفع والتنزيل"""
    try:
        from modules import admin_management
        
        if text.startswith('رفع '):
            await admin_management.handle_rank_promotion(message, text[4:].strip(), "رفع")
        elif text.startswith('تنزيل '):
            await admin_management.handle_rank_promotion(message, text[6:].strip(), "تنزيل")
        else:
            await message.reply("❌ أمر غير مفهوم")
            
    except Exception as e:
        logging.error(f"خطأ في معالج الأوامر الإدارية: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ الأمر")


async def handle_clear_command(message: Message, text: str):
    """معالج أوامر المسح"""
    try:
        from modules import clear_commands
        
        if hasattr(clear_commands, 'handle_clear_command'):
            await clear_commands.handle_clear_command(message, text)
        else:
            await message.reply("❌ وظيفة المسح غير متاحة حالياً")
            
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر المسح: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ أمر المسح")


async def handle_lock_command(message: Message, text: str):
    """معالج أوامر القفل"""
    try:
        from modules import media_locks
        
        if hasattr(media_locks, 'handle_lock_command'):
            await media_locks.handle_lock_command(message, text)
        else:
            await message.reply("❌ وظيفة القفل غير متاحة حالياً")
            
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر القفل: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ أمر القفل")


async def handle_unlock_command(message: Message, text: str):
    """معالج أوامر الفتح"""
    try:
        from modules import media_locks
        
        if hasattr(media_locks, 'handle_unlock_command'):
            await media_locks.handle_unlock_command(message, text)
        else:
            await message.reply("❌ وظيفة الفتح غير متاحة حالياً")
            
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر الفتح: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ أمر الفتح")


async def handle_toggle_command(message: Message, text: str, action: str):
    """معالج أوامر التفعيل والتعطيل"""
    try:
        from modules import group_settings
        
        if hasattr(group_settings, 'handle_toggle_command'):
            await group_settings.handle_toggle_command(message, text, action)
        else:
            await message.reply("❌ وظيفة التفعيل/التعطيل غير متاحة حالياً")
            
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر التفعيل/التعطيل: {e}")
        await message.reply("❌ حدث خطأ في تنفيذ الأمر")
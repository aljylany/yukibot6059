"""
معالج الـ Callbacks
Bot Callbacks Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

from modules import banks, real_estate, theft, stocks, investment, ranking, administration, farm, castle
from utils.decorators import user_required, admin_required
from config.settings import SYSTEM_MESSAGES

router = Router()


# Callbacks البنوك
@router.callback_query(F.data.startswith("bank_"))
@user_required
async def bank_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks البنوك"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "deposit":
            await banks.start_deposit(callback.message, state)
        elif action == "withdraw":
            await banks.start_withdraw(callback.message, state)
        elif action == "balance":
            await banks.show_bank_balance(callback.message)
        elif action == "interest":
            await banks.show_interest_info(callback.message)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks البنوك: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks العقارات
@router.callback_query(F.data.startswith("property_"))
@user_required
async def property_callbacks(callback: CallbackQuery):
    """معالج callbacks العقارات"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "buy":
            await real_estate.show_available_properties(callback.message)
        elif action == "sell":
            await real_estate.show_owned_properties(callback.message)
        elif action == "manage":
            await real_estate.show_property_management(callback.message)
        elif action.startswith("buy_"):
            property_id = action.split("_", 1)[1]
            await real_estate.buy_property(callback.message, property_id)
        elif action.startswith("sell_"):
            property_id = action.split("_", 1)[1]
            await real_estate.sell_property(callback.message, property_id)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks العقارات: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks السرقة
@router.callback_query(F.data.startswith("theft_"))
@user_required
async def theft_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks السرقة"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "steal":
            await theft.start_steal(callback.message, state)
        elif action == "security":
            await theft.show_security_menu(callback.message)
        elif action.startswith("upgrade_security_"):
            level = action.split("_", 2)[2]
            await theft.upgrade_security(callback.message, int(level))
        elif action.startswith("steal_user_"):
            user_id = action.split("_", 2)[2]
            await theft.attempt_steal(callback.message, int(user_id))
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks السرقة: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks الأسهم
@router.callback_query(F.data.startswith("stocks_"))
@user_required
async def stocks_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks الأسهم"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "buy":
            await stocks.show_buy_stocks(callback.message)
        elif action == "sell":
            await stocks.show_sell_stocks(callback.message)
        elif action == "portfolio":
            await stocks.show_user_portfolio(callback.message)
        elif action.startswith("buy_"):
            symbol = action.split("_", 1)[1]
            await stocks.start_buy_process(callback.message, symbol, state)
        elif action.startswith("sell_"):
            symbol = action.split("_", 1)[1]
            await stocks.start_sell_process(callback.message, symbol, state)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks الأسهم: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks الاستثمار
@router.callback_query(F.data.startswith("investment_"))
@user_required
async def investment_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks الاستثمار"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "create":
            await investment.show_investment_options(callback.message)
        elif action == "portfolio":
            await investment.show_portfolio(callback.message)
        elif action == "withdraw":
            await investment.show_withdrawal_options(callback.message)
        elif action.startswith("create_"):
            investment_type = action.split("_", 1)[1]
            await investment.start_investment_process(callback.message, investment_type, state)
        elif action.startswith("withdraw_"):
            investment_id = action.split("_", 1)[1]
            await investment.withdraw_investment(callback.message, int(investment_id))
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks الاستثمار: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks المزرعة
@router.callback_query(F.data.startswith("farm_"))
@user_required
async def farm_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks المزرعة"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "plant":
            await farm.show_planting_options(callback.message)
        elif action == "harvest":
            await farm.harvest_crops(callback.message)
        elif action == "status":
            await farm.show_farm_status(callback.message)
        elif action.startswith("plant_"):
            crop_type = action.split("_", 1)[1]
            await farm.start_planting_process(callback.message, crop_type, state)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks المزرعة: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks القلعة
@router.callback_query(F.data.startswith("castle_"))
@user_required
async def castle_callbacks(callback: CallbackQuery):
    """معالج callbacks القلعة"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "upgrade":
            await castle.show_upgrade_options(callback.message)
        elif action == "defend":
            await castle.show_defense_menu(callback.message)
        elif action == "attack":
            await castle.show_attack_options(callback.message)
        elif action.startswith("upgrade_"):
            building = action.split("_", 1)[1]
            await castle.upgrade_building(callback.message, building)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks القلعة: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks الترتيب
@router.callback_query(F.data.startswith("ranking_"))
@user_required
async def ranking_callbacks(callback: CallbackQuery):
    """معالج callbacks الترتيب"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "leaderboard":
            await ranking.show_leaderboard(callback.message)
        elif action == "personal":
            await ranking.show_user_ranking(callback.message)
        elif action == "weekly":
            await ranking.show_weekly_ranking(callback.message)
        elif action == "monthly":
            await ranking.show_monthly_ranking(callback.message)
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks الترتيب: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])


# Callbacks الإدارة
@router.callback_query(F.data.startswith("admin_"))
@admin_required
async def admin_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks الإدارة"""
    try:
        action = callback.data.split("_", 1)[1]
        
        if action == "stats":
            await administration.show_bot_stats(callback.message)
        elif action == "broadcast":
            await administration.start_broadcast(callback.message, state)
        elif action == "users":
            await administration.show_user_management(callback.message)
        elif action == "backup":
            await administration.create_backup(callback.message)
        elif action.startswith("ban_"):
            user_id = action.split("_", 1)[1]
            await administration.ban_user(callback.message, int(user_id))
        elif action.startswith("unban_"):
            user_id = action.split("_", 1)[1]
            await administration.unban_user(callback.message, int(user_id))
        else:
            await callback.answer("❌ إجراء غير معروف")
            return
            
        await callback.answer()
        
    except Exception as e:
        logging.error(f"خطأ في callbacks الإدارة: {e}")
        await callback.answer(SYSTEM_MESSAGES["error"])

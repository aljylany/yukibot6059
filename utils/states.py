"""
حالات البوت FSM States
Bot FSM States for aiogram
"""

from aiogram.fsm.state import State, StatesGroup


class BanksStates(StatesGroup):
    """حالات البنوك"""
    waiting_bank_selection = State()
    waiting_deposit_amount = State()
    waiting_withdraw_amount = State()
    waiting_transfer_user = State()
    waiting_transfer_amount = State()


class PropertyStates(StatesGroup):
    """حالات العقارات"""
    waiting_property_choice = State()
    waiting_sell_confirmation = State()
    waiting_property_location = State()
    waiting_property_upgrade = State()


class TheftStates(StatesGroup):
    """حالات السرقة"""
    waiting_target_user = State()
    waiting_security_upgrade = State()
    waiting_theft_confirmation = State()


class StocksStates(StatesGroup):
    """حالات الأسهم"""
    waiting_stock_symbol = State()
    waiting_buy_quantity = State()
    waiting_sell_quantity = State()
    waiting_stock_analysis = State()


class InvestmentStates(StatesGroup):
    """حالات الاستثمار"""
    waiting_investment_amount = State()
    waiting_investment_duration = State()
    waiting_investment_type = State()
    waiting_withdrawal_confirmation = State()


class FarmStates(StatesGroup):
    """حالات المزرعة"""
    waiting_crop_type = State()
    waiting_crop_quantity = State()
    waiting_harvest_confirmation = State()
    waiting_equipment_upgrade = State()


class CastleStates(StatesGroup):
    """حالات القلعة"""
    entering_castle_name = State()
    waiting_building_choice = State()
    waiting_upgrade_confirmation = State()
    waiting_attack_target = State()
    waiting_defense_strategy = State()
    waiting_delete_confirmation = State()


class AdminStates(StatesGroup):
    """حالات الإدارة"""
    waiting_broadcast_message = State()
    waiting_user_id_action = State()
    waiting_ban_reason = State()
    waiting_maintenance_message = State()


class GeneralStates(StatesGroup):
    """حالات عامة"""
    waiting_feedback = State()
    waiting_support_message = State()
    waiting_bug_report = State()
    waiting_profile_update = State()


class PaymentStates(StatesGroup):
    """حالات الدفع"""
    waiting_payment_method = State()
    waiting_payment_amount = State()
    waiting_payment_confirmation = State()


class GameStates(StatesGroup):
    """حالات اللعبة العامة"""
    waiting_daily_bonus = State()
    waiting_lottery_ticket = State()
    waiting_minigame_choice = State()
    waiting_tournament_entry = State()


class TradingStates(StatesGroup):
    """حالات التداول"""
    waiting_trade_partner = State()
    waiting_trade_offer = State()
    waiting_trade_confirmation = State()
    waiting_auction_bid = State()


class SettingsStates(StatesGroup):
    """حالات الإعدادات"""
    waiting_language_choice = State()
    waiting_notification_settings = State()
    waiting_privacy_settings = State()
    waiting_theme_choice = State()


class ProfileStates(StatesGroup):
    """حالات الملف الشخصي"""
    waiting_username_update = State()
    waiting_bio_update = State()
    waiting_avatar_upload = State()
    waiting_contact_info = State()


class SocialStates(StatesGroup):
    """حالات التفاعل الاجتماعي"""
    waiting_friend_request = State()
    waiting_guild_creation = State()


class XOGameStates(StatesGroup):
    """حالات لعبة اكس اوه"""
    waiting_for_player = State()
    game_in_progress = State()
    game_ended = State()


class EventStates(StatesGroup):
    """حالات الأحداث الخاصة"""
    waiting_event_participation = State()
    waiting_quest_choice = State()
    waiting_challenge_acceptance = State()
    waiting_reward_claim = State()


class MarketStates(StatesGroup):
    """حالات السوق"""
    waiting_item_listing = State()
    waiting_price_setting = State()
    waiting_purchase_confirmation = State()
    waiting_negotiation_offer = State()


class LotteryStates(StatesGroup):
    """حالات اليانصيب"""
    waiting_ticket_quantity = State()
    waiting_number_selection = State()
    waiting_draw_participation = State()


class CompetitionStates(StatesGroup):
    """حالات المسابقات"""
    waiting_competition_entry = State()
    waiting_submission_upload = State()
    waiting_voting_choice = State()


class NewsStates(StatesGroup):
    """حالات الأخبار والإعلانات"""
    waiting_news_category = State()
    waiting_news_subscription = State()


class BackupStates(StatesGroup):
    """حالات النسخ الاحتياطي"""
    waiting_backup_confirmation = State()
    waiting_restore_file = State()


class SecurityStates(StatesGroup):
    """حالات الأمان"""
    waiting_password_setup = State()
    waiting_two_factor_setup = State()
    waiting_security_question = State()


class TransactionStates(StatesGroup):
    """حالات المعاملات"""
    waiting_transaction_verification = State()
    waiting_receipt_confirmation = State()
    waiting_dispute_reason = State()


class NotificationStates(StatesGroup):
    """حالات الإشعارات"""
    waiting_notification_preference = State()
    waiting_alert_setup = State()
    waiting_reminder_time = State()


class StatisticsStates(StatesGroup):
    """حالات الإحصائيات"""
    waiting_report_type = State()
    waiting_date_range = State()
    waiting_export_format = State()


class MaintenanceStates(StatesGroup):
    """حالات الصيانة"""
    waiting_maintenance_type = State()
    waiting_downtime_schedule = State()
    waiting_maintenance_completion = State()


class TestingStates(StatesGroup):
    """حالات الاختبار"""
    waiting_test_scenario = State()
    waiting_test_data = State()
    waiting_test_results = State()


class DebugStates(StatesGroup):
    """حالات التصحيح"""
    waiting_debug_command = State()
    waiting_log_level = State()
    waiting_debug_confirmation = State()


class MigrationStates(StatesGroup):
    """حالات ترحيل البيانات"""
    waiting_migration_confirmation = State()
    waiting_data_export = State()
    waiting_data_import = State()


class AnalyticsStates(StatesGroup):
    """حالات التحليلات"""
    waiting_analytics_period = State()
    waiting_metric_selection = State()
    waiting_chart_type = State()


class CustomCommandsStates(StatesGroup):
    """حالات الأوامر المخصصة"""
    waiting_keyword = State()
    waiting_response = State()

class CustomReplyStates(StatesGroup):
    """حالات الردود المخصصة"""
    waiting_for_keyword = State()
    waiting_for_response = State()
    waiting_for_scope = State()


class RankManagementStates(StatesGroup):
    """حالات إدارة الرتب المتقدمة"""
    waiting_for_rank_name = State()
    waiting_for_reason = State()
    waiting_for_target_user = State()
    waiting_for_confirmation = State()


class SmartCommandStates(StatesGroup):
    """حالات الأوامر الذكية"""
    waiting_smart_menu_choice = State()
    waiting_economic_analysis_choice = State()
    waiting_investment_strategy_choice = State()
    waiting_smart_games_choice = State()
    waiting_adaptive_quiz_choice = State()
    waiting_economic_challenge_choice = State()
    waiting_interactive_story_choice = State()
    waiting_ai_battle_choice = State()
    waiting_system_status_choice = State()
    waiting_quiz_answer = State()
    waiting_story_choice = State()
    waiting_battle_answer = State()
    waiting_challenge_answer = State()


class ReportStates(StatesGroup):
    """حالات نظام التقرير الملكي"""
    waiting_title = State()
    waiting_description = State()
    waiting_steps = State()
    waiting_expected_result = State()
    waiting_actual_result = State()
    waiting_screenshot = State()
    waiting_admin_comment = State()
    waiting_status_update = State()

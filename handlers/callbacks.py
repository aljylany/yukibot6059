"""
معالج callbacks للبوت
Bot Callbacks Handler
"""

import logging
from datetime import datetime
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext

router = Router()


@router.callback_query()
async def handle_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج شامل لجميع الـ callbacks"""
    try:
        data = callback.data
        
        # التحقق من أن data ليس None
        if not data:
            await callback.answer("❌ بيانات الزر غير صحيحة")
            return
            
        logging.info(f"🔍 CALLBACK DEBUG: تم استقبال callback_data: '{data}' من المستخدم {callback.from_user.id}")
        
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
        
        # معالجة callbacks الترقية والرتب
        if (data.startswith('promote_') or data == 'cancel_promotion' or 
            data == 'show_entertainment_ranks' or data == 'show_all_admin_ranks' or 
            data == 'show_all_ent_ranks'):
            from handlers.admin_callbacks import handle_promotion_callback, handle_rank_info_callback
            if data.startswith('promote_') or data == 'cancel_promotion' or data == 'show_entertainment_ranks':
                await handle_promotion_callback(callback, state)
            else:
                await handle_rank_info_callback(callback)
            return
        
        # معالجة callbacks لعبة الرويال
        if data.startswith('royal_join_'):
            from modules.royal_game import handle_royal_join
            await handle_royal_join(callback)
            return
        
        if data.startswith('royal_confirm_'):
            from modules.royal_game import handle_royal_confirmation
            await handle_royal_confirmation(callback)
            return
        
        # معالجة callbacks قائمة الألعاب
        if data.startswith('start_game_'):
            from modules.games_list import handle_game_start_callback
            game_command = data.replace('start_game_', '')
            await handle_game_start_callback(callback, game_command)
            return
        
        # معالجة callbacks عجلة الحظ
        if data.startswith('spin_wheel_'):
            from modules.luck_wheel_game import handle_wheel_spin
            await handle_wheel_spin(callback)
            return
        
        # معالجة callbacks مسابقة سؤال وجواب
        if data.startswith('quiz_answer_'):
            from modules.quick_quiz_game import handle_quiz_answer
            # استخراج الاختيار من البيانات
            parts = data.split('_')
            if len(parts) >= 4:
                choice = int(parts[-1])
                await handle_quiz_answer(callback, choice)
            return
        
        # معالجة callbacks لعبة ساحة الموت الأخيرة
        if data.startswith('battle_join_'):
            from modules.battle_arena_callbacks import handle_battle_join
            await handle_battle_join(callback)
            return
        
        if data.startswith('battle_start_'):
            from modules.battle_arena_callbacks import handle_battle_start
            await handle_battle_start(callback)
            return
        
        if data.startswith('battle_move_'):
            from modules.battle_arena_callbacks import handle_battle_move
            await handle_battle_move(callback)
            return
        
        if data.startswith('battle_attack_'):
            from modules.battle_arena_callbacks import handle_battle_attack
            await handle_battle_attack(callback)
            return
        
        if data.startswith('battle_defend_'):
            from modules.battle_arena_callbacks import handle_battle_defend
            await handle_battle_defend(callback)
            return
        
        if data.startswith('battle_scout_'):
            from modules.battle_arena_callbacks import handle_battle_scout
            await handle_battle_scout(callback)
            return
        
        # معالجة callbacks لعبة اكس اوه
        if data.startswith('xo_join_'):
            from modules.xo_game import handle_xo_join
            await handle_xo_join(callback)
            return
        
        if data.startswith('xo_ai_join_'):
            from modules.xo_ai_handler import handle_xo_ai_join
            await handle_xo_ai_join(callback)
            return
        
        if data.startswith('xo_move_'):
            from modules.xo_game import handle_xo_move
            await handle_xo_move(callback)
            return
        
        if data == 'xo_info':
            from modules.xo_game import handle_xo_info
            await handle_xo_info(callback)
            return
        
        # معالجة callbacks لعبة الكلمة
        if data.startswith('word_hint_'):
            from modules.word_game import handle_word_hint_callback
            await handle_word_hint_callback(callback)
            return
        
        if data.startswith('word_status_'):
            from modules.word_game import handle_word_status_callback
            await handle_word_status_callback(callback)
            return
        
        if data.startswith('word_cancel_'):
            from modules.word_game import handle_word_cancel_callback
            await handle_word_cancel_callback(callback)
            return
        
        # معالجة التنقل في قائمة الألعاب
        if data.startswith('games_nav_') or data.startswith('games_close_'):
            from modules.games_list import handle_games_navigation_callback
            await handle_games_navigation_callback(callback)
            return
        
        # معالجة callbacks لعبة الرموز
        if data.startswith('symbols_hint_'):
            from modules.symbols_game import handle_symbols_hint_callback
            await handle_symbols_hint_callback(callback)
            return
        
        if data.startswith('symbols_status_'):
            from modules.symbols_game import handle_symbols_status_callback
            await handle_symbols_status_callback(callback)
            return
        
        if data.startswith('symbols_cancel_'):
            from modules.symbols_game import handle_symbols_cancel_callback
            await handle_symbols_cancel_callback(callback)
            return
        
        # معالجة callbacks لعبة ترتيب الحروف
        if data.startswith('shuffle_hint_'):
            from modules.letter_shuffle_game import handle_shuffle_hint_callback
            await handle_shuffle_hint_callback(callback)
            return
        
        if data.startswith('shuffle_status_'):
            from modules.letter_shuffle_game import handle_shuffle_status_callback
            await handle_shuffle_status_callback(callback)
            return
        
        if data.startswith('shuffle_close_'):
            from modules.letter_shuffle_game import handle_shuffle_close_callback
            await handle_shuffle_close_callback(callback)
            return
        
        # معالجة callbacks لعبة حجر ورقة مقص
        if data.startswith('rps_choice_'):
            from modules.rock_paper_scissors_game import handle_rps_choice
            await handle_rps_choice(callback)
            return
        
        # معالجة callbacks لعبة صدق أم كذب
        if data.startswith('tf_join_'):
            from modules.true_false_game import handle_tf_join
            await handle_tf_join(callback)
            return
        
        if data.startswith('tf_answer_true_'):
            from modules.true_false_game import handle_tf_answer
            await handle_tf_answer(callback, True)
            return
        
        if data.startswith('tf_answer_false_'):
            from modules.true_false_game import handle_tf_answer
            await handle_tf_answer(callback, False)
            return
        
        # معالجة callbacks التحدي الرياضي
        if data.startswith('math_join_'):
            from modules.math_challenge_game import handle_math_join
            await handle_math_join(callback)
            return
        
        if data.startswith('math_answer_'):
            from modules.math_challenge_game import handle_math_answer
            await handle_math_answer(callback)
            return
        
        # معالجة callbacks المزرعة
        if data == 'farm_harvest':
            from modules.farm import handle_harvest_callback
            await handle_harvest_callback(callback)
            return
        
        if data == 'farm_plant':
            from modules.farm import handle_plant_callback
            await handle_plant_callback(callback)
            return
        
        if data.startswith('farm_plant_'):
            from modules.farm import handle_specific_plant_callback
            await handle_specific_plant_callback(callback)
            return
        
        # معالجة callbacks العقارات (معطلة مؤقتاً)
        if data.startswith('property_buy_') or data.startswith('property_sell_'):
            await callback.answer("🏠 نظام العقارات قيد الصيانة حالياً")
            return
        
        # معالجة callbacks نظام التقرير  
        if data.startswith('report:'):
            # استخراج البيانات
            parts = data.split(":")
            action = parts[1] if len(parts) > 1 else ""
            original_user_id = int(parts[2]) if len(parts) > 2 else None
            
            # التحقق من أن الضاغط هو المالك
            if original_user_id and callback.from_user.id != original_user_id:
                await callback.answer("⚠️ هذا الزر خاص بمن طلب التقرير فقط!", show_alert=True)
                return
            
            if action in ["critical", "major", "minor", "suggestion"]:
                # استخدام معالج التقرير المناسب مع FSM
                from handlers.bug_report_handler import handle_report_callbacks
                await handle_report_callbacks(callback, state)
                
            elif action == "stats":
                await callback.answer("📊 إحصائياتك")
                if callback.message:
                    await callback.message.edit_text("📊 **إحصائياتك في نظام التقرير**\n\n• التقارير المرسلة: 0\n• التقارير المُصلحة: 0\n• المكافآت المكتسبة: 0$\n• رتبتك: مبلغ مبتدئ")
            elif action == "my_reports":
                await callback.answer("📋 تقاريرك")
                if callback.message:
                    await callback.message.edit_text("📋 **تقاريرك الأخيرة**\n\n📝 لم تقم بإرسال أي تقارير بعد!\n\nاستخدم أمر 'تقرير' لإنشاء تقرير جديد")
            else:
                await callback.answer("✅ تم")
            return
        
        # معالجة callbacks النقابة
        if (data.startswith("guild_") or 
            data.startswith("missions_") or 
            data.startswith("shop_") or 
            data.startswith("buy_") or 
            data.startswith("cant_buy_") or
            data.startswith("start_mission_") or
            data.startswith("locked_mission_") or
            data.startswith("change_class_") or 
            data.startswith("gender_select_") or 
            data.startswith("class_select_") or 
            data == "current_class" or
            data == "mission_status" or
            data == "confirm_delete_guild" or
            data == "cancel_delete_guild"):
            from modules.guild_game import (
                handle_guild_selection, handle_gender_selection, handle_class_selection,
                show_guild_main_menu, show_personal_code, confirm_delete_guild_account,
                cancel_delete_guild_account
            )
            from modules.guild_missions import (
                show_missions_menu, show_normal_missions, show_collect_missions,
                start_mission, show_active_mission_status, handle_locked_mission
            )
            from modules.guild_shop import (
                show_shop_menu, show_weapons_shop, show_badges_shop, show_titles_shop,
                buy_item, show_inventory, handle_cant_buy
            )
            from modules.guild_upgrade import (
                show_upgrade_menu, level_up_player, show_advanced_classes,
                change_advanced_class, handle_current_class
            )
            
            # معالجة اختيار النقابة
            if data.startswith("guild_select_"):
                await handle_guild_selection(callback, state)
            
            # معالجة اختيار الجنس
            elif data.startswith("gender_select_"):
                await handle_gender_selection(callback, state)
            
            # معالجة اختيار الفئة
            elif data.startswith("class_select_"):
                await handle_class_selection(callback, state)
            
            # القوائم الرئيسية
            elif data == "guild_main_menu":
                if callback.message:
                    await show_guild_main_menu(callback.message, state, user_id=callback.from_user.id, is_callback=True)
            
            elif data == "guild_code":
                await show_personal_code(callback)
            
            # نظام المهام
            elif data == "guild_missions":
                await show_missions_menu(callback)
            
            elif data == "missions_normal":
                await show_normal_missions(callback)
            
            elif data == "missions_collect":
                await show_collect_missions(callback)
            
            elif data == "missions_medium":
                await callback.answer("🔧 مهام المستوى المتوسط قيد التطوير")
            
            elif data == "missions_legendary":
                await callback.answer("🔧 المهام الأسطورية قيد التطوير")
            
            elif (data.startswith("start_mission_normal_") or 
                  data.startswith("start_mission_collect_") or 
                  data.startswith("start_mission_medium_") or 
                  data.startswith("start_mission_legendary_")):
                await start_mission(callback)
            
            elif data == "mission_status":
                await show_active_mission_status(callback)
            
            elif data.startswith("locked_mission_"):
                await handle_locked_mission(callback)
            
            # نظام المتجر
            elif data == "guild_shop":
                await show_shop_menu(callback)
            
            elif data == "shop_weapons":
                await show_weapons_shop(callback)
            
            elif data == "shop_badges":
                await show_badges_shop(callback)
            
            elif data == "shop_titles":
                await show_titles_shop(callback)
            
            elif data == "shop_inventory":
                await show_inventory(callback)
            
            elif (data.startswith("buy_weapon_") or 
                  data.startswith("buy_badge_") or 
                  data.startswith("buy_title_") or 
                  data.startswith("buy_potion_") or 
                  data.startswith("buy_ring_") or 
                  data.startswith("buy_animal_")):
                await buy_item(callback)
            
            elif data.startswith("cant_buy_"):
                await handle_cant_buy(callback)
            
            # نظام الترقية
            elif data == "guild_upgrade":
                await show_upgrade_menu(callback)
            
            elif data == "guild_level_up":
                await level_up_player(callback)
            
            elif data == "guild_advanced_class":
                await show_advanced_classes(callback)
            
            elif data.startswith("change_class_"):
                await change_advanced_class(callback)
            
            elif data == "current_class":
                await handle_current_class(callback)
            
            # تغيير الفئة العادية
            elif data == "guild_change_class":
                await callback.answer("🔧 هذه الميزة ستكون متاحة قريباً!")
            
            # معالجة حذف حساب النقابة
            elif data == "confirm_delete_guild":
                await confirm_delete_guild_account(callback)
            
            elif data == "cancel_delete_guild":
                await cancel_delete_guild_account(callback)
            
            else:
                await callback.answer("❓ أمر نقابة غير معروف")
            
            return
        
        # معالجة callbacks أخرى
        await callback.answer("⚠️ هذا الزر غير نشط حالياً")
        
    except Exception as e:
        logging.error(f"خطأ في معالج الـ callbacks: {e}")
        try:
            await callback.answer("❌ حدث خطأ")
        except:
            pass
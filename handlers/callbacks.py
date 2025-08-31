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
        
        # معالجة callbacks العقارات
        if data.startswith('property_buy_'):
            from modules.real_estate import handle_property_buy_callback
            await handle_property_buy_callback(callback)
            return
            
        if data.startswith('property_sell_'):
            from modules.real_estate import handle_property_sell_callback
            await handle_property_sell_callback(callback)
            return
        
        # معالجة callbacks نظام التقرير  
        if data.startswith('report:'):
            from modules.bug_report_system import bug_report_system
            action = data.split(":")[1] if ":" in data else ""
            
            if action in ["critical", "major", "minor", "suggestion"]:
                await callback.answer("🔄 جار تحضير نموذج التقرير...")
                if callback.message:
                    await callback.message.edit_text(f"""
📝 **إنشاء تقرير جديد**

اكتب عنوان مختصر وواضح للتقرير:

💡 **أمثلة جيدة:**
• "البوت لا يستجيب لأمر الرصيد"
• "خطأ في حساب الفوائد البنكية"  
• "اقتراح إضافة نظام تقييم اللاعبين"

❌ **تجنب:**
• عناوين غير واضحة مثل "مشكلة" أو "خطأ"
• عناوين طويلة جداً

اكتب العنوان كرسالة عادية:
                    """)
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
        
        # معالجة callbacks أخرى
        await callback.answer("⚠️ هذا الزر غير نشط حالياً")
        
    except Exception as e:
        logging.error(f"خطأ في معالج الـ callbacks: {e}")
        try:
            await callback.answer("❌ حدث خطأ")
        except:
            pass
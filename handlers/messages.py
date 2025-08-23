"""
معالج الرسائل النصية
Bot Messages Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from database.operations import get_or_create_user, update_user_activity, get_user
from modules import banks, real_estate, theft, stocks, investment, administration, farm, castle
from modules import admin_management, group_settings, entertainment, clear_commands, fun_commands, utility_commands
from modules.special_responses import get_special_response
from modules.custom_commands import handle_add_command, handle_delete_command, handle_list_commands, handle_custom_commands_message, handle_custom_commands_states, load_custom_commands
from modules.music_search import handle_eid_music_trigger, handle_music_search, handle_add_music_command
from modules.message_handlers import (
    handle_banks_message, handle_property_message, handle_theft_message,
    handle_stocks_message, handle_investment_message, handle_farm_message,
    handle_castle_message, handle_admin_message, handle_admin_command,
    handle_clear_command, handle_lock_command, handle_unlock_command,
    handle_toggle_command
)
from modules.special_admin import handle_special_admin_commands
from modules.response_tester import handle_response_tester_commands
from modules.master_commands import handle_master_commands
from modules.group_hierarchy import handle_hierarchy_commands
from modules.utility_commands import handle_utility_commands
from utils.states import *
from utils.decorators import user_required, group_only
from config.settings import SYSTEM_MESSAGES
from config.hierarchy import MASTERS
from modules.utility_commands import WhisperStates

router = Router()


# تم نقل معالج الهمسة إلى handlers/commands.py


# معالج خاص لنص الهمسة
@router.message(WhisperStates.waiting_for_text)
async def handle_whisper_text_input(message: Message, state: FSMContext):
    """معالج خاص لنص الهمسة"""
    try:
        if message.chat.type != 'private':
            return  # فقط في الخاص
            
        from modules.utility_commands import handle_whisper_text
        await handle_whisper_text(message, state)
        
    except Exception as e:
        logging.error(f"خطأ في معالج نص الهمسة: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الهمسة")
        await state.clear()


# معالج خاص لإنشاء الحساب البنكي بدون فحص التسجيل
@router.message(F.text.contains("انشاء حساب بنكي") | F.text.contains("إنشاء حساب بنكي") | F.text.contains("انشئ حساب"))
async def handle_bank_creation_only(message: Message, state: FSMContext):
    """معالج خاص لإنشاء الحساب البنكي للمستخدمين الجدد"""
    try:
        # التحقق من أن الرسالة في مجموعة وليس في الخاص
        if message.chat.type == 'private':
            await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**\n\n➕ أضف البوت لمجموعتك وابدأ اللعب مباشرة")
            return
            
        from modules.manual_registration import handle_bank_account_creation
        await handle_bank_account_creation(message, state)
        
    except Exception as e:
        logging.error(f"خطأ في معالج إنشاء الحساب البنكي: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء الحساب البنكي")


# معالج خاص لاختيار البنك أثناء التسجيل بدون فحص user_required
@router.message(F.text.in_({"الأهلي", "الراجحي", "سامبا", "الرياض"}))
async def handle_bank_selection_state(message: Message, state: FSMContext):
    """معالج خاص لاختيار البنك أثناء عملية التسجيل"""
    try:
        current_state = await state.get_state()
        
        # التحقق من أن المستخدم في حالة اختيار البنك فقط
        if current_state == "BanksStates:waiting_bank_selection":
            # التحقق من أن الرسالة في مجموعة وليس في الخاص
            if message.chat.type == 'private':
                await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**")
                return
                
            from modules.manual_registration import handle_bank_selection
            await handle_bank_selection(message, state)
        else:
            # إذا لم يكن في حالة اختيار البنك، اتركه يمر للمعالج العادي
            return
        
    except Exception as e:
        logging.error(f"خطأ في معالج اختيار البنك: {e}")
        await message.reply("❌ حدث خطأ أثناء اختيار البنك")


@router.message(F.text)
@user_required
async def handle_text_messages(message: Message, state: FSMContext):
    """معالج الرسائل النصية العامة حسب الحالة"""
    try:
        current_state = await state.get_state()
        
        if current_state is None:
            # رسالة عادية بدون حالة محددة
            await handle_general_message(message, state)
            return
        
        # معالجة الرسائل حسب الحالة
        if current_state.startswith("Banks"):
            if current_state == "BanksStates:waiting_bank_selection":
                from modules.manual_registration import handle_bank_selection
                await handle_bank_selection(message, state)
            else:
                await handle_banks_message(message, state, current_state)
        elif current_state.startswith("Property"):
            await handle_property_message(message, state, current_state)
        elif current_state.startswith("Theft"):
            await handle_theft_message(message, state, current_state)
        elif current_state.startswith("Stocks"):
            await handle_stocks_message(message, state, current_state)
        elif current_state.startswith("Investment"):
            await handle_investment_message(message, state, current_state)
        elif current_state.startswith("Farm"):
            await handle_farm_message(message, state, current_state)
        elif current_state.startswith("Castle"):
            await handle_castle_message(message, state, current_state)
        elif current_state.startswith("Admin"):
            await handle_admin_message(message, state, current_state)
        elif current_state.startswith("CustomCommands"):
            await handle_custom_commands_states(message, state, current_state)
        elif current_state.startswith("CustomReply"):
            from modules.custom_replies import handle_keyword_input, handle_response_input
            if current_state == "CustomReplyStates:waiting_for_keyword":
                await handle_keyword_input(message, state)
            elif current_state == "CustomReplyStates:waiting_for_response":
                await handle_response_input(message, state)
        else:
            await handle_general_message(message, state)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الرسالة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])
        await state.clear()


async def handle_transfer_command(message: Message):
    """معالج أمر التحويل عبر الرد على الرسائل"""
    try:
        # التحقق من وجود الرد والرسالة
        if not message.reply_to_message or not message.text:
            await message.reply("❌ يرجى الرد على رسالة اللاعب مع كتابة المبلغ")
            return
            
        # استخراج المبلغ من النص
        text_parts = message.text.split()
        if len(text_parts) < 2:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n"
                "رد على رسالة اللاعب واكتب: تحويل [المبلغ]\n\n"
                "مثال: تحويل 500"
            )
            return
        
        try:
            amount = int(text_parts[1])
        except ValueError:
            await message.reply("❌ يرجى كتابة مبلغ صحيح\n\nمثال: تحويل 500")
            return
        
        if amount <= 0:
            await message.reply("❌ يجب أن يكون المبلغ أكبر من صفر")
            return
        
        # الحصول على معلومات المرسل والمستقبل
        if not message.from_user or not message.reply_to_message.from_user:
            await message.reply("❌ لا يمكن الحصول على معلومات المستخدمين")
            return
            
        sender_id = message.from_user.id
        receiver_id = message.reply_to_message.from_user.id
        
        if sender_id == receiver_id:
            await message.reply("❌ لا يمكنك تحويل المال لنفسك!")
            return
        
        # التحقق من وجود المرسل
        from database.operations import get_user
        sender = await get_user(sender_id)
        if not sender:
            await message.reply("❌ لم تقم بإنشاء حساب بنكي بعد!\n\nاكتب 'انشاء حساب بنكي' للبدء")
            return
        
        # التحقق من وجود المستقبل
        receiver = await get_user(receiver_id)
        if not receiver:
            receiver_name = message.reply_to_message.from_user.first_name or "المستخدم"
            await message.reply(
                f"❌ {receiver_name} لم ينشئ حساب بنكي بعد!\n"
                f"يجب عليه كتابة 'انشاء حساب بنكي' أولاً"
            )
            return
        
        # التحقق من توفر الرصيد
        if sender['balance'] < amount:
            from utils.helpers import format_number
            await message.reply(
                f"❌ رصيدك غير كافٍ!\n\n"
                f"💰 رصيدك الحالي: {format_number(sender['balance'])}$\n"
                f"💸 المبلغ المطلوب: {format_number(amount)}$"
            )
            return
        
        # تنفيذ عملية التحويل
        from database.operations import update_user_balance, add_transaction
        
        new_sender_balance = sender['balance'] - amount
        new_receiver_balance = receiver['balance'] + amount
        
        await update_user_balance(sender_id, new_sender_balance)
        await update_user_balance(receiver_id, new_receiver_balance)
        
        # تسجيل المعاملات
        receiver_name = message.reply_to_message.from_user.first_name or "مستخدم"
        sender_name = message.from_user.first_name or "مستخدم"
        
        await add_transaction(
            sender_id,
            f"تحويل إلى {receiver_name}",
            -amount,
            "transfer"
        )
        await add_transaction(
            receiver_id,
            f"تحويل من {sender_name}",
            amount,
            "transfer"
        )
        
        # رسالة التأكيد
        from utils.helpers import format_number
        success_msg = f"""
✅ **تم التحويل بنجاح!**

💸 المرسل: {sender_name}
💰 المستقبل: {receiver_name}
📊 المبلغ: {format_number(amount)}$

💵 رصيد {sender_name}: {format_number(new_sender_balance)}$
💵 رصيد {receiver_name}: {format_number(new_receiver_balance)}$
        """
        
        await message.reply(success_msg)
        
    except Exception as e:
        logging.error(f"خطأ في تحويل الأموال: {e}")
        await message.reply("❌ حدث خطأ أثناء التحويل، حاول مرة أخرى")


async def handle_deposit_with_amount(message: Message, amount_text: str):
    """معالجة أمر الإيداع مع المبلغ مباشرة"""
    try:
        from database.operations import get_user, update_user_balance, update_user_bank_balance, add_transaction
        from utils.helpers import format_number, is_valid_amount
        
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # تحديد المبلغ
        if amount_text.lower() in ['الكل', 'كل', 'all']:
            amount = user['balance']
        else:
            if not is_valid_amount(amount_text):
                await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح أو 'الكل'")
                return
            amount = int(amount_text)
        
        # التحقق من صحة المبلغ
        if amount <= 0:
            await message.reply("❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if amount > user['balance']:
            await message.reply(f"❌ ليس لديك رصيد كافٍ!\n💰 رصيدك الحالي: {format_number(user['balance'])}$")
            return
        
        # تنفيذ الإيداع
        new_cash_balance = user['balance'] - amount
        new_bank_balance = user['bank_balance'] + amount
        
        await update_user_balance(message.from_user.id, new_cash_balance)
        await update_user_bank_balance(message.from_user.id, new_bank_balance)
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            "إيداع في البنك",
            amount,
            "bank_deposit"
        )
        
        await message.reply(
            f"✅ **تم الإيداع بنجاح!**\n\n"
            f"💵 المبلغ المودع: {format_number(amount)}$\n"
            f"💰 رصيدك النقدي: {format_number(new_cash_balance)}$\n"
            f"🏦 رصيد البنك: {format_number(new_bank_balance)}$"
        )
        
    except Exception as e:
        logging.error(f"خطأ في الإيداع المباشر: {e}")
        await message.reply("❌ حدث خطأ في عملية الإيداع")


async def handle_withdraw_with_amount(message: Message, amount_text: str):
    """معالجة أمر السحب مع المبلغ مباشرة"""
    try:
        from database.operations import get_user, update_user_balance, update_user_bank_balance, add_transaction
        from utils.helpers import format_number, is_valid_amount
        
        user = await get_user(message.from_user.id)
        if not user:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
        
        # تحديد المبلغ
        if amount_text.lower() in ['الكل', 'كل', 'all']:
            amount = user['bank_balance']
        else:
            if not is_valid_amount(amount_text):
                await message.reply("❌ مبلغ غير صحيح. يرجى إدخال رقم صحيح أو 'الكل'")
                return
            amount = int(amount_text)
        
        # التحقق من صحة المبلغ
        if amount <= 0:
            await message.reply("❌ المبلغ يجب أن يكون أكبر من صفر")
            return
        
        if amount > user['bank_balance']:
            await message.reply(f"❌ ليس لديك رصيد كافٍ في البنك!\n🏦 رصيد البنك: {format_number(user['bank_balance'])}$")
            return
        
        # تنفيذ السحب
        new_cash_balance = user['balance'] + amount
        new_bank_balance = user['bank_balance'] - amount
        
        await update_user_balance(message.from_user.id, new_cash_balance)
        await update_user_bank_balance(message.from_user.id, new_bank_balance)
        
        # إضافة معاملة
        await add_transaction(
            message.from_user.id,
            "سحب من البنك",
            amount,
            "bank_withdraw"
        )
        
        await message.reply(
            f"✅ **تم السحب بنجاح!**\n\n"
            f"💵 المبلغ المسحوب: {format_number(amount)}$\n"
            f"💰 رصيدك النقدي: {format_number(new_cash_balance)}$\n"
            f"🏦 رصيد البنك: {format_number(new_bank_balance)}$"
        )
        
    except Exception as e:
        logging.error(f"خطأ في السحب المباشر: {e}")
        await message.reply("❌ حدث خطأ في عملية السحب")


async def handle_theft_command(message: Message):
    """معالجة أمر السرقة عبر الرد على الرسائل"""
    try:
        # التحقق من وجود الرد والمستخدم
        if not message.reply_to_message or not message.from_user:
            await message.reply("❌ يرجى الرد على رسالة اللاعب الذي تريد سرقته")
            return
            
        # التحقق من أن المستخدم مسجل
        from database.operations import get_user
        thief = await get_user(message.from_user.id)
        if not thief:
            await message.reply("❌ يرجى التسجيل أولاً باستخدام 'انشاء حساب بنكي'")
            return
            
        # الحصول على معرف الضحية
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username or "مجهول"
        target_name = message.reply_to_message.from_user.first_name or "مستخدم"
        
        # التحقق من عدم سرقة النفس
        if target_user_id == message.from_user.id:
            await message.reply("❌ لا يمكنك سرقة نفسك! 🤔")
            return
            
        # التحقق من أن الضحية مسجلة
        target = await get_user(target_user_id)
        if not target:
            await message.reply(f"❌ المستخدم {target_name} غير مسجل في البوت")
            return
            
        # التحقق من أن الضحية لديها أموال
        if target['balance'] <= 0:
            await message.reply(f"😅 المستخدم {target_name} لا يملك أموال نقدية للسرقة!")
            return
            
        # إجراء محاولة السرقة
        await attempt_theft_on_target(message, thief, target, target_user_id, target_name)
        
    except Exception as e:
        logging.error(f"خطأ في سرقة الرد: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة السرقة")


async def attempt_theft_on_target(message: Message, thief: dict, target: dict, target_user_id: int, target_name: str):
    """محاولة سرقة المستخدم المستهدف"""
    try:
        from database.operations import update_user_balance, add_transaction
        from utils.helpers import format_number
        import random
        
        # حساب احتمالية النجاح بناءً على مستوى الأمان
        SECURITY_LEVELS = {
            1: {"name": "أساسي", "protection": 10},
            2: {"name": "متوسط", "protection": 30},
            3: {"name": "قوي", "protection": 50},
            4: {"name": "فائق", "protection": 70},
            5: {"name": "أسطوري", "protection": 90}
        }
        
        target_security_level = target.get('security_level', 1)
        target_protection = SECURITY_LEVELS.get(target_security_level, SECURITY_LEVELS[1])['protection']
        
        # احتمالية النجاح (كلما زاد الأمان، قل احتمال النجاح)
        thief_skill = random.randint(1, 100)
        success_chance = max(10, 80 - target_protection)
        
        if thief_skill <= success_chance:
            # السرقة نجحت!
            max_steal_amount = min(target['balance'], 10000)  # الحد الأقصى للسرقة
            stolen_amount = random.randint(int(max_steal_amount * 0.1), int(max_steal_amount * 0.3))
            stolen_amount = max(1, stolen_amount)  # على الأقل 1$
            
            # تحديث الأرصدة
            new_thief_balance = thief['balance'] + stolen_amount
            new_target_balance = target['balance'] - stolen_amount
            
            await update_user_balance(message.from_user.id, new_thief_balance)
            await update_user_balance(target_user_id, new_target_balance)
            
            # إضافة المعاملة
            await add_transaction(
                target_user_id,
                f"سرقة بواسطة {message.from_user.first_name or 'لص مجهول'}",
                -stolen_amount,
                "theft"
            )
            await add_transaction(
                message.from_user.id,
                f"سرقة ناجحة من {target_name}",
                stolen_amount,
                "theft"
            )
            
            # رسائل نجاح متنوعة
            success_messages = [
                "🎉 نجحت في السرقة!",
                "💰 عملية ناجحة!",
                "🔓 سرقة محترفة!",
                "⭐ مهمة مكتملة!",
                "🏆 لص ماهر!"
            ]
            
            success_msg = random.choice(success_messages)
            
            await message.reply(
                f"{success_msg}\n\n"
                f"💰 المبلغ المسروق: {format_number(stolen_amount)}$\n"
                f"👤 من: {target_name}\n"
                f"💵 رصيدك الجديد: {format_number(new_thief_balance)}$\n\n"
                f"🎭 كن حذراً... قد يكتشف أمرك!"
            )
            
            # إشعار الضحية (إذا أمكن)
            try:
                await message.bot.send_message(
                    target_user_id,
                    f"🚨 **تم سرقتك!**\n\n"
                    f"💸 المبلغ المسروق: {format_number(stolen_amount)}$\n"
                    f"👤 بواسطة: {message.from_user.first_name or 'لص مجهول'}\n"
                    f"💰 رصيدك الجديد: {format_number(new_target_balance)}$\n\n"
                    f"🛡 نصيحة: قم بترقية أمانك أو ضع أموالك في البنك!"
                )
            except:
                pass  # إذا فشل إرسال الإشعار
                
        else:
            # السرقة فشلت!
            penalty = random.randint(50, 200)  # غرامة الفشل
            
            if thief['balance'] >= penalty:
                new_thief_balance = thief['balance'] - penalty
                await update_user_balance(message.from_user.id, new_thief_balance)
                
                await add_transaction(
                    message.from_user.id,
                    f"غرامة فشل سرقة {target_name}",
                    -penalty,
                    "theft_penalty"
                )
                
                penalty_msg = f"\n💸 غرامة الفشل: {format_number(penalty)}$"
            else:
                penalty_msg = ""
            
            # رسائل فشل متنوعة
            fail_messages = [
                "😅 تم اكتشافك!",
                "🚨 فشلت المحاولة!",
                "🛡 الضحية محمية جيداً!",
                "❌ لم تنجح هذه المرة!",
                "🔒 أمان قوي جداً!"
            ]
            
            fail_msg = random.choice(fail_messages)
            
            await message.reply(
                f"{fail_msg}\n\n"
                f"👤 فشل في سرقة: {target_name}\n"
                f"🛡 مستوى الأمان عالي جداً!"
                f"{penalty_msg}\n\n"
                f"💡 نصيحة: حاول مع ضحية أقل حماية!"
            )
            
    except Exception as e:
        logging.error(f"خطأ في محاولة السرقة: {e}")
        await message.reply("❌ حدث خطأ أثناء محاولة السرقة")


async def handle_general_message(message: Message, state: FSMContext):
    """معالجة الرسائل العامة - الكلمات المفتاحية فقط"""
    text = message.text.lower() if message.text else ""
    
    # تتبع عدد الرسائل الحقيقي في المجموعات
    if message.chat.type in ['group', 'supergroup'] and message.from_user:
        try:
            from database.operations import increment_user_message_count
            await increment_user_message_count(message.from_user.id, message.chat.id)
        except Exception as msg_count_error:
            logging.error(f"خطأ في تتبع عدد الرسائل: {msg_count_error}")
    
    # تحديث نشاط المستخدم وإضافة XP للرسائل
    try:
        await update_user_activity(message.from_user.id)
        from modules.simple_level_display import add_simple_xp
        await add_simple_xp(message.from_user.id, 1)
    except Exception as activity_error:
        logging.error(f"خطأ في تحديث النشاط أو XP: {activity_error}")
    
    # دليل المستويات الشامل
    if text in ['المستويات', 'دليل المستويات', 'شرح المستويات', 'كيفية التقدم']:
        from modules.levels_guide import show_levels_guide
        await show_levels_guide(message)
        return
    
    # فحص أوامر المستوى أولاً
    if any(keyword in text for keyword in ["مستواي", "مستوايا", "مستوى", "level", "xp", "تفاعلي"]):
        try:
            from modules.enhanced_xp_handler import handle_level_command
            await handle_level_command(message)
        except Exception as level_error:
            logging.error(f"خطأ في نظام المستوى المحسن: {level_error}")
            # استخدام النظام البديل
            from modules.simple_level_display import show_simple_level
            await show_simple_level(message)
        return
    
    # أمر التقدم البسيط - تم نقله لأسفل لتجنب التضارب
    # if "تقدمي" in text:
    #     from modules.simple_level_display import handle_simple_progress_command
    #     await handle_simple_progress_command(message)
    #     return
    
    # فحص الردود المهينة للصلاحيات أولاً (أعلى أولوية)
    from modules.permission_handler import handle_permission_check
    if await handle_permission_check(message):
        return
    
    # فحص أوامر الأسياد المطلقة (أعلى أولوية للأسياد فقط)
    if await handle_master_commands(message):
        return
    
    # فحص موسيقى العيد
    if await handle_eid_music_trigger(message):
        return
    
    # فحص البحث عن الموسيقى
    if await handle_music_search(message):
        return
    
    # فحص إضافة موسيقى (للمديرين)
    if await handle_add_music_command(message):
        return
    
    # فحص الأوامر المخصصة قبل الردود الخاصة
    if await handle_custom_commands_message(message):
        return
    
    # فحص الردود المخصصة
    from modules.custom_replies import check_for_custom_replies, handle_show_custom_replies
    if await check_for_custom_replies(message):
        # إضافة XP للمستخدم عند استخدام رد مخصص
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "custom_reply")
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP: {xp_error}")
        return
    
    # فحص أوامر إدارة الأوامر المخصصة
    if await handle_add_command(message, state):
        return
    
    if await handle_delete_command(message):
        return
        
    if message.text and (message.text.strip() == 'الأوامر المخصصة' or message.text.strip() == 'الاوامر المخصصة'):
        await handle_list_commands(message)
        return
    
    # فحص الردود (خاصة أو عامة) بعد الأوامر المهمة
    if message.from_user:
        response = get_special_response(message.from_user.id, text)
        if response:
            await message.reply(response)
            return
    
    # التحقق من طلب إنشاء حساب بنكي
    if any(phrase in text for phrase in ['انشاء حساب بنكي', 'إنشاء حساب بنكي', 'انشئ حساب', 'حساب بنكي جديد']):
        from modules.manual_registration import handle_bank_account_creation
        await handle_bank_account_creation(message, state)
        # إضافة XP للتسجيل
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "banking")
        except:
            pass
        return
    
    # فحص أوامر الاستثمار المحسنة
    try:
        from modules.investment_enhanced import handle_enhanced_investment_text
        if await handle_enhanced_investment_text(message):
            # إضافة XP للاستثمار
            try:
                from modules.enhanced_xp_handler import add_xp_for_activity
                await add_xp_for_activity(message.from_user.id, "investment")
            except:
                pass
            return
    except Exception as inv_error:
        logging.error(f"خطأ في نظام الاستثمار المحسن: {inv_error}")
    
    # فحص أوامر العمليات المصرفية
    if any(keyword in text for keyword in ["البنك", "بنك", "حسابي", "محفظتي", "المحفظة", "ايداع", "إيداع", "سحب"]):
        # إضافة XP للعمليات المصرفية
        try:
            from modules.enhanced_xp_handler import add_xp_for_activity
            await add_xp_for_activity(message.from_user.id, "banking")
        except:
            pass
    
    # فحص أوامر إدارة الردود الخاصة للمديرين
    if await handle_special_admin_commands(message):
        return
    
    # فحص أوامر اختبار نظام الردود للمديرين
    if await handle_response_tester_commands(message):
        return
    
    # تم نقل فحص أوامر الأسياد لأعلى لتجنب التداخل مع نظام الردود
    
    # فحص أوامر الهيكل الإداري
    if await handle_hierarchy_commands(message):
        return
    
    # فحص الأوامر المساعدة والأدوات
    if await handle_utility_commands(message):
        return
    
    # === أمر عرض قائمة الأوامر الشاملة ===
    if (text == 'الأوامر' or text == 'الاوامر' or text == 'قائمة الأوامر' or 
        text == 'قائمة الاوامر' or text == 'جميع الأوامر' or text == 'كل الأوامر'):
        try:
            commands_file = FSInputFile('commands_list.txt', filename='yuki_commands.txt')
            await message.reply_document(
                document=commands_file,
                caption="📋 **قائمة أوامر بوت يوكي الشاملة**\n\n"
                       "🔍 **هذا الملف يحتوي على:**\n"
                       "• جميع أوامر البوت مقسمة حسب الصلاحيات\n"
                       "• شرح مفصل لكل أمر\n"
                       "• التحديثات الأخيرة للنظام\n\n"
                       "💡 **نصيحة:** احفظ هذا الملف للرجوع إليه وقت الحاجة!"
            )
        except Exception as e:
            logging.error(f"خطأ في إرسال ملف الأوامر: {e}")
            await message.reply("❌ حدث خطأ في تحميل ملف الأوامر")
        return
    
    # === أمر عرض قائمة الأسياد (للأسياد فقط) ===
    if text == 'الأسياد' or text == 'الاسياد' or text == 'قائمة الأسياد' or text == 'قائمة الاسياد':
        user_id = message.from_user.id if message.from_user else 0
        if user_id in MASTERS:
            try:
                masters_info = "👑 **قائمة الأسياد الحاليين:**\n\n"
                
                for i, master_id in enumerate(MASTERS, 1):
                    try:
                        # جلب معلومات المستخدم من تيليجرام
                        chat_info = await message.bot.get_chat(master_id)
                        
                        # تكوين الاسم الكامل
                        display_name = ""
                        if chat_info.first_name:
                            display_name = chat_info.first_name
                        if chat_info.last_name:
                            display_name += f" {chat_info.last_name}"
                        if not display_name.strip():
                            display_name = f"سيد {i}"
                        
                        # إنشاء رابط قابل للنقر
                        mention_link = f"[{display_name}](tg://user?id={master_id})"
                        
                        masters_info += f"{i}. 👑 {mention_link}\n"
                        
                        # إضافة اسم المستخدم إذا كان موجوداً
                        if chat_info.username:
                            masters_info += f"   📱 @{chat_info.username}\n"
                        
                        masters_info += f"   🆔 `{master_id}`\n\n"
                        
                    except Exception as e:
                        # في حالة عدم القدرة على جلب معلومات المستخدم
                        masters_info += f"{i}. 👑 [سيد {i}](tg://user?id={master_id})\n"
                        masters_info += f"   🆔 `{master_id}`\n\n"
                        logging.warning(f"لم يتم العثور على معلومات المستخدم {master_id}: {e}")
                
                masters_info += f"📊 **إجمالي الأسياد:** {len(MASTERS)}\n\n"
                masters_info += "🔴 **الأسياد لديهم صلاحيات مطلقة في جميع المجموعات**\n"
                masters_info += "⚡ **يمكنهم تنفيذ أي أمر وإدارة جميع الأنظمة**\n\n"
                masters_info += "💡 **اضغط على أي اسم للانتقال إلى حساب السيد**"
                
                await message.reply(masters_info, parse_mode="Markdown")
                
            except Exception as e:
                logging.error(f"خطأ في عرض قائمة الأسياد: {e}")
                await message.reply("❌ حدث خطأ في تحميل قائمة الأسياد")
        else:
            await message.reply("❌ هذا الأمر متاح للأسياد فقط")
        return
    
    # === أوامر إضافة الردود المخصصة ===
    if text == 'اضف رد' or text == 'إضف رد' or text == 'اضافة رد':
        from modules.custom_replies import start_add_custom_reply
        await start_add_custom_reply(message, state)
        return
    
    # === أوامر عرض الردود المخصصة ===
    if (text == 'الردود المخصصة' or text == 'عرض الردود' or 
        text == 'قائمة الردود' or text == 'الردود المخصصه' or 
        text == 'عرض ردود'):
        await handle_show_custom_replies(message)
        return
    
    # === أوامر حذف الردود المخصصة ===
    if text.startswith('حذف رد '):
        from modules.custom_replies import handle_delete_custom_reply
        if await handle_delete_custom_reply(message):
            return
    
    # === تم نقل فحص الردود المخصصة لأعلى لتجنب التكرار ===
    
    # البحث عن كلمات مفتاحية محددة بتطابق دقيق
    words = text.split()
    
    if any(word in words for word in ['راتب', 'مرتب', 'راتبي']):
        await banks.collect_daily_salary(message)
    elif text.startswith('تحويل') and message.reply_to_message:
        await handle_transfer_command(message)
    elif text == 'حذف حسابه' and message.reply_to_message:
        # أمر حذف الحساب للأسياد فقط
        from modules.master_commands import delete_account_command
        await delete_account_command(message)
    elif text == 'اصلح مستواه' and message.reply_to_message:
        # أمر إصلاح مستوى المستخدم للأسياد فقط
        from modules.master_commands import fix_user_level_command
        await fix_user_level_command(message)
    elif (text in ['سرقة'] or text.startswith('سرقة')) and message.reply_to_message:
        await handle_theft_command(message)
    elif (text in ['زررف', 'زرف'] or text.startswith('زررف') or text.startswith('زرف')) and message.reply_to_message:
        # فحص إذا كان الرد على البوت نفسه
        if message.reply_to_message.from_user and message.reply_to_message.from_user.is_bot:
            sarcastic_responses = [
                "😂 تحاول تزرفني؟ أنا يوكي الذكي لا أُزرف!",
                "🙄 زرف؟ أنا بوت محترم، جرب مع إنسان!",
                "😏 أظن أنك تخلط الأوراق، البوتات لا تُزرف!",
                "🤭 ههههه محاولة لطيفة، لكني يوكي المقاوم للزرف!",
                "😎 زرف البوت؟ هذه فكرة مضحكة جداً!",
                "🎭 تمثيلية حلوة، لكن أنا لست قابلاً للزرف!",
                "⚡ أنا يوكي، البوت الوحيد المضاد للزرف!"
            ]
            await message.reply(random.choice(sarcastic_responses))
        else:
            await handle_theft_command(message)
    elif any(word in words for word in ['رصيد', 'فلوس', 'مال']):
        await banks.show_balance(message)
    elif text.startswith('ايداع') and len(words) > 1:
        # معالجة أمر الإيداع مع المبلغ مثل "ايداع 100"
        await handle_deposit_with_amount(message, words[1])
    elif text.startswith('سحب') and len(words) > 1:
        # معالجة أمر السحب مع المبلغ مثل "سحب 100"
        await handle_withdraw_with_amount(message, words[1])
    elif any(word in words for word in ['بنك', 'ايداع', 'سحب']):
        await banks.show_bank_menu(message)
    # === أوامر العقارات الجديدة ===
    elif text.startswith('شراء عقار ') and len(words) >= 4:
        # معالجة أمر "شراء عقار [النوع] [الكمية]"
        try:
            property_name = words[2]
            quantity = int(words[3])
            await real_estate.handle_buy_property_text(message, property_name, quantity)
        except (ValueError, IndexError):
            await message.reply("❌ استخدم الصيغة الصحيحة: شراء عقار [النوع] [الكمية]\n\nمثال: شراء عقار شقة 2")
    elif text.startswith('بيع عقار ') and len(words) >= 4:
        # معالجة أمر "بيع عقار [النوع] [الكمية]"
        try:
            property_name = words[2]
            quantity = int(words[3])
            await real_estate.handle_sell_property_text(message, property_name, quantity)
        except (ValueError, IndexError):
            await message.reply("❌ استخدم الصيغة الصحيحة: بيع عقار [النوع] [الكمية]\n\nمثال: بيع عقار بيت 1")
    elif text in ['قائمة العقارات', 'انواع العقارات', 'أنواع العقارات']:
        await real_estate.show_properties_list(message)
    elif text in ['عقاراتي', 'ممتلكاتي']:
        await real_estate.show_property_management(message)
    elif text in ['احصائيات العقارات', 'إحصائيات العقارات']:
        await real_estate.show_property_management(message)
    elif any(word in words for word in ['عقار', 'بيت']) and not any(castle_word in words for castle_word in ['قلعة', 'موارد']):
        await real_estate.show_property_menu(message)
    elif text.startswith('ترقية امان تأكيد'):
        await theft.upgrade_security_level(message)
    elif text.startswith('ترقية الامان') or text in ['ترقية الأمان', 'ترقية امان']:
        await theft.show_security_upgrade(message)
    elif text in ['احصائيات سرقة', 'إحصائيات سرقة', 'احصائياتي سرقة']:
        await theft.show_theft_stats(message)
    elif text in ['افضل لصوص', 'أفضل لصوص', 'افضل اللصوص', 'أفضل اللصوص', 'ترتيب لصوص']:
        await theft.show_top_thieves(message)
    elif any(word in words for word in ['سرقة', 'سرق']) or text == 'امان':
        await theft.show_security_menu(message)
    
    # === أوامر الاستثمار ===
    elif text == 'استثمار فلوسي':
        # الاستثمار البسيط - استثمار كل الفلوس
        from modules.simple_investment import handle_simple_investment_command
        await handle_simple_investment_command(message, text)
    elif text.startswith('استثمار ') and len(words) == 2 and words[1].replace('.', '').replace(',', '').isdigit():
        # الاستثمار البسيط - استثمار مبلغ محدد
        from modules.simple_investment import handle_simple_investment_command
        await handle_simple_investment_command(message, text)
    elif text.startswith('استثمار ') and len(words) >= 2:
        # التحقق من نوع الاستثمار
        if words[1] in ['فلوسي'] or words[1].replace('.', '').replace(',', '').isdigit():
            # الاستثمار البسيط
            from modules.simple_investment import handle_simple_investment_command
            await handle_simple_investment_command(message, text)
        else:
            # الاستثمار المتقدم في الشركات أو عرض القائمة
            from modules import investment
            await investment.show_investment_menu(message)
    elif text == 'استثمار':
        # عرض قائمة الاستثمار عند كتابة "استثمار" فقط
        from modules import investment
        await investment.show_investment_menu(message)
    elif text == 'استثمار جديد':
        from modules import investment
        await investment.show_investment_options(message)
    elif text == 'محفظة الاستثمارات':
        from modules import investment
        await investment.show_portfolio(message)
    elif text == 'سحب استثمار':
        from modules import investment
        await investment.show_withdrawal_options(message)
    elif text == 'تقرير الاستثمارات':
        from modules import investment
        await investment.show_investment_report(message)
    elif text == 'معلومات الاستثمار البسيط':
        from modules.simple_investment import show_investment_info
        await show_investment_info(message)
    
    # === أوامر الأسهم ===
    elif text == 'شراء اسهم':
        await stocks.show_buy_stocks(message)
    elif text == 'بيع اسهم':
        await stocks.show_sell_stocks(message)
    elif text == 'محفظة الاسهم' or text == 'محفظتي':
        await stocks.show_portfolio(message)
    elif text == 'اسهمي':
        await stocks.show_simple_portfolio(message)
    elif text == 'اسعار الاسهم':
        await stocks.show_stock_prices(message)
    elif text == 'قائمة الاسهم':
        await stocks.list_available_stocks(message)
    elif text.startswith('شراء سهم ') or text.startswith('شراء اسهم '):
        await stocks.buy_stock_command(message)
    elif text.startswith('بيع سهم ') or text.startswith('بيع اسهم '):
        await stocks.sell_stock_command(message)
    elif any(word in words for word in ['اسهم', 'محفظة']):
        await stocks.show_stocks_menu(message)
    
    # === أوامر المزرعة ===
    elif text == 'قائمة المزروعات':
        await farm.list_crops(message)
    elif text.startswith('زراعة '):
        await farm.plant_crop_command(message)
    elif text == 'زراعة':
        await farm.list_crops(message)
    elif text == 'حصاد':
        await farm.harvest_command(message)
    elif text == 'حالة المزرعة':
        await farm.show_farm_status(message)
    elif text == 'شراء بذور':
        await farm.show_seeds_shop(message)
    elif any(word in words for word in ['مزرعة']):
        await farm.show_farm_menu(message)
    elif any(phrase in text for phrase in ['انشاء قلعة', 'إنشاء قلعة', 'انشئ قلعة']):
        await castle.create_castle_command(message, state)
    elif text.strip() == 'قلعة':
        await castle.show_castle_menu(message)
    elif any(phrase in text for phrase in ['بحث عن كنز', 'بحث كنز', 'ابحث كنز']):
        await castle.treasure_hunt_command(message)
    elif any(phrase in text for phrase in ['طور القلعة', 'تطوير القلعة', 'ترقية القلعة']):
        await castle.upgrade_castle_command(message)
    elif any(phrase in text for phrase in ['احصائيات القلعة', 'إحصائيات القلعة', 'احصائيات قلعة']):
        await castle.castle_stats_command(message)
    elif any(phrase in text for phrase in ['متجر القلعة', 'متجر قلعة', 'شراء موارد']) or (text.strip() == 'متجر' and 'قلعة' in words):
        await castle.show_castle_shop(message)
    elif text.startswith('شراء ') and any(word in text for word in ['ذهب', 'حجارة', 'حجار', 'عمال', 'موارد']):
        await castle.purchase_item_command(message)
    elif text.startswith('شراء '):
        await real_estate.show_property_menu(message)
    elif any(phrase in text for phrase in ['حذف قلعتي', 'احذف قلعتي']):
        await castle.delete_castle_command(message)
    elif text.strip() in ['تأكيد', 'نعم']:
        await castle.confirm_delete_castle_command(message)
    elif text.strip() == 'لا':
        await castle.cancel_delete_castle_command(message)
    elif any(phrase in text for phrase in ['حسابي', 'حساب اللاعب', 'معلوماتي', 'تفاصيلي']):
        await castle.show_player_profile(message)
    elif any(phrase in text for phrase in ['اخفاء قلعتي', 'إخفاء قلعتي', 'اخفي قلعتي']):
        await castle.hide_castle_command(message)
    elif any(phrase in text for phrase in ['اظهار قلعتي', 'إظهار قلعتي', 'اظهر قلعتي']):
        await castle.show_castle_command(message)
    elif any(phrase in text for phrase in ['قائمة القلاع', 'القلاع المتاحة', 'عرض القلاع']):
        await castle.list_available_castles(message)
    elif text.startswith('هجوم '):
        await castle.attack_castle_command(message)
    elif any(phrase in text for phrase in ['سجل المعارك', 'معارك القلعة', 'سجل الحروب']):
        await castle.castle_battles_log_command(message)
    elif any(word in words for word in ['ترتيب', 'متصدرين', 'رانكنغ']):
        from modules import ranking
        await ranking.show_leaderboard(message)
    
    # === نظام البقشيش ===
    elif text.startswith('بقشيش '):
        from modules import tip_system
        await tip_system.give_tip_command(message)
    elif text == 'بقشيش':
        from modules import tip_system
        await tip_system.tip_menu(message)
    
    # === أوامر الإدارة والرفع/التنزيل ===
    elif text.startswith('رفع '):
        await handle_admin_command(message, text)
    elif text.startswith('تنزيل '):
        await handle_admin_command(message, text)
    elif text == 'تنزيل الكل':
        await admin_management.handle_rank_promotion(message, "", "تنزيل الكل")
    
    # === أوامر المسح ===
    elif text.startswith('مسح '):
        await handle_clear_command(message, text)
    
    # === أوامر الطرد والحظر ===
    elif text == 'حظر' or text.startswith('حظر '):
        await admin_management.handle_ban_user(message)
    elif text == 'طرد' or text.startswith('طرد '):
        await admin_management.handle_kick_user(message)
    elif text == 'كتم' or text.startswith('كتم '):
        await admin_management.handle_mute_user(message)
    elif text.startswith('تحذير '):
        await admin_management.handle_warn_user(message)
    
    # === أوامر إلغاء الحظر والكتم ===
    elif text == 'الغاء حظر' or text.startswith('الغاء حظر ') or text == 'إلغاء حظر' or text.startswith('إلغاء حظر '):
        await admin_management.handle_unban_user(message)
    elif text == 'الغاء كتم' or text.startswith('الغاء كتم ') or text == 'إلغاء كتم' or text.startswith('إلغاء كتم '):
        await admin_management.handle_unmute_user(message)
    
    # === أوامر عرض القوائم ===
    elif text == 'المحظورين' or text == 'قائمة المحظورين':
        await admin_management.show_banned_users(message)
    elif text == 'المكتومين' or text == 'قائمة المكتومين':
        await admin_management.show_muted_users(message)
    
    # === أوامر القفل والفتح ===
    elif text.startswith('قفل '):
        await handle_lock_command(message, text)
    elif text.startswith('فتح '):
        await handle_unlock_command(message, text)
    
    # === أوامر التفعيل والتعطيل ===
    elif text.startswith('تفعيل '):
        await handle_toggle_command(message, text, 'تفعيل')
    elif text.startswith('تعطيل '):
        await handle_toggle_command(message, text, 'تعطيل')
    
    # === أوامر العرض ===
    elif text in ['المالكين الاساسيين', 'المالكين', 'المنشئين', 'المدراء', 'الادمنيه', 'المميزين']:
        await admin_management.show_group_ranks(message, text)
    elif text == 'الاعدادات':
        await group_settings.show_group_settings(message)
    elif text == 'القوانين':
        await group_settings.show_group_rules(message)
    
    # === أوامر إدارة المجموعة الجديدة ===
    elif text == 'الرابط':
        from modules.group_management import show_group_link
        await show_group_link(message)
    elif text == 'المالكين الأساسيين':
        from modules.group_management import show_owners
        await show_owners(message)
    elif text == 'المالكين':
        from modules.group_management import show_group_owners
        await show_group_owners(message)
    elif text == 'المنشئين':
        from modules.group_management import show_creators
        await show_creators(message)
    elif text == 'المدراء':
        from modules.group_management import show_managers
        await show_managers(message)
    elif text == 'الإدمنية' or text == 'الادمنيه':
        from modules.group_management import show_admins
        await show_admins(message)
    elif text == 'المميزين':
        from modules.group_management import show_vips
        await show_vips(message)
    elif text == 'المحظورين':
        from modules.group_management import show_banned_users
        await show_banned_users(message)
    elif text == 'المكتومين':
        from modules.group_management import show_muted_users
        await show_muted_users(message)
    elif text == 'معلوماتي':
        from modules.group_management import show_my_info
        await show_my_info(message)
    elif text == 'الحمايه' or text == 'الحماية':
        from modules.group_management import show_group_protection
        await show_group_protection(message)
    elif text == 'الاعدادات':
        from modules.group_management import show_group_settings
        await show_group_settings(message)
    elif text == 'المجموعه' or text == 'المجموعة':
        from modules.group_management import show_group_info
        await show_group_info(message)
    
    # === أوامر تحميل الوسائط ===
    elif text == 'تفعيل التحميل':
        from modules.media_download import toggle_download
        await toggle_download(message, True)
    elif text == 'تعطيل التحميل':
        from modules.media_download import toggle_download
        await toggle_download(message, False)
    elif text.startswith('تيك '):
        from modules.media_download import download_tiktok
        await download_tiktok(message)
    elif text.startswith('تويتر '):
        from modules.media_download import download_twitter
        await download_twitter(message)
    elif text.startswith('ساوند '):
        from modules.media_download import download_soundcloud
        await download_soundcloud(message)
    elif text.startswith('بحث '):
        from modules.media_download import search_youtube
        await search_youtube(message)
    
    # === أوامر قفل الوسائط ===
    elif text == 'قفل الصور':
        from modules.media_locks import lock_photos
        await lock_photos(message)
    elif text == 'فتح الصور':
        from modules.media_locks import unlock_photos
        await unlock_photos(message)
    elif text == 'قفل الفيديو':
        from modules.media_locks import lock_videos
        await lock_videos(message)
    elif text == 'فتح الفيديو':
        from modules.media_locks import unlock_videos
        await unlock_videos(message)
    elif text == 'قفل الصوت':
        from modules.media_locks import lock_voice
        await lock_voice(message)
    elif text == 'فتح الصوت':
        from modules.media_locks import unlock_voice
        await unlock_voice(message)
    elif text == 'قفل الملصقات':
        from modules.media_locks import lock_stickers
        await lock_stickers(message)
    elif text == 'فتح الملصقات':
        from modules.media_locks import unlock_stickers
        await unlock_stickers(message)
    elif text == 'قفل المتحركه':
        from modules.media_locks import lock_gifs
        await lock_gifs(message)
    elif text == 'فتح المتحركه':
        from modules.media_locks import unlock_gifs
        await unlock_gifs(message)
    elif text == 'قفل الروابط':
        from modules.media_locks import lock_links
        await lock_links(message)
    elif text == 'فتح الروابط':
        from modules.media_locks import unlock_links
        await unlock_links(message)
    elif text == 'قفل التوجيه':
        from modules.media_locks import lock_forwarding
        await lock_forwarding(message)
    elif text == 'فتح التوجيه':
        from modules.media_locks import unlock_forwarding
        await unlock_forwarding(message)
    elif text == 'قفل الكل':
        from modules.media_locks import lock_all_media
        await lock_all_media(message)
    elif text == 'فتح الكل':
        from modules.media_locks import unlock_all_media
        await unlock_all_media(message)
    
    # === أوامر إدارة الروابط ===
    elif text.startswith('ضع رابط '):
        from modules.link_management import set_group_link
        await set_group_link(message)
    elif text == 'مسح الرابط':
        from modules.link_management import delete_group_link
        await delete_group_link(message)
    elif text == 'انشاء رابط' or text == 'إنشاء رابط':
        from modules.link_management import create_invite_link
        await create_invite_link(message)
    elif text == 'المجموعه':
        await group_settings.show_group_info(message)
    
    # === لوحات التحكم والإحصائيات ===
    elif text == 'لوحة التحكم' or text == 'الاحصائيات':
        from modules import dashboard
        await dashboard.show_main_dashboard(message)
    elif text == 'احصائيات مالية' or text == 'الاحصائيات المالية':
        from modules import dashboard
        await dashboard.show_financial_dashboard(message)
    elif text == 'احصائيات النشاط' or text == 'نشاط المجموعة':
        from modules import dashboard
        await dashboard.show_activity_dashboard(message)
    elif text == 'احصائيات الاشراف' or text == 'احصائيات الإشراف':
        from modules import dashboard
        await dashboard.show_moderation_stats(message)
    elif text == 'تقرير شامل' or text == 'التقرير الشامل':
        from modules import dashboard
        await dashboard.show_comprehensive_report(message)
    elif text == 'صحة المجموعة' or text == 'نقاط الصحة':
        from modules import dashboard
        await dashboard.show_health_dashboard(message)
    
    # === أوامر التسلية ===
    elif any(rank in text for rank in ['هطف', 'بثر', 'حمار', 'كلب', 'كلبه', 'عتوي', 'عتويه', 'لحجي', 'لحجيه', 'خروف', 'خفيفه', 'خفيف']):
        await handle_entertainment_rank_command(message, text)
    elif text.startswith('زواج '):  # زواج مع مبلغ المهر
        await entertainment.handle_marriage(message, "زواج")
    elif text == 'زواج':  # زواج بدون مبلغ (سيطلب المبلغ)
        await entertainment.handle_marriage(message, "زواج")
    elif text == 'طلاق':
        await entertainment.handle_marriage(message, "طلاق")
    elif text == 'موافقة':
        await entertainment.handle_marriage_response(message, "موافقة")
    elif text == 'رفض':
        await entertainment.handle_marriage_response(message, "رفض")
    elif text in ['زوجي', 'زوجتي']:
        await entertainment.show_marriage_status(message)
    elif text == 'سيارتي':
        await fun_commands.my_car(message)
    elif text == 'منزلي':
        await fun_commands.my_house(message)
    elif text == 'عمري':
        await fun_commands.my_age(message)
    elif text == 'طولي':
        await fun_commands.my_height(message)
    elif text == 'وزني':
        await fun_commands.my_weight(message)
    elif text == 'تحبني':
        await fun_commands.do_you_love_me(message)
    elif text == 'تكرهني':
        await fun_commands.do_you_hate_me(message)
    elif text == 'شبيهي' or text == 'شبيهتي':
        await fun_commands.get_similar(message)
    elif text == 'اهدي لي':
        await fun_commands.give_gift(message)
    elif text == 'شرايك في افتاري':
        await fun_commands.avatar_opinion(message)
    elif text.startswith('نسبة الحب'):
        parts = text.split()
        if len(parts) >= 3:
            await fun_commands.love_percentage(message, parts[2], parts[3] if len(parts) > 3 else "شخص آخر")
    elif text == 'نسبة الغباء' and message.reply_to_message:
        await fun_commands.stupidity_percentage(message)
    elif text == 'نسبة انوثتها' and message.reply_to_message:
        await fun_commands.femininity_percentage(message)
    elif text == 'نسبة رجولته' and message.reply_to_message:
        await fun_commands.masculinity_percentage(message)
    elif text.startswith('مايكي السحري'):
        question = text.replace('مايكي السحري', '').strip()
        await fun_commands.magic_yuki(message, question)
    
    # === أوامر معلومات المستخدم والتفاعل ===
    elif text == 'كشف' and message.reply_to_message:
        await utility_commands.show_target_user_info(message)
    elif text in ['تفاعلي', 'ترتيب التفاعل', 'ترتيب المجموعة']:
        await utility_commands.show_group_activity_ranking(message)
    elif text in ['رسائلي', 'عدد رسائلي']:
        await utility_commands.show_my_messages_count(message)
    elif text in ['رسائله', 'عدد رسائله'] and message.reply_to_message:
        await utility_commands.show_target_user_messages(message)
    elif text in ['تفاعله', 'نشاطه'] and message.reply_to_message:
        await utility_commands.show_target_user_activity(message)
    elif text == 'رتبتي':
        from modules import user_info
        await user_info.show_my_rank(message)
    elif text == 'رتبته' and message.reply_to_message:
        from modules import user_info
        await user_info.show_user_rank(message)
    elif text == 'فلوسي':
        from modules import user_info
        await user_info.show_my_balance(message)
    elif text == 'حسابي':
        # استخدام النظام الموحد لعرض الحساب
        try:
            from modules.unified_level_system import show_unified_user_info
            info_text = await show_unified_user_info(message, message.from_user.id)
            await message.reply(info_text)
        except Exception as info_error:
            logging.error(f"خطأ في النظام الموحد: {info_error}")
            # الرجوع للنظام القديم في حالة الخطأ
            from modules import user_info
            await user_info.show_detailed_account_info(message)
    elif text == 'فلوسه' and message.reply_to_message:
        from modules import user_info
        await user_info.show_user_balance(message)
    elif text == 'مستواي' or text == 'تقدمي':
        # استخدام النظام الموحد لعرض المستوى
        try:
            from modules.unified_level_system import get_unified_user_level
            level_info = await get_unified_user_level(message.from_user.id)
            
            level_text = f"""🌟 **مستواك الحالي:**

🌍 العالم: {level_info['world_name']}
⭐ المستوى: {level_info['level']}
🎭 الرتبة: {level_info['level_name']}
✨ XP: {level_info['xp']}

💡 كل نشاط يمنحك XP!"""
            
            await message.reply(level_text)
        except Exception as level_error:
            logging.error(f"خطأ في النظام الموحد للمستوى: {level_error}")
            # الرجوع للنظام القديم في حالة الخطأ
            from modules import user_info
            await user_info.show_my_level(message)
    elif text == 'مستواه' and message.reply_to_message:
        from modules import user_info
        await user_info.show_user_level(message)
    
    # === أوامر خدمية ===
    elif text == 'من ضافني':
        await utility_commands.who_added_me(message)
    elif text == 'البايو بالرد' and message.reply_to_message:
        await utility_commands.get_bio(message)
    elif text.startswith('قوقل '):
        query = text.replace('قوقل ', '').strip()
        await utility_commands.google_search(message, query)
    elif text.startswith('تطبيق '):
        app_name = text.replace('تطبيق ', '').strip()
        await utility_commands.download_app(message, app_name)
    elif text.startswith('تحميل لعبه '):
        game_name = text.replace('تحميل لعبه ', '').strip()
        await utility_commands.download_game(message, game_name)
    elif text.startswith('زخرف '):
        text_to_decorate = text.replace('زخرف ', '').strip()
        await fun_commands.decorative_text(message, text_to_decorate)
    elif text == 'قرآن' or text == 'آيه':
        await utility_commands.islamic_quran(message)
    elif text == 'حديث':
        await utility_commands.islamic_hadith(message)
    elif text in ['اقتباسات', 'اقتباس']:
        await fun_commands.send_quote(message)
    elif text in ['شعر', 'قصائد']:
        await fun_commands.send_poetry(message)
    elif text == 'صراحه':
        await fun_commands.truth_dare(message)
    elif text == 'لو خيروك':
        await fun_commands.would_you_rather(message)
    elif text == 'كت تويت':
        await fun_commands.kit_tweet(message)
    elif text == 'تحويل' and message.reply_to_message:
        await utility_commands.convert_formats(message)
    elif text.startswith('انشاء تيم '):
        team_name = text.replace('انشاء تيم ', '').strip()
        await utility_commands.create_team(message, team_name)
    elif text.startswith('دخول التيم '):
        team_code = text.replace('دخول التيم ', '').strip()
        await utility_commands.join_team(message, team_code)
    elif text.startswith('ارسل '):
        # زاجل - إرسال رسالة خاصة
        parts = text.split()
        if len(parts) >= 3 and parts[1].startswith('@'):
            username = parts[1][1:]  # إزالة @
            message_text = ' '.join(parts[2:])
            await utility_commands.send_message_private(message, username, message_text)
    elif text.startswith('صيح '):
        username = text.replace('صيح ', '').strip()
        await utility_commands.disturb_user(message, username)
    elif text == 'صيح' and message.reply_to_message:
        await utility_commands.disturb_user(message)
    
    # === أوامر المسح الإضافية ===
    elif text == 'مسح المحظورين':
        await clear_commands.clear_banned(message)
    elif text == 'مسح المكتومين':
        await clear_commands.clear_muted(message)
    elif text == 'مسح قائمة المنع':
        await clear_commands.clear_ban_words(message)
    elif text == 'مسح الردود':
        await clear_commands.clear_replies(message)
    elif text == 'مسح الاوامر المضافه':
        await clear_commands.clear_custom_commands(message)
    elif text == 'مسح الايدي':
        await clear_commands.clear_id_template(message)
    elif text == 'مسح الترحيب':
        await clear_commands.clear_welcome(message)
    elif text == 'مسح الرابط':
        await clear_commands.clear_link(message)
    
    # إزالة الرد الافتراضي - البوت لن يرد على الرسائل غير المعروفة


# === دوال مساعدة للأوامر الإدارية ===

async def handle_admin_command(message: Message, text: str):
    """معالج أوامر الرفع والتنزيل"""
    try:
        parts = text.split()
        if len(parts) < 2:
            return
            
        action = parts[0]  # رفع أو تنزيل
        rank_text = ' '.join(parts[1:])  # باقي النص
        
        # تحديد نوع الرتبة
        rank_map = {
            'مالك اساسي': 'مالك اساسي',
            'مالك': 'مالك', 
            'منشئ': 'منشئ',
            'مدير': 'مدير',
            'ادمن': 'ادمن',
            'مشرف': 'مشرف',
            'مميز': 'مميز'
        }
        
        rank_type = None
        for key, value in rank_map.items():
            if key in rank_text:
                rank_type = value
                break
        
        if rank_type:
            await admin_management.handle_rank_promotion(message, rank_type, action)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الأمر الإداري: {e}")


async def handle_custom_reply_states(message: Message, state: FSMContext, current_state: str):
    """معالجة حالات الردود المخصصة"""
    try:
        from modules.custom_replies import handle_keyword_input, handle_response_input
        
        if current_state == "CustomReplyStates:waiting_for_keyword":
            await handle_keyword_input(message, state)
        elif current_state == "CustomReplyStates:waiting_for_response":
            await handle_response_input(message, state)
    except Exception as e:
        logging.error(f"خطأ في معالجة حالات الردود المخصصة: {e}")
        await message.reply("❌ حدث خطأ في إضافة الرد المخصص")
        await state.clear()


async def handle_clear_command(message: Message, text: str):
    """معالج أوامر المسح"""
    try:
        clear_text = text.replace('مسح ', '').strip()
        
        if clear_text == 'الكل':
            await admin_management.handle_clear_ranks(message, 'الكل')
        elif clear_text == 'المالكين':
            await admin_management.handle_clear_ranks(message, 'مالك')
        elif clear_text == 'المنشئين':
            await admin_management.handle_clear_ranks(message, 'منشئ')
        elif clear_text == 'المدراء':
            await admin_management.handle_clear_ranks(message, 'مدير')
        elif clear_text == 'الادمنيه':
            await admin_management.handle_clear_ranks(message, 'ادمن')
        elif clear_text == 'المميزين':
            await admin_management.handle_clear_ranks(message, 'مميز')
        elif clear_text.isdigit():
            # مسح عدد من الرسائل
            count = int(clear_text)
            await group_settings.handle_delete_messages(message, count)
        elif clear_text == 'بالرد' and message.reply_to_message:
            # مسح الرسالة المرد عليها
            try:
                # التحقق من أن البوت لديه صلاحيات الحذف
                chat_member = await message.bot.get_chat_member(message.chat.id, message.bot.id)
                if not chat_member.can_delete_messages:
                    await message.reply("❌ البوت لا يملك صلاحيات حذف الرسائل")
                    return
                
                # حذف الرسالة المرد عليها
                await message.bot.delete_message(
                    chat_id=message.chat.id, 
                    message_id=message.reply_to_message.message_id
                )
                
                # حذف أمر المسح أيضاً للتنظيف
                try:
                    await message.delete()
                except:
                    pass  # إذا فشل حذف أمر المسح فلا مشكلة
                    
            except Exception as e:
                logging.error(f"خطأ في حذف الرسالة بالرد: {e}")
                await message.reply("❌ حدث خطأ أثناء حذف الرسالة")
            
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر المسح: {e}")


async def handle_lock_command(message: Message, text: str):
    """معالج أوامر القفل"""
    try:
        setting = text.replace('قفل ', '').strip()
        await group_settings.handle_lock_command(message, setting, 'قفل')
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر القفل: {e}")


async def handle_unlock_command(message: Message, text: str):
    """معالج أوامر الفتح"""
    try:
        setting = text.replace('فتح ', '').strip()
        await group_settings.handle_lock_command(message, setting, 'فتح')
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر الفتح: {e}")


async def handle_toggle_command(message: Message, text: str, action: str):
    """معالج أوامر التفعيل والتعطيل"""
    try:
        setting = text.replace(f'{action} ', '').strip()
        await group_settings.handle_toggle_command(message, setting, action)
    except Exception as e:
        logging.error(f"خطأ في معالجة أمر {action}: {e}")


async def handle_entertainment_rank_command(message: Message, text: str):
    """معالج أوامر رتب التسلية"""
    try:
        # تحديد الرتبة والعمل
        entertainment_ranks = ['هطف', 'بثر', 'حمار', 'كلب', 'كلبه', 'عتوي', 'عتويه', 'لحجي', 'لحجيه', 'خروف', 'خفيفه', 'خفيف']
        
        rank_type = None
        action = None
        
        # البحث عن نوع الرتبة
        for rank in entertainment_ranks:
            if rank in text:
                rank_type = rank
                break
        
        # تحديد العمل (رفع أو تنزيل)
        if text.startswith('رفع '):
            action = 'رفع'
        elif text.startswith('تنزيل '):
            action = 'تنزيل'
        
        if rank_type and action:
            await entertainment.handle_entertainment_rank(message, rank_type, action)
        elif rank_type and not action:
            # عرض قائمة الرتبة
            await entertainment.show_entertainment_ranks(message, rank_type)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة رتب التسلية: {e}")


async def handle_bank_account_creation(message: Message, state: FSMContext):
    """معالج إنشاء الحساب البنكي"""
    try:
        # التحقق من أن المحادثة في مجموعة
        if message.chat.type == 'private':
            await message.reply(
                "🚫 يجب إنشاء الحساب البنكي في المجموعة فقط!\n\n"
                "➕ أضف البوت لمجموعتك واكتب 'انشاء حساب بنكي' هناك"
            )
            return
            
        # التحقق من وجود المستخدم مسبقاً
        user = await get_user(message.from_user.id)
        if user:
            await message.reply(
                f"✅ أهلاً بعودتك {message.from_user.first_name}!\n\n"
                f"لديك حساب بنكي بالفعل برصيد: {user['balance']}$\n"
                f"اكتب 'رصيد' لعرض تفاصيل حسابك"
            )
            return
        
        # إنشاء حساب جديد مع نظام اختيار البنك
        await banks.start_bank_selection(message)
        
        # تعيين الحالة لانتظار اختيار البنك
        await state.set_state(BanksStates.waiting_bank_selection)
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء الحساب البنكي: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء حسابك، حاول مرة أخرى")


async def handle_banks_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل البنوك"""
    if current_state == BanksStates.waiting_bank_selection.state:
        await banks.process_bank_selection(message, state)
    elif current_state == BanksStates.waiting_deposit_amount.state:
        await banks.process_deposit_amount(message, state)
    elif current_state == BanksStates.waiting_withdraw_amount.state:
        await banks.process_withdraw_amount(message, state)
    elif current_state == BanksStates.waiting_transfer_user.state:
        await banks.process_transfer_user(message, state)
    elif current_state == BanksStates.waiting_transfer_amount.state:
        await banks.process_transfer_amount(message, state)


async def handle_property_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل العقارات"""
    if current_state == PropertyStates.waiting_property_choice.state:
        await real_estate.process_property_choice(message, state)
    elif current_state == PropertyStates.waiting_sell_confirmation.state:
        await real_estate.process_sell_confirmation(message, state)


async def handle_theft_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل السرقة"""
    if current_state == TheftStates.waiting_target_user.state:
        await theft.process_target_user(message, state)


async def handle_stocks_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الأسهم"""
    if current_state == StocksStates.waiting_stock_symbol.state:
        await stocks.process_stock_symbol(message, state)
    elif current_state == StocksStates.waiting_buy_quantity.state:
        await stocks.process_buy_quantity(message, state)
    elif current_state == StocksStates.waiting_sell_quantity.state:
        await stocks.process_sell_quantity(message, state)


async def handle_investment_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الاستثمار"""
    if current_state == InvestmentStates.waiting_investment_amount.state:
        await investment.process_investment_amount(message, state)
    elif current_state == InvestmentStates.waiting_investment_duration.state:
        await investment.process_investment_duration(message, state)


async def handle_farm_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل المزرعة"""
    if current_state == FarmStates.waiting_crop_quantity.state:
        await farm.process_crop_quantity(message, state)


async def handle_castle_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل القلعة"""
    from utils.states import CastleStates
    
    if current_state == CastleStates.entering_castle_name.state:
        await castle.handle_castle_name_input(message, state)
    elif current_state == CastleStates.waiting_upgrade_confirmation.state:
        await castle.process_upgrade_confirmation(message, state)


async def handle_admin_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الإدارة"""
    if current_state == AdminStates.waiting_broadcast_message.state:
        await administration.process_broadcast_message(message, state)
    elif current_state == AdminStates.waiting_user_id_action.state:
        await administration.process_user_id_action(message, state)


# معالج الصور والملفات
@router.message(F.photo | F.document | F.video | F.audio)
@user_required
async def handle_media_messages(message: Message):
    """معالج الرسائل المتعددة الوسائط"""
    await message.reply(
        "📷 تم استلام الملف!\n\n"
        "حالياً لا يدعم البوت معالجة الملفات، "
        "لكن يمكنك استخدام الأوامر النصية للتفاعل مع البوت."
    )


# معالج الملصقات
@router.message(F.sticker)
@user_required
async def handle_sticker_messages(message: Message):
    """معالج الملصقات"""
    stickers = [
        "🎮", "💰", "🏦", "🏠", "🔓", "📈", "🌾", "🏰", "⭐"
    ]
    import random
    
    await message.reply(
        f"{random.choice(stickers)} ملصق جميل!\n\n"
        "استخدم /help لعرض الأوامر المتاحة."
    )


# معالج جهات الاتصال
@router.message(F.contact)
@user_required
async def handle_contact_messages(message: Message):
    """معالج جهات الاتصال"""
    await message.reply(
        "📞 شكراً لمشاركة جهة الاتصال!\n\n"
        "حالياً لا نحتاج لهذه المعلومات، "
        "يمكنك استخدام الأوامر العادية للتفاعل مع البوت."
    )


# معالج المواقع الجغرافية
@router.message(F.location)
@user_required
async def handle_location_messages(message: Message):
    """معالج المواقع الجغرافية"""
    await message.reply(
        "📍 تم استلام موقعك الجغرافي!\n\n"
        "في المستقبل قد نضيف ميزات تعتمد على الموقع، "
        "لكن حالياً يمكنك استخدام الأوامر العادية."
    )

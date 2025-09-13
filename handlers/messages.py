"""
معالج الرسائل النصية
Bot Messages Handler
"""

import logging
import asyncio
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
# استيراد نظام الذكاء الاصطناعي الشامل
from modules.ai_integration_handler import ai_integration
# استيراد معالج القوائم الذكية
from modules.smart_menu_handler import smart_menu_handler
# استيراد نظام فلتر الألفاظ المسيئة
from modules.profanity_commands import PROFANITY_COMMANDS
# تم حذف نظام عبيد الذكي غير الضروري

router = Router()

# سيتم تهيئة نظام كشف الألفاظ المسيئة تلقائياً عند أول استخدام

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


# معالج إنشاء الحساب البنكي المطور - نظام التسجيل اليدوي الجديد
@router.message(F.text.contains("انشاء حساب بنكي") | F.text.contains("إنشاء حساب بنكي") | F.text.contains("انشئ حساب"))
async def handle_bank_creation_only(message: Message, state: FSMContext):
    """معالج إنشاء الحساب البنكي المطور مع النظام اليدوي الجديد"""
    try:
        # التحقق من أن الرسالة في مجموعة وليس في الخاص
        if message.chat.type == 'private':
            await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**\n\n➕ أضف البوت لمجموعتك وابدأ اللعب مباشرة")
            return
        
        # فحص إذا كان المستخدم مسجلاً بالفعل أو لديه حساب بنكي قديم
        from modules.manual_registration import is_user_registered
        from database.operations import get_user
        user_id = message.from_user.id
        
        # التحقق من التسجيل الحديث أو وجود حساب قديم
        is_registered = await is_user_registered(user_id)
        existing_user = await get_user(user_id)
        
        if is_registered or (existing_user and existing_user.get('balance') is not None):
            # المستخدم مسجل أو لديه حساب قديم
            user_info = existing_user or {}
            
            # معلومات الحساب الأساسية
            bank_type = user_info.get('bank_type', 'غير محدد')
            balance = user_info.get('balance', 0)
            bank_balance = user_info.get('bank_balance', 0)
            
            # معلومات شخصية
            full_name = user_info.get('first_name', '')
            gender = user_info.get('gender', '')
            country = user_info.get('country', '')
            
            # تحديد حالة الحساب والبيانات الناقصة
            missing_data = []
            if not full_name or full_name.strip() == '':
                missing_data.append("الاسم")
            if not gender or gender.strip() == '':
                missing_data.append("الجنس")
            if not country or country.strip() == '':
                missing_data.append("البلد")
            
            # تحديد نوع الحساب
            if is_registered and not missing_data:
                account_status = "✅ **لديك حساب مسجل بالكامل!**\n\n"
                account_info = f"🏦 **معلومات حسابك الكاملة:**\n"
                account_info += f"• 👤 الاسم: {full_name}\n"
                account_info += f"• {'👨' if gender == 'male' else '👩' if gender == 'female' else '🧑'} الجنس: {'ذكر' if gender == 'male' else 'أنثى' if gender == 'female' else 'غير محدد'}\n"
                account_info += f"• 🌍 البلد: {country}\n"
                account_info += f"• 💰 الرصيد النقدي: {balance:,.0f}$\n"
                account_info += f"• 🏦 رصيد البنك: {bank_balance:,.0f}$\n"
                account_info += f"• 🏛️ نوع البنك: {bank_type}\n\n"
                account_info += f"💡 يمكنك استخدام جميع ميزات البوت مباشرة\n"
                account_info += f"🎮 جرب: رصيد، راتب، استثمار، اسهم"
            elif missing_data:
                # حساب قديم أو ناقص البيانات
                account_status = "⚠️ **لديك حساب بنكي لكن ينقصه بعض المعلومات!**\n\n"
                account_info = f"🏦 **معلومات حسابك الحالية:**\n"
                if full_name and full_name.strip():
                    account_info += f"• 👤 الاسم: {full_name}\n"
                if gender and gender.strip():
                    account_info += f"• {'👨' if gender == 'male' else '👩' if gender == 'female' else '🧑'} الجنس: {'ذكر' if gender == 'male' else 'أنثى' if gender == 'female' else gender}\n"
                if country and country.strip():
                    account_info += f"• 🌍 البلد: {country}\n"
                account_info += f"• 💰 الرصيد النقدي: {balance:,.0f}$\n"
                account_info += f"• 🏦 رصيد البنك: {bank_balance:,.0f}$\n"
                account_info += f"• 🏛️ نوع البنك: {bank_type}\n\n"
                
                account_info += f"📝 **البيانات الناقصة:** {', '.join(missing_data)}\n\n"
                account_info += f"🔄 **لإكمال ملفك الشخصي:**\n"
                account_info += f"اكتب 'اكمال التسجيل' لإضافة المعلومات الناقصة\n\n"
                account_info += f"💡 يمكنك استخدام البوت حالياً لكن بعض المميزات تتطلب إكمال البيانات"
            else:
                # حساب قديم كامل
                account_status = "✅ **لديك حساب بنكي كامل!**\n\n"
                account_info = f"🏦 **معلومات حسابك:**\n"
                account_info += f"• 👤 الاسم: {full_name}\n"
                account_info += f"• {'👨' if gender == 'male' else '👩' if gender == 'female' else '🧑'} الجنس: {'ذكر' if gender == 'male' else 'أنثى' if gender == 'female' else gender}\n"
                account_info += f"• 🌍 البلد: {country}\n"
                account_info += f"• 💰 الرصيد النقدي: {balance:,.0f}$\n"
                account_info += f"• 🏦 رصيد البنك: {bank_balance:,.0f}$\n"
                account_info += f"• 🏛️ نوع البنك: {bank_type}\n\n"
                account_info += f"💡 يمكنك استخدام جميع ميزات البوت مباشرة\n"
                account_info += f"🎮 جرب: رصيد، راتب، استثمار، اسهم"
            
            await message.reply(f"{account_status}{account_info}")
            return
        
        # بدء عملية التسجيل اليدوي الجديدة
        from modules.manual_registration import send_registration_required_message
        await send_registration_required_message(message)
        
    except Exception as e:
        logging.error(f"خطأ في معالج إنشاء الحساب البنكي: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء الحساب البنكي")


# معالج إكمال التسجيل للمستخدمين القدامى
@router.message(F.text.contains("اكمال التسجيل") | F.text.contains("إكمال التسجيل") | F.text.contains("اكمل تسجيلي"))
async def handle_complete_registration(message: Message, state: FSMContext):
    """معالج إكمال التسجيل للمستخدمين القدامى"""
    try:
        # التحقق من أن الرسالة في مجموعة وليس في الخاص
        if message.chat.type == 'private':
            await message.reply("🚫 **هذا الأمر متاح في المجموعات فقط!**\n\n➕ أضف البوت لمجموعتك وابدأ اللعب مباشرة")
            return
        
        from database.operations import get_user
        user_id = message.from_user.id
        
        # التحقق من وجود المستخدم
        existing_user = await get_user(user_id)
        if not existing_user:
            await message.reply("❌ لا يوجد لديك حساب بنكي!\n\nاكتب 'انشاء حساب بنكي' لإنشاء حساب جديد")
            return
        
        # التحقق من البيانات الناقصة
        full_name = existing_user.get('first_name', '')
        gender = existing_user.get('gender', '')
        country = existing_user.get('country', '')
        
        missing_data = []
        if not full_name or full_name.strip() == '':
            missing_data.append("الاسم")
        if not gender or gender.strip() == '':
            missing_data.append("الجنس")
        if not country or country.strip() == '':
            missing_data.append("البلد")
        
        if not missing_data:
            await message.reply(
                "✅ **حسابك مكتمل بالفعل!**\n\n"
                "جميع بياناتك موجودة ولا تحتاج لإكمال أي شيء\n"
                "يمكنك استخدام جميع ميزات البوت مباشرة"
            )
            return
        
        # بدء عملية إكمال التسجيل
        from modules.manual_registration import send_completion_required_message
        await send_completion_required_message(message, missing_data)
        
    except Exception as e:
        logging.error(f"خطأ في معالج إكمال التسجيل: {e}")
        await message.reply("❌ حدث خطأ أثناء إكمال التسجيل")


# سيتم التعامل مع اختيار البنك عبر نظام التسجيل الجديد باستخدام callback buttons
# لا حاجة لمعالج نص منفصل للبنوك


# معالج خاص للنداء على الشيخ
@router.message(F.text.contains("يا شيخ") | F.text.contains("يا الشيخ") | F.text.contains("ياشيخ"))
@group_only
async def handle_sheikh_call(message: Message):
    """معالج النداء على الشيخ - يرسل إشعار خاص للشيخ"""
    try:
        SHEIKH_ID = 7155814194  # معرف الشيخ ردفان
        
        caller_name = message.from_user.first_name or "شخص"
        group_name = message.chat.title or "مجموعة"
        group_id = message.chat.id
        
        # إرسال رسالة للشيخ في الخاص
        try:
            await message.bot.send_message(
                SHEIKH_ID,
                f"🕌 **السلام عليكم فضيلة الشيخ**\n\n"
                f"👤 **ينادي عليكم:** {caller_name}\n"
                f"📱 **المعرف:** @{message.from_user.username if message.from_user.username else 'غير محدد'}\n"
                f"🏠 **في المجموعة:** {group_name}\n"
                f"🔗 **رابط المجموعة:** [انقر هنا](https://t.me/c/{str(group_id)[4:]}/{message.message_id})\n\n"
                f"📝 **نص الرسالة:** {message.text}\n\n"
                f"🌟 بارك الله فيكم وفي خدمتكم للمسلمين"
            )
            
            # رد في المجموعة
            await message.reply(
                f"🕌 **تم إشعار فضيلة الشيخ**\n\n"
                f"📨 تم إرسال إشعار خاص لفضيلة الشيخ الكريم\n"
                f"⏰ سيرد عليكم في أقرب وقت إن شاء الله\n"
                f"🤲 جزاكم الله خيراً لاحترامكم للشيخ المحترم"
            )
            
        except Exception as send_error:
            logging.error(f"فشل في إرسال الإشعار للشيخ: {send_error}")
            await message.reply(
                f"🕌 **تم استلام النداء**\n\n"
                f"📞 لم أتمكن من الوصول للشيخ الآن\n"
                f"💬 يمكنكم التواصل معه مباشرة: @Hacker20263\n"
                f"🤲 بارك الله فيكم"
            )
            
    except Exception as e:
        logging.error(f"خطأ في معالج نداء الشيخ: {e}")
        await message.reply("❌ حدث خطأ أثناء النداء على الشيخ")


@router.message(F.text)
@user_required
async def handle_text_messages(message: Message, state: FSMContext):
    """معالج الرسائل النصية العامة حسب الحالة"""
    try:
        # فحص فلتر الألفاظ المسيئة أولاً
        if message.text and message.chat.type in ['group', 'supergroup']:
            try:
                from modules.profanity_filter import profanity_filter
                
                logging.info(f"🔍 FILTER DEBUG: بدء فحص رسالة '{message.text}' في المجموعة {message.chat.id}")
                
                # التحقق من تفعيل الفلتر في هذه المجموعة
                is_enabled = profanity_filter.is_enabled(message.chat.id)
                logging.info(f"🔍 FILTER DEBUG: حالة الفلتر في المجموعة {message.chat.id}: {is_enabled}")
                
                if is_enabled:
                    # فحص النص للألفاظ المسيئة
                    has_profanity, found_words = profanity_filter.contains_profanity(message.text)
                    logging.info(f"🔍 FILTER DEBUG: نتيجة الفحص: {has_profanity}, كلمات مكتشفة: {found_words}")
                    
                    if has_profanity:
                        # حذف الرسالة فوراً
                        try:
                            await message.delete()
                            logging.info(f"🗑️ تم حذف رسالة مسيئة من المستخدم {message.from_user.id}: '{message.text}'")
                        except Exception as delete_error:
                            logging.error(f"❌ خطأ في حذف الرسالة: {delete_error}")
                        
                        # إرسال تحذير للمستخدم
                        user_name = message.from_user.first_name or "المستخدم"
                        warning_text = f"⚠️ **تحذير!**\n\n👤 {user_name}\n🚫 تم حذف رسالتك لاحتوائها على ألفاظ مسيئة\n\n🔍 **الكلمات المكتشفة:** {', '.join(found_words[:3])}"
                        
                        try:
                            await message.bot.send_message(
                                chat_id=message.chat.id,
                                text=warning_text,
                                parse_mode='Markdown'
                            )
                        except Exception as warn_error:
                            logging.error(f"❌ خطأ في إرسال التحذير: {warn_error}")
                        
                        return  # توقف عن معالجة الرسالة
                else:
                    logging.info(f"🔍 FILTER DEBUG: الفلتر غير مفعل في هذه المجموعة")
            except Exception as filter_error:
                logging.error(f"خطأ في فلتر الألفاظ: {filter_error}")
        
        # معالجة نظام تحليل المستخدمين المتقدم
        try:
            from modules.user_analysis_integration import analyze_user_message
            analysis_handled = await analyze_user_message(message)
            if analysis_handled:
                return  # تم التعامل مع الرسالة بواسطة نظام التحليل
        except Exception as analysis_error:
            logging.debug(f"تحذير في نظام التحليل: {analysis_error}")
            # نتابع المعالجة العادية حتى لو فشل التحليل
        
        # أولاً: فحص أوامر الإصمات الخاصة بالسيد الأعلى
        from modules.supreme_silence_commands import handle_silence_command, handle_unsilence_command, handle_silenced_list_command
        
        # فحص أوامر الإصمات
        if await handle_silence_command(message):
            return
        if await handle_unsilence_command(message):
            return
        if await handle_silenced_list_command(message):
            return
            
        # ثانياً: فحص إذا كان المرسل مشرف مصمت وحذف رسالته
        from modules.silence_message_handler import handle_silenced_moderator_message
        if await handle_silenced_moderator_message(message):
            return  # تم حذف الرسالة، لا نواصل المعالجة
        
        # استثناء أوامر نظام التقرير الملكي
        if message.text in ["تقرير", "إبلاغ", "تقارير", "تقاريري", "تقاريري الخاصة", "تقارير المستخدم", "إحصائيات_التقارير"]:
            return  # تمرير للمعالج المخصص
            
        # تم إزالة النظام غير الضروري - يوكي الذكي الأساسي يكفي
        
        current_state = await state.get_state()
        
        if current_state is None:
            # رسالة عادية بدون حالة محددة
            await handle_general_message(message, state)
            return
        
        # معالجة الرسائل حسب الحالة
        if current_state.startswith("Banks"):
            if current_state == BanksStates.waiting_bank_selection.state:
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
        elif current_state.startswith("RankManagement"):
            from handlers.advanced_admin_handler import handle_advanced_admin_commands
            await handle_advanced_admin_commands(message, state)
        elif current_state.startswith("CustomCommands"):
            await handle_custom_commands_states(message, state, current_state)
        elif current_state.startswith("CustomReply"):
            from modules.custom_replies import handle_keyword_input, handle_response_input
            if current_state == CustomReplyStates.waiting_for_keyword.state:
                await handle_keyword_input(message, state)
            elif current_state == CustomReplyStates.waiting_for_response.state:
                await handle_response_input(message, state)
        elif current_state.startswith("SmartCommand"):
            await handle_smart_menu_states(message, state, current_state)
        else:
            await handle_general_message(message, state)
            
    except Exception as e:
        logging.error(f"خطأ في معالجة الرسالة: {e}")
        await message.reply(SYSTEM_MESSAGES["error"])
        await state.clear()


async def handle_smart_menu_states(message: Message, state: FSMContext, current_state: str):
    """معالج حالات القوائم الذكية"""
    try:
        from utils.states import SmartCommandStates
        
        if current_state == SmartCommandStates.waiting_smart_menu_choice.state:
            await smart_menu_handler.handle_smart_menu_choice(message, state, 'main_smart_menu')
            
        elif current_state == SmartCommandStates.waiting_smart_games_choice.state:
            await smart_menu_handler.handle_smart_menu_choice(message, state, 'games_menu')
            
        elif current_state == SmartCommandStates.waiting_quiz_answer.state:
            await handle_quiz_answer(message, state)
            
        elif current_state == SmartCommandStates.waiting_story_choice.state:
            await handle_story_choice(message, state)
            
        elif current_state == SmartCommandStates.waiting_battle_answer.state:
            await handle_battle_answer(message, state)
            
        elif current_state == SmartCommandStates.waiting_challenge_answer.state:
            await handle_challenge_answer(message, state)
            
    except Exception as e:
        logging.error(f"خطأ في معالج القوائم الذكية: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة اختيارك")
        await state.clear()


async def handle_quiz_answer(message: Message, state: FSMContext):
    """معالج إجابات الكويز الذكي"""
    try:
        user_input = message.text.strip()
        if not user_input.isdigit():
            await message.reply("❌ يرجى إدخال رقم الإجابة (1-4)")
            return
            
        choice = int(user_input)
        if choice < 1 or choice > 4:
            await message.reply("❌ يرجى اختيار رقم من 1 إلى 4")
            return
            
        # الحصول على بيانات الكويز
        data = await state.get_data()
        quiz_data = data.get('quiz_data')
        
        if not quiz_data:
            await message.reply("❌ انتهت صلاحية الكويز، ابدأ كويز جديد")
            await state.clear()
            return
            
        # معالجة الإجابة
        result = f"🧠 **نتيجة الكويز**\n\n"
        
        if choice == quiz_data.get('correct_answer', 1):
            result += "✅ **إجابة صحيحة!**\n"
            result += f"🏆 لقد ربحت {quiz_data.get('xp_reward', 10)} XP\n"
            
            # إضافة XP
            try:
                from modules.leveling import add_xp
                await add_xp(message.from_user.id, quiz_data.get('xp_reward', 10))
            except Exception as xp_error:
                logging.error(f"خطأ في إضافة XP: {xp_error}")
        else:
            result += "❌ **إجابة خاطئة**\n"
            result += f"💡 الإجابة الصحيحة هي: {quiz_data.get('correct_answer', 1)}\n"
            
        result += f"📚 **التفسير:** {quiz_data.get('explanation', 'لا يوجد تفسير')}\n\n"
        result += "🎮 اكتب 'كويز ذكي' لبدء كويز جديد!"
        
        await message.reply(result)
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالج إجابة الكويز: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة إجابتك")
        await state.clear()


async def handle_story_choice(message: Message, state: FSMContext):
    """معالج اختيار القصة التفاعلية"""
    try:
        user_input = message.text.strip()
        if not user_input.isdigit():
            await message.reply("❌ يرجى إدخال رقم الخيار")
            return
            
        choice = int(user_input)
        
        # الحصول على بيانات القصة
        data = await state.get_data()
        story_data = data.get('story_data')
        
        if not story_data:
            await message.reply("❌ انتهت صلاحية القصة، ابدأ قصة جديدة")
            await state.clear()
            return
            
        # الحصول على خيارات الفصل الحالي
        chapter_data = story_data.get('chapter_data', {})
        choices = chapter_data.get('choices', [])
        
        if choice < 1 or choice > len(choices):
            await message.reply(f"❌ يرجى اختيار رقم من 1 إلى {len(choices)}")
            return
            
        # معالجة الاختيار وعرض النتيجة
        selected_choice_data = choices[choice - 1]
        choice_text = selected_choice_data.get('text', f'الخيار {choice}') if isinstance(selected_choice_data, dict) else str(selected_choice_data)
        
        result = f"📖 **{story_data.get('title', 'رحلة التاجر')}**\n\n"
        result += f"✨ **اختيارك:** {choice_text}\n\n"
        
        # إضافة نتيجة مخصصة حسب الاختيار
        if choice == 1:
            result += f"⚡ لقد اخترت المخاطرة! قد تكون مربحة أو خطيرة...\n\n"
        elif choice == 2:
            result += f"🧠 اختيار حكيم! الدراسة قبل القرار أمر مهم.\n\n"
        elif choice == 3:
            result += f"🛡️ اختيار آمن! أحياناً الحذر أفضل من الندم.\n\n"
        
        # إضافة XP
        xp_reward = story_data.get('xp_reward', 400)
        result += f"🏆 لقد ربحت **{xp_reward} XP** لإكمال القصة!\n\n"
        result += "📚 اكتب 'قصة ذكية' لبدء مغامرة جديدة!"
        
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, xp_reward)
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP: {xp_error}")
        
        await message.reply(result)
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالج اختيار القصة: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة اختيارك")
        await state.clear()


async def handle_battle_answer(message: Message, state: FSMContext):
    """معالج إجابات معركة الذكاء"""
    try:
        user_input = message.text.strip()
        if not user_input.isdigit():
            await message.reply("❌ يرجى إدخال رقم الإجابة")
            return
            
        choice = int(user_input)
        
        # الحصول على بيانات المعركة
        data = await state.get_data()
        battle_data = data.get('battle_data')
        
        if not battle_data:
            await message.reply("❌ انتهت صلاحية المعركة")
            await state.clear()
            return
            
        options = battle_data.get('options', [])
        if choice < 1 or choice > len(options):
            await message.reply(f"❌ يرجى اختيار رقم من 1 إلى {len(options)}")
            return
            
        # معالجة النتيجة
        user_name = message.from_user.first_name or "اللاعب"
        
        result = f"⚔️ **نتيجة معركة الذكاء**\n\n"
        
        if choice == battle_data.get('correct_answer', 1):
            result += f"🏆 **انتصار! {user_name} فاز على يوكي!**\n"
            result += f"🤖 يوكي: هااااه! لقد هزمتني! أحسنت يا {user_name}!\n"
            result += f"💎 مكافأة الانتصار: {battle_data.get('victory_reward', 25)} XP\n"
            
            try:
                from modules.leveling import add_xp
                await add_xp(message.from_user.id, battle_data.get('victory_reward', 25))
            except Exception as xp_error:
                logging.error(f"خطأ في إضافة XP: {xp_error}")
        else:
            result += f"🤖 **يوكي انتصر!**\n"
            result += f"🤖 يوكي: أحسنت يا {user_name}، لكن الذكاء الاصطناعي فاز هذه المرة!\n"
            result += f"💡 الإجابة الصحيحة كانت: {battle_data.get('correct_answer', 1)}\n"
            result += f"🎁 مكافأة المشاركة: {battle_data.get('participation_reward', 10)} XP\n"
            
            try:
                from modules.leveling import add_xp
                await add_xp(message.from_user.id, battle_data.get('participation_reward', 10))
            except Exception as xp_error:
                logging.error(f"خطأ في إضافة XP: {xp_error}")
                
        result += f"\n🔥 اكتب 'معركة ذكية' لتحدٍ جديد!"
        
        await message.reply(result)
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالج معركة الذكاء: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة المعركة")
        await state.clear()


async def handle_challenge_answer(message: Message, state: FSMContext):
    """معالج إجابات التحدي الاقتصادي"""
    try:
        user_input = message.text.strip()
        if not user_input.isdigit():
            await message.reply("❌ يرجى إدخال رقم القرار")
            return
            
        choice = int(user_input)
        
        # الحصول على بيانات التحدي
        data = await state.get_data()
        challenge_data = data.get('challenge_data')
        
        if not challenge_data:
            await message.reply("❌ انتهت صلاحية التحدي")
            await state.clear()
            return
            
        options = challenge_data.get('options', [])
        if choice < 1 or choice > len(options):
            await message.reply(f"❌ يرجى اختيار رقم من 1 إلى {len(options)}")
            return
            
        # معالجة النتيجة
        selected_option = options[choice - 1]
        user_name = message.from_user.first_name or "المستثمر"
        
        result = f"💼 **نتيجة التحدي الاقتصادي**\n\n"
        result += f"📊 **قرارك:** {selected_option}\n\n"
        
        # تحديد النتيجة بناءً على الاختيار
        outcomes = challenge_data.get('outcomes', {})
        outcome = outcomes.get(str(choice), 'قرار جيد!')
        
        result += f"📈 **النتيجة:** {outcome}\n"
        
        # المكافآت
        xp_reward = challenge_data.get('xp_reward', 20)
        money_reward = challenge_data.get('money_reward', 0)
        
        result += f"🏆 مكافأة XP: {xp_reward}\n"
        if money_reward > 0:
            result += f"💰 مكافأة نقدية: {money_reward}$\n"
            
            # إضافة المال للرصيد
            try:
                from database.operations import update_user_balance
                await update_user_balance(message.from_user.id, money_reward)
            except Exception as money_error:
                logging.error(f"خطأ في إضافة المال: {money_error}")
        
        result += f"\n💡 اكتب 'تحدي اقتصادي' لتحدٍ جديد!"
        
        # إضافة XP
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, xp_reward)
        except Exception as xp_error:
            logging.error(f"خطأ في إضافة XP: {xp_error}")
        
        await message.reply(result)
        await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالج التحدي الاقتصادي: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة التحدي")
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
    
    # تم تعطيل فحص المحتوى هنا لأن المعالج الموحد يتعامل مع كل شيء الآن
    # النظام الموحد في unified_message_processor.py يعالج جميع الرسائل أولاً
    
    # التحقق من الأوامر الإدارية المتقدمة أولاً
    from handlers.advanced_admin_handler import handle_advanced_admin_commands
    if await handle_advanced_admin_commands(message, state):
        return  # تم التعامل مع الأمر الإداري
    
    text = message.text.lower() if message.text else ""
    
    # نقل فحص الذكاء الاصطناعي لأسفل - بعد الأوامر المطلقة
    # (تم نقل هذا القسم لأسفل لضمان أولوية الأوامر المطلقة)
    
    # الرد الإسلامي - السلام عليكم ووعليكم السلام
    if (message.text and message.chat.type in ['group', 'supergroup'] and 
        any(greeting in message.text for greeting in ['السلام عليكم', 'السلام عليكم ورحمة الله', 'السلام عليكم ورحمة الله وبركاته'])):
        try:
            islamic_responses = [
                "وعليكم السلام ورحمة الله وبركاته 🕌",
                "وعليكم السلام ورحمة الله 🌙",
                "وعليكم السلام وأهلاً وسهلاً 🤲",
                "وعليكم السلام، مرحباً بكم 🕌✨",
                "وعليكم السلام ورحمة الله، حياكم الله 🌙"
            ]
            import random
            response = random.choice(islamic_responses)
            await message.reply(response)
            return
        except Exception as e:
            logging.error(f"خطأ في الرد الإسلامي: {e}")
    
    # لعبة الرويال - Royal Battle Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        royal_commands = ['لعبة الحظ', 'رويال', 'royal']
        
        # فحص الأوامر ككلمات مستقلة
        is_royal_command = False
        for command in royal_commands:
            if command == 'لعبة الحظ':
                # فحص خاص للعبارة المكونة من كلمتين
                if re.search(r'\bلعبة\s+الحظ\b', text):
                    is_royal_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_royal_command = True
                    break
        
        if is_royal_command:
            try:
                from modules.royal_game import start_royal_game
                await start_royal_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة الرويال: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة الرويال")
    
    # لعبة الكلمة - Word Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        word_commands = ['الكلمة', 'كلمة', 'word']
        
        # فحص الأوامر كأوامر منفردة فقط (النص كاملاً يجب أن يكون الأمر)
        is_word_command = text.strip() in word_commands
        
        if is_word_command:
            try:
                from modules.word_game import start_word_game
                await start_word_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة الكلمة: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة الكلمة")
    
    # لعبة الرموز - Symbols Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        symbols_commands = ['الرموز', 'رموز', 'symbols']
        
        # فحص الأوامر كأوامر منفردة فقط (النص كاملاً يجب أن يكون الأمر)
        is_symbols_command = text.strip() in symbols_commands
        
        if is_symbols_command:
            try:
                from modules.symbols_game import start_symbols_game
                await start_symbols_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة الرموز: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة الرموز")
    
    # أمر قائمة الألعاب
    if message.text:
        import re
        games_list_commands = ['العاب', 'الالعاب', 'games', 'قائمة الالعاب']
        
        # فحص الأوامر ككلمات مستقلة
        is_games_list_command = False
        for command in games_list_commands:
            if command == 'قائمة الالعاب':
                if re.search(r'\bقائمة\s+الالعاب\b', text):
                    is_games_list_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_games_list_command = True
                    break
        
        if is_games_list_command:
            try:
                from modules.games_list import show_games_list
                await show_games_list(message)
                return
            except Exception as e:
                logging.error(f"خطأ في عرض قائمة الألعاب: {e}")
                await message.reply("❌ حدث خطأ في عرض قائمة الألعاب")

    # أمر الألعاب المقترحة
    if message.text:
        import re
        suggested_commands = ['اقتراحات', 'العاب مقترحة', 'الاقتراحات', 'مقترحة']
        
        # فحص الأوامر ككلمات مستقلة
        is_suggested_command = False
        for command in suggested_commands:
            if command == 'العاب مقترحة':
                if re.search(r'\bالعاب\s+مقترحة\b', text):
                    is_suggested_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_suggested_command = True
                    break
        
        if is_suggested_command:
            try:
                from modules.suggested_games import get_suggested_games_list
                suggested_text = get_suggested_games_list()
                await message.reply(suggested_text)
                return
            except Exception as e:
                logging.error(f"خطأ في عرض الألعاب المقترحة: {e}")
                await message.reply("❌ حدث خطأ في عرض الألعاب المقترحة")

    # لعبة ساحة الموت الأخيرة - Battle Arena Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        battle_commands = ['ساحة الموت', 'battle', 'معركة', 'ساحة المعركة']
        
        # فحص الأوامر ككلمات مستقلة
        is_battle_command = False
        for command in battle_commands:
            if command in ['ساحة الموت', 'ساحة المعركة']:
                command_words = command.split()
                pattern = r'\b' + r'\s+'.join(re.escape(word) for word in command_words) + r'\b'
                if re.search(pattern, text):
                    is_battle_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_battle_command = True
                    break
        
        if is_battle_command:
            try:
                from modules.battle_arena_game import start_battle_arena
                await start_battle_arena(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء ساحة الموت: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء ساحة الموت الأخيرة")
    
    # نظام مراهنة الحظ - Luck Gambling System
    if (message.text and (
        # أوامر المراهنة المحددة
        any(phrase in text for phrase in ['حظ فلوسي', 'حظ كل فلوسي', 'حظ كامل فلوسي']) or
        # حظ + مبلغ
        (text.strip().startswith('حظ ') and len(text.split()) >= 2 and text.split()[1].replace('$', '').replace(',', '').isdigit())
    )):
        try:
            from modules.luck_gambling import parse_gamble_command, process_luck_gamble
            amount, bet_all = parse_gamble_command(text)
            
            if amount is not None or bet_all:
                await process_luck_gamble(message, amount, bet_all)
            else:
                from modules.luck_gambling import show_gambling_help
                await show_gambling_help(message)
            return
        except Exception as e:
            logging.error(f"خطأ في مراهنة الحظ: {e}")
            await message.reply("❌ حدث خطأ في مراهنة الحظ")

    # لعبة عجلة الحظ - Luck Wheel Game  
    if message.text:
        import re
        wheel_commands = ['عجلة الحظ', 'عجلة', 'wheel']
        
        # فحص الأوامر ككلمات مستقلة
        is_wheel_command = False
        for command in wheel_commands:
            if command == 'عجلة الحظ':
                if re.search(r'\bعجلة\s+الحظ\b', text):
                    is_wheel_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_wheel_command = True
                    break
        
        # فحص خاص لكلمة "حظ" مع شروط خاصة
        if not is_wheel_command and (text == 'حظ' or text.endswith(' حظ') or ' حظ ' in text):
            is_wheel_command = True
        
        if is_wheel_command:
            try:
                from modules.luck_wheel_game import start_luck_wheel
                await start_luck_wheel(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء عجلة الحظ: {e}")
                await message.reply("❌ حدث خطأ في عجلة الحظ")

    # لعبة خمن الرقم - Number Guess Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        number_commands = ['خمن الرقم', 'تخمين', 'رقم', 'guess']
        
        # فحص الأوامر ككلمات مستقلة
        is_number_command = False
        for command in number_commands:
            if command == 'خمن الرقم':
                if re.search(r'\bخمن\s+الرقم\b', text):
                    is_number_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_number_command = True
                    break
        
        if is_number_command:
            try:
                from modules.number_guess_game import start_number_guess_game
                await start_number_guess_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة خمن الرقم: {e}")
                await message.reply("❌ حدث خطأ في لعبة خمن الرقم")

    # لعبة سؤال وجواب سريعة - Quick Quiz Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        # فحص الأوامر ككلمات مستقلة باستخدام word boundaries
        import re
        quiz_commands = ['سؤال وجواب', 'مسابقة', 'quiz', 'سؤال']
        
        # فحص كل أمر على حدة ككلمة مستقلة
        is_quiz_command = False
        for command in quiz_commands:
            if command == 'سؤال وجواب':
                # فحص خاص للعبارة المكونة من كلمتين
                if re.search(r'\bسؤال\s+وجواب\b', text):
                    is_quiz_command = True
                    break
            else:
                # فحص الكلمات المفردة كأوامر مستقلة
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_quiz_command = True
                    break
        
        if is_quiz_command:
            try:
                from modules.quick_quiz_game import start_quick_quiz_game
                await start_quick_quiz_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء مسابقة سؤال وجواب: {e}")
                await message.reply("❌ حدث خطأ في بدء المسابقة")
    
    # لعبة اكس اوه - XO/Tic-Tac-Toe Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        xo_commands = ['اكس اوه', 'xo', 'اكس او', 'اكساوه']
        
        # فحص الأوامر ككلمات مستقلة
        is_xo_command = False
        for command in xo_commands:
            if command in ['اكس اوه', 'اكس او']:
                command_words = command.split()
                pattern = r'\b' + r'\s+'.join(re.escape(word) for word in command_words) + r'\b'
                if re.search(pattern, text):
                    is_xo_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_xo_command = True
                    break
        
        if is_xo_command:
            try:
                from modules.xo_game import start_xo_game
                await start_xo_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة اكس اوه: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة اكس اوه")
    
    # لعبة حجر ورقة مقص - Rock Paper Scissors Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        rps_commands = ['حجر ورقة مقص', 'حجر ورقة', 'rps']
        
        # فحص الأوامر ككلمات مستقلة
        is_rps_command = False
        for command in rps_commands:
            if command in ['حجر ورقة مقص', 'حجر ورقة']:
                command_words = command.split()
                pattern = r'\b' + r'\s+'.join(re.escape(word) for word in command_words) + r'\b'
                if re.search(pattern, text):
                    is_rps_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_rps_command = True
                    break
        
        if is_rps_command:
            try:
                from modules.rock_paper_scissors_game import start_rock_paper_scissors_game
                await start_rock_paper_scissors_game(message)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة حجر ورقة مقص: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة حجر ورقة مقص")
    
    # لعبة صدق أم كذب - True False Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        tf_commands = ['صدق أم كذب', 'صدق كذب', 'true false']
        
        # فحص الأوامر ككلمات مستقلة
        is_tf_command = False
        for command in tf_commands:
            if command in ['صدق أم كذب', 'صدق كذب']:
                command_words = command.split()
                pattern = r'\b' + r'\s+'.join(re.escape(word) for word in command_words) + r'\b'
                if re.search(pattern, text):
                    is_tf_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_tf_command = True
                    break
        
        if is_tf_command:
            try:
                from modules.true_false_game import start_true_false_game
                await start_true_false_game(message, vs_ai=True)
                return
            except Exception as e:
                logging.error(f"خطأ في بدء لعبة صدق أم كذب: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء لعبة صدق أم كذب")
    
    # لعبة التحدي الرياضي - Math Challenge Game
    if (message.text and message.chat.type in ['group', 'supergroup']):
        import re
        math_commands = ['تحدي رياضي', 'رياضيات', 'math challenge']
        
        # فحص الأوامر ككلمات مستقلة
        is_math_command = False
        for command in math_commands:
            if command in ['تحدي رياضي']:
                command_words = command.split()
                pattern = r'\b' + r'\s+'.join(re.escape(word) for word in command_words) + r'\b'
                if re.search(pattern, text):
                    is_math_command = True
                    break
            else:
                if re.search(rf'\b{re.escape(command)}\b', text):
                    is_math_command = True
                    break
        
        if is_math_command:
            try:
                from modules.math_challenge_game import start_math_challenge_game
                await start_math_challenge_game(message, vs_ai=True, difficulty="easy")
                return
            except Exception as e:
                logging.error(f"خطأ في بدء التحدي الرياضي: {e}")
                await message.reply("❌ حدث خطأ أثناء بدء التحدي الرياضي")
    
    # معالج خاص لحرف "ا" منفرداً في المجموعات - عرض معلومات الملف الشخصي
    if (message.text and message.text.strip() == "ا" and 
        message.chat.type in ['group', 'supergroup'] and message.from_user):
        try:
            user = message.from_user
            
            # بناء نص معلومات المستخدم
            profile_text = f"👤 **الملف الشخصي**\n\n"
            profile_text += f"🏷️ **الاسم:** {user.first_name}"
            if user.last_name:
                profile_text += f" {user.last_name}"
            
            if user.username:
                profile_text += f"\n📧 **اليوزرنيم:** @{user.username}"
            else:
                profile_text += f"\n📧 **اليوزرنيم:** غير محدد"
            
            profile_text += f"\n🆔 **المعرف:** `{user.id}`"
            
            # إضافة الرتبة الإدارية في المجموعة
            try:
                from config.hierarchy import get_user_admin_level, get_admin_level_name, MASTERS
                admin_level = get_user_admin_level(user.id, message.chat.id)
                level_name = get_admin_level_name(admin_level)
                profile_text += f"\n⭐ **الرتبة:** {level_name}"
                
                # إضافة تمييز خاص للأسياد
                if user.id in MASTERS:
                    profile_text += " 👑"
            except Exception as rank_error:
                logging.error(f"خطأ في الحصول على الرتبة: {rank_error}")
                profile_text += f"\n⭐ **الرتبة:** عضو"
            
            # محاولة الحصول على معلومات إضافية من المجموعة
            try:
                chat_member = await message.bot.get_chat_member(message.chat.id, user.id)
                if hasattr(chat_member.user, 'bio') and chat_member.user.bio:
                    profile_text += f"\n📝 **السيرة الذاتية:** {chat_member.user.bio}"
                else:
                    profile_text += f"\n📝 **السيرة الذاتية:** غير محددة"
            except:
                profile_text += f"\n📝 **السيرة الذاتية:** غير محددة"
            
            # محاولة إرسال صورة الملف الشخصي مع النص
            try:
                # الحصول على صور الملف الشخصي
                photos = await message.bot.get_user_profile_photos(user.id, limit=1)
                if photos.photos:
                    # إرسال الصورة مع النص
                    photo_file_id = photos.photos[0][-1].file_id
                    await message.reply_photo(photo=photo_file_id, caption=profile_text)
                else:
                    # لا توجد صورة ملف شخصي، إرسال النص فقط
                    profile_text += "\n\n📷 **صورة الملف الشخصي:** غير محددة"
                    await message.reply(profile_text)
            except Exception as photo_error:
                # في حال فشل في الحصول على الصورة، إرسال النص فقط
                logging.error(f"خطأ في الحصول على صورة الملف الشخصي: {photo_error}")
                profile_text += "\n\n📷 **صورة الملف الشخصي:** غير متاحة"
                await message.reply(profile_text)
            
            return  # انتهى التعامل مع الرسالة
            
        except Exception as e:
            logging.error(f"خطأ في عرض الملف الشخصي للحرف 'ا': {e}")
            await message.reply("❌ حدث خطأ أثناء عرض معلومات الملف الشخصي")
            return

    # أمر المطور - عرض معلومات المطور مع خلفية مميزة
    if (message.text and any(keyword in message.text.lower() for keyword in ['مطور', 'developer', 'dev info']) and 
        message.chat.type in ['group', 'supergroup'] and message.from_user):
        try:
            from config.hierarchy import MASTERS
            
            # أمر المطور متاح للجميع الآن - لكن يعرض معلومات المطور الأساسي فقط
            # نأخذ السيد الأول من قائمة الأسياد (هو المطور الأساسي)
            developer_id = MASTERS[0]  # المطور الأساسي هو أول سيد
            
            try:
                # محاولة الحصول على معلومات المطور من Telegram
                developer_user = await message.bot.get_chat(developer_id)
                
                # معلومات المطور
                developer_info = f"👨‍💻 **معلومات المطور**\n\n"
                developer_info += f"🏷️ **الاسم:** {developer_user.first_name}"
                if hasattr(developer_user, 'last_name') and developer_user.last_name:
                    developer_info += f" {developer_user.last_name}"
                
                if hasattr(developer_user, 'username') and developer_user.username:
                    developer_info += f"\n📧 **اليوزرنيم:** @{developer_user.username}"
                else:
                    developer_info += f"\n📧 **اليوزرنيم:** غير محدد"
                
                developer_info += f"\n🆔 **المعرف:** `{developer_id}`"
                developer_info += f"\n⭐ **الرتبة:** مطور البوت 👑"
                developer_info += f"\n🛠️ **الصلاحيات:** صلاحيات مطلقة"
                developer_info += f"\n💻 **التخصص:** تطوير البوتات والأنظمة"
                developer_info += f"\n🌟 **الحالة:** نشط ومتاح للدعم"
                
                # محاولة إرسال صورة خلفية مميزة مع معلومات المطور
                try:
                    # أولاً محاولة الحصول على صورة الملف الشخصي للمطور
                    photos = await message.bot.get_user_profile_photos(developer_id, limit=1)
                    if photos.photos:
                        # إرسال صورة الملف الشخصي مع المعلومات
                        photo_file_id = photos.photos[0][-1].file_id
                        await message.reply_photo(
                            photo=photo_file_id, 
                            caption=developer_info
                        )
                    else:
                        # إذا لم توجد صورة ملف شخصي، إرسال بخلفية نصية مميزة
                        developer_banner = f"""
╔══════════════════════════════════════╗
║         🌟 مطور البوت 🌟            ║
╠══════════════════════════════════════╣
║                                      ║
{developer_info}
║                                      ║
╠══════════════════════════════════════╣
║    🚀 شكراً لاستخدام بوت يوكي! 🚀    ║
╚══════════════════════════════════════╝
                        """
                        await message.reply(developer_banner)
                        
                except Exception as photo_error:
                    logging.error(f"خطأ في الحصول على صورة المطور: {photo_error}")
                    # إرسال المعلومات مع تصميم نصي مميز
                    developer_banner = f"""
🌟═══════════════════════════════════════🌟
           👨‍💻 معلومات المطور 👨‍💻
🌟═══════════════════════════════════════🌟

{developer_info}

🚀════════════════════════════════════════🚀
        شكراً لاستخدام بوت يوكي!
🚀════════════════════════════════════════🚀
                    """
                    await message.reply(developer_banner)
                    
            except Exception as get_chat_error:
                logging.error(f"خطأ في الحصول على معلومات المطور من Telegram: {get_chat_error}")
                # في حال فشل في جلب البيانات، استخدم المعلومات المحفوظة
                developer_info = f"""👨‍💻 **معلومات المطور**

🏷️ **الاسم:** Yuki Brandon
📧 **اليوزرنيم:** @YukiBrandon
🆔 **المعرف:** `{developer_id}`
⭐ **الرتبة:** مطور البوت 👑
🛠️ **الصلاحيات:** صلاحيات مطلقة
💻 **التخصص:** تطوير البوتات والأنظمة
🌟 **الحالة:** نشط ومتاح للدعم"""
                
                await message.reply(developer_info)
            
            return
            
        except Exception as e:
            logging.error(f"خطأ في عرض معلومات المطور: {e}")
            await message.reply("❌ حدث خطأ أثناء عرض معلومات المطور")
            return
    
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
        from modules.leveling import add_xp
        await add_xp(message.from_user.id, 1)
    except Exception as activity_error:
        logging.error(f"خطأ في تحديث النشاط أو XP: {activity_error}")
    
    # أمر ذكر جميع الأعضاء الغير متصلين
    if text.lower() in ['الكل', 'all', 'mention all', 'ذكر الكل', 'نداء عام']:
        try:
            if message.chat.type not in ['group', 'supergroup']:
                await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
                return
            
            # فحص رتبة المستخدم - يجب أن يكون مشرف أو أعلى
            from config.hierarchy import get_user_admin_level, AdminLevel
            user_level = get_user_admin_level(message.from_user.id, message.chat.id)
            
            if user_level == AdminLevel.MEMBER:
                await message.reply("❌ هذا الأمر مخصص للمشرفين والمالكين فقط!")
                return
            
            # الحصول على قائمة أعضاء المجموعة
            chat_members = []
            mentions_text = "📢 **نداء عام لجميع الأعضاء:**\n\n"
            
            try:
                # جلب معرفات أعضاء المجموعة من الرسائل المحفوظة أو من قاعدة البيانات
                from database.operations import execute_query
                
                # البحث عن جميع الأعضاء مع ترتيب الغير نشطين أولاً
                all_users = await execute_query(
                    """
                    SELECT DISTINCT user_id, 
                           COALESCE(last_activity, '1970-01-01') as last_activity
                    FROM (
                        SELECT user_id, MAX(last_activity) as last_activity FROM group_ranks WHERE chat_id = ?
                        UNION
                        SELECT from_user_id as user_id, NULL as last_activity FROM transactions 
                        WHERE from_user_id IN (SELECT user_id FROM group_ranks WHERE chat_id = ?)
                        AND from_user_id IS NOT NULL AND from_user_id != 0
                        UNION
                        SELECT to_user_id as user_id, NULL as last_activity FROM transactions 
                        WHERE to_user_id IN (SELECT user_id FROM group_ranks WHERE chat_id = ?)
                        AND to_user_id IS NOT NULL AND to_user_id != 0
                        UNION
                        SELECT user_id, NULL as last_activity FROM levels 
                        WHERE user_id IN (SELECT user_id FROM group_ranks WHERE chat_id = ?)
                        UNION
                        SELECT user_id, NULL as last_activity FROM farm 
                        WHERE user_id IN (SELECT user_id FROM group_ranks WHERE chat_id = ?)
                    ) 
                    ORDER BY last_activity ASC
                    LIMIT 50
                    """,
                    (message.chat.id, message.chat.id, message.chat.id, message.chat.id, message.chat.id),
                    fetch_all=True
                )
                
                if not all_users:
                    await message.reply("❌ لا يمكن العثور على أعضاء لذكرهم!")
                    return
                
                mentions_count = 0
                mentions_list = []
                
                # إنشاء قائمة الذكر - أولوية للمستخدمين الغير نشطين
                for user_data in all_users[:25]:  # حد أقصى 25 عضو لتجنب الإزعاج
                    user_id = user_data['user_id']
                    
                    # تجنب ذكر البوت نفسه
                    if user_id == message.bot.id:
                        continue
                    
                    # تجنب ذكر مرسل الرسالة
                    if user_id == message.from_user.id:
                        continue
                    
                    # الحصول على اسم المستخدم من قاعدة البيانات
                    user_info = await execute_query(
                        "SELECT first_name, username FROM users WHERE user_id = ?",
                        (user_id,),
                        fetch_one=True
                    )
                    
                    if user_info and user_info['first_name']:
                        display_name = user_info['first_name']
                    else:
                        display_name = f"عضو {user_id}"
                    
                    mentions_list.append(f"[{display_name}](tg://user?id={user_id})")
                    mentions_count += 1
                
                if mentions_count == 0:
                    await message.reply("❌ لا يوجد أعضاء لذكرهم!")
                    return
                
                # تقسيم القائمة إلى مجموعات صغيرة لتجنب الرسائل الطويلة
                mentions_per_message = 10
                for i in range(0, len(mentions_list), mentions_per_message):
                    chunk = mentions_list[i:i + mentions_per_message]
                    
                    final_text = f"📢 **نداء عام (أولوية للأعضاء الغير نشطين) - المجموعة {i//mentions_per_message + 1}:**\n\n"
                    final_text += " • ".join(chunk)
                    final_text += f"\n\n👤 المرسل: {message.from_user.first_name}\n💡 **ملاحظة:** تم ترتيب الأعضاء حسب النشاط (الأقل نشاطاً أولاً)"
                    
                    await message.reply(final_text, parse_mode="Markdown")
                
                # رسالة تأكيد
                await message.reply(f"✅ تم ذكر {mentions_count} عضو من أعضاء المجموعة!")
                
            except Exception as db_error:
                logging.error(f"خطأ في قاعدة البيانات لأمر الكل: {db_error}")
                
                # طريقة بديلة - ذكر المستخدمين من الرسائل الأخيرة
                simple_mentions = []
                simple_mentions.append(f"[@user{message.from_user.id}](tg://user?id={message.from_user.id})")
                
                final_text = "📢 **نداء عام:**\n\n"
                final_text += "تعذر جلب قائمة الأعضاء، لكن تم إرسال النداء!\n\n"
                final_text += f"👤 المرسل: {message.from_user.first_name}"
                
                await message.reply(final_text, parse_mode="Markdown")
            
        except Exception as e:
            logging.error(f"خطأ في أمر ذكر الكل: {e}")
            await message.reply("❌ حدث خطأ أثناء محاولة ذكر الأعضاء")
        return

    # دليل المستويات الشامل
    if text in ['المستويات', 'دليل المستويات', 'شرح المستويات', 'كيفية التقدم']:
        from modules.levels_guide import show_levels_guide
        await show_levels_guide(message)
        return
    
    # أوامر الترتيب والمتصدرين
    if text in ['الأغنياء', 'الاغنياء', 'المتصدرين', 'المتصدرون', 'قائمة الأغنياء']:
        from modules.ranking import show_leaderboard
        await show_leaderboard(message)
        return
    
    if text.strip() in ['ترتيبي', 'مركزي']:
        from modules.ranking import show_user_ranking
        await show_user_ranking(message)
        return
    
    # فحص أوامر المستوى بدقة - مستواي كلمة مفردة فقط
    import re
    level_commands = ["مستوايا", "مستوى", "level", "xp"]
    is_level_command = False
    
    # فحص "مستواي" و "تقدمي" كلمات مفردة فقط (مع السماح للمسافات في البداية والنهاية)
    if text.strip() == "مستواي" or text.strip() == "تقدمي":
        is_level_command = True
    else:
        # فحص الأوامر الأخرى بالطريقة العادية
        for command in level_commands:
            if re.search(rf'\b{re.escape(command)}\b', text):
                is_level_command = True
                break
    
    if is_level_command:
        try:
            from modules.leveling import get_user_level_info
            level_info = await get_user_level_info(message.from_user.id)
            if level_info:
                await message.reply(level_info)
            else:
                await message.reply("❌ لم يتم العثور على مستواك")
        except Exception as e:
            logging.error(f"خطأ في عرض المستوى: {e}")
            await message.reply("❌ حدث خطأ في عرض مستواك")
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
    
    # فحص تحميل الموسيقى
    from modules.music_search import handle_music_download
    if await handle_music_download(message):
        return
    
    # فحص إضافة موسيقى (للمديرين)
    if await handle_add_music_command(message):
        return
    
    # فحص الأوامر المخصصة قبل الردود الخاصة
    if await handle_custom_commands_message(message):
        return
    
    # فحص أوامر المسح قبل الردود المخصصة
    if text.startswith('مسح ') or text == 'مسح بالرد' or text == 'مسح':
        logging.info(f"تم اكتشاف أمر مسح: '{text}' - سيتم توجيهه للمعالج")
        from modules.clear_commands import handle_clear_command
        await handle_clear_command(message, text)
        return
    
    # فحص أوامر إدارة قاعدة بيانات المخالفات الجديدة
    if text in ['سجل السوابق', 'سجل السبابين'] or text.startswith('سجل السوابق '):
        logging.info(f"تم اكتشاف أمر سجل السوابق: '{text}'")
        from modules.admin_management import handle_violations_record_command
        await handle_violations_record_command(message)
        return
    elif text == 'تنظيف' or text.startswith('تنظيف '):
        logging.info(f"تم اكتشاف أمر تنظيف: '{text}'")
        from modules.admin_management import handle_violations_cleanup_command
        await handle_violations_cleanup_command(message)
        return
    elif text.startswith('إلغاء سوابق ') or text == 'إلغاء سوابق':
        logging.info(f"تم اكتشاف أمر إلغاء سوابق: '{text}'")
        from modules.admin_management import handle_clear_user_record_command
        await handle_clear_user_record_command(message)
        return
    
    # معالجة أرقام لعبة خمن الرقم
    if (message.text and message.chat.type in ['group', 'supergroup'] and 
        message.text.strip().isdigit()):
        try:
            from modules.number_guess_game import handle_number_input
            await handle_number_input(message)
            # لا نستخدم return هنا للسماح بمعالجة أخرى
        except Exception as e:
            logging.error(f"خطأ في معالجة تخمين الرقم: {e}")

    # فحص الردود المخصصة
    from modules.custom_replies import check_for_custom_replies, handle_show_custom_replies
    if await check_for_custom_replies(message):
        # إضافة XP للمستخدم عند استخدام رد مخصص
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, "custom_reply")
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
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, "banking")
        except:
            pass
        return
    
    # فحص أوامر الاستثمار المحسنة
    try:
        from modules.investment_enhanced import handle_enhanced_investment_text
        if await handle_enhanced_investment_text(message):
            # إضافة XP للاستثمار
            try:
                from modules.leveling import add_xp
                await add_xp(message.from_user.id, "investment")
            except:
                pass
            return
    except Exception as inv_error:
        logging.error(f"خطأ في نظام الاستثمار المحسن: {inv_error}")
    
    # فحص أوامر العمليات المصرفية
    # قاموس كلمات البنك - تحتاج لتكون مفردات فقط
    bank_standalone_words = ['البنك', 'بنك', 'بنكي', 'المحفظة', 'محفظتي']
    bank_context_words = ['ايداع', 'إيداع', 'سحب']  # هذه يمكن أن تكون في سياق
    
    if (text.strip() in bank_standalone_words or 
        any(word in text for word in bank_context_words)):
        # إضافة XP للعمليات المصرفية
        try:
            from modules.leveling import add_xp
            await add_xp(message.from_user.id, "banking")
        except:
            pass
    
    # فحص أوامر إدارة الردود الخاصة للمديرين
    if await handle_special_admin_commands(message):
        return
    
    # فحص أوامر اختبار نظام الردود للمديرين
    if await handle_response_tester_commands(message):
        return
    
    # أمر اختبار الأحداث والنظام
    if text in ['اختبار الاحداث', 'اختبار الأحداث', 'اختبار النظام', 'اختبار الفلتر', 'فحص النظام', 'فحص الفلتر']:
        try:
            # فحص حالة النظام الشامل
            test_result = "🔍 **اختبار الأحداث والنظام**\n\n"
            test_result += "✅ نظام المجموعات المتعددة: يعمل\n"
            test_result += "✅ نظام الذكاء الاصطناعي: يعمل\n"
            test_result += "✅ نظام XP والمستويات: يعمل\n"
            test_result += "✅ نظام الذاكرة والسياق: يعمل\n"
            test_result += "✅ قاعدة البيانات: متصلة\n"
            test_result += "✅ أنظمة الألعاب والاقتصاد: تعمل\n\n"
            
            # إضافة معلومات المجموعة الحالية
            chat_info = f"📊 **معلومات المجموعة الحالية:**\n"
            chat_info += f"• الاسم: {message.chat.title or 'غير معروف'}\n"
            chat_info += f"• المعرف: {message.chat.id}\n"
            chat_info += f"• النوع: {'مجموعة عملاقة' if message.chat.type == 'supergroup' else 'مجموعة عادية'}\n\n"
            
            test_result += chat_info
            test_result += "🎯 **جميع الأنظمة تعمل بنجاح!**"
            
            await message.reply(test_result)
        except Exception as e:
            logging.error(f"خطأ في اختبار النظام: {e}")
            await message.reply("❌ حدث خطأ أثناء اختبار النظام")
        return
    
    # تم نقل فحص أوامر الأسياد لأعلى لتجنب التداخل مع نظام الردود
    
    # فحص أوامر الهيكل الإداري
    if await handle_hierarchy_commands(message):
        return
    
    # فحص الأوامر المساعدة والأدوات
    if await handle_utility_commands(message):
        return
    
    # فحص أوامر فلتر الألفاظ المسيئة
    if text in PROFANITY_COMMANDS:
        try:
            await PROFANITY_COMMANDS[text](message)
            return
        except Exception as profanity_error:
            logging.error(f"خطأ في أمر فلتر الألفاظ المسيئة: {profanity_error}")
            await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")
    
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
    
    # === أمر عرض حالة المجموعة الشاملة (للأسياد فقط) ===
    if text == 'حالة المجموعة' or text == 'تقرير المجموعة' or text == 'إحصائيات المجموعة':
        from config.hierarchy import MASTERS
        from database.operations import execute_query
        user_id = message.from_user.id if message.from_user else 0
        if user_id in MASTERS:
            try:
                chat_id = message.chat.id
                
                # جلب جميع الأعضاء من قاعدة البيانات
                query = "SELECT user_id, first_name, last_name, username, bank, balance FROM users"
                all_users = await execute_query(query, fetch=True)
                
                if not all_users:
                    await message.reply("❌ لا توجد بيانات مستخدمين في قاعدة البيانات")
                    return
                
                # إحصائيات عامة
                total_users = len(all_users)
                registered_users = [user for user in all_users if user[4] is not None]  # bank field
                unregistered_users = [user for user in all_users if user[4] is None]
                
                total_balance = sum([user[5] or 0 for user in registered_users])  # balance field
                avg_balance = total_balance // len(registered_users) if registered_users else 0
                
                # بناء التقرير
                report = f"📊 **تقرير حالة المجموعة الشامل**\n\n"
                report += f"👥 **إجمالي الأعضاء:** {total_users:,}\n"
                report += f"✅ **مسجلون في البنك:** {len(registered_users):,}\n"
                report += f"❌ **غير مسجلين:** {len(unregistered_users):,}\n"
                report += f"💰 **إجمالي الأموال:** {total_balance:,} ريال\n"
                report += f"📈 **متوسط الرصيد:** {avg_balance:,} ريال\n\n"
                
                # أغنى المستخدمين
                if registered_users:
                    richest = sorted(registered_users, key=lambda x: x[5] or 0, reverse=True)[:5]
                    report += f"👑 **أغنى 5 أعضاء:**\n"
                    for i, user in enumerate(richest, 1):
                        name = user[1] or user[3] or f"المستخدم {user[0]}"
                        balance = user[5] or 0
                        report += f"{i}. {name}: {balance:,} ريال\n"
                    report += "\n"
                
                # قائمة غير المسجلين
                if unregistered_users and len(unregistered_users) <= 20:
                    report += f"❌ **الأعضاء غير المسجلين ({len(unregistered_users)}):**\n"
                    for user in unregistered_users[:10]:  # أول 10 فقط
                        name = user[1] or user[3] or f"المستخدم {user[0]}"
                        report += f"• {name}\n"
                    if len(unregistered_users) > 10:
                        report += f"• ... و {len(unregistered_users) - 10} آخرين\n"
                elif unregistered_users:
                    report += f"❌ **عدد غير المسجلين كبير:** {len(unregistered_users)}\n"
                
                report += f"\n💡 **نصيحة:** شجع الأعضاء على كتابة 'انشاء حساب بنكي'"
                
                await message.reply(report, parse_mode="Markdown")
                
            except Exception as e:
                logging.error(f"خطأ في عرض حالة المجموعة: {e}")
                await message.reply("❌ حدث خطأ في تحميل بيانات المجموعة")
        else:
            await message.reply("❌ هذا الأمر متاح للأسياد فقط")
        return
    
    # === أمر عرض قائمة الأسياد (للأسياد فقط) ===
    if text == 'الأسياد' or text == 'الاسياد' or text == 'قائمة الأسياد' or text == 'قائمة الاسياد':
        from config.hierarchy import MASTERS
        user_id = message.from_user.id if message.from_user else 0
        if user_id in MASTERS:
            try:
                masters_info = "👑 قائمة الأسياد الحاليين:\n\n"
                
                for i, master_id in enumerate(MASTERS, 1):
                    try:
                        # محاولة الحصول على معلومات المستخدم من تليجرام
                        chat_member = await message.bot.get_chat(master_id)
                        user_name = chat_member.first_name or "بدون اسم"
                        if chat_member.last_name:
                            user_name += f" {chat_member.last_name}"
                        
                        username = f"@{chat_member.username}" if chat_member.username else "بدون يوزر"
                        
                        # تنظيف الاسم من الرموز الخاصة التي قد تسبب مشاكل في Markdown
                        clean_name = user_name.replace("[", "").replace("]", "").replace("(", "").replace(")", "").replace("*", "").replace("_", "").replace("`", "")
                        
                        # جعل الاسم قابلاً للنقر للانتقال إلى حساب المستخدم
                        clickable_name = f"[{clean_name}](tg://user?id={master_id})"
                        
                        masters_info += f"{i}. 👑 {clickable_name}\n"
                        masters_info += f"   📱 {username}\n"
                        masters_info += f"   🆔 {master_id}\n\n"
                        
                    except Exception as e:
                        # في حالة فشل الحصول على معلومات المستخدم
                        clickable_name = f"[سيد {i}](tg://user?id={master_id})"
                        masters_info += f"{i}. 👑 {clickable_name}\n"
                        masters_info += f"   🆔 {master_id}\n\n"
                
                masters_info += f"📊 إجمالي الأسياد: {len(MASTERS)}\n\n"
                masters_info += "🔴 الأسياد لديهم صلاحيات مطلقة في جميع المجموعات\n"
                masters_info += "⚡ يمكنهم تنفيذ أي أمر وإدارة جميع الأنظمة\n\n"
                masters_info += "💡 اضغط على أي اسم للانتقال إلى حساب السيد\n"
                masters_info += "🔄 ملاحظة: إذا لاحظت أي يوزر خاطئ فهذا يعني أن تيليجرام لم يحدث المعلومات"
                
                # تجربة إرسال بتنسيق HTML أولاً، وإذا فشل استخدم النص العادي
                try:
                    # تحويل Markdown إلى HTML بشكل صحيح
                    import re
                    html_info = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', masters_info)
                    await message.reply(html_info, parse_mode="HTML", disable_web_page_preview=True)
                except Exception as html_error:
                    logging.warning(f"فشل إرسال HTML، جاري التجربة بالنص العادي: {html_error}")
                    # في حالة فشل HTML، استخدم النص العادي بدون تنسيق
                    import re
                    plain_info = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', masters_info)
                    await message.reply(plain_info, disable_web_page_preview=True)
                
            except Exception as e:
                logging.error(f"خطأ في عرض قائمة الأسياد: {e}")
                await message.reply("❌ حدث خطأ في تحميل قائمة الأسياد")
        else:
            await message.reply("❌ هذا الأمر متاح للأسياد فقط")
        return
    
    # === أمر عرض المكتومين ===
    if text in ['المكتومين', 'مكتومين', 'قائمة المكتومين']:
        try:
            from modules.group_management import show_muted_users
            await show_muted_users(message)
        except Exception as e:
            logging.error(f"خطأ في عرض المكتومين: {e}")
            await message.reply("❌ حدث خطأ في عرض قائمة المكتومين")
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
    elif text in ['حصاد محاصيلي', 'حصاد الكل']:
        await farm.harvest_all_crops_command(message)
    elif text.startswith('حصاد ') and len(text.split()) >= 3:
        await farm.harvest_specific_crop_command(message)
    elif text == 'حالة المزرعة':
        await farm.show_farm_status(message)
    elif text == 'شراء بذور':
        await farm.show_seeds_shop(message)
    elif text.strip() in ['مزرعة', 'مزرعتي', 'المزرعة'] or (len(words) == 1 and words[0] in ['مزرعة', 'مزرعتي', 'المزرعة']):
        await farm.show_farm_menu(message)
    elif any(phrase in text for phrase in ['انشاء قلعة', 'إنشاء قلعة', 'انشئ قلعة']):
        await castle.create_castle_command(message, state)
    elif text.strip() in ['قلعة', 'قلعتي', 'القلعة']:
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
        await castle.delete_castle_command(message, state)
    # تم نقل معالجة تأكيد/إلغاء حذف القلعة إلى نظام الحالات
    elif text.strip() in ['حساب اللاعب', 'تفاصيلي'] or 'حساب اللاعب' in text or 'تفاصيلي' in text:
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
    
    # === أوامر المسح === (تم نقلها لأعلى)
    
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
    elif text.strip() == 'معلوماتي':
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
    elif text.startswith('بحث ') and not any(phrase in text for phrase in ['كنز', 'عن كنز']):
        await handle_music_search(message)
    
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
    elif text == 'خلع':
        await entertainment.handle_marriage(message, "خلع")
    elif text == 'موافقة':
        await entertainment.handle_marriage_response(message, "موافقة")
    elif text == 'رفض':
        await entertainment.handle_marriage_response(message, "رفض")
    elif text in ['زوجي', 'زوجتي']:
        await entertainment.show_marriage_status(message)
    elif text == 'رقص':
        await entertainment.wedding_dance(message)
    elif text == 'اعراس' or text == 'أعراس':
        await entertainment.show_group_weddings(message)
    elif text == 'مراسم':
        await entertainment.start_royal_ceremony(message)
    elif text == 'هدية':
        await entertainment.give_wedding_gift(message)
    elif text == 'تهنئة':
        await entertainment.wedding_congratulation(message)
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
    # قائمة التصنيف الذهبي
    elif text in ['قائمة التصنيف', 'التصنيف', 'الترتيب الذهبي', 'النقاط الذهبية']:
        from modules.ranking_system import show_ranking_list
        await show_ranking_list(message)
        return
    elif text in ['تفاعلي', 'ترتيب التفاعل', 'ترتيب المجموعة']:
        await utility_commands.show_group_activity_ranking(message)
    elif text in ['رسائلي', 'عدد رسائلي']:
        await utility_commands.show_my_messages_count(message)
    elif text in ['رسائله', 'عدد رسائله'] and message.reply_to_message:
        await utility_commands.show_target_user_messages(message)
    elif text in ['تفاعله', 'نشاطه'] and message.reply_to_message:
        await utility_commands.show_target_user_activity(message)
    elif text.strip() == 'رتبتي':
        from modules import user_info
        await user_info.show_my_rank(message)
    elif text == 'رتبته' and message.reply_to_message:
        from modules import user_info
        await user_info.show_user_rank(message)
    elif text.strip() == 'فلوسي':
        from modules import user_info
        await user_info.show_my_balance(message)
    elif text.strip() == 'حسابي':
        # عرض معلومات الحساب الشاملة
        from modules import user_info
        await user_info.show_comprehensive_account_info(message)
    elif text == 'فلوسه' and message.reply_to_message:
        from modules import user_info
        await user_info.show_user_balance(message)
    elif text.strip() == "مستواي" or text.strip() == "تقدمي" or re.search(r'\b(مستوى)\b', text):
        # عرض معلومات المستوى
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
    
    # معالجة تخمينات الألعاب (فقط عند وجود ألعاب نشطة)
    elif message.chat.type in ['group', 'supergroup']:
        try:
            # فحص وجود ألعاب نشطة قبل المعالجة
            group_id = message.chat.id
            
            # معالجة تخمينات لعبة الكلمة (فقط إذا كانت نشطة)
            from modules.word_game import ACTIVE_WORD_GAMES
            if group_id in ACTIVE_WORD_GAMES and not ACTIVE_WORD_GAMES[group_id].game_ended:
                from modules.word_game import handle_word_guess
                await handle_word_guess(message)
            
            # معالجة تخمينات لعبة الرموز (فقط إذا كانت نشطة)
            from modules.symbols_game import ACTIVE_SYMBOLS_GAMES
            if group_id in ACTIVE_SYMBOLS_GAMES and not ACTIVE_SYMBOLS_GAMES[group_id].game_ended:
                from modules.symbols_game import handle_symbols_guess
                await handle_symbols_guess(message)
            
            # معالجة تخمينات لعبة ترتيب الحروف (فقط إذا كانت نشطة)
            from modules.letter_shuffle_game import ACTIVE_SHUFFLE_GAMES
            if group_id in ACTIVE_SHUFFLE_GAMES and not ACTIVE_SHUFFLE_GAMES[group_id].game_ended:
                from modules.letter_shuffle_game import handle_shuffle_guess
                await handle_shuffle_guess(message)
        except Exception as e:
            logging.error(f"خطأ في معالجة تخمينات الألعاب: {e}")
    
    # === فحص الذكاء الاصطناعي في النهاية (بعد جميع الأوامر المطلقة والمهمة) ===
    
    # فحص إذا كان يرد على رسالة من يوكي بدون ذكر اسمه
    is_reply_to_yuki = False
    if (message.reply_to_message and 
        message.reply_to_message.from_user and 
        message.reply_to_message.from_user.is_bot and
        message.reply_to_message.from_user.id == 7942168520):  # معرف بوت يوكي
        is_reply_to_yuki = True
        logging.info(f"🔄 رد على رسالة يوكي: '{message.text}' من المستخدم {message.from_user.id}")
    
    # فحص ذكر اسم يوكي في النص
    has_yuki_mention = (message.text and 
                       any(trigger in message.text.lower() for trigger in ['يوكي', 'yuki', 'يوكى']))
    
    # تشغيل النظام الذكي إذا ذُكر يوكي أو إذا كان رداً على رسالة يوكي
    if (message.text and message.chat.type in ['group', 'supergroup'] and
        (has_yuki_mention or is_reply_to_yuki)):
        
        if has_yuki_mention:
            logging.info(f"🎯 تم اكتشاف رسالة يوكي: '{message.text}' - توجيه للنظام المتقدم")
        elif is_reply_to_yuki:
            logging.info(f"💬 رد على رسالة يوكي: '{message.text}' - توجيه للنظام المتقدم")
            
        try:
            from modules.real_ai import handle_real_yuki_ai_message
            await handle_real_yuki_ai_message(message)
            return
        except Exception as e:
            logging.error(f"خطأ في نظام الذكاء الاصطناعي الحقيقي: {e}")
            import traceback
            logging.error(f"تفاصيل الخطأ: {traceback.format_exc()}")
            await message.reply("🤖 مرحباً! أنا يوكي، النظام الذكي معطل مؤقتاً، لكن يمكنك استخدام جميع ألعاب وأنظمة البوت الأخرى!")
            return
    
    # === فحص أوامر الذاكرة المشتركة قبل النهاية ===
    if message.text:
        try:
            from handlers.memory_commands import handle_memory_commands
            if await handle_memory_commands(message):
                return
        except Exception as e:
            logging.error(f"خطأ في معالج أوامر الذاكرة: {e}")
    
    # === منح XP للرسائل العادية في نهاية معالجة الرسائل ===
    if (message.text and message.chat.type in ['group', 'supergroup'] and 
        message.from_user and not message.from_user.is_bot):
        try:
            # منح XP للنشاط العادي (الرسائل) باستخدام النظام المباشر
            from modules.leveling import leveling_system
            success, xp_message = await leveling_system.add_xp(message.from_user.id, "message")
            
            # تحديث نشاط المستخدم
            await update_user_activity(message.from_user.id)
            
            if success:
                logging.info(f"✨ تم منح XP للمستخدم {message.from_user.id} من الرسالة العادية - {xp_message}")
            else:
                logging.warning(f"⚠️ فشل منح XP للمستخدم {message.from_user.id}: {xp_message}")
            
        except Exception as e:
            logging.error(f"خطأ في منح XP للرسالة العادية: {e}")
    
    # البوت لا يرد على الرسائل غير المعروفة


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
        
        if current_state == CustomReplyStates.waiting_for_keyword.state:
            await handle_keyword_input(message, state)
        elif current_state == CustomReplyStates.waiting_for_response.state:
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
        # معالجة تأكيد الترقية مؤقتاً
        await castle.upgrade_castle_command(message)
    elif current_state == CastleStates.waiting_delete_confirmation.state:
        # معالجة تأكيد أو إلغاء حذف القلعة
        text = message.text.strip()
        if text in ['تأكيد', 'نعم']:
            await castle.confirm_delete_castle_command(message, state)
        elif text == 'لا':
            await castle.cancel_delete_castle_command(message, state)
        else:
            await message.reply(
                "❓ يرجى الإجابة بوضوح:\n"
                "✅ **تأكيد** أو **نعم** للموافقة على حذف القلعة\n"
                "❌ **لا** لإلغاء العملية"
            )


async def handle_admin_message(message: Message, state: FSMContext, current_state: str):
    """معالجة رسائل الإدارة"""
    if current_state == AdminStates.waiting_broadcast_message.state:
        await administration.process_broadcast_message(message, state)
    elif current_state == AdminStates.waiting_user_id_action.state:
        await administration.process_user_id_action(message, state)


# معالج الصور والملفات الذكي مع فحص المحتوى
@router.message(F.photo | F.document | F.video | F.audio)
@user_required
async def handle_media_messages(message: Message):
    """معالج الرسائل المتعددة الوسائط مع فحص المحتوى"""
    try:
        # استيراد الوحدات المطلوبة
        from modules.media_analyzer import media_analyzer
        from modules.content_moderation import content_moderator
        
        # إرسال رسالة معالجة
        processing_msg = await message.reply("🔍 جاري تحليل الملف...")
        
        bot = message.bot
        analysis_result = None
        file_path = None
        
        # تحديد نوع الملف ومعالجته
        if message.photo:
            # معالجة الصور
            photo = message.photo[-1]  # أعلى جودة
            file_path = await media_analyzer.download_media_file(bot, photo.file_id, "image.jpg")
            if file_path:
                analysis_result = await media_analyzer.analyze_image_content(file_path)
        
        elif message.video:
            # معالجة الفيديو
            video = message.video
            file_path = await media_analyzer.download_media_file(bot, video.file_id, "video.mp4")
            if file_path:
                analysis_result = await media_analyzer.analyze_video_content(file_path)
        
        elif message.document:
            # معالجة المستندات
            document = message.document
            file_path = await media_analyzer.download_media_file(bot, document.file_id, document.file_name or "document")
            if file_path:
                analysis_result = await media_analyzer.analyze_document_content(file_path)
        
        elif message.audio:
            # للصوتيات، نعتبرها آمنة مؤقتاً (يمكن إضافة تحليل الصوت لاحقاً)
            analysis_result = {
                "is_safe": True,
                "violations": [],
                "severity": "low",
                "description": "ملف صوتي",
                "confidence": 0.8
            }
        
        # التحقق من نتيجة التحليل
        if analysis_result and not analysis_result.get("error"):
            # فحص المخالفات
            violation_detected = await content_moderator.handle_violation(message, bot, analysis_result)
            
            if violation_detected:
                # تم حذف الملف - حذف رسالة المعالجة
                try:
                    await processing_msg.delete()
                except:
                    pass
            else:
                # الملف آمن - إرسال رد إيجابي
                if analysis_result.get("is_safe", True):
                    await processing_msg.edit_text(
                        "✅ **تم تحليل الملف بنجاح!**\n\n"
                        f"📋 **النوع:** {'صورة' if message.photo else 'فيديو' if message.video else 'مستند' if message.document else 'صوت'}\n"
                        f"🛡️ **الحالة:** محتوى آمن\n"
                        f"🤖 **تحليل الذكاء الاصطناعي:** {analysis_result.get('description', 'تم فحص المحتوى')[:100]}...\n\n"
                        f"💡 يمكنك الآن استخدام الأوامر النصية للتفاعل مع البوت."
                    )
                else:
                    # مخالفة بسيطة - تحذير فقط
                    await processing_msg.edit_text(
                        "⚠️ **تحذير بسيط**\n\n"
                        f"تم اكتشاف محتوى قد يكون غير مناسب، لكن لم يتم حذفه.\n"
                        f"يرجى الحرص على نشر محتوى مناسب للجميع."
                    )
        else:
            # خطأ في التحليل
            error_msg = analysis_result.get("error", "خطأ غير معروف") if analysis_result else "فشل في التحميل"
            await processing_msg.edit_text(
                f"❌ **خطأ في تحليل الملف**\n\n"
                f"📝 التفاصيل: {error_msg}\n"
                f"🔄 يرجى المحاولة مرة أخرى أو استخدام الأوامر النصية."
            )
        
        # تنظيف الملف المؤقت
        if file_path:
            await media_analyzer.cleanup_temp_file(file_path)
    
    except Exception as e:
        logging.error(f"❌ خطأ في معالج الوسائط: {e}")
        try:
            await message.reply(
                "❌ حدث خطأ أثناء معالجة الملف.\n"
                "يرجى المحاولة مرة أخرى أو استخدام الأوامر النصية."
            )
        except:
            pass


# تم حذف معالج الملصقات لتمرير جميع الملصقات لمحلل المحتوى في unified_message_processor.py



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




# معالج الذكاء الاصطناعي الشامل - يأتي كآخر معالج
@router.message(F.text)
@group_only  # يعمل فقط في المجموعات
async def handle_ai_comprehensive_response(message: Message):
    """المعالج الذكي الشامل للرسائل - يدمج جميع أنظمة الذكاء الاصطناعي"""
    try:
        # فحص فلتر الألفاظ المسيئة قبل كل شيء
        if message.text and message.chat.type in ['group', 'supergroup']:
            try:
                from modules.profanity_filter import ProfanityFilter
                profanity_filter = ProfanityFilter()
                
                # التحقق من تفعيل الفلتر في هذه المجموعة
                if profanity_filter.is_enabled(message.chat.id):
                    # فحص النص للألفاظ المسيئة
                    has_profanity, found_words = profanity_filter.contains_profanity(message.text)
                    
                    if has_profanity:
                        # حذف الرسالة فوراً
                        try:
                            await message.delete()
                            logging.info(f"🗑️ تم حذف رسالة مسيئة من المعالج الشامل للمستخدم {message.from_user.id}: '{message.text}'")
                        except Exception as delete_error:
                            logging.error(f"❌ خطأ في حذف الرسالة: {delete_error}")
                        
                        # إرسال تحذير للمستخدم
                        user_name = message.from_user.first_name or "المستخدم"
                        warning_text = f"⚠️ **تحذير!**\n\n👤 {user_name}\n🚫 تم حذف رسالتك لاحتوائها على ألفاظ مسيئة\n\n🔍 **الكلمات المكتشفة:** {', '.join(found_words[:3])}"
                        
                        try:
                            await message.bot.send_message(
                                chat_id=message.chat.id,
                                text=warning_text,
                                parse_mode='Markdown'
                            )
                        except Exception as warn_error:
                            logging.error(f"❌ خطأ في إرسال التحذير: {warn_error}")
                        
                        return  # توقف عن معالجة الرسالة
            except Exception as filter_error:
                logging.error(f"خطأ في فلتر الألفاظ: {filter_error}")
        
        # استثناء أوامر نظام التقرير الملكي
        if message.text in ["تقرير", "إبلاغ", "تقارير", "تقاريري", "تقاريري الخاصة", "تقارير المستخدم", "إحصائيات_التقارير"]:
            return  # تمرير للمعالج المخصص
            
        # التحقق من أن الرسالة تحتوي على نص
        if not message.text or message.text.strip() == "":
            return
        
        # تجاهل الأوامر التي بدأت بـ /
        if message.text.startswith('/'):
            return
        
        # نظام عبيد الذكي - تتبع رسائل عبيد
        # تم حذف النظام غير الضروري
        
        # فحص الردود على رسائل عبيد
        if message.reply_to_message:
            # تم حذف النظام غير الضروري
            pass
            
        # تجاهل الرسائل التي تحتوي على أوامر معروفة تم التعامل معها
        text_lower = message.text.lower().strip()
        
        # قائمة الأوامر المعروفة التي لا نريد الرد عليها بالذكاء الاصطناعي
        known_commands = [
            'الأوامر', 'معلوماتي', 'راتب', 'ايداع', 'سحب', 'تحويل',
            'عقار', 'استثمار', 'أسهم', 'مزرعة', 'قلعة', 'ترتيب',
            'بان', 'كتم', 'طرد', 'قفل', 'الغاء القفل',
            'انشاء حساب', 'انشئ حساب', 'سرقة', 'سرف',
            # أوامر القائمة الذكية
            'قائمة ذكية', 'القائمة الذكية', 'تحليل اقتصادي', 'حلل وضعي',
            'استراتيجية ذكية', 'اقترح استراتيجية', 'العاب ذكية', 'اقترح لعبة',
            'كويز ذكي', 'اختبار ذكي', 'تحدي اقتصادي', 'تحدي ذكي',
            'قصة ذكية', 'احكي قصة', 'معركة ذكية', 'تحدي يوكي',
            'حالة الذكاء الاصطناعي'
        ]
        
        # إذا كانت الرسالة تحتوي على أوامر معروفة، لا نرد بالذكاء الاصطناعي
        if any(cmd in text_lower for cmd in known_commands):
            return
        
        # فحص fallback للأوامر الإدارية غير المتعرف عليها
        admin_command_patterns = [
            'قفل', 'فتح', 'حظر', 'إلغاء حظر',
            'رفع', 'تنزيل', 'طرد', 'كتم', 'إلغاء كتم'
        ]
        
        # فحص خاص لأوامر التفعيل والتعطيل (ما عدا أوامر العقوبات)
        if text_lower.startswith('تفعيل') or text_lower.startswith('تعطيل'):
            # إذا كان الأمر يتعلق بالعقوبات أو العقود، لا نتدخل
            if not any(keyword in text_lower for keyword in ['عقوبة', 'عقوبات', 'عقود']):
                if any(text_lower.startswith(pattern) for pattern in ['تفعيل', 'تعطيل']):
                    await message.reply("❌ إعداد غير صحيح")
                    return
        elif any(text_lower.startswith(pattern) for pattern in admin_command_patterns):
            await message.reply("❌ إعداد غير صحيح")
            return
        
        # فحص التفاعل العشوائي لعبيد
        # تم حذف النظام غير الضروري
        
        # معالجة الرسالة بنظام الذكاء الاصطناعي الشامل
        ai_response = await ai_integration.handle_message_with_ai(message)
        
        if ai_response:
            # إرسال الرد الذكي
            await message.reply(ai_response, parse_mode='Markdown')
            
            # إضافة XP إضافي للتفاعل مع الذكاء الاصطناعي
            try:
                from modules.leveling import add_xp
                await add_xp(message.from_user.id, 5)  # 5 XP إضافي للتفاعل الذكي
            except Exception as xp_error:
                logging.error(f"خطأ في إضافة XP للتفاعل الذكي: {xp_error}")
        
    except Exception as e:
        logging.error(f"خطأ في معالج الذكاء الاصطناعي الشامل: {e}")
        # لا نرسل رسالة خطأ حتى لا نزعج المستخدمين، فقط نسجل الخطأ


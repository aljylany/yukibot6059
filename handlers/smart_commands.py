"""
معالج الأوامر الذكية - Smart Commands Handler
يتعامل مع الأوامر الذكية الجديدة التي تعرض خيارات مرقمة
"""

import logging
from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from utils.decorators import user_required, group_only
from utils.states import SmartCommandStates
from modules.smart_menu_handler import smart_menu_handler

router = Router()


@router.message(F.text.in_([
    "قائمة ذكية", "القائمة الذكية", "أوامر ذكية", 
    "الأوامر الذكية", "خيارات ذكية"
]))
@user_required
@group_only
async def show_smart_menu(message: Message, state: FSMContext):
    """عرض القائمة الذكية الرئيسية"""
    try:
        user_name = message.from_user.first_name or "صديقي"
        
        smart_menu = f"""
🧠 **القائمة الذكية لـ {user_name}**

اختر من الخيارات التالية:

1️⃣ 📊 التحليل الاقتصادي الذكي
    تحليل شامل لوضعك المالي مع نصائح مخصصة

2️⃣ 💡 استراتيجية الاستثمار الذكية  
    استراتيجية مخصصة لحالتك المالية

3️⃣ 🎮 اقتراح الألعاب الذكية
    ألعاب مناسبة لمستواك ومهاراتك

4️⃣ 🧠 الكويز الذكي التكيفي
    كويز يتكيف مع مستوى معرفتك

5️⃣ 💼 التحدي الاقتصادي الذكي
    سيناريوهات اقتصادية واقعية

6️⃣ 📖 القصة التفاعلية الذكية
    قصص تتغير حسب اختياراتك

7️⃣ ⚔️ معركة الذكاء مع يوكي
    تحديات ذكية مباشرة ضد يوكي

8️⃣ 🔧 حالة الأنظمة الذكية
    فحص حالة جميع الأنظمة الذكية

⚡ **اكتب رقم الخيار للبدء:**
"""
        
        await message.reply(smart_menu)
        await state.set_state(SmartCommandStates.waiting_smart_menu_choice)
        
    except Exception as e:
        logging.error(f"خطأ في عرض القائمة الذكية: {e}")
        await message.reply("❌ حدث خطأ في عرض القائمة الذكية")


# معالج الأوامر المباشرة للميزات الذكية
@router.message(F.text.regexp(r"تحليل (اقتصادي|ذكي|مالي)"))
@router.message(F.text.in_([
    "حلل وضعي", "تحليل وضعي", "تحليل حالتي", 
    "تحليل اقتصادي", "تحليل ذكي", "تحليل مالي"
]))
@user_required  
@group_only
async def economic_analysis_command(message: Message):
    """أمر التحليل الاقتصادي المباشر"""
    try:
        await smart_menu_handler.handle_economic_analysis(
            message, 
            message.from_user.id, 
            message.chat.id,
            message.from_user.first_name or "صديقي"
        )
    except Exception as e:
        logging.error(f"خطأ في التحليل الاقتصادي المباشر: {e}")
        await message.reply("❌ حدث خطأ في التحليل الاقتصادي")


@router.message(F.text.regexp(r"استراتيجية (ذكية|استثمار)"))
@router.message(F.text.in_([
    "اقترح استراتيجية", "نصائح استثمار", "استراتيجية ذكية",
    "استراتيجية استثمار", "خطة استثمار"
]))
@user_required
@group_only  
async def investment_strategy_command(message: Message):
    """أمر استراتيجية الاستثمار المباشر"""
    try:
        await smart_menu_handler.handle_investment_strategy(
            message,
            message.from_user.id,
            message.chat.id, 
            message.from_user.first_name or "صديقي"
        )
    except Exception as e:
        logging.error(f"خطأ في استراتيجية الاستثمار المباشر: {e}")
        await message.reply("❌ حدث خطأ في استراتيجية الاستثمار")


@router.message(F.text.regexp(r"العاب (ذكية|مناسبة)"))
@router.message(F.text.in_([
    "اقترح لعبة", "العاب ذكية", "ألعاب ذكية",
    "العاب مناسبة", "ألعاب مناسبة"
]))
@user_required
@group_only
async def smart_games_command(message: Message, state: FSMContext):
    """أمر اقتراح الألعاب الذكية"""
    try:
        await smart_menu_handler.handle_smart_games(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي",
            state
        )
    except Exception as e:
        logging.error(f"خطأ في اقتراح الألعاب الذكية: {e}")
        await message.reply("❌ حدث خطأ في اقتراح الألعاب")


@router.message(F.text.regexp(r"كويز (ذكي|تكيفي)"))
@router.message(F.text.in_([
    "اختبار ذكي", "سؤال وجواب ذكي", "كويز ذكي",
    "اختبار تكيفي", "كويز تكيفي"
]))
@user_required
@group_only
async def adaptive_quiz_command(message: Message, state: FSMContext):
    """أمر الكويز الذكي التكيفي"""
    try:
        await smart_menu_handler.handle_adaptive_quiz(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي",
            state
        )
    except Exception as e:
        logging.error(f"خطأ في الكويز الذكي التكيفي: {e}")
        await message.reply("❌ حدث خطأ في الكويز التكيفي")


@router.message(F.text.regexp(r"تحدي (اقتصادي|ذكي|مالي)"))
@router.message(F.text.in_([
    "اختبار اقتصادي", "تحدي اقتصادي", "تحدي ذكي",
    "تحدي مالي", "اختبار مالي"
]))
@user_required
@group_only
async def economic_challenge_command(message: Message, state: FSMContext):
    """أمر التحدي الاقتصادي الذكي"""
    try:
        await smart_menu_handler.handle_economic_challenge(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي",
            state
        )
    except Exception as e:
        logging.error(f"خطأ في التحدي الاقتصادي الذكي: {e}")
        await message.reply("❌ حدث خطأ في التحدي الاقتصادي")


@router.message(F.text.regexp(r"قصة (ذكية|تفاعلية)"))
@router.message(F.text.in_([
    "احكي قصة", "قصة مغامرة", "قصة ذكية", 
    "قصة تفاعلية", "قصة مخصصة"
]))
@user_required
@group_only
async def interactive_story_command(message: Message, state: FSMContext):
    """أمر القصة التفاعلية الذكية"""
    try:
        await smart_menu_handler.handle_interactive_story(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي",
            state
        )
    except Exception as e:
        logging.error(f"خطأ في القصة التفاعلية الذكية: {e}")
        await message.reply("❌ حدث خطأ في القصة التفاعلية")


@router.message(F.text.regexp(r"معركة (ذكية|ذكاء)"))
@router.message(F.text.in_([
    "تحدي يوكي", "معركة مع يوكي", "معركة ذكية",
    "باتل ذكي", "معركة الذكاء", "تحدي ذكي"
]))
@user_required
@group_only
async def ai_battle_command(message: Message, state: FSMContext):
    """أمر معركة الذكاء مع يوكي"""
    try:
        await smart_menu_handler.handle_ai_battle(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي",
            state
        )
    except Exception as e:
        logging.error(f"خطأ في معركة الذكاء: {e}")
        await message.reply("❌ حدث خطأ في معركة الذكاء")


@router.message(F.text.in_([
    "حالة الذكاء الاصطناعي", "حالة الانظمة الذكية", 
    "وضع الذكاء", "فحص الانظمة", "حالة النظام الذكي"
]))
@user_required
@group_only
async def ai_system_status_command(message: Message):
    """أمر فحص حالة الأنظمة الذكية"""
    try:
        await smart_menu_handler.handle_system_status(
            message,
            message.from_user.id,
            message.chat.id,
            message.from_user.first_name or "صديقي"
        )
    except Exception as e:
        logging.error(f"خطأ في فحص حالة الأنظمة الذكية: {e}")
        await message.reply("❌ حدث خطأ في فحص حالة الأنظمة")
"""
معالج نظام التقرير الملكي
Bug Report System Handler
"""

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from datetime import datetime

from modules.bug_report_system import bug_report_system
from utils.states import ReportStates
from utils.decorators import user_required
from config.settings import ADMIN_IDS

router = Router()

# أوامر النظام للمستخدمين العاديين
@router.message(Command("report", "تقرير", "إبلاغ"))
@user_required
async def report_command(message: Message):
    """أمر إنشاء تقرير جديد"""
    try:
        await bug_report_system.show_report_menu(message)
    except Exception as e:
        logging.error(f"خطأ في أمر التقرير: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة التقارير")

# معالج النصوص العادية لكلمة "تقرير"
@router.message(F.text.in_(["تقرير", "إبلاغ", "تقارير"]))
@user_required
async def report_text_command(message: Message):
    """معالج النص العادي لإنشاء تقرير"""
    try:
        await bug_report_system.show_report_menu(message)
    except Exception as e:
        logging.error(f"خطأ في أمر التقرير النصي: {e}")
        await message.reply("❌ حدث خطأ في عرض قائمة التقارير")

@router.message(Command("my_reports", "تقاريري"))
@user_required  
async def my_reports_command(message: Message):
    """عرض تقارير المستخدم"""
    try:
        await bug_report_system.show_user_reports(message)
    except Exception as e:
        logging.error(f"خطأ في عرض تقارير المستخدم: {e}")
        await message.reply("❌ حدث خطأ في عرض تقاريرك")

# معالج النصوص العادية لكلمة "تقاريري"
@router.message(F.text.in_(["تقاريري", "تقاريري الخاصة", "تقارير المستخدم"]))
@user_required
async def my_reports_text_command(message: Message):
    """معالج النص العادي لعرض تقارير المستخدم"""
    try:
        await bug_report_system.show_user_reports(message)
    except Exception as e:
        logging.error(f"خطأ في عرض تقارير المستخدم النصي: {e}")
        await message.reply("❌ حدث خطأ في عرض تقاريرك")

@router.message(Command("report_stats", "إحصائيات_التقارير"))
@user_required
async def report_stats_command(message: Message):
    """عرض إحصائيات المستخدم في التقارير"""
    try:
        await bug_report_system.show_detailed_stats(message)
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات التقارير: {e}")
        await message.reply("❌ حدث خطأ في عرض الإحصائيات")

# معالجة أمر التحقق من تقرير معين
@router.message(F.text.startswith(("تقرير RPT", "report RPT")))
@user_required
async def check_specific_report(message: Message):
    """التحقق من حالة تقرير معين"""
    try:
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ استخدم: تقرير RPT123456789")
            return
            
        report_id = parts[1]
        await bug_report_system.show_report_details(message, report_id)
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من التقرير: {e}")
        await message.reply("❌ حدث خطأ في جلب بيانات التقرير")

# معالج الcallbacks للأزرار
@router.callback_query(F.data.startswith("report:"))
async def handle_report_callbacks(callback: CallbackQuery, state: FSMContext):
    """معالج callbacks نظام التقارير"""
    try:
        action = callback.data.split(":")[1]
        
        if action in ["critical", "major", "minor", "suggestion"]:
            await bug_report_system.start_bug_report(callback, state, action)
        elif action == "cancel":
            await state.clear()
            await callback.message.edit_text("❌ تم إلغاء العملية")
        elif action == "stats":
            # تحويل callback إلى message-like object
            fake_message = type('FakeMessage', (), {
                'from_user': callback.from_user,
                'reply': lambda text: callback.message.edit_text(text)
            })()
            await bug_report_system.show_detailed_stats(fake_message)
        elif action == "my_reports":
            # تحويل callback إلى message-like object
            fake_message = type('FakeMessage', (), {
                'from_user': callback.from_user,
                'reply': lambda text: callback.message.edit_text(text)
            })()
            await bug_report_system.show_user_reports(fake_message)
        else:
            await callback.answer("❌ عملية غير معروفة")
            
    except Exception as e:
        logging.error(f"خطأ في معالج callbacks التقارير: {e}")
        await callback.answer("❌ حدث خطأ في النظام")

# معالجة الحالات المختلفة لإنشاء التقرير
@router.message(StateFilter(ReportStates.waiting_title))
async def handle_report_title(message: Message, state: FSMContext):
    """معالجة عنوان التقرير"""
    await bug_report_system.process_report_title(message, state)

@router.message(StateFilter(ReportStates.waiting_description))  
async def handle_report_description(message: Message, state: FSMContext):
    """معالجة وصف التقرير"""
    await bug_report_system.process_report_description(message, state)

# === أوامر المديرين ===

@router.message(Command("admin_reports", "تقارير_المديرين"))
async def admin_reports_command(message: Message):
    """عرض جميع التقارير للمديرين"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط")
            return
            
        await bug_report_system.show_admin_reports(message)
        
    except Exception as e:
        logging.error(f"خطأ في عرض تقارير المديرين: {e}")
        await message.reply("❌ حدث خطأ في عرض التقارير")

@router.message(F.text.startswith(("/admin_report", "/تقرير_مدير")))
async def admin_single_report_command(message: Message):
    """عرض تقرير واحد للمديرين"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط")
            return
        
        parts = message.text.split()
        if len(parts) < 2:
            await message.reply("❌ استخدم: /admin_report RPT123456789")
            return
            
        report_id = parts[1]
        await bug_report_system.show_admin_report_details(message, report_id)
        
    except Exception as e:
        logging.error(f"خطأ في عرض تفاصيل التقرير للمدير: {e}")
        await message.reply("❌ حدث خطأ في جلب التقرير")

@router.message(F.text.startswith(("/update_report", "/تحديث_تقرير")))
async def update_report_status_command(message: Message):
    """تحديث حالة التقرير"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            await message.reply("""
❌ استخدام خاطئ!

**الصيغة الصحيحة:**
`/update_report RPT123456789 الحالة_الجديدة`

**الحالات المتاحة:**
• `in_progress` - قيد العمل
• `testing` - قيد الاختبار
• `fixed` - تم الإصلاح
• `rejected` - مرفوض
• `duplicate` - مكرر

**مثال:**
`/update_report RPT202508301234567 fixed`
            """)
            return
            
        report_id = parts[1]
        new_status = parts[2]
        
        await bug_report_system.update_report_status(message, report_id, new_status)
        
    except Exception as e:
        logging.error(f"خطأ في تحديث حالة التقرير: {e}")
        await message.reply("❌ حدث خطأ في تحديث التقرير")

@router.message(Command("reports_stats", "إحصائيات_كل_التقارير"))
async def all_reports_stats_command(message: Message):
    """إحصائيات شاملة عن جميع التقارير - للمديرين"""
    try:
        if message.from_user.id not in ADMIN_IDS:
            await message.reply("❌ هذا الأمر متاح للمديرين فقط")
            return
            
        await bug_report_system.show_system_stats(message)
        
    except Exception as e:
        logging.error(f"خطأ في عرض إحصائيات النظام: {e}")
        await message.reply("❌ حدث خطأ في عرض الإحصائيات")

# أوامر التصويت المجتمعي
@router.callback_query(F.data.startswith("vote_report:"))
async def handle_report_voting(callback: CallbackQuery):
    """معالج التصويت على التقارير"""
    try:
        parts = callback.data.split(":")
        report_id = parts[1] 
        vote_type = parts[2]  # "confirm" أو "deny"
        
        await bug_report_system.process_vote(callback, report_id, vote_type)
        
    except Exception as e:
        logging.error(f"خطأ في معالجة التصويت: {e}")
        await callback.answer("❌ حدث خطأ في التصويت")

@router.callback_query(F.data.startswith("admin_report:"))
async def handle_admin_report_actions(callback: CallbackQuery):
    """معالج إجراءات المديرين على التقارير"""
    try:
        if callback.from_user.id not in ADMIN_IDS:
            await callback.answer("❌ هذا الأمر متاح للمديرين فقط")
            return
            
        parts = callback.data.split(":")
        action = parts[1]
        report_id = parts[2] if len(parts) > 2 else None
        
        if action == "assign_to_me":
            await bug_report_system.assign_report(callback, report_id, callback.from_user.id)
        elif action == "mark_fixed":
            await bug_report_system.mark_as_fixed(callback, report_id)
        elif action == "mark_duplicate": 
            await bug_report_system.mark_as_duplicate(callback, report_id)
        elif action == "reject":
            await bug_report_system.reject_report(callback, report_id)
        else:
            await callback.answer("❌ إجراء غير معروف")
            
    except Exception as e:
        logging.error(f"خطأ في معالجة إجراءات المديرين: {e}")
        await callback.answer("❌ حدث خطأ في النظام")
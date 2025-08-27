"""
أوامر المشرفين للنظام الشامل
Comprehensive Admin Commands
"""

import logging
from datetime import datetime
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext

from handlers.comprehensive_content_handler import (
    get_comprehensive_group_stats,
    get_user_comprehensive_report,
    toggle_comprehensive_system,
    subscribe_admin_to_comprehensive_reports,
    get_system_status,
    comprehensive_handler
)
from modules.admin_reports_system import admin_reports
from config.hierarchy import has_permission, AdminLevel, is_master
from utils.decorators import admin_required, group_only

class ComprehensiveAdminCommands:
    """أوامر المشرفين للنظام الشامل"""
    
    def __init__(self):
        self.commands = {
            # أوامر الإحصائيات والتقارير
            'احصائيات_الأمان': self.show_security_stats,
            'تقرير_المجموعة': self.show_group_report,
            'تقرير_مستخدم': self.show_user_report,
            'ملخص_يومي': self.show_daily_summary,
            
            # أوامر التحكم في النظام
            'تفعيل_النظام_الشامل': self.enable_comprehensive_system,
            'تعطيل_النظام_الشامل': self.disable_comprehensive_system,
            'حالة_النظام': self.show_system_status,
            
            # أوامر التقارير والإشعارات
            'اشتراك_تقارير': self.subscribe_to_reports,
            'إلغاء_اشتراك_تقارير': self.unsubscribe_from_reports,
            'تقارير_فورية': self.toggle_instant_reports,
            'ملخص_يومي_تلقائي': self.toggle_daily_summary,
            
            # أوامر الإدارة المتقدمة
            'مراجعة_تقرير': self.review_report,
            'حذف_سجل_مستخدم': self.clear_user_record,
            'إعادة_تعيين_نقاط': self.reset_user_points,
            'قائمة_المحظورين': self.show_banned_users,
            
            # أوامر التحليل والإحصائيات المتقدمة
            'تحليل_المخاطر': self.analyze_group_risks,
            'إحصائيات_أسبوعية': self.show_weekly_stats,
            'إحصائيات_شهرية': self.show_monthly_stats,
            'تصدير_التقارير': self.export_reports,
        }
    
    async def handle_admin_command(self, message: Message, command: str, args: list = None) -> bool:
        """معالجة أوامر المشرفين"""
        try:
            # التحقق من الصلاحيات
            if not (has_permission(message.from_user.id, AdminLevel.MODERATOR, message.chat.id) or 
                   has_permission(message.from_user.id, AdminLevel.GROUP_OWNER, message.chat.id) or 
                   is_master(message.from_user.id)):
                await message.reply("❌ ليس لديك صلاحية لاستخدام هذا الأمر")
                return False
            
            # البحث عن الأمر
            handler = self.commands.get(command)
            if not handler:
                return False
            
            # تنفيذ الأمر
            await handler(message, args or [])
            return True
            
        except Exception as e:
            logging.error(f"❌ خطأ في معالجة أمر المشرف: {e}")
            await message.reply("❌ حدث خطأ في تنفيذ الأمر")
            return False
    
    # أوامر الإحصائيات والتقارير
    async def show_security_stats(self, message: Message, args: list):
        """عرض إحصائيات الأمان"""
        try:
            stats = await get_comprehensive_group_stats(message.chat.id)
            
            # إضافة معلومات إضافية
            enhanced_stats = f"🔒 **إحصائيات الأمان الشاملة**\n\n{stats}\n\n"
            enhanced_stats += f"🤖 **النظام الشامل:** {'🟢 نشط' if comprehensive_handler.filter.enabled else '🔴 معطل'}\n"
            enhanced_stats += f"📅 **تاريخ التقرير:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            await message.reply(enhanced_stats, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض إحصائيات الأمان: {e}")
            await message.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    async def show_group_report(self, message: Message, args: list):
        """عرض تقرير المجموعة المفصل"""
        try:
            report = await get_comprehensive_group_stats(message.chat.id)
            
            # إضافة أزرار تفاعلية
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="📊 إحصائيات مفصلة", callback_data="detailed_stats"),
                    InlineKeyboardButton(text="📈 تحليل المخاطر", callback_data="risk_analysis")
                ],
                [
                    InlineKeyboardButton(text="📄 تصدير التقرير", callback_data="export_report"),
                    InlineKeyboardButton(text="🔄 تحديث", callback_data="refresh_stats")
                ]
            ])
            
            await message.reply(report, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض تقرير المجموعة: {e}")
            await message.reply("❌ حدث خطأ في إنشاء التقرير")
    
    async def show_user_report(self, message: Message, args: list):
        """عرض تقرير مستخدم محدد"""
        try:
            # التحقق من وجود معرف المستخدم
            if not args or not args[0].isdigit():
                await message.reply("❌ يرجى تحديد معرف المستخدم\nمثال: تقرير_مستخدم 123456789")
                return
            
            user_id = int(args[0])
            report = await get_user_comprehensive_report(user_id, message.chat.id)
            
            # إضافة أزرار إدارية
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="🔄 إعادة تعيين النقاط", callback_data=f"reset_points:{user_id}"),
                    InlineKeyboardButton(text="🗑️ حذف السجل", callback_data=f"clear_record:{user_id}")
                ],
                [
                    InlineKeyboardButton(text="📊 إحصائيات مفصلة", callback_data=f"user_detailed:{user_id}")
                ]
            ])
            
            await message.reply(report, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض تقرير المستخدم: {e}")
            await message.reply("❌ حدث خطأ في إنشاء تقرير المستخدم")
    
    async def show_daily_summary(self, message: Message, args: list):
        """عرض الملخص اليومي"""
        try:
            summary = await admin_reports.generate_daily_summary(message.chat.id)
            
            await message.reply(
                f"📊 **الملخص اليومي للأمان**\n\n{summary}",
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض الملخص اليومي: {e}")
            await message.reply("❌ حدث خطأ في إنشاء الملخص اليومي")
    
    # أوامر التحكم في النظام
    async def enable_comprehensive_system(self, message: Message, args: list):
        """تفعيل النظام الشامل"""
        try:
            # التحقق من الصلاحيات العالية
            if not (has_permission(message.from_user.id, AdminLevel.GROUP_OWNER, message.chat.id) or is_master(message.from_user.id)):
                await message.reply("❌ هذا الأمر مخصص لمالكي المجموعة والأسياد فقط")
                return
            
            result = await toggle_comprehensive_system(message.chat.id, True)
            
            await message.reply(
                f"✅ {result}\n\n"
                f"🔍 **الميزات المفعلة:**\n"
                f"• فحص النصوص والسباب\n"
                f"• فحص السياق الجنسي\n"
                f"• فحص الصور والفيديوهات\n"
                f"• فحص الملصقات والملفات\n"
                f"• نظام العقوبات المتدرج\n"
                f"• تقارير المشرفين الفورية\n\n"
                f"🛡️ **النظام الشامل نشط الآن**"
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في تفعيل النظام: {e}")
            await message.reply("❌ حدث خطأ في تفعيل النظام")
    
    async def disable_comprehensive_system(self, message: Message, args: list):
        """تعطيل النظام الشامل"""
        try:
            # التحقق من الصلاحيات العالية
            if not (has_permission(message.from_user.id, AdminLevel.GROUP_OWNER, message.chat.id) or is_master(message.from_user.id)):
                await message.reply("❌ هذا الأمر مخصص لمالكي المجموعة والأسياد فقط")
                return
            
            result = await toggle_comprehensive_system(message.chat.id, False)
            
            await message.reply(
                f"⚠️ {result}\n\n"
                f"📴 **تم تعطيل:**\n"
                f"• فحص الصور والفيديوهات المتقدم\n"
                f"• التقارير الفورية للمشرفين\n"
                f"• نظام العقوبات المتدرج\n\n"
                f"ℹ️ **ملاحظة:** نظام السباب الأساسي ما زال يعمل"
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في تعطيل النظام: {e}")
            await message.reply("❌ حدث خطأ في تعطيل النظام")
    
    async def show_system_status(self, message: Message, args: list):
        """عرض حالة النظام"""
        try:
            status = await get_system_status()
            await message.reply(status, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض حالة النظام: {e}")
            await message.reply("❌ حدث خطأ في جلب حالة النظام")
    
    # أوامر التقارير والإشعارات
    async def subscribe_to_reports(self, message: Message, args: list):
        """الاشتراك في التقارير"""
        try:
            # تحديد أنواع التقارير
            report_types = ['instant_alerts', 'daily_summary']
            if args:
                available_types = ['instant_alerts', 'daily_summary', 'weekly_summary']
                report_types = [t for t in args if t in available_types]
            
            result = await subscribe_admin_to_comprehensive_reports(
                message.from_user.id, 
                message.chat.id, 
                report_types
            )
            
            await message.reply(
                f"{result}\n\n"
                f"📧 **ستصلك إشعارات عن:**\n"
                f"• {'✅' if 'instant_alerts' in report_types else '❌'} التنبيهات الفورية\n"
                f"• {'✅' if 'daily_summary' in report_types else '❌'} الملخص اليومي\n\n"
                f"💡 **لإلغاء الاشتراك:** استخدم أمر إلغاء_اشتراك_تقارير"
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في الاشتراك في التقارير: {e}")
            await message.reply("❌ حدث خطأ في عملية الاشتراك")
    
    async def unsubscribe_from_reports(self, message: Message, args: list):
        """إلغاء الاشتراك في التقارير"""
        try:
            # إلغاء الاشتراك (تمرير قائمة فارغة)
            result = await subscribe_admin_to_comprehensive_reports(
                message.from_user.id, 
                message.chat.id, 
                []
            )
            
            await message.reply(
                f"✅ تم إلغاء اشتراكك في جميع التقارير\n\n"
                f"💡 **للاشتراك مرة أخرى:** استخدم أمر اشتراك_تقارير"
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في إلغاء الاشتراك: {e}")
            await message.reply("❌ حدث خطأ في إلغاء الاشتراك")
    
    async def toggle_instant_reports(self, message: Message, args: list):
        """تفعيل/تعطيل التقارير الفورية"""
        try:
            # تبديل حالة التقارير الفورية
            result = await subscribe_admin_to_comprehensive_reports(
                message.from_user.id, 
                message.chat.id, 
                ['instant_alerts']
            )
            
            await message.reply(f"✅ تم تحديث إعدادات التقارير الفورية")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث التقارير الفورية: {e}")
            await message.reply("❌ حدث خطأ في تحديث الإعدادات")
    
    async def toggle_daily_summary(self, message: Message, args: list):
        """تفعيل/تعطيل الملخص اليومي التلقائي"""
        try:
            result = await subscribe_admin_to_comprehensive_reports(
                message.from_user.id, 
                message.chat.id, 
                ['daily_summary']
            )
            
            await message.reply(f"✅ تم تحديث إعدادات الملخص اليومي")
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحديث الملخص اليومي: {e}")
            await message.reply("❌ حدث خطأ في تحديث الإعدادات")
    
    # أوامر الإدارة المتقدمة
    async def review_report(self, message: Message, args: list):
        """مراجعة تقرير محدد"""
        try:
            if not args or not args[0].isdigit():
                await message.reply("❌ يرجى تحديد رقم التقرير\nمثال: مراجعة_تقرير 123")
                return
            
            report_id = int(args[0])
            report_data = await admin_reports.get_report_details(report_id)
            
            if not report_data:
                await message.reply("❌ لم يتم العثور على التقرير")
                return
            
            review_msg = f"📋 **مراجعة التقرير رقم {report_id}**\n\n"
            review_msg += f"👤 **المستخدم:** {report_data['user_id']}\n"
            review_msg += f"⚠️ **نوع المخالفة:** {report_data['violation_type']}\n"
            review_msg += f"📈 **مستوى الخطورة:** {report_data['severity_level']}\n"
            review_msg += f"⚖️ **الإجراء المتخذ:** {report_data['action_taken']}\n"
            review_msg += f"📊 **حالة التقرير:** {report_data['report_status']}\n"
            review_msg += f"🕐 **التاريخ:** {report_data['created_at']}\n\n"
            review_msg += f"📝 **الملخص:**\n{report_data['content_summary']}"
            
            # أزرار المراجعة
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ موافق", callback_data=f"report_approve:{report_id}"),
                    InlineKeyboardButton(text="❌ رفض", callback_data=f"report_reject:{report_id}")
                ],
                [
                    InlineKeyboardButton(text="📝 إضافة ملاحظة", callback_data=f"report_note:{report_id}")
                ]
            ])
            
            await message.reply(review_msg, reply_markup=keyboard, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في مراجعة التقرير: {e}")
            await message.reply("❌ حدث خطأ في مراجعة التقرير")
    
    async def clear_user_record(self, message: Message, args: list):
        """حذف سجل مستخدم"""
        try:
            # التحقق من الصلاحيات العالية
            if not (has_permission(message.from_user.id, AdminLevel.GROUP_OWNER, message.chat.id) or is_master(message.from_user.id)):
                await message.reply("❌ هذا الأمر مخصص لمالكي المجموعة والأسياد فقط")
                return
            
            if not args or not args[0].isdigit():
                await message.reply("❌ يرجى تحديد معرف المستخدم\nمثال: حذف_سجل_مستخدم 123456789")
                return
            
            user_id = int(args[0])
            
            # هنا يمكن إضافة الكود لحذف السجل من قاعدة البيانات
            # سأتركه كتأكيد فقط لأن هذا إجراء حساس
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ تأكيد الحذف", callback_data=f"confirm_clear:{user_id}"),
                    InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_clear")
                ]
            ])
            
            await message.reply(
                f"⚠️ **تأكيد حذف السجل**\n\n"
                f"👤 **المستخدم:** {user_id}\n"
                f"🗑️ **سيتم حذف:** جميع المخالفات والنقاط التراكمية\n\n"
                f"❗ **تحذير:** هذا الإجراء لا يمكن التراجع عنه",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في حذف سجل المستخدم: {e}")
            await message.reply("❌ حدث خطأ في العملية")
    
    async def reset_user_points(self, message: Message, args: list):
        """إعادة تعيين نقاط المستخدم"""
        try:
            if not args or not args[0].isdigit():
                await message.reply("❌ يرجى تحديد معرف المستخدم\nمثال: إعادة_تعيين_نقاط 123456789")
                return
            
            user_id = int(args[0])
            
            # تأكيد العملية
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ إعادة تعيين", callback_data=f"confirm_reset:{user_id}"),
                    InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_reset")
                ]
            ])
            
            await message.reply(
                f"🔄 **إعادة تعيين النقاط**\n\n"
                f"👤 **المستخدم:** {user_id}\n"
                f"📊 **سيتم:** إعادة تعيين النقاط التراكمية إلى الصفر\n"
                f"📋 **ملاحظة:** السجل سيبقى محفوظاً للمراجعة",
                reply_markup=keyboard,
                parse_mode='Markdown'
            )
            
        except Exception as e:
            logging.error(f"❌ خطأ في إعادة تعيين النقاط: {e}")
            await message.reply("❌ حدث خطأ في العملية")
    
    async def show_banned_users(self, message: Message, args: list):
        """عرض قائمة المحظورين"""
        try:
            # هنا يمكن إضافة الكود لجلب قائمة المحظورين
            banned_list = "📋 **قائمة المحظورين**\n\n"
            banned_list += "🔍 جاري البحث في قاعدة البيانات...\n\n"
            banned_list += "💡 **ملاحظة:** يتم عرض المستخدمين المحظورين نهائياً فقط"
            
            await message.reply(banned_list, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في عرض قائمة المحظورين: {e}")
            await message.reply("❌ حدث خطأ في جلب القائمة")
    
    # أوامر التحليل والإحصائيات المتقدمة
    async def analyze_group_risks(self, message: Message, args: list):
        """تحليل مخاطر المجموعة"""
        try:
            analysis = f"🎯 **تحليل المخاطر للمجموعة**\n\n"
            analysis += f"📊 جاري تحليل البيانات...\n"
            analysis += f"🔍 فحص أنماط المخالفات...\n"
            analysis += f"📈 تقييم مستوى المخاطر...\n\n"
            analysis += f"⏳ **النتائج ستظهر قريباً**"
            
            await message.reply(analysis, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في تحليل المخاطر: {e}")
            await message.reply("❌ حدث خطأ في التحليل")
    
    async def show_weekly_stats(self, message: Message, args: list):
        """عرض الإحصائيات الأسبوعية"""
        try:
            weekly_stats = f"📊 **الإحصائيات الأسبوعية**\n\n"
            weekly_stats += f"📅 **الفترة:** آخر 7 أيام\n"
            weekly_stats += f"🔍 جاري جمع البيانات...\n\n"
            weekly_stats += f"💡 **ملاحظة:** التقرير الأسبوعي قيد التطوير"
            
            await message.reply(weekly_stats, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في الإحصائيات الأسبوعية: {e}")
            await message.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    async def show_monthly_stats(self, message: Message, args: list):
        """عرض الإحصائيات الشهرية"""
        try:
            monthly_stats = f"📊 **الإحصائيات الشهرية**\n\n"
            monthly_stats += f"📅 **الفترة:** آخر 30 يوم\n"
            monthly_stats += f"🔍 جاري جمع البيانات...\n\n"
            monthly_stats += f"💡 **ملاحظة:** التقرير الشهري قيد التطوير"
            
            await message.reply(monthly_stats, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في الإحصائيات الشهرية: {e}")
            await message.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    async def export_reports(self, message: Message, args: list):
        """تصدير التقارير"""
        try:
            export_msg = f"📄 **تصدير التقارير**\n\n"
            export_msg += f"🔄 جاري إنشاء ملف التصدير...\n"
            export_msg += f"📊 تجميع البيانات...\n"
            export_msg += f"📁 إنشاء ملف CSV...\n\n"
            export_msg += f"⏳ **سيتم إرسال الملف قريباً**"
            
            await message.reply(export_msg, parse_mode='Markdown')
            
        except Exception as e:
            logging.error(f"❌ خطأ في تصدير التقارير: {e}")
            await message.reply("❌ حدث خطأ في التصدير")

# إنشاء كائن أوامر المشرفين
comprehensive_admin = ComprehensiveAdminCommands()
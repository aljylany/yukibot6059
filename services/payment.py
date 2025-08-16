"""
خدمة الدفع
Payment Service
"""

import logging
import json
from datetime import datetime
from aiogram.types import Message, LabeledPrice, PreCheckoutQuery
from aiogram.types.input_invoice_message_content import InputInvoiceMessageContent

from config.settings import PAYMENT_SETTINGS
from database.operations import get_user, update_user_balance, add_transaction


class PaymentService:
    """خدمة معالجة المدفوعات"""
    
    def __init__(self):
        self.provider_token = PAYMENT_SETTINGS.get('provider_token', '')
        self.currency = PAYMENT_SETTINGS.get('currency', 'USD')
    
    async def create_invoice(self, user_id: int, title: str, description: str, 
                           amount: int, payload: str = None):
        """إنشاء فاتورة دفع"""
        try:
            if not self.provider_token:
                logging.error("رمز مقدم الدفع غير متوفر")
                return None
            
            # إنشاء الفاتورة
            prices = [LabeledPrice(label=title, amount=amount * 100)]  # السعر بالسنت
            
            invoice_payload = payload or f"user_{user_id}_{datetime.now().timestamp()}"
            
            return {
                "title": title,
                "description": description,
                "payload": invoice_payload,
                "provider_token": self.provider_token,
                "currency": self.currency,
                "prices": prices,
                "is_flexible": False
            }
            
        except Exception as e:
            logging.error(f"خطأ في إنشاء الفاتورة: {e}")
            return None
    
    async def send_invoice(self, bot, chat_id: int, invoice_data: dict):
        """إرسال فاتورة للمستخدم"""
        try:
            return await bot.send_invoice(
                chat_id=chat_id,
                **invoice_data
            )
        except Exception as e:
            logging.error(f"خطأ في إرسال الفاتورة: {e}")
            return None
    
    async def handle_pre_checkout(self, pre_checkout_query: PreCheckoutQuery):
        """معالجة استعلام ما قبل الدفع"""
        try:
            # التحقق من صحة الطلب
            payload = pre_checkout_query.invoice_payload
            user_id = pre_checkout_query.from_user.id
            amount = pre_checkout_query.total_amount // 100  # تحويل من السنت
            
            # يمكن إضافة التحقق من البيانات هنا
            
            await pre_checkout_query.answer(ok=True)
            logging.info(f"تم قبول طلب الدفع للمستخدم {user_id} بمبلغ {amount}")
            
        except Exception as e:
            logging.error(f"خطأ في معالجة ما قبل الدفع: {e}")
            await pre_checkout_query.answer(
                ok=False, 
                error_message="حدث خطأ في معالجة الدفع"
            )
    
    async def handle_successful_payment(self, message: Message):
        """معالجة الدفع الناجح"""
        try:
            payment = message.successful_payment
            user_id = message.from_user.id
            amount = payment.total_amount // 100
            payload = payment.invoice_payload
            
            # تحليل معرف العملية
            operation_type = self.parse_payment_payload(payload)
            
            if operation_type:
                await self.process_payment_operation(user_id, amount, operation_type)
            
            # إضافة معاملة مالية
            await add_transaction(
                from_user_id=0,  # النظام
                to_user_id=user_id,
                transaction_type="payment_purchase",
                amount=amount,
                description=f"شراء عبر الدفع الإلكتروني - {operation_type}"
            )
            
            await message.reply(
                f"✅ **تم الدفع بنجاح!**\n\n"
                f"💰 المبلغ: {amount}$\n"
                f"🆔 معرف العملية: {payment.telegram_payment_charge_id}\n"
                f"📅 التاريخ: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                f"شكراً لك على الشراء!"
            )
            
            logging.info(f"تم استلام دفعة ناجحة: {user_id} - {amount}$ - {operation_type}")
            
        except Exception as e:
            logging.error(f"خطأ في معالجة الدفع الناجح: {e}")
            await message.reply("❌ حدث خطأ في معالجة دفعتك، يرجى التواصل مع الدعم")
    
    def parse_payment_payload(self, payload: str):
        """تحليل معرف العملية"""
        try:
            if payload.startswith("coins_"):
                return f"شراء عملات - {payload.split('_')[1]}"
            elif payload.startswith("premium_"):
                return f"اشتراك مميز - {payload.split('_')[1]}"
            elif payload.startswith("package_"):
                return f"حزمة مميزة - {payload.split('_')[1]}"
            else:
                return "عملية شراء"
        except:
            return "عملية شراء"
    
    async def process_payment_operation(self, user_id: int, amount: int, operation_type: str):
        """معالجة العملية بعد الدفع الناجح"""
        try:
            if "عملات" in operation_type:
                # إضافة عملات للمستخدم
                coins_amount = amount * 100  # 100 عملة لكل دولار
                user = await get_user(user_id)
                if user:
                    new_balance = user['balance'] + coins_amount
                    await update_user_balance(user_id, new_balance)
                    
            elif "مميز" in operation_type:
                # تفعيل الاشتراك المميز
                await self.activate_premium_subscription(user_id)
                
            elif "حزمة" in operation_type:
                # تفعيل الحزمة المميزة
                await self.activate_premium_package(user_id, operation_type)
                
        except Exception as e:
            logging.error(f"خطأ في معالجة العملية بعد الدفع: {e}")
    
    async def activate_premium_subscription(self, user_id: int):
        """تفعيل الاشتراك المميز"""
        try:
            # يمكن إضافة منطق تفعيل الاشتراك هنا
            logging.info(f"تم تفعيل الاشتراك المميز للمستخدم {user_id}")
        except Exception as e:
            logging.error(f"خطأ في تفعيل الاشتراك المميز: {e}")
    
    async def activate_premium_package(self, user_id: int, package_type: str):
        """تفعيل الحزمة المميزة"""
        try:
            # يمكن إضافة منطق تفعيل الحزم هنا
            logging.info(f"تم تفعيل الحزمة المميزة للمستخدم {user_id}: {package_type}")
        except Exception as e:
            logging.error(f"خطأ في تفعيل الحزمة المميزة: {e}")


# الباقات المتاحة للشراء
AVAILABLE_PACKAGES = {
    "coins_1000": {
        "title": "1000 عملة ذهبية",
        "description": "احصل على 1000 عملة ذهبية لتطوير حسابك",
        "price": 10,  # 10 دولار
        "coins": 1000
    },
    "coins_5000": {
        "title": "5000 عملة ذهبية", 
        "description": "احصل على 5000 عملة ذهبية مع خصم 20%",
        "price": 40,  # بدلاً من 50
        "coins": 5000
    },
    "coins_10000": {
        "title": "10000 عملة ذهبية",
        "description": "احصل على 10000 عملة ذهبية مع خصم 30%",
        "price": 70,  # بدلاً من 100
        "coins": 10000
    },
    "premium_monthly": {
        "title": "اشتراك مميز شهري",
        "description": "اشتراك مميز لمدة شهر مع مزايا إضافية",
        "price": 15,
        "duration_days": 30
    },
    "premium_yearly": {
        "title": "اشتراك مميز سنوي",
        "description": "اشتراك مميز لمدة سنة مع خصم 50%",
        "price": 90,  # بدلاً من 180
        "duration_days": 365
    },
    "starter_package": {
        "title": "حزمة البداية",
        "description": "1000 عملة + قلعة مطورة + اشتراك مميز لأسبوع",
        "price": 20,
        "coins": 1000,
        "premium_days": 7,
        "castle_boost": True
    },
    "vip_package": {
        "title": "حزمة VIP",
        "description": "5000 عملة + اشتراك مميز شهري + مزايا حصرية",
        "price": 50,
        "coins": 5000,
        "premium_days": 30,
        "vip_features": True
    }
}


async def show_purchase_menu(message: Message):
    """عرض قائمة الشراء"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard_buttons = []
        
        # إضافة باقات العملات
        keyboard_buttons.append([InlineKeyboardButton(
            text="💰 باقات العملات",
            callback_data="purchase_category_coins"
        )])
        
        # إضافة الاشتراكات المميزة
        keyboard_buttons.append([InlineKeyboardButton(
            text="⭐ الاشتراكات المميزة", 
            callback_data="purchase_category_premium"
        )])
        
        # إضافة الحزم الخاصة
        keyboard_buttons.append([InlineKeyboardButton(
            text="🎁 الحزم الخاصة",
            callback_data="purchase_category_packages"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        menu_text = f"""
🛒 **متجر البوت**

مرحباً بك في متجر البوت! يمكنك شراء:

💰 **العملات الذهبية:**
استخدمها لتطوير حسابك وشراء العقارات والاستثمارات

⭐ **الاشتراكات المميزة:**
احصل على مزايا حصرية ومكافآت إضافية

🎁 **الحزم الخاصة:**
عروض مجمعة بأسعار مخفضة

💳 ندعم جميع طرق الدفع الآمنة
        """
        
        await message.reply(menu_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الشراء: {e}")
        await message.reply("❌ حدث خطأ في عرض متجر البوت")


async def show_category_packages(message: Message, category: str):
    """عرض باقات فئة معينة"""
    try:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        
        keyboard_buttons = []
        category_text = ""
        
        if category == "coins":
            category_text = "💰 **باقات العملات الذهبية:**\n\n"
            packages = ["coins_1000", "coins_5000", "coins_10000"]
        elif category == "premium":
            category_text = "⭐ **الاشتراكات المميزة:**\n\n"
            packages = ["premium_monthly", "premium_yearly"]
        elif category == "packages":
            category_text = "🎁 **الحزم الخاصة:**\n\n"
            packages = ["starter_package", "vip_package"]
        else:
            await message.reply("❌ فئة غير صحيحة")
            return
        
        for package_id in packages:
            if package_id in AVAILABLE_PACKAGES:
                package = AVAILABLE_PACKAGES[package_id]
                
                category_text += f"🔹 **{package['title']}**\n"
                category_text += f"   📝 {package['description']}\n"
                category_text += f"   💵 السعر: {package['price']}$\n\n"
                
                keyboard_buttons.append([InlineKeyboardButton(
                    text=f"{package['title']} - {package['price']}$",
                    callback_data=f"purchase_buy_{package_id}"
                )])
        
        keyboard_buttons.append([InlineKeyboardButton(
            text="🔙 العودة للقائمة الرئيسية",
            callback_data="purchase_menu"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        await message.reply(category_text, reply_markup=keyboard)
        
    except Exception as e:
        logging.error(f"خطأ في عرض باقات الفئة: {e}")
        await message.reply("❌ حدث خطأ في عرض الباقات")


async def initiate_purchase(message: Message, package_id: str):
    """بدء عملية الشراء"""
    try:
        if package_id not in AVAILABLE_PACKAGES:
            await message.reply("❌ باقة غير صحيحة")
            return
        
        package = AVAILABLE_PACKAGES[package_id]
        payment_service = PaymentService()
        
        # إنشاء الفاتورة
        invoice_data = await payment_service.create_invoice(
            user_id=message.from_user.id,
            title=package['title'],
            description=package['description'],
            amount=package['price'],
            payload=package_id
        )
        
        if not invoice_data:
            await message.reply(
                "❌ عذراً، خدمة الدفع غير متوفرة حالياً.\n"
                "يرجى المحاولة لاحقاً أو التواصل مع الدعم."
            )
            return
        
        # إرسال الفاتورة
        sent_invoice = await payment_service.send_invoice(
            bot=message.bot,
            chat_id=message.chat.id,
            invoice_data=invoice_data
        )
        
        if sent_invoice:
            await message.reply(
                f"💳 **تم إنشاء فاتورة الدفع**\n\n"
                f"📦 المنتج: {package['title']}\n"
                f"💵 السعر: {package['price']}$\n\n"
                f"اضغط على الزر أدناه لإتمام عملية الدفع الآمنة"
            )
        else:
            await message.reply("❌ فشل في إنشاء فاتورة الدفع")
        
    except Exception as e:
        logging.error(f"خطأ في بدء عملية الشراء: {e}")
        await message.reply("❌ حدث خطأ في عملية الشراء")


# إنشاء كائن الخدمة العام
payment_service = PaymentService()

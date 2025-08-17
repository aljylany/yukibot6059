"""
تسجيل يدوي للمستخدمين في النظام المصرفي
Manual User Registration System
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from database.operations import get_user, create_user, update_user_activity
from modules.banks import start_bank_selection, BANK_TYPES
from utils.states import BanksStates
from utils.helpers import format_number

async def handle_bank_account_creation(message: Message, state: FSMContext):
    """معالج إنشاء الحساب البنكي"""
    try:
        if not message.from_user:
            return
            
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or "مستخدم"
        
        # التحقق من وجود حساب مسبقاً
        existing_user = await get_user(user_id)
        if existing_user:
            await message.reply(
                f"✅ **لديك حساب بنكي بالفعل!**\n\n"
                f"🏦 البنك: {existing_user.get('bank_name', 'غير محدد')}\n"
                f"💰 الرصيد: {format_number(existing_user['balance'])}$\n"
                f"🏛️ رصيد البنك: {format_number(existing_user['bank_balance'])}$\n\n"
                f"💡 يمكنك البدء في اللعب مباشرة!"
            )
            return
        
        # بدء عملية اختيار البنك
        await start_bank_selection(message)
        await state.set_state(BanksStates.selecting_bank)
        
    except Exception as e:
        logging.error(f"خطأ في handle_bank_account_creation: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء الحساب البنكي")

async def handle_bank_selection(message: Message, state: FSMContext):
    """معالج اختيار البنك"""
    try:
        if not message.text or not message.from_user:
            return
            
        text = message.text.strip()
        user_id = message.from_user.id
        username = message.from_user.username or ""
        first_name = message.from_user.first_name or "مستخدم"
        
        # فحص اختيار البنك
        selected_bank = None
        for key, bank in BANK_TYPES.items():
            if text == key or text == bank['name']:
                selected_bank = key
                break
        
        if not selected_bank:
            await message.reply(
                "❌ **اختيار غير صحيح!**\n\n"
                "💡 اختر أحد البنوك التالية:\n"
                "• الأهلي\n• الراجحي\n• سامبا\n• الرياض\n\n"
                "اكتب اسم البنك كما هو موضح أعلاه"
            )
            return
        
        bank_info = BANK_TYPES[selected_bank]
        
        # إنشاء المستخدم مع البنك المختار
        success = await create_user_with_bank(user_id, username, first_name, selected_bank)
        
        if success:
            await message.reply(
                f"🎉 **تم إنشاء حسابك البنكي بنجاح!**\n\n"
                f"{bank_info['emoji']} **{bank_info['name']}**\n"
                f"💰 مكافأة التسجيل: {format_number(bank_info['initial_bonus'])}$\n"
                f"💼 راتبك اليومي: {bank_info['daily_salary'][0]}-{bank_info['daily_salary'][1]}$\n"
                f"📈 معدل الفائدة: {bank_info['interest_rate']*100:.1f}%\n\n"
                f"✅ **أصبح بإمكانك الآن:**\n"
                f"• جمع راتبك اليومي بكتابة 'راتب'\n"
                f"• عرض رصيدك بكتابة 'رصيد'\n"
                f"• تحويل الأموال والاستثمار\n"
                f"• اللعب مع الأصدقاء\n\n"
                f"🎮 **مرحباً بك في عالم الألعاب الاقتصادية!**"
            )
            
            # إلغاء الحالة
            await state.clear()
        else:
            await message.reply("❌ حدث خطأ أثناء إنشاء الحساب، حاول مرة أخرى")
            
    except Exception as e:
        logging.error(f"خطأ في handle_bank_selection: {e}")
        await message.reply("❌ حدث خطأ أثناء اختيار البنك")

async def create_user_with_bank(user_id: int, username: str, first_name: str, bank_key: str) -> bool:
    """إنشاء مستخدم مع بنك محدد"""
    try:
        import aiosqlite
        from config.database import DATABASE_URL
        from datetime import datetime
        
        bank_info = BANK_TYPES[bank_key]
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            await db.execute(
                """
                INSERT INTO users (
                    user_id, username, first_name, balance, bank_balance, 
                    bank_name, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id, username, first_name, 
                    bank_info['initial_bonus'], 0, bank_info['name'],
                    datetime.now().isoformat(), datetime.now().isoformat()
                )
            )
            await db.commit()
            
            logging.info(f"تم إنشاء مستخدم جديد: {user_id} - {username} - البنك: {bank_info['name']}")
            return True
            
    except Exception as e:
        logging.error(f"خطأ في create_user_with_bank: {e}")
        return False
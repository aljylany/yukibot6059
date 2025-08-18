"""
إدارة الردود الخاصة - للمديرين فقط
Special Responses Admin Management
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from modules.special_responses import (
    add_special_user, remove_special_user, update_special_responses,
    get_all_special_users, is_special_user, add_trigger_keyword,
    remove_trigger_keyword, SPECIAL_RESPONSES, TRIGGER_KEYWORDS
)
from utils.decorators import admin_required
from config.settings import ADMINS


@admin_required
async def add_special_user_command(message: Message):
    """إضافة مستخدم خاص جديد"""
    try:
        # التحقق من صيغة الأمر
        if not message.text:
            return
        parts = message.text.split('\n', 1)
        if len(parts) < 2:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n\n"
                "إضافة مستخدم خاص [معرف المستخدم]\n"
                "[قائمة الردود، كل رد في سطر منفصل]\n\n"
                "مثال:\n"
                "إضافة مستخدم خاص 123456789\n"
                "مرحباً يا صديقي\n"
                "أهلاً وسهلاً بك\n"
                "كيف حالك اليوم؟"
            )
            return
        
        # استخراج معرف المستخدم
        first_line = parts[0].split()
        if len(first_line) < 4:
            await message.reply("❌ يرجى كتابة معرف المستخدم بعد 'إضافة مستخدم خاص'")
            return
        
        try:
            user_id = int(first_line[3])
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً صحيحاً")
            return
        
        # استخراج الردود
        responses = [response.strip() for response in parts[1].split('\n') if response.strip()]
        if not responses:
            await message.reply("❌ يجب إضافة رد واحد على الأقل")
            return
        
        # إضافة المستخدم
        if add_special_user(user_id, responses):
            await message.reply(
                f"✅ تم إضافة المستخدم {user_id} للقائمة الخاصة\n"
                f"📝 عدد الردود: {len(responses)}\n\n"
                f"الردود المضافة:\n" + "\n".join([f"• {r}" for r in responses[:3]]) +
                (f"\n... و {len(responses)-3} ردود أخرى" if len(responses) > 3 else "")
            )
        else:
            await message.reply("❌ فشل في إضافة المستخدم")
            
    except Exception as e:
        logging.error(f"خطأ في add_special_user_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إضافة المستخدم")


@admin_required
async def remove_special_user_command(message: Message):
    """إزالة مستخدم من القائمة الخاصة"""
    try:
        if not message.text:
            return
        parts = message.text.split()
        if len(parts) < 4:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n"
                "إزالة مستخدم خاص [معرف المستخدم]\n\n"
                "مثال: إزالة مستخدم خاص 123456789"
            )
            return
        
        try:
            user_id = int(parts[3])
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً صحيحاً")
            return
        
        if remove_special_user(user_id):
            await message.reply(f"✅ تم إزالة المستخدم {user_id} من القائمة الخاصة")
        else:
            await message.reply(f"❌ المستخدم {user_id} غير موجود في القائمة الخاصة")
            
    except Exception as e:
        logging.error(f"خطأ في remove_special_user_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إزالة المستخدم")


@admin_required
async def list_special_users_command(message: Message):
    """عرض قائمة المستخدمين الخاصين"""
    try:
        special_users = get_all_special_users()
        
        if not special_users:
            await message.reply("📝 لا يوجد مستخدمين في القائمة الخاصة حالياً")
            return
        
        response = "👥 **قائمة المستخدمين الخاصين:**\n\n"
        
        for user_id, responses in special_users.items():
            response += f"🆔 **المستخدم:** `{user_id}`\n"
            response += f"📝 **عدد الردود:** {len(responses)}\n"
            response += f"💬 **مثال على الردود:**\n"
            response += "\n".join([f"  • {r}" for r in responses[:2]])
            if len(responses) > 2:
                response += f"\n  ... و {len(responses)-2} ردود أخرى"
            response += "\n" + "─"*30 + "\n"
        
        await message.reply(response)
        
    except Exception as e:
        logging.error(f"خطأ في list_special_users_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض القائمة")


@admin_required
async def update_special_responses_command(message: Message):
    """تحديث ردود مستخدم خاص"""
    try:
        if not message.text:
            return
        parts = message.text.split('\n', 1)
        if len(parts) < 2:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n\n"
                "تحديث ردود خاصة [معرف المستخدم]\n"
                "[قائمة الردود الجديدة، كل رد في سطر منفصل]\n\n"
                "مثال:\n"
                "تحديث ردود خاصة 123456789\n"
                "رد جديد 1\n"
                "رد جديد 2\n"
                "رد جديد 3"
            )
            return
        
        first_line = parts[0].split()
        if len(first_line) < 4:
            await message.reply("❌ يرجى كتابة معرف المستخدم بعد 'تحديث ردود خاصة'")
            return
        
        try:
            user_id = int(first_line[3])
        except ValueError:
            await message.reply("❌ معرف المستخدم يجب أن يكون رقماً صحيحاً")
            return
        
        # التحقق من وجود المستخدم
        if not is_special_user(user_id):
            await message.reply(f"❌ المستخدم {user_id} غير موجود في القائمة الخاصة")
            return
        
        # استخراج الردود الجديدة
        new_responses = [response.strip() for response in parts[1].split('\n') if response.strip()]
        if not new_responses:
            await message.reply("❌ يجب إضافة رد واحد على الأقل")
            return
        
        # تحديث الردود
        if update_special_responses(user_id, new_responses):
            await message.reply(
                f"✅ تم تحديث ردود المستخدم {user_id}\n"
                f"📝 عدد الردود الجديدة: {len(new_responses)}\n\n"
                f"الردود الجديدة:\n" + "\n".join([f"• {r}" for r in new_responses[:3]]) +
                (f"\n... و {len(new_responses)-3} ردود أخرى" if len(new_responses) > 3 else "")
            )
        else:
            await message.reply("❌ فشل في تحديث الردود")
            
    except Exception as e:
        logging.error(f"خطأ في update_special_responses_command: {e}")
        await message.reply("❌ حدث خطأ أثناء تحديث الردود")


@admin_required
async def add_trigger_keyword_command(message: Message):
    """إضافة كلمة مفتاحية جديدة"""
    try:
        if not message.text:
            return
        parts = message.text.split(maxsplit=3)
        if len(parts) < 4:
            await message.reply(
                "❌ استخدم الصيغة الصحيحة:\n"
                "إضافة كلمة مفتاحية [الكلمة]\n\n"
                "مثال: إضافة كلمة مفتاحية صباح النور"
            )
            return
        
        keyword = parts[3]
        
        if add_trigger_keyword(keyword):
            await message.reply(f"✅ تم إضافة الكلمة المفتاحية: '{keyword}'")
        else:
            await message.reply(f"❌ الكلمة '{keyword}' موجودة مسبقاً")
            
    except Exception as e:
        logging.error(f"خطأ في add_trigger_keyword_command: {e}")
        await message.reply("❌ حدث خطأ أثناء إضافة الكلمة المفتاحية")


@admin_required
async def list_trigger_keywords_command(message: Message):
    """عرض قائمة الكلمات المفتاحية"""
    try:
        keywords = TRIGGER_KEYWORDS.copy()
        
        if not keywords:
            await message.reply("📝 لا توجد كلمات مفتاحية محددة")
            return
        
        response = "🔑 **الكلمات المفتاحية للردود الخاصة:**\n\n"
        
        # تقسيم الكلمات إلى مجموعات
        for i in range(0, len(keywords), 6):
            group = keywords[i:i+6]
            response += "• " + " | ".join(group) + "\n"
        
        response += f"\n📊 **إجمالي الكلمات:** {len(keywords)}"
        
        await message.reply(response)
        
    except Exception as e:
        logging.error(f"خطأ في list_trigger_keywords_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الكلمات المفتاحية")


async def handle_special_admin_commands(message: Message) -> bool:
    """معالج أوامر إدارة الردود الخاصة"""
    if not message.text or not message.from_user:
        return False
    
    # التحقق من صلاحية المدير
    if message.from_user.id not in ADMINS:
        return False
    
    text = message.text.lower()
    
    if text.startswith('إضافة مستخدم خاص'):
        await add_special_user_command(message)
        return True
    elif text.startswith('إزالة مستخدم خاص'):
        await remove_special_user_command(message)
        return True
    elif text in ['قائمة المستخدمين الخاصين', 'المستخدمين الخاصين']:
        await list_special_users_command(message)
        return True
    elif text.startswith('تحديث ردود خاصة'):
        await update_special_responses_command(message)
        return True
    elif text.startswith('إضافة كلمة مفتاحية'):
        await add_trigger_keyword_command(message)
        return True
    elif text in ['الكلمات المفتاحية', 'قائمة الكلمات المفتاحية']:
        # التحقق من أن المستخدم مدير أساسي (ماستر)
        if message.from_user.id in [7155814194, 8278493069]:  # معرفات المديرين الأساسيين
            await list_trigger_keywords_command(message)
        else:
            await message.reply("❌ هذا الأمر متاح للمديرين الأساسيين فقط")
        return True
    
    return False
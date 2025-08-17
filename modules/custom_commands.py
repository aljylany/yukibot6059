"""
نظام الأوامر المخصصة
Custom Commands System
"""

import logging
import random
from typing import Dict, List, Optional, Any
from aiogram import Bot
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from config.hierarchy import has_permission, AdminLevel
from database.operations import execute_query
from utils.states import CustomCommandsStates


# قاموس الأوامر المخصصة المحملة في الذاكرة
CUSTOM_COMMANDS: Dict[int, Dict[str, List[str]]] = {}  # {group_id: {keyword: [responses]}}


async def load_custom_commands():
    """تحميل الأوامر المخصصة من قاعدة البيانات"""
    try:
        commands = await execute_query(
            "SELECT chat_id, keyword, responses FROM custom_commands",
            fetch_all=True
        )
        
        CUSTOM_COMMANDS.clear()
        
        if commands:
            for command in commands:
                chat_id = command[0] if isinstance(command, tuple) else command['chat_id']
                keyword = command[1] if isinstance(command, tuple) else command['keyword']
                responses = command[2] if isinstance(command, tuple) else command['responses']
                
                if chat_id not in CUSTOM_COMMANDS:
                    CUSTOM_COMMANDS[chat_id] = {}
                
                # تحويل النصوص المحفوظة إلى قائمة
                response_list = responses.split('|||') if responses else []
                CUSTOM_COMMANDS[chat_id][keyword] = response_list
        
        logging.info("تم تحميل الأوامر المخصصة من قاعدة البيانات بنجاح")
        
    except Exception as e:
        logging.error(f"خطأ في تحميل الأوامر المخصصة: {e}")


async def save_custom_command(chat_id: int, keyword: str, responses: List[str]) -> bool:
    """حفظ أمر مخصص في قاعدة البيانات"""
    try:
        # دمج الردود في نص واحد
        responses_text = '|||'.join(responses)
        
        await execute_query(
            "INSERT OR REPLACE INTO custom_commands (chat_id, keyword, responses, created_at) VALUES (?, ?, ?, datetime('now'))",
            (chat_id, keyword, responses_text)
        )
        
        # تحديث الذاكرة
        if chat_id not in CUSTOM_COMMANDS:
            CUSTOM_COMMANDS[chat_id] = {}
        
        CUSTOM_COMMANDS[chat_id][keyword] = responses
        
        logging.info(f"تم حفظ أمر مخصص: {keyword} في المجموعة {chat_id}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في حفظ الأمر المخصص: {e}")
        return False


async def delete_custom_command(chat_id: int, keyword: str) -> bool:
    """حذف أمر مخصص"""
    try:
        await execute_query(
            "DELETE FROM custom_commands WHERE chat_id = ? AND keyword = ?",
            (chat_id, keyword)
        )
        
        # تحديث الذاكرة
        if chat_id in CUSTOM_COMMANDS and keyword in CUSTOM_COMMANDS[chat_id]:
            del CUSTOM_COMMANDS[chat_id][keyword]
        
        logging.info(f"تم حذف أمر مخصص: {keyword} من المجموعة {chat_id}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في حذف الأمر المخصص: {e}")
        return False


async def get_custom_response(chat_id: int, message_text: str) -> Optional[str]:
    """البحث عن رد مخصص للرسالة"""
    try:
        if chat_id not in CUSTOM_COMMANDS:
            return None
        
        message_lower = message_text.lower().strip()
        
        # البحث عن كلمة مفتاحية مطابقة
        for keyword, responses in CUSTOM_COMMANDS[chat_id].items():
            # فحص التطابق الدقيق أو الاحتواء
            if (message_lower == keyword.lower() or 
                keyword.lower() in message_lower or
                any(word.strip() == keyword.lower() for word in message_lower.split())):
                
                if responses:
                    return random.choice(responses)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في البحث عن رد مخصص: {e}")
        return None


async def handle_add_command(message: Message, state: FSMContext):
    """معالج إضافة أمر جديد"""
    try:
        # التحقق من الصلاحيات
        if not message.from_user or message.chat.type == 'private':
            return False
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # فحص الصلاحيات - المشرفين وما فوق
        if not has_permission(user_id, AdminLevel.MODERATOR, chat_id):
            sarcastic_responses = [
                "😂 وانت مين عشان تضيف أوامر؟ أنا يوكي مش بوت عادي!",
                "🙄 صلاحياتك محدودة جداً... حاول تكون مشرف أولاً!",
                "😏 أوامر مخصصة؟ هذه للكبار فقط، عذراً!",
                "🤭 أعتقد أنك تخلط بيني وبين بوت آخر، أنا يوكي الذكي!",
                "😎 هذه ميزة VIP يا صديقي، ارجع لما تصير مشرف!"
            ]
            
            await message.reply(random.choice(sarcastic_responses))
            return False
        
        text = message.text
        
        if text.startswith('اضافة امر ') or text.startswith('إضافة أمر '):
            # استخراج الكلمة المفتاحية
            parts = text.split(' ', 2)
            if len(parts) < 3:
                await message.reply(
                    "❌ **طريقة الاستخدام:**\n\n"
                    "`اضافة امر [الكلمة المفتاحية] [الرد]`\n\n"
                    "**مثال:**\n"
                    "`اضافة امر مرحبا أهلاً وسهلاً بك في المجموعة!`"
                )
                return True
            
            keyword = parts[2].split()[0]  # أول كلمة بعد "اضافة امر"
            response = ' '.join(parts[2].split()[1:])  # باقي النص
            
            if not keyword or not response:
                await message.reply(
                    "❌ **يجب تحديد الكلمة المفتاحية والرد**\n\n"
                    "**مثال:**\n"
                    "`اضافة امر مرحبا أهلاً وسهلاً بك في المجموعة!`"
                )
                return True
            
            # حفظ الأمر
            if await save_custom_command(chat_id, keyword, [response]):
                await message.reply(
                    f"✅ **تم إضافة الأمر بنجاح!**\n\n"
                    f"🔑 **الكلمة المفتاحية:** `{keyword}`\n"
                    f"💬 **الرد:** {response}\n\n"
                    f"الآن عندما يكتب أي شخص `{keyword}` سيرد البوت بـ: {response}"
                )
            else:
                await message.reply("❌ فشل في إضافة الأمر، حاول مرة أخرى")
            
            return True
        
        elif text.strip() == 'اضافة امر' or text.strip() == 'إضافة أمر':
            # وضع المستخدم في حالة انتظار الكلمة المفتاحية
            await state.set_state(CustomCommandsStates.waiting_keyword)
            await message.reply(
                "🎯 **إضافة أمر جديد**\n\n"
                "1️⃣ اكتب الكلمة المفتاحية التي ستفعل الأمر\n\n"
                "**مثال:** `مرحبا` أو `قوانين` أو `معلومات`\n\n"
                "🚫 **ألغِ العملية:** `/cancel`"
            )
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج إضافة الأمر: {e}")
        return False


async def handle_delete_command(message: Message):
    """معالج حذف أمر"""
    try:
        # التحقق من الصلاحيات
        if not message.from_user or message.chat.type == 'private':
            return False
        
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        # فحص الصلاحيات - المشرفين وما فوق
        if not has_permission(user_id, AdminLevel.MODERATOR, chat_id):
            await message.reply("❌ هذا الأمر متاح للمشرفين وما فوق فقط")
            return False
        
        text = message.text
        
        if text.startswith('حذف امر ') or text.startswith('حذف أمر '):
            # استخراج الكلمة المفتاحية
            parts = text.split(' ', 2)
            if len(parts) < 3:
                await message.reply(
                    "❌ **طريقة الاستخدام:**\n\n"
                    "`حذف امر [الكلمة المفتاحية]`\n\n"
                    "**مثال:**\n"
                    "`حذف امر مرحبا`"
                )
                return True
            
            keyword = parts[2].strip()
            
            # التحقق من وجود الأمر
            if chat_id not in CUSTOM_COMMANDS or keyword not in CUSTOM_COMMANDS[chat_id]:
                await message.reply(f"❌ لا يوجد أمر بالكلمة المفتاحية: `{keyword}`")
                return True
            
            # حذف الأمر
            if await delete_custom_command(chat_id, keyword):
                await message.reply(
                    f"✅ **تم حذف الأمر بنجاح!**\n\n"
                    f"🗑 **الكلمة المحذوفة:** `{keyword}`"
                )
            else:
                await message.reply("❌ فشل في حذف الأمر، حاول مرة أخرى")
            
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج حذف الأمر: {e}")
        return False


async def handle_list_commands(message: Message):
    """معالج عرض قائمة الأوامر المخصصة"""
    try:
        if message.chat.type == 'private':
            return False
        
        chat_id = message.chat.id
        
        if chat_id not in CUSTOM_COMMANDS or not CUSTOM_COMMANDS[chat_id]:
            await message.reply("📋 **لا توجد أوامر مخصصة في هذه المجموعة**")
            return True
        
        commands_list = []
        for keyword, responses in CUSTOM_COMMANDS[chat_id].items():
            commands_list.append(f"🔹 `{keyword}` - {len(responses)} رد")
        
        if commands_list:
            await message.reply(
                f"📋 **الأوامر المخصصة ({len(commands_list)}):**\n\n" +
                "\n".join(commands_list) +
                "\n\n💡 **استخدم:** `حذف امر [الكلمة]` لحذف أمر"
            )
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في عرض قائمة الأوامر: {e}")
        return False


async def handle_custom_commands_states(message: Message, state: FSMContext, current_state: str):
    """معالج حالات إضافة الأوامر المخصصة"""
    try:
        if current_state == "CustomCommandsStates:waiting_keyword":
            # حفظ الكلمة المفتاحية وانتظار الرد
            keyword = message.text.strip()
            
            if not keyword:
                await message.reply("❌ يرجى كتابة كلمة مفتاحية صحيحة")
                return
            
            # حفظ الكلمة المفتاحية في البيانات
            await state.update_data(keyword=keyword)
            await state.set_state(CustomCommandsStates.waiting_response)
            
            await message.reply(
                f"✅ **تم حفظ الكلمة:** `{keyword}`\n\n"
                f"2️⃣ **الآن اكتب الرد للكلمة المفتاحية**\n\n"
                f"**مثال:** أهلاً وسهلاً بك في مجموعتنا الرائعة!\n\n"
                f"🚫 **ألغِ العملية:** `/cancel`"
            )
        
        elif current_state == "CustomCommandsStates:waiting_response":
            # حفظ الرد واكتمال العملية
            response = message.text.strip()
            
            if not response:
                await message.reply("❌ يرجى كتابة رد صحيح")
                return
            
            # الحصول على الكلمة المفتاحية
            data = await state.get_data()
            keyword = data.get('keyword')
            
            if not keyword:
                await message.reply("❌ حدث خطأ، يرجى البدء من جديد")
                await state.clear()
                return
            
            # حفظ الأمر
            chat_id = message.chat.id
            if await save_custom_command(chat_id, keyword, [response]):
                await message.reply(
                    f"✅ **تم إضافة الأمر بنجاح!**\n\n"
                    f"🔑 **الكلمة المفتاحية:** `{keyword}`\n"
                    f"💬 **الرد:** {response}\n\n"
                    f"الآن عندما يكتب أي شخص `{keyword}` سيرد البوت بـ: {response}"
                )
            else:
                await message.reply("❌ فشل في إضافة الأمر، حاول مرة أخرى")
            
            await state.clear()
        
    except Exception as e:
        logging.error(f"خطأ في معالج حالات الأوامر المخصصة: {e}")
        await message.reply("❌ حدث خطأ، تم إلغاء العملية")
        await state.clear()


async def handle_custom_commands_message(message: Message) -> bool:
    """فحص الرسائل للأوامر المخصصة"""
    try:
        if message.chat.type == 'private':
            return False
        
        text = message.text
        if not text:
            return False
        
        # فحص أوامر الإدارة أولاً
        if text.startswith('اضافة امر') or text.startswith('إضافة أمر'):
            return False  # سيتم معالجتها في handle_add_command
        
        if text.startswith('حذف امر') or text.startswith('حذف أمر'):
            return False  # سيتم معالجتها في handle_delete_command
        
        if text.strip() == 'الأوامر المخصصة' or text.strip() == 'الاوامر المخصصة':
            return False  # سيتم معالجتها في handle_list_commands
        
        # البحث عن رد مخصص
        chat_id = message.chat.id
        custom_response = await get_custom_response(chat_id, text)
        
        if custom_response:
            await message.reply(custom_response)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج الأوامر المخصصة: {e}")
        return False
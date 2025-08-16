"""
وحدة التسلية والترفيه
Entertainment Module
"""

import logging
import random
from datetime import datetime
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from database.operations import execute_query, get_user
from utils.helpers import format_number, format_user_mention
from utils.decorators import group_only

# رتب التسلية
ENTERTAINMENT_RANKS = [
    "هطف", "بثر", "حمار", "كلب", "كلبه", "عتوي", "عتويه", 
    "لحجي", "لحجيه", "خروف", "خفيفه", "خفيف"
]

# ردود التسلية
ENTERTAINMENT_RESPONSES = {
    "سيارتي": [
        "🚗 لديك سيارة BMW X6 فخمة!",
        "🚙 سيارتك هي تويوتا كامري 2023",
        "🏎 تملك لامبورغيني أفنتادور!",
        "🚌 سيارتك هي باص نقل عام 😂",
        "🛵 لديك دراجة نارية سريعة",
        "🚲 سيارتك هي... دراجة هوائية! 😅"
    ],
    
    "منزلي": [
        "🏰 تعيش في قصر فخم!",
        "🏠 منزلك جميل ومرتب",
        "🏘 لديك فيلا كبيرة",
        "🏚 منزلك... كوخ صغير 😂",
        "🏨 تعيش في فندق 5 نجوم!",
        "⛺ منزلك خيمة في الصحراء! 😄"
    ],
    
    "عمري": [
        f"🎂 عمرك {random.randint(18, 80)} سنة",
        f"👶 عمرك {random.randint(5, 17)} سنة (صغير!)",
        f"👴 عمرك {random.randint(60, 100)} سنة (كبير!)",
        f"🎈 عمرك {random.randint(20, 35)} سنة (شباب)"
    ],
    
    "طولي": [
        f"📏 طولك {random.randint(160, 190)} سم",
        f"📐 طولك {random.randint(140, 159)} سم (قصير)",
        f"📏 طولك {random.randint(190, 220)} سم (طويل!)",
        f"📏 طولك مثالي: {random.randint(170, 180)} سم"
    ],
    
    "وزني": [
        f"⚖️ وزنك {random.randint(60, 90)} كيلو",
        f"⚖️ وزنك {random.randint(40, 59)} كيلو (نحيف)",
        f"⚖️ وزنك {random.randint(90, 150)} كيلو (ثقيل!)",
        f"⚖️ وزنك مثالي: {random.randint(65, 80)} كيلو"
    ]
}

LOVE_RESPONSES = [
    "💕 نعم أحبك كثيراً!",
    "❤️ بالطبع أحبك!",
    "💖 أحبك أكثر من الشوكولاتة!",
    "💔 لا... لا أحبك",
    "😐 مش متأكد صراحة",
    "🤔 ممكن... ممكن لا",
    "😍 أحبك جداً جداً!",
    "💙 أحبك كصديق فقط"
]

HATE_RESPONSES = [
    "😠 نعم أكرهك!",
    "😡 أكرهك جداً!",
    "💔 للأسف نعم",
    "😌 لا، لا أكرهك",
    "🤗 مستحيل أكرهك!",
    "😊 أحبك أكثر مما أكرهك",
    "😤 أكرهك أحياناً فقط",
    "🙄 لا أكرهك ولا أحبك"
]


async def handle_entertainment_rank(message: Message, rank: str, action: str):
    """معالج رتب التسلية"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص")
            return

        if action == "رفع":
            # رفع رتبة تسلية
            await execute_query(
                "INSERT OR REPLACE INTO entertainment_ranks (user_id, chat_id, rank_type, given_by, given_at) VALUES (?, ?, ?, ?, ?)",
                (target_user.id, message.chat.id, rank, message.from_user.id, datetime.now().isoformat())
            )
            
            await message.reply(f"😂 تم رفع {format_user_mention(target_user)} إلى رتبة {rank}")
            
        elif action == "تنزيل":
            # تنزيل رتبة تسلية
            result = await execute_query(
                "DELETE FROM entertainment_ranks WHERE user_id = ? AND chat_id = ? AND rank_type = ?",
                (target_user.id, message.chat.id, rank)
            )
            
            if result:
                await message.reply(f"✅ تم تنزيل {format_user_mention(target_user)} من رتبة {rank}")
            else:
                await message.reply(f"❌ {format_user_mention(target_user)} ليس لديه رتبة {rank}")

    except Exception as e:
        logging.error(f"خطأ في رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def show_entertainment_ranks(message: Message, rank_type: str = None):
    """عرض قوائم رتب التسلية"""
    try:
        if rank_type:
            # عرض رتبة محددة
            ranks = await execute_query(
                "SELECT user_id FROM entertainment_ranks WHERE chat_id = ? AND rank_type = ?",
                (message.chat.id, rank_type),
                fetch_all=True
            )
            
            if not ranks:
                await message.reply(f"📝 لا يوجد {rank_type} في المجموعة")
                return

            rank_text = f"😂 **قائمة {rank_type}:**\n\n"
            
            for i, rank in enumerate(ranks, 1):
                user_id = rank['user_id'] if isinstance(rank, dict) else rank[0]
                user = await get_user(user_id)
                if user:
                    user_mention = f"@{user['username']}" if user.get('username') else f"#{user_id}"
                    rank_text += f"{i}. {user_mention}\n"

            await message.reply(rank_text)
        
        else:
            # عرض جميع رتب التسلية
            await message.reply("😄 **رتب التسلية المتاحة:**\n" + 
                              "\n".join([f"• {rank}" for rank in ENTERTAINMENT_RANKS]))

    except Exception as e:
        logging.error(f"خطأ في عرض رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الرتب")


async def handle_custom_rank(message: Message, custom_rank: str):
    """معالج الرتب المخصصة"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        target_user = None
        if message.reply_to_message:
            target_user = message.reply_to_message.from_user
        
        if not target_user:
            await message.reply("❌ يرجى الرد على رسالة الشخص")
            return

        # رفع رتبة مخصصة
        await execute_query(
            "INSERT OR REPLACE INTO entertainment_ranks (user_id, chat_id, rank_type, given_by, given_at) VALUES (?, ?, ?, ?, ?)",
            (target_user.id, message.chat.id, custom_rank, message.from_user.id, datetime.now().isoformat())
        )
        
        await message.reply(f"🎭 تم رفع {format_user_mention(target_user)} إلى رتبة {custom_rank}")

    except Exception as e:
        logging.error(f"خطأ في الرتبة المخصصة: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def handle_marriage(message: Message, action: str):
    """معالج الزواج والطلاق"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        user_id = message.from_user.id
        
        if action == "زواج":
            target_user = None
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
            
            if not target_user:
                await message.reply("❌ يرجى الرد على رسالة الشخص الذي تريد الزواج منه")
                return

            if target_user.id == user_id:
                await message.reply("😅 لا يمكنك الزواج من نفسك!")
                return

            # التحقق من الزواج الحالي
            current_marriage = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            if current_marriage:
                await message.reply("💔 أنت متزوج بالفعل! اطلق أولاً")
                return

            # إجراء الزواج
            await execute_query(
                "INSERT INTO entertainment_marriages (user1_id, user2_id, chat_id, married_at) VALUES (?, ?, ?, ?)",
                (user_id, target_user.id, message.chat.id, datetime.now().isoformat())
            )
            
            await message.reply(
                f"💒 مبروك! تم زواج {format_user_mention(message.from_user)} "
                f"و {format_user_mention(target_user)} بنجاح! 💕"
            )
        
        elif action == "طلاق":
            # البحث عن الزواج
            marriage = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            if not marriage:
                await message.reply("😔 أنت لست متزوجاً!")
                return

            # حذف الزواج
            await execute_query(
                "DELETE FROM entertainment_marriages WHERE id = ?",
                (marriage['id'] if isinstance(marriage, dict) else marriage[0],)
            )
            
            await message.reply("💔 تم الطلاق بنجاح! وداعاً أيها الحب 😢")

    except Exception as e:
        logging.error(f"خطأ في الزواج/الطلاق: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ العملية")


async def show_marriage_status(message: Message):
    """عرض حالة الزواج"""
    try:
        user_id = message.from_user.id
        
        marriage = await execute_query(
            "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
            (user_id, user_id, message.chat.id),
            fetch_one=True
        )
        
        if not marriage:
            await message.reply("💔 أنت أعزب/عزباء حالياً")
            return

        # تحديد الشريك
        partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        partner = await get_user(partner_id)
        
        if partner:
            partner_name = partner.get('first_name', f'المستخدم #{partner_id}')
            married_date = marriage['married_at'] if isinstance(marriage, dict) else marriage[3]
            
            await message.reply(
                f"💕 **حالة الزواج:**\n"
                f"💍 الشريك: {partner_name}\n"
                f"📅 تاريخ الزواج: {married_date[:10]}\n"
                f"❤️ دام الحب!"
            )
        else:
            await message.reply("💔 لم أتمكن من العثور على معلومات الشريك")

    except Exception as e:
        logging.error(f"خطأ في عرض حالة الزواج: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الحالة")


async def handle_entertainment_command(message: Message, command: str):
    """معالج أوامر التسلية المختلفة"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            await message.reply("❌ التسلية معطلة في هذه المجموعة")
            return

        if command in ENTERTAINMENT_RESPONSES:
            response = random.choice(ENTERTAINMENT_RESPONSES[command])
            await message.reply(response)
        
        elif command == "تحبني":
            response = random.choice(LOVE_RESPONSES)
            await message.reply(response)
        
        elif command == "تكرهني":
            response = random.choice(HATE_RESPONSES)
            await message.reply(response)
        
        elif command == "نسبه الحب":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                love_percentage = random.randint(0, 100)
                await message.reply(
                    f"💕 نسبة الحب بين {format_user_mention(message.from_user)} "
                    f"و {format_user_mention(target_user)} هي {love_percentage}%"
                )
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")
        
        elif command == "نسبه الغباء":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                stupidity_percentage = random.randint(0, 100)
                await message.reply(
                    f"🤪 نسبة الغباء لدى {format_user_mention(target_user)} "
                    f"هي {stupidity_percentage}%"
                )
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")
        
        elif command == "تحبه":
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
                response = random.choice(LOVE_RESPONSES)
                await message.reply(f"عن {format_user_mention(target_user)}: {response}")
            else:
                await message.reply("❌ يرجى الرد على رسالة الشخص")

    except Exception as e:
        logging.error(f"خطأ في أوامر التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء تنفيذ الأمر")


async def clear_entertainment_ranks(message: Message):
    """مسح رتب التسلية"""
    try:
        if not await has_admin_permission(message.from_user.id, message.chat.id):
            await message.reply("❌ هذا الأمر للإدارة فقط")
            return

        await execute_query(
            "DELETE FROM entertainment_ranks WHERE chat_id = ?",
            (message.chat.id,)
        )
        
        await message.reply("✅ تم مسح جميع رتب التسلية من المجموعة")

    except Exception as e:
        logging.error(f"خطأ في مسح رتب التسلية: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح الرتب")


# دوال مساعدة
async def is_entertainment_enabled(chat_id: int) -> bool:
    """التحقق من تفعيل التسلية"""
    try:
        setting = await execute_query(
            "SELECT setting_value FROM group_settings WHERE chat_id = ? AND setting_key = 'enable_entertainment'",
            (chat_id,),
            fetch_one=True
        )
        
        if setting:
            return setting[0] == "True" if isinstance(setting, tuple) else setting['setting_value'] == "True"
        return True  # افتراضياً مفعل
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من تفعيل التسلية: {e}")
        return True


async def has_admin_permission(user_id: int, chat_id: int) -> bool:
    """التحقق من صلاحيات الإدارة"""
    try:
        from config.settings import ADMINS
        if user_id in ADMINS:
            return True
            
        user_rank = await execute_query(
            "SELECT rank_type FROM group_ranks WHERE user_id = ? AND chat_id = ?",
            (user_id, chat_id),
            fetch_one=True
        )
        
        return user_rank is not None
        
    except Exception as e:
        logging.error(f"خطأ في التحقق من الصلاحيات: {e}")
        return False
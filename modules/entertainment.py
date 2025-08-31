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
        
        # فحص إذا كان المستخدم من العائلة الملكية
        from config.hierarchy import is_royal, is_king, is_queen
        user_is_royal = is_royal(user_id)
        
        if action == "زواج":
            # معالجة خاصة للعائلة الملكية
            if user_is_royal:
                # الزواج الملكي مجاني تماماً!
                dowry_amount = 0
                royal_title = "الملك" if is_king(user_id) else "الملكة"
                await message.reply(
                    f"👑 **زواج ملكي مجاني!**\n\n"
                    f"🎭 {royal_title} لا يدفع مهراً - هذا شرف للطرف الآخر!\n"
                    f"💎 الزواج الملكي مجاني تماماً ومليء بالامتيازات\n"
                    f"🏰 ستحصل على حفل زفاف أسطوري!"
                )
            else:
                # تحليل الرسالة للحصول على المهر للمستخدمين العاديين
                text_parts = message.text.split()
                if len(text_parts) < 2:
                    await message.reply(
                        "❌ **طريقة الزواج الصحيحة:**\n\n"
                        "1️⃣ رد على رسالة من تريد/ين الزواج منه/ها\n"
                        "2️⃣ اكتب: زواج [مبلغ المهر]\n\n"
                        "**مثال:** زواج 5000\n"
                        "💰 المهر يجب أن يكون 1000 أو أكثر"
                    )
                    return
                
                try:
                    dowry_amount = int(text_parts[1])
                except ValueError:
                    await message.reply("❌ يرجى كتابة مبلغ مهر صحيح\n\n**مثال:** زواج 5000")
                    return
                
                if dowry_amount < 1000:
                    await message.reply("❌ مبلغ المهر يجب أن يكون 1,000 أو أكثر")
                    return
            
            target_user = None
            if message.reply_to_message:
                target_user = message.reply_to_message.from_user
            
            if not target_user:
                await message.reply("❌ يرجى الرد على رسالة الشخص الذي تريد الزواج منه")
                return

            if target_user.id == user_id:
                await message.reply("😅 لا يمكنك الزواج من نفسك!")
                return

            # التحقق من الزواج الحالي للطرفين
            current_marriage_proposer = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            current_marriage_target = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (target_user.id, target_user.id, message.chat.id),
                fetch_one=True
            )
            
            if current_marriage_proposer:
                await message.reply("💔 أنت متزوج بالفعل! اطلق أولاً")
                return
                
            if current_marriage_target:
                target_name = target_user.first_name or "الشخص"
                await message.reply(f"💔 {target_name} متزوج بالفعل!")
                return

            # التحقق من رصيد المتقدم للزواج (إذا لم يكن من العائلة الملكية)
            from database.operations import get_user
            proposer = await get_user(user_id)
            if not proposer:
                await message.reply("❌ يرجى إنشاء حساب بنكي أولاً")
                return
            
            # العائلة الملكية لا تحتاج لفحص الرصيد
            if not user_is_royal and proposer['balance'] < dowry_amount:
                from utils.helpers import format_number
                await message.reply(
                    f"❌ ليس لديك رصيد كافٍ للمهر!\n"
                    f"💰 رصيدك: {format_number(proposer['balance'])}$\n"
                    f"💎 المهر المطلوب: {format_number(dowry_amount)}$"
                )
                return

            # إنشاء طلب زواج في قاعدة البيانات
            await execute_query(
                "INSERT INTO marriage_proposals (proposer_id, target_id, chat_id, dowry_amount, proposed_at, status) VALUES (?, ?, ?, ?, ?, 'pending')",
                (user_id, target_user.id, message.chat.id, dowry_amount, datetime.now().isoformat())
            )
            
            proposer_name = message.from_user.first_name or "شخص"
            target_name = target_user.first_name or "شخص"
            
            from utils.helpers import format_number
            
            # رسالة طلب زواج مختلفة للعائلة الملكية
            if user_is_royal:
                royal_title = "الملك" if is_king(user_id) else "الملكة"
                target_is_royal = is_royal(target_user.id)
                target_royal_title = ""
                if target_is_royal:
                    target_royal_title = "الملك" if is_king(target_user.id) else "الملكة"
                
                marriage_message = (
                    f"👑 **طلب زواج ملكي أسطوري!** 👑\n\n"
                    f"🎭 من: {royal_title} {proposer_name}\n"
                    f"🎭 إلى: {target_royal_title + ' ' if target_royal_title else ''}{target_name}\n"
                    f"💎 المهر: مجاني تماماً - شرف ملكي!\n"
                    f"🏰 نوع الزواج: **زواج ملكي فخم**\n"
                    f"🎊 المكافآت: حفل زفاف أسطوري + هدايا ملكية\n\n"
                    f"⏰ **في انتظار الموافقة الملكية من {target_name}**\n"
                    f"👑 يجب على {target_name} الرد بكلمة **موافقة** للحصول على الشرف الملكي\n"
                    f"🚫 أو **رفض** لتفويت هذا الشرف العظيم"
                )
            else:
                marriage_message = (
                    f"💍 **طلب زواج جديد!**\n\n"
                    f"👤 من: {proposer_name}\n"
                    f"👤 إلى: {target_name}\n"
                    f"💰 المهر: {format_number(dowry_amount)}$\n\n"
                    f"⏰ **في انتظار موافقة {target_name}**\n"
                    f"📝 يجب على {target_name} الرد بكلمة **موافقة** للقبول\n"
                    f"🚫 أو **رفض** لرفض الطلب"
                )
            
            await message.reply(marriage_message)
        
        elif action == "طلاق" or action == "خلع":
            # البحث عن الزواج
            marriage = await execute_query(
                "SELECT * FROM entertainment_marriages WHERE (user1_id = ? OR user2_id = ?) AND chat_id = ?",
                (user_id, user_id, message.chat.id),
                fetch_one=True
            )
            
            if not marriage:
                await message.reply("😔 أنت لست متزوجاً!")
                return

            # تحديد الطرفين - الآن نضمن أن نحصل على المعرفات بشكل صحيح
            if isinstance(marriage, dict):
                user1_id = marriage['user1_id']
                user2_id = marriage['user2_id']
                marriage_id = marriage['id']
            else:
                # إذا كانت النتيجة tuple أو list
                marriage_id = marriage[0]
                user1_id = marriage[1]
                user2_id = marriage[2]
            
            from database.operations import get_user, update_user_balance, add_transaction
            
            # جلب بيانات الطرفين
            user1 = await get_user(user1_id)
            user2 = await get_user(user2_id)
            
            if not user1 or not user2:
                await message.reply("❌ خطأ في الحصول على بيانات الأطراف")
                return
            
            # التحقق من أن كلا الطرفين لديهما 500 على الأقل
            divorce_fee = 500
            if user1['balance'] < divorce_fee:
                user1_name = user1.get('first_name', f'المستخدم #{user1_id}')
                await message.reply(f"❌ {user1_name} لا يملك {divorce_fee}$ للطلاق")
                return
                
            if user2['balance'] < divorce_fee:
                user2_name = user2.get('first_name', f'المستخدم #{user2_id}')
                await message.reply(f"❌ {user2_name} لا يملك {divorce_fee}$ للطلاق")
                return
            
            # معرف الشيخ
            JUDGE_ID = 7155814194
            JUDGE_USERNAME = "@Hacker20263"
            JUDGE_NAME = "ردفان"
            
            # خصم 500 من كل طرف
            new_user1_balance = user1['balance'] - divorce_fee
            new_user2_balance = user2['balance'] - divorce_fee
            
            await update_user_balance(user1_id, new_user1_balance)
            await update_user_balance(user2_id, new_user2_balance)
            
            # إعطاء الشيخ 1000 (500+500)
            judge = await get_user(JUDGE_ID)
            if judge:
                new_judge_balance = judge['balance'] + (divorce_fee * 2)
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي
                await add_transaction(
                    JUDGE_ID,
                    f"أتعاب طلاق {user1.get('first_name', 'مستخدم')} و {user2.get('first_name', 'مستخدم')}",
                    divorce_fee * 2,
                    "divorce_fee"
                )
            
            # إضافة المعاملات للطرفين
            divorce_type = "طلاق" if action == "طلاق" else "خلع"
            await add_transaction(
                user1_id,
                f"رسوم {divorce_type}",
                -divorce_fee,
                "divorce_fee"
            )
            await add_transaction(
                user2_id,
                f"رسوم {divorce_type}",
                -divorce_fee,
                "divorce_fee"
            )

            # حذف الزواج
            await execute_query(
                "DELETE FROM entertainment_marriages WHERE id = ?",
                (marriage_id,)
            )
            
            from utils.helpers import format_number
            divorce_message = (
                f"💔 **تم {divorce_type} بنجاح!**\n\n"
                f"👤 الطرف الأول: {user1.get('first_name', 'مستخدم')}\n"
                f"👤 الطرف الثاني: {user2.get('first_name', 'مستخدم')}\n"
                f"💰 رسوم {divorce_type}: {format_number(divorce_fee)}$ من كل طرف\n"
                f"⚖️ أتعاب الشيخ: {format_number(divorce_fee * 2)}$\n\n"
                f"🕌 **تم الطلاق بحضور فضيلة الشيخ:**\n"
                f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n\n"
                f"😢 وداعاً أيها الحب!"
            )
            
            await message.reply(divorce_message)
            
            # إشعار القاضي إذا كان متاح
            if judge:
                try:
                    await message.bot.send_message(
                        JUDGE_ID,
                        f"⚖️ **تم {divorce_type} جديد بحضرتكم**\n\n"
                        f"👤 الطرف الأول: {user1.get('first_name', 'مستخدم')}\n"
                        f"👤 الطرف الثاني: {user2.get('first_name', 'مستخدم')}\n"
                        f"💰 الأتعاب المستحقة: {format_number(divorce_fee * 2)}$\n"
                        f"💳 رصيدكم الجديد: {format_number(new_judge_balance)}$\n\n"
                        f"🌟 جزاكم الله خيراً على خدمة المسلمين"
                    )
                except:
                    pass  # إذا فشل إرسال الإشعار

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
        
        # تسجيل لمراقبة حالة الزواج
        logging.info(f"البحث عن زواج للمستخدم {user_id} في المجموعة {message.chat.id}: {marriage}")
        
        if not marriage:
            await message.reply("💔 أنت أعزب/عزباء حالياً")
            return

        # تحديد الشريك
        if isinstance(marriage, dict):
            partner_id = marriage['user2_id'] if marriage['user1_id'] == user_id else marriage['user1_id']
        else:
            # إذا كانت النتيجة tuple أو list
            partner_id = marriage[2] if marriage[1] == user_id else marriage[1]
        
        partner = await get_user(partner_id)
        
        if partner:
            partner_name = partner.get('first_name', f'المستخدم #{partner_id}')
            married_date = marriage.get('married_at', '') if isinstance(marriage, dict) else marriage[6] if len(marriage) > 6 else ''
            dowry_amount = marriage.get('dowry_amount', 0) if isinstance(marriage, dict) else marriage[4] if len(marriage) > 4 else 0
            judge_commission = marriage.get('judge_commission', 0) if isinstance(marriage, dict) else marriage[5] if len(marriage) > 5 else 0
            
            marriage_info = (
                f"💕 **حالة الزواج:**\n"
                f"💍 الشريك: {partner_name}\n"
                f"📅 تاريخ الزواج: {married_date[:10] if married_date else 'غير محدد'}\n"
            )
            
            if dowry_amount > 0:
                from utils.helpers import format_number
                marriage_info += f"💎 المهر: {format_number(dowry_amount)}$\n"
            
            if judge_commission > 0:
                from utils.helpers import format_number
                marriage_info += f"⚖️ أتعاب الشيخ: {format_number(judge_commission)}$\n"
                marriage_info += f"🕌 كتب العقد: الشيخ المحترم ردفان @Hacker20263\n"
            
            marriage_info += f"❤️ دام الحب!"
            
            await message.reply(marriage_info)
        else:
            await message.reply("💔 لم أتمكن من العثور على معلومات الشريك")

    except Exception as e:
        logging.error(f"خطأ في عرض حالة الزواج: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض الحالة")


async def handle_marriage_response(message: Message, response_type: str):
    """معالج موافقة أو رفض الزواج"""
    try:
        if not await is_entertainment_enabled(message.chat.id):
            return

        user_id = message.from_user.id
        
        # البحث عن طلب زواج معلق
        proposal = await execute_query(
            "SELECT * FROM marriage_proposals WHERE target_id = ? AND chat_id = ? AND status = 'pending' ORDER BY proposed_at DESC LIMIT 1",
            (user_id, message.chat.id),
            fetch_one=True
        )
        
        if not proposal:
            await message.reply("❌ لا يوجد طلب زواج معلق لك")
            return
        
        proposer_id = proposal['proposer_id'] if isinstance(proposal, dict) else proposal[1]
        dowry_amount = proposal['dowry_amount'] if isinstance(proposal, dict) else proposal[4]
        proposal_id = proposal['id'] if isinstance(proposal, dict) else proposal[0]
        
        from database.operations import get_user
        proposer = await get_user(proposer_id)
        target = await get_user(user_id)
        
        if not proposer or not target:
            await message.reply("❌ خطأ في الحصول على بيانات المستخدمين")
            return
        
        proposer_name = proposer.get('first_name', f'المستخدم #{proposer_id}')
        target_name = target.get('first_name', f'المستخدم #{user_id}')
        
        if response_type == "موافقة":
            # فحص إذا كان أحد الأطراف من العائلة الملكية
            from config.hierarchy import is_royal, is_king, is_queen
            proposer_is_royal = is_royal(proposer_id)
            target_is_royal = is_royal(user_id)
            
            # التحقق من أن المتقدم لا يزال لديه الرصيد (إلا إذا كان ملكياً)
            if not proposer_is_royal and proposer['balance'] < dowry_amount:
                await execute_query(
                    "UPDATE marriage_proposals SET status = 'cancelled' WHERE id = ?",
                    (proposal_id,)
                )
                from utils.helpers import format_number
                await message.reply(
                    f"❌ **تم إلغاء الطلب!**\n"
                    f"السبب: {proposer_name} لا يملك رصيد كافٍ للمهر\n"
                    f"💰 المهر المطلوب: {format_number(dowry_amount)}$"
                )
                return
            
            # الآن نحتاج للقاضي - معرف القاضي المحدد (الشيخ ردفان)
            JUDGE_ID = 7155814194
            JUDGE_USERNAME = "@Hacker20263"
            JUDGE_NAME = "ردفان"
            
            # معالجة مختلفة للزواج الملكي
            if proposer_is_royal or target_is_royal:
                # الزواج الملكي بدون رسوم أو عمولة
                judge_commission = 0
                total_cost = 0
                royal_wedding = True
            else:
                # حساب عمولة القاضي (بين 100-1000 حسب المهر)
                judge_commission = max(100, min(1000, int(dowry_amount * 0.05)))  # 5% من المهر
                total_cost = dowry_amount + judge_commission
                royal_wedding = False
                
                # التحقق من أن المتقدم يستطيع دفع المهر + العمولة
                if proposer['balance'] < total_cost:
                    from utils.helpers import format_number
                    await message.reply(
                        f"❌ **رصيد غير كافٍ!**\n"
                        f"💰 المهر: {format_number(dowry_amount)}$\n"
                        f"💼 عمولة القاضي: {format_number(judge_commission)}$\n"
                        f"💸 المطلوب: {format_number(total_cost)}$\n"
                        f"💰 الرصيد الحالي: {format_number(proposer['balance'])}$"
                    )
                    return
            
            # تنفيذ المعاملة المالية
            from database.operations import update_user_balance, add_transaction
            
            # معالجة مختلفة للزواج الملكي
            if royal_wedding:
                # الزواج الملكي - هدايا ملكية بدلاً من المهر
                royal_gift = 50000  # هدية ملكية كبيرة
                new_proposer_balance = proposer['balance'] + royal_gift
                new_target_balance = target['balance'] + royal_gift
                await update_user_balance(proposer_id, new_proposer_balance)
                await update_user_balance(user_id, new_target_balance)
                
                # إضافة المعاملات الملكية
                await add_transaction(
                    proposer_id,
                    "هدية زواج ملكي",
                    royal_gift,
                    "royal_wedding_gift"
                )
                await add_transaction(
                    user_id,
                    "هدية زواج ملكي",
                    royal_gift,
                    "royal_wedding_gift"
                )
            else:
                # الزواج العادي
                # خصم من المتقدم
                new_proposer_balance = proposer['balance'] - total_cost
                await update_user_balance(proposer_id, new_proposer_balance)
                
                # إعطاء المهر للعروس
                new_target_balance = target['balance'] + dowry_amount
                await update_user_balance(user_id, new_target_balance)
            
            # إعطاء العمولة للقاضي (إذا كان مسجل في البوت وليس زواج ملكي)
            judge = await get_user(JUDGE_ID)
            if judge and not royal_wedding:
                new_judge_balance = judge['balance'] + judge_commission
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي
                await add_transaction(
                    JUDGE_ID,
                    f"عمولة زواج {proposer_name} و {target_name}",
                    judge_commission,
                    "judge_commission"
                )
            elif judge and royal_wedding:
                # القاضي يحصل على هدية ملكية خاصة
                royal_judge_gift = 100000
                new_judge_balance = judge['balance'] + royal_judge_gift
                await update_user_balance(JUDGE_ID, new_judge_balance)
                
                # إضافة معاملة للقاضي
                await add_transaction(
                    JUDGE_ID,
                    f"هدية ملكية لقاضي الزواج الملكي {proposer_name} و {target_name}",
                    royal_judge_gift,
                    "royal_judge_gift"
                )
            
            # إضافة المعاملات للزواج العادي فقط
            if not royal_wedding:
                await add_transaction(
                    proposer_id,
                    f"مهر زواج من {target_name}",
                    -dowry_amount,
                    "marriage_dowry"
                )
                await add_transaction(
                    proposer_id,
                    f"عمولة القاضي للزواج",
                    -judge_commission,
                    "judge_fee"
                )
                await add_transaction(
                    user_id,
                    f"مهر زواج من {proposer_name}",
                    dowry_amount,
                    "marriage_dowry"
                )
            
            # إجراء الزواج
            marriage_saved = await execute_query(
                "INSERT INTO entertainment_marriages (user1_id, user2_id, chat_id, dowry_amount, judge_commission, married_at) VALUES (?, ?, ?, ?, ?, ?)",
                (proposer_id, user_id, message.chat.id, dowry_amount, judge_commission, datetime.now().isoformat())
            )
            
            # تسجيل لوحظة حفظ الزواج
            logging.info(f"تم حفظ الزواج بين {proposer_id} و {user_id} في المجموعة {message.chat.id}: {marriage_saved}")
            
            # تحديث حالة الطلب
            await execute_query(
                "UPDATE marriage_proposals SET status = 'accepted' WHERE id = ?",
                (proposal_id,)
            )
            
            from utils.helpers import format_number
            
            # رسالة زواج مختلفة للعائلة الملكية
            if royal_wedding:
                # تحديد الألقاب الملكية
                proposer_title = "الملك" if is_king(proposer_id) else "الملكة" if is_queen(proposer_id) else "الأمير/ة"
                target_title = "الملك" if is_king(user_id) else "الملكة" if is_queen(user_id) else "الأمير/ة"
                
                marriage_message = (
                    f"👑✨ **زفاف ملكي أسطوري!** ✨👑\n\n"
                    f"🎭 **طقوس الزفاف الملكي الفخم:**\n"
                    f"👸 العروس الملكية: {target_title} {target_name}\n"
                    f"🤴 العريس الملكي: {proposer_title} {proposer_name}\n"
                    f"💎 المهر الملكي: مجاني - شرف ملكي!\n"
                    f"🎁 الهدايا الملكية: {format_number(royal_gift)}$ لكل طرف\n"
                    f"👑 هدية القاضي الملكية: {format_number(royal_judge_gift)}$\n\n"
                    f"🏰 **مراسم الزفاف الأسطوري:**\n"
                    f"🕌 **كتب العقد الملكي فضيلة الشيخ الأعظم:**\n"
                    f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n"
                    f"🎊 **إعلان لجميع الرعايا:** لقد تم الزفاف الملكي!\n"
                    f"🎭 **مراسم احتفالية:** موكب ملكي + هدايا للحضور\n\n"
                    f"✨ **بارك الله في العائلة الملكية الجديدة!** ✨\n"
                    f"👑 عاشت العائلة الملكية! 👑\n"
                    f"🌟 دام الحب الملكي والهناء الأبدي! 🌟"
                )
            else:
                marriage_message = (
                    f"💒 **مبروك الزواج!** 🎉\n\n"
                    f"👰 العروس: {target_name}\n"
                    f"🤵 العريس: {proposer_name}\n"
                    f"💎 المهر: {format_number(dowry_amount)}$\n"
                    f"⚖️ أتعاب الشيخ: {format_number(judge_commission)}$\n\n"
                    f"🕌 **شهد على العقد وكتبه فضيلة الشيخ المحترم:**\n"
                    f"📜 الشيخ {JUDGE_NAME} {JUDGE_USERNAME}\n"
                    f"🌟 بارك الله للعروسين وجمع بينهما في خير\n\n"
                    f"💕 ألف مبروك للعروسين!\n"
                    f"🌹 دام الحب والهناء!"
                )
            
            await message.reply(marriage_message)
            
            # إشعار القاضي إذا كان متاح
            if judge:
                try:
                    if royal_wedding:
                        await message.bot.send_message(
                            JUDGE_ID,
                            f"👑 **مبروك فضيلة الشيخ الأعظم** 👑\n\n"
                            f"🎭 تم إتمام أول زفاف ملكي في التاريخ بحضرتكم المباركة!\n"
                            f"👸 العروس الملكية: {target_name}\n"
                            f"🤴 العريس الملكي: {proposer_name}\n"
                            f"👑 الهدية الملكية الخاصة: {format_number(royal_judge_gift)}$\n"
                            f"💳 رصيدكم الملكي الجديد: {format_number(new_judge_balance)}$\n\n"
                            f"🏰 **شرف عظيم:** أنتم قاضي الزفاف الملكي الأول!\n"
                            f"✨ جزاكم الله خيراً على خدمة العائلة الملكية والمسلمين"
                        )
                    else:
                        await message.bot.send_message(
                            JUDGE_ID,
                            f"🕌 **بارك الله في فضيلة الشيخ**\n\n"
                            f"📜 تم إتمام عقد زواج جديد بحضرتكم المباركة\n"
                            f"👰 العروس: {target_name}\n"
                            f"🤵 العريس: {proposer_name}\n"
                            f"💰 الأتعاب المستحقة: {format_number(judge_commission)}$\n"
                            f"💳 رصيدكم الجديد: {format_number(new_judge_balance)}$\n\n"
                            f"🌟 جزاكم الله خيراً على خدمة المسلمين"
                        )
                except:
                    pass  # إذا فشل إرسال الإشعار
        
        elif response_type == "رفض":
            # رفض الطلب
            await execute_query(
                "UPDATE marriage_proposals SET status = 'rejected' WHERE id = ?",
                (proposal_id,)
            )
            
            from utils.helpers import format_number
            await message.reply(
                f"💔 **تم رفض طلب الزواج**\n\n"
                f"👤 المرفوض: {proposer_name}\n"
                f"💰 المهر المرفوض: {format_number(dowry_amount)}$\n\n"
                f"😔 ربما في المرة القادمة!"
            )
    
    except Exception as e:
        logging.error(f"خطأ في معالجة رد الزواج: {e}")
        await message.reply("❌ حدث خطأ أثناء معالجة الرد")


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
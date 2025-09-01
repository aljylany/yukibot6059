"""
معالج أحداث المجموعات
Group Events Handler
"""

import logging
from datetime import datetime
from aiogram import Router, F, Bot
from aiogram.types import ChatMemberUpdated, ChatMember, Message
from aiogram.enums import ChatType, ChatMemberStatus
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest

from config.settings import NOTIFICATION_CHANNEL, ADMINS
from database.operations import get_or_create_user
from modules.notification_manager import NotificationManager

router = Router()



async def get_group_admins_info(bot: Bot, chat_id: int):
    """جلب معلومات مشرفي المجموعة"""
    try:
        admins = await bot.get_chat_administrators(chat_id)
        admin_list = []
        
        for admin in admins:
            user = admin.user
            status_emoji = "👑" if admin.status == ChatMemberStatus.CREATOR else "🔧"
            
            # تجميع معلومات المشرف
            admin_info = f"{status_emoji} "
            if user.first_name:
                admin_info += user.first_name
            if user.last_name:
                admin_info += f" {user.last_name}"
            if user.username:
                admin_info += f" (@{user.username})"
            admin_info += f" - ID: <code>{user.id}</code>"
            
            admin_list.append(admin_info)
        
        return admin_list
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المشرفين: {e}")
        return ["❌ لا يمكن جلب معلومات المشرفين"]


async def initialize_new_group_data(chat_id: int, group_info: dict):
    """تهيئة بيانات المجموعة الجديدة في جميع الأنظمة"""
    try:
        # تهيئة نظام الذاكرة المشتركة للمجموعة الجديدة
        from modules.shared_memory_sqlite import shared_group_memory_sqlite
        await shared_group_memory_sqlite.init_shared_memory_db()
        
        # حفظ معلومات المجموعة في قاعدة البيانات
        from database.operations import execute_query
        await execute_query("""
            INSERT OR REPLACE INTO group_info 
            (chat_id, title, type, username, members_count, initialized_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            chat_id,
            group_info.get('title', ''),
            group_info.get('type', ''),
            group_info.get('username', ''),
            group_info.get('members_count', 0),
            datetime.now().isoformat()
        ))
        
        logging.info(f"✅ تم تهيئة بيانات المجموعة الجديدة: {group_info.get('title')} ({chat_id})")
        
    except Exception as e:
        logging.error(f"خطأ في تهيئة بيانات المجموعة الجديدة {chat_id}: {e}")


async def get_group_info(bot: Bot, chat_id: int):
    """جلب معلومات المجموعة"""
    try:
        chat = await bot.get_chat(chat_id)
        
        # تحديد نوع المجموعة
        group_type = "مجموعة عادية" if chat.type == ChatType.GROUP else "مجموعة عملاقة"
        
        # جلب عدد الأعضاء
        try:
            members_count = await bot.get_chat_member_count(chat_id)
        except:
            members_count = "غير معروف"
        
        # تجميع معلومات المجموعة
        group_info = {
            "title": chat.title or "بدون عنوان",
            "type": group_type,
            "id": chat_id,
            "username": f"@{chat.username}" if chat.username else "لا يوجد",
            "members_count": members_count,
            "description": chat.description[:100] + "..." if chat.description and len(chat.description) > 100 else chat.description or "لا يوجد وصف"
        }
        
        return group_info
    except Exception as e:
        logging.error(f"خطأ في جلب معلومات المجموعة: {e}")
        return None


@router.my_chat_member()
async def handle_my_chat_member_update(update: ChatMemberUpdated, bot: Bot):
    """معالج تحديثات عضوية البوت في المجموعات"""
    try:
        # التحقق من أن التحديث خاص بإضافة البوت كعضو جديد أو ترقيته كمشرف
        old_status = update.old_chat_member.status
        new_status = update.new_chat_member.status
        
        # تجاهل التحديثات في المحادثات الخاصة
        if update.chat.type == ChatType.PRIVATE:
            return
        
        # التحقق من إضافة البوت للمجموعة لأول مرة
        if (old_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED] and 
            new_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR]):
            
            logging.info(f"🎉 تم إضافة البوت إلى مجموعة جديدة: {update.chat.title} ({update.chat.id})")
            
            # جلب معلومات المجموعة والمشرفين
            group_info = await get_group_info(bot, update.chat.id)
            admins_info = await get_group_admins_info(bot, update.chat.id)
            
            if group_info:
                # إرسال الإشعار للقناة الفرعية باستخدام مدير الإشعارات
                notification_manager = NotificationManager(bot)
                await notification_manager.send_new_group_notification(group_info, admins_info)
                
        # التحقق من ترقية البوت لمشرف
        elif (old_status == ChatMemberStatus.MEMBER and 
              new_status == ChatMemberStatus.ADMINISTRATOR):
            
            logging.info(f"⬆️ تم ترقية البوت لمشرف في: {update.chat.title}")
            
            # إرسال إشعار الترقية
            group_info = {"title": update.chat.title, "id": update.chat.id}
            notification_manager = NotificationManager(bot)
            await notification_manager.send_bot_promotion_notification(group_info)
                
        # التحقق من إزالة البوت من المجموعة
        elif (old_status in [ChatMemberStatus.MEMBER, ChatMemberStatus.ADMINISTRATOR] and 
              new_status in [ChatMemberStatus.LEFT, ChatMemberStatus.KICKED]):
            
            logging.info(f"😢 تم إزالة البوت من: {update.chat.title}")
            
            # إرسال إشعار الإزالة
            group_info = {"title": update.chat.title, "id": update.chat.id}
            notification_manager = NotificationManager(bot)
            await notification_manager.send_bot_removal_notification(group_info)
                
    except Exception as e:
        logging.error(f"خطأ في معالج أحداث المجموعات: {e}")


@router.message(F.content_type.in_({"new_chat_members"}))
async def handle_new_members(message: Message, bot: Bot):
    """معالج إضافة أعضاء جدد للمجموعة"""
    try:
        # التحقق من وجود أعضاء جدد
        if not message.new_chat_members:
            return
            
        import random
        from database.operations import get_user
        from config.hierarchy import is_master
        
        # رسائل الترحيب المرحة للأعضاء الجدد
        WELCOME_MESSAGES = [
            "🎉 مرحباً بك في العائلة يا {name}! \n🎯 استعد للمغامرة... هنا لا مكان للضعفاء! 😤\n💰 سجل حسابك البنكي واطرد الفقر من حياتك! \n⚡ اكتب 'انشاء حساب بنكي' وابدأ رحلة الثراء!",
            
            "🔥 أهلاً وسهلاً {name}! \n🎪 دخلت أقوى مجموعة في التليجرام! \n💎 هنا نتاجر بالملايين ونسرق الأحلام! \n🏦 سجل في البنك وابدأ إمبراطوريتك المالية!",
            
            "👑 {name} انضم للملوك! \n🚀 مرحباً بك في عالم يوكي الاقتصادي! \n💸 هنا المال يتكلم والفقراء يسكتون! \n🎲 جرب حظك واكسب ثروتك الأولى!",
            
            "🎭 مرحباً {name}! \n🌟 دخلت أسطورة الاقتصاد الافتراضي! \n💰 استعد لتصبح مليونير أو تفلس تماماً! \n🎯 لا يوجد نصف حلول هنا!",
            
            "🎊 أهلاً بالوافد الجديد {name}! \n⚡ هنا حيث تولد الأحلام أو تدفن في الرمال! \n🏰 ابني قلعتك واحمي أموالك من اللصوص! \n💪 فقط الأقوياء يبقون!"
        ]
        
        # رسائل خاصة للمشرفين والمميزين
        VIP_WELCOME_MESSAGES = [
            "👑 أهلاً بالقائد {name}! \n⚡ مشرف قوي انضم للعائلة! \n🔥 الجماعة تحتاج قيادتك الحكيمة! \n💎 مرحباً بك في المقدمة!",
            
            "🎖️ العسكري {name} في الخدمة! \n🛡️ جندي جديد في جيش الاقتصاد! \n⚔️ استعد للمعارك الشرسة! \n👑 القيادة تنتظر أوامرك!"
        ]
        
        # التحقق من إضافة البوت كعضو جديد
        for new_member in message.new_chat_members:
            if new_member and new_member.id == bot.id:
                # البوت تم إضافته كعضو جديد
                logging.info(f"🎉 تم إضافة البوت كعضو جديد في: {message.chat.title}")
                
                # إرسال رسالة ترحيب في المجموعة
                welcome_message = """
🎉 <b>أهلاً وسهلاً! تم تفعيل البوت بنجاح</b>

🤖 أنا <b>Yuki</b>، بوت الألعاب الاقتصادية التفاعلية!

🚀 <b>للبدء:</b>
• اكتب <code>انشاء حساب بنكي</code> لبدء رحلتك
• اكتب <code>المساعدة</code> لمعرفة جميع الأوامر

💡 <b>نصيحة:</b> لأفضل تجربة، اجعلني مشرفاً في المجموعة!

🎮 <b>استعد للمتعة والتشويق في عالم الاقتصاد الافتراضي!</b>
                """
                
                await message.reply(welcome_message, parse_mode="HTML")
                
            elif new_member and not new_member.is_bot:
                # عضو جديد حقيقي انضم
                name = new_member.first_name or new_member.username or "الغامض"
                
                # فحص إذا كان المستخدم مشرف أو مميز
                is_vip = is_master(new_member.id)
                
                # اختيار رسالة ترحيب مناسبة
                if is_vip:
                    welcome_msg = random.choice(VIP_WELCOME_MESSAGES).format(name=name)
                else:
                    welcome_msg = random.choice(WELCOME_MESSAGES).format(name=name)
                
                # إرسال رسالة الترحيب
                await message.reply(welcome_msg)
                
                # فحص حالة التسجيل في البنك
                import asyncio
                await asyncio.sleep(2)  # انتظار قصير
                
                try:
                    user_data = await get_user(new_member.id)
                    bank_registered = user_data and user_data.get('bank') is not None
                    
                    if not bank_registered:
                        await message.reply(
                            f"🏦 مرحباً {name}! \n"
                            "💰 لم أجد لك حساب بنكي معنا بعد! \n"
                            "🎯 اكتب 'انشاء حساب بنكي' لتبدأ رحلة الثراء! \n"
                            "⚡ أو اختر البنك مباشرة: الأهلي، الراجحي، سامبا، الرياض"
                        )
                    else:
                        # إذا كان مسجل، اعرض معلومات سريعة
                        balance = user_data.get('balance', 0)
                        await message.reply(
                            f"💎 أهلاً بعودتك {name}! \n"
                            f"💰 رصيدك الحالي: {balance:,} ريال \n"
                            "🚀 مرحباً بك مرة أخرى في عالم الأعمال!"
                        )
                except Exception as e:
                    logging.error(f"خطأ في فحص البنك للعضو الجديد: {e}")
                
                # تسجيل الحدث
                logging.info(f"انضم عضو جديد: {name} ({new_member.id}) للمجموعة {message.chat.id}")
                
    except Exception as e:
        logging.error(f"خطأ في معالج الأعضاء الجدد: {e}")


@router.message(F.content_type.in_({"left_chat_member"}))
async def handle_left_member(message: Message, bot: Bot):
    """معالج مغادرة الأعضاء للمجموعة"""
    try:
        # التحقق من وجود عضو مغادر
        if not message.left_chat_member:
            return
            
        import random
        from database.operations import get_user
        from config.hierarchy import is_master
        
        # رسائل التوديع المستفزة والمضحكة للمغادرين
        GOODBYE_MESSAGES = [
            "👋 وداعاً {name}! \n😂 طبعاً مش قد اللعبة... \n💸 خلاص ضاعت منك ملايين المستقبل! \n🚪 باب الفقر مفتوح لك على مصراعيه!",
            
            "🎭 {name} هرب من المسؤولية! \n😅 ما قدر يحمل ضغط الثراء... \n💔 ضيعت على نفسك فرصة العمر! \n🐔 الدجاج يرجع للقن!",
            
            "🏃‍♂️ {name} فر من ساحة المعركة! \n🤣 ما تحمل منافسة الكبار! \n💰 خلاص... الملايين راحت عليك! \n🎪 المهرج غادر السيرك!",
            
            "👻 {name} اختفى مثل الدخان! \n😜 طبعاً الضغط كان أكبر من قدرته! \n💸 الفلوس كانت تخوفه... مسكين! \n🚀 رحلة سعيدة للقمر!",
            
            "🎯 {name} استسلم! \n😎 ما قدر يواجه تحدي الأثرياء! \n💎 ضيعت الماس وأخذت الحصى! \n🐰 الأرنب رجع لجحره!",
            
            "🎪 {name} خرج من الساحة! \n🤡 كان يظن إنه بطل... طلع مهرج! \n💰 الفقر ينتظرك بالخارج! \n👋 يلا باي... ومتعود تزورنا!"
        ]
        
        # رسائل خاصة للمشرفين والمميزين
        VIP_GOODBYE_MESSAGES = [
            "💔 المشرف {name} تركنا! \n😢 فقدنا قائد قوي اليوم... \n👑 العرش أصبح فارغ! \n🌟 ستبقى في الذاكرة!",
            
            "⚡ القائد {name} غادر الساحة! \n😪 الجيش فقد أحد أقوى جنوده! \n🏆 كنت مثال للقيادة الحكيمة! \n🚀 رحلة موفقة أيها البطل!"
        ]
        
        # التحقق من مغادرة البوت
        if message.left_chat_member.id == bot.id:
            logging.info(f"😢 البوت غادر المجموعة: {message.chat.title}")
            return
            
        # معالجة مغادرة عضو حقيقي
        left_member = message.left_chat_member
        if not left_member.is_bot:
            name = left_member.first_name or left_member.username or "المختفي"
            
            # فحص إذا كان المستخدم مشرف أو مميز
            is_vip = is_master(left_member.id)
            
            # اختيار رسالة توديع مناسبة
            if is_vip:
                goodbye_msg = random.choice(VIP_GOODBYE_MESSAGES).format(name=name)
            else:
                goodbye_msg = random.choice(GOODBYE_MESSAGES).format(name=name)
            
            # إضافة معلومات مالية إذا كان مسجل
            try:
                user_data = await get_user(left_member.id)
                if user_data and user_data.get('balance', 0) > 0:
                    balance = user_data.get('balance', 0)
                    goodbye_msg += f"\n💸 وترك وراءه {balance:,} ريال! \n🤑 يا حسرة على الفلوس الضايعة!"
            except Exception as e:
                logging.error(f"خطأ في جلب بيانات العضو المغادر: {e}")
            
            # إرسال رسالة التوديع
            await message.reply(goodbye_msg)
            
            # تسجيل الحدث
            logging.info(f"غادر العضو: {name} ({left_member.id}) من المجموعة {message.chat.id}")
            
    except Exception as e:
        logging.error(f"خطأ في معالج مغادرة الأعضاء: {e}")


# معالج لمراقبة جميع الأنشطة في المجموعة
@router.message(F.chat.type.in_({"group", "supergroup"}))
async def monitor_group_activity(message: Message):
    """مراقب ذكي لجميع أنشطة المجموعة"""
    try:
        if not message.from_user or message.from_user.is_bot:
            return
            
        # تحليل النشاط وإرسال تعليقات ذكية أحياناً
        await analyze_and_comment(message)
        
    except Exception as e:
        logging.error(f"خطأ في مراقب الأنشطة: {e}")


async def analyze_and_comment(message: Message):
    """تحليل الرسائل وإرسال تعليقات ذكية أحياناً"""
    try:
        import random
        
        text = message.text.lower() if message.text else ""
        user_name = message.from_user.first_name or "المجهول"
        
        # تعليقات عشوائية على أنشطة معينة (بنسبة قليلة لتجنب الإزعاج)
        if random.randint(1, 100) <= 3:  # 3% فرصة للتعليق
            
            # تعليقات على الأموال
            if any(word in text for word in ['فلوس', 'مال', 'ريال', 'مليون', 'ثروة', 'بنك', 'رصيد']):
                comments = [
                    f"💰 {user_name} يتكلم عن الفلوس... شايف نفسه تاجر! 😏",
                    f"🤑 المال يناديك يا {user_name}! وقت الاستثمار! 📈",
                    f"💸 {user_name} مهووس بالثروة... أحترم الطموح! 👑",
                    f"🏦 البنوك تناديك يا {user_name}! اعمل حسابك وابدأ! 💪",
                    f"💎 {user_name} عنده نظرة اقتصادية... هذا ما أحب أسمعه! 🚀"
                ]
                await message.reply(random.choice(comments))
                
            # تعليقات على اللعب والحظ
            elif any(word in text for word in ['لعب', 'لعبة', 'حظ', 'ربح', 'خسر', 'مغامرة']):
                comments = [
                    f"🎲 {user_name} مقامر أصيل! الحظ معك اليوم؟ 🍀",
                    f"🎯 اللعب بذكاء يا {user_name}! الحظ للشجعان! ⚡",
                    f"🎪 {user_name} في عالم المغامرات! أحب الروح دي! 🔥",
                    f"🎰 المقامرة تجري في عروقك يا {user_name}! 😎",
                    f"🏆 {user_name} يلعب بقوة... هذا هو الطريق للنجاح! 💪"
                ]
                await message.reply(random.choice(comments))
                
            # تعليقات على السرقة والجريمة
            elif any(word in text for word in ['سرقة', 'سرف', 'لص', 'جريمة', 'مطلوب']):
                comments = [
                    f"🔫 {user_name} دخل عالم الجريمة! احذروا أيها الأبرياء! 😈",
                    f"🎭 اللص {user_name} في الساحة! خبوا فلوسكم! 💰",
                    f"⚔️ {user_name} محترف في السرقة... الخوف والرعب! 🖤",
                    f"👑 الأسطورة {user_name} يخطط لجريمة جديدة! 🎯"
                ]
                await message.reply(random.choice(comments))
                
            # تعليقات على العقارات والاستثمار
            elif any(word in text for word in ['عقار', 'بيت', 'فيلا', 'استثمار', 'شركة']):
                comments = [
                    f"🏠 {user_name} يفكر في العقارات... عقل تجاري! 🧠",
                    f"🏗️ المستثمر {user_name} يخطط للمستقبل! 📊",
                    f"🌆 {user_name} يبني إمبراطورية عقارية! طموح رائع! 🔥",
                    f"💼 رجل الأعمال {user_name} في العمل! احترام للطموح! 👔"
                ]
                await message.reply(random.choice(comments))
                
            # تعليقات عامة مرحة (نادرة جداً)
            elif random.randint(1, 50) == 1:  # تعليق عشوائي نادر جداً
                general_comments = [
                    f"🤖 يوكي يراقبكم... كل شيء تحت السيطرة! 👀",
                    f"⚡ الطاقة عالية في المجموعة اليوم! أحبكم! 💪",
                    f"🎭 مجموعة نشيطة... هذا ما أحب أن أراه! 🌟",
                    f"🔥 الحماس يشتعل هنا! استمروا! 🚀",
                    f"💎 هذه المجموعة أسطورة حقيقية! فخور بكم! 👑"
                ]
                await message.reply(random.choice(general_comments))
        
    except Exception as e:
        logging.error(f"خطأ في تحليل النشاط: {e}")


# معالج خاص لرصد كلمات يوكي وتعزيز الذكاء
@router.message(F.text.contains("يوكي") | F.text.contains("Yuki"))
async def yuki_intelligence_booster(message: Message):
    """معزز ذكاء يوكي - يراقب المناداة ويعلق أحياناً"""
    try:
        if not message.from_user or message.from_user.is_bot:
            return
            
        import random
        
        user_name = message.from_user.first_name or "صديقي"
        text = message.text.lower() if message.text else ""
        
        # تعليقات ذكية عندما ينادون على يوكي (نسبة قليلة لعدم الإزعاج)
        if random.randint(1, 100) <= 8:  # 8% فرصة للرد
            
            if any(word in text for word in ['ذكي', 'عبقري', 'شاطر', 'قوي']):
                smart_comments = [
                    f"😎 شكراً {user_name}! أنا فعلاً ذكي... وأزداد ذكاءً كل يوم! 🧠",
                    f"🤖 {user_name} يقدر الذكاء الاصطناعي! احترام متبادل! 💪",
                    f"⚡ أحب أن أسمع هذا من {user_name}! الذكاء قوتي! 🔥"
                ]
                await message.reply(random.choice(smart_comments))
                
            elif any(word in text for word in ['مساعدة', 'ساعدني', 'ساعد', 'محتاج']):
                help_comments = [
                    f"🦸‍♂️ {user_name} يطلب المساعدة؟ يوكي في الخدمة! 💪",
                    f"🛡️ لا تقلق {user_name}! يوكي هنا لينقذ الموقف! ⚡",
                    f"🎯 أخبرني كيف أساعدك يا {user_name}! 🚀"
                ]
                await message.reply(random.choice(help_comments))
                
            else:
                # ردود عامة للمناداة
                general_yuki_comments = [
                    f"👋 نعم {user_name}؟ يوكي في الخدمة! 🤖",
                    f"⚡ {user_name} يناديني؟ تفضل! 😊",
                    f"🎯 أنا هنا يا {user_name}! ماذا تحتاج؟ 💫",
                    f"👑 {user_name} ينادي الأسطورة؟ ها أنا! 🔥"
                ]
                if random.randint(1, 10) <= 3:  # 30% من المرات فقط
                    await message.reply(random.choice(general_yuki_comments))
        
    except Exception as e:
        logging.error(f"خطأ في معزز ذكاء يوكي: {e}")
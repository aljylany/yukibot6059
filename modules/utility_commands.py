"""
أوامر مساعدة وأدوات عامة
Utility Commands and General Tools
"""

import logging
from aiogram.types import Message
from config.hierarchy import get_user_admin_level, get_admin_level_name, MASTERS


async def check_bot_permissions(message: Message):
    """فحص صلاحيات البوت في المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        bot_id = message.bot.id
        chat_id = message.chat.id
        
        # الحصول على معلومات البوت في المجموعة
        bot_member = await message.bot.get_chat_member(chat_id, bot_id)
        
        permissions_text = "🤖 **صلاحيات البوت في المجموعة**\n\n"
        permissions_text += f"📊 **النوع:** {bot_member.status}\n\n"
        
        if bot_member.status == 'administrator':
            permissions_text += "✅ **البوت مدير في المجموعة**\n\n"
            permissions_text += "🔑 **الصلاحيات المتاحة:**\n"
            
            # فحص الصلاحيات المختلفة
            permissions = [
                ("can_be_edited", "تعديل صلاحيات أخرى"),
                ("can_manage_chat", "إدارة المجموعة"),
                ("can_delete_messages", "حذف الرسائل"),
                ("can_manage_video_chats", "إدارة المكالمات المرئية"),
                ("can_restrict_members", "تقييد الأعضاء"),
                ("can_promote_members", "ترقية الأعضاء"),
                ("can_change_info", "تغيير معلومات المجموعة"),
                ("can_invite_users", "دعوة مستخدمين"),
                ("can_pin_messages", "تثبيت الرسائل"),
                ("can_manage_topics", "إدارة المواضيع")
            ]
            
            available_permissions = 0
            for perm_attr, perm_name in permissions:
                if hasattr(bot_member, perm_attr):
                    has_perm = getattr(bot_member, perm_attr)
                    status = "✅" if has_perm else "❌"
                    permissions_text += f"{status} {perm_name}\n"
                    if has_perm:
                        available_permissions += 1
            
            permissions_text += f"\n📈 **إجمالي الصلاحيات:** {available_permissions}/{len(permissions)}"
            
            if available_permissions < 5:
                permissions_text += "\n\n⚠️ **تحذير:** البوت يحتاج صلاحيات أكثر لتنفيذ جميع الأوامر بفعالية"
            
        else:
            permissions_text += "❌ **البوت ليس مديراً**\n"
            permissions_text += "💡 اجعل البوت مديراً لاستخدام الأوامر المتقدمة\n\n"
            permissions_text += "🔧 **الصلاحيات المطلوبة للأوامر المطلقة:**\n"
            permissions_text += "• حظر المستخدمين\n"
            permissions_text += "• حذف الرسائل\n"
            permissions_text += "• إدارة المجموعة\n"
            permissions_text += "• تقييد الأعضاء"
        
        await message.reply(permissions_text)
        
    except Exception as e:
        logging.error(f"خطأ في check_bot_permissions: {e}")
        await message.reply(f"❌ حدث خطأ أثناء فحص الصلاحيات: {str(e)[:100]}")


async def show_user_info(message: Message):
    """عرض معلومات المستخدم والمجموعة"""
    try:
        user = message.from_user
        chat = message.chat
        
        if not user:
            return
        
        # معلومات المستخدم
        info_text = f"👤 **معلومات المستخدم**\n\n"
        info_text += f"🏷️ **الاسم:** {user.first_name}"
        if user.last_name:
            info_text += f" {user.last_name}"
        info_text += f"\n🆔 **المعرف:** `{user.id}`"
        if user.username:
            info_text += f"\n📧 **اليوزر:** @{user.username}"
        
        # مستوى الإدارة
        if chat.type in ['group', 'supergroup']:
            admin_level = get_user_admin_level(user.id, chat.id)
            level_name = get_admin_level_name(admin_level)
            info_text += f"\n⭐ **المستوى الإداري:** {level_name}"
            
            # إضافة تمييز خاص للأسياد
            if user.id in MASTERS:
                info_text += " 👑"
        
        # معلومات المجموعة (إذا كانت مجموعة)
        if chat.type in ['group', 'supergroup']:
            info_text += f"\n\n🏠 **معلومات المجموعة**\n"
            info_text += f"📛 **الاسم:** {chat.title}\n"
            info_text += f"🆔 **المعرف:** `{chat.id}`\n"
            info_text += f"📊 **النوع:** {chat.type}"
            
            # عدد الأعضاء
            try:
                member_count = await message.bot.get_chat_member_count(chat.id)
                info_text += f"\n👥 **الأعضاء:** {member_count}"
            except:
                pass
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_user_info: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المعلومات")


async def show_target_user_info(message: Message):
    """عرض معلومات المستخدم المراد كشفه بالرد"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("❌ يرجى الرد على رسالة المستخدم المراد كشفه")
            return
        
        target_user = message.reply_to_message.from_user
        chat = message.chat
        
        # العنوان الرئيسي
        info_text = f"📋 **كشف معلومات المستخدم**\n\n"
        
        # معلومات المستخدم الأساسية
        info_text += f"👤 **الاسم:** {target_user.first_name}"
        if target_user.last_name:
            info_text += f" {target_user.last_name}"
        info_text += f"\n🆔 **معرف المستخدم:** `{target_user.id}`"
        if target_user.username:
            info_text += f"\n📧 **اليوزرنيم:** @{target_user.username}"
        
        # إذا كانت مجموعة، عرض الرتبة والمستوى الإداري
        if chat.type in ['group', 'supergroup']:
            admin_level = get_user_admin_level(target_user.id, chat.id)
            level_name = get_admin_level_name(admin_level)
            info_text += f"\n⭐ **الرتبة:** {level_name}"
            
            # الحصول على عدد رسائل المستخدم في المجموعة
            from database.operations import get_user_message_count
            message_count = await get_user_message_count(target_user.id, chat.id)
            info_text += f"\n📊 **عدد الرسائل:** {message_count}"
            
            # إضافة تمييز خاص للأسياد
            if target_user.id in MASTERS:
                info_text += "\n\n👑 **مستخدم مميز: السيد**"
        else:
            # في المحادثات الخاصة لا يمكن حساب الرسائل
            info_text += f"\n📊 **عدد الرسائل:** غير متوفر في المحادثات الخاصة"
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_target_user_info: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات المستخدم")


async def show_group_activity_ranking(message: Message):
    """عرض ترتيب تفاعل المجموعة حسب عدد الرسائل"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
            return
        
        from database.operations import get_group_message_ranking
        from utils.helpers import format_number
        
        # الحصول على أفضل 15 مستخدم
        ranking = await get_group_message_ranking(message.chat.id, 15)
        
        if not ranking:
            await message.reply("📊 **ترتيب التفاعل**\n\n❌ لا توجد بيانات تفاعل متاحة بعد!")
            return
        
        # بناء رسالة الترتيب
        activity_text = "📊 **ترتيب التفاعل في المجموعة**\n\n"
        
        medals = ["🥇", "🥈", "🥉"]
        
        for i, user_data in enumerate(ranking):
            rank = i + 1
            user_id = user_data.get('user_id')
            message_count = user_data.get('message_count', 0)
            first_name = user_data.get('first_name', 'مستخدم')
            username = user_data.get('username')
            
            # اختيار الأيقونة المناسبة
            if rank <= 3:
                icon = medals[rank - 1]
            elif rank <= 10:
                icon = "🔹"
            else:
                icon = "▫️"
            
            # تنسيق اسم المستخدم
            display_name = first_name[:15] if first_name else "مستخدم"
            if username:
                display_name += f" (@{username[:10]})"
            
            activity_text += f"{icon} **{rank}.** {display_name}\n"
            activity_text += f"    📨 **{format_number(message_count)}** رسالة\n\n"
        
        activity_text += "━━━━━━━━━━━━━━━━━━━━\n"
        activity_text += "💡 **للتحقق من تفاعلك:** اكتب `رسائلي`\n"
        activity_text += "👥 **للتحقق من تفاعل آخر:** ارد عليه واكتب `تفاعله`"
        
        await message.reply(activity_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض ترتيب التفاعل: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض ترتيب التفاعل")


async def show_my_messages_count(message: Message):
    """عرض عدد رسائل المستخدم الحالي"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
            return
        
        from database.operations import get_user_message_rank
        from utils.helpers import format_number
        
        user_count, user_rank = await get_user_message_rank(message.from_user.id, message.chat.id)
        
        user_name = message.from_user.first_name or "مستخدم"
        
        if user_count == 0:
            rank_text = "غير مرتب"
        else:
            rank_text = f"#{user_rank}"
        
        result_text = (
            f"📨 **رسائل {user_name}**\n\n"
            f"📊 **عدد الرسائل:** {format_number(user_count)}\n"
            f"🏆 **الترتيب:** {rank_text}\n\n"
            f"💡 **لرؤية ترتيب المجموعة:** اكتب `تفاعلي`"
        )
        
        await message.reply(result_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض عدد رسائل المستخدم: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض عدد الرسائل")


async def show_target_user_messages(message: Message):
    """عرض عدد رسائل المستخدم المحدد بالرد"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
            return
        
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("❌ قم بالرد على رسالة المستخدم المطلوب مع كتابة 'رسائله'")
            return
        
        from database.operations import get_user_message_rank
        from utils.helpers import format_number
        
        target_user = message.reply_to_message.from_user
        user_count, user_rank = await get_user_message_rank(target_user.id, message.chat.id)
        
        target_name = target_user.first_name or "مستخدم"
        
        if user_count == 0:
            rank_text = "غير مرتب"
        else:
            rank_text = f"#{user_rank}"
        
        result_text = (
            f"📨 **رسائل {target_name}**\n\n"
            f"📊 **عدد الرسائل:** {format_number(user_count)}\n"
            f"🏆 **الترتيب:** {rank_text}\n\n"
            f"💡 **لرؤية ترتيب المجموعة:** اكتب `تفاعلي`"
        )
        
        await message.reply(result_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض عدد رسائل المستخدم المحدد: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض عدد الرسائل")


async def show_target_user_activity(message: Message):
    """عرض تفاعل المستخدم المحدد بالرد"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط!")
            return
        
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("❌ قم بالرد على رسالة المستخدم المطلوب مع كتابة 'تفاعله'")
            return
        
        from database.operations import get_user_message_rank
        from utils.helpers import format_number
        
        target_user = message.reply_to_message.from_user
        user_count, user_rank = await get_user_message_rank(target_user.id, message.chat.id)
        
        target_name = target_user.first_name or "مستخدم"
        target_username = f"@{target_user.username}" if target_user.username else ""
        
        if user_count == 0:
            rank_text = "غير مرتب"
            activity_level = "🔇 خامل"
        else:
            rank_text = f"#{user_rank}"
            if user_count >= 100:
                activity_level = "🔥 نشط جداً"
            elif user_count >= 50:
                activity_level = "⚡ نشط"
            elif user_count >= 20:
                activity_level = "📈 متوسط النشاط"
            else:
                activity_level = "📊 نشاط قليل"
        
        result_text = (
            f"📊 **تفاعل {target_name}**\n\n"
            f"👤 **المستخدم:** {target_name} {target_username}\n"
            f"📨 **عدد الرسائل:** {format_number(user_count)}\n"
            f"🏆 **الترتيب:** {rank_text}\n"
            f"📈 **مستوى التفاعل:** {activity_level}\n\n"
            f"💡 **لرؤية ترتيب المجموعة:** اكتب `تفاعلي`"
        )
        
        await message.reply(result_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض تفاعل المستخدم المحدد: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض التفاعل")


async def show_help_command(message: Message):
    """عرض مساعدة أوامر النظام الإداري"""
    try:
        user_id = message.from_user.id if message.from_user else 0
        chat_id = message.chat.id if message.chat.type in ['group', 'supergroup'] else None
        
        admin_level = get_user_admin_level(user_id, chat_id)
        
        help_text = "📚 **دليل أوامر النظام الإداري**\n\n"
        
        # أوامر عامة للجميع
        help_text += "🔰 **أوامر عامة (للجميع):**\n"
        help_text += "• `معلوماتي` - عرض معلوماتك الشخصية\n"
        help_text += "• `صلاحيات البوت` - فحص صلاحيات البوت\n"
        help_text += "• `قائمة المديرين` - عرض مديرين المجموعة\n"
        help_text += "• `المساعدة الإدارية` - عرض هذه المساعدة\n\n"
        
        # أوامر المشرفين
        if admin_level.value >= 1:  # MODERATOR
            help_text += "👮‍♂️ **أوامر المشرفين:**\n"
            help_text += "• أوامر الإشراف الأساسية\n"
            help_text += "• كتم وإلغاء كتم الأعضاء\n"
            help_text += "• تحذير الأعضاء\n\n"
        
        # أوامر مالكي المجموعات
        if admin_level.value >= 2:  # GROUP_OWNER
            help_text += "🏆 **أوامر مالكي المجموعات:**\n"
            help_text += "• `ترقية مشرف` (رد على رسالة)\n"
            help_text += "• `تنزيل مشرف` (رد على رسالة)\n"
            help_text += "• حظر وإلغاء حظر الأعضاء\n"
            help_text += "• إعدادات المجموعة المتقدمة\n\n"
        
        # أوامر الأسياد
        if admin_level.value >= 3:  # MASTER
            help_text += "👑 **أوامر الأسياد المطلقة:**\n"
            help_text += "• `يوكي قم بإعادة التشغيل`\n"
            help_text += "• `يوكي قم بالتدمير الذاتي`\n"
            help_text += "• `يوكي قم بمغادرة المجموعة`\n"
            help_text += "• `يوكي رقي مالك مجموعة` (رد على رسالة)\n"
            help_text += "• `يوكي نزل مالك المجموعة` (رد على رسالة)\n"
            help_text += "• `الهيكل الإداري` - عرض التنظيم الكامل\n"
            help_text += "• `إلغاء` - إيقاف أي أمر مطلق أثناء العد التنازلي\n\n"
            help_text += "⚠️ **ملاحظة:** جميع الأوامر المطلقة لها عد تنازلي 15 ثانية\n"
        
        help_text += f"📊 **مستواك الحالي:** {get_admin_level_name(admin_level)}"
        if user_id in MASTERS:
            help_text += " 👑"
        
        await message.reply(help_text)
        
    except Exception as e:
        logging.error(f"خطأ في show_help_command: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض المساعدة")


async def islamic_quran(message: Message):
    """إرسال آية قرآنية عشوائية"""
    try:
        import random
        
        verses = [
            "﴿وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا وَيَرْزُقْهُ مِنْ حَيْثُ لَا يَحْتَسِبُ﴾ [سورة الطلاق: 2-3]",
            "﴿وَمَن يَتَوَكَّلْ عَلَى اللَّهِ فَهُوَ حَسْبُهُ إِنَّ اللَّهَ بَالِغُ أَمْرِهِ قَدْ جَعَلَ اللَّهُ لِكُلِّ شَيْءٍ قَدْرًا﴾ [سورة الطلاق: 3]",
            "﴿وَلَا تَيْأَسُوا مِن رَّوْحِ اللَّهِ إِنَّهُ لَا يَيْأَسُ مِن رَّوْحِ اللَّهِ إِلَّا الْقَوْمُ الْكَافِرُونَ﴾ [سورة يوسف: 87]",
            "﴿وَمَن صَبَرَ وَغَفَرَ إِنَّ ذَٰلِكَ لَمِنْ عَزْمِ الْأُمُورِ﴾ [سورة الشورى: 43]",
            "﴿وَلَئِن شَكَرْتُمْ لَأَزِيدَنَّكُمْ وَلَئِن كَفَرْتُمْ إِنَّ عَذَابِي لَشَدِيدٌ﴾ [سورة إبراهيم: 7]",
            "﴿فَاذْكُرُونِي أَذْكُرْكُمْ وَاشْكُرُوا لِي وَلَا تَكْفُرُونِ﴾ [سورة البقرة: 152]",
            "﴿إِنَّ مَعَ الْعُسْرِ يُسْرًا﴾ [سورة الشرح: 6]",
            "﴿وَمَن يُؤْمِن بِاللَّهِ يَهْدِ قَلْبَهُ وَاللَّهُ بِكُلِّ شَيْءٍ عَلِيمٌ﴾ [سورة التغابن: 11]",
            "﴿وَهُوَ الَّذِي يُنَزِّلُ الْغَيْثَ مِن بَعْدِ مَا قَنَطُوا وَيَنشُرُ رَحْمَتَهُ وَهُوَ الْوَلِيُّ الْحَمِيدُ﴾ [سورة الشورى: 28]",
            "﴿وَلَا تَحْزَنْ عَلَيْهِمْ وَلَا تَكُن فِي ضَيْقٍ مِّمَّا يَمْكُرُونَ﴾ [سورة النحل: 127]"
        ]
        
        verse = random.choice(verses)
        await message.reply(f"📖 آية كريمة:\n\n{verse}")
        
    except Exception as e:
        logging.error(f"خطأ في islamic_quran: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب الآية")


async def islamic_hadith(message: Message):
    """إرسال حديث نبوي شريف عشوائي"""
    try:
        import random
        
        hadiths = [
            "قال رسول الله ﷺ: \"إنما الأعمال بالنيات، وإنما لكل امرئ ما نوى\" (متفق عليه)",
            "قال رسول الله ﷺ: \"الدين النصيحة\" (رواه مسلم)",
            "قال رسول الله ﷺ: \"خير الناس أنفعهم للناس\" (رواه الطبراني)",
            "قال رسول الله ﷺ: \"المؤمن للمؤمن كالبنيان يشد بعضه بعضاً\" (متفق عليه)",
            "قال رسول الله ﷺ: \"من كان في حاجة أخيه كان الله في حاجته\" (متفق عليه)",
            "قال رسول الله ﷺ: \"لا يؤمن أحدكم حتى يحب لأخيه ما يحب لنفسه\" (متفق عليه)",
            "قال رسول الله ﷺ: \"إن الله كتب الإحسان على كل شيء\" (رواه مسلم)",
            "قال رسول الله ﷺ: \"اتق الله حيثما كنت\" (رواه الترمذي)",
            "قال رسول الله ﷺ: \"أحب الأعمال إلى الله أدومها وإن قل\" (متفق عليه)",
            "قال رسول الله ﷺ: \"من تواضع لله رفعه\" (رواه مسلم)"
        ]
        
        hadith = random.choice(hadiths)
        await message.reply(f"🌸 حديث شريف:\n\n{hadith}")
        
    except Exception as e:
        logging.error(f"خطأ في islamic_hadith: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب الحديث")


async def google_search(message: Message):
    """رابط للبحث في جوجل"""
    try:
        search_text = "🔍 **بحث جوجل**\n\n"
        search_text += "للبحث في جوجل، استخدم الرابط التالي:\n"
        search_text += "🌐 https://www.google.com\n\n"
        search_text += "💡 **نصيحة:** يمكنك البحث عن أي شيء تريده!"
        
        await message.reply(search_text)
        
    except Exception as e:
        logging.error(f"خطأ في google_search: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض رابط البحث")


async def who_added_me(message: Message):
    """معرفة من أضاف البوت للمجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        add_info = "👤 **معلومات إضافة البوت**\n\n"
        add_info += "🤖 تم إضافة البوت للمجموعة من قبل أحد المديرين\n"
        add_info += "📝 لمعرفة تفاصيل أكثر، تحقق من سجل المجموعة\n\n"
        add_info += "💡 **نصيحة:** المديرون فقط يمكنهم إضافة البوتات للمجموعات"
        
        await message.reply(add_info)
        
    except Exception as e:
        logging.error(f"خطأ في who_added_me: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات الإضافة")


async def send_message_private(message: Message):
    """إرسال رسالة خاصة (همسة)"""
    try:
        if not message.reply_to_message:
            await message.reply("❌ قم بالرد على رسالة الشخص المراد إرسال همسة له")
            return
        
        whisper_text = "💬 **همسة خاصة**\n\n"
        whisper_text += "🔒 هذه رسالة خاصة من "
        whisper_text += f"{message.from_user.first_name or 'مجهول'}\n\n"
        whisper_text += "📝 **الرسالة:** مرحباً! هذه همسة خاصة 💫\n\n"
        whisper_text += "💡 لإرسال همسة مخصصة، اكتب: همسة [النص]"
        
        await message.reply(whisper_text)
        
    except Exception as e:
        logging.error(f"خطأ في send_message_private: {e}")
        await message.reply("❌ حدث خطأ أثناء إرسال الهمسة")


async def clear_muted_users(message: Message):
    """مسح المكتومين"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        clear_text = "🧹 **مسح المكتومين**\n\n"
        clear_text += "⚠️ هذه الميزة تتطلب صلاحيات إدارية خاصة\n"
        clear_text += "🔧 حالياً غير متاحة، قد تتم إضافتها لاحقاً\n\n"
        clear_text += "💡 **بديل:** يمكن للمديرين إلغاء كتم الأعضاء يدوياً"
        
        await message.reply(clear_text)
        
    except Exception as e:
        logging.error(f"خطأ في clear_muted_users: {e}")
        await message.reply("❌ حدث خطأ أثناء مسح المكتومين")


async def get_group_link(message: Message):
    """الحصول على رابط المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        try:
            # محاولة الحصول على رابط دعوة المجموعة
            invite_link = await message.bot.export_chat_invite_link(message.chat.id)
            
            link_text = "🔗 **رابط المجموعة**\n\n"
            link_text += f"📝 **اسم المجموعة:** {message.chat.title or 'غير محدد'}\n"
            link_text += f"🔗 **الرابط:** {invite_link}\n\n"
            link_text += "💡 يمكنك مشاركة هذا الرابط لدعوة أشخاص جدد"
            
            await message.reply(link_text)
            
        except Exception as link_error:
            await message.reply("❌ لا يمكن الحصول على رابط المجموعة\n💡 تأكد من أن البوت لديه صلاحية إنشاء روابط دعوة")
        
    except Exception as e:
        logging.error(f"خطأ في get_group_link: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب رابط المجموعة")


async def add_group_link(message: Message):
    """إضافة رابط للمجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        add_link_text = "➕ **إضافة رابط للمجموعة**\n\n"
        add_link_text += "🔧 هذه الميزة تتطلب صلاحيات إدارية\n"
        add_link_text += "📝 يمكن للمديرين إنشاء رابط دعوة من إعدادات المجموعة\n\n"
        add_link_text += "💡 **خطوات الإضافة:**\n"
        add_link_text += "1. اذهب لإعدادات المجموعة\n"
        add_link_text += "2. اختر 'رابط الدعوة'\n"
        add_link_text += "3. انشئ رابط جديد أو استخدم الموجود"
        
        await message.reply(add_link_text)
        
    except Exception as e:
        logging.error(f"خطأ في add_group_link: {e}")
        await message.reply("❌ حدث خطأ أثناء إضافة الرابط")


async def convert_formats(message: Message):
    """زخرفة النصوص"""
    try:
        decoration_text = "✨ **زخرفة النصوص**\n\n"
        decoration_text += "🎨 **أنواع الزخرفة المتاحة:**\n"
        decoration_text += "• 𝓣𝓮𝔁𝓽 (خط مزخرف)\n"
        decoration_text += "• 𝕋𝕖𝕩𝕥 (خط عريض)\n"
        decoration_text += "• 𝑇𝑒𝑥𝑡 (خط مائل)\n"
        decoration_text += "• T⃣e⃣x⃣t⃣ (دوائر)\n\n"
        decoration_text += "💡 **للزخرفة:** اكتب زخرف [النص المراد زخرفته]\n"
        decoration_text += "مثال: زخرف مرحبا"
        
        await message.reply(decoration_text)
        
    except Exception as e:
        logging.error(f"خطأ في convert_formats: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض خيارات الزخرفة")


async def download_app(message: Message):
    """تحميل التطبيقات"""
    try:
        app_text = "📱 **تحميل التطبيقات**\n\n"
        app_text += "🔍 **متاجر التطبيقات الرسمية:**\n"
        app_text += "• 🍏 App Store (للآيفون)\n"
        app_text += "• 🤖 Google Play (للأندرويد)\n"
        app_text += "• 🪟 Microsoft Store (للويندوز)\n\n"
        app_text += "⚠️ **تحذير:** احذر من تحميل التطبيقات من مصادر غير موثوقة\n"
        app_text += "💡 استخدم المتاجر الرسمية لضمان الأمان"
        
        await message.reply(app_text)
        
    except Exception as e:
        logging.error(f"خطأ في download_app: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات التحميل")


async def download_game(message: Message):
    """تحميل الألعاب"""
    try:
        game_text = "🎮 **تحميل الألعاب**\n\n"
        game_text += "🕹️ **منصات الألعاب الشهيرة:**\n"
        game_text += "• 🎯 Steam (ألعاب الكمبيوتر)\n"
        game_text += "• 🎪 Epic Games (ألعاب مجانية)\n"
        game_text += "• 🍏 App Store (ألعاب الآيفون)\n"
        game_text += "• 🤖 Google Play Games (ألعاب الأندرويد)\n\n"
        game_text += "💡 **نصائح:**\n"
        game_text += "• تحقق من متطلبات التشغيل\n"
        game_text += "• اقرأ التقييمات قبل التحميل\n"
        game_text += "• احذر من الألعاب المدفوعة المقرصنة"
        
        await message.reply(game_text)
        
    except Exception as e:
        logging.error(f"خطأ في download_game: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات الألعاب")


async def get_bio(message: Message):
    """عرض البايو"""
    try:
        if not message.reply_to_message:
            # عرض بايو المستخدم نفسه
            user = message.from_user
            bio_text = f"📝 **بايو {user.first_name or 'المستخدم'}**\n\n"
            bio_text += f"👤 **الاسم:** {user.first_name}"
            if user.last_name:
                bio_text += f" {user.last_name}"
            bio_text += f"\n🆔 **المعرف:** `{user.id}`"
            if user.username:
                bio_text += f"\n📧 **اليوزرنيم:** @{user.username}"
            bio_text += "\n\n💡 للحصول على بايو شخص آخر، ارد على رسالته واكتب 'بايو'"
        else:
            # عرض بايو الشخص المرد عليه
            target_user = message.reply_to_message.from_user
            if not target_user:
                await message.reply("❌ لا يمكن الحصول على معلومات هذا المستخدم")
                return
            
            bio_text = f"📝 **بايو {target_user.first_name or 'المستخدم'}**\n\n"
            bio_text += f"👤 **الاسم:** {target_user.first_name}"
            if target_user.last_name:
                bio_text += f" {target_user.last_name}"
            bio_text += f"\n🆔 **المعرف:** `{target_user.id}`"
            if target_user.username:
                bio_text += f"\n📧 **اليوزرنيم:** @{target_user.username}"
        
        await message.reply(bio_text)
        
    except Exception as e:
        logging.error(f"خطأ في get_bio: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض البايو")


async def create_team(message: Message):
    """إنشاء فريق"""
    try:
        team_text = "👥 **إنشاء فريق**\n\n"
        team_text += "🔧 هذه الميزة قيد التطوير حالياً\n"
        team_text += "📝 **الميزات المخططة:**\n"
        team_text += "• إنشاء فرق للألعاب\n"
        team_text += "• دعوة الأعضاء للفريق\n"
        team_text += "• إدارة أنشطة الفريق\n"
        team_text += "• مسابقات بين الفرق\n\n"
        team_text += "🔔 ستتم إضافة هذه الميزة في التحديثات القادمة!"
        
        await message.reply(team_text)
        
    except Exception as e:
        logging.error(f"خطأ في create_team: {e}")
        await message.reply("❌ حدث خطأ أثناء عرض معلومات الفريق")


async def handle_utility_commands(message: Message) -> bool:
    """معالج الأوامر المساعدة"""
    if not message.text or not message.from_user:
        return False
    
    text = message.text.lower().strip()
    
    # أوامر الفحص والمعلومات
    if text in ['صلاحيات البوت', 'فحص البوت', 'bot permissions']:
        await check_bot_permissions(message)
        return True
    
    elif text in ['معلوماتي', 'my info', 'user info']:
        await show_user_info(message)
        return True
    
    elif text in ['المساعدة الإدارية', 'مساعدة النظام', 'admin help']:
        await show_help_command(message)
        return True
    
    # أوامر التفاعل والإحصائيات
    elif text in ['تفاعلي', 'ترتيب التفاعل', 'ترتيب المجموعة']:
        await show_group_activity_ranking(message)
        return True
    
    elif text in ['رسائلي', 'عدد رسائلي']:
        await show_my_messages_count(message)
        return True
    
    elif text in ['رسائله', 'عدد رسائله'] and message.reply_to_message:
        await show_target_user_messages(message)
        return True
    
    elif text in ['تفاعله', 'نشاطه'] and message.reply_to_message:
        await show_target_user_activity(message)
        return True
    
    # الأوامر الدينية
    elif text in ['آيه', 'ايه', 'آية', 'اية']:
        await islamic_quran(message)
        return True
    
    elif text in ['حديث', 'الحديث']:
        await islamic_hadith(message)
        return True
    
    # أوامر أخرى
    elif text in ['قوقل', 'جوجل', 'google']:
        await google_search(message)
        return True
    
    elif text in ['من ضافني', 'من اضافني', 'من أضافني']:
        await who_added_me(message)
        return True
    
    elif text in ['همسة', 'همسه']:
        await send_message_private(message)
        return True
    
    elif text in ['مسح المكتومين', 'مسح الكتم']:
        await clear_muted_users(message)
        return True
    
    elif text in ['الرابط', 'رابط المجموعة']:
        await get_group_link(message)
        return True
    
    elif text in ['اضف رابط', 'إضافة رابط']:
        await add_group_link(message)
        return True
    
    elif text in ['زخرف', 'زخرفة']:
        await convert_formats(message)
        return True
    
    elif text in ['تطبيق', 'تحميل تطبيق']:
        await download_app(message)
        return True
    
    elif text in ['تحميل لعبه', 'تحميل لعبة', 'لعبه', 'لعبة']:
        await download_game(message)
        return True
    
    elif text in ['بايو', 'البايو']:
        await get_bio(message)
        return True
    
    elif text in ['انشاء تيم', 'إنشاء تيم', 'انشئ تيم']:
        await create_team(message)
        return True
    
    # أوامر الاقتباسات والترفيه
    elif text in ['اقتباس', 'quote']:
        await send_quote(message)
        return True
    
    # أوامر إضافية
    elif text in ['ارسل']:
        await send_command(message)
        return True
    
    elif text in ['خروف']:
        await find_sheep(message)
        return True
    
    elif text.startswith('رفع '):
        await promote_user(message)
        return True
    
    return False


async def send_quote(message: Message):
    """إرسال اقتباس ملهم عشوائي"""
    try:
        import random
        
        quotes = [
            "💭 التغيير صعب في البداية، فوضوي في المنتصف، جميل في النهاية.",
            "🌟 النجاح ليس نهائياً، والفشل ليس قاتلاً، إنما الشجاعة للمتابعة هي ما يهم.",
            "⭐ لا تنتظر اللحظة المثالية، خذ اللحظة واجعلها مثالية.",
            "🎯 كل خطوة تخطوها إلى الأمام تجعلك أقرب إلى هدفك.",
            "💪 القوة لا تأتي من القدرة الجسدية، بل من الإرادة التي لا تقهر.",
            "🌈 بعد كل عاصفة تأتي قوس قزح.",
            "🔥 الأحلام لا تنتهي صلاحيتها، ابدأ من حيث أنت.",
            "💎 الضغط يصنع الماس، والتحديات تصنع الأبطال.",
            "🌱 كل يوم هو فرصة جديدة لتصبح أفضل مما كنت عليه أمس.",
            "✨ أنت أقوى مما تتخيل وأقدر مما تعتقد."
        ]
        
        quote = random.choice(quotes)
        await message.reply(quote)
        
    except Exception as e:
        logging.error(f"خطأ في send_quote: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب الاقتباس")


async def send_command(message: Message):
    """أمر الإرسال العشوائي"""
    try:
        import random
        
        send_responses = [
            "📤 تم إرسال الرسالة بنجاح!",
            "✅ وصلت الرسالة للمستقبل!",
            "📨 تم التسليم بأمان!",
            "📬 الرسالة في الطريق!",
            "💌 رسالة خاصة تم إرسالها!",
            "📮 تم الإرسال عبر البوت السريع!",
            "🚀 انطلقت الرسالة بسرعة الضوء!",
            "📧 تم التوصيل الفوري!"
        ]
        
        response = random.choice(send_responses)
        await message.reply(response)
        
    except Exception as e:
        logging.error(f"خطأ في send_command: {e}")
        await message.reply("❌ حدث خطأ أثناء الإرسال")


async def find_sheep(message: Message):
    """البحث عن الخروف في المجموعة"""
    try:
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ هذا الأمر يعمل في المجموعات فقط")
            return
        
        import random
        
        sheep_responses = [
            "🐑 لا يوجد خروف في المجموعة",
            "🐏 تم العثور على خروف بري! اهربوا!",
            "🐑 الخروف مختبئ في مكان سري",
            "🐏 خروف ذكي هرب من المجموعة",
            "🐑 يبدو أن الخروف نائم",
            "🐏 الخروف يلعب مع الأغنام",
            "🐑 خروف مفقود! هل رأيتموه؟",
            "🐏 وجدت خروف... لا، إنه مجرد عضو عادي!"
        ]
        
        # أحياناً نشير لعضو عشوائي بطريقة مرحة
        if random.randint(1, 100) <= 30:  # 30% احتمالية
            response = random.choice(sheep_responses)
        else:
            response = "🐑 لا يوجد خروف في المجموعة"
        
        await message.reply(response)
        
    except Exception as e:
        logging.error(f"خطأ في find_sheep: {e}")
        await message.reply("❌ حدث خطأ أثناء البحث عن الخروف")


async def promote_user(message: Message):
    """رفع المستخدم (ترقية)"""
    try:
        # استخراج نوع الترقية من النص
        text = message.text.lower().strip()
        
        if not message.reply_to_message:
            await message.reply("❌ قم بالرد على رسالة الشخص المراد ترقيته\n💡 مثال: رفع مشرف")
            return
        
        # أنواع الترقية المختلفة
        promotion_types = {
            'مشرف': 'مشرف',
            'مميز': 'مميز', 
            'vip': 'مميز',
            'هطف': 'هطف'  # ترقية خاصة مرحة
        }
        
        # البحث عن نوع الترقية
        promotion_type = None
        for key, value in promotion_types.items():
            if key in text:
                promotion_type = value
                break
        
        if not promotion_type:
            await message.reply(
                "❌ يرجى تحديد نوع الترقية\n\n"
                "💡 **الأنواع المتاحة:**\n"
                "• رفع مشرف\n"
                "• رفع مميز\n" 
                "• رفع هطف (ترقية مرحة)\n\n"
                "⚠️ **ملاحظة:** هذه ترقيات رمزية للتسلية فقط"
            )
            return
        
        target_user = message.reply_to_message.from_user
        if not target_user:
            await message.reply("❌ لا يمكن الحصول على معلومات المستخدم")
            return
        
        target_name = target_user.first_name or "المستخدم"
        
        # رسائل الترقية حسب النوع
        if promotion_type == 'مشرف':
            promo_text = f"🎖️ **تم رفع {target_name} إلى رتبة مشرف!**\n\n"
            promo_text += "👮‍♂️ **الصلاحيات الجديدة:**\n"
            promo_text += "• إشراف على المحادثات\n"
            promo_text += "• مراقبة النشاط\n"
            promo_text += "• المساعدة في الإدارة\n\n"
            promo_text += "🎉 مبارك الترقية!"
            
        elif promotion_type == 'مميز':
            promo_text = f"⭐ **تم رفع {target_name} إلى رتبة مميز!**\n\n"
            promo_text += "💎 **المزايا الجديدة:**\n"
            promo_text += "• عضوية مميزة\n"
            promo_text += "• أولوية في الخدمات\n"
            promo_text += "• مزايا خاصة\n\n"
            promo_text += "✨ مبارك التميز!"
            
        elif promotion_type == 'هطف':
            promo_text = f"🤪 **تم رفع {target_name} إلى رتبة هطف!**\n\n"
            promo_text += "😂 **المزايا الكوميدية:**\n"
            promo_text += "• حق التهطيف الرسمي\n"
            promo_text += "• صنع النكات السيئة\n"
            promo_text += "• إضحاك المجموعة\n\n"
            promo_text += "🎭 مبارك الهطفة الجديدة!"
        
        await message.reply(promo_text)
        
    except Exception as e:
        logging.error(f"خطأ في promote_user: {e}")
        await message.reply("❌ حدث خطأ أثناء الترقية")
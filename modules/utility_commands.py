"""
أوامر الخدمات والأدوات
Utility and Service Commands Module
"""

import logging
import random
from aiogram.types import Message
from config.database import get_database_connection


async def who_added_me(message: Message):
    """معرفة من أضافك للمجموعة"""
    try:
        # في البوتات العادية، هذه المعلومة غير متاحة
        # لكن يمكننا تقديم رد توضيحي
        await message.reply("""
ℹ️ **معلومات عضويتك في المجموعة:**

📝 للأسف، لا يمكنني معرفة من قام بإضافتك بالضبط، لكن يمكنك:

🔍 **طرق معرفة من أضافك:**
• تحقق من رسائل المجموعة القديمة
• اسأل الإدارة في المجموعة
• تحقق من سجل الأنشطة (إذا كان متاحاً)

💡 **نصيحة:** عادة ما يظهر في المجموعات رسالة عند إضافة عضو جديد
        """)
    except Exception as e:
        logging.error(f"خطأ في أمر من ضافني: {e}")


async def get_bio(message: Message):
    """عرض البايو للشخص المرد عليه"""
    try:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            await message.reply("❌ يجب الرد على رسالة شخص لعرض بايو حسابه")
            return
            
        user = message.reply_to_message.from_user
        bio_text = f"""
👤 **معلومات المستخدم:**

🏷️ **الاسم:** {user.first_name}
{f"📝 **اسم المستخدم:** @{user.username}" if user.username else "❌ **اسم المستخدم:** غير متوفر"}
🆔 **الايدي:** `{user.id}`
🤖 **نوع الحساب:** {'بوت' if user.is_bot else 'مستخدم عادي'}

ℹ️ **ملاحظة:** البايو الشخصي غير متاح للبوتات
        """
        await message.reply(bio_text)
        
    except Exception as e:
        logging.error(f"خطأ في عرض البايو: {e}")
        await message.reply("❌ حدث خطأ أثناء جلب معلومات المستخدم")


async def google_search(message: Message, query: str):
    """البحث في جوجل"""
    try:
        # بدلاً من البحث الفعلي، نوفر رابط بحث
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        
        search_text = f"""
🔍 **نتائج البحث عن:** `{query}`

🌐 [اضغط هنا للبحث في جوجل]({search_url})

💡 **اقتراحات للبحث الأفضل:**
• استخدم كلمات مفتاحية واضحة
• ضع الجمل في علامات اقتباس للبحث الدقيق
• استخدم علامة + بين الكلمات للبحث عن جميعها
        """
        await message.reply(search_text, disable_web_page_preview=False)
        
    except Exception as e:
        logging.error(f"خطأ في البحث في جوجل: {e}")


async def download_app(message: Message, app_name: str):
    """تحميل التطبيقات"""
    try:
        search_text = f"""
📱 **البحث عن تطبيق:** `{app_name}`

🔗 **مصادر التحميل:**

**📱 للأندرويد:**
• [Google Play Store](https://play.google.com/store/search?q={app_name.replace(' ', '+')})
• [APKPure](https://apkpure.com/search?q={app_name.replace(' ', '+')})

**🍎 للآيفون:**
• [App Store](https://apps.apple.com/search?term={app_name.replace(' ', '+')})

⚠️ **تحذير:** تأكد من تحميل التطبيقات من مصادر موثوقة فقط
        """
        await message.reply(search_text, disable_web_page_preview=False)
        
    except Exception as e:
        logging.error(f"خطأ في تحميل التطبيق: {e}")


async def download_game(message: Message, game_name: str):
    """تحميل الألعاب"""
    try:
        search_text = f"""
🎮 **البحث عن لعبة:** `{game_name}`

🔗 **مصادر التحميل:**

**🎮 للكمبيوتر:**
• [Steam](https://store.steampowered.com/search/?term={game_name.replace(' ', '+')})
• [Epic Games](https://www.epicgames.com/store)

**📱 للهاتف:**
• [Google Play Games](https://play.google.com/store/search?q={game_name.replace(' ', '+')}&c=games)
• [App Store Games](https://apps.apple.com/search?term={game_name.replace(' ', '+')})

🆓 **ألعاب مجانية:**
• تحقق من قسم الألعاب المجانية في كل متجر
        """
        await message.reply(search_text, disable_web_page_preview=False)
        
    except Exception as e:
        logging.error(f"خطأ في تحميل اللعبة: {e}")


async def islamic_quran(message: Message):
    """آية قرآنية عشوائية"""
    try:
        # آيات قرآنية مختارة
        verses = [
            "وَمَن يَتَّقِ اللَّهَ يَجْعَل لَّهُ مَخْرَجًا • وَيَرْزُقْهُ مِنْ حَيْثُ لَا يَحْتَسِبُ",
            "إِنَّ مَعَ الْعُسْرِ يُسْرًا",
            "وَلَا تَيْأَسُوا مِن رَّوْحِ اللَّهِ ۖ إِنَّهُ لَا يَيْأَسُ مِن رَّوْحِ اللَّهِ إِلَّا الْقَوْمُ الْكَافِرُونَ",
            "رَبَّنَا آتِنَا فِي الدُّنْيَا حَسَنَةً وَفِي الْآخِرَةِ حَسَنَةً وَقِنَا عَذَابَ النَّارِ",
            "وَمَن يَعْمَلْ مِثْقَالَ ذَرَّةٍ خَيْرًا يَرَهُ"
        ]
        
        verse = random.choice(verses)
        await message.reply(f"📖 **آية كريمة:**\n\n{verse}")
        
    except Exception as e:
        logging.error(f"خطأ في عرض الآية: {e}")


async def islamic_hadith(message: Message):
    """حديث شريف عشوائي"""
    try:
        hadiths = [
            "قال رسول الله ﷺ: \"إنما الأعمال بالنيات\"",
            "قال رسول الله ﷺ: \"الدين النصيحة\"",
            "قال رسول الله ﷺ: \"خير الناس أنفعهم للناس\"",
            "قال رسول الله ﷺ: \"المؤمن للمؤمن كالبنيان يشد بعضه بعضاً\"",
            "قال رسول الله ﷺ: \"من كان في حاجة أخيه كان الله في حاجته\""
        ]
        
        hadith = random.choice(hadiths)
        await message.reply(f"🕌 **حديث شريف:**\n\n{hadith}")
        
    except Exception as e:
        logging.error(f"خطأ في عرض الحديث: {e}")


async def islamic_dhikr(message: Message):
    """ذكر إسلامي"""
    try:
        dhikr_list = [
            "سبحان الله وبحمده، سبحان الله العظيم",
            "لا إله إلا الله وحده لا شريك له، له الملك وله الحمد وهو على كل شيء قدير",
            "اللهم صل وسلم وبارك على نبينا محمد",
            "أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه",
            "حسبنا الله ونعم الوكيل"
        ]
        
        dhikr = random.choice(dhikr_list)
        await message.reply(f"📿 **ذكر شريف:**\n\n{dhikr}")
        
    except Exception as e:
        logging.error(f"خطأ في عرض الذكر: {e}")


async def send_message_private(message: Message, username: str, text: str):
    """إرسال رسالة خاصة (زاجل)"""
    try:
        # في البوتات العادية، لا يمكن إرسال رسائل لمستخدمين لم يبدؤوا محادثة
        await message.reply(f"""
📨 **خدمة الزاجل:**

❌ **لا يمكن إرسال الرسالة إلى @{username}**

📝 **السبب:**
البوتات في تيليجرام لا تستطيع إرسال رسائل للمستخدمين إلا إذا بدؤوا محادثة مع البوت أولاً.

💡 **الحل:**
اطلب من @{username} أن يرسل /start للبوت في الخاص أولاً.

📱 **الرسالة المطلوب إرسالها:**
`{text}`
        """)
        
    except Exception as e:
        logging.error(f"خطأ في الزاجل: {e}")


async def disturb_user(message: Message, username: str = None):
    """صيح - إزعاج المستخدم"""
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user = message.reply_to_message.from_user
            name = target_user.first_name
        elif username:
            name = username
        else:
            await message.reply("❌ يجب الرد على رسالة أو كتابة اسم المستخدم")
            return
            
        await message.reply(f"""
📢 **تم إرسال صيحة إلى {name}!**

🔊 مايكي يصيح: "استيقظ يا {name}! هناك من يناديك في المجموعة!"

⚠️ **ملاحظة:** هذه مجرد رسالة تفاعلية، لا يتم إرسال إشعارات فعلية.
        """)
        
    except Exception as e:
        logging.error(f"خطأ في الصيحة: {e}")


async def my_similar_gender(message: Message, gender: str):
    """شبيهي/شبيهتي حسب الجنس"""
    try:
        if gender == "male":
            names = [
                "أحمد محمد", "محمد علي", "خالد حسن", "عمر سالم", "يوسف أحمد",
                "حسام الدين", "طارق محمود", "سامر نادر", "فادي جمال", "رامي حسين"
            ]
        else:
            names = [
                "فاطمة أحمد", "عائشة محمد", "نور الهدى", "سارة علي", "مريم حسان",
                "زينب خالد", "هدى محمود", "ريم سالم", "نادية حسن", "ليلى عمر"
            ]
            
        similar = random.choice(names)
        gender_text = "شبيهك" if gender == "male" else "شبيهتك"
        await message.reply(f"👥 {gender_text} هو/هي: {similar}")
        
    except Exception as e:
        logging.error(f"خطأ في الشبيه: {e}")


async def convert_formats(message: Message):
    """تحويل الصيغ"""
    try:
        if not message.reply_to_message:
            await message.reply("""
🔄 **خدمة تحويل الصيغ:**

📝 **كيفية الاستخدام:**
• رد على فيديو واكتب "تحويل"
• رد على صوت واكتب "تحويل" 
• رد على صورة واكتب "تحويل"

🎯 **الصيغ المدعومة:**
• فيديو → صوت
• صوت → بصمة
• صورة → ملصق
• GIF → فيديو

⚠️ **ملاحظة:** هذه الخدمة تتطلب معالجة خاصة وقد لا تكون متاحة حالياً
            """)
            return
            
        file_type = "غير معروف"
        if message.reply_to_message.video:
            file_type = "فيديو"
        elif message.reply_to_message.audio or message.reply_to_message.voice:
            file_type = "صوت"
        elif message.reply_to_message.photo:
            file_type = "صورة"
        elif message.reply_to_message.animation:
            file_type = "متحركة"
            
        await message.reply(f"🔄 تم استلام {file_type} للتحويل...\n⚠️ خدمة التحويل قيد التطوير")
        
    except Exception as e:
        logging.error(f"خطأ في تحويل الصيغ: {e}")


async def create_team(message: Message, team_name: str):
    """إنشاء تيم جديد"""
    try:
        async with get_database_connection() as db:
            # التحقق من وجود التيم
            existing = await db.execute("""
                SELECT id FROM teams WHERE leader_id = ? AND chat_id = ?
            """, (message.from_user.id, message.chat.id))
            
            if await existing.fetchone():
                await message.reply("❌ لديك تيم بالفعل! استخدم 'حذف التيم' أولاً")
                return
                
            # إنشاء التيم الجديد
            team_code = f"T{random.randint(1000, 9999)}"
            await db.execute("""
                INSERT INTO teams (team_name, team_code, leader_id, chat_id, members_count, points, level)
                VALUES (?, ?, ?, ?, 1, 0, 1)
            """, (team_name, team_code, message.from_user.id, message.chat.id))
            
            # إضافة القائد كعضو
            await db.execute("""
                INSERT INTO team_members (team_code, user_id, chat_id, joined_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (team_code, message.from_user.id, message.chat.id))
            
            await db.commit()
            
        await message.reply(f"""
🎉 **تم إنشاء التيم بنجاح!**

📋 **معلومات التيم:**
• 🏷️ الاسم: {team_name}
• 🔑 الكود: `{team_code}`
• 👑 القائد: {message.from_user.first_name}
• 👥 الأعضاء: 1/20
• ⭐ النقاط: 0
• 🏆 المستوى: 1

💡 **لدعوة الأعضاء:** شارك الكود `{team_code}` معهم
        """)
        
    except Exception as e:
        logging.error(f"خطأ في إنشاء التيم: {e}")
        await message.reply("❌ حدث خطأ أثناء إنشاء التيم")


async def join_team(message: Message, team_code: str):
    """الانضمام لتيم"""
    try:
        async with get_database_connection() as db:
            # التحقق من وجود التيم
            team = await db.execute("""
                SELECT team_name, members_count FROM teams WHERE team_code = ?
            """, (team_code,))
            team_data = await team.fetchone()
            
            if not team_data:
                await message.reply("❌ كود التيم غير صحيح")
                return
                
            if team_data[1] >= 20:
                await message.reply("❌ التيم ممتلئ (20/20 عضو)")
                return
                
            # التحقق من عدم انضمام المستخدم لتيم آخر
            existing = await db.execute("""
                SELECT team_code FROM team_members WHERE user_id = ? AND chat_id = ?
            """, (message.from_user.id, message.chat.id))
            
            if await existing.fetchone():
                await message.reply("❌ أنت عضو في تيم بالفعل! استخدم 'خروج من التيم' أولاً")
                return
                
            # إضافة العضو للتيم
            await db.execute("""
                INSERT INTO team_members (team_code, user_id, chat_id, joined_at)
                VALUES (?, ?, ?, datetime('now'))
            """, (team_code, message.from_user.id, message.chat.id))
            
            # تحديث عدد الأعضاء
            await db.execute("""
                UPDATE teams SET members_count = members_count + 1 WHERE team_code = ?
            """, (team_code,))
            
            await db.commit()
            
        await message.reply(f"""
✅ **تم الانضمام للتيم بنجاح!**

🎉 مرحباً بك في تيم: **{team_data[0]}**
👥 أنت العضو رقم: {team_data[1] + 1}

🎯 **الآن يمكنك:**
• المشاركة في مهام التيم
• كسب نقاط للتيم
• المشاركة في الهجمات والدفاع
        """)
        
    except Exception as e:
        logging.error(f"خطأ في الانضمام للتيم: {e}")
        await message.reply("❌ حدث خطأ أثناء الانضمام للتيم")
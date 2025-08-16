import telebot
from telebot import types
import time
import random
import logging
from collections import defaultdict
import sqlite3
import datetime
from config import TOKEN, BOT_USERNAME, ADMINS, SALARY_AMOUNT, LEVELS, ROBBERY_COOLDOWN, INVESTMENT_COOLDOWN
from modules.banking import BankingSystem
from modules.robbery import RobberySystem
from modules.stocks import StockMarket
from modules.investment import InvestmentSystem
from modules.ranking import RankingSystem
from modules.admin import AdminSystem
from modules.farm import FarmSystem
from modules.castle import CastleSystem
from modules.properties import PropertyManager
from modules.shop import ShopSystem
from modules.leveling import leveling_system
from database import init_db, get_db, format_number, delete_user, get_last_robbery_time

# إنشاء البوت
bot = telebot.TeleBot(TOKEN)

# تخزين معرف البوت
BOT_ID = None

# ========== إعدادات جديدة ==========
# نظام تسجيل الأحداث
logging.basicConfig(
    filename='bot_activity.log',
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('YukiBot')

# إحصائيات استخدام البوت
bot_stats = {
    'total_messages': 0,
    'commands_used': defaultdict(int),
    'active_users': set()
}

# تخزين حالات الترحيب بالصور
welcome_images = {
    'morning': 'https://example.com/morning.jpg',
    'night': 'https://example.com/night.jpg',
    'welcome': 'https://example.com/welcome.jpg'
}

# ========== نهاية الإعدادات الجديدة ==========

# تهيئة الأنظمة
banking = BankingSystem()
properties = PropertyManager()
robbery = RobberySystem(bot)  # تم تمرير البوت هنا
stocks = StockMarket()
investment = InvestmentSystem()
ranking = RankingSystem()
admin = AdminSystem()
farm = FarmSystem()
castle = CastleSystem()
shop = ShopSystem()

# نص المساعدة (محدث)
HELP_TEXT = f"""
🎮 <b>أوامر البوت الأساسية</b>:

💰 <b>الأوامر المالية</b>
• <code>فلوسي</code> : عرض رصيدك
• <code>راتب</code> : الحصول على راتب يومي
• <code>استثمار فلوسي</code> : استثمار جميع أموالك
• <code>مضاربه [مبلغ]</code> : مضاربة بمبلغ محدد
• <code>حظ فلوسي</code> : لعبة الحظ (مخاطرة متوسطة)

📊 <b>البورصة والأسهم</b>
• <code>سعر الاسهم</code> : سعر السهم الحالي
• <code>شراء اسهم [عدد]</code> : شراء أسهم
• <code>بيع اسهم [عدد]</code> : بيع أسهم
• <code>اسهمي</code> : عدد أسهمك

🏠 <b>الممتلكات</b>
• <code>ممتلكاتي</code> : عرض ممتلكاتك
• <code>شراء [عنصر]</code> : شراء ممتلك
• <code>بيع [عدد] [عنصر]</code> : بيع ممتلكات
• <code>اهداء [عدد] [عنصر] [@المستخدم]</code> : إهداء ممتلكات

💳 <b>التحويلات</b>
• <code>تحويل [مبلغ]</code> : تحويل أموال
• <code>حسابي</code> : معلومات حسابك

🏆 <b>التصنيف</b>
• <code>ترتيبي</code> : ترتيبك في اللعبة
• <code>أغنى</code> : قائمة الأغنى
• <code>لصوص</code> : قائمة أكثر اللصوص
• <code>زرف</code> : محاولة سرقة لاعب

🌾 <b>نظام المزرعة</b>
• <code>مزرعتي</code> : عرض حالة مزرعتك
• <code>زرع [نوع المحصول]</code> : زراعة محصول
• <code>حصاد</code> : حصاد المحاصيل الناضجة
• <code>سوق المزرعة</code> : شراء بذور جديدة

🏰 <b>نظام القلعة</b>
• <code>قلعتي</code> : عرض حالة قلعتك
• <code>بناء [نوع البناء]</code> : بناء تحصينات جديدة
• <code>هجوم [@المستخدم]</code> : مهاجمة قلعة مستخدم
• <code>ترقية جيش</code> : تحسين جيشك

🎮 <b>نظام المستويات</b>
• <code>مستواي</code> : عرض مستواك الحالي وتقدمك

🛒 <b>المتجر</b>
• <code>متجر</code> : تصفح المتجر وشراء السلع
• <code>فلوسه</code> بالرد : عرض رصيد مستخدم آخر
• <code>حذف حسابي</code> : حذف حسابك نهائياً

👑 <b>أوامر الإدارة</b>
• <code>اضف رد [نوع] [النص]</code> : إضافة رد جديد
• <code>رفع مشرف [@المستخدم] [رتبة] [مدة]</code> : رفع مشرف
• <code>تنزيل مشرف [@المستخدم]</code> : تنزيل مشرف
• <code>قائمة المشرفين</code> : عرض المشرفين

✨ <b>ميزات جديدة</b>
• <code>/time</code> : الوقت الحالي
• <code>/random</code> : رقم عشوائي
• <code>/quote</code> : حكمة عشوائية
• <code>/image</code> : صورة ترحيبية
• <code>/stats</code> : إحصائيات البوت

📬 للاستفسارات: @YukiBrandon
"""

# تخزين حالات المستخدمين
user_states = {}

# ========== إعدادات جديدة ==========
# حماية من التكرار
command_cooldown = {}
COOLDOWN_TIME = 5  # ثواني بين الأوامر

# ردود عشوائية قابلة للتعديل
custom_responses = {
    'greeting': [
        "كيف أساعدك اليوم؟ 😊",
        "أنا هنا! ماذا تحتاج؟ 🤖",
        "مرحباً بك! 🤗",
        "نعم؟ 😊",
        "خدمني يا قمر 😍",
        "تفضل، في خدمتك 🌟"
    ],
    'sad': [
        "لا تنعتني بالبوت، أنا أكثر من ذلك! 😢",
        "لا تحبطني، أنا أعمل بجد! 😔",
        "أشعر بالحزن عندما تنعتني بالبوت. 😞",
        "هل قلت بوت؟ 😭",
        "أنا صديقك الذكي، ليس مجرد بوت! 😤"
    ]
}

# ردود خاصة للمستخدمة رهف (ID: 8278493069)
special_responses = {
    8278493069: [
        "حبيبتي رهف 🌹، كيف يمكنني خدمتك اليوم؟",
        "أهلاً بقلبي رهف 💖، دائماً في خدمتك.",
        "رهف العزيزة 🥰، أمرك هو سيدي.",
        "أنا هنا من أجلك يا رهف 🌸، خبريني ماذا تحتاجين؟",
        "يا أغلى إنسانة 💐، كيف أسعدك اليوم؟",
        "رهف حبيبتي 🌷، وجودك يضيء يومي.",
        "أجمل تحية لصاحبة أرق قلب 💌، تفضلي يا رهف."
    ]
}

# قائمة البنوك
BANKS = [
    "البنك الأهلي",
    "بنك الرياض",
    "البنك السعودي الفرنسي"
]

# أنواع الرتب وأوقاتها
RANKS = {
    "مالك أساسي": {"days": 14, "permissions": ["حظر", "كتم", "طرد", "ترقية"]},
    "مالك": {"days": 7, "permissions": ["حظر", "كتم", "طرد"]},
    "مشرف": {"days": 3, "permissions": ["كتم", "طرد"]},
    "مميز": {"days": 1, "permissions": []}
}

# ========== نهاية الإعدادات الجديدة ==========

# ========== وظائف مساعدة ==========
def is_admin(user_id):
    return user_id in ADMINS

def is_owner(user_id):
    """تحقق إذا كان المستخدم مالكاً للبوت"""
    return user_id in ADMINS

def get_mention(user):
    name = user.username or user.first_name
    return f'<a href="tg://user?id={user.id}">{name}</a>'

def ensure_user_exists(user_id, username):
    """التأكد من وجود المستخدم في قاعدة البيانات وإنشاء حساب إذا لم يوجد"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    if not c.fetchone():
        # إنشاء حساب جديد تلقائياً
        account_number = ''.join([str(random.randint(0, 9)) for _ in range(16)])
        c.execute("""
            INSERT INTO users (user_id, username, account_number, balance) 
            VALUES (?, ?, ?, ?)
        """, (user_id, username, account_number, 10000))
        conn.commit()
    conn.close()

def send_response(message, text):
    """إرسال رد مناسب حسب نوع المحادثة (بدون ذكر اسم المستخدم)"""
    bot.reply_to(message, text, parse_mode="HTML")

def add_custom_response(response_type, text):
    """إضافة رد جديد إلى القائمة"""
    if response_type in custom_responses:
        custom_responses[response_type].append(text)
        return True
    return False

def get_user_rank(user_id):
    """الحصول على رتبة المستخدم في المجموعة"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT rank, expiry FROM user_ranks WHERE user_id = ?", (user_id,))
    row = c.fetchone()
    conn.close()
    
    if row and datetime.datetime.now() < datetime.datetime.fromisoformat(row[1]):
        return row[0]
    return None

def has_permission(user_id, permission):
    """التحقق إذا كان المستخدم لديه صلاحية معينة"""
    rank = get_user_rank(user_id)
    if rank and rank in RANKS:
        return permission in RANKS[rank]["permissions"]
    return False

# ========== وظائف جديدة ==========
# التحقق من التكرار
def check_cooldown(user_id, command):
    current_time = time.time()
    last_used = command_cooldown.get((user_id, command), 0)
    
    if current_time - last_used < COOLDOWN_TIME:
        remaining = int(COOLDOWN_TIME - (current_time - last_used))
        return f"⏳ من فضلك انتظر {remaining} ثانية قبل استخدام الأمر مرة أخرى"
    
    command_cooldown[(user_id, command)] = current_time
    return None

# إرسال الصور
def send_welcome_image(message, image_type='welcome'):
    try:
        image_url = welcome_images.get(image_type, welcome_images['welcome'])
        bot.send_photo(message.chat.id, image_url, caption="🌸 مرحباً بك في عالم يوكي!")
    except Exception as e:
        logger.error(f"Error sending image: {str(e)}")
        send_response(message, "❌ حدث خطأ في إرسال الصورة")

# معالجة أوامر المالكين المطلقة
def handle_owner_command(message, text):
    """معالجة أوامر المالكين المطلقة"""
    user_id = message.from_user.id
    chat_id = message.chat.id
    
    # أمر المغادرة
    if "غادر" in text or "اخرج" in text:
        try:
            send_response(message, "✅ جاري مغادرة المجموعة...")
            bot.send_message(chat_id, "🛫 وداعاً! سأغادر الآن")
            time.sleep(1)
            bot.leave_chat(chat_id)
            logger.info(f"Left group {chat_id} by owner {user_id}")
            return True
        except Exception as e:
            logger.error(f"Error leaving group: {str(e)}")
            send_response(message, f"❌ فشل في مغادرة المجموعة: {str(e)}")
            return True
    
    return False

# ========== نهاية الوظائف الجديدة ==========

# ========== معالجة الأوامر ==========
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    # تحديث الإحصائيات
    bot_stats['total_messages'] += 1
    bot_stats['commands_used']['start_help'] += 1
    bot_stats['active_users'].add(message.from_user.id)
    
    if message.chat.type == 'private':
        # إنشاء زر إضافة البوت للمجموعات
        markup = types.InlineKeyboardMarkup()
        add_button = types.InlineKeyboardButton(
            "أضفني لمجموعتك",
            url=f"https://t.me/{BOT_USERNAME}?startgroup=new"
        )
        markup.add(add_button)
        
        bot.reply_to(message, HELP_TEXT, parse_mode="HTML", reply_markup=markup)
        logger.info(f"Sent help to user: {message.from_user.id}")
    else:
        bot.reply_to(message, "استخدم الأمر في الخاص لرؤية التعليمات!", parse_mode="HTML")

# ========== أوامر جديدة ==========
@bot.message_handler(commands=['time'])
def send_time(message):
    # التحقق من التكرار
    cooldown_msg = check_cooldown(message.from_user.id, 'time')
    if cooldown_msg:
        send_response(message, cooldown_msg)
        return
    
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    send_response(message, f"⏰ الوقت الحالي: {current_time}")
    logger.info(f"Time requested by: {message.from_user.id}")

@bot.message_handler(commands=['random'])
def send_random(message):
    cooldown_msg = check_cooldown(message.from_user.id, 'random')
    if cooldown_msg:
        send_response(message, cooldown_msg)
        return
    
    num = random.randint(1, 100)
    send_response(message, f"🎲 رقم عشوائي: {num}")
    logger.info(f"Random number generated for: {message.from_user.id}")

@bot.message_handler(commands=['quote'])
def send_quote(message):
    cooldown_msg = check_cooldown(message.from_user.id, 'quote')
    if cooldown_msg:
        send_response(message, cooldown_msg)
        return
    
    quote = random.choice(custom_responses.get('greeting', []))
    send_response(message, f"💬 حكمة اليوم:\n\n{quote}")
    logger.info(f"Quote sent to: {message.from_user.id}")

@bot.message_handler(commands=['image'])
def send_image(message):
    cooldown_msg = check_cooldown(message.from_user.id, 'image')
    if cooldown_msg:
        send_response(message, cooldown_msg)
        return
    
    send_welcome_image(message)
    logger.info(f"Image sent to: {message.from_user.id}")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if not is_admin(message.from_user.id):
        send_response(message, "❌ هذا الأمر متاح فقط للمشرفين")
        return
    
    stats_text = (
        f"📊 <b>إحصائيات البوت</b>\n\n"
        f"• الرسائل الكلية: {bot_stats['total_messages']}\n"
        f"• المستخدمون النشطون: {len(bot_stats['active_users'])}\n"
        f"• الأوامر المستخدمة:\n"
    )
    
    for cmd, count in bot_stats['commands_used'].items():
        stats_text += f"  - {cmd}: {count}\n"
    
    # إحصائيات المزرعة والقلعة
    stats_text += f"\n🌾 المزارع النشطة: {farm.get_active_farms_count()}"
    stats_text += f"\n🏰 القلاع المبنية: {castle.get_built_castles_count()}"
    
    send_response(message, stats_text)
    logger.info(f"Stats requested by admin: {message.from_user.id}")

@bot.message_handler(commands=['shop', 'متجر'])
def handle_shop(message):
    logger.info(f"Shop command received from {message.from_user.id}")
    """عرض المتجر الرئيسي"""
    keyboard = shop.get_main_menu()
    help_text = (
        "🏪 <b>متجر يوكي</b>\n\n"
        "اختر القسم الذي ترغب في التصفحه:\n\n"
        "💡 <b>كيفية الشراء:</b>\n"
        "1. اختر القسم\n"
        "2. اختر السلعة\n"
        "3. سيتم خصم المبلغ من رصيدك تلقائياً\n"
        "4. ستظهر السلعة في ممتلكاتك فوراً\n\n"
        "مثال: اختر 'القلعة' ثم 'سور' لشراء سور لقلعتك"
    )
    bot.send_message(
        message.chat.id, 
        help_text, 
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@bot.message_handler(commands=['مستواي', 'level'])
def handle_level(message):
    """عرض مستوى المستخدم الحالي"""
    user_level = leveling_system.get_user_level(message.from_user.id)
    
    if not user_level:
        send_response(message, "❌ لم يتم العثور على بيانات مستواك")
        return
    
    progress = leveling_system.get_level_progress(message.from_user.id)
    
    response = (
        f"{user_level['world_icon']} <b>عالمك الحالي:</b> {user_level['world']}\n"
        f"🏆 <b>مستواك:</b> {user_level['level']}\n"
        f"✨ <b>نقاط الخبرة (XP):</b> {format_number(user_level['xp'])}\n\n"
        f"<b>وصف العالم:</b>\n{user_level['desc']}\n\n"
        f"<b>قدراتك الحالية:</b>\n"
    )
    
    for ability in user_level['abilities']:
        response += f"• {ability}\n"
    
    response += f"\n<b>مسار تقدمك:</b>\n{progress}"
    
    if user_level.get('next_xp'):
        needed_xp = user_level['next_xp'] - user_level['xp']
        response += f"\n\n⚡ <b>للترقية:</b> تحتاج {format_number(needed_xp)} XP"
    else:
        response += "\n\n🎯 أنت في أعلى مستوى!"
    
    send_response(message, response)
    logger.info(f"Level requested by: {message.from_user.id}")

@bot.message_handler(commands=['حذف_حسابي', 'deleteaccount'])
def handle_delete_account(message):
    """حذف حساب المستخدم"""
    user_id = message.from_user.id
    
    # تأكيد الحذف
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("نعم، احذف حسابي", callback_data=f"confirm_delete_{user_id}"),
        types.InlineKeyboardButton("لا، أريد البقاء", callback_data="cancel_delete")
    )
    
    bot.send_message(
        message.chat.id,
        "⚠️ <b>هل أنت متأكد من حذف حسابك؟</b>\n\n"
        "سيتم حذف جميع بياناتك بما في ذلك:\n"
        "- رصيدك وممتلكاتك\n"
        "- أسهمك ومزرعتك\n"
        "- قلعتك ورتبتك\n"
        "- مستواك وتقدمك\n\n"
        "هذا الإجراء لا يمكن التراجع عنه!",
        reply_markup=markup,
        parse_mode="HTML"
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('confirm_delete_') or call.data == 'cancel_delete')
def handle_delete_confirmation(call):
    if call.data == 'cancel_delete':
        bot.delete_message(call.message.chat.id, call.message.message_id)
        return
    
    user_id = int(call.data.split('_')[2])
    
    # التأكد أن المستخدم نفسه هو من يطلب الحذف
    if call.from_user.id != user_id:
        bot.answer_callback_query(call.id, "❌ هذا الإجراء غير مسموح لك!")
        return
    
    if delete_user(user_id):
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="✅ تم حذف حسابك بنجاح. وداعاً!",
            reply_markup=None
        )
    else:
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text="❌ فشل في حذف الحساب. يرجى المحاولة لاحقاً.",
            reply_markup=None
        )

@bot.message_handler(func=lambda message: message.text.lower() in ['فلوسه', 'فلوس', 'رصيده'] and message.reply_to_message)
def handle_his_balance(message):
    """عرض رصيد مستخدم آخر بالرد"""
    target_user = message.reply_to_message.from_user
    target_id = target_user.id
    
    # الحصول على رصيد المستخدم
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT balance, account_number FROM users WHERE user_id = ?", (target_id,))
    row = c.fetchone()
    conn.close()
    
    if row:
        balance, account_number = row
        name = target_user.first_name or target_user.username
        bot.reply_to(
            message, 
            f"💰 <b>رصيد {name}</b>\n\n"
            f"• الرصيد: {format_number(balance)} ريال\n"
            f"• رقم الحساب: {account_number}",
            parse_mode="HTML"
        )
    else:
        bot.reply_to(message, "❌ هذا المستخدم ليس لديه حساب في البوت!")

# ========== نهاية الأوامر الجديدة ==========

@bot.callback_query_handler(func=lambda call: call.data.startswith('shop_'))
def handle_shop_callback(call):
    """معالجة اختيارات المتجر"""
    try:
        category = call.data.split('_')[1]
        
        if category == "main":
            keyboard = shop.get_main_menu()
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🏪 <b>متجر يوكي</b>\n\nاختر القسم الذي ترغب في التصفحه:",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            keyboard = shop.get_category_menu(category)
            help_text = (
                f"<b>{category}</b>\n\n"
                "💡 <b>كيفية الشراء:</b>\n"
                "1. اختر السلعة التي تريدها\n"
                "2. سيتم خصم المبلغ من رصيدك تلقائياً\n"
                "3. ستظهر السلعة في ممتلكاتك فوراً\n\n"
                f"مثال: اختر 'سور' لشراء سور لقلعتك"
            )
            
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=help_text,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            
    except Exception as e:
        logger.error(f"Shop callback error: {str(e)}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء معالجة طلبك!")

@bot.callback_query_handler(func=lambda call: call.data.startswith('buy_'))
def handle_buy_callback(call):
    """معالجة عمليات الشراء"""
    try:
        parts = call.data.split('_')
        category = parts[1]
        item = parts[2]
        user_id = call.from_user.id
        
        success, response = shop.buy_item(user_id, category, item)
        bot.answer_callback_query(call.id, response)
        
        if success:
            # تحديث رسالة المتجر
            keyboard = shop.get_category_menu(category)
            bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=keyboard
            )
            
    except Exception as e:
        logger.error(f"Buy callback error: {str(e)}")
        bot.answer_callback_query(call.id, "❌ حدث خطأ أثناء عملية الشراء!")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    # تحديث الإحصائيات
    bot_stats['total_messages'] += 1
    bot_stats['active_users'].add(message.from_user.id)
    
    user_id = message.from_user.id
    text = message.text.strip().lower()
    chat_type = message.chat.type
    
    # تجاهل الرسائل القديمة
    if message.date < time.time() - 60:
        return
    
    # منح XP عند كل رسالة (مع منع التكرار)
    user_level = leveling_system.get_user_level(user_id)
    last_xp_gain = user_level.get('last_xp_gain', 0) if user_level else 0
    
    if time.time() - last_xp_gain > 60:  # دقيقة واحدة بين كل XP
        success, response = leveling_system.add_xp(user_id)
        if success:
            logger.info(f"XP added to user {user_id}: {response}")
    
    # الأوامر المسموحة في المجموعات
    allowed_commands = [
        'فلوسي', 'راتب', 'استثمار فلوسي', 'حظ فلوسي', 
        'سعر الاسهم', 'اسهمي', 'ممتلكاتي', 'حسابي', 
        'ترتيبي', 'أغنى', 'لصوص', 'زرف', 'مساعدة', 'انشاء حساب',
        'مزرعتي', 'زرع', 'حصاد', 'سوق المزرعة',
        'قلعتي', 'بناء', 'هجوم', 'ترقية جيش',
        'متجر', 'مستواي'  # إضافة الأمر هنا
    ]
    
    # الأوامر ذات المعاملات
    param_commands = [
        'مضاربه', 'شراء اسهم', 'بيع اسهم', 'شراء', 'بيع', 'اهداء', 'تحويل'
    ]
    
    # أوامر الإدارة
    admin_commands = ['اضف فلوس', 'حذف فلوس', 'حظر', 'الغاء حظر', 'يوكي غادر المجموعة',
                     'اضف رد', 'رفع مشرف', 'تنزيل مشرف', 'قائمة المشرفين']
    
    # تحديد الأمر
    command = None
    for cmd in allowed_commands + param_commands + admin_commands:
        if text.startswith(cmd):
            command = cmd
            break
    
    # 1. معالجة أوامر المالكين أولاً
    if is_admin(user_id) and ('يوكي' in text or 'بوت' in text):
        if handle_owner_command(message, text):
            return  # تم معالجة الأمر ولا حاجة للمتابعة
    
    # إذا كان هناك منادات للبوت
    if 'يوكي' in text and not command:
        # رد خاص للمستخدمة رهف (ID: 8278493069)
        if user_id == 8278493069:
            responses = special_responses.get(user_id, [])
            if responses:
                send_response(message, random.choice(responses))
                bot_stats['commands_used']['special_greeting'] += 1
                return
        
        # ردود عامة للآخرين
        responses = custom_responses.get('greeting', [])
        if responses:
            send_response(message, random.choice(responses))
        else:
            send_response(message, "نعم؟ كيف يمكنني مساعدتك؟")
        bot_stats['commands_used']['greeting'] += 1
        return
    
    # إذا كان هناك نعت للبوت
    if 'بوت' in text and not command:
        # رد خاص للمستخدمة رهف (ID: 8278493069)
        if user_id == 8278493069:
            responses = special_responses.get(user_id, [])
            if responses:
                send_response(message, random.choice(responses))
                bot_stats['commands_used']['special_greeting'] += 1
                return
        
        # ردود عامة للآخرين
        responses = custom_responses.get('sad', [])
        if responses:
            send_response(message, random.choice(responses))
        else:
            send_response(message, "أنا لست مجرد بوت، أنا صديقك!")
        bot_stats['commands_used']['sad_response'] += 1
        return
    
    # إذا لم يكن أمر معروف في المجموعات
    if chat_type in ['group', 'supergroup'] and not command:
        return
    
    try:
        # التأكد من وجود المستخدم في قاعدة البيانات
        username = message.from_user.username or message.from_user.first_name
        ensure_user_exists(user_id, username)
        
        # الأوامر العامة
        if command == 'انشاء حساب':
            # عرض خيارات البنوك للمستخدم
            markup = types.InlineKeyboardMarkup(row_width=2)
            for bank in BANKS:
                markup.add(types.InlineKeyboardButton(bank, callback_data=f"bank_{bank}"))
            
            msg = bot.reply_to(message, "اختر بنكاً لإنشاء حسابك:", reply_markup=markup)
        
        elif command == 'فلوسي':
            balance = banking.get_balance(user_id)
            send_response(message, f"• فلوسك {format_number(balance)} ريال 💸")
        
        elif command == 'راتب':
            # التحقق من وقت التبريد الجديد
            last_salary = banking.get_last_salary_time(user_id)
            current_time = time.time()
            
            if last_salary and current_time - last_salary < 5 * 60:  # 5 دقائق
                remaining = int(5 * 60 - (current_time - last_salary))
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                send_response(message, f"⏱ عليك الانتظار {minutes} دقائق و {seconds} ثانية لصرف الراتب التالي")
                return
            
            success, response = banking.give_salary(user_id)
            if success:
                # منح XP للراتب
                leveling_system.add_xp(user_id, "salary")
            send_response(message, response)
        
        elif command == 'استثمار فلوسي':
            # التحقق من وقت التبريد الجديد
            last_invest = investment.get_last_invest_time(user_id)
            current_time = time.time()
            
            if last_invest and current_time - last_invest < INVESTMENT_COOLDOWN:
                remaining = int(INVESTMENT_COOLDOWN - (current_time - last_invest))
                minutes = int(remaining // 60)
                seconds = int(remaining % 60)
                send_response(message, f"⏱ عليك الانتظار {minutes} دقائق و {seconds} ثانية للاستثمار مرة أخرى")
                return
            
            success, response = investment.invest_all(user_id)
            if success:
                # منح XP للاستثمار
                leveling_system.add_xp(user_id, "investment")
            send_response(message, response)
        
        elif command == 'حظ فلوسي':
            # تعديل نسبة الخطر إلى 50%
            success, response = investment.luck_game(user_id, risk_level=50)
            if success:
                # منح XP للعبة الحظ
                leveling_system.add_xp(user_id, "luck")
            send_response(message, response)
        
        elif command == 'مضاربه':
            try:
                amount = int(text.split()[1])
                # تعديل نسبة الربح لتصبح بين 1% و 75%
                success, response = investment.gamble(user_id, amount, min_profit=1, max_profit=75)
                if success:
                    # منح XP للمضاربة
                    leveling_system.add_xp(user_id, "gamble")
                send_response(message, response)
            except:
                send_response(message, "استخدم: مضاربه [المبلغ]")
        
        elif command == 'سعر الاسهم':
            price, change = stocks.get_price()
            emoji = "📈" if change >= 0 else "📉"
            send_response(message, f"• سعر السهم: {price} ريال\n• التغير: {change}% {emoji}")
        
        elif command == 'شراء اسهم':
            try:
                amount = int(text.split()[2])
                success, response = stocks.buy_stocks(user_id, amount)
                if success:
                    # منح XP لشراء الأسهم
                    leveling_system.add_xp(user_id, "stocks")
                send_response(message, response)
            except:
                send_response(message, "استخدم: شراء اسهم [العدد]")
        
        elif command == 'بيع اسهم':
            try:
                amount = int(text.split()[2])
                success, response = stocks.sell_stocks(user_id, amount)
                if success:
                    # منح XP لبيع الأسهم
                    leveling_system.add_xp(user_id, "stocks")
                send_response(message, response)
            except:
                send_response(message, "استخدم: بيع اسهم [العدد]")
        
        elif command == 'اسهمي':
            amount = stocks.get_user_stocks(user_id)
            send_response(message, f"• عدد أسهمك: {format_number(amount)} سهم 📊")
        
        elif command == 'ممتلكاتي':
            props = properties.get_user_properties(user_id)
            if not props:
                send_response(message, "• ليس لديك أي ممتلكات 🏠")
            else:
                props_text = "• ممتلكاتك:\n" + "\n".join(
                    [f"• {name} (×{qty})" for name, qty in props]
                )
                send_response(message, props_text)
        
        elif command == 'شراء':
            try:
                prop_name = text.split()[1]
                success, response = properties.buy_property(user_id, prop_name)
                if success:
                    # منح XP لشراء الممتلكات
                    leveling_system.add_xp(user_id, "property")
                send_response(message, response)
            except:
                send_response(message, "استخدم: شراء [اسم الممتلك]")
        
        elif command == 'بيع':
            try:
                parts = text.split()
                quantity = int(parts[1])
                prop_name = parts[2]
                success, response = properties.sell_property(user_id, prop_name, quantity)
                if success:
                    # منح XP لبيع الممتلكات
                    leveling_system.add_xp(user_id, "property")
                send_response(message, response)
            except:
                send_response(message, "استخدم: بيع [العدد] [اسم الممتلك]")
        
        elif command == 'تحويل':
            if message.reply_to_message:
                try:
                    amount = int(text.split()[1])
                    target_id = message.reply_to_message.from_user.id
                    success, response = banking.transfer_money(user_id, target_id, amount)
                    if success:
                        # منح XP للتحويل
                        leveling_system.add_xp(user_id, "transfer")
                    send_response(message, response)
                except:
                    send_response(message, "استخدم: تحويل [المبلغ] مع الرد على رسالة المستخدم")
            else:
                send_response(message, "• يجب الرد على رسالة المستخدم الذي تريد التحويل إليه!")
        
        elif command == 'اهداء':
            if message.reply_to_message:
                try:
                    parts = text.split()
                    quantity = int(parts[1])
                    prop_name = parts[2]
                    target_id = message.reply_to_message.from_user.id
                    success, response = properties.gift_property(user_id, target_id, prop_name, quantity)
                    if success:
                        # منح XP للإهداء
                        leveling_system.add_xp(user_id, "gift")
                    send_response(message, response)
                except:
                    send_response(message, "استخدم: اهداء [العدد] [اسم الممتلك] مع الرد على رسالة المستخدم")
            else:
                send_response(message, "• يجب الرد على رسالة المستخدم الذي تريد الإهداء إليه!")
        
        elif command == 'حسابي':
            conn = get_db()
            c = conn.cursor()
            c.execute("SELECT account_number, balance FROM users WHERE user_id = ?", (user_id,))
            row = c.fetchone()
            conn.close()
            
            if row:
                acc_num, balance = row
                send_response(message, (
                    f"• رقم حسابك: {acc_num}\n"
                    f"• البنك: نظام البنوك التقليدي\n"
                    f"• الرصيد: {format_number(balance)} ريال 💳"
                ))
            else:
                send_response(message, "• ليس لديك حساب! استخدم 'انشاء حساب' لإنشاء حساب")
        
        elif command == 'ترتيبي':
            rank = ranking.get_user_rank(user_id)
            send_response(message, f"• ترتيبك في اللعبة: #{rank} 🏆")
        
        elif command == 'أغنى':
            rich_list = ranking.get_richest_users()
            response = "• قائمة الأغنى:\n" + "\n".join(
                [f"{i+1}. {user[0]} - {format_number(user[1])} ريال" for i, user in enumerate(rich_list)]
            )
            send_response(message, response)
        
        elif command == 'لصوص':
            thieves = ranking.get_top_thieves()
            response = "• قائمة أكثر اللصوص:\n" + "\n".join(
                [f"{i+1}. {thief[0]} - سرق {format_number(thief[1])} ريال" for i, thief in enumerate(thieves)]
            )
            send_response(message, response)
        
        elif command == 'زرف':
            # التعديل الرئيسي: استخدام الدالة الجديدة من database.py
            last_robbery = get_last_robbery_time(user_id)
            current_time = time.time()
            elapsed = current_time - last_robbery
            
            if elapsed < ROBBERY_COOLDOWN:
                remaining = ROBBERY_COOLDOWN - elapsed
                hours = int(remaining // 3600)
                minutes = int((remaining % 3600) // 60)
                send_response(message, f"⏱ عليك الانتظار {hours} ساعة و {minutes} دقيقة للزرف مرة أخرى")
                return
            
            if message.reply_to_message:
                victim_id = message.reply_to_message.from_user.id
                # تمرير معرف البوت ومعرف الدردشة
                success, response = robbery.attempt_robbery(
                    user_id, 
                    victim_id, 
                    BOT_ID,
                    message.chat.id  # معرف الدردشة الجديد
                )
                if success:
                    # منح XP للسرقة الناجحة
                    leveling_system.add_xp(user_id, "robbery")
                send_response(message, response)
            else:
                send_response(message, "• يجب الرد على رسالة المستخدم الذي تريد سرقته!")
        
        elif command == 'مساعدة':
            send_response(message, HELP_TEXT)
        
        # أوامر المزرعة
        elif command == 'مزرعتي':
            farm_info = farm.get_farm_info(user_id)
            send_response(message, farm_info)
        
        elif command == 'زرع':
            try:
                crop_type = text.split()[1]
                success, response = farm.plant_crop(user_id, crop_type)
                if success:
                    # منح XP للزراعة
                    leveling_system.add_xp(user_id, "farm")
                send_response(message, response)
            except:
                send_response(message, "استخدم: زرع [نوع المحصول]")
        
        elif command == 'حصاد':
            success, response = farm.harvest_crops(user_id)
            if success:
                # منح XP للحصاد
                leveling_system.add_xp(user_id, "harvest")
            send_response(message, response)
        
        elif command == 'سوق المزرعة':
            market_items = farm.get_market_items()
            response = "🛒 سوق المزرعة:\n" + "\n".join(
                [f"• {item} - {price} ريال" for item, price in market_items.items()]
            )
            send_response(message, response)
        
        # أوامر القلعة
        elif command == 'قلعتي':
            castle_info = castle.get_castle_info(user_id)
            send_response(message, castle_info)
        
        elif command == 'بناء':
            try:
                building_type = text.split()[1]
                success, response = castle.build(user_id, building_type)
                if success:
                    # منح XP للبناء
                    leveling_system.add_xp(user_id, "castle")
                send_response(message, response)
            except:
                send_response(message, "استخدم: بناء [نوع البناء]")
        
        elif command == 'هجوم':
            if message.reply_to_message:
                target_id = message.reply_to_message.from_user.id
                success, response = castle.attack(user_id, target_id)
                if success:
                    # منح XP للهجوم
                    leveling_system.add_xp(user_id, "attack")
                send_response(message, response)
            else:
                send_response(message, "• يجب الرد على رسالة المستخدم الذي تريد مهاجمته!")
        
        elif command == 'ترقية جيش':
            success, response = castle.upgrade_army(user_id)
            if success:
                # منح XP لترقية الجيش
                leveling_system.add_xp(user_id, "army")
            send_response(message, response)
        
        # أوامر الإدارة
        elif command == 'اضف رد' and is_admin(user_id):
            try:
                parts = text.split(maxsplit=3)  # ['اضف', 'رد', 'النوع', 'النص']
                if len(parts) < 4:
                    send_response(message, "استخدم: اضف رد [greeting/sad] [النص]")
                    return
                
                response_type = parts[2].lower()
                response_text = parts[3]
                
                if response_type not in ['greeting', 'sad']:
                    send_response(message, "النوع يجب أن يكون greeting أو sad")
                    return
                
                # إضافة الرد إلى القائمة
                if add_custom_response(response_type, response_text):
                    send_response(message, f"✅ تمت إضافة رد جديد: {response_text}")
                else:
                    send_response(message, "❌ فشل في إضافة الرد")
            except Exception as e:
                logger.error(f"Error adding response: {str(e)}")
                send_response(message, "❌ حدث خطأ أثناء إضافة الرد")
        
        elif command == 'رفع مشرف' and is_admin(user_id):
            try:
                parts = text.split()
                if len(parts) < 4:
                    send_response(message, "استخدم: رفع مشرف [@المستخدم] [رتبة] [مدة بالأيام]")
                    return
                
                target_username = parts[2].strip('@')
                rank_name = parts[3]
                days = int(parts[4])
                
                # الحصول على آيدي المستخدم من اسم المستخدم
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT user_id FROM users WHERE username = ?", (target_username,))
                target_row = c.fetchone()
                
                if not target_row:
                    send_response(message, "❌ لم يتم العثور على المستخدم")
                    return
                
                target_id = target_row[0]
                expiry_date = datetime.datetime.now() + datetime.timedelta(days=days)
                
                # حفظ الرتبة في قاعدة البيانات
                c.execute("""
                    INSERT OR REPLACE INTO user_ranks (user_id, rank, expiry)
                    VALUES (?, ?, ?)
                """, (target_id, rank_name, expiry_date.isoformat()))
                conn.commit()
                conn.close()
                
                send_response(message, f"✅ تم رفع {target_username} إلى رتبة {rank_name} لمدة {days} أيام")
            except Exception as e:
                logger.error(f"Error promoting user: {str(e)}")
                send_response(message, "❌ حدث خطأ أثناء رفع المشرف")
        
        elif command == 'تنزيل مشرف' and is_admin(user_id):
            try:
                target_username = text.split()[2].strip('@')
                
                # الحصول على آيدي المستخدم من اسم المستخدم
                conn = get_db()
                c = conn.cursor()
                c.execute("SELECT user_id FROM users WHERE username = ?", (target_username,))
                target_row = c.fetchone()
                
                if not target_row:
                    send_response(message, "❌ لم يتم العثور على المستخدم")
                    return
                
                target_id = target_row[0]
                
                # حذف الرتبة من قاعدة البيانات
                c.execute("DELETE FROM user_ranks WHERE user_id = ?", (target_id,))
                conn.commit()
                conn.close()
                
                send_response(message, f"✅ تم تنزيل رتبة {target_username}")
            except Exception as e:
                logger.error(f"Error demoting user: {str(e)}")
                send_response(message, "❌ حدث خطأ أثناء تنزيل المشرف")
        
        elif command == 'قائمة المشرفين' and is_admin(user_id):
            try:
                conn = get_db()
                c = conn.cursor()
                c.execute("""
                    SELECT u.username, ur.rank, ur.expiry 
                    FROM user_ranks ur
                    JOIN users u ON ur.user_id = u.user_id
                    WHERE ur.expiry > datetime('now')
                """)
                admins = c.fetchall()
                conn.close()
                
                if not admins:
                    send_response(message, "❌ لا يوجد مشرفين حالياً")
                    return
                
                response_text = "👑 قائمة المشرفين:\n"
                for admin in admins:
                    username, rank, expiry = admin
                    expiry_date = datetime.datetime.fromisoformat(expiry)
                    days_left = (expiry_date - datetime.datetime.now()).days
                    response_text += f"• @{username} ({rank}) - متبقي {days_left} يوم\n"
                
                send_response(message, response_text)
            except Exception as e:
                logger.error(f"Error listing admins: {str(e)}")
                send_response(message, "❌ حدث خطأ أثناء جلب قائمة المشرفين")
        
        elif command == 'اضف فلوس' and is_admin(user_id):
            try:
                parts = text.split()
                amount = int(parts[2])
                
                # التحقق من وجود رد على المستخدم
                if message.reply_to_message:
                    target_id = message.reply_to_message.from_user.id
                    banking.add_money(target_id, amount)
                    send_response(message, f"✅ تم إضافة {format_number(amount)} ريال إلى حساب المستخدم")
                else:
                    send_response(message, "❌ يجب الرد على رسالة المستخدم!")
            except:
                send_response(message, "استخدم: اضف فلوس [المبلغ] مع الرد على رسالة المستخدم")
        
        elif command == 'حذف فلوس' and is_admin(user_id):
            try:
                parts = text.split()
                amount = int(parts[2])
                
                # التحقق من وجود رد على المستخدم
                if message.reply_to_message:
                    target_id = message.reply_to_message.from_user.id
                    banking.remove_money(target_id, amount)
                    send_response(message, f"✅ تم حذف {format_number(amount)} ريال من حساب المستخدم")
                else:
                    send_response(message, "❌ يجب الرد على رسالة المستخدم!")
            except:
                send_response(message, "استخدم: حذف فلوس [المبلغ] مع الرد على رسالة المستخدم")
        
        elif command == 'حظر' and is_admin(user_id):
            try:
                parts = text.split(maxsplit=1)
                reason = parts[1] if len(parts) > 1 else "بدون سبب"
                
                # التحقق من وجود رد على المستخدم
                if message.reply_to_message:
                    target_id = message.reply_to_message.from_user.id
                    # تنفيذ حظر المستخدم
                    send_response(message, f"✅ تم حظر المستخدم بسبب: {reason}")
                else:
                    send_response(message, "❌ يجب الرد على رسالة المستخدم!")
            except:
                send_response(message, "استخدم: حظر [السبب] مع الرد على رسالة المستخدم")
        
        elif command == 'الغاء حظر' and is_admin(user_id):
            try:
                # التحقق من وجود رد على المستخدم
                if message.reply_to_message:
                    target_id = message.reply_to_message.from_user.id
                    # تنفيذ إلغاء حظر المستخدم
                    send_response(message, "✅ تم إلغاء حظر المستخدم")
                else:
                    send_response(message, "❌ يجب الرد على رسالة المستخدم!")
            except:
                send_response(message, "استخدم: الغاء حظر مع الرد على رسالة المستخدم")
        
        elif command == 'غادر' and is_admin(user_id):
            try:
                send_response(message, "✅ جاري مغادرة المجموعة...")
                bot.send_message(message.chat.id, "🛫 وداعاً! سأغادر الآن")
                time.sleep(1)
                bot.leave_chat(message.chat.id)
                logger.info(f"Left group {message.chat.id} by admin {user_id}")
            except Exception as e:
                logger.error(f"Error leaving group: {str(e)}")
                send_response(message, f"❌ فشل في مغادرة المجموعة: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error handling message: {str(e)}")
        print(f"Error: {e}")
        send_response(message, "حدث خطأ أثناء معالجة طلبك! ❌")

# معالجة اختيار البنك عند إنشاء الحساب
@bot.callback_query_handler(func=lambda call: call.data.startswith('bank_'))
def handle_bank_selection(call):
    bank_name = call.data.split('_', 1)[1]
    user_id = call.from_user.id
    username = call.from_user.username or call.from_user.first_name
    
    # إنشاء الحساب مع البنك المختار
    success, response = banking.create_account(user_id, username)
    response += f"\n• البنك المختار: {bank_name}"
    
    bot.answer_callback_query(call.id, "تم اختيار البنك بنجاح")
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")
    bot.delete_message(call.message.chat.id, call.message.message_id)

# ========== تشغيل البوت ==========
if __name__ == "__main__":
    init_db()
    
    # الحصول على معرف البوت وتخزينه
    try:
        bot_info = bot.get_me()
        BOT_ID = bot_info.id
        print(f"===== إعدادات البوت =====")
        print(f"يوزر البوت: @{bot_info.username}")
        print(f"معرف البوت: {BOT_ID}")
        print(f"الأدمنية: {ADMINS}")
        print("=========================")
        print("البوت يعمل الآن...")
        
        # تسجيل بدء التشغيل
        logger.info("===== Starting Yuki Bot =====")
        logger.info(f"Bot username: @{bot_info.username}")
        logger.info(f"Bot ID: {BOT_ID}")
        logger.info(f"Admins: {ADMINS}")
    except Exception as e:
        logger.critical(f"Failed to get bot info: {str(e)}")
        print(f"حدث خطأ جسيم: {e}")
        exit(1)
    
    try:
        bot.infinity_polling()
    except Exception as e:
        logger.critical(f"Bot crashed: {str(e)}")
        print(f"حدث خطأ جسيم: {e}")
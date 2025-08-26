"""
أوامر الذاكرة المشتركة والبحث في المواضيع
Shared Memory and Topic Search Commands
"""

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
import logging

router = Router()

@router.message(Command("ذاكرة"))
async def memory_info_command(message: Message):
    """عرض معلومات نظام الذاكرة المشتركة"""
    try:
        info_text = """
🧠 **نظام الذاكرة المشتركة المتطور**

🔍 **الميزات الجديدة:**
• ذاكرة مشتركة للمجموعة مع NLTK
• ربط المواضيع بين المستخدمين
• تحليل المشاعر والمواضيع
• تتبع الإشارات والعلاقات

💬 **أمثلة للاستخدام:**
• "يوكي ماذا تعرف عن براندون؟"
• "ماذا كنتم تتحدثون عني؟"
• "من تحدث عن الألعاب؟"
• "ماذا قال غيو عني؟"

⭐ **المستخدمون المميزون:**
• غيو الأسطورة - محترف الألعاب
• الشيخ - حلال المشاكل وكاتب العقود

🚀 **النظام يتذكر كل شيء الآن!**
        """
        
        await message.reply(info_text)
        
    except Exception as e:
        logging.error(f"خطأ في أمر الذاكرة: {e}")
        await message.reply("❌ خطأ في عرض معلومات الذاكرة")

@router.message(Command("بحث"))
async def search_command(message: Message):
    """أمر البحث في الذاكرة المشتركة"""
    try:
        if len(message.text.split()) < 2:
            await message.reply("""
🔍 **أمر البحث في الذاكرة المشتركة**

**الاستخدام:**
`/بحث [كلمة البحث أو السؤال]`

**أمثلة:**
• `/بحث غيو`
• `/بحث من تحدث عن الألعاب`
• `/بحث ماذا قال براندون عني`
            """)
            return
        
        # استخراج النص المراد البحث عنه
        search_query = message.text.replace('/بحث', '').strip()
        
        if not search_query:
            await message.reply("⚠️ يرجى كتابة شيء للبحث عنه")
            return
        
        # تنفيذ البحث
        from modules.topic_search import topic_search_engine
        
        result = await topic_search_engine.process_query(
            search_query, 
            message.from_user.id, 
            message.chat.id
        )
        
        if result:
            await message.reply(result)
        else:
            await message.reply("🔍 لم أجد نتائج مطابقة لبحثك في الذاكرة المشتركة")
            
    except Exception as e:
        logging.error(f"خطأ في أمر البحث: {e}")
        await message.reply("❌ خطأ في تنفيذ البحث")

@router.message(Command("احصائيات_الذاكرة"))
async def memory_stats_command(message: Message):
    """عرض إحصائيات الذاكرة المشتركة"""
    try:
        from modules.shared_memory import shared_memory
        from config.settings import DATABASE_URL
        import aiosqlite
        
        async with aiosqlite.connect(DATABASE_URL) as db:
            # عدد المحادثات المحفوظة
            cursor = await db.execute('SELECT COUNT(*) FROM shared_conversations WHERE chat_id = ?', (message.chat.id,))
            conversations_count = (await cursor.fetchone())[0]
            
            # عدد المواضيع المختلفة
            cursor = await db.execute('SELECT COUNT(DISTINCT topic) FROM topic_links WHERE chat_id = ?', (message.chat.id,))
            topics_count = (await cursor.fetchone())[0]
            
            # عدد المستخدمين النشطين
            cursor = await db.execute('SELECT COUNT(DISTINCT user_id) FROM shared_conversations WHERE chat_id = ?', (message.chat.id,))
            users_count = (await cursor.fetchone())[0]
            
            stats_text = f"""
📊 **إحصائيات الذاكرة المشتركة**

💬 **المحادثات المحفوظة:** {conversations_count}
🏷️ **المواضيع المختلفة:** {topics_count}
👥 **المستخدمون النشطون:** {users_count}

🧠 **نظام NLTK:** ✅ نشط
🔗 **ربط المواضيع:** ✅ يعمل
⭐ **المستخدمون المميزون:** ✅ محدّثون

🚀 **النظام يتطور باستمرار!**
            """
            
            await message.reply(stats_text)
        
    except Exception as e:
        logging.error(f"خطأ في إحصائيات الذاكرة: {e}")
        await message.reply("❌ خطأ في جلب الإحصائيات")

@router.message(F.text.contains("@Hacker20263"))
async def detect_sheikh_mention(message: Message):
    """اكتشاف إشارة للشيخ وحفظ معرفه"""
    try:
        # إذا كان المرسل هو الشيخ نفسه، نحفظ معرفه
        if message.from_user and message.from_user.username == "Hacker20263":
            # تحديث معرف الشيخ في النظام
            from modules.shared_memory import shared_memory
            
            # إزالة المعرف المؤقت وإضافة المعرف الحقيقي
            if 1234567890 in shared_memory.special_users:
                sheikh_data = shared_memory.special_users.pop(1234567890)
                shared_memory.special_users[message.from_user.id] = sheikh_data
                
                logging.info(f"تم حفظ معرف الشيخ: {message.from_user.id}")
                
                # إرسال رسالة ترحيب للشيخ
                await message.reply("🕌 أهلاً وسهلاً بالشيخ الكريم! تم تحديث معرفك في النظام ✨")
        
    except Exception as e:
        logging.error(f"خطأ في اكتشاف الشيخ: {e}")


async def handle_memory_commands(message: Message):
    """معالج أوامر الذاكرة المشتركة للنصوص العادية"""
    try:
        text = message.text.lower().strip()
        
        if text == '/ذاكرة' or text == 'ذاكرة':
            await memory_info_command(message)
            return True
        
        elif text.startswith('ذاكرة المجموعة') or text.startswith('احصائيات الذاكرة'):
            await memory_stats_command(message)
            return True
        
        elif text.startswith('بحث في الذاكرة') or text.startswith('/بحث'):
            await search_command(message)
            return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج أوامر الذاكرة: {e}")
        return False
"""
وحدة تحميل الوسائط من المنصات الاجتماعية
Media Download Module
"""

import logging
import re
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.decorators import group_only
from utils.helpers import format_user_mention


# حالة التحميل (مفعل/معطل) لكل مجموعة
download_settings = {}


async def load_download_settings():
    """تحميل إعدادات التحميل من قاعدة البيانات"""
    try:
        from database.operations import execute_query
        
        settings = await execute_query(
            "SELECT chat_id, setting_value FROM group_settings WHERE setting_key = 'enable_download'",
            fetch_all=True
        )
        
        if settings:
            for setting in settings:
                chat_id = setting[0] if isinstance(setting, tuple) else setting['chat_id']
                value = setting[1] if isinstance(setting, tuple) else setting['setting_value']
                download_settings[chat_id] = value == "True"
        
        logging.info(f"تم تحميل إعدادات التحميل: {download_settings}")
        
    except Exception as e:
        logging.error(f"خطأ في تحميل إعدادات التحميل: {e}")


@group_only
async def toggle_download(message: Message, enable: bool = True):
    """تفعيل أو تعطيل التحميل"""
    try:
        # التحقق من الصلاحيات أولاً
        from config.hierarchy import has_permission, AdminLevel
        
        # إزالة فحص الصلاحيات مؤقتاً للاختبار
        # if not has_permission(message.from_user.id, AdminLevel.MEMBER, message.chat.id):
        #     await message.reply("❌ هذا الأمر للأعضاء المسجلين وما فوق فقط")
        #     return
        
        logging.info(f"محاولة {'تفعيل' if enable else 'تعطيل'} التحميل للمستخدم {message.from_user.id} في المجموعة {message.chat.id}")
        
        chat_id = message.chat.id
        download_settings[chat_id] = enable
        
        # حفظ في قاعدة البيانات
        from database.operations import execute_query
        from datetime import datetime
        
        await execute_query(
            "INSERT OR REPLACE INTO group_settings (chat_id, setting_key, setting_value, updated_at) VALUES (?, ?, ?, ?)",
            (chat_id, "enable_download", str(enable), datetime.now().isoformat())
        )
        
        # إضافة تسجيل للتصحيح
        logging.info(f"تم {'تفعيل' if enable else 'تعطيل'} التحميل للمجموعة {chat_id}. الإعدادات الحالية: {download_settings}")
        
        status = "مفعل ✅" if enable else "معطل ❌"
        action = "تم تفعيل" if enable else "تم تعطيل"
        
        await message.reply(
            f"✅ **{action} تحميل الوسائط**\n\n"
            f"📱 الحالة الحالية: {status}\n\n"
            f"💡 يمكن للأعضاء الآن {'تحميل' if enable else 'لا يمكنهم تحميل'} الوسائط من الروابط"
        )
        
    except Exception as e:
        logging.error(f"خطأ في تغيير حالة التحميل: {e}")
        await message.reply("❌ حدث خطأ في تغيير حالة التحميل")


@group_only
async def download_tiktok(message: Message, url: str = None):
    """تحميل فيديو من تيك توك"""
    try:
        chat_id = message.chat.id
        
        # التحقق من تفعيل التحميل
        if not download_settings.get(chat_id, False):
            await message.reply("❌ التحميل معطل في هذه المجموعة\nاستخدم 'تفعيل التحميل' لتفعيله")
            return
        
        # استخراج الرابط من النص
        if not url:
            text = message.text or ""
            # البحث عن رابط تيك توك
            tiktok_pattern = r'https?://(?:www\.)?(?:tiktok\.com|vm\.tiktok\.com)/\S+'
            matches = re.findall(tiktok_pattern, text)
            if not matches:
                await message.reply("❌ يرجى إدخال رابط تيك توك صحيح\nمثال: تيك https://tiktok.com/...")
                return
            url = matches[0]
        
        # التحقق من صحة الرابط
        if not is_valid_tiktok_url(url):
            await message.reply("❌ رابط تيك توك غير صحيح")
            return
        
        # إرسال رسالة تحميل
        loading_msg = await message.reply("⏳ جاري تحميل الفيديو من تيك توك...")
        
        # محاكاة التحميل (يحتاج لمكتبة خارجية مثل yt-dlp)
        await simulate_download(loading_msg, "تيك توك", url)
        
    except Exception as e:
        logging.error(f"خطأ في تحميل تيك توك: {e}")
        await message.reply("❌ حدث خطأ في تحميل الفيديو من تيك توك")


@group_only
async def download_twitter(message: Message, url: str = None):
    """تحميل وسائط من تويتر"""
    try:
        chat_id = message.chat.id
        
        # التحقق من تفعيل التحميل
        if not download_settings.get(chat_id, False):
            await message.reply("❌ التحميل معطل في هذه المجموعة\nاستخدم 'تفعيل التحميل' لتفعيله")
            return
        
        # استخراج الرابط من النص
        if not url:
            text = message.text or ""
            # البحث عن رابط تويتر/X
            twitter_pattern = r'https?://(?:www\.)?(?:twitter\.com|x\.com)/\S+'
            matches = re.findall(twitter_pattern, text)
            if not matches:
                await message.reply("❌ يرجى إدخال رابط تويتر/X صحيح\nمثال: تويتر https://twitter.com/...")
                return
            url = matches[0]
        
        # التحقق من صحة الرابط
        if not is_valid_twitter_url(url):
            await message.reply("❌ رابط تويتر/X غير صحيح")
            return
        
        # إرسال رسالة تحميل
        loading_msg = await message.reply("⏳ جاري تحميل المحتوى من تويتر...")
        
        # محاكاة التحميل
        await simulate_download(loading_msg, "تويتر", url)
        
    except Exception as e:
        logging.error(f"خطأ في تحميل تويتر: {e}")
        await message.reply("❌ حدث خطأ في تحميل المحتوى من تويتر")


@group_only
async def download_soundcloud(message: Message, url: str = None):
    """تحميل صوت من ساوند كلاود"""
    try:
        chat_id = message.chat.id
        
        # التحقق من تفعيل التحميل
        if not download_settings.get(chat_id, False):
            await message.reply("❌ التحميل معطل في هذه المجموعة\nاستخدم 'تفعيل التحميل' لتفعيله")
            return
        
        # استخراج الرابط من النص
        if not url:
            text = message.text or ""
            # البحث عن رابط ساوند كلاود
            soundcloud_pattern = r'https?://(?:www\.)?soundcloud\.com/\S+'
            matches = re.findall(soundcloud_pattern, text)
            if not matches:
                await message.reply("❌ يرجى إدخال رابط ساوند كلاود صحيح\nمثال: ساوند https://soundcloud.com/...")
                return
            url = matches[0]
        
        # التحقق من صحة الرابط
        if not is_valid_soundcloud_url(url):
            await message.reply("❌ رابط ساوند كلاود غير صحيح")
            return
        
        # إرسال رسالة تحميل
        loading_msg = await message.reply("⏳ جاري تحميل المقطع الصوتي من ساوند كلاود...")
        
        # محاكاة التحميل
        await simulate_download(loading_msg, "ساوند كلاود", url)
        
    except Exception as e:
        logging.error(f"خطأ في تحميل ساوند كلاود: {e}")
        await message.reply("❌ حدث خطأ في تحميل المقطع الصوتي")


@group_only
async def search_youtube(message: Message, query: str = None):
    """البحث في يوتيوب"""
    try:
        chat_id = message.chat.id
        
        # إضافة تسجيل للتصحيح
        current_setting = download_settings.get(chat_id, False)
        logging.info(f"فحص إعدادات التحميل للمجموعة {chat_id}: {current_setting}. جميع الإعدادات: {download_settings}")
        
        # التحقق من تفعيل التحميل
        if not current_setting:
            await message.reply("❌ التحميل معطل في هذه المجموعة\nاستخدم 'تفعيل التحميل' لتفعيله")
            return
        
        # استخراج النص من الأمر
        if not query:
            text = message.text or ""
            if text.startswith("بحث "):
                query = text[4:].strip()
            else:
                await message.reply("❌ يرجى إدخال نص البحث\nمثال: بحث أغنية جميلة")
                return
        
        if not query:
            await message.reply("❌ يرجى إدخال نص البحث")
            return
        
        # إرسال رسالة بحث
        search_msg = await message.reply(f"🔍 جاري البحث في يوتيوب عن: '{query}'...")
        
        # محاكاة البحث
        await simulate_youtube_search(search_msg, query)
        
    except Exception as e:
        logging.error(f"خطأ في البحث في يوتيوب: {e}")
        await message.reply("❌ حدث خطأ في البحث في يوتيوب")


def is_valid_tiktok_url(url: str) -> bool:
    """التحقق من صحة رابط تيك توك"""
    tiktok_domains = ['tiktok.com', 'vm.tiktok.com', 'www.tiktok.com']
    return any(domain in url for domain in tiktok_domains)


def is_valid_twitter_url(url: str) -> bool:
    """التحقق من صحة رابط تويتر/X"""
    twitter_domains = ['twitter.com', 'x.com', 'www.twitter.com', 'www.x.com']
    return any(domain in url for domain in twitter_domains)


def is_valid_soundcloud_url(url: str) -> bool:
    """التحقق من صحة رابط ساوند كلاود"""
    soundcloud_domains = ['soundcloud.com', 'www.soundcloud.com']
    return any(domain in url for domain in soundcloud_domains)


async def simulate_download(loading_msg: Message, platform: str, url: str):
    """محاكاة عملية التحميل"""
    try:
        import asyncio
        await asyncio.sleep(2)  # محاكاة وقت التحميل
        
        # في التطبيق الحقيقي، هنا سيتم استخدام مكتبة مثل yt-dlp
        await loading_msg.edit_text(
            f"❌ **عذراً، التحميل من {platform} غير متاح حالياً**\n\n"
            f"🔗 الرابط: {url}\n"
            f"💡 هذه الميزة تحتاج لإعداد إضافي من المطور"
        )
        
    except Exception as e:
        logging.error(f"خطأ في محاكاة التحميل: {e}")
        await loading_msg.edit_text("❌ حدث خطأ في عملية التحميل")


async def simulate_youtube_search(search_msg: Message, query: str):
    """البحث في يوتيوب باستخدام YouTube API"""
    try:
        from modules.music_search import search_youtube_api
        
        # البحث باستخدام YouTube API الحقيقي
        video_info = await search_youtube_api(query)
        
        if video_info:
            await search_msg.edit_text(
                f"🎵 **تم العثور على الأغنية!**\n\n"
                f"🎤 **العنوان:** {video_info['title']}\n"
                f"📺 **القناة:** {video_info['channel']}\n"
                f"📝 **الوصف:** {video_info['description']}\n"
                f"\n🔗 **الرابط:** {video_info['url']}"
            )
        else:
            await search_msg.edit_text(
                f"❌ **لم يتم العثور على نتائج**\n\n"
                f"🔍 البحث عن: '{query}'\n"
                f"💡 جرب كتابة اسم الأغنية بطريقة مختلفة"
            )
        
    except Exception as e:
        logging.error(f"خطأ في البحث في يوتيوب: {e}")
        await search_msg.edit_text("❌ حدث خطأ في عملية البحث")
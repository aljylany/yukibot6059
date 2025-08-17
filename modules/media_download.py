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


@group_only
async def toggle_download(message: Message, enable: bool = True):
    """تفعيل أو تعطيل التحميل"""
    try:
        chat_id = message.chat.id
        download_settings[chat_id] = enable
        
        status = "مفعل ✅" if enable else "معطل ❌"
        await message.reply(f"🔄 **تحميل الوسائط الآن:** {status}")
        
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
        
        # التحقق من تفعيل التحميل
        if not download_settings.get(chat_id, False):
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
    """محاكاة البحث في يوتيوب"""
    try:
        import asyncio
        await asyncio.sleep(2)  # محاكاة وقت البحث
        
        # في التطبيق الحقيقي، هنا سيتم استخدام YouTube API
        await search_msg.edit_text(
            f"❌ **البحث في يوتيوب غير متاح حالياً**\n\n"
            f"🔍 البحث عن: '{query}'\n"
            f"💡 هذه الميزة تحتاج لـ YouTube API key"
        )
        
    except Exception as e:
        logging.error(f"خطأ في محاكاة البحث: {e}")
        await search_msg.edit_text("❌ حدث خطأ في عملية البحث")
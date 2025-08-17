"""
وحدة قفل الوسائط والمحتوى
Media Locks Module
"""

import logging
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from utils.decorators import group_only, admin_required
from database.operations import execute_query


# إعدادات القفل لكل مجموعة
group_locks = {}


@group_only
@admin_required
async def lock_photos(message: Message):
    """قفل الصور"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['photos'] = True
        await message.reply("🔒 **تم قفل الصور**\nلن يتمكن الأعضاء من إرسال الصور")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الصور: {e}")
        await message.reply("❌ حدث خطأ في قفل الصور")


@group_only
@admin_required
async def unlock_photos(message: Message):
    """فتح الصور"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['photos'] = False
        await message.reply("🔓 **تم فتح الصور**\nيمكن للأعضاء إرسال الصور الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الصور: {e}")
        await message.reply("❌ حدث خطأ في فتح الصور")


@group_only
@admin_required
async def lock_videos(message: Message):
    """قفل الفيديوهات"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['videos'] = True
        await message.reply("🔒 **تم قفل الفيديو**\nلن يتمكن الأعضاء من إرسال الفيديوهات")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الفيديو: {e}")
        await message.reply("❌ حدث خطأ في قفل الفيديو")


@group_only
@admin_required
async def unlock_videos(message: Message):
    """فتح الفيديوهات"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['videos'] = False
        await message.reply("🔓 **تم فتح الفيديو**\nيمكن للأعضاء إرسال الفيديوهات الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الفيديو: {e}")
        await message.reply("❌ حدث خطأ في فتح الفيديو")


@group_only
@admin_required
async def lock_voice(message: Message):
    """قفل التسجيلات الصوتية"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['voice'] = True
        await message.reply("🔒 **تم قفل الصوت**\nلن يتمكن الأعضاء من إرسال التسجيلات الصوتية")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الصوت: {e}")
        await message.reply("❌ حدث خطأ في قفل الصوت")


@group_only
@admin_required
async def unlock_voice(message: Message):
    """فتح التسجيلات الصوتية"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['voice'] = False
        await message.reply("🔓 **تم فتح الصوت**\nيمكن للأعضاء إرسال التسجيلات الصوتية الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الصوت: {e}")
        await message.reply("❌ حدث خطأ في فتح الصوت")


@group_only
@admin_required
async def lock_stickers(message: Message):
    """قفل الملصقات"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['stickers'] = True
        await message.reply("🔒 **تم قفل الملصقات**\nلن يتمكن الأعضاء من إرسال الملصقات")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الملصقات: {e}")
        await message.reply("❌ حدث خطأ في قفل الملصقات")


@group_only
@admin_required
async def unlock_stickers(message: Message):
    """فتح الملصقات"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['stickers'] = False
        await message.reply("🔓 **تم فتح الملصقات**\nيمكن للأعضاء إرسال الملصقات الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الملصقات: {e}")
        await message.reply("❌ حدث خطأ في فتح الملصقات")


@group_only
@admin_required
async def lock_gifs(message: Message):
    """قفل المتحركات (GIF)"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['gifs'] = True
        await message.reply("🔒 **تم قفل المتحركه**\nلن يتمكن الأعضاء من إرسال المتحركات (GIF)")
        
    except Exception as e:
        logging.error(f"خطأ في قفل المتحركات: {e}")
        await message.reply("❌ حدث خطأ في قفل المتحركات")


@group_only
@admin_required
async def unlock_gifs(message: Message):
    """فتح المتحركات (GIF)"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['gifs'] = False
        await message.reply("🔓 **تم فتح المتحركه**\nيمكن للأعضاء إرسال المتحركات (GIF) الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح المتحركات: {e}")
        await message.reply("❌ حدث خطأ في فتح المتحركات")


@group_only
@admin_required
async def lock_links(message: Message):
    """قفل الروابط"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['links'] = True
        await message.reply("🔒 **تم قفل الروابط**\nلن يتمكن الأعضاء من إرسال الروابط")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الروابط: {e}")
        await message.reply("❌ حدث خطأ في قفل الروابط")


@group_only
@admin_required
async def unlock_links(message: Message):
    """فتح الروابط"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['links'] = False
        await message.reply("🔓 **تم فتح الروابط**\nيمكن للأعضاء إرسال الروابط الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الروابط: {e}")
        await message.reply("❌ حدث خطأ في فتح الروابط")


@group_only
@admin_required
async def lock_forwarding(message: Message):
    """قفل التوجيه"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['forwarding'] = True
        await message.reply("🔒 **تم قفل التوجيه**\nلن يتمكن الأعضاء من إعادة توجيه الرسائل")
        
    except Exception as e:
        logging.error(f"خطأ في قفل التوجيه: {e}")
        await message.reply("❌ حدث خطأ في قفل التوجيه")


@group_only
@admin_required
async def unlock_forwarding(message: Message):
    """فتح التوجيه"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        group_locks[chat_id]['forwarding'] = False
        await message.reply("🔓 **تم فتح التوجيه**\nيمكن للأعضاء إعادة توجيه الرسائل الآن")
        
    except Exception as e:
        logging.error(f"خطأ في فتح التوجيه: {e}")
        await message.reply("❌ حدث خطأ في فتح التوجيه")


@group_only
@admin_required
async def lock_all_media(message: Message):
    """قفل جميع الوسائط"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        # قفل جميع أنواع الوسائط
        locks = ['photos', 'videos', 'voice', 'stickers', 'gifs', 'links', 'forwarding']
        for lock_type in locks:
            group_locks[chat_id][lock_type] = True
        
        await message.reply("🔒 **تم قفل الكل**\nتم قفل جميع أنواع الوسائط والمحتوى")
        
    except Exception as e:
        logging.error(f"خطأ في قفل الكل: {e}")
        await message.reply("❌ حدث خطأ في قفل جميع الوسائط")


@group_only
@admin_required
async def unlock_all_media(message: Message):
    """فتح جميع الوسائط"""
    try:
        chat_id = message.chat.id
        if chat_id not in group_locks:
            group_locks[chat_id] = {}
        
        # فتح جميع أنواع الوسائط
        locks = ['photos', 'videos', 'voice', 'stickers', 'gifs', 'links', 'forwarding']
        for lock_type in locks:
            group_locks[chat_id][lock_type] = False
        
        await message.reply("🔓 **تم فتح الكل**\nتم فتح جميع أنواع الوسائط والمحتوى")
        
    except Exception as e:
        logging.error(f"خطأ في فتح الكل: {e}")
        await message.reply("❌ حدث خطأ في فتح جميع الوسائط")


def is_media_locked(chat_id: int, media_type: str) -> bool:
    """التحقق من حالة قفل نوع معين من الوسائط"""
    return group_locks.get(chat_id, {}).get(media_type, False)


def get_lock_status(chat_id: int) -> dict:
    """الحصول على حالة جميع الأقفال للمجموعة"""
    return group_locks.get(chat_id, {})
"""
نظام البحث عن الموسيقى
Music Search System
"""

import logging
import re
import aiohttp
import os
from typing import Optional, Dict, Any, List
from aiogram.types import Message

# قاموس الأغاني والروابط (يمكن توسيعه)
MUSIC_DATABASE = {
    "جاب العيد": "https://www.youtube.com/watch?v=xRWJAusCpGU",
    "عيد سعيد": "https://www.youtube.com/watch?v=xRWJAusCpGU",
    "موسيقى العيد": "https://www.youtube.com/watch?v=xRWJAusCpGU"
}

# روابط شائعة لمنصات الموسيقى
MUSIC_PLATFORMS = {
    "youtube": "https://www.youtube.com/results?search_query=",
    "soundcloud": "https://soundcloud.com/search?q=",
    "spotify": "https://open.spotify.com/search/"
}


async def search_youtube_api(query: str) -> Optional[Dict[str, Any]]:
    """البحث في يوتيوب باستخدام API الحقيقي"""
    try:
        api_key = os.getenv('YOUTUBE_API_KEY')
        if not api_key:
            logging.warning("YouTube API Key غير متوفر")
            return None
        
        # تنظيف الاستعلام
        clean_query = query.strip()
        
        # URL للبحث في YouTube API
        api_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': clean_query,
            'type': 'video',
            'maxResults': 5,
            'key': api_key,
            'regionCode': 'SA',  # السعودية للنتائج العربية
            'relevanceLanguage': 'ar'  # اللغة العربية
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if 'items' in data and len(data['items']) > 0:
                        # أخذ أول نتيجة
                        first_result = data['items'][0]
                        video_info = {
                            'title': first_result['snippet']['title'],
                            'video_id': first_result['id']['videoId'],
                            'url': f"https://www.youtube.com/watch?v={first_result['id']['videoId']}",
                            'thumbnail': first_result['snippet']['thumbnails']['default']['url'],
                            'description': first_result['snippet']['description'][:200] + "..." if len(first_result['snippet']['description']) > 200 else first_result['snippet']['description'],
                            'channel': first_result['snippet']['channelTitle']
                        }
                        return video_info
                else:
                    logging.error(f"خطأ في YouTube API: {response.status}")
                    return None
        
    except Exception as e:
        logging.error(f"خطأ في البحث في يوتيوب API: {e}")
        return None


async def search_youtube(query: str) -> Optional[str]:
    """البحث في يوتيوب - احتياطي بدون API"""
    try:
        # تنظيف الاستعلام
        clean_query = query.strip().replace(" ", "+")
        search_url = f"https://www.youtube.com/results?search_query={clean_query}"
        
        return search_url
        
    except Exception as e:
        logging.error(f"خطأ في البحث في يوتيوب: {e}")
        return None


async def search_music_platforms(query: str) -> Dict[str, str]:
    """البحث في منصات الموسيقى المختلفة"""
    try:
        results = {}
        clean_query = query.strip().replace(" ", "+")
        
        for platform, base_url in MUSIC_PLATFORMS.items():
            if platform == "spotify":
                results[platform] = f"{base_url}{clean_query}"
            else:
                results[platform] = f"{base_url}{clean_query}"
        
        return results
        
    except Exception as e:
        logging.error(f"خطأ في البحث في منصات الموسيقى: {e}")
        return {}


async def handle_eid_music_trigger(message: Message) -> bool:
    """معالج الرد على كلمة 'جاب العيد'"""
    try:
        if not message.text:
            return False
        
        text = message.text.lower().strip()
        
        # البحث عن عبارة "جاب العيد"
        if "جاب العيد" in text:
            eid_url = MUSIC_DATABASE.get("جاب العيد")
            
            if eid_url:
                # إرسال الموسيقى كملف صوتي بدلاً من الرابط
                from aiogram.types import URLInputFile
                
                try:
                    # إرسال الملف الصوتي مباشرة بدون نص
                    from aiogram.types import InputFile, FSInputFile
                    import aiohttp
                    import tempfile
                    import os
                    
                    # تحميل الملف مؤقتاً
                    async with aiohttp.ClientSession() as session:
                        async with session.get(eid_url) as response:
                            if response.status == 200:
                                # إنشاء ملف مؤقت
                                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_file:
                                    temp_file.write(await response.read())
                                    temp_path = temp_file.name
                                
                                # إرسال الملف الصوتي بدون أي نص
                                audio_file = FSInputFile(temp_path)
                                await message.reply_audio(audio=audio_file)
                                
                                # حذف الملف المؤقت
                                os.unlink(temp_path)
                            else:
                                # فشل التحميل - أرسل رسالة بدون رابط
                                await message.reply("🎵 العيد جاب العيد! 🎉")
                    
                except Exception as e:
                    logging.error(f"خطأ في إرسال موسيقى العيد: {e}")
                    # في حالة الفشل - رسالة بسيطة فقط بدون نص
                    try:
                        # محاولة إرسال ملف صوتي فارغ صغير أو بدون محتوى
                        await message.reply("🎵")
                    except:
                        # في حالة فشل كل شيء
                        pass
                return True
        
        return False
        
    except Exception as e:
        logging.error(f"خطأ في معالج موسيقى العيد: {e}")
        return False


async def handle_music_search(message: Message) -> bool:
    """معالج البحث عن الموسيقى"""
    try:
        if not message.text:
            return False
        
        text = message.text.strip()
        
        # البحث عن أوامر البحث عن الموسيقى
        music_commands = [
            'ابحث عن اغنية', 'ابحث اغنية', 'بحث اغنية', 'بحث عن اغنية',
            'ابحث عن أغنية', 'ابحث أغنية', 'بحث أغنية', 'بحث عن أغنية',
            'شغل اغنية', 'شغل أغنية', 'تشغيل اغنية', 'تشغيل أغنية',
            'بحث'
        ]
        
        found_command = None
        query = None
        
        for cmd in music_commands:
            if text.startswith(cmd):
                found_command = cmd
                query = text[len(cmd):].strip()
                break
        
        if not found_command or not query:
            return False
        
        # البحث في قاعدة البيانات المحلية أولاً
        local_result = None
        for song_name, url in MUSIC_DATABASE.items():
            if song_name.lower() in query.lower() or query.lower() in song_name.lower():
                local_result = {"name": song_name, "url": url}
                break
        
        if local_result:
            await message.reply(
                f"🎵 **تم العثور على الأغنية!**\n\n"
                f"🎤 **الاسم:** {local_result['name']}\n"
                f"🔗 **الرابط:** {local_result['url']}\n\n"
                f"🎧 **استمتع بالاستماع!**"
            )
            return True
        
        # البحث باستخدام YouTube API الحقيقي
        video_info = await search_youtube_api(query)
        
        if video_info:
            await message.reply(
                f"🎵 **تم العثور على الأغنية!**\n\n"
                f"🎤 **العنوان:** {video_info['title']}\n"
                f"📺 **القناة:** {video_info['channel']}\n"
                f"📝 **الوصف:** {video_info['description']}\n"
                f"\n🔗 **الرابط:** {video_info['url']}"
            )
            return True
        
        # البحث الاحتياطي في المنصات الخارجية
        search_results = await search_music_platforms(query)
        
        if search_results:
            response_text = f"🔍 **نتائج البحث عن:** `{query}`\n\n"
            
            platform_names = {
                "youtube": "🎥 يوتيوب",
                "soundcloud": "🎵 ساوند كلاود", 
                "spotify": "🎧 سبوتيفاي"
            }
            
            for platform, url in search_results.items():
                platform_display = platform_names.get(platform, platform.title())
                response_text += f"{platform_display}\n{url}\n\n"
            
            response_text += "✨ **اختر المنصة المفضلة لك!**"
            
            await message.reply(response_text)
            return True
        else:
            await message.reply(
                f"😔 **لم أتمكن من العثور على:** `{query}`\n\n"
                f"💡 **جرب:**\n"
                f"• تأكد من كتابة اسم الأغنية بشكل صحيح\n"
                f"• استخدم كلمات مفتاحية أقل\n"
                f"• جرب البحث باللغة الإنجليزية"
            )
            return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج البحث عن الموسيقى: {e}")
        return False


async def add_song_to_database(name: str, url: str) -> bool:
    """إضافة أغنية جديدة لقاعدة البيانات"""
    try:
        MUSIC_DATABASE[name] = url
        logging.info(f"تم إضافة أغنية جديدة: {name}")
        return True
        
    except Exception as e:
        logging.error(f"خطأ في إضافة الأغنية: {e}")
        return False


def is_valid_music_url(url: str) -> bool:
    """التحقق من صحة رابط الموسيقى"""
    try:
        music_domains = [
            "youtube.com", "youtu.be", "soundcloud.com", 
            "spotify.com", "music.apple.com", "tidal.com",
            "deezer.com", "pandora.com"
        ]
        
        return any(domain in url.lower() for domain in music_domains)
        
    except Exception:
        return False


async def download_youtube_audio(url: str, title: str) -> Optional[str]:
    """تحميل الصوت من يوتيوب وإرجاع مسار الملف"""
    try:
        import yt_dlp
        import tempfile
        import os
        
        # إنشاء مجلد مؤقت للتحميل
        temp_dir = tempfile.mkdtemp()
        
        # تنظيف اسم الملف
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:50]
        
        # خيارات التحميل
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(temp_dir, f'{safe_title}.%(ext)s'),
            'extractaudio': True,
            'audioformat': 'mp3',
            'audioquality': '192K',
            'quiet': True,
            'no_warnings': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # تحميل الفيديو
            info = ydl.extract_info(url, download=True)
            
            # العثور على الملف المحمل
            for file in os.listdir(temp_dir):
                if file.endswith(('.mp3', '.m4a', '.webm', '.ogg')):
                    return os.path.join(temp_dir, file)
        
        return None
        
    except Exception as e:
        logging.error(f"خطأ في تحميل الصوت: {e}")
        return None


async def handle_music_download(message: Message) -> bool:
    """معالج تحميل الموسيقى"""
    try:
        if not message.text:
            return False
        
        text = message.text.strip()
        
        # البحث عن أوامر التحميل
        download_commands = [
            'تحميل اغنية', 'تحميل أغنية', 'تحميل'
        ]
        
        found_command = None
        query = None
        
        for cmd in download_commands:
            if text.startswith(cmd):
                found_command = cmd
                query = text[len(cmd):].strip()
                break
        
        if not found_command or not query:
            return False
        
        # إرسال رسالة انتظار
        wait_msg = await message.reply("🎵 جاري البحث والتحميل...")
        
        # البحث في قاعدة البيانات المحلية أولاً
        local_result = None
        for song_name, url in MUSIC_DATABASE.items():
            if song_name.lower() in query.lower() or query.lower() in song_name.lower():
                local_result = {"name": song_name, "url": url, "title": song_name}
                break
        
        if local_result:
            # تحميل من قاعدة البيانات المحلية
            file_path = await download_youtube_audio(local_result['url'], local_result['title'])
            
            if file_path and os.path.exists(file_path):
                # إرسال الملف الصوتي
                from aiogram.types import FSInputFile
                audio_file = FSInputFile(file_path)
                await message.reply_audio(audio=audio_file)
                
                # حذف الملف المؤقت
                os.unlink(file_path)
                # حذف المجلد المؤقت
                import shutil
                shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
            else:
                await wait_msg.edit_text("❌ فشل في تحميل الملف الصوتي")
            
            # حذف رسالة الانتظار
            try:
                await wait_msg.delete()
            except:
                pass
            
            return True
        
        # البحث باستخدام YouTube API
        video_info = await search_youtube_api(query)
        
        if video_info:
            # تحميل الملف الصوتي
            file_path = await download_youtube_audio(video_info['url'], video_info['title'])
            
            if file_path and os.path.exists(file_path):
                # إرسال الملف الصوتي بدون نص إضافي
                from aiogram.types import FSInputFile
                audio_file = FSInputFile(file_path)
                await message.reply_audio(audio=audio_file)
                
                # حذف الملف المؤقت
                os.unlink(file_path)
                # حذف المجلد المؤقت
                import shutil
                shutil.rmtree(os.path.dirname(file_path), ignore_errors=True)
            else:
                await wait_msg.edit_text("❌ فشل في تحميل الملف الصوتي")
            
            # حذف رسالة الانتظار
            try:
                await wait_msg.delete()
            except:
                pass
            
            return True
        else:
            await wait_msg.edit_text(f"❌ لم أتمكن من العثور على: `{query}`")
            return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج تحميل الموسيقى: {e}")
        return False


async def handle_add_music_command(message: Message) -> bool:
    """معالج إضافة موسيقى جديدة (للمديرين)"""
    try:
        if not message.from_user or message.chat.type == 'private':
            return False
        
        # التحقق من الصلاحيات
        from config.hierarchy import has_permission, AdminLevel
        user_id = message.from_user.id
        chat_id = message.chat.id
        
        if not has_permission(user_id, AdminLevel.MODERATOR, chat_id):
            return False
        
        text = message.text
        if not (text.startswith('اضف اغنية ') or text.startswith('اضف أغنية ')):
            return False
        
        # استخراج اسم الأغنية والرابط
        parts = text.split(' ', 2)
        if len(parts) < 3:
            await message.reply(
                "❌ **طريقة الاستخدام:**\n\n"
                "`اضف اغنية [الاسم] [الرابط]`\n\n"
                "**مثال:**\n"
                "`اضف اغنية عيد سعيد https://youtube.com/watch?v=...`"
            )
            return True
        
        # تحليل المدخل
        remaining_text = parts[2]
        words = remaining_text.split()
        
        # آخر كلمة يجب أن تكون رابط
        if not words:
            await message.reply("❌ يرجى تحديد اسم الأغنية والرابط")
            return True
        
        url = words[-1]
        name = ' '.join(words[:-1])
        
        if not name or not url:
            await message.reply("❌ يرجى تحديد اسم الأغنية والرابط")
            return True
        
        # التحقق من صحة الرابط
        if not is_valid_music_url(url):
            await message.reply("❌ الرابط غير صحيح، يرجى استخدام رابط من منصة موسيقى معروفة")
            return True
        
        # إضافة الأغنية
        if await add_song_to_database(name, url):
            await message.reply(
                f"✅ **تم إضافة الأغنية بنجاح!**\n\n"
                f"🎵 **الاسم:** {name}\n"
                f"🔗 **الرابط:** {url}\n\n"
                f"الآن يمكن للأعضاء البحث عنها!"
            )
        else:
            await message.reply("❌ فشل في إضافة الأغنية")
        
        return True
        
    except Exception as e:
        logging.error(f"خطأ في معالج إضافة الموسيقى: {e}")
        return False
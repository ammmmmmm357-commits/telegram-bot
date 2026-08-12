import os
import re
import asyncio
import logging
from typing import Dict, Any

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
)
from telegram.constants import ParseMode

class Config:
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TIMEOUT = 45
    if not BOT_TOKEN:
        raise ValueError("❌ خطأ: لم يتم العثور على TELEGRAM_BOT_TOKEN!")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log", encoding="utf-8")]
)
logger = logging.getLogger(__name__)

def is_youtube_url(url: str) -> bool:
    return bool(re.match(r'(https?://)?(www\.)?(youtube\.com|youtu\.be|youtube\.com/shorts)/.+', url))

def format_duration(seconds: int) -> str:
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    if h > 0: return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

async def async_extract_info(url: str) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, sync_extract_info, url)

def sync_extract_info(url: str) -> Dict[str, Any]:
    ydl_opts = {'quiet': True, 'no_warnings': True, 'socket_timeout': Config.TIMEOUT}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            video_formats, audio_formats = [], []
            for f in info.get('formats', []):
                if f.get('vcodec') != 'none' and f.get('acodec') != 'none':
                    video_formats.append(f)
                elif f.get('vcodec') == 'none' and f.get('acodec') != 'none':
                    audio_formats.append(f)
            return {
                'success': True,
                'title': info.get('title', 'عنوان غير معروف'),
                'uploader': info.get('uploader', 'قناة غير معروفة'),
                'duration': info.get('duration', 0),
                'views': info.get('view_count', 0),
                'thumbnail': info.get('thumbnail'),
                'video_formats': video_formats,
                'audio_formats': audio_formats,
                'url': url
            }
    except yt_dlp.utils.DownloadError:
        return {'success': False, 'error': 'الرابط غير صحيح أو الفيديو خاص 🚫'}
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        return {'success': False, 'error': f'حدث خطأ: {str(e)[:50]}'}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 **مرحباً بك في بوت تحميل YouTube!**\n\n"
        "🔹 أرسل لي رابط فيديو يوتيوب.\n"
        "🔹 سأعرض لك معلومات الفيديو مع أزرار التحميل.\n\n"
        "_يمكنك اختيار تحميل الفيديو أو الصوت فقط._",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_youtube_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not is_youtube_url(text):
        await update.message.reply_text("❌ الرابط غير صحيح، يرجى إرسال رابط يوتيوب صالح.")
        return
    msg = await update.message.reply_text("⏳ جاري استخراج معلومات الفيديو...")
    try:
        info = await async_extract_info(text)
        if not info['success']:
            await msg.edit_text(f"❌ {info['error']}")
            return
        caption = (
            f"**{info['title']}**\n\n"
            f"👤 **القناة:** `{info['uploader']}`\n"
            f"⏱ **المدة:** `{format_duration(info['duration'])}`\n"
            f"👁 **المشاهدات:** `{info['views']}`\n\n"
            f"_اختر نوع التحميل من الأسفل:_"
        )
        keyboard = []
        if info['video_formats']:
            keyboard.append([InlineKeyboardButton("🎬 مقطع فيديو", callback_data=f"v|{info['url']}")])
        if info['audio_formats']:
            keyboard.append([InlineKeyboardButton("🎵 ملف صوتي", callback_data=f"a|{info['url']}")])
        if info['thumbnail']:
            await msg.delete()
            await update.message.reply_photo(
                photo=info['thumbnail'],
                caption=caption,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await msg.edit_text(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=InlineKeyboardMarkup(keyboard))
    except Exception as e:
        logger.error(f"Error: {e}")
        await msg.edit_text("💥 حدث خطأ غير متوقع.")

async def download_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('|')
    dl_type = data[0]
    dl_url = data[1]
    await query.edit_message_text("⏳ جاري تحميل الملف، يرجى الانتظار...")
    try:
        loop = asyncio.get_running_loop()
        opts = {'quiet': True, 'socket_timeout': 60}
        if dl_type == "v":
            opts['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]'
            file_name = f"video_{int(asyncio.get_event_loop().time())}.mp4"
        elif dl_type == "a":
            opts['format'] = 'bestaudio[ext=m4a]'
            file_name = f"audio_{int(asyncio.get_event_loop().time())}.m4a"
        filepath = await loop.run_in_executor(None, download_sync, dl_url, opts, file_name)
        if dl_type == "v":
            await query.message.reply_video(video=open(filepath, 'rb'), caption="🎬 تم تحميل المقطع بنجاح!")
        elif dl_type == "a":
            await query.message.reply_audio(audio=open(filepath, 'rb'), caption="🎵 تم تحميل الملف الصوتي!")
        await query.edit_message_text("✅ تم إرسال الملف بنجاح!")
        os.remove(filepath)
    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text("❌ حدث خطأ أثناء التحميل، قد يكون حجم الملف كبيراً جداً.")

def download_sync(url, opts, filename):
    opts['outtmpl'] = filename
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])
        return filename

def main():
    app = Application.builder().token(Config.BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_youtube_url))
    app.add_handler(CallbackQueryHandler(download_buttons, pattern="^(v|a)\|.+"))
    logger.info("🚀 تشغيل بوت التحميل!")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()
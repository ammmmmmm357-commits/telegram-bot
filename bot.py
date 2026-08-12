import os
import re
import asyncio
import logging
from datetime import datetime
from typing import Optional, Dict, Any

import yt_dlp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    JobQueue
)
from telegram.constants import ParseMode
from telegram.error import TelegramError

# ==========================================
# 1. الإعدادات الأساسية (Configuration)
# ==========================================
class Config:
    # ✅ هنا يتم استيراد التوكن من متغيرات البيئة (Railway Variables)
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TIMEOUT = 30
    MAX_DESCRIPTION_LENGTH = 200
    
    # التحقق من وجود التوكن قبل تشغيل البوت
    if not BOT_TOKEN:
        raise ValueError("❌ خطأ: لم يتم العثور على TELEGRAM_BOT_TOKEN في متغيرات البيئة!")

# ==========================================
# 2. إعدادات السجلات (Logging)
# ==========================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("bot.log", encoding="utf-8")
    ]
)
logger = logging.getLogger(__name__)

# ==========================================
# 3. دوال المساعدة المتقدمة (Utils)
# ==========================================

def _validate_youtube_url(url: str) -> bool:
    """فحص الرابط بشكل دقيق (Regex)"""
    pattern = r'(https?://)?(www\.)?(youtube\.com/watch\?v=|youtu\.be/|youtube\.com/shorts/)[a-zA-Z0-9_-]+'
    return bool(re.match(pattern, url))

def _format_duration(seconds: int) -> str:
    if not seconds:
        return "غير معروف"
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h}:{m:02d}:{s:02d}" if h > 0 else f"{m}:{s:02d}"

def _format_views(views: Optional[int]) -> str:
    if not views: return "N/A"
    if views >= 1_000_000: return f"{views / 1_000_000:.1f}مليون"
    if views >= 1_000: return f"{views / 1_000:.1f}ألف"
    return str(views)

# ==========================================
# 4. وظيفة استخراج المعلومات (Async Safe)
# ==========================================

async def _async_extract_info(url: str) -> Dict[str, Any]:
    """تشغيل yt-dlp بشكل غير متزامن لعزل الضغط عن البوت"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _sync_extract_info, url)

def _sync_extract_info(url: str) -> Dict[str, Any]:
    """الكود المتزامن الحقيقي الذي يعمل في الخلفية"""
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': Config.TIMEOUT,
        'extract_flat': False
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            description = info.get('description', 'لا يوجد وصف')
            if len(description) > Config.MAX_DESCRIPTION_LENGTH:
                description = description[:Config.MAX_DESCRIPTION_LENGTH] + '...'

            return {
                'success': True,
                'title': info.get('title', 'عنوان غير معروف'),
                'uploader': info.get('uploader', 'قناة غير معروفة'),
                'duration': info.get('duration', 0),
                'views': info.get('view_count'),
                'upload_date': info.get('upload_date', 'غير معروف'),
                'description': description,
                'thumbnail': info.get('thumbnail'),
                'formats_count': len(info.get('formats', [])),
                'url': url
            }
    except yt_dlp.utils.DownloadError:
        return {'success': False, 'error': 'الرابط غير صحيح أو الفيديو خاص/محظور 🚫'}
    except Exception as e:
        logger.error(f"yt-dlp error: {e}")
        return {'success': False, 'error': f'خطأ في الاتصال بـ YouTube ⚠️'}

# ==========================================
# 5. الدوال الأساسية للبوت (Handlers)
# ==========================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر البدء"""
    user = update.effective_user
    await update.message.reply_text(
        f"👋 مرحباً بك {user.first_name}!\n\n"
        "أنا بوت احترافي لاستخراج معلومات فيديوهات يوتيوب.\n"
        "❓ **كيف تستعملني؟**\n"
        "• أرسل رابط فيديو YouTube مباشرة.\n"
        "• أو استخدم الأمر: `/info <رابط>`\n\n"
        "✅ سأقوم بتحليل الرابط وإظهار التفاصيل لك.",
        parse_mode=ParseMode.MARKDOWN
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التعامل مع الرسائل النصية"""
    text = update.message.text
    if not text:
        return
        
    # إذا كان الرابط داخل رسالة، استخرجه وقم بالمعالجة
    if _validate_youtube_url(text):
        await process_video(update, context, text)
    else:
        await update.message.reply_text("🔍 يرجى إرسال رابط يوتيوب صحيح للبحث عنه.")

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
    """معالجة الفيديو وعرض النتائج"""
    msg = await update.message.reply_text("⏳ جاري استخراج معلومات الفيديو... يرجى الانتظار.")
    
    try:
        info = await _async_extract_info(url)
        await msg.delete()
        
        if not info['success']:
            await update.message.reply_text(f"❌ **خطأ:** {info['error']}", parse_mode=ParseMode.MARKDOWN)
            return

        # تنسيق التاريخ
        upload_date = info['upload_date']
        if upload_date != 'غير معروف' and len(str(upload_date)) == 8:
            try:
                date_obj = datetime.strptime(str(upload_date), '%Y%m%d')
                upload_date = date_obj.strftime('%d/%m/%Y')
            except:
                pass

        response = (
            f"✅ **معلومات الفيديو**\n\n"
            f"📝 **العنوان:**\n_{info['title']}_\n\n"
            f"👤 **القناة:** `{info['uploader']}`\n"
            f"⏱ **المدة:** `{_format_duration(info['duration'])}`\n"
            f"👁 **المشاهدات:** `{_format_views(info['views'])}`\n"
            f"📅 **تاريخ الرفع:** `{upload_date}`\n"
            f"🎥 **الصيغ المتاحة:** `{info['formats_count']} صيغة`\n\n"
            f"📋 **ملخص الوصف:**\n__{info['description']}__"
        )
        
        await update.message.reply_text(
            response,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📂 فيديو جديد", callback_data="new")]
            ])
        )
        
    except asyncio.TimeoutError:
        await msg.edit_text("⏰ استغرق الطلب وقتاً طويلاً، حاول مرة أخرى.")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        await msg.edit_text("💥 حدث خطأ داخلي غير متوقع.")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار"""
    query = update.callback_query
    await query.answer()
    if query.data == "new":
        await query.edit_message_text("📌 أرسل لي رابط يوتيوب جديد لبدء البحث.")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأخطاء المتقدم"""
    logger.error(f"حدث خطأ: {context.error}", exc_info=context.error)
    if update and hasattr(update, 'effective_message'):
        await update.effective_message.reply_text(
            "🚨 حدث عطل تقني. حاول مجدداً لاحقاً."
        )

# ==========================================
# 6. تشغيل البوت (Main Entry Point)
# ==========================================
def main():
    if not Config.BOT_TOKEN:
        return # سيتم إيقافه بواسطة الـ ValueError في كلاس Config

    app = Application.builder().token(Config.BOT_TOKEN).build()

    # تسجيل المعالجات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("info", handle_message)) # دعم أمر /info
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback, pattern="new"))
    app.add_error_handler(error_handler)

    logger.info("⚡ البوت يعمل على أعلى مستوى احترافي!")
    print("="*50)
    print("✅ بوت يوتيوب يعمل الآن!")
    print("="*50)
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
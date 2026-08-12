import logging
import os
import re
from datetime import datetime
from typing import Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler
)
from telegram.error import TelegramError
import yt_dlp

# ============ Configuration ============
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ TELEGRAM_BOT_TOKEN environment variable not set!")

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("bot.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants
TIMEOUT = 30
MAX_DESCRIPTION_LENGTH = 200
MODES = {"get_info": "📊 معلومات الفيديو", "download": "⬇️ تحميل الفيديو"}
GET_INFO, AWAITING_URL = range(2)


# ============ Utility Functions ============
def is_valid_youtube_url(url: str) -> bool:
    """Validate if URL is a YouTube link"""
    youtube_regex = r'(https?://)?(www\.)?(youtube|youtu|youtube-nocookie)\.(com|be)/'
    return bool(re.match(youtube_regex, url))


def format_duration(seconds: int) -> str:
    """Format duration in seconds to HH:MM:SS"""
    if not seconds:
        return "Unknown"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"


def format_views(views: Optional[int]) -> str:
    """Format view count"""
    if not views:
        return "N/A"
    if views >= 1_000_000:
        return f"{views / 1_000_000:.1f}M"
    elif views >= 1_000:
        return f"{views / 1_000:.1f}K"
    return str(views)


async def get_video_info(url: str) -> dict:
    """Extract video information using yt-dlp"""
    try:
        ydl_opts = {
            'format': 'best',
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': TIMEOUT,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Extracting info from: {url}")
            info = ydl.extract_info(url, download=False)
            
            return {
                'success': True,
                'title': info.get('title', 'Unknown'),
                'uploader': info.get('uploader', 'Unknown'),
                'duration': info.get('duration', 0),
                'views': info.get('view_count', None),
                'upload_date': info.get('upload_date', 'Unknown'),
                'description': (info.get('description', '')[:MAX_DESCRIPTION_LENGTH] + '...') 
                    if info.get('description') else 'No description',
                'thumbnail': info.get('thumbnail'),
                'formats_count': len(info.get('formats', [])),
                'url': url
            }
    except yt_dlp.utils.DownloadError as e:
        logger.error(f"Download error: {e}")
        return {
            'success': False,
            'error': "الرابط غير صحيح أو الفيديو غير متاح 🔗❌"
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {
            'success': False,
            'error': f"خطأ في الاتصال: {str(e)[:100]} 🚨"
        }


def create_info_message(info: dict) -> str:
    """Format video info into a nice message"""
    if not info['success']:
        return f"❌ {info['error']}"
    
    date_formatted = "Unknown"
    if info['upload_date'] != 'Unknown':
        try:
            date_obj = datetime.strptime(info['upload_date'], '%Y%m%d')
            date_formatted = date_obj.strftime('%d/%m/%Y')
        except:
            pass
    
    message = (
        f"✅ *معلومات الفيديو*\n\n"
        f"📝 *العنوان:*\n_{info['title']}_\n\n"
        f"👤 *القناة:* `{info['uploader']}`\n\n"
        f"⏱ *المدة:* `{format_duration(info['duration'])}`\n\n"
        f"👁 *المشاهدات:* `{format_views(info['views'])}`\n\n"
        f"📅 *تاريخ الرفع:* `{date_formatted}`\n\n"
        f"📋 *الوصف:* __{info['description']}__\n\n"
        f"🎥 *الصيغ المتاحة:* `{info['formats_count']} صيغة`"
    )
    return message


# ============ Bot Handlers ============
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start command handler"""
    user = update.effective_user
    logger.info(f"User {user.id} started the bot")
    
    keyboard = [
        [InlineKeyboardButton("📊 معلومات الفيديو", callback_data="get_info")],
        [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")]
    ]
    
    welcome_text = (
        f"مرحباً بك 👋 {user.first_name}!\n\n"
        "أنا بوت متخصص لاستخراج معلومات فيديوهات YouTube\n\n"
        "✨ *المميزات:*\n"
        "• عرض معلومات الفيديو\n"
        "• عدد المشاهدات والتاريخ\n"
        "• جودات التحميل المتاحة\n\n"
        "📌 فقط أرسل رابط YouTube وسأتولى الباقي!"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
    return GET_INFO


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Help button handler"""
    query = update.callback_query
    await query.answer()
    
    help_text = (
        "*🆘 مساعدة*\n\n"
        "1️⃣ اختر 'معلومات الفيديو'\n"
        "2️⃣ أرسل رابط YouTube صحيح\n"
        "3️⃣ انتظر النتائج\n\n"
        "*✅ الروابط المقبولة:*\n"
        "• `https://www.youtube.com/watch?v=...`\n"
        "• `https://youtu.be/...`\n"
        "• `https://www.youtube.com/shorts/...`\n\n"
        "*📝 ملاحظات:*\n"
        "• تأكد من اتصال الإنترنت\n"
        "• الفيديو يجب أن يكون متاحاً عموماً\n"
        "• قد تستغرق العملية بضع ثوانٍ"
    )
    
    await query.edit_message_text(
        help_text,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ])
    )
    return GET_INFO


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "help":
        await help_callback(update, context)
    elif query.data == "back":
        keyboard = [
            [InlineKeyboardButton("📊 معلومات الفيديو", callback_data="get_info")],
            [InlineKeyboardButton("ℹ️ مساعدة", callback_data="help")]
        ]
        await query.edit_message_text(
            "اختر ما تريد أن تفعل:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    elif query.data == "get_info":
        await query.edit_message_text(
            "📌 *الآن:* أرسل لي رابط YouTube\n"
            "_جاهز لاستخراج المعلومات!_",
            parse_mode='Markdown'
        )
        return AWAITING_URL


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle URL input"""
    url = update.message.text.strip()
    user = update.effective_user
    
    logger.info(f"User {user.id} sent URL: {url}")
    
    # Validate URL
    if not is_valid_youtube_url(url):
        await update.message.reply_text(
            "❌ *خطأ:* الرابط لا يبدو أنه من YouTube!\n\n"
            "تأكد من صحة الرابط وأرسله مجدداً.",
            parse_mode='Markdown'
        )
        return AWAITING_URL
    
    # Show processing message
    processing_msg = await update.message.reply_text(
        "⏳ جاري معالجة الطلب...",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ إلغاء", callback_data="cancel")]
        ])
    )
    
    try:
        # Get video info
        info = await get_video_info(url)
        
        # Create response
        response_text = create_info_message(info)
        
        # Delete processing message
        await processing_msg.delete()
        
        # Send result
        await update.message.reply_text(
            response_text,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🔍 فيديو جديد", callback_data="get_info")],
                [InlineKeyboardButton("🏠 القائمة الرئيسية", callback_data="back")]
            ])
        )
        
    except TelegramError as e:
        logger.error(f"Telegram error: {e}")
        await update.message.reply_text("❌ حدث خطأ في الاتصال!")
    except Exception as e:
        logger.error(f"Error: {e}")
        await update.message.reply_text(f"❌ خطأ غير متوقع: {str(e)[:100]}")
    
    return GET_INFO


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors"""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "😔 حدث خطأ. حاول مجدداً من فضلك."
            )
        except TelegramError:
            pass


# ============ Main ============
def main():
    """Start the bot"""
    try:
        # Create app
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CallbackQueryHandler(button_callback))
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url)
        )
        
        # Error handler
        app.add_error_handler(error_handler)
        
        # Start bot
        logger.info("🚀 Bot started successfully!")
        print("=" * 50)
        print("✅ البوت يعمل الآن!")
        print("=" * 50)
        
        app.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        print("\n❌ تم إيقاف البوت")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"❌ خطأ حرج: {e}")


if __name__ == '__main__':
    main()

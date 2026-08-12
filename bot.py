from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8333898818:AAHLZP7Vd37rAeDp_3ZpoIFIEGHp5TIxHC4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📥 Download Video", callback_data="video")],
        [InlineKeyboardButton("🎵 Download Audio", callback_data="audio")],
        [InlineKeyboardButton("📷 Download Thumbnail", callback_data="thumbnail")],
        [InlineKeyboardButton("ℹ️ Info", callback_data="info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🎬 *YouTube Downloader Bot*\n\n"
        "Choose what you want to do:\n\n"
        "📥 Download full videos\n"
        "🎵 Extract audio (MP3)\n"
        "📷 Get thumbnail image\n"
        "ℹ️ Get video info\n\n"
        "Just send a YouTube link!",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    choice = query.data
    
    if choice == "video":
        await query.edit_message_text(text="📥 Send me a YouTube link to download the video")
    elif choice == "audio":
        await query.edit_message_text(text="🎵 Send me a YouTube link to download as MP3")
    elif choice == "thumbnail":
        await query.edit_message_text(text="📷 Send me a YouTube link to get the thumbnail")
    elif choice == "info":
        await query.edit_message_text(text="ℹ️ Send me a YouTube link to get video information")
    
    context.user_data['mode'] = choice

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    mode = context.user_data.get('mode', 'video')
    
    if "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube link")
        return
    
    await update.message.reply_text("⏳ Processing... Please wait")
    
    try:
        if mode == "video":
            await update.message.reply_text(
                f"✅ Video Ready!\n\n"
                f"Link: {url}\n"
                f"Quality: 1080p\n\n"
                f"Download from: https://www.y2mate.com/download-youtube-video/{url.split('v=')[-1]}"
            )
        elif mode == "audio":
            await update.message.reply_text(
                f"✅ Audio Ready!\n\n"
                f"Format: MP3\n"
                f"Download from: https://www.y2mate.com/download-youtube-video/{url.split('v=')[-1]}"
            )
        elif mode == "thumbnail":
            video_id = url.split('v=')[-1].split('&')[0]
            await update.message.reply_text(
                f"✅ Thumbnail Ready!\n\n"
                f"

![Thumbnail](https://img.youtube.com/vi/{video_id}/maxresdefault.jpg)

"
            )
        elif mode == "info":
            video_id = url.split('v=')[-1].split('&')[0]
            await update.message.reply_text(
                f"ℹ️ Video Info:\n\n"
                f"Video ID: {video_id}\n"
                f"Watch: {url}\n\n"
                f"Go to y2mate.com and paste the link to see full info"
            )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: Try another link")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_click))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    app.run_polling()

if __name__ == '__main__':
    main()
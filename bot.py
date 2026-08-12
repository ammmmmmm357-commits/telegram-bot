from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8333898818:AAHLZP7Vd37rAeDp_3ZpoIFIEGHp5TIxHC4"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("Download Video", callback_data="download_video"),
            InlineKeyboardButton("Download Audio", callback_data="download_audio")
        ],
        [
            InlineKeyboardButton("Get Info", callback_data="get_info"),
            InlineKeyboardButton("Help", callback_data="help")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Welcome {user.first_name}!\n\n"
        "YouTube Downloader Bot\n\n"
        "Choose an option or send a YouTube link",
        reply_markup=reply_markup
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    action = query.data
    
    messages = {
        "download_video": "Send a YouTube link to download video",
        "download_audio": "Send a YouTube link to download as MP3",
        "get_info": "Send a YouTube link to get video information",
        "help": "Send any YouTube link\n\nFormats: video, audio, thumbnail"
    }
    
    await query.edit_message_text(text=messages.get(action, "Unknown"))
    context.user_data['mode'] = action

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    mode = context.user_data.get('mode', 'download_video')
    
    if "youtu" not in url and "youtube" not in url:
        await update.message.reply_text("Invalid YouTube link")
        return
    
    video_id = ""
    if "v=" in url:
        video_id = url.split("v=")[-1].split("&")[0]
    elif "youtu.be" in url:
        video_id = url.split("/")[-1].split("?")[0]
    
    if not video_id:
        await update.message.reply_text("Could not extract video ID")
        return
    
    download_url = f"https://www.y2mate.com/download-youtube-video/{video_id}"
    
    if mode == "download_video":
        await update.message.reply_text(f"Video Download:\n{download_url}")
    elif mode == "download_audio":
        await update.message.reply_text(f"Audio (MP3):\n{download_url}")
    elif mode == "get_info":
        await update.message.reply_text(f"Video ID: {video_id}\n\n{download_url}")
    else:
        await update.message.reply_text(download_url)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "YouTube Downloader Bot\n\n"
        "/start - Start\n"
        "/help - Help\n\n"
        "Send YouTube link to download"
    )
    await update.message.reply_text(help_text)

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    app.run_polling()

if __name__ == '__main__':
    main()
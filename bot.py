import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
import yt_dlp

BOT_TOKEN = "8333898818:AAFaM7glgRRv8nTN3RrHT6c_OYBCAYNjx5I"

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Get Info", callback_data="get_info")],
        [InlineKeyboardButton("Help", callback_data="help")]
    ]
    await update.message.reply_text("Hello! Send a YouTube link and I will fetch the video information for you.", 
                                    reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "help":
        await query.edit_message_text("Send any YouTube link and I will extract its information for you.")
    else:
        context.user_data['mode'] = query.data
        await query.edit_message_text("Great, now send the YouTube link:")

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text("Fetching data, please wait...")
    
    try:
        ydl_opts = {'format': 'best'}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            uploader = info.get('uploader', 'Unknown')
            
            response = (
                f"✅ **Video Found:**\n\n"
                f"📝 Title: {title}\n"
                f"👤 Channel: {uploader}\n"
                f"⏱ Duration: {duration // 60} minutes and {duration % 60} seconds\n"
            )
            await update.message.reply_text(response, parse_mode='Markdown')
            
    except Exception as e:
        await update.message.reply_text(f"Sorry, an error occurred while fetching data: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

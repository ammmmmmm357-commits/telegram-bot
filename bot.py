from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import requests

BOT_TOKEN = "8333898818:AAGIpDv5KfhdlBtkemWvLRV1vulJVlRR-g0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a YouTube link and I'll get the download link for you")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "youtu" not in url:
        await update.message.reply_text("Please send a valid YouTube link")
        return
    
    await update.message.reply_text("⏳ Processing... Please wait")
    
    try:
        # Use free API to get download link
        api_url = f"https://www.y2mate.com/api/ajax/search"
        
        # Alternative: Simple method - send the URL formatted
        video_id = url.split("v=")[-1].split("&")[0]
        
        download_link = f"https://www.y2mate.com/download-youtube-video/{video_id}"
        
        await update.message.reply_text(
            f"✅ Download link ready!\n\n"
            f"Click here to download: {download_link}\n\n"
            f"Choose quality and format on the website"
        )
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()

if __name__ == '__main__':
    main()
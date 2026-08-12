from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from pytube import YouTube

BOT_TOKEN = "8333898818:AAGIpDv5KfhdlBtkemWvLRV1vulJVlRR-g0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a YouTube link to download")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "youtu" not in url:
        await update.message.reply_text("Please send a valid YouTube link")
        return
    
    await update.message.reply_text("⏳ Processing... Please wait")
    
    try:
        yt = YouTube(url)
        
        # Get best quality
        stream = yt.streams.get_highest_resolution()
        
        info = f"""
✅ Title: {yt.title}
📏 Duration: {yt.length // 60} minutes
👁 Views: {yt.views:,}
📊 Quality: {stream.resolution}
💾 Size: ~{stream.filesize // (1024*1024)} MB

Download link ready!
Click on the link below to download from y2mate or similar service:
https://www.y2mate.com/download-youtube-video/{url.split('v=')[-1]}
        """
        
        await update.message.reply_text(info)
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: Try another link")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()

if __name__ == '__main__':
    main()
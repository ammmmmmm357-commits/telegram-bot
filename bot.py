from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import os
import subprocess

BOT_TOKEN = "8333898818:AAGIpDv5KfhdlBtkemWvLRV1vulJVlRR-g0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! Send me a YouTube link to download\n\nFormats:\n🎬 Video\n🎵 Audio\n📷 Thumbnail")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    
    if "youtu" not in url:
        await update.message.reply_text("Please send a valid YouTube link")
        return
    
    await update.message.reply_text("⏳ Downloading... This may take a minute")
    
    try:
        # Create downloads folder
        os.makedirs("downloads", exist_ok=True)
        
        # Download best quality
        cmd = f'yt-dlp -f "best[ext=mp4]" -o "downloads/%(title)s.%(ext)s" "{url}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        # Find downloaded file
        files = os.listdir("downloads")
        if files:
            file_path = f"downloads/{files[0]}"
            file_size = os.path.getsize(file_path) / (1024 * 1024)  # MB
            
            if file_size > 50:  # If larger than 50MB, send link instead
                await update.message.reply_text(f"✅ Downloaded successfully!\n\nFile size: {file_size:.1f}MB\n\nFile is too large to send via Telegram.\nYou can download it from: {url}")
            else:
                with open(file_path, 'rb') as video:
                    await update.message.reply_video(video)
                    await update.message.reply_text("✅ Download complete!")
            
            # Clean up
            os.remove(file_path)
        else:
            await update.message.reply_text("❌ Failed to download. Try another link")
    
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {str(e)}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()

if __name__ == '__main__':
    main()
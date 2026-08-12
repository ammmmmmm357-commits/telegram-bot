from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

BOT_TOKEN = "8333898818:AAGIpDv5KfhdlBtkemWvLRV1vulJVlRR-g0"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am a download bot\nSend me any link")

async def download(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    await update.message.reply_text(f"Received: {url}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download))
    app.run_polling()

if __name__ == '__main__':
    main()
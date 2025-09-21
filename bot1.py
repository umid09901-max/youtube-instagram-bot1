import os, re, asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

def sanitize_filename(name):
    import re
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:100]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Salom! YouTube yoki Instagram havolasini yuboring…", parse_mode="Markdown")

async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎬 Yana qaysi videoni yuklashni xohlaysiz? Havolani yuboring 👇")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    msg = await update.message.reply_text("⏳ Yuklab olinyapti...")
    ydl_opts = {'format': 'best[ext=mp4]/best', 'outtmpl': 'downloads/' + sanitize_filename('%(title)s.%(ext)s'), 'noplaylist': True, 'merge_output_format':'mp4','quiet': True,'no_warnings': True}
    loop = asyncio.get_event_loop()
    info = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(url, download=True))
    filename = yt_dlp.YoutubeDL(ydl_opts).prepare_filename(info)
    with open(filename,'rb') as f:
        await update.message.reply_video(video=f)

application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
application.add_handler(CallbackQueryHandler(restart_handler, pattern='^restart$'))

if __name__ == "__main__":
    application.run_webhook(
        listen="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
        url_path=TOKEN,
        webhook_url=f"{WEBHOOK_URL}/{TOKEN}"
    )



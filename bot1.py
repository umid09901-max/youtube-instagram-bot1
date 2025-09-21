import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
import yt_dlp
from flask import Flask, request

# 🔑 TOKEN va WEBHOOK_URL
TOKEN = os.getenv("TOKEN")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Render yoki Railway dagi https://... URL

# Flask app (Render uchun)
app = Flask(__name__)

# 📝 Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# 🧹 Fayl nomini tozalash
def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:100]

# 🎬 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! YouTube yoki Instagram havolasini yuboring — men videoni yuklab beraman.\n"
        "Masalan: `https://youtu.be/dQw4w9WgXcQ` yoki `https://www.instagram.com/reel/.../`",
        parse_mode="Markdown"
    )

# 🔄 Restart tugmasi
async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎬 Yana qaysi videoni yuklashni xohlaysiz? Havolani yuboring 👇")

# 📥 Video yuklab olish
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ To‘g‘ri URL yuboring. Masalan: `https://youtu.be/...`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("⏳ Yuklab olinyapti... kuting.")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': 'downloads/' + sanitize_filename('%(title)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        if not os.path.exists(filename):
            raise FileNotFoundError("❌ Fayl yuklanmadi.")

        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await msg.edit_text("⚠️ Video 50 MB dan katta. Telegram yubora olmaydi.")
            os.remove(filename)
            return

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)

        keyboard = [[InlineKeyboardButton("🔄 Yana yuklash", callback_data='restart')]]
        await msg.edit_text("✅ Tayyor!", reply_markup=InlineKeyboardMarkup(keyboard))

        os.remove(filename)

    except Exception as e:
        await msg.edit_text(f"❌ Xatolik: {str(e)[:200]}")

# 🚀 Telegram botni yaratish
application = Application.builder().token(TOKEN).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
application.add_handler(CallbackQueryHandler(restart_handler, pattern='^restart$'))

# 🌐 Flask bilan Webhook
@app.route(f"/{TOKEN}", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    application.update_queue.put_nowait(update)
    return "OK", 200

@app.route("/", methods=["GET"])
def home():
    return "Bot ishlayapti 🚀", 200

def main():
    # Webhook o‘rnatish
    application.bot.set_webhook(url=f"{WEBHOOK_URL}/{TOKEN}")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))

if __name__ == "__main__":
    main()




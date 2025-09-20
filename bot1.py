import logging
import os
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import yt_dlp

# 🔑 SIZNING BOT TOKENINGIZ — Buni o'zgartiring!
TOKEN = os.getenv("Bot token")

# 📝 Logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# 🧹 Fayl nomini tozalash
def sanitize_filename(name):
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name[:100]

# 🎬 /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! YouTube yoki Instagram havolasini yuboring — men videoni yuklab beraman.\n"
        "Masalan: `https://youtu.be/dQw4w9WgXcQ` yoki `https://www.instagram.com/reel/CzABC123XYZ/`",
        parse_mode="Markdown"
    )

# 🔄 Restart tugmasi
async def restart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.message.reply_text("🎬 Yana qaysi videoni yuklashni xoxlaysiz? Havolani yuboring 👇")

# 📥 Video yuklab olish — BARCHA XATOLIKLARNI BOSHQARUVCHI
async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("❌ Iltimos, to'g'ri URL havola yuboring. Masalan: `https://youtu.be/...`", parse_mode="Markdown")
        return

    msg = await update.message.reply_text("⏳ Videoni yuklab olmoqdaman... Iltimos, 10-30 soniya kuting.")

    if not os.path.exists('downloads'):
        os.makedirs('downloads')

    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': 'downloads/' + sanitize_filename('%(title)s.%(ext)s'),
        'noplaylist': True,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36',
        'retries': 3,
        'fragment_retries': 3,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)

        # Fayl mavjudligini tekshirish
        if not os.path.exists(filename):
            raise FileNotFoundError("Fayl yuklanmadi — format topilmadi yoki video yo'q.")

        # Hajmni tekshirish (Telegram 50MB chegarasi)
        file_size = os.path.getsize(filename)
        if file_size > 50 * 1024 * 1024:
            await msg.edit_text(
                "⚠️ Ushbu video hajmi 50 MB dan oshib ketdi. Telegram chegarasi sababli yubora olmayman.\n"
                "Iltimos, boshqa video yuboring yoki pastroq sifatda yuklab olishni sinab ko'ring."
            )
            os.remove(filename)
            return

        # Video yuborish
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(video=video_file)

        # Tugma qo'shish
        keyboard = [[InlineKeyboardButton("🔄 Boshqa video yuklash", callback_data='restart')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await msg.edit_text("✅ Video muvaffaqiyatli yuborildi!", reply_markup=reply_markup)

        # Faylni o'chirish
        os.remove(filename)

    except Exception as e:
        error_msg = str(e)

        if "Requested format is not available" in error_msg or "No video formats found" in error_msg:
            await msg.edit_text(
                "⚠️ Ushbu havoladan video topilmadi. Sabablari:\n"
                "• Postda faqat rasm bor\n"
                "• Akkaunt yopiq (private)\n"
                "• Video o'chirilgan yoki cheklangan\n\n"
                "Iltimos, boshqa havola yuboring."
            )
        elif "HTTP Error 404" in error_msg or "Video unavailable" in error_msg:
            await msg.edit_text("❌ Video topilmadi yoki o'chirilgan. Iltimos, boshqa havola yuboring.")
        elif "not a valid URL" in error_msg:
            await msg.edit_text("❌ Noto'g'ri URL. Iltimos, YouTube yoki Instagram havolasini yuboring.")
        else:
            await msg.edit_text(
                f"❌ Noto'g'ri xatolik yuz berdi:\n`{error_msg[:200]}`\n\n"
                "Iltimos, boshqa havola yuboring yoki keyinroq urinib ko'ring.",
                parse_mode="Markdown"
            )

# 🚀 Asosiy funksiya
def main():
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_handler(CallbackQueryHandler(restart_handler, pattern='^restart$'))

    logger.info("✅ Bot ishga tushdi! Telegramda sinab ko'ring.")
    application.run_polling()

# 🏁 Ishga tushirish
if __name__ == '__main__':

    main()

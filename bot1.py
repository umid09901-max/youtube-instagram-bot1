import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("TOKEN")

if not TOKEN:
    raise ValueError("❌ TOKEN environment variable topilmadi! Render settings'da to‘g‘ri qo‘shganingni tekshir.")

async def start(update, context):
    await update.message.reply_text("Salom! Bot Render'da ishlayapti 🚀")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("✅ Bot ishga tushdi...")
app.run_polling()

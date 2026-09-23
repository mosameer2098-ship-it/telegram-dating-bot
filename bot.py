
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "❤️ Welcome to LoveMatch!\n\n"
        "Your Telegram dating journey starts here.\n\n"
        "Use /profile to create your profile."
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("LoveMatch bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

from telegram.ext import Application, CommandHandler

from config import BOT_TOKEN
from handlers.start import start_command


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))

    print("LoveMatch bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

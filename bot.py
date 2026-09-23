from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import BOT_TOKEN
from database import init_db

from handlers.start import start_command
from handlers.matching import discover_command
from handlers.likes import handle_like, handle_pass

from handlers.profile import (
    profile_start,
    get_name,
    get_age,
    get_city,
    get_bio,
    get_photo,
    get_gender,
    get_interested_in,
    cancel_profile,
    NAME,
    AGE,
    CITY,
    BIO,
    PHOTO,
    GENDER,
    INTERESTED_IN,
)


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Start
    app.add_handler(
        CommandHandler("start", start_command)
    )

    # Discover
    app.add_handler(
        CommandHandler("discover", discover_command)
    )

    # Like / Pass buttons
    app.add_handler(
        CallbackQueryHandler(
            handle_like,
            pattern="^like$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_pass,
            pattern="^pass$",
        )
    )

    # Profile creation
    profile_handler = ConversationHandler(
        entry_points=[
            CommandHandler("profile", profile_start)
        ],
        states={
            NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_name,
                )
            ],
            AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_age,
                )
            ],
            CITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_city,
                )
            ],
            BIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_bio,
                )
            ],
            PHOTO: [
                MessageHandler(
                    filters.PHOTO,
                    get_photo,
                )
            ],
            GENDER: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_gender,
                )
            ],
            INTERESTED_IN: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    get_interested_in,
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                "cancel",
                cancel_profile,
            )
        ],
    )

    app.add_handler(profile_handler)

    print("LoveMatch bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

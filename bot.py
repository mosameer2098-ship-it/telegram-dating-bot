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
from handlers.reports import handle_report, handle_block
from handlers.chat import (
    start_chat,
    end_chat,
    forward_chat_message,
)

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

    # Basic commands
    app.add_handler(
        CommandHandler("start", start_command)
    )

    app.add_handler(
        CommandHandler("discover", discover_command)
    )

    # Chat commands
    app.add_handler(
        CommandHandler("endchat", end_chat)
    )

    # Like
    app.add_handler(
        CallbackQueryHandler(
            handle_like,
            pattern="^like$",
        )
    )

    # Pass
    app.add_handler(
        CallbackQueryHandler(
            handle_pass,
            pattern="^pass$",
        )
    )

    # Report
    app.add_handler(
        CallbackQueryHandler(
            handle_report,
            pattern="^report$",
        )
    )

    # Block
    app.add_handler(
        CallbackQueryHandler(
            handle_block,
            pattern="^block$",
        )
    )

    # Start chat
    app.add_handler(
        CallbackQueryHandler(
            start_chat,
            pattern="^start_chat$",
        )
    )

    # Profile creation
    profile_handler = ConversationHandler(
        entry_points=[
            CommandHandler(
                "profile",
                profile_start,
            )
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

    # Chat messages
    app.add_handler(
        MessageHandler(
            filters.ALL & ~filters.COMMAND,
            forward_chat_message,
        )
    )

    print("LoveMatch bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()

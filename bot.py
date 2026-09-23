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

from handlers.start import (
    start_command,
    language_command,
    language_callback,
    change_language,
    safety_info,
    welcome_back,
)
from handlers.matching import (
    discover_command,
    discover_callback,
)
from handlers.likes import handle_like, handle_pass
from handlers.reports import handle_report, handle_block
from handlers.chat import (
    start_chat,
    end_chat,
    forward_chat_message,
)
from handlers.settings import (
    settings_command,
    show_my_profile,
    delete_profile,
)

from handlers.premium import (
    premium_dashboard,
    premium_status,
    premium_plans,
)

from handlers.admin_premium import (
    premium_grant,
    premium_revoke,
    premium_status_command,
)

from handlers.admin_premium_settings import (
    premium_settings,
    premium_mode_change,
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
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("discover", discover_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("endchat", end_chat))

    # Welcome Dashboard
    app.add_handler(
        CallbackQueryHandler(
            safety_info,
            pattern=r"^safety_info$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            welcome_back,
            pattern=r"^welcome_back$",
        )
    )

    # Language selection
    app.add_handler(
        CallbackQueryHandler(
            language_callback,
            pattern=r"^lang_(en|hi|hinglish|bn)$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            change_language,
            pattern=r"^change_language$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            settings_command,
            pattern=r"^settings$",
        )
    )


    # Dashboard Discover button
    app.add_handler(
        CallbackQueryHandler(
            discover_callback,
            pattern=r"^dashboard_discover$",
        )
    )

    # Dating buttons
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

    app.add_handler(
        CallbackQueryHandler(
            handle_report,
            pattern="^report$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_block,
            pattern="^block$",
        )
    )

    # Match chat
    app.add_handler(
        CallbackQueryHandler(
            start_chat,
            pattern="^start_chat$",
        )
    )

    # Premium Dashboard
    app.add_handler(
        CallbackQueryHandler(
            premium_dashboard,
            pattern=r"^premium_dashboard$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            premium_status,
            pattern=r"^premium_status$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            premium_plans,
            pattern=r"^premium_plans$",
        )
    )
    app.add_handler(
        CallbackQueryHandler(
            welcome_back,
            pattern=r"^premium_back$",
        )
    )


    # Admin Premium Settings
    app.add_handler(
        CommandHandler(
            "premium_settings",
            premium_settings,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            premium_settings,
            pattern=r"^premium_settings$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            premium_mode_change,
            pattern=r"^premium_mode_(free|paid)$",
        )
    )

    # Settings
    app.add_handler(
        CallbackQueryHandler(
            show_my_profile,
            pattern="^my_profile$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            delete_profile,
            pattern="^delete_profile$",
        )
    )

    # Admin Premium Commands
    app.add_handler(CommandHandler("premium_grant", premium_grant))
    app.add_handler(CommandHandler("premium_revoke", premium_revoke))
    app.add_handler(CommandHandler("premium_status", premium_status_command))

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

from telegram.ext import (
    Application,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    CallbackQueryHandler,
    PreCheckoutQueryHandler,
    filters,
)

from config import BOT_TOKEN
import asyncio
from database import init_db
from services.pro_features import ensure_pro_tables

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
from handlers.who_liked import (
    who_liked_me,
    who_like_back,
    who_pass,
)

from handlers.verification import (
    verification_menu,
    verification_start,
    receive_verification_photo,
    verification_status,
    WAITING_VERIFICATION_PHOTO,
)

from handlers.profile_photos import (
    my_profile_photos,
    profile_photo_add,
    receive_profile_photo,
    profile_photo_view,
    profile_photo_manage,
    profile_photo_primary,
    profile_photo_delete,
    profile_photo_back,
    WAITING_PHOTO,
)

from handlers.favorites import (
    favorite_add,
    favorite_remove,
    favorite_current,
    my_favorites,
    favorite_next,
)
from handlers.advanced_actions import (
    handle_super_like,
    handle_rewind,
)
from handlers.reports import handle_report, handle_block
from handlers.matches import (
    view_match,
    unmatch,
    ai_icebreaker,
)
from handlers.chat import (
    start_chat,
    end_chat,
    forward_chat_message,
    chat_menu,
    chat_continue,
    chat_history,
    chat_unread,
    chat_end,
)
from handlers.notifications import (
    notifications_dashboard,
    notifications_mark_all_read,
)
from handlers.profile_edit import (
    edit_profile,
    edit_name_start,
    edit_age_start,
    edit_city_start,
    edit_bio_start,
    save_edit_name,
    save_edit_age,
    save_edit_city,
    save_edit_bio,
    ai_generate_bio,
    ai_save_bio,
    ai_cancel_bio,
    cancel_edit,
    EDIT_NAME,
    EDIT_AGE,
    EDIT_CITY,
    EDIT_BIO,
)

from handlers.settings import (
    settings_command,
    settings_callback,
    show_my_profile,
    delete_profile,
    incognito_toggle,
)

from handlers.filters import (
    advanced_filters,
    filter_age,
    filter_gender,
    filter_city,
    filter_distance,
    filter_age_select,
    filter_gender_select,
    filter_distance_select,
    filter_reset,
    filter_city_message,
)

from handlers.payments import (
    buy_premium_plan,
    precheckout_callback,
    successful_payment_callback,
)

from handlers.premium import (
    premium_dashboard,
    premium_status,
    premium_plans,
    redeem_promo_start,
    redeem_promo_code_message,
    redeem_promo_cancel,
    premium_features,
)

from handlers.admin_promo import (
    promo_create,
    promo_disable,
    promo_list,
)

from handlers.referral import (
    referral_command,
    referral_refresh,
    referral_back,
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

from handlers.pro_features import (
    pro_command, pro_dashboard, pro_recommendations, pro_trending, pro_compatibility,
    pro_achievements, pro_viewers, pro_notifications, notif_toggle,
    admin_dashboard, admin_broadcast_toggle, admin_ban, admin_unban,
    admin_reports, admin_users, admin_flag, translate_command,
)
from jobs.pro_jobs import hourly_ai_broadcast_loop

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


async def _post_init(application):
    ensure_pro_tables()
    application.bot_data["pro_broadcast_task"] = asyncio.create_task(hourly_ai_broadcast_loop(application.bot))


async def _post_shutdown(application):
    task = application.bot_data.get("pro_broadcast_task")
    if task:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def main():
    init_db()

    app = Application.builder().token(BOT_TOKEN).post_init(_post_init).post_shutdown(_post_shutdown).build()

    # Basic commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("language", language_command))
    app.add_handler(CommandHandler("discover", discover_command))
    app.add_handler(CommandHandler("settings", settings_command))
    app.add_handler(CommandHandler("referral", referral_command))
    app.add_handler(CommandHandler("pro", pro_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("admin", admin_dashboard))
    app.add_handler(CommandHandler("admin_broadcast_on", admin_broadcast_toggle))
    app.add_handler(CommandHandler("admin_broadcast_off", admin_broadcast_toggle))
    app.add_handler(CommandHandler("admin_ban", admin_ban))
    app.add_handler(CommandHandler("admin_unban", admin_unban))
    app.add_handler(CommandHandler("admin_reports", admin_reports))
    app.add_handler(CommandHandler("admin_users", admin_users))
    app.add_handler(CommandHandler("admin_flag", admin_flag))

    app.add_handler(
        CallbackQueryHandler(
            referral_refresh,
            pattern=r"^referral_refresh$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            referral_back,
            pattern=r"^referral_back$",
        )
    )
    app.add_handler(CommandHandler("endchat", end_chat))

    # Welcome Dashboard
    app.add_handler(
        CallbackQueryHandler(
            view_match,
            pattern=r"^view_match$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            unmatch,
            pattern=r"^unmatch$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            ai_icebreaker,
            pattern=r"^ai_icebreaker$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            notifications_dashboard,
            pattern=r"^notifications$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            notifications_mark_all_read,
            pattern=r"^notifications_mark_all$",
        )
    )

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

    # Stage 3 Pro
    app.add_handler(CallbackQueryHandler(pro_dashboard, pattern=r"^pro_dashboard$"))
    app.add_handler(CallbackQueryHandler(pro_recommendations, pattern=r"^pro_recommendations$"))
    app.add_handler(CallbackQueryHandler(pro_trending, pattern=r"^pro_trending$"))
    app.add_handler(CallbackQueryHandler(pro_compatibility, pattern=r"^pro_compatibility$"))
    app.add_handler(CallbackQueryHandler(pro_achievements, pattern=r"^pro_achievements$"))
    app.add_handler(CallbackQueryHandler(pro_viewers, pattern=r"^pro_viewers$"))
    app.add_handler(CallbackQueryHandler(pro_notifications, pattern=r"^pro_notifications$"))
    app.add_handler(CallbackQueryHandler(notif_toggle, pattern=r"^notif_toggle_(likes|matches|messages|profile_views|promotions)$"))

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
            settings_callback,
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

    # Advanced Filters
    app.add_handler(
        CallbackQueryHandler(
            advanced_filters,
            pattern=r"^advanced_filters$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_age,
            pattern=r"^filter_age$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_gender,
            pattern=r"^filter_gender$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_city,
            pattern=r"^filter_city$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_distance,
            pattern=r"^filter_distance$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_age_select,
            pattern=r"^filter_age_\d+_\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_gender_select,
            pattern=r"^filter_gender_(male|female|other|any)$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_distance_select,
            pattern=r"^filter_distance_\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            filter_reset,
            pattern=r"^filter_reset$",
        )
    )

    # Who Liked Me
    app.add_handler(
        CallbackQueryHandler(
            who_liked_me,
            pattern=r"^who_liked_me$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            who_like_back,
            pattern=r"^who_like_\\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            who_pass,
            pattern=r"^who_pass_\\d+$",
        )
    )

    # Favorites
    app.add_handler(
        CallbackQueryHandler(
            my_favorites,
            pattern=r"^my_favorites$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            favorite_add,
            pattern=r"^favorite_add_\\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            favorite_remove,
            pattern=r"^favorite_remove_\\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            favorite_next,
            pattern=r"^favorite_next$",
        )
    )

    # Current Profile Favorite
    app.add_handler(
        CallbackQueryHandler(
            favorite_current,
            pattern=r"^favorite_current$",
        )
    )

    # Profile Verification
    app.add_handler(
        CallbackQueryHandler(
            verification_menu,
            pattern=r"^verification$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            verification_status,
            pattern=r"^verification_status$",
        )
    )

    # Profile Photos
    app.add_handler(
        CallbackQueryHandler(
            my_profile_photos,
            pattern=r"^profile_photos$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile_photo_view,
            pattern=r"^profile_photo_view$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile_photo_manage,
            pattern=r"^profile_photo_manage_\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile_photo_primary,
            pattern=r"^profile_photo_primary_\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile_photo_delete,
            pattern=r"^profile_photo_delete_\d+$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            profile_photo_back,
            pattern=r"^profile_photo_back$",
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

    # Ultra Pro Dating Actions
    app.add_handler(
        CallbackQueryHandler(
            handle_super_like,
            pattern="^super_like$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            handle_rewind,
            pattern="^rewind$",
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

    # Advanced Filters - City Input
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            filter_city_message,
        ),
        group=1,
    )

    # Advanced Chat
    app.add_handler(
        CallbackQueryHandler(
            chat_menu,
            pattern=r"^chat_menu$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            chat_continue,
            pattern=r"^chat_continue$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            chat_history,
            pattern=r"^chat_history$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            chat_unread,
            pattern=r"^chat_unread$",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            chat_end,
            pattern=r"^chat_end$",
        )
    )

    # Match chat
    app.add_handler(
        CallbackQueryHandler(
            start_chat,
            pattern="^start_chat$",
        )
    )

    # Telegram Stars Premium Payments
    app.add_handler(
        CallbackQueryHandler(
            buy_premium_plan,
            pattern=r"^buy_premium_(7_days|30_days|90_days)$",
        )
    )

    app.add_handler(
        PreCheckoutQueryHandler(precheckout_callback)
    )

    app.add_handler(
        MessageHandler(
            filters.SUCCESSFUL_PAYMENT,
            successful_payment_callback,
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

    redeem_promo_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                redeem_promo_start,
                pattern=r"^redeem_promo$",
            )
        ],
        states={
            1: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    redeem_promo_code_message,
                )
            ],
        },
        fallbacks=[
            CommandHandler(
                "cancel",
                redeem_promo_cancel,
            )
        ],
        allow_reentry=True,
    )

    app.add_handler(redeem_promo_handler)

    app.add_handler(
        CallbackQueryHandler(
            premium_features,
            pattern=r"^premium_features$",
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

    # Profile Editing
    app.add_handler(
        CallbackQueryHandler(
            edit_profile,
            pattern=r"^edit_profile$",
        )
    )

    # Profile Verification photo conversation
    verification_photo_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                verification_start,
                pattern=r"^verification_start$",
            )
        ],
        states={
            WAITING_VERIFICATION_PHOTO: [
                MessageHandler(
                    filters.PHOTO,
                    receive_verification_photo,
                )
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(verification_photo_handler)

    # Multiple Profile Photos conversation
    profile_photo_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(
                profile_photo_add,
                pattern=r"^profile_photo_add$",
            )
        ],
        states={
            WAITING_PHOTO: [
                MessageHandler(
                    filters.PHOTO,
                    receive_profile_photo,
                )
            ],
        },
        fallbacks=[],
        allow_reentry=True,
    )

    app.add_handler(profile_photo_handler)

    # Incognito Mode
    app.add_handler(
        CallbackQueryHandler(
            incognito_toggle,
            pattern=r"^incognito$",
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
    app.add_handler(CommandHandler("promo_create", promo_create))
    app.add_handler(CommandHandler("promo_disable", promo_disable))
    app.add_handler(CommandHandler("promo_list", promo_list))

    # Profile editing conversation
    profile_edit_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(edit_name_start, pattern=r"^edit_name$"),
            CallbackQueryHandler(edit_age_start, pattern=r"^edit_age$"),
            CallbackQueryHandler(edit_city_start, pattern=r"^edit_city$"),
            CallbackQueryHandler(edit_bio_start, pattern=r"^edit_bio$"),
            CallbackQueryHandler(ai_generate_bio, pattern=r"^ai_generate_bio$"),
            CallbackQueryHandler(ai_save_bio, pattern=r"^ai_save_bio$"),
            CallbackQueryHandler(ai_cancel_bio, pattern=r"^ai_cancel_bio$"),
        ],
        states={
            EDIT_NAME: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_edit_name,
                )
            ],
            EDIT_AGE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_edit_age,
                )
            ],
            EDIT_CITY: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_edit_city,
                )
            ],
            EDIT_BIO: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    save_edit_bio,
                )
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_edit),
        ],
        allow_reentry=True,
    )

    app.add_handler(profile_edit_handler)

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

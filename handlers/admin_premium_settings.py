from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import ADMIN_ID
from database import get_connection


def is_admin(user_id):
    return user_id == ADMIN_ID


def get_premium_mode():
    connection = get_connection()

    row = connection.execute(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'premium_mode'
        """
    ).fetchone()

    connection.close()

    if not row:
        return "free"

    return row["value"]


def set_premium_mode(mode):
    if mode not in ("free", "paid"):
        return

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO app_settings (key, value)
        VALUES ('premium_mode', ?)
        ON CONFLICT(key)
        DO UPDATE SET value = excluded.value
        """,
        (mode,),
    )

    connection.commit()
    connection.close()


def settings_keyboard(mode):
    if mode == "free":
        return InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🔴 Turn ON Paid Mode",
                    callback_data="premium_mode_paid"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔄 Refresh",
                    callback_data="premium_settings"
                )
            ],
        ])

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🟢 Turn ON Free Mode",
                callback_data="premium_mode_free"
            )
        ],
        [
            InlineKeyboardButton(
                "🔄 Refresh",
                callback_data="premium_settings"
            )
        ],
    ])


def settings_text():
    mode = get_premium_mode()

    if mode == "free":
        status = "🟢 FREE MODE"
        description = (
            "Everyone can use Premium features for free.\n"
            "No payment is required."
        )
    else:
        status = "🔴 PAID MODE"
        description = (
            "Premium requires payment or an admin grant.\n"
            "Payment integration can be enabled later."
        )

    return (
        "💎 <b>Premium Settings</b>\n\n"
        f"Current Mode: <b>{status}</b>\n\n"
        f"{description}\n\n"
        "Choose an option below:"
    )


async def premium_settings(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_admin(user.id):
        if update.callback_query:
            await update.callback_query.answer(
                "❌ Admin only.",
                show_alert=True,
            )
        return

    query = update.callback_query

    if query:
        await query.answer()
        await query.edit_message_text(
            settings_text(),
            reply_markup=settings_keyboard(get_premium_mode()),
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            settings_text(),
            reply_markup=settings_keyboard(get_premium_mode()),
            parse_mode="HTML",
        )


async def premium_mode_change(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user = update.effective_user

    if not is_admin(user.id):
        await update.callback_query.answer(
            "❌ Admin only.",
            show_alert=True,
        )
        return

    query = update.callback_query
    await query.answer()

    mode = query.data.replace("premium_mode_", "")
    set_premium_mode(mode)

    await query.edit_message_text(
        settings_text(),
        reply_markup=settings_keyboard(mode),
        parse_mode="HTML",
    )

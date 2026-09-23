from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_connection
from services.premium import get_premium_mode, has_premium_access


def premium_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💎 Premium Plans",
                callback_data="premium_plans"
            )
        ],
        [
            InlineKeyboardButton(
                "👤 My Premium Status",
                callback_data="premium_status"
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="premium_back"
            )
        ],
    ])


def get_premium_status(telegram_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT is_premium, premium_until
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    connection.close()

    if not row:
        return False, None

    return bool(row["is_premium"]), row["premium_until"]


async def premium_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    mode = get_premium_mode()
    user_id = update.effective_user.id
    access = has_premium_access(user_id)

    if mode == "free":
        mode_text = (
            "🟢 <b>FREE MODE</b>\n"
            "Everyone currently has Premium access."
        )
        access_text = "✅ Your Premium access is active for free."
    else:
        mode_text = (
            "🔴 <b>PAID MODE</b>\n"
            "Premium access requires an active Premium plan."
        )
        access_text = (
            "✅ You have Premium access."
            if access
            else "🔒 You currently don't have Premium access."
        )

    await query.edit_message_text(
        "💎 <b>LoveMatch Premium Dashboard</b>\n\n"
        f"{mode_text}\n\n"
        f"{access_text}\n\n"
        "Choose an option below:",
        reply_markup=premium_keyboard(),
        parse_mode="HTML",
    )


async def premium_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    mode = get_premium_mode()
    is_premium, premium_until = get_premium_status(user.id)

    if mode == "free":
        status = (
            "🟢 <b>FREE MODE</b>\n\n"
            "💎 Premium access is currently free for everyone."
        )
    elif is_premium:
        status = (
            "💎 <b>Premium Active</b>\n\n"
            f"📅 Valid until: {premium_until or 'No expiry'}"
        )
    else:
        status = (
            "⚪ <b>Free Plan</b>\n\n"
            "Premium access is currently locked for your account."
        )

    await query.edit_message_text(
        status,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="premium_dashboard"
                )
            ]
        ]),
        parse_mode="HTML",
    )


async def premium_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    query = update.callback_query
    await query.answer()

    mode = get_premium_mode()

    if mode == "free":
        text = (
            "🟢 <b>Premium is currently FREE!</b>\n\n"
            "🎉 Enjoy all available Premium features without payment.\n\n"
            "The admin can switch Premium to Paid Mode whenever required."
        )
    else:
        text = (
            "💎 <b>Premium Plans</b>\n\n"
            "🌟 7 Days — Coming Soon\n"
            "🌟 30 Days — Coming Soon\n"
            "🌟 90 Days — Coming Soon\n\n"
            "Payment integration will be connected later."
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="premium_dashboard"
                )
            ]
        ]),
        parse_mode="HTML",
    )

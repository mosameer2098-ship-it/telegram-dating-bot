from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_connection
from services.premium import get_premium_mode, has_premium_access


def premium_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💖 Premium Plans",
                callback_data="premium_plans",
            )
        ],
        [
            InlineKeyboardButton(
                "👑 My Premium",
                callback_data="premium_status",
            )
        ],
        [
            InlineKeyboardButton(
                "✨ Premium Features",
                callback_data="premium_features",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to LoveMatch",
                callback_data="premium_back",
            )
        ],
    ])


def premium_back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "💖 Premium Dashboard",
                callback_data="premium_dashboard",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="premium_dashboard",
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


def premium_features_text():
    return (
        "✨ <b>LoveMatch Premium Features</b>\n\n"
        "❤️ <b>Unlimited Likes</b>\n"
        "💖 <b>Super Likes</b>\n"
        "👀 <b>Who Liked You</b>\n"
        "🔥 <b>Profile Boost</b>\n"
        "↩️ <b>Rewind</b>\n"
        "🎯 <b>Advanced Match Filters</b>\n"
        "🕶️ <b>Incognito Mode</b>\n"
        "👑 <b>Premium Badge</b>\n"
        "⚡ <b>Priority Discovery</b>\n\n"
        "💞 <i>Unlock your LoveMatch experience.</i>"
    )


async def premium_dashboard(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    mode = get_premium_mode()
    user_id = update.effective_user.id
    access = has_premium_access(user_id)

    if mode == "free":
        access_text = (
            "🟢 <b>FREE PREMIUM MODE</b>\n"
            "Everyone currently has Premium access."
        )
    elif access:
        access_text = (
            "👑 <b>PREMIUM ACTIVE</b>\n"
            "Your Premium experience is unlocked."
        )
    else:
        access_text = (
            "🔒 <b>PREMIUM LOCKED</b>\n"
            "Choose a Premium plan to unlock the features."
        )

    text = (
        "💖 <b>LoveMatch Premium</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "✨ <i>Unlock Your Love Experience</i>\n\n"
        f"{access_text}\n\n"
        "❤️ Unlimited Likes\n"
        "💖 Super Likes\n"
        "👀 See Who Liked You\n"
        "🔥 Profile Boost\n"
        "↩️ Rewind\n"
        "🎯 Advanced Filters\n\n"
        "Choose an option below:"
    )

    await query.edit_message_text(
        text,
        reply_markup=premium_keyboard(),
        parse_mode="HTML",
    )


async def premium_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    mode = get_premium_mode()
    is_premium, premium_until = get_premium_status(user.id)

    if mode == "free":
        status = (
            "💖 <b>LoveMatch Premium</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "🟢 <b>FREE MODE</b>\n\n"
            "👑 Your Premium access is currently free.\n\n"
            "Enjoy all available Premium features! ❤️"
        )
    elif is_premium:
        status = (
            "👑 <b>Premium Active</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            f"📅 Valid until: <b>{premium_until or 'No expiry'}</b>\n\n"
            "💖 Your LoveMatch Premium experience is active."
        )
    else:
        status = (
            "🤍 <b>Free Plan</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "🔒 Premium features are locked.\n\n"
            "Upgrade to unlock your LoveMatch experience. 💖"
        )

    await query.edit_message_text(
        status,
        reply_markup=premium_back_keyboard(),
        parse_mode="HTML",
    )


async def premium_features(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        premium_features_text(),
        reply_markup=premium_back_keyboard(),
        parse_mode="HTML",
    )


async def premium_plans(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    mode = get_premium_mode()

    if mode == "free":
        text = (
            "💖 <b>LoveMatch Premium</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "🟢 <b>Premium is currently FREE!</b>\n\n"
            "🎉 You can enjoy all currently available Premium "
            "features without payment.\n\n"
            "👑 The admin can switch to Paid Mode whenever required."
        )
    else:
        text = (
            "💎 <b>LoveMatch Premium Plans</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "🌟 <b>7 Days</b>\n"
            "🌟 <b>30 Days</b>\n"
            "🌟 <b>90 Days</b>\n\n"
            "💳 Payment integration will be connected in the "
            "Premium billing module."
        )

    await query.edit_message_text(
        text,
        reply_markup=premium_back_keyboard(),
        parse_mode="HTML",
    )

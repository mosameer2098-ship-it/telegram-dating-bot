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
                "🎟️ Redeem Promo Code",
                callback_data="redeem_promo",
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
        plans = [
            ("7_days", "🌟 7 Days Premium", 200),
            ("30_days", "🌟 30 Days Premium", 400),
            ("90_days", "🌟 90 Days Premium", 1500),
        ]

        buttons = [
            [
                InlineKeyboardButton(
                    f"{name} — {stars} ⭐",
                    callback_data=f"buy_premium_{plan_id}",
                )
            ]
            for plan_id, name, stars in plans
        ]

        buttons.append([
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="premium_dashboard",
            )
        ])

        keyboard = InlineKeyboardMarkup(buttons)

        text = (
            "💎 <b>LoveMatch Premium Plans</b>\n"
            "━━━━━━━━━━━━━━\n\n"
            "Choose your Premium duration:\n\n"
            "🌟 <b>7 Days</b> — 200 ⭐\n"
            "🌟 <b>30 Days</b> — 400 ⭐\n"
            "🌟 <b>90 Days</b> — 1500 ⭐\n\n"
            "💳 Pay securely using Telegram Stars."
        )

    await query.edit_message_text(
        text,
        reply_markup=keyboard if mode != "free" else premium_back_keyboard(),
        parse_mode="HTML",
    )


async def redeem_promo_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "🎟️ <b>Redeem Promo Code</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "Enter your promo code below.\n\n"
        "Example: <code>LOVE7</code>\n\n"
        "Send /cancel to go back.",
        parse_mode="HTML",
    )

    return 1


async def redeem_promo_code_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    from services.promo_codes import (
        get_promo_code,
        is_promo_valid,
        redeem_promo_code,
        apply_promo_premium,
    )

    user_id = update.effective_user.id
    code = (update.message.text or "").strip().upper()

    promo = get_promo_code(code)

    if not promo:
        await update.message.reply_text(
            "❌ <b>Invalid Promo Code</b>\n\n"
            "This promo code was not found.\n"
            "Please check the code and try again.",
            parse_mode="HTML",
        )
        return 1

    valid, message = is_promo_valid(code)

    if not valid:
        await update.message.reply_text(
            f"❌ <b>Promo Code Unavailable</b>\n\n"
            f"{message}",
            parse_mode="HTML",
        )
        return 1

    result = redeem_promo_code(user_id, code)

    if not result["success"]:
        await update.message.reply_text(
            f"❌ <b>Promo Code Failed</b>\n\n"
            f"{result['message']}",
            parse_mode="HTML",
        )
        return 1

    reward_days = int(result["reward_value"])

    activation = apply_promo_premium(
        user_id,
        reward_days,
    )

    if not activation["success"]:
        await update.message.reply_text(
            "⚠️ Promo code was redeemed, but Premium "
            "activation could not be completed.\n\n"
            "Please contact support.",
            parse_mode="HTML",
        )
        return -1

    await update.message.reply_text(
        "🎉 <b>Promo Code Redeemed!</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"🎟️ Code: <code>{code}</code>\n"
        f"👑 Premium Added: <b>{reward_days} days</b>\n\n"
        f"📅 Premium Until:\n"
        f"<b>{activation['premium_until']}</b>\n\n"
        "💖 Enjoy your LoveMatch Premium experience!",
        parse_mode="HTML",
    )

    return -1


async def redeem_promo_cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "❌ Promo code redemption cancelled."
    )
    return -1

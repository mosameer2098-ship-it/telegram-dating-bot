from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.referrals.service import (
    get_referral_link,
    get_referral_stats,
)


async def referral_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user = update.effective_user

    bot = await context.bot.get_me()

    referral_link = get_referral_link(
        bot.username,
        user.id,
    )

    stats = get_referral_stats(user.id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Refresh Referral Stats",
                callback_data="referral_refresh",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to LoveMatch",
                callback_data="referral_back",
            )
        ],
    ])

    text = (
        "💞 <b>LoveMatch Referral</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        "👥 <b>Invite your friends to LoveMatch!</b>\n\n"
        "🔗 <b>Your Referral Link:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"👥 Total Referrals: <b>{stats['total_referrals']}</b>\n"
        f"🎁 Rewards Claimed: <b>{stats['rewards_claimed']}</b>\n"
        f"⏳ Pending Rewards: <b>{stats['pending_rewards']}</b>\n\n"
        "💖 Share your link and invite new users!"
    )

    await update.message.reply_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def referral_refresh(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user = update.effective_user
    bot = await context.bot.get_me()

    referral_link = get_referral_link(
        bot.username,
        user.id,
    )

    stats = get_referral_stats(user.id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Refresh Referral Stats",
                callback_data="referral_refresh",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back to LoveMatch",
                callback_data="referral_back",
            )
        ],
    ])

    text = (
        "💞 <b>LoveMatch Referral</b>\n"
        "━━━━━━━━━━━━━━\n\n"
        f"🔗 <b>Your Referral Link:</b>\n"
        f"<code>{referral_link}</code>\n\n"
        f"👥 Total Referrals: <b>{stats['total_referrals']}</b>\n"
        f"🎁 Rewards Claimed: <b>{stats['rewards_claimed']}</b>\n"
        f"⏳ Pending Rewards: <b>{stats['pending_rewards']}</b>\n\n"
        "💖 Keep sharing your referral link!"
    )

    await query.edit_message_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def referral_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "💖 <b>LoveMatch</b>\n\n"
        "Welcome back! ❤️",
        parse_mode="HTML",
    )

from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import discover_keyboard
from services.matching import get_profile
from services.recommendations.engine import get_best_match
from services.analytics.service import record_profile_view


def build_profile_text(result):
    profile = result["profile"]

    name = profile["name"]
    age = profile["age"]
    city = profile["city"]
    bio = profile["bio"] or "No bio available."
    score = result["score"]
    reason = result["reason"]

    return (
        f"👤 <b>{name}, {age}</b>\n"
        f"📍 {city}\n\n"
        f"📝 {bio}\n\n"
        f"💖 Compatibility: <b>{score}%</b>\n"
        f"{reason}\n\n"
        "What do you think?"
    )


async def _send_discovery(update, context):
    user_id = update.effective_user.id

    profile = get_profile(user_id)

    if not profile:
        message = (
            "❤️ First create your profile with /profile"
        )

        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)

        return

    result = get_best_match(user_id)

    if not result:
        message = (
            "😔 No new compatible profiles found right now.\n\n"
            "Try again later or update your preferences."
        )

        if update.callback_query:
            await update.callback_query.message.reply_text(message)
        else:
            await update.message.reply_text(message)

        return

    candidate = result["profile"]

    # Record profile view for analytics.
    record_profile_view(
        user_id,
        candidate["telegram_id"],
    )

    context.user_data["current_profile"] = candidate["telegram_id"]

    text = build_profile_text(result)
    photo_file_id = candidate["photo_file_id"]

    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    if photo_file_id:
        await message.reply_photo(
            photo=photo_file_id,
            caption=text,
            parse_mode="HTML",
            reply_markup=discover_keyboard(),
        )
    else:
        await message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=discover_keyboard(),
        )


async def discover_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await _send_discovery(update, context)


async def discover_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await _send_discovery(update, context)

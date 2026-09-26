from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import discover_keyboard, match_keyboard
from services.matching import get_profile
from services.recommendations.actions import (
    super_like_user,
    rewind_user,
)


async def handle_super_like(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile")

    if not target_id:
        await query.message.reply_text(
            "😕 This profile is no longer available."
        )
        return

    result = super_like_user(
        user_id=user_id,
        target_id=target_id,
    )

    context.user_data["previous_profile"] = target_id
    context.user_data.pop("current_profile", None)

    if result["matched"]:
        profile = get_profile(target_id)
        name = profile["name"] if profile else "your match"

        await query.message.reply_text(
            f"💞 <b>IT'S A MATCH!</b>\n\n"
            f"You and {name} liked each other! ❤️",
            reply_markup=match_keyboard(),
            parse_mode="HTML",
        )
        return

    await query.message.reply_text(
        "💖 <b>Super Like sent!</b>\n\n"
        "They'll know you really liked their profile. ❤️",
        parse_mode="HTML",
    )


async def handle_rewind(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    previous_id = context.user_data.get("previous_profile")

    if not previous_id:
        await query.message.reply_text(
            "↩️ No previous profile is available yet."
        )
        return

    rewind_user(
        user_id=user_id,
        target_id=previous_id,
    )

    # Consume the rewind target after restoring it.
    context.user_data.pop("previous_profile", None)

    profile = get_profile(previous_id)

    if not profile:
        await query.message.reply_text(
            "😕 That profile is no longer available."
        )
        return

    context.user_data["current_profile"] = previous_id

    name = profile["name"]
    age = profile["age"]
    city = profile["city"]
    bio = profile["bio"] or "No bio available."
    photo = profile["photo_file_id"]

    text = (
        f"👤 <b>{name}, {age}</b>\n"
        f"📍 {city}\n\n"
        f"📝 {bio}\n\n"
        "↩️ <b>Previous profile restored.</b>"
    )

    if photo:
        await query.message.reply_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=discover_keyboard(),
        )
    else:
        await query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=discover_keyboard(),
        )

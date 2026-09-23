from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import discover_keyboard
from services.matching import get_profile, get_discover_profile


async def discover_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    user_id = update.effective_user.id

    profile = get_profile(user_id)

    if not profile:
        await update.message.reply_text(
            "❤️ First create your profile with /profile"
        )
        return

    # Find a compatible profile
    interested_in = profile["interested_in"]

    target_gender = None

    if interested_in == "men":
        target_gender = "male"
    elif interested_in == "women":
        target_gender = "female"

    candidate = get_discover_profile(
        telegram_id=user_id,
        gender=target_gender,
    )

    if not candidate:
        await update.message.reply_text(
            "😔 No profiles found right now.\n\n"
            "Try again later."
        )
        return

    context.user_data["current_profile"] = candidate["telegram_id"]

    name = candidate["name"]
    age = candidate["age"]
    city = candidate["city"]
    bio = candidate["bio"] or "No bio available."

    text = (
        f"👤 {name}, {age}\n"
        f"📍 {city}\n\n"
        f"📝 {bio}\n\n"
        "What do you think?"
    )

    photo_file_id = candidate["photo_file_id"]

    if photo_file_id:
        await update.message.reply_photo(
            photo=photo_file_id,
            caption=text,
            reply_markup=discover_keyboard(),
        )
    else:
        await update.message.reply_text(
            text,
            reply_markup=discover_keyboard(),
        )

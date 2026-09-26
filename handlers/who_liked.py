from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.likes import get_who_liked_me, get_who_liked_me_count


def who_liked_keyboard(user_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "❤️ Like Back",
                    callback_data=f"who_like_{user_id}",
                ),
                InlineKeyboardButton(
                    "❌ Pass",
                    callback_data=f"who_pass_{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="welcome_back",
                )
            ],
        ]
    )


def build_liker_text(profile):
    name = profile.get("name") or "Someone"
    age = profile.get("age") or "?"
    city = profile.get("city") or "Unknown"
    bio = profile.get("bio") or "No bio available."

    return (
        f"❤️ <b>{name}, {age}</b>\n"
        f"📍 {city}\n\n"
        f"📝 {bio}\n\n"
        "This person liked your profile. ❤️"
    )


async def who_liked_me(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    profiles = get_who_liked_me(user_id, limit=20)

    if not profiles:
        await query.edit_message_text(
            "❤️ <b>Who Liked Me</b>\n\n"
            "No new likes right now.\n\n"
            "Keep discovering and your new likes will appear here. ✨",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔎 Discover",
                            callback_data="dashboard_discover",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="welcome_back",
                        )
                    ],
                ]
            ),
        )
        return

    context.user_data["who_liked_list"] = profiles
    context.user_data["who_liked_index"] = 0

    await _show_liker(update, context)


async def _show_liker(update, context):
    profiles = context.user_data.get("who_liked_list", [])
    index = context.user_data.get("who_liked_index", 0)

    if index >= len(profiles):
        await _finish_who_liked(update, context)
        return

    profile = profiles[index]
    text = (
        f"❤️ <b>Who Liked Me</b>\n"
        f"💌 {index + 1}/{len(profiles)}\n\n"
        f"{build_liker_text(profile)}"
    )

    keyboard = who_liked_keyboard(profile["telegram_id"])

    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    photo = profile.get("photo_file_id")

    if photo:
        await message.reply_photo(
            photo=photo,
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


async def _finish_who_liked(update, context):
    context.user_data.pop("who_liked_list", None)
    context.user_data.pop("who_liked_index", None)

    if update.callback_query:
        await update.callback_query.message.reply_text(
            "❤️ <b>Who Liked Me</b>\n\n"
            "You've checked all your new likes.",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "🔎 Discover",
                            callback_data="dashboard_discover",
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "⬅️ Back",
                            callback_data="welcome_back",
                        )
                    ],
                ]
            ),
        )


async def who_like_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    liker_id = int(query.data.replace("who_like_", ""))
    context.user_data["current_profile"] = liker_id

    # Reuse the existing Like/Match system.
    from handlers.likes import handle_like

    await handle_like(update, context)

    context.user_data["who_liked_index"] = (
        context.user_data.get("who_liked_index", 0) + 1
    )

    await _show_liker(update, context)


async def who_pass(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    passer_id = int(query.data.replace("who_pass_", ""))

    from services.recommendations.actions import pass_user

    pass_user(
        user_id=update.effective_user.id,
        target_id=passer_id,
    )

    context.user_data["who_liked_index"] = (
        context.user_data.get("who_liked_index", 0) + 1
    )

    await _show_liker(update, context)

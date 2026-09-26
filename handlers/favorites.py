from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from services.favorites import (
    add_favorite,
    remove_favorite,
    is_favorite,
    get_favorites,
)


def favorite_action_keyboard(user_id, favorite=False):
    if favorite:
        action = InlineKeyboardButton(
            "🗑️ Remove Favorite",
            callback_data=f"favorite_remove_{user_id}",
        )
    else:
        action = InlineKeyboardButton(
            "⭐ Add Favorite",
            callback_data=f"favorite_add_{user_id}",
        )

    return InlineKeyboardMarkup(
        [
            [action],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="dashboard_discover",
                )
            ],
        ]
    )


def favorites_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "⭐ My Favorites",
                    callback_data="my_favorites",
                )
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="welcome_back",
                )
            ],
        ]
    )


def build_favorite_text(profile):
    name = profile.get("name") or "Unknown"
    age = profile.get("age") or "?"
    city = profile.get("city") or "Unknown"
    bio = profile.get("bio") or "No bio available."

    return (
        f"⭐ <b>{name}, {age}</b>\n"
        f"📍 {city}\n\n"
        f"📝 {bio}"
    )


async def favorite_add(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    favorite_id = int(query.data.replace("favorite_add_", ""))

    if add_favorite(user_id, favorite_id):
        await query.answer("⭐ Added to favorites!", show_alert=True)
    else:
        await query.answer(
            "⭐ Already in favorites or invalid profile.",
            show_alert=True,
        )


async def favorite_remove(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    favorite_id = int(query.data.replace("favorite_remove_", ""))

    if remove_favorite(user_id, favorite_id):
        await query.answer("🗑️ Removed from favorites.", show_alert=True)
    else:
        await query.answer(
            "This profile is not in your favorites.",
            show_alert=True,
        )


async def my_favorites(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    profiles = get_favorites(user_id, limit=20)

    if not profiles:
        await query.edit_message_text(
            "⭐ <b>My Favorites</b>\n\n"
            "You haven't added anyone to favorites yet.",
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

    context.user_data["favorites_list"] = profiles
    context.user_data["favorites_index"] = 0

    await _show_favorite(update, context)


async def _show_favorite(update, context):
    profiles = context.user_data.get("favorites_list", [])
    index = context.user_data.get("favorites_index", 0)

    if index >= len(profiles):
        context.user_data.pop("favorites_list", None)
        context.user_data.pop("favorites_index", None)

        await update.callback_query.message.reply_text(
            "⭐ <b>Favorites</b>\n\n"
            "You've viewed all saved profiles.",
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

    profile = profiles[index]
    user_id = profile["telegram_id"]

    text = (
        f"⭐ <b>Favorite {index + 1}/{len(profiles)}</b>\n\n"
        f"{build_favorite_text(profile)}"
    )

    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "🗑️ Remove",
                    callback_data=f"favorite_remove_{user_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    "➡️ Next",
                    callback_data="favorite_next",
                ),
            ],
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="welcome_back",
                ),
            ],
        ]
    )

    if profile.get("photo_file_id"):
        await update.callback_query.message.reply_photo(
            photo=profile["photo_file_id"],
            caption=text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )
    else:
        await update.callback_query.message.reply_text(
            text,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


async def favorite_next(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    context.user_data["favorites_index"] = (
        context.user_data.get("favorites_index", 0) + 1
    )

    await _show_favorite(update, context)

async def favorite_current(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    target_id = context.user_data.get("current_profile")

    if not target_id:
        await query.answer(
            "😕 No active profile found.",
            show_alert=True,
        )
        return

    if add_favorite(user_id, target_id):
        await query.answer(
            "⭐ Added to favorites!",
            show_alert=True,
        )
    else:
        await query.answer(
            "⭐ This profile is already in your favorites.",
            show_alert=True,
        )


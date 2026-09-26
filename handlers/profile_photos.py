from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters

from services.profile_photos import (
    MAX_PROFILE_PHOTOS,
    get_profile_photos,
    get_profile_photo_count,
    add_profile_photo,
    set_primary_photo,
    delete_profile_photo,
)

WAITING_PHOTO = 1


def profile_photos_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📸 Add Photo",
                callback_data="profile_photo_add",
            )
        ],
        [
            InlineKeyboardButton(
                "🖼️ View Photos",
                callback_data="profile_photo_view",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="profile_photo_back",
            )
        ],
    ])


def photo_manage_keyboard(photo_id, is_primary=False):
    buttons = []

    if not is_primary:
        buttons.append([
            InlineKeyboardButton(
                "⭐ Set Primary",
                callback_data=f"profile_photo_primary_{photo_id}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "🗑️ Delete",
            callback_data=f"profile_photo_delete_{photo_id}",
        )
    ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ Back",
            callback_data="profile_photo_view",
        )
    ])

    return InlineKeyboardMarkup(buttons)


async def my_profile_photos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query:
        await query.answer()
        await query.edit_message_text(
            "📸 <b>My Profile Photos</b>\n\n"
            "You can add up to 6 profile photos.",
            reply_markup=profile_photos_keyboard(),
            parse_mode="HTML",
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "📸 <b>My Profile Photos</b>\n\n"
        "You can add up to 6 profile photos.",
        reply_markup=profile_photos_keyboard(),
        parse_mode="HTML",
    )


async def profile_photo_add(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    count = get_profile_photo_count(user_id)

    if count >= MAX_PROFILE_PHOTOS:
        await query.edit_message_text(
            f"📸 You already have {MAX_PROFILE_PHOTOS} photos.\n\n"
            "Delete a photo before adding a new one.",
            reply_markup=profile_photos_keyboard(),
        )
        return ConversationHandler.END

    await query.edit_message_text(
        f"📸 <b>Add Profile Photo</b>\n\n"
        f"Photos: {count}/{MAX_PROFILE_PHOTOS}\n\n"
        "Send me a photo from your Telegram camera or gallery.",
        parse_mode="HTML",
    )

    return WAITING_PHOTO


async def receive_profile_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.photo:
        await update.message.reply_text(
            "📸 Please send a photo."
        )
        return WAITING_PHOTO

    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    photo_id = add_profile_photo(
        user_id,
        photo.file_id,
    )

    if photo_id is None:
        await update.message.reply_text(
            "❌ You have reached the maximum of "
            f"{MAX_PROFILE_PHOTOS} profile photos."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Profile photo added successfully!\n\n"
        "⭐ The first photo is automatically your primary photo.",
        reply_markup=profile_photos_keyboard(),
    )

    return ConversationHandler.END


async def profile_photo_view(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    photos = get_profile_photos(user_id)

    if not photos:
        await query.edit_message_text(
            "🖼️ You don't have any profile photos yet.",
            reply_markup=profile_photos_keyboard(),
        )
        return

    await query.edit_message_text(
        f"🖼️ <b>Your Profile Photos</b>\n\n"
        f"Total photos: {len(photos)}/{MAX_PROFILE_PHOTOS}\n\n"
        "Choose a photo below to manage it.",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    f"{'⭐ ' if row[3] else ''}Photo {index + 1}",
                    callback_data=f"profile_photo_manage_{row[0]}",
                )
            ]
            for index, row in enumerate(photos)
        ] + [
            [
                InlineKeyboardButton(
                    "⬅️ Back",
                    callback_data="profile_photo_back",
                )
            ]
        ]),
    )


async def profile_photo_manage(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    photo_id = int(query.data.rsplit("_", 1)[1])
    user_id = update.effective_user.id

    photos = get_profile_photos(user_id)
    photo = next((row for row in photos if row[0] == photo_id), None)

    if not photo:
        await query.edit_message_text(
            "❌ Photo not found.",
            reply_markup=profile_photos_keyboard(),
        )
        return

    await query.message.reply_photo(
        photo=photo[2],
        caption=(
            f"{'⭐ Primary Photo' if photo[3] else '🖼️ Profile Photo'}"
        ),
        reply_markup=photo_manage_keyboard(
            photo_id,
            bool(photo[3]),
        ),
    )


async def profile_photo_primary(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    photo_id = int(query.data.rsplit("_", 1)[1])
    user_id = update.effective_user.id

    if set_primary_photo(user_id, photo_id):
        await query.answer("⭐ Primary photo updated!", show_alert=True)
    else:
        await query.answer("❌ Photo not found.", show_alert=True)


async def profile_photo_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    photo_id = int(query.data.rsplit("_", 1)[1])
    user_id = update.effective_user.id

    if delete_profile_photo(user_id, photo_id):
        await query.answer("🗑️ Photo deleted.", show_alert=True)
    else:
        await query.answer("❌ Photo not found.", show_alert=True)

    await profile_photo_view(update, context)


async def profile_photo_back(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📸 <b>My Profile Photos</b>\n\n"
        "You can add up to 6 profile photos.",
        reply_markup=profile_photos_keyboard(),
        parse_mode="HTML",
    )

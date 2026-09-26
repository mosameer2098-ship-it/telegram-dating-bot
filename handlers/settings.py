from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from database import get_connection


def settings_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "👤 My Profile",
                    callback_data="my_profile",
                )
            ],
            [
                InlineKeyboardButton(
                    "🕵️ Incognito Mode",
                    callback_data="incognito",
                )
            ],
            [
                InlineKeyboardButton(
                    "🗑️ Delete Profile",
                    callback_data="delete_profile",
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


async def settings_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "⚙️ LoveMatch Settings",
        reply_markup=settings_keyboard(),
    )


async def show_my_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    connection = get_connection()

    profile = connection.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    if not profile:
        await query.edit_message_text(
            "👤 You don't have a profile yet.\n\n"
            "Use /profile to create one."
        )
        return

    text = (
        f"👤 {profile['name']}, {profile['age']}\n"
        f"📍 {profile['city']}\n"
        f"⚧ {profile['gender'] or 'Not set'}\n\n"
        f"❤️ Interested in: "
        f"{profile['interested_in'] or 'Not set'}\n\n"
        f"📝 {profile['bio'] or 'No bio'}"
    )

    if profile["photo_file_id"]:
        await query.message.reply_photo(
            photo=profile["photo_file_id"],
            caption=text,
        )

        await query.edit_message_text(
            "👤 Your profile is shown above."
        )
    else:
        await query.edit_message_text(text)


async def delete_profile(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    connection = get_connection()

    connection.execute(
        "DELETE FROM users WHERE telegram_id = ?",
        (user_id,),
    )

    connection.execute(
        """
        DELETE FROM likes
        WHERE liker_id = ?
           OR liked_id = ?
        """,
        (user_id, user_id),
    )

    connection.execute(
        """
        DELETE FROM matches
        WHERE user1_id = ?
           OR user2_id = ?
        """,
        (user_id, user_id),
    )

    connection.commit()
    connection.close()

    context.user_data.clear()

    await query.edit_message_text(
        "🗑️ Your LoveMatch profile has been deleted.\n\n"
        "You can create a new profile anytime with /profile."
    )


async def settings_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "⚙️ <b>LoveMatch Settings</b>",
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )


async def incognito_toggle(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    from services.incognito import is_incognito, set_incognito

    user_id = update.effective_user.id
    current = is_incognito(user_id)
    new_state = not current

    set_incognito(user_id, new_state)

    if new_state:
        text = (
            "🕵️ <b>Incognito Mode: ON</b>\n\n"
            "Your profile will no longer appear in normal discovery.\n"
            "You can turn Incognito Mode off anytime."
        )
    else:
        text = (
            "👀 <b>Incognito Mode: OFF</b>\n\n"
            "Your profile can now appear in normal discovery."
        )

    await query.edit_message_text(
        text,
        reply_markup=settings_keyboard(),
        parse_mode="HTML",
    )

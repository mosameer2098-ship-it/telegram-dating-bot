from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


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
                    "🗑️ Delete Profile",
                    callback_data="delete_profile",
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

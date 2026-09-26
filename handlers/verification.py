from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ConversationHandler, ContextTypes

from services.verification import (
    is_verified,
    get_verification,
    submit_verification,
)

WAITING_VERIFICATION_PHOTO = 1


def verification_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📸 Verify My Profile",
                callback_data="verification_start",
            )
        ],
        [
            InlineKeyboardButton(
                "⬅️ Back",
                callback_data="verification_back",
            )
        ],
    ])


async def verification_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query:
        await query.answer()

    user_id = update.effective_user.id

    if is_verified(user_id):
        await update.effective_message.reply_text(
            "✅ <b>Your profile is verified!</b>\n\n"
            "You have a verified badge on your profile.",
            parse_mode="HTML",
            reply_markup=verification_keyboard(),
        )
        return ConversationHandler.END

    await update.effective_message.reply_text(
        "🛡️ <b>Profile Verification</b>\n\n"
        "Verify your profile to receive a ✅ Verified badge.\n\n"
        "Send a clear photo when asked.",
        parse_mode="HTML",
        reply_markup=verification_keyboard(),
    )

    return ConversationHandler.END


async def verification_start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    if is_verified(user_id):
        await query.edit_message_text(
            "✅ Your profile is already verified."
        )
        return ConversationHandler.END

    await query.edit_message_text(
        "📸 <b>Verification Photo</b>\n\n"
        "Please send a clear photo of yourself.\n\n"
        "Your verification will be processed automatically.",
        parse_mode="HTML",
    )

    return WAITING_VERIFICATION_PHOTO


async def receive_verification_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message or not update.message.photo:
        await update.message.reply_text(
            "📸 Please send a photo for verification."
        )
        return WAITING_VERIFICATION_PHOTO

    user_id = update.effective_user.id
    photo = update.message.photo[-1]

    verification_id = submit_verification(
        user_id,
        photo.file_id,
    )

    if not verification_id:
        await update.message.reply_text(
            "❌ Verification could not be completed. Please try again."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "🎉 <b>Profile Verified!</b> ✅\n\n"
        "Your profile has been automatically verified.\n"
        "Your verified badge is now active.",
        parse_mode="HTML",
    )

    return ConversationHandler.END


async def verification_status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if query:
        await query.answer()

    user_id = update.effective_user.id
    verification = get_verification(user_id)

    if verification and verification[3] == "verified":
        text = (
            "✅ <b>Verified Profile</b>\n\n"
            "Your profile is verified."
        )
    else:
        text = (
            "🛡️ <b>Profile Not Verified</b>\n\n"
            "Verify your profile to receive the badge."
        )

    await update.effective_message.reply_text(
        text,
        parse_mode="HTML",
        reply_markup=verification_keyboard(),
    )

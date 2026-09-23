from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import discover_keyboard, match_keyboard
from services.matching import add_like, get_profile


async def handle_like(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    liked_id = context.user_data.get("current_profile")

    if not liked_id:
        await query.edit_message_text(
            "😕 This profile is no longer available."
        )
        return

    user_id = update.effective_user.id

    is_match = add_like(
        liker_id=user_id,
        liked_id=liked_id,
    )

    if is_match:
        liked_profile = get_profile(liked_id)

        if liked_profile:
            name = liked_profile["name"]

            await query.edit_message_text(
                f"💞 IT'S A MATCH!\n\n"
                f"You and {name} liked each other! ❤️"
            )

            await query.message.reply_text(
                "💬 You can now start a conversation."
                ,
                reply_markup=match_keyboard(),
            )
        else:
            await query.edit_message_text(
                "💞 It's a match!"
            )

    else:
        await query.edit_message_text(
            "❤️ Like sent!\n\n"
            "Finding another profile..."
        )


async def handle_pass(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    context.user_data.pop(
        "current_profile",
        None,
    )

    await query.edit_message_text(
        "❌ Passed.\n\n"
        "Use /discover to see another profile."
    )

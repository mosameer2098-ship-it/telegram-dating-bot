from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import match_keyboard
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

    if not is_match:
        await query.edit_message_text(
            "❤️ Like sent!\n\n"
            "Use /discover to find another profile."
        )
        return

    liked_profile = get_profile(liked_id)

    if not liked_profile:
        await query.edit_message_text(
            "💞 It's a match!"
        )
        return

    name = liked_profile["name"]

    await query.edit_message_text(
        f"💞 IT'S A MATCH!\n\n"
        f"You and {name} liked each other! ❤️",
        reply_markup=match_keyboard(),
    )

    # Notify the other matched user
    try:
        await context.bot.send_message(
            chat_id=liked_id,
            text=(
                "💞 IT'S A MATCH!\n\n"
                f"You and {update.effective_user.first_name} "
                "liked each other! ❤️\n\n"
                "You can now start a conversation."
            ),
            reply_markup=match_keyboard(),
        )
    except Exception:
        pass

    context.user_data.pop(
        "current_profile",
        None,
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

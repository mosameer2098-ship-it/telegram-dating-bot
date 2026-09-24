from telegram import Update
from telegram.ext import ContextTypes

from keyboards.matching import match_keyboard
from services.matching import get_profile
from services.recommendations.actions import (
    like_user,
    pass_user,
)


async def _show_result(query, text, reply_markup=None):
    """Safely show a result for text or photo messages."""
    try:
        if query.message and query.message.text is not None:
            await query.edit_message_text(
                text,
                reply_markup=reply_markup,
            )
        else:
            await query.message.reply_text(
                text,
                reply_markup=reply_markup,
            )
    except Exception:
        await query.message.reply_text(
            text,
            reply_markup=reply_markup,
        )


async def handle_like(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    liked_id = context.user_data.get("current_profile")

    if not liked_id:
        await _show_result(
            query,
            "😕 This profile is no longer available.",
        )
        return

    user_id = update.effective_user.id

    result = like_user(
        user_id=user_id,
        target_id=liked_id,
    )

    context.user_data["previous_profile"] = liked_id
    context.user_data.pop("current_profile", None)

    if not result["matched"]:
        await _show_result(
            query,
            "❤️ Like sent!\n\n"
            "Finding another match for you...",
        )
        return

    liked_profile = get_profile(liked_id)

    if not liked_profile:
        await _show_result(
            query,
            "💞 It's a match!",
            reply_markup=match_keyboard(),
        )
        return

    name = liked_profile["name"]

    await _show_result(
        query,
        f"💞 <b>IT'S A MATCH!</b>\n\n"
        f"You and {name} liked each other! ❤️",
        reply_markup=match_keyboard(),
    )

    try:
        await context.bot.send_message(
            chat_id=liked_id,
            text=(
                "💞 <b>IT'S A MATCH!</b>\n\n"
                f"You and {update.effective_user.first_name} "
                "liked each other! ❤️\n\n"
                "You can now start a conversation."
            ),
            reply_markup=match_keyboard(),
            parse_mode="HTML",
        )
    except Exception:
        pass


async def handle_pass(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    target_id = context.user_data.get("current_profile")

    if target_id:
        pass_user(
            user_id=update.effective_user.id,
            target_id=target_id,
        )

        context.user_data["previous_profile"] = target_id

    context.user_data.pop("current_profile", None)

    await _show_result(
        query,
        "❌ Passed.\n\n"
        "Finding another profile for you...",
    )

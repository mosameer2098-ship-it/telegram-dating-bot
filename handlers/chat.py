from telegram import Update
from telegram.ext import ContextTypes

from database import get_connection


def get_match_partner(user_id):
    connection = get_connection()

    match = connection.execute(
        """
        SELECT user1_id, user2_id
        FROM matches
        WHERE user1_id = ?
           OR user2_id = ?
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (user_id, user_id),
    ).fetchone()

    connection.close()

    if not match:
        return None

    if match["user1_id"] == user_id:
        return match["user2_id"]

    return match["user1_id"]


async def start_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id

    partner_id = get_match_partner(user_id)

    if not partner_id:
        await query.edit_message_text(
            "💬 You don't have an active match yet."
        )
        return

    context.user_data["chat_partner"] = partner_id

    await query.edit_message_text(
        "💬 Chat mode enabled!\n\n"
        "Send a message and I'll forward it to your match.\n\n"
        "Use /endchat to stop chatting."
    )


async def end_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop(
        "chat_partner",
        None,
    )

    await update.message.reply_text(
        "🛑 Chat mode ended."
    )


async def forward_chat_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    partner_id = context.user_data.get(
        "chat_partner"
    )

    if not partner_id:
        return

    if not update.message:
        return

    try:
        await context.bot.copy_message(
            chat_id=partner_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )

        await update.message.reply_text(
            "✅ Sent"
        )

    except Exception:
        await update.message.reply_text(
            "⚠️ Unable to send the message right now."
        )

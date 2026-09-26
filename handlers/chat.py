from telegram import Update
from telegram.ext import ContextTypes

from database import get_connection
from services.chat import (
    save_chat_message,
    get_unread_count,
    mark_messages_read,
    get_chat_history,
)
from services.moderation import is_blocked


def get_match_partner(user_id):
    connection = get_connection()

    match = connection.execute(
        """
        SELECT user1_id, user2_id
        FROM matches
        WHERE (user1_id = ? OR user2_id = ?)
          AND status = 'active'
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

    # Mark previous incoming messages as read.
    mark_messages_read(user_id, partner_id)

    unread = get_unread_count(user_id)

    from keyboards.matching import advanced_chat_keyboard

    await query.edit_message_text(
        "💬 <b>Chat mode enabled!</b>\n\n"
        "Send a message and I'll forward it to your match.\n\n"
        "📖 Chat history is available below.\n"
        "🔔 Unread messages are tracked automatically.",
        reply_markup=advanced_chat_keyboard(unread),
        parse_mode="HTML",
    )


async def end_chat(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.pop("chat_partner", None)

    await update.message.reply_text(
        "🛑 Chat mode ended.\n\n"
        "You can start chatting again from your match."
    )


async def forward_chat_message(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    partner_id = context.user_data.get("chat_partner")

    if not partner_id:
        return

    if not update.message:
        return

    user_id = update.effective_user.id

    # Make sure the current chat is still an active match.
    current_partner = get_match_partner(user_id)

    if current_partner != partner_id:
        context.user_data.pop("chat_partner", None)

        await update.message.reply_text(
            "⚠️ This chat is no longer active."
        )
        return

    # Respect blocks in both directions.
    if is_blocked(user_id, partner_id) or is_blocked(partner_id, user_id):
        context.user_data.pop("chat_partner", None)

        await update.message.reply_text(
            "🚫 This chat is unavailable because one of the users "
            "has blocked the other."
        )
        return

    message_type = "text"
    message_preview = None

    if update.message.text:
        message_type = "text"
        message_preview = update.message.text[:500]

    elif update.message.photo:
        message_type = "photo"
        message_preview = "📷 Photo"

    elif update.message.video:
        message_type = "video"
        message_preview = "🎥 Video"

    elif update.message.voice:
        message_type = "voice"
        message_preview = "🎤 Voice message"

    elif update.message.audio:
        message_type = "audio"
        message_preview = "🎵 Audio"

    elif update.message.document:
        message_type = "document"
        message_preview = "📎 Document"

    elif update.message.sticker:
        message_type = "sticker"
        message_preview = "😊 Sticker"

    elif update.message.animation:
        message_type = "animation"
        message_preview = "🎞️ Animation"

    else:
        message_type = "other"
        message_preview = "📨 Message"

    reply_to_message_id = None

    if update.message.reply_to_message:
        reply_to_message_id = update.message.reply_to_message.message_id

    try:
        await context.bot.copy_message(
            chat_id=partner_id,
            from_chat_id=update.effective_chat.id,
            message_id=update.message.message_id,
        )

        save_chat_message(
            sender_id=user_id,
            receiver_id=partner_id,
            message_id=update.message.message_id,
            message_type=message_type,
            message_preview=message_preview,
            reply_to_message_id=reply_to_message_id,
        )

        await update.message.reply_text("✅ Sent")

    except Exception:
        await update.message.reply_text(
            "⚠️ Unable to send the message right now."
        )


def get_recent_chat_history(user_id, partner_id, limit=20):
    return get_chat_history(
        user_id,
        partner_id,
        limit=limit,
    )


async def chat_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    partner_id = get_match_partner(user_id)

    if not partner_id:
        await query.edit_message_text(
            "💬 You don't have an active match."
        )
        return

    unread = get_unread_count(user_id)

    from keyboards.matching import advanced_chat_keyboard

    await query.edit_message_text(
        "💬 <b>Advanced Chat</b>\n\n"
        f"🔔 Unread messages: <b>{unread}</b>\n\n"
        "Choose an option below:",
        reply_markup=advanced_chat_keyboard(unread),
        parse_mode="HTML",
    )


async def chat_continue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    partner_id = get_match_partner(user_id)

    if not partner_id:
        await query.edit_message_text(
            "💬 You don't have an active match."
        )
        return

    context.user_data["chat_partner"] = partner_id

    mark_messages_read(user_id, partner_id)

    await query.edit_message_text(
        "💬 <b>Chat mode enabled!</b>\n\n"
        "Send your message and it will be forwarded to your match.\n\n"
        "Use /endchat anytime to stop.",
        parse_mode="HTML",
    )


async def chat_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    partner_id = get_match_partner(user_id)

    if not partner_id:
        await query.edit_message_text(
            "📖 No active match found."
        )
        return

    history = get_chat_history(
        user_id,
        partner_id,
        limit=20,
    )

    if not history:
        await query.edit_message_text(
            "📖 <b>Chat History</b>\n\n"
            "No messages yet.",
            parse_mode="HTML",
        )
        return

    lines = ["📖 <b>Recent Chat History</b>\n"]

    for row in history:
        sender = "You" if row["sender_id"] == user_id else "Match"
        preview = row["message_preview"] or "📨 Message"
        timestamp = row["created_at"]

        lines.append(
            f"<b>{sender}</b> · {timestamp}\n"
            f"{preview}\n"
        )

    text = "\n".join(lines)

    if len(text) > 4000:
        text = text[:3950] + "\n\n…"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
    )


async def chat_unread(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    unread = get_unread_count(user_id)

    await query.edit_message_text(
        "🔔 <b>Unread Messages</b>\n\n"
        f"You have <b>{unread}</b> unread message(s).",
        parse_mode="HTML",
    )


async def chat_end(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data.pop("chat_partner", None)

    await query.edit_message_text(
        "🛑 <b>Chat ended.</b>\n\n"
        "You can start it again from your match.",
        parse_mode="HTML",
    )

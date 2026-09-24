from telegram import Update
from telegram.ext import ContextTypes

from database import get_connection
from keyboards.matching import match_actions_keyboard


def get_match_profile(user_id):
    conn = get_connection()
    row = conn.execute(
        """
        SELECT u.*
        FROM matches m
        JOIN users u
          ON u.telegram_id = CASE
                WHEN m.user1_id = ? THEN m.user2_id
                ELSE m.user1_id
             END
        WHERE (m.user1_id = ? OR m.user2_id = ?)
          AND m.status = 'active'
        ORDER BY m.created_at DESC
        LIMIT 1
        """,
        (user_id, user_id, user_id),
    ).fetchone()
    conn.close()
    return row


async def view_match(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    profile = get_match_profile(user_id)

    if not profile:
        await query.message.reply_text(
            "💔 You don't have an active match yet."
        )
        return

    text = (
        "💖 <b>Your Match</b>\n\n"
        f"👤 <b>{profile['name']}, {profile['age']}</b>\n"
        f"📍 {profile['city']}\n\n"
        f"📝 {profile['bio'] or 'No bio available.'}\n\n"
        "✨ You can start chatting whenever you're ready."
    )

    await query.message.reply_text(
        text,
        reply_markup=match_actions_keyboard(),
        parse_mode="HTML",
    )


async def unmatch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    profile = get_match_profile(user_id)

    if not profile:
        await query.message.reply_text(
            "ℹ️ No active match found."
        )
        return

    target_id = profile["telegram_id"]

    conn = get_connection()
    conn.execute(
        """
        UPDATE matches
        SET status = 'unmatched'
        WHERE status = 'active'
          AND (
                (user1_id = ? AND user2_id = ?)
                OR
                (user1_id = ? AND user2_id = ?)
              )
        """,
        (user_id, target_id, target_id, user_id),
    )
    conn.commit()
    conn.close()

    await query.message.reply_text(
        "💔 Match removed successfully."
    )

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


async def ai_icebreaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer("🤖 Creating an icebreaker...")

    from services.ai import generate_icebreaker

    user_id = update.effective_user.id

    conn = get_connection()
    user = conn.execute(
        "SELECT name, city, bio FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()
    conn.close()

    profile = get_match_profile(user_id)

    if not user or not profile:
        await query.message.reply_text(
            "💔 You need an active match to generate an icebreaker."
        )
        return

    try:
        message = await generate_icebreaker(
            user_name=user["name"] or "",
            user_city=user["city"] or "",
            user_bio=user["bio"] or "",
            match_name=profile["name"] or "",
            match_city=profile["city"] or "",
            match_bio=profile["bio"] or "",
        )
    except Exception:
        await query.message.reply_text(
            "❌ Couldn't generate an icebreaker right now. Please try again."
        )
        return

    await query.message.reply_text(
        "🤖 <b>AI Icebreaker</b>\n\n"
        f"💬 {message}\n\n"
        "You can copy it and send it to your match.",
        parse_mode="HTML",
    )

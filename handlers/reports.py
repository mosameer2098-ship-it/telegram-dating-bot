from telegram import Update
from telegram.ext import ContextTypes

from database import get_connection


async def handle_report(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    reported_id = context.user_data.get("current_profile")

    if not reported_id:
        await query.edit_message_text(
            "⚠️ This profile is no longer available."
        )
        return

    reporter_id = update.effective_user.id

    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            reported_id INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        INSERT INTO reports (
            reporter_id,
            reported_id,
            reason
        )
        VALUES (?, ?, ?)
        """,
        (
            reporter_id,
            reported_id,
            "Profile reported by user",
        ),
    )

    connection.commit()
    connection.close()

    context.user_data.pop("current_profile", None)

    await query.edit_message_text(
        "🚩 Report submitted.\n\n"
        "Thank you for helping keep LoveMatch safe."
    )

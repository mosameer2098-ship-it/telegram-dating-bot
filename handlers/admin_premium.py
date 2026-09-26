from datetime import datetime, timedelta

from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID
from database import get_connection


def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)


async def premium_grant(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    if len(context.args) != 2:
        await update.message.reply_text(
            "Usage:\n/premium_grant USER_ID DAYS"
        )
        return

    try:
        user_id = int(context.args[0])
        days = int(context.args[1])

        if days <= 0:
            raise ValueError
    except ValueError:
        await update.message.reply_text(
            "❌ USER_ID and DAYS must be valid numbers."
        )
        return

    connection = get_connection()

    user = connection.execute(
        "SELECT telegram_id FROM users WHERE telegram_id = ?",
        (user_id,),
    ).fetchone()

    if not user:
        connection.close()
        await update.message.reply_text(
            "❌ User profile not found."
        )
        return

    premium_until = datetime.utcnow() + timedelta(days=days)

    connection.execute(
        """
        UPDATE users
        SET is_premium = 1,
            premium_until = ?
        WHERE telegram_id = ?
        """,
        (premium_until.isoformat(), user_id),
    )

    connection.commit()
    connection.close()

    await update.message.reply_text(
        f"✅ Premium granted.\n\n"
        f"👤 User: {user_id}\n"
        f"📅 Days: {days}\n"
        f"⏳ Until: {premium_until.isoformat()}"
    )


async def premium_revoke(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/premium_revoke USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid USER_ID."
        )
        return

    connection = get_connection()

    connection.execute(
        """
        UPDATE users
        SET is_premium = 0,
            premium_until = NULL
        WHERE telegram_id = ?
        """,
        (user_id,),
    )

    connection.commit()
    connection.close()

    await update.message.reply_text(
        f"✅ Premium revoked for user {user_id}."
    )


async def premium_status_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/premium_status USER_ID"
        )
        return

    try:
        user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid USER_ID."
        )
        return

    connection = get_connection()

    row = connection.execute(
        """
        SELECT is_premium, premium_until
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    if not row:
        await update.message.reply_text(
            "❌ User profile not found."
        )
        return

    status = "ACTIVE" if row["is_premium"] else "INACTIVE"

    await update.message.reply_text(
        f"💎 Premium Status\n\n"
        f"👤 User: {user_id}\n"
        f"📌 Status: {status}\n"
        f"📅 Until: {row['premium_until'] or 'No expiry'}"
    )

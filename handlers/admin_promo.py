from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_ID
from database import get_connection
from services.promo_codes import create_promo_code, deactivate_promo_code


def is_admin(user_id):
    return int(user_id) == int(ADMIN_ID)


async def promo_create(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    if len(context.args) not in (3, 4):
        await update.message.reply_text(
            "Usage:\n"
            "/promo_create CODE DAYS MAX_USES [EXPIRY_HOURS]\n\n"
            "Examples:\n"
            "/promo_create LOVE7 7 100\n"
            "/promo_create LOVE24 7 100 24\n\n"
            "MAX_USES = 0 means unlimited.\n"
            "EXPIRY_HOURS omitted means no expiry."
        )
        return

    code = context.args[0].strip().upper()

    try:
        days = int(context.args[1])
        max_uses = int(context.args[2])

        if days <= 0:
            raise ValueError

        if max_uses < 0:
            raise ValueError

        expiry_hours = None

        if len(context.args) == 4:
            expiry_hours = int(context.args[3])

            if expiry_hours <= 0:
                raise ValueError

    except ValueError:
        await update.message.reply_text(
            "❌ Invalid values. DAYS must be > 0, "
            "MAX_USES >= 0 and EXPIRY_HOURS > 0."
        )
        return

    expires_at = None

    if expiry_hours is not None:
        from datetime import datetime, timedelta, timezone

        expires_at = (
            datetime.now(timezone.utc)
            + timedelta(hours=expiry_hours)
        ).isoformat()

    try:
        promo = create_promo_code(
            code=code,
            reward_type="premium_days",
            reward_value=days,
            max_uses=max_uses,
            expires_at=expires_at,
        )

    except ValueError as exc:
        await update.message.reply_text(
            f"❌ {exc}"
        )
        return

    usage = (
        "Unlimited"
        if max_uses == 0
        else str(max_uses)
    )

    expiry_text = (
        expires_at
        if expires_at
        else "Never"
    )

    await update.message.reply_text(
        "🎟️ <b>Promo Code Created</b>\n\n"
        f"🔑 Code: <code>{promo['code']}</code>\n"
        f"👑 Premium: <b>{days} days</b>\n"
        f"🔢 Max Uses: <b>{usage}</b>\n"
        f"📊 Used: <b>0</b>\n"
        f"⏳ Expires: <b>{expiry_text}</b>",
        parse_mode="HTML",
    )


async def promo_disable(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    if len(context.args) != 1:
        await update.message.reply_text(
            "Usage:\n/promo_disable CODE"
        )
        return

    code = context.args[0].strip().upper()

    if deactivate_promo_code(code):
        await update.message.reply_text(
            f"🔴 Promo code <code>{code}</code> disabled.",
            parse_mode="HTML",
        )
    else:
        await update.message.reply_text(
            "❌ Promo code not found."
        )


async def promo_list(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("❌ Admin only.")
        return

    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            code,
            reward_type,
            reward_value,
            max_uses,
            used_count,
            active,
            expires_at
        FROM promo_codes
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()

    connection.close()

    if not rows:
        await update.message.reply_text(
            "🎟️ No promo codes found."
        )
        return

    lines = ["🎟️ <b>Promo Codes</b>\n"]

    for row in rows:
        status = "🟢 ACTIVE" if row["active"] else "🔴 DISABLED"

        usage = (
            "∞"
            if not row["max_uses"]
            else f"{row['used_count']}/{row['max_uses']}"
        )

        lines.append(
            f"<b>{row['code']}</b>\n"
            f"👑 {row['reward_value']} premium days\n"
            f"📊 Uses: {usage}\n"
            f"📌 {status}\n"
            f"⏳ Expires: {row['expires_at'] or 'Never'}\n"
        )

    await update.message.reply_text(
        "\n".join(lines),
        parse_mode="HTML",
    )

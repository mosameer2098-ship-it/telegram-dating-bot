from datetime import datetime, timezone

from database import get_connection


def get_premium_mode():
    connection = get_connection()

    row = connection.execute(
        """
        SELECT value
        FROM app_settings
        WHERE key = 'premium_mode'
        """
    ).fetchone()

    connection.close()

    return row["value"] if row else "free"


def has_premium_access(telegram_id):
    # FREE mode: everyone gets Premium access.
    if get_premium_mode() == "free":
        return True

    # PAID mode: only active Premium users get access.
    connection = get_connection()

    row = connection.execute(
        """
        SELECT is_premium, premium_until
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    connection.close()

    if not row or not row["is_premium"]:
        return False

    premium_until = row["premium_until"]

    # Admin-granted Premium without expiry remains active.
    if not premium_until:
        return True

    try:
        expiry = datetime.fromisoformat(premium_until)

        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)

        if expiry <= datetime.now(timezone.utc):
            return False

    except ValueError:
        return False

    return True


def premium_required_message():
    return (
        "💎 Premium is required for this feature.\n\n"
        "Please upgrade to Premium to continue."
    )

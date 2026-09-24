from pathlib import Path
from datetime import datetime, timedelta, timezone

from database import get_connection
from services.notifications.service import notify_boost


def activate_boost(telegram_id, minutes=30):
    if minutes <= 0:
        raise ValueError("Boost duration must be greater than 0")

    conn = get_connection()

    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(minutes=minutes)

    conn.execute(
        """
        INSERT INTO boosts (
            telegram_id,
            started_at,
            expires_at,
            is_active
        )
        VALUES (?, ?, ?, 1)
        """,
        (
            telegram_id,
            now.isoformat(),
            expires_at.isoformat(),
        ),
    )

    conn.commit()
    boost_id = conn.execute(
        "SELECT last_insert_rowid()"
    ).fetchone()[0]

    conn.close()

    notify_boost(
        telegram_id,
        f"Your profile boost is active for {minutes} minutes.",
    )

    return {
        "id": boost_id,
        "telegram_id": telegram_id,
        "started_at": now.isoformat(),
        "expires_at": expires_at.isoformat(),
        "minutes": minutes,
    }


def get_active_boost(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM boosts
        WHERE telegram_id = ?
          AND is_active = 1
        ORDER BY expires_at DESC
        LIMIT 1
        """,
        (telegram_id,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    expires_at = datetime.fromisoformat(row["expires_at"])

    if expires_at <= datetime.now(timezone.utc):
        conn.execute(
            """
            UPDATE boosts
            SET is_active = 0
            WHERE id = ?
            """,
            (row["id"],),
        )
        conn.commit()
        conn.close()
        return None

    result = dict(row)
    conn.close()
    return result


def is_boosted(telegram_id):
    return get_active_boost(telegram_id) is not None


def deactivate_expired_boosts():
    conn = get_connection()

    now = datetime.now(timezone.utc).isoformat()

    cursor = conn.execute(
        """
        UPDATE boosts
        SET is_active = 0
        WHERE is_active = 1
          AND expires_at <= ?
        """,
        (now,),
    )

    conn.commit()
    count = cursor.rowcount
    conn.close()

    return count

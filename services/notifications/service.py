import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "database" / "lovematch.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_notification(
    telegram_id,
    notification_type,
    title,
    body,
):
    conn = get_connection()

    cursor = conn.execute(
        """
        INSERT INTO notifications (
            telegram_id,
            notification_type,
            title,
            body
        )
        VALUES (?, ?, ?, ?)
        """,
        (
            telegram_id,
            notification_type,
            title,
            body,
        ),
    )

    conn.commit()
    notification_id = cursor.lastrowid
    conn.close()

    return notification_id


def get_unread_notifications(telegram_id, limit=20):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE telegram_id = ?
          AND is_read = 0
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (telegram_id, limit),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_notifications(telegram_id, limit=50):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT *
        FROM notifications
        WHERE telegram_id = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (telegram_id, limit),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def mark_notification_read(notification_id, telegram_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE id = ?
          AND telegram_id = ?
        """,
        (
            notification_id,
            telegram_id,
        ),
    )

    conn.commit()
    conn.close()


def mark_all_read(telegram_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE notifications
        SET is_read = 1
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )

    conn.commit()
    conn.close()


def unread_count(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM notifications
        WHERE telegram_id = ?
          AND is_read = 0
        """,
        (telegram_id,),
    ).fetchone()

    conn.close()

    return row["total"] if row else 0


def notify_like(user_id, liker_name):
    return create_notification(
        user_id,
        "like",
        "❤️ New Like",
        f"{liker_name} liked your profile.",
    )


def notify_super_like(user_id, liker_name):
    return create_notification(
        user_id,
        "super_like",
        "💖 Super Like",
        f"{liker_name} sent you a Super Like!",
    )


def notify_match(user_id, match_name):
    return create_notification(
        user_id,
        "match",
        "💞 New Match",
        f"You matched with {match_name}!",
    )


def notify_message(user_id, sender_name):
    return create_notification(
        user_id,
        "message",
        "💬 New Message",
        f"You received a message from {sender_name}.",
    )


def notify_premium(user_id, message):
    return create_notification(
        user_id,
        "premium",
        "👑 LoveMatch Premium",
        message,
    )


def notify_boost(user_id, message):
    return create_notification(
        user_id,
        "boost",
        "🔥 Profile Boost",
        message,
    )


def notify_referral(user_id, message):
    return create_notification(
        user_id,
        "referral",
        "🎁 Referral Reward",
        message,
    )

from datetime import datetime, timezone

from database import get_connection


def record_activity(telegram_id, online=True):
    now = datetime.now(timezone.utc).isoformat()

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT telegram_id, login_streak
        FROM user_activity
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    if existing:
        streak = existing["login_streak"]
        conn.execute(
            """
            UPDATE user_activity
            SET last_seen = ?,
                online = ?,
                login_streak = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE telegram_id = ?
            """,
            (now, int(online), streak, telegram_id),
        )
    else:
        conn.execute(
            """
            INSERT INTO user_activity (
                telegram_id,
                last_seen,
                online,
                login_streak
            )
            VALUES (?, ?, ?, 1)
            """,
            (telegram_id, now, int(online)),
        )

    conn.commit()
    conn.close()


def set_online(telegram_id):
    record_activity(telegram_id, True)


def set_offline(telegram_id):
    conn = get_connection()

    conn.execute(
        """
        UPDATE user_activity
        SET online = 0,
            updated_at = CURRENT_TIMESTAMP
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    )

    conn.commit()
    conn.close()


def record_profile_view(viewer_id, viewed_id):
    if viewer_id == viewed_id:
        return False

    conn = get_connection()

    conn.execute(
        """
        INSERT INTO profile_views (
            viewer_id,
            viewed_id
        )
        VALUES (?, ?)
        """,
        (viewer_id, viewed_id),
    )

    conn.commit()
    conn.close()

    return True


def get_profile_view_count(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM profile_views
        WHERE viewed_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    conn.close()

    return row["total"] if row else 0


def get_activity(telegram_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM user_activity
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    conn.close()

    return dict(row) if row else None


def unlock_achievement(telegram_id, achievement_key):
    conn = get_connection()

    existing = conn.execute(
        """
        SELECT id
        FROM achievements
        WHERE telegram_id = ?
          AND achievement_key = ?
        LIMIT 1
        """,
        (telegram_id, achievement_key),
    ).fetchone()

    if existing:
        conn.close()
        return False

    conn.execute(
        """
        INSERT INTO achievements (
            telegram_id,
            achievement_key
        )
        VALUES (?, ?)
        """,
        (telegram_id, achievement_key),
    )

    conn.commit()
    conn.close()

    return True


def get_achievements(telegram_id):
    conn = get_connection()

    rows = conn.execute(
        """
        SELECT achievement_key, unlocked_at
        FROM achievements
        WHERE telegram_id = ?
        ORDER BY unlocked_at DESC
        """,
        (telegram_id,),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]

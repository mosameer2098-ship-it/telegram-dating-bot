import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "database" / "lovematch.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_who_liked_me(user_id, limit=20):
    """
    Return users who liked this user but are not already matched.
    """

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            u.telegram_id,
            u.username,
            u.name,
            u.age,
            u.city,
            u.bio,
            u.photo_file_id,
            u.gender,
            u.interested_in,
            l.created_at
        FROM likes l
        JOIN users u
          ON u.telegram_id = l.liker_id
        WHERE l.liked_id = ?
          AND l.liker_id != ?
          AND NOT EXISTS (
              SELECT 1
              FROM matches m
              WHERE m.status = 'active'
                AND (
                    (m.user1_id = ? AND m.user2_id = l.liker_id)
                    OR
                    (m.user1_id = l.liker_id AND m.user2_id = ?)
                )
          )
        ORDER BY l.created_at DESC
        LIMIT ?
        """,
        (user_id, user_id, user_id, user_id, limit),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_who_liked_me_count(user_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM likes l
        WHERE l.liked_id = ?
          AND l.liker_id != ?
          AND NOT EXISTS (
              SELECT 1
              FROM matches m
              WHERE m.status = 'active'
                AND (
                    (m.user1_id = ? AND m.user2_id = l.liker_id)
                    OR
                    (m.user1_id = l.liker_id AND m.user2_id = ?)
                )
          )
        """,
        (user_id, user_id, user_id, user_id),
    ).fetchone()

    conn.close()

    return int(row["total"]) if row else 0

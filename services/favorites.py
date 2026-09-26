import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[1] / "database" / "lovematch.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def add_favorite(user_id, favorite_id):
    if user_id == favorite_id:
        return False

    conn = get_connection()

    existing = conn.execute(
        """
        SELECT 1
        FROM favorites
        WHERE user_id = ?
          AND favorite_id = ?
        """,
        (user_id, favorite_id),
    ).fetchone()

    if existing:
        conn.close()
        return False

    conn.execute(
        """
        INSERT INTO favorites (
            user_id,
            favorite_id
        )
        VALUES (?, ?)
        """,
        (user_id, favorite_id),
    )

    conn.commit()
    conn.close()

    return True


def remove_favorite(user_id, favorite_id):
    conn = get_connection()

    cursor = conn.execute(
        """
        DELETE FROM favorites
        WHERE user_id = ?
          AND favorite_id = ?
        """,
        (user_id, favorite_id),
    )

    conn.commit()
    conn.close()

    return cursor.rowcount > 0


def is_favorite(user_id, favorite_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT 1
        FROM favorites
        WHERE user_id = ?
          AND favorite_id = ?
        """,
        (user_id, favorite_id),
    ).fetchone()

    conn.close()

    return row is not None


def get_favorites(user_id, limit=50):
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
            f.created_at
        FROM favorites f
        JOIN users u
          ON u.telegram_id = f.favorite_id
        WHERE f.user_id = ?
        ORDER BY f.created_at DESC
        LIMIT ?
        """,
        (user_id, limit),
    ).fetchall()

    conn.close()

    return [dict(row) for row in rows]


def get_favorite_count(user_id):
    conn = get_connection()

    row = conn.execute(
        """
        SELECT COUNT(*) AS total
        FROM favorites
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()

    conn.close()

    return int(row["total"]) if row else 0

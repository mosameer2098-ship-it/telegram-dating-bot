import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "database" / "lovematch.db"

from services.notifications.service import (
    notify_like,
    notify_super_like,
    notify_match,
)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


FREE_DAILY_LIKE_LIMIT = 20
FREE_DAILY_SUPER_LIKE_LIMIT = 5


def like_user(user_id, target_id):
    conn = get_connection()

    # Do not count an already-existing like again.
    existing = conn.execute(
        """
        SELECT 1
        FROM likes
        WHERE liker_id = ? AND liked_id = ?
        """,
        (user_id, target_id),
    ).fetchone()

    if existing:
        conn.close()
        return {
            "matched": False,
            "target_id": target_id,
            "already_liked": True,
            "limited": False,
        }

    # Premium users are not limited here.
    premium_row = conn.execute(
        """
        SELECT COALESCE(is_premium, 0) AS is_premium
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    is_premium = bool(premium_row["is_premium"]) if premium_row else False

    if not is_premium:
        like_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM likes
            WHERE liker_id = ?
              AND date(created_at) = date('now')
            """,
            (user_id,),
        ).fetchone()

        daily_count = int(like_count["total"]) if like_count else 0

        if daily_count >= FREE_DAILY_LIKE_LIMIT:
            conn.close()
            return {
                "matched": False,
                "target_id": target_id,
                "already_liked": False,
                "limited": True,
                "daily_limit": FREE_DAILY_LIKE_LIMIT,
                "daily_used": daily_count,
            }

    conn.execute(
        """
        INSERT OR IGNORE INTO likes (liker_id, liked_id)
        VALUES (?, ?)
        """,
        (user_id, target_id),
    )

    conn.commit()

    mutual = conn.execute(
        """
        SELECT id
        FROM likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (target_id, user_id),
    ).fetchone()

    if mutual:
        user1 = min(user_id, target_id)
        user2 = max(user_id, target_id)

        conn.execute(
            """
            INSERT OR IGNORE INTO matches (user1_id, user2_id)
            VALUES (?, ?)
            """,
            (user1, user2),
        )
        conn.commit()

    conn.close()

    if mutual:
        notify_like(target_id, f"User {user_id}")
        notify_match(user_id, f"User {target_id}")
        notify_match(target_id, f"User {user_id}")
    else:
        notify_like(target_id, f"User {user_id}")

    return {
        "matched": mutual is not None,
        "target_id": target_id,
    }


def super_like_user(user_id, target_id):
    conn = get_connection()

    # Do not count an already-existing Super Like again.
    existing = conn.execute(
        """
        SELECT 1
        FROM super_likes
        WHERE liker_id = ? AND liked_id = ?
        """,
        (user_id, target_id),
    ).fetchone()

    if existing:
        conn.close()
        return {
            "matched": False,
            "target_id": target_id,
            "already_super_liked": True,
            "limited": False,
        }

    # Premium users are not limited here.
    premium_row = conn.execute(
        """
        SELECT COALESCE(is_premium, 0) AS is_premium
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    is_premium = bool(premium_row["is_premium"]) if premium_row else False

    if not is_premium:
        super_like_count = conn.execute(
            """
            SELECT COUNT(*) AS total
            FROM super_likes
            WHERE liker_id = ?
              AND date(created_at) = date('now')
            """,
            (user_id,),
        ).fetchone()

        daily_count = (
            int(super_like_count["total"])
            if super_like_count
            else 0
        )

        if daily_count >= FREE_DAILY_SUPER_LIKE_LIMIT:
            conn.close()
            return {
                "matched": False,
                "target_id": target_id,
                "already_super_liked": False,
                "limited": True,
                "daily_limit": FREE_DAILY_SUPER_LIKE_LIMIT,
                "daily_used": daily_count,
            }

    conn.execute(
        """
        INSERT OR IGNORE INTO super_likes (liker_id, liked_id)
        VALUES (?, ?)
        """,
        (user_id, target_id),
    )

    # A Super Like also counts as a Like.
    conn.execute(
        """
        INSERT OR IGNORE INTO likes (liker_id, liked_id)
        VALUES (?, ?)
        """,
        (user_id, target_id),
    )

    conn.commit()

    mutual = conn.execute(
        """
        SELECT id
        FROM likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (target_id, user_id),
    ).fetchone()

    if mutual:
        user1 = min(user_id, target_id)
        user2 = max(user_id, target_id)

        conn.execute(
            """
            INSERT OR IGNORE INTO matches (user1_id, user2_id)
            VALUES (?, ?)
            """,
            (user1, user2),
        )
        conn.commit()

    conn.close()

    if mutual:
        notify_super_like(target_id, f"User {user_id}")
        notify_match(user_id, f"User {target_id}")
        notify_match(target_id, f"User {user_id}")
    else:
        notify_super_like(target_id, f"User {user_id}")

    return {
        "matched": mutual is not None,
        "target_id": target_id,
    }


def pass_user(user_id, target_id):
    conn = get_connection()

    conn.execute(
        """
        INSERT OR IGNORE INTO passes (passer_id, passed_id)
        VALUES (?, ?)
        """,
        (user_id, target_id),
    )

    conn.commit()
    conn.close()

    return True


def rewind_user(user_id, target_id):
    """
    Remove the most recent Like/Pass/Super Like action
    for the selected target.
    """

    conn = get_connection()

    conn.execute(
        """
        DELETE FROM likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (user_id, target_id),
    )

    conn.execute(
        """
        DELETE FROM super_likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (user_id, target_id),
    )

    conn.execute(
        """
        DELETE FROM passes
        WHERE passer_id = ?
          AND passed_id = ?
        """,
        (user_id, target_id),
    )

    conn.commit()
    conn.close()

    return True


def get_action_state(user_id, target_id):
    conn = get_connection()

    liked = conn.execute(
        """
        SELECT 1 FROM likes
        WHERE liker_id = ? AND liked_id = ?
        """,
        (user_id, target_id),
    ).fetchone()

    super_liked = conn.execute(
        """
        SELECT 1 FROM super_likes
        WHERE liker_id = ? AND liked_id = ?
        """,
        (user_id, target_id),
    ).fetchone()

    passed = conn.execute(
        """
        SELECT 1 FROM passes
        WHERE passer_id = ? AND passed_id = ?
        """,
        (user_id, target_id),
    ).fetchone()

    conn.close()

    return {
        "liked": liked is not None,
        "super_liked": super_liked is not None,
        "passed": passed is not None,
    }

from database import get_connection


def block_user(blocker_id, blocked_id):
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS blocked_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            blocker_id INTEGER NOT NULL,
            blocked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(blocker_id, blocked_id)
        )
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO blocked_users (
            blocker_id,
            blocked_id
        )
        VALUES (?, ?)
        """,
        (blocker_id, blocked_id),
    )

    connection.commit()
    connection.close()


def is_blocked(user_id, other_user_id):
    connection = get_connection()

    result = connection.execute(
        """
        SELECT id
        FROM blocked_users
        WHERE blocker_id = ?
        AND blocked_id = ?
        """,
        (user_id, other_user_id),
    ).fetchone()

    connection.close()

    return result is not None

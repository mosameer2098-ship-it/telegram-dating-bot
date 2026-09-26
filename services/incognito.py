from database import get_connection


def is_incognito(user_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT COALESCE(is_incognito, 0) AS is_incognito
        FROM users
        WHERE telegram_id = ?
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    return bool(row["is_incognito"]) if row else False


def set_incognito(user_id, enabled):
    connection = get_connection()

    connection.execute(
        """
        UPDATE users
        SET is_incognito = ?
        WHERE telegram_id = ?
        """,
        (1 if enabled else 0, user_id),
    )

    connection.commit()
    connection.close()

    return bool(enabled)


def toggle_incognito(user_id):
    current = is_incognito(user_id)
    return set_incognito(user_id, not current)

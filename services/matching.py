from database import get_connection


def get_profile(telegram_id):
    connection = get_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    connection.close()

    return user


def get_discover_profile(
    telegram_id,
    gender=None,
    city=None,
):
    connection = get_connection()

    query = """
        SELECT *
        FROM users
        WHERE telegram_id != ?
          AND telegram_id NOT IN (
              SELECT blocked_id
              FROM blocked_users
              WHERE blocker_id = ?
          )
    """

    params = [telegram_id, telegram_id]

    if gender:
        query += " AND gender = ?"
        params.append(gender)

    if city:
        query += " AND city = ?"
        params.append(city)

    query += """
        AND telegram_id NOT IN (
            SELECT liked_id
            FROM likes
            WHERE liker_id = ?
        )
    """

    params.append(telegram_id)

    query += """
        ORDER BY RANDOM()
        LIMIT 1
    """

    user = connection.execute(
        query,
        params,
    ).fetchone()

    connection.close()

    return user


def add_like(liker_id, liked_id):
    connection = get_connection()

    connection.execute(
        """
        INSERT OR IGNORE INTO likes (
            liker_id,
            liked_id
        )
        VALUES (?, ?)
        """,
        (liker_id, liked_id),
    )

    connection.commit()

    mutual_like = connection.execute(
        """
        SELECT id
        FROM likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (liked_id, liker_id),
    ).fetchone()

    if mutual_like:
        user1 = min(liker_id, liked_id)
        user2 = max(liker_id, liked_id)

        connection.execute(
            """
            INSERT OR IGNORE INTO matches (
                user1_id,
                user2_id
            )
            VALUES (?, ?)
            """,
            (user1, user2),
        )

        connection.commit()

    connection.close()

    return bool(mutual_like)


def has_liked(liker_id, liked_id):
    connection = get_connection()

    result = connection.execute(
        """
        SELECT id
        FROM likes
        WHERE liker_id = ?
          AND liked_id = ?
        """,
        (liker_id, liked_id),
    ).fetchone()

    connection.close()

    return result is not None

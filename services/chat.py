import sqlite3

from database import DB_PATH


def _connect():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def save_chat_message(
    sender_id,
    receiver_id,
    message_id=None,
    message_type="text",
    message_preview=None,
    reply_to_message_id=None,
):
    connection = _connect()

    cursor = connection.execute(
        """
        INSERT INTO chat_messages (
            sender_id,
            receiver_id,
            message_id,
            message_type,
            message_preview,
            reply_to_message_id,
            is_read
        )
        VALUES (?, ?, ?, ?, ?, ?, 0)
        """,
        (
            sender_id,
            receiver_id,
            message_id,
            message_type,
            message_preview,
            reply_to_message_id,
        ),
    )

    connection.commit()
    message_db_id = cursor.lastrowid
    connection.close()

    return message_db_id


def get_unread_count(user_id):
    connection = _connect()

    row = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM chat_messages
        WHERE receiver_id = ?
          AND is_read = 0
        """,
        (user_id,),
    ).fetchone()

    connection.close()

    return row[0] if row else 0


def mark_messages_read(user_id, partner_id):
    connection = _connect()

    connection.execute(
        """
        UPDATE chat_messages
        SET is_read = 1
        WHERE receiver_id = ?
          AND sender_id = ?
          AND is_read = 0
        """,
        (user_id, partner_id),
    )

    connection.commit()
    connection.close()


def get_chat_history(user_id, partner_id, limit=20):
    connection = _connect()

    rows = connection.execute(
        """
        SELECT
            id,
            sender_id,
            receiver_id,
            message_id,
            message_type,
            message_preview,
            reply_to_message_id,
            is_read,
            created_at
        FROM chat_messages
        WHERE
            (sender_id = ? AND receiver_id = ?)
            OR
            (sender_id = ? AND receiver_id = ?)
        ORDER BY id DESC
        LIMIT ?
        """,
        (
            user_id,
            partner_id,
            partner_id,
            user_id,
            limit,
        ),
    ).fetchall()

    connection.close()

    return list(reversed(rows))


def delete_chat_history(user_id, partner_id):
    connection = _connect()

    connection.execute(
        """
        DELETE FROM chat_messages
        WHERE
            (sender_id = ? AND receiver_id = ?)
            OR
            (sender_id = ? AND receiver_id = ?)
        """,
        (
            user_id,
            partner_id,
            partner_id,
            user_id,
        ),
    )

    connection.commit()
    connection.close()

import sqlite3
from database import DB_PATH

MAX_PROFILE_PHOTOS = 6


def _connect():
    return sqlite3.connect(DB_PATH)


def get_profile_photos(telegram_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT id, telegram_id, file_id, is_primary, created_at
        FROM profile_photos
        WHERE telegram_id = ?
        ORDER BY is_primary DESC, id ASC
    """, (telegram_id,))

    rows = cur.fetchall()
    db.close()
    return rows


def get_profile_photo_count(telegram_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM profile_photos
        WHERE telegram_id = ?
    """, (telegram_id,))

    count = cur.fetchone()[0]
    db.close()
    return count


def add_profile_photo(telegram_id, file_id, is_primary=False):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT COUNT(*)
        FROM profile_photos
        WHERE telegram_id = ?
    """, (telegram_id,))

    count = cur.fetchone()[0]

    if count >= MAX_PROFILE_PHOTOS:
        db.close()
        return None

    if count == 0:
        is_primary = True

    if is_primary:
        cur.execute("""
            UPDATE profile_photos
            SET is_primary = 0
            WHERE telegram_id = ?
        """, (telegram_id,))

    cur.execute("""
        INSERT INTO profile_photos
        (telegram_id, file_id, is_primary)
        VALUES (?, ?, ?)
    """, (
        telegram_id,
        file_id,
        1 if is_primary else 0,
    ))

    photo_id = cur.lastrowid
    db.commit()
    db.close()

    return photo_id


def set_primary_photo(telegram_id, photo_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT id
        FROM profile_photos
        WHERE id = ? AND telegram_id = ?
    """, (photo_id, telegram_id))

    if not cur.fetchone():
        db.close()
        return False

    cur.execute("""
        UPDATE profile_photos
        SET is_primary = 0
        WHERE telegram_id = ?
    """, (telegram_id,))

    cur.execute("""
        UPDATE profile_photos
        SET is_primary = 1
        WHERE id = ? AND telegram_id = ?
    """, (photo_id, telegram_id))

    db.commit()
    db.close()

    return True


def delete_profile_photo(telegram_id, photo_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT is_primary
        FROM profile_photos
        WHERE id = ? AND telegram_id = ?
    """, (photo_id, telegram_id))

    row = cur.fetchone()

    if not row:
        db.close()
        return False

    was_primary = bool(row[0])

    cur.execute("""
        DELETE FROM profile_photos
        WHERE id = ? AND telegram_id = ?
    """, (photo_id, telegram_id))

    if was_primary:
        cur.execute("""
            SELECT id
            FROM profile_photos
            WHERE telegram_id = ?
            ORDER BY id ASC
            LIMIT 1
        """, (telegram_id,))

        next_photo = cur.fetchone()

        if next_photo:
            cur.execute("""
                UPDATE profile_photos
                SET is_primary = 1
                WHERE id = ?
            """, (next_photo[0],))

    db.commit()
    db.close()

    return True

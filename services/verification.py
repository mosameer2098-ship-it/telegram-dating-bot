import sqlite3
from database import DB_PATH


def _connect():
    return sqlite3.connect(DB_PATH)


def is_verified(telegram_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT 1
        FROM profile_verifications
        WHERE telegram_id = ?
          AND status = 'verified'
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))

    result = cur.fetchone()
    db.close()

    return result is not None


def get_verification(telegram_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT id, telegram_id, photo_file_id, status, created_at
        FROM profile_verifications
        WHERE telegram_id = ?
        ORDER BY id DESC
        LIMIT 1
    """, (telegram_id,))

    result = cur.fetchone()
    db.close()

    return result


def submit_verification(telegram_id, photo_file_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        SELECT id
        FROM profile_verifications
        WHERE telegram_id = ?
          AND status = 'verified'
        LIMIT 1
    """, (telegram_id,))

    existing = cur.fetchone()

    if existing:
        db.close()
        return existing[0]

    cur.execute("""
        INSERT INTO profile_verifications
        (
            telegram_id,
            photo_file_id,
            status
        )
        VALUES (?, ?, 'verified')
    """, (
        telegram_id,
        photo_file_id,
    ))

    verification_id = cur.lastrowid

    db.commit()
    db.close()

    return verification_id


def remove_verification(telegram_id):
    db = _connect()
    cur = db.cursor()

    cur.execute("""
        DELETE FROM profile_verifications
        WHERE telegram_id = ?
    """, (telegram_id,))

    deleted = cur.rowcount

    db.commit()
    db.close()

    return deleted > 0

import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "lovematch.db"


def get_connection():
    DB_DIR.mkdir(exist_ok=True)

    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    return connection


def init_db():
    connection = get_connection()

    # Users
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            username TEXT,
            name TEXT NOT NULL,
            age INTEGER NOT NULL,
            city TEXT NOT NULL,
            bio TEXT,
            photo_file_id TEXT,
            gender TEXT,
            interested_in TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Add new columns to old databases
    columns = {
        row["name"]
        for row in connection.execute(
            "PRAGMA table_info(users)"
        ).fetchall()
    }

    new_columns = {
        "photo_file_id": "TEXT",
        "gender": "TEXT",
        "interested_in": "TEXT",
    }

    for column, column_type in new_columns.items():
        if column not in columns:
            connection.execute(
                f"ALTER TABLE users ADD COLUMN {column} {column_type}"
            )

    # Likes
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS likes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            liker_id INTEGER NOT NULL,
            liked_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(liker_id, liked_id)
        )
        """
    )

    # Matches
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS matches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user1_id INTEGER NOT NULL,
            user2_id INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user1_id, user2_id)
        )
        """
    )

    connection.commit()
    connection.close()


def save_profile(
    telegram_id,
    username,
    name,
    age,
    city,
    bio,
    photo_file_id=None,
    gender=None,
    interested_in=None,
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO users (
            telegram_id,
            username,
            name,
            age,
            city,
            bio,
            photo_file_id,
            gender,
            interested_in
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            name = excluded.name,
            age = excluded.age,
            city = excluded.city,
            bio = excluded.bio,
            photo_file_id = excluded.photo_file_id,
            gender = excluded.gender,
            interested_in = excluded.interested_in
        """,
        (
            telegram_id,
            username,
            name,
            age,
            city,
            bio,
            photo_file_id,
            gender,
            interested_in,
        ),
    )

    connection.commit()
    connection.close()


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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
            bio
        )
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            name = excluded.name,
            age = excluded.age,
            city = excluded.city,
            bio = excluded.bio
        """,
        (
            telegram_id,
            username,
            name,
            age,
            city,
            bio,
        ),
    )

    connection.commit()
    connection.close()

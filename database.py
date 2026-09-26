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
        "language": "TEXT DEFAULT 'en'",
        "is_premium": "INTEGER DEFAULT 0",
        "premium_until": "TIMESTAMP",
        "is_incognito": "INTEGER DEFAULT 0",
    }

    for column, column_type in new_columns.items():
        if column not in columns:
            connection.execute(
                f"ALTER TABLE users ADD COLUMN {column} {column_type}"
            )

    # App settings
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS app_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
        """
    )

    connection.execute(
        """
        INSERT OR IGNORE INTO app_settings (key, value)
        VALUES ('premium_mode', 'free')
        """
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

    # Blocked users
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

    # Reports
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reporter_id INTEGER NOT NULL,
            reported_id INTEGER NOT NULL,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    # Indexes
    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_likes_liker
        ON likes(liker_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_likes_liked
        ON likes(liked_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_matches_user1
        ON matches(user1_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_matches_user2
        ON matches(user2_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_blocked_blocker
        ON blocked_users(blocker_id)
        """
    )

    connection.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_reports_reporter
        ON reports(reporter_id)
        """
    )

    # Apply additive SQL migrations bundled with the project.
    migrations_dir = BASE_DIR / "migrations"
    if migrations_dir.exists():
        for migration in sorted(migrations_dir.glob("*.sql")):
            sql = migration.read_text(encoding="utf-8")
            try:
                connection.executescript(sql)
            except sqlite3.OperationalError as exc:
                # Keep startup resilient when an already-applied additive statement
                # is encountered; migrations are designed to be idempotent.
                if "duplicate column name" not in str(exc).lower():
                    raise

    connection.commit()
    connection.close()


def set_user_language(telegram_id, language):
    connection = get_connection()

    connection.execute(
        """
        UPDATE users
        SET language = ?
        WHERE telegram_id = ?
        """,
        (language, telegram_id),
    )

    connection.commit()
    connection.close()


def get_user_language(telegram_id):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT language
        FROM users
        WHERE telegram_id = ?
        """,
        (telegram_id,),
    ).fetchone()

    connection.close()

    if not row or not row["language"]:
        return "en"

    return row["language"]


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
    language="en",
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
            interested_in,
            language
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)

        ON CONFLICT(telegram_id)
        DO UPDATE SET
            username = excluded.username,
            name = excluded.name,
            age = excluded.age,
            city = excluded.city,
            bio = excluded.bio,
            photo_file_id = excluded.photo_file_id,
            gender = excluded.gender,
            interested_in = excluded.interested_in,
            language = excluded.language
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
            language,
        ),
    )

    connection.commit()
    connection.close()

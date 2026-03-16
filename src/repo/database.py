"""Database initialization and connection management. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from src.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)

_MIGRATIONS: list[tuple[int, str]] = [
    (1, "ALTER TABLE users ADD COLUMN language_code TEXT DEFAULT NULL"),
]

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
    language_code TEXT DEFAULT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    is_free INTEGER DEFAULT 1,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL UNIQUE REFERENCES topics(id) ON DELETE CASCADE,
    schedule_type TEXT NOT NULL CHECK(schedule_type IN ('interval', 'fixed_time')),
    value TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    last_sent_at TEXT
);

CREATE TABLE IF NOT EXISTS sent_photos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    photo_id TEXT NOT NULL,
    source TEXT NOT NULL CHECK(source IN ('pexels', 'unsplash')),
    sent_at TEXT DEFAULT (datetime('now')),
    UNIQUE(topic_id, photo_id, source)
);

CREATE INDEX IF NOT EXISTS idx_sent_photos_topic ON sent_photos(topic_id);
CREATE INDEX IF NOT EXISTS idx_topics_user ON topics(user_id);
CREATE INDEX IF NOT EXISTS idx_schedules_active ON schedules(is_active);
"""


async def get_connection(db_path: str | None = None) -> aiosqlite.Connection:
    """Create a new database connection.

    Args:
        db_path: Override path (use ":memory:" for tests). Defaults to DATABASE_PATH from config.

    Returns:
        An open aiosqlite connection with WAL mode and foreign keys enabled.
    """
    path = db_path or DATABASE_PATH

    if path != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)

    db = await aiosqlite.connect(path)
    db.row_factory = aiosqlite.Row
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA foreign_keys=ON")
    return db


async def _ensure_schema_version_table(db: aiosqlite.Connection) -> None:
    """Create the schema_version tracking table if it does not exist."""
    await db.execute(
        "CREATE TABLE IF NOT EXISTS schema_version ("
        "    version INTEGER PRIMARY KEY,"
        "    applied_at TEXT DEFAULT (datetime('now'))"
        ")"
    )
    await db.commit()


async def run_migrations(db: aiosqlite.Connection) -> None:
    """Apply pending migrations in order. Idempotent — safe to call multiple times."""
    await _ensure_schema_version_table(db)

    cursor = await db.execute("SELECT COALESCE(MAX(version), 0) FROM schema_version")
    row = await cursor.fetchone()
    current_version: int = row[0] if row else 0

    for version, sql in _MIGRATIONS:
        if version <= current_version:
            continue

        try:
            await db.execute(sql)
            await db.execute(
                "INSERT INTO schema_version (version) VALUES (?)", (version,)
            )
            await db.commit()
            logger.info("Applied migration v%d.", version)
        except Exception:
            # Column may already exist (e.g. fresh DB created with updated DDL).
            # SQLite raises OperationalError for duplicate ALTER TABLE ADD COLUMN.
            await db.rollback()
            await db.execute(
                "INSERT OR IGNORE INTO schema_version (version) VALUES (?)", (version,)
            )
            await db.commit()
            logger.info("Migration v%d already applied, skipped.", version)


async def init_db(db: aiosqlite.Connection) -> None:
    """Initialize database schema. Safe to call multiple times (CREATE IF NOT EXISTS)."""
    await db.executescript(_DDL)
    await db.commit()
    logger.info("Database schema initialized.")
    await run_migrations(db)

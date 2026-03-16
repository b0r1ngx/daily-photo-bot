"""Database initialization and connection management. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging
from pathlib import Path

import aiosqlite

from src.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)

_DDL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    username TEXT,
    first_name TEXT,
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


async def init_db(db: aiosqlite.Connection) -> None:
    """Initialize database schema. Safe to call multiple times (CREATE IF NOT EXISTS)."""
    await db.executescript(_DDL)
    await db.commit()
    logger.info("Database schema initialized.")

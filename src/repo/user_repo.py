"""User repository. Layer: Repo (depends on: types, config)."""
from __future__ import annotations

import logging

import aiosqlite

from src.types.user import User

logger = logging.getLogger(__name__)


class UserRepo:
    """SQLite-backed user data access."""

    def __init__(self, db: aiosqlite.Connection) -> None:
        self._db = db

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
    ) -> User:
        """Get existing user or create a new one."""
        row = await self._fetch_by_telegram_id(telegram_id)
        if row:
            return self._row_to_user(row)

        await self._db.execute(
            "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name),
        )
        await self._db.commit()
        logger.info("Created new user: telegram_id=%d", telegram_id)

        row = await self._fetch_by_telegram_id(telegram_id)
        return self._row_to_user(row)  # type: ignore[arg-type]

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        """Get user by Telegram ID, or None if not found."""
        row = await self._fetch_by_telegram_id(telegram_id)
        if row is None:
            return None
        return self._row_to_user(row)

    async def _fetch_by_telegram_id(self, telegram_id: int) -> aiosqlite.Row | None:
        cursor = await self._db.execute(
            "SELECT id, telegram_id, username, first_name, created_at "
            "FROM users WHERE telegram_id = ?",
            (telegram_id,),
        )
        return await cursor.fetchone()

    @staticmethod
    def _row_to_user(row: aiosqlite.Row) -> User:
        return User(
            id=row[0],
            telegram_id=row[1],
            username=row[2],
            first_name=row[3],
            created_at=row[4],
        )

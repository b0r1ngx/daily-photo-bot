"""User and topic data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class User:
    """Represents a bot user."""

    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    language_code: str | None = None
    id: int | None = None
    created_at: datetime | None = None


@dataclass(frozen=True)
class Topic:
    """A photo topic chosen by a user."""

    user_id: int
    name: str
    is_free: bool = True
    is_active: bool = True
    id: int | None = None
    created_at: datetime | None = None

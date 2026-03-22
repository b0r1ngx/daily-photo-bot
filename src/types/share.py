"""Topic sharing data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class TopicSubscription:
    """A subscription linking a user to someone else's topic."""

    topic_id: int
    subscriber_user_id: int
    is_active: bool = True
    id: int | None = None
    created_at: datetime | None = None

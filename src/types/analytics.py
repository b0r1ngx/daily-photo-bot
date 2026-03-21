"""Analytics data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AnalyticsSnapshot:
    """A point-in-time snapshot of bot analytics metrics."""

    total_users: int
    users_by_language: dict[str, int]
    active_users: int
    paid_users: int
    pexels_requests_today: int
    unsplash_requests_today: int
    photos_sent_today: int
    generated_at: str

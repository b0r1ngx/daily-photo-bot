"""Schedule configuration data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ScheduleType(StrEnum):
    """Type of schedule."""

    INTERVAL = "interval"
    FIXED_TIME = "fixed_time"


@dataclass(frozen=True)
class ScheduleConfig:
    """Schedule configuration for a topic."""

    topic_id: int
    schedule_type: ScheduleType
    value: str  # seconds for interval, "HH:MM" for fixed_time
    is_active: bool = True
    id: int | None = None
    last_sent_at: str | None = None

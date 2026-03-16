"""Schedule management service. Layer: Service (depends on: types, config)."""
from __future__ import annotations

import logging

from src.config.constants import SCHEDULE_INTERVALS
from src.types.exceptions import BotError
from src.types.protocols import ScheduleRepository
from src.types.schedule import ScheduleConfig, ScheduleType

logger = logging.getLogger(__name__)


class ScheduleService:
    """Manages topic delivery schedules."""

    def __init__(self, schedule_repo: ScheduleRepository) -> None:
        self._repo = schedule_repo

    async def set_interval_schedule(
        self, topic_id: int, seconds: int
    ) -> ScheduleConfig:
        """Set an interval-based schedule for a topic.

        Args:
            topic_id: Database topic ID.
            seconds: Interval in seconds.

        Returns:
            Created/updated ScheduleConfig.

        Raises:
            BotError: If seconds is not a valid interval option.
        """
        valid_seconds = {s for _, s in SCHEDULE_INTERVALS}
        if seconds not in valid_seconds:
            raise BotError(
                f"Invalid interval: {seconds}s. "
                f"Valid options: {sorted(valid_seconds)}"
            )
        return await self._repo.create_or_update(
            topic_id=topic_id,
            schedule_type=ScheduleType.INTERVAL.value,
            value=str(seconds),
        )

    async def set_fixed_time_schedule(
        self, topic_id: int, hour: int, minute: int
    ) -> ScheduleConfig:
        """Set a fixed-time daily schedule for a topic.

        Args:
            topic_id: Database topic ID.
            hour: Hour (0-23).
            minute: Minute (0-59).

        Returns:
            Created/updated ScheduleConfig.

        Raises:
            BotError: If hour/minute is out of range.
        """
        if not (0 <= hour <= 23):
            raise BotError(f"Invalid hour: {hour}. Must be 0-23.")
        if not (0 <= minute <= 59):
            raise BotError(f"Invalid minute: {minute}. Must be 0-59.")

        value = f"{hour:02d}:{minute:02d}"
        return await self._repo.create_or_update(
            topic_id=topic_id,
            schedule_type=ScheduleType.FIXED_TIME.value,
            value=value,
        )

    async def get_schedule(self, topic_id: int) -> ScheduleConfig | None:
        """Get current schedule for a topic."""
        return await self._repo.get_by_topic(topic_id)

    async def get_all_active_schedules(self) -> list[ScheduleConfig]:
        """Get all active schedules (for startup reload)."""
        return await self._repo.get_all_active()

    async def mark_sent(self, schedule_id: int) -> None:
        """Update last_sent_at timestamp after a photo is sent."""
        await self._repo.update_last_sent(schedule_id)

    async def remove_schedule(self, topic_id: int) -> None:
        """Deactivate schedule for a topic."""
        await self._repo.delete_by_topic(topic_id)

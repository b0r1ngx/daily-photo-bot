"""Repository protocol interfaces. Layer: Types (zero dependencies).

Services depend on these protocols, not concrete repo implementations.
This enables dependency injection and easy mocking in tests.
"""
from __future__ import annotations

from typing import Protocol

from src.types.schedule import ScheduleConfig
from src.types.user import MetadataPrefs, Topic, User


class UserRepository(Protocol):
    """Interface for user data access."""

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        ...

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        ...


class TopicRepository(Protocol):
    """Interface for topic data access."""

    async def create(self, user_id: int, name: str, is_free: bool = True) -> Topic:
        ...

    async def get_by_id(self, topic_id: int) -> Topic | None:
        ...

    async def get_by_user(self, user_id: int, active_only: bool = True) -> list[Topic]:
        ...

    async def count_by_user(self, user_id: int) -> int:
        ...

    async def delete(self, topic_id: int) -> None:
        ...

    async def update_name(self, topic_id: int, new_name: str) -> None:
        ...

    async def get_by_id_with_user_language(
        self, topic_id: int,
    ) -> tuple[str, str | None] | None:
        ...

    async def get_owner_telegram_id(self, topic_id: int) -> int | None:
        ...

    async def get_metadata_prefs(self, topic_id: int) -> MetadataPrefs:
        ...

    async def update_metadata_prefs(self, topic_id: int, prefs: MetadataPrefs) -> None:
        ...


class ScheduleRepository(Protocol):
    """Interface for schedule data access."""

    async def create_or_update(
        self, topic_id: int, schedule_type: str, value: str
    ) -> ScheduleConfig:
        ...

    async def get_by_topic(self, topic_id: int) -> ScheduleConfig | None:
        ...

    async def get_all_active(self) -> list[ScheduleConfig]:
        ...

    async def update_last_sent(self, schedule_id: int) -> None:
        ...

    async def delete_by_topic(self, topic_id: int) -> None:
        ...


class SentPhotoRepository(Protocol):
    """Interface for tracking sent photos."""

    async def add(self, topic_id: int, photo_id: str, source: str) -> None:
        ...

    async def exists(self, topic_id: int, photo_id: str, source: str) -> bool:
        ...

    async def count_by_topic(self, topic_id: int) -> int:
        ...

    async def reset_by_topic(self, topic_id: int) -> None:
        ...

    async def get_sent_ids(self, topic_id: int, source: str) -> set[str]:
        ...


class ApiRequestRecorder(Protocol):
    """Interface for recording external API requests (used by PhotoService)."""

    async def record_api_request(self, source: str) -> None:
        ...


class AnalyticsRepository(Protocol):
    """Interface for analytics data access."""

    async def get_total_users(self) -> int:
        ...

    async def get_users_by_language(self) -> dict[str, int]:
        ...

    async def get_active_user_count(self) -> int:
        ...

    async def get_paid_user_count(self) -> int:
        ...

    async def get_photos_sent_since(self, since_dt_text: str) -> int:
        ...

    async def get_api_requests_since(self, source: str, since_dt_text: str) -> int:
        ...

    async def record_api_request(self, source: str) -> None:
        ...

    async def cleanup_old_api_requests(self, older_than_dt_text: str) -> int:
        ...

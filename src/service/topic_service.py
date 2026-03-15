"""Topic management service. Layer: Service (depends on: types, config)."""
from __future__ import annotations

import logging
import re

from src.config.settings import FREE_TOPICS_LIMIT
from src.types.exceptions import TopicLimitError
from src.types.protocols import TopicRepository, UserRepository
from src.types.user import Topic, User

logger = logging.getLogger(__name__)

# Validation: topic name must be 1-50 chars, letters/numbers/spaces/hyphens only
_TOPIC_NAME_PATTERN = re.compile(r"^[\w\s\-]{1,50}$", re.UNICODE)


class TopicService:
    """Manages user topics with free-tier limits."""

    def __init__(self, user_repo: UserRepository, topic_repo: TopicRepository) -> None:
        self._user_repo = user_repo
        self._topic_repo = topic_repo

    async def ensure_user(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        language_code: str | None = None,
    ) -> User:
        """Get or create a user."""
        return await self._user_repo.get_or_create(
            telegram_id, username, first_name, language_code
        )

    async def add_topic(self, user_id: int, name: str, is_free: bool = True) -> Topic:
        """Add a new topic for a user.

        Args:
            user_id: Database user ID.
            name: Topic name (e.g., "parrots").
            is_free: Whether this is a free topic.

        Returns:
            Created Topic.

        Raises:
            TopicLimitError: If user has reached the free topic limit and is_free=True.
            ValueError: If topic name is invalid.
        """
        cleaned = name.strip()
        if not cleaned or not _TOPIC_NAME_PATTERN.match(cleaned):
            raise ValueError(
                f"Invalid topic name: '{name}'. "
                "Use 1-50 characters: letters, numbers, spaces, hyphens."
            )

        if is_free:
            count = await self._topic_repo.count_by_user(user_id)
            if count >= FREE_TOPICS_LIMIT:
                raise TopicLimitError(FREE_TOPICS_LIMIT)

        return await self._topic_repo.create(user_id, cleaned, is_free)

    async def get_topic(self, topic_id: int) -> Topic | None:
        """Get a single active topic by ID."""
        return await self._topic_repo.get_by_id(topic_id)

    async def get_user_topics(self, user_id: int) -> list[Topic]:
        """Get all active topics for a user."""
        return await self._topic_repo.get_by_user(user_id)

    async def get_topic_count(self, user_id: int) -> int:
        """Get count of active topics for a user."""
        return await self._topic_repo.count_by_user(user_id)

    async def can_add_free_topic(self, user_id: int) -> bool:
        """Check if user can add another free topic."""
        count = await self._topic_repo.count_by_user(user_id)
        return count < FREE_TOPICS_LIMIT

    async def remove_topic(self, topic_id: int) -> None:
        """Soft-delete a topic."""
        await self._topic_repo.delete(topic_id)

    async def rename_topic(self, topic_id: int, new_name: str) -> None:
        """Rename an active topic.

        Args:
            topic_id: Database topic ID.
            new_name: New topic name.

        Raises:
            ValueError: If the new name is invalid.
        """
        cleaned = new_name.strip()
        if not cleaned or not _TOPIC_NAME_PATTERN.match(cleaned):
            raise ValueError(
                f"Invalid topic name: '{new_name}'. "
                "Use 1-50 characters: letters, numbers, spaces, hyphens."
            )
        await self._topic_repo.update_name(topic_id, cleaned)

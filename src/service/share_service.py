"""Topic sharing service. Layer: Service (depends on: types, config)."""
from __future__ import annotations

import logging
import secrets

from src.config.settings import BOT_USERNAME, FREE_SHARES_PER_TOPIC
from src.types.exceptions import InvalidShareTokenError, ShareLimitError
from src.types.protocols import ShareRepository, TopicRepository, UserRepository
from src.types.share import TopicSubscription

logger = logging.getLogger(__name__)


class ShareService:
    """Manages topic sharing and subscriptions."""

    def __init__(
        self,
        share_repo: ShareRepository,
        topic_repo: TopicRepository,
        user_repo: UserRepository,
    ) -> None:
        self._share_repo = share_repo
        self._topic_repo = topic_repo
        self._user_repo = user_repo

    async def get_or_create_share_token(self, topic_id: int) -> str:
        """Get existing share token or generate a new one.

        Returns:
            The share token string (without the deep-link prefix).
        """
        existing = await self._share_repo.get_share_token(topic_id)
        if existing:
            return existing
        token = secrets.token_urlsafe(16)
        await self._share_repo.set_share_token(topic_id, token)
        return token

    async def get_share_link(self, topic_id: int, bot_username: str = "") -> str:
        """Generate the full t.me deep link for sharing a topic.

        Args:
            topic_id: Database topic ID.
            bot_username: Bot username override. Uses BOT_USERNAME setting if empty.

        Returns:
            Full deep link URL string.
        """
        token = await self.get_or_create_share_token(topic_id)
        username = bot_username or BOT_USERNAME
        return f"https://t.me/{username}?start=share_{token}"

    async def can_add_subscriber(self, topic_id: int) -> bool:
        """Check if topic has room for another free subscriber."""
        count = await self._share_repo.get_active_subscription_count(topic_id)
        return count < FREE_SHARES_PER_TOPIC

    async def get_subscriber_count(self, topic_id: int) -> int:
        """Get count of active subscribers for a topic."""
        return await self._share_repo.get_active_subscription_count(topic_id)

    async def validate_token(self, token: str) -> int:
        """Validate a share token and return the topic_id.

        Args:
            token: The share token (without the 'share_' prefix).

        Returns:
            The topic_id associated with this token.

        Raises:
            InvalidShareTokenError: If token doesn't match any active topic.
        """
        topic_id = await self._share_repo.get_topic_id_by_share_token(token)
        if topic_id is None:
            raise InvalidShareTokenError(token)
        return topic_id

    async def subscribe(
        self,
        token: str,
        subscriber_telegram_id: int,
    ) -> TopicSubscription:
        """Subscribe a user to a topic via share token.

        Args:
            token: The share token (without 'share_' prefix).
            subscriber_telegram_id: Telegram ID of the subscribing user.

        Returns:
            Created TopicSubscription.

        Raises:
            InvalidShareTokenError: Token doesn't match any active topic.
            ShareLimitError: Free share limit reached.
            ValueError: User tries to subscribe to own topic, or already subscribed.
        """
        topic_id = await self.validate_token(token)

        topic = await self._topic_repo.get_by_id(topic_id)
        if not topic or topic.id is None:
            raise InvalidShareTokenError(token)

        # Get subscriber's DB user
        subscriber = await self._user_repo.get_by_telegram_id(subscriber_telegram_id)
        if not subscriber or subscriber.id is None:
            raise InvalidShareTokenError(token)

        # Can't subscribe to own topic
        if subscriber.id == topic.user_id:
            raise ValueError("Cannot subscribe to your own topic")

        # Check for existing active subscription
        existing = await self._share_repo.get_subscription(topic_id, subscriber.id)
        if existing and existing.is_active:
            raise ValueError("Already subscribed")

        # Check free limit
        can_add = await self.can_add_subscriber(topic_id)
        if not can_add:
            raise ShareLimitError(topic_id)

        subscription = await self._share_repo.create_subscription(
            topic_id, subscriber.id,
        )
        logger.info(
            "User telegram_id=%d subscribed to topic_id=%d",
            subscriber_telegram_id,
            topic_id,
        )
        return subscription

    async def unsubscribe(
        self, topic_id: int, subscriber_telegram_id: int,
    ) -> bool:
        """Unsubscribe a user from a topic.

        Returns True if a subscription was deactivated, False if none existed.
        """
        subscriber = await self._user_repo.get_by_telegram_id(subscriber_telegram_id)
        if not subscriber or subscriber.id is None:
            return False
        return await self._share_repo.deactivate_subscription(topic_id, subscriber.id)

    async def get_subscriber_telegram_ids(self, topic_id: int) -> list[int]:
        """Get all active subscriber Telegram IDs for fan-out."""
        return await self._share_repo.get_subscriber_telegram_ids(topic_id)

    async def remove_subscriber_by_telegram_id(
        self, topic_id: int, telegram_id: int,
    ) -> None:
        """Remove a subscriber when Forbidden is raised during fan-out."""
        subscriber = await self._user_repo.get_by_telegram_id(telegram_id)
        if subscriber and subscriber.id is not None:
            await self._share_repo.deactivate_subscription(topic_id, subscriber.id)
            logger.info(
                "Removed subscription for blocked user telegram_id=%d, topic_id=%d",
                telegram_id,
                topic_id,
            )

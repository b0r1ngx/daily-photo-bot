"""Custom exception hierarchy. Layer: Types (zero dependencies)."""


class BotError(Exception):
    """Base exception for all bot errors."""


class PhotoSourceError(BotError):
    """Error fetching photos from external API."""


class RateLimitError(PhotoSourceError):
    """API rate limit exceeded."""

    def __init__(self, source: str, retry_after: int | None = None) -> None:
        self.source = source
        self.retry_after = retry_after
        msg = f"Rate limit exceeded for {source}"
        if retry_after:
            msg += f" (retry after {retry_after}s)"
        super().__init__(msg)


class PhotoNotFoundError(PhotoSourceError):
    """No photos found for the given topic."""

    def __init__(self, topic: str) -> None:
        self.topic = topic
        super().__init__(f"No photos found for topic: '{topic}'")


class PhotoExhaustedError(PhotoSourceError):
    """All available photos for a topic have been sent."""

    def __init__(self, topic: str, sent_count: int) -> None:
        self.topic = topic
        self.sent_count = sent_count
        super().__init__(f"All photos exhausted for topic '{topic}' ({sent_count} sent)")


class PaymentError(BotError):
    """Error processing Telegram Stars payment."""


class DatabaseError(BotError):
    """Error interacting with SQLite database."""


class TopicLimitError(BotError):
    """User has reached the free topic limit."""

    def __init__(self, limit: int) -> None:
        self.limit = limit
        super().__init__(f"Free topic limit reached ({limit})")


class ShareLimitError(BotError):
    """Free share limit reached for a topic."""

    def __init__(self, topic_id: int) -> None:
        self.topic_id = topic_id
        super().__init__(f"Free share limit reached for topic {topic_id}")


class InvalidShareTokenError(BotError):
    """Share token is invalid or expired."""

    def __init__(self, token: str) -> None:
        self.token = token
        super().__init__(f"Invalid share token: '{token}'")

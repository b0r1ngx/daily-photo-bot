"""Data models layer. Zero dependencies."""
from src.types.exceptions import (
    BotError,
    DatabaseError,
    PaymentError,
    PhotoExhaustedError,
    PhotoNotFoundError,
    PhotoSourceError,
    RateLimitError,
    TopicLimitError,
)
from src.types.payment import PaymentInfo
from src.types.photo import PhotoResult
from src.types.protocols import (
    ScheduleRepository,
    SentPhotoRepository,
    TopicRepository,
    UserRepository,
)
from src.types.schedule import ScheduleConfig, ScheduleType
from src.types.user import Topic, User

__all__ = [
    "BotError",
    "DatabaseError",
    "PaymentError",
    "PaymentInfo",
    "PhotoExhaustedError",
    "PhotoNotFoundError",
    "PhotoResult",
    "PhotoSourceError",
    "RateLimitError",
    "ScheduleConfig",
    "ScheduleRepository",
    "ScheduleType",
    "SentPhotoRepository",
    "Topic",
    "TopicLimitError",
    "TopicRepository",
    "User",
    "UserRepository",
]

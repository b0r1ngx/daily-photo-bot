"""Unit tests for TopicService."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.service.topic_service import TopicService
from src.types.exceptions import TopicLimitError
from src.types.user import Topic, User


@pytest.fixture
def user_repo():
    repo = AsyncMock()
    repo.get_or_create.return_value = User(
        id=1, telegram_id=12345, username="test", first_name="Test"
    )
    return repo


@pytest.fixture
def topic_repo():
    return AsyncMock()


@pytest.fixture
def service(user_repo, topic_repo):
    return TopicService(user_repo=user_repo, topic_repo=topic_repo)


@pytest.mark.asyncio
async def test_ensure_user(service: TopicService, user_repo):
    user = await service.ensure_user(12345, "test", "Test")
    assert user.telegram_id == 12345
    user_repo.get_or_create.assert_awaited_once_with(12345, "test", "Test")


@pytest.mark.asyncio
async def test_add_topic_success(service: TopicService, topic_repo):
    topic_repo.count_by_user.return_value = 0
    topic_repo.create.return_value = Topic(id=1, user_id=1, name="parrots")
    topic = await service.add_topic(user_id=1, name="parrots")
    assert topic.name == "parrots"
    topic_repo.create.assert_awaited_once_with(1, "parrots", True)


@pytest.mark.asyncio
async def test_add_topic_limit_reached(service: TopicService, topic_repo):
    topic_repo.count_by_user.return_value = 1  # FREE_TOPICS_LIMIT is 1
    with pytest.raises(TopicLimitError):
        await service.add_topic(user_id=1, name="mountains")


@pytest.mark.asyncio
async def test_add_topic_invalid_name(service: TopicService):
    with pytest.raises(ValueError, match="Invalid topic name"):
        await service.add_topic(user_id=1, name="")


@pytest.mark.asyncio
async def test_add_topic_paid_bypasses_limit(service: TopicService, topic_repo):
    topic_repo.count_by_user.return_value = 5
    topic_repo.create.return_value = Topic(id=2, user_id=1, name="cars", is_free=False)
    topic = await service.add_topic(user_id=1, name="cars", is_free=False)
    assert topic.name == "cars"


@pytest.mark.asyncio
async def test_can_add_free_topic(service: TopicService, topic_repo):
    topic_repo.count_by_user.return_value = 0
    assert await service.can_add_free_topic(1) is True
    topic_repo.count_by_user.return_value = 1
    assert await service.can_add_free_topic(1) is False


@pytest.mark.asyncio
async def test_rename_topic_success(service: TopicService, topic_repo) -> None:
    """Test renaming a topic with valid name."""
    await service.rename_topic(1, 'new name')
    topic_repo.update_name.assert_called_once_with(1, 'new name')


@pytest.mark.asyncio
async def test_rename_topic_invalid_name(service: TopicService) -> None:
    """Test renaming with invalid name raises ValueError."""
    with pytest.raises(ValueError):
        await service.rename_topic(1, '')

    with pytest.raises(ValueError):
        await service.rename_topic(1, 'a' * 51)

    with pytest.raises(ValueError):
        await service.rename_topic(1, '!!!')

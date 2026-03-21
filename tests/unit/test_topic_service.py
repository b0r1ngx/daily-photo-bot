"""Unit tests for TopicService."""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.service.topic_service import TopicService
from src.types.exceptions import TopicLimitError
from src.types.user import MetadataPrefs, Topic, User


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
    user_repo.get_or_create.assert_awaited_once_with(12345, "test", "Test", None)


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
    await service.rename_topic(1, "new name")
    topic_repo.update_name.assert_awaited_once_with(1, "new name")


@pytest.mark.asyncio
async def test_rename_topic_invalid_name(service: TopicService) -> None:
    """Test renaming with invalid name raises ValueError."""
    with pytest.raises(ValueError):
        await service.rename_topic(1, "")

    with pytest.raises(ValueError):
        await service.rename_topic(1, "a" * 51)

    with pytest.raises(ValueError):
        await service.rename_topic(1, "!!!")


@pytest.mark.asyncio
async def test_get_topic_with_language(service: TopicService, topic_repo) -> None:
    """get_topic_with_language delegates to repo.get_by_id_with_user_language."""
    topic_repo.get_by_id_with_user_language.return_value = ("parrots", "en")
    result = await service.get_topic_with_language(42)
    assert result == ("parrots", "en")
    topic_repo.get_by_id_with_user_language.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_get_owner_telegram_id(service: TopicService, topic_repo) -> None:
    """get_owner_telegram_id delegates to repo.get_owner_telegram_id."""
    topic_repo.get_owner_telegram_id.return_value = 12345
    result = await service.get_owner_telegram_id(42)
    assert result == 12345
    topic_repo.get_owner_telegram_id.assert_awaited_once_with(42)


@pytest.mark.asyncio
async def test_get_metadata_prefs_default(service: TopicService, topic_repo) -> None:
    """get_metadata_prefs returns defaults from repo."""
    topic_repo.get_metadata_prefs.return_value = MetadataPrefs()
    result = await service.get_metadata_prefs(1)
    assert result.show_description is True
    assert result.show_location is True
    assert result.show_camera is True
    topic_repo.get_metadata_prefs.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_update_metadata_prefs(service: TopicService, topic_repo) -> None:
    """update_metadata_prefs delegates to repo."""
    prefs = MetadataPrefs(show_description=False, show_location=True, show_camera=False)
    await service.update_metadata_prefs(1, prefs)
    topic_repo.update_metadata_prefs.assert_awaited_once_with(1, prefs)


@pytest.mark.asyncio
async def test_toggle_metadata_field(service: TopicService, topic_repo) -> None:
    """toggle_metadata_field toggles a single field and saves."""
    topic_repo.get_metadata_prefs.return_value = MetadataPrefs(
        show_description=True, show_location=True, show_camera=True,
    )
    result = await service.toggle_metadata_field(1, "description")
    assert result.show_description is False
    assert result.show_location is True
    assert result.show_camera is True
    topic_repo.update_metadata_prefs.assert_awaited_once()


@pytest.mark.asyncio
async def test_toggle_metadata_field_invalid(service: TopicService) -> None:
    """toggle_metadata_field raises ValueError for invalid field."""
    with pytest.raises(ValueError, match="Invalid metadata field"):
        await service.toggle_metadata_field(1, "invalid_field")

"""Integration tests for TopicRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.topic_repo import TopicRepo
from src.repo.user_repo import UserRepo
from src.types.user import MetadataPrefs


@pytest.fixture
async def db():
    conn = await get_connection(":memory:")
    await init_db(conn)
    yield conn
    await conn.close()


@pytest.fixture
async def user_repo(db: aiosqlite.Connection):
    return UserRepo(db)


@pytest.fixture
async def topic_repo(db: aiosqlite.Connection):
    return TopicRepo(db)


@pytest.fixture
async def user_id(user_repo: UserRepo):
    user = await user_repo.get_or_create(telegram_id=12345)
    return user.id


@pytest.mark.asyncio
async def test_create_topic(topic_repo: TopicRepo, user_id: int):
    topic = await topic_repo.create(user_id=user_id, name="parrots")
    assert topic.name == "parrots"
    assert topic.user_id == user_id
    assert topic.is_free is True
    assert topic.is_active is True
    assert topic.id is not None


@pytest.mark.asyncio
async def test_get_by_user(topic_repo: TopicRepo, user_id: int):
    await topic_repo.create(user_id=user_id, name="parrots")
    await topic_repo.create(user_id=user_id, name="mountains")
    topics = await topic_repo.get_by_user(user_id)
    assert len(topics) == 2
    names = {t.name for t in topics}
    assert names == {"parrots", "mountains"}


@pytest.mark.asyncio
async def test_count_by_user(topic_repo: TopicRepo, user_id: int):
    assert await topic_repo.count_by_user(user_id) == 0
    await topic_repo.create(user_id=user_id, name="parrots")
    assert await topic_repo.count_by_user(user_id) == 1


@pytest.mark.asyncio
async def test_delete_topic(topic_repo: TopicRepo, user_id: int):
    topic = await topic_repo.create(user_id=user_id, name="parrots")
    await topic_repo.delete(topic.id)  # type: ignore[arg-type]
    topics = await topic_repo.get_by_user(user_id)
    assert len(topics) == 0


@pytest.mark.asyncio
async def test_delete_shows_in_all(topic_repo: TopicRepo, user_id: int):
    topic = await topic_repo.create(user_id=user_id, name="parrots")
    await topic_repo.delete(topic.id)  # type: ignore[arg-type]
    all_topics = await topic_repo.get_by_user(user_id, active_only=False)
    assert len(all_topics) == 1
    assert all_topics[0].is_active is False


@pytest.mark.asyncio
async def test_update_name(topic_repo: TopicRepo, user_id: int) -> None:
    """Test renaming a topic."""
    topic = await topic_repo.create(user_id=user_id, name='old name', is_free=True)
    assert topic.id is not None
    await topic_repo.update_name(topic.id, 'new name')
    topics = await topic_repo.get_by_user(user_id)
    assert topics[0].name == 'new name'


@pytest.mark.asyncio
async def test_update_name_deleted_topic(topic_repo: TopicRepo, user_id: int) -> None:
    """Renaming a soft-deleted topic should raise ValueError."""
    topic = await topic_repo.create(user_id=user_id, name='doomed', is_free=True)
    assert topic.id is not None
    await topic_repo.delete(topic.id)
    with pytest.raises(ValueError):
        await topic_repo.update_name(topic.id, 'new name')


@pytest.mark.asyncio
async def test_get_by_id(topic_repo: TopicRepo, user_id: int) -> None:
    """Test fetching a topic by its ID."""
    topic = await topic_repo.create(user_id=user_id, name='findme', is_free=True)
    assert topic.id is not None
    found = await topic_repo.get_by_id(topic.id)
    assert found is not None
    assert found.name == 'findme'


@pytest.mark.asyncio
async def test_get_by_id_not_found(topic_repo: TopicRepo) -> None:
    """get_by_id returns None for non-existent topic."""
    found = await topic_repo.get_by_id(99999)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_deleted(topic_repo: TopicRepo, user_id: int) -> None:
    """get_by_id returns None for soft-deleted topic."""
    topic = await topic_repo.create(user_id=user_id, name='deleted', is_free=True)
    assert topic.id is not None
    await topic_repo.delete(topic.id)
    found = await topic_repo.get_by_id(topic.id)
    assert found is None


@pytest.mark.asyncio
async def test_get_by_id_with_user_language(
    topic_repo: TopicRepo, user_repo: UserRepo,
) -> None:
    """get_by_id_with_user_language returns (name, language_code) for active topic."""
    user = await user_repo.get_or_create(
        telegram_id=99001, language_code="en",
    )
    assert user.id is not None
    topic = await topic_repo.create(user_id=user.id, name="parrots")
    assert topic.id is not None

    result = await topic_repo.get_by_id_with_user_language(topic.id)
    assert result is not None
    assert result == ("parrots", "en")


@pytest.mark.asyncio
async def test_get_by_id_with_user_language_inactive(
    topic_repo: TopicRepo, user_repo: UserRepo,
) -> None:
    """get_by_id_with_user_language returns None for inactive topic."""
    user = await user_repo.get_or_create(
        telegram_id=99002, language_code="ru",
    )
    assert user.id is not None
    topic = await topic_repo.create(user_id=user.id, name="mountains")
    assert topic.id is not None
    await topic_repo.delete(topic.id)

    result = await topic_repo.get_by_id_with_user_language(topic.id)
    assert result is None


@pytest.mark.asyncio
async def test_get_owner_telegram_id(
    topic_repo: TopicRepo, user_repo: UserRepo,
) -> None:
    """get_owner_telegram_id returns the telegram_id of the topic owner."""
    user = await user_repo.get_or_create(telegram_id=99003)
    assert user.id is not None
    topic = await topic_repo.create(user_id=user.id, name="cats")
    assert topic.id is not None

    telegram_id = await topic_repo.get_owner_telegram_id(topic.id)
    assert telegram_id == 99003


@pytest.mark.asyncio
async def test_get_owner_telegram_id_not_found(topic_repo: TopicRepo) -> None:
    """get_owner_telegram_id returns None for nonexistent topic."""
    result = await topic_repo.get_owner_telegram_id(99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_metadata_prefs_null_returns_defaults(
    topic_repo: TopicRepo, user_id: int,
) -> None:
    """get_metadata_prefs returns all-True defaults when column is NULL."""
    topic = await topic_repo.create(user_id=user_id, name="parrots")
    assert topic.id is not None
    prefs = await topic_repo.get_metadata_prefs(topic.id)
    assert prefs == MetadataPrefs()
    assert prefs.show_description is True
    assert prefs.show_location is True
    assert prefs.show_camera is True


@pytest.mark.asyncio
async def test_update_and_get_metadata_prefs(
    topic_repo: TopicRepo, user_id: int,
) -> None:
    """update_metadata_prefs persists and get_metadata_prefs retrieves."""
    topic = await topic_repo.create(user_id=user_id, name="mountains")
    assert topic.id is not None

    new_prefs = MetadataPrefs(show_description=False, show_location=True, show_camera=False)
    await topic_repo.update_metadata_prefs(topic.id, new_prefs)

    loaded = await topic_repo.get_metadata_prefs(topic.id)
    assert loaded.show_description is False
    assert loaded.show_location is True
    assert loaded.show_camera is False


@pytest.mark.asyncio
async def test_update_metadata_prefs_nonexistent_topic(
    topic_repo: TopicRepo,
) -> None:
    """update_metadata_prefs raises ValueError for nonexistent topic."""
    with pytest.raises(ValueError, match="not found or inactive"):
        await topic_repo.update_metadata_prefs(99999, MetadataPrefs())


@pytest.mark.asyncio
async def test_update_metadata_prefs_deleted_topic(
    topic_repo: TopicRepo, user_id: int,
) -> None:
    """update_metadata_prefs raises ValueError for soft-deleted topic."""
    topic = await topic_repo.create(user_id=user_id, name="doomed", is_free=True)
    assert topic.id is not None
    await topic_repo.delete(topic.id)
    with pytest.raises(ValueError, match="not found or inactive"):
        await topic_repo.update_metadata_prefs(topic.id, MetadataPrefs())


@pytest.mark.asyncio
async def test_metadata_prefs_not_found_returns_defaults(
    topic_repo: TopicRepo,
) -> None:
    """get_metadata_prefs returns defaults for nonexistent topic."""
    prefs = await topic_repo.get_metadata_prefs(99999)
    assert prefs == MetadataPrefs()

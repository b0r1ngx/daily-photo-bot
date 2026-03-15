"""Integration tests for TopicRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.topic_repo import TopicRepo
from src.repo.user_repo import UserRepo


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

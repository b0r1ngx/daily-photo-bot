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

"""Integration tests for SentPhotoRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.sent_photo_repo import SentPhotoRepo
from src.repo.topic_repo import TopicRepo
from src.repo.user_repo import UserRepo


@pytest.fixture
async def db():
    conn = await get_connection(":memory:")
    await init_db(conn)
    yield conn
    await conn.close()


@pytest.fixture
async def sent_repo(db: aiosqlite.Connection):
    return SentPhotoRepo(db)


@pytest.fixture
async def topic_id(db: aiosqlite.Connection):
    user_repo = UserRepo(db)
    topic_repo = TopicRepo(db)
    user = await user_repo.get_or_create(telegram_id=12345)
    topic = await topic_repo.create(user_id=user.id, name="parrots")  # type: ignore[arg-type]
    return topic.id


@pytest.mark.asyncio
async def test_add_and_exists(sent_repo: SentPhotoRepo, topic_id: int):
    await sent_repo.add(topic_id=topic_id, photo_id="px_123", source="pexels")
    assert await sent_repo.exists(topic_id, "px_123", "pexels") is True
    assert await sent_repo.exists(topic_id, "px_999", "pexels") is False


@pytest.mark.asyncio
async def test_add_duplicate_ignored(sent_repo: SentPhotoRepo, topic_id: int):
    await sent_repo.add(topic_id=topic_id, photo_id="px_123", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="px_123", source="pexels")  # no error
    count = await sent_repo.count_by_topic(topic_id)
    assert count == 1


@pytest.mark.asyncio
async def test_same_id_different_source(sent_repo: SentPhotoRepo, topic_id: int):
    await sent_repo.add(topic_id=topic_id, photo_id="123", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="123", source="unsplash")
    count = await sent_repo.count_by_topic(topic_id)
    assert count == 2


@pytest.mark.asyncio
async def test_count_by_topic(sent_repo: SentPhotoRepo, topic_id: int):
    assert await sent_repo.count_by_topic(topic_id) == 0
    await sent_repo.add(topic_id=topic_id, photo_id="px_1", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="px_2", source="pexels")
    assert await sent_repo.count_by_topic(topic_id) == 2


@pytest.mark.asyncio
async def test_reset_by_topic(sent_repo: SentPhotoRepo, topic_id: int):
    await sent_repo.add(topic_id=topic_id, photo_id="px_1", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="px_2", source="pexels")
    await sent_repo.reset_by_topic(topic_id)
    assert await sent_repo.count_by_topic(topic_id) == 0


@pytest.mark.asyncio
async def test_get_sent_ids(sent_repo: SentPhotoRepo, topic_id: int):
    await sent_repo.add(topic_id=topic_id, photo_id="px_1", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="px_2", source="pexels")
    await sent_repo.add(topic_id=topic_id, photo_id="un_1", source="unsplash")
    pexels_ids = await sent_repo.get_sent_ids(topic_id, "pexels")
    assert pexels_ids == {"px_1", "px_2"}
    unsplash_ids = await sent_repo.get_sent_ids(topic_id, "unsplash")
    assert unsplash_ids == {"un_1"}

"""Integration tests for ScheduleRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.schedule_repo import ScheduleRepo
from src.repo.topic_repo import TopicRepo
from src.repo.user_repo import UserRepo
from src.types.schedule import ScheduleType


@pytest.fixture
async def db():
    conn = await get_connection(":memory:")
    await init_db(conn)
    yield conn
    await conn.close()


@pytest.fixture
async def schedule_repo(db: aiosqlite.Connection):
    return ScheduleRepo(db)


@pytest.fixture
async def topic_id(db: aiosqlite.Connection):
    user_repo = UserRepo(db)
    topic_repo = TopicRepo(db)
    user = await user_repo.get_or_create(telegram_id=12345)
    topic = await topic_repo.create(user_id=user.id, name="parrots")  # type: ignore[arg-type]
    return topic.id


@pytest.mark.asyncio
async def test_create_schedule(schedule_repo: ScheduleRepo, topic_id: int):
    schedule = await schedule_repo.create_or_update(
        topic_id=topic_id, schedule_type="interval", value="3600"
    )
    assert schedule.topic_id == topic_id
    assert schedule.schedule_type == ScheduleType.INTERVAL
    assert schedule.value == "3600"
    assert schedule.is_active is True


@pytest.mark.asyncio
async def test_update_schedule(schedule_repo: ScheduleRepo, topic_id: int):
    await schedule_repo.create_or_update(topic_id=topic_id, schedule_type="interval", value="3600")
    updated = await schedule_repo.create_or_update(
        topic_id=topic_id, schedule_type="fixed_time", value="09:30"
    )
    assert updated.schedule_type == ScheduleType.FIXED_TIME
    assert updated.value == "09:30"


@pytest.mark.asyncio
async def test_get_all_active(schedule_repo: ScheduleRepo, topic_id: int):
    await schedule_repo.create_or_update(topic_id=topic_id, schedule_type="interval", value="300")
    active = await schedule_repo.get_all_active()
    assert len(active) == 1
    assert active[0].topic_id == topic_id


@pytest.mark.asyncio
async def test_delete_by_topic(schedule_repo: ScheduleRepo, topic_id: int):
    await schedule_repo.create_or_update(topic_id=topic_id, schedule_type="interval", value="300")
    await schedule_repo.delete_by_topic(topic_id)
    active = await schedule_repo.get_all_active()
    assert len(active) == 0


@pytest.mark.asyncio
async def test_update_last_sent(schedule_repo: ScheduleRepo, topic_id: int):
    schedule = await schedule_repo.create_or_update(
        topic_id=topic_id, schedule_type="interval", value="300"
    )
    assert schedule.last_sent_at is None
    await schedule_repo.update_last_sent(schedule.id)  # type: ignore[arg-type]
    updated = await schedule_repo.get_by_topic(topic_id)
    assert updated is not None
    assert updated.last_sent_at is not None

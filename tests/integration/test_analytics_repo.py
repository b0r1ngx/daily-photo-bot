"""Integration tests for AnalyticsRepo using in-memory SQLite."""
from __future__ import annotations

import aiosqlite
import pytest

from src.repo.analytics_repo import AnalyticsRepo
from src.repo.database import get_connection, init_db


@pytest.fixture
async def db():
    conn = await get_connection(":memory:")
    await init_db(conn)
    yield conn
    await conn.close()


@pytest.fixture
async def repo(db: aiosqlite.Connection):
    return AnalyticsRepo(db)


# --- Helper to insert test data ---


async def _insert_user(
    db: aiosqlite.Connection,
    telegram_id: int,
    language_code: str | None = None,
) -> int:
    cursor = await db.execute(
        "INSERT INTO users (telegram_id, language_code) VALUES (?, ?)",
        (telegram_id, language_code),
    )
    await db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


async def _insert_topic(
    db: aiosqlite.Connection,
    user_id: int,
    name: str = "test",
    is_free: bool = True,
    is_active: bool = True,
) -> int:
    cursor = await db.execute(
        "INSERT INTO topics (user_id, name, is_free, is_active) VALUES (?, ?, ?, ?)",
        (user_id, name, int(is_free), int(is_active)),
    )
    await db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


async def _insert_schedule(
    db: aiosqlite.Connection,
    topic_id: int,
    is_active: bool = True,
) -> int:
    cursor = await db.execute(
        "INSERT INTO schedules (topic_id, schedule_type, value, is_active) "
        "VALUES (?, 'interval', '3600', ?)",
        (topic_id, int(is_active)),
    )
    await db.commit()
    return cursor.lastrowid  # type: ignore[return-value]


async def _insert_sent_photo(
    db: aiosqlite.Connection,
    topic_id: int,
    photo_id: str,
    source: str = "pexels",
    sent_at: str | None = None,
) -> None:
    if sent_at:
        await db.execute(
            "INSERT INTO sent_photos (topic_id, photo_id, source, sent_at) "
            "VALUES (?, ?, ?, ?)",
            (topic_id, photo_id, source, sent_at),
        )
    else:
        await db.execute(
            "INSERT INTO sent_photos (topic_id, photo_id, source) VALUES (?, ?, ?)",
            (topic_id, photo_id, source),
        )
    await db.commit()


# --- Tests ---


@pytest.mark.asyncio
async def test_get_total_users_empty(repo: AnalyticsRepo):
    assert await repo.get_total_users() == 0


@pytest.mark.asyncio
async def test_get_total_users_with_data(repo: AnalyticsRepo, db: aiosqlite.Connection):
    await _insert_user(db, 100)
    await _insert_user(db, 200)
    await _insert_user(db, 300)
    assert await repo.get_total_users() == 3


@pytest.mark.asyncio
async def test_get_users_by_language(repo: AnalyticsRepo, db: aiosqlite.Connection):
    await _insert_user(db, 100, "en")
    await _insert_user(db, 200, "en")
    await _insert_user(db, 300, "ru")
    result = await repo.get_users_by_language()
    assert result == {"en": 2, "ru": 1}


@pytest.mark.asyncio
async def test_get_users_by_language_null_handling(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    await _insert_user(db, 100, "en")
    await _insert_user(db, 200, None)
    result = await repo.get_users_by_language()
    assert result["en"] == 1
    assert result["unknown"] == 1


@pytest.mark.asyncio
async def test_get_active_user_count_no_schedules(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    user_id = await _insert_user(db, 100)
    await _insert_topic(db, user_id)
    assert await repo.get_active_user_count() == 0


@pytest.mark.asyncio
async def test_get_active_user_count_with_active_schedule(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    user_id = await _insert_user(db, 100)
    topic_id = await _insert_topic(db, user_id)
    await _insert_schedule(db, topic_id, is_active=True)
    assert await repo.get_active_user_count() == 1


@pytest.mark.asyncio
async def test_get_active_user_count_inactive_schedule_excluded(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    user_id = await _insert_user(db, 100)
    topic_id = await _insert_topic(db, user_id)
    await _insert_schedule(db, topic_id, is_active=False)
    assert await repo.get_active_user_count() == 0


@pytest.mark.asyncio
async def test_get_active_user_count_inactive_topic_excluded(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    user_id = await _insert_user(db, 100)
    topic_id = await _insert_topic(db, user_id, is_active=False)
    await _insert_schedule(db, topic_id, is_active=True)
    assert await repo.get_active_user_count() == 0


@pytest.mark.asyncio
async def test_get_active_user_count_deduped(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    """A user with 2 active schedules should be counted once."""
    user_id = await _insert_user(db, 100)
    t1 = await _insert_topic(db, user_id, name="topic1")
    t2 = await _insert_topic(db, user_id, name="topic2")
    await _insert_schedule(db, t1, is_active=True)
    await _insert_schedule(db, t2, is_active=True)
    assert await repo.get_active_user_count() == 1


@pytest.mark.asyncio
async def test_get_paid_user_count_no_paid(repo: AnalyticsRepo, db: aiosqlite.Connection):
    user_id = await _insert_user(db, 100)
    await _insert_topic(db, user_id, is_free=True)
    assert await repo.get_paid_user_count() == 0


@pytest.mark.asyncio
async def test_get_paid_user_count_with_paid_topics(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    user_id = await _insert_user(db, 100)
    await _insert_topic(db, user_id, is_free=False)
    await _insert_topic(db, user_id, name="t2", is_free=False)
    assert await repo.get_paid_user_count() == 1  # deduped by user


@pytest.mark.asyncio
async def test_get_paid_user_count_excludes_inactive_topics(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    """Soft-deleted paid topics should not be counted."""
    user_id = await _insert_user(db, 100)
    await _insert_topic(db, user_id, is_free=False, is_active=False)
    assert await repo.get_paid_user_count() == 0


@pytest.mark.asyncio
async def test_get_paid_user_count_mixed_active_inactive(
    repo: AnalyticsRepo, db: aiosqlite.Connection,
):
    """User with one active and one inactive paid topic is counted once."""
    user_id = await _insert_user(db, 100)
    await _insert_topic(db, user_id, name="active_paid", is_free=False, is_active=True)
    await _insert_topic(db, user_id, name="deleted_paid", is_free=False, is_active=False)
    assert await repo.get_paid_user_count() == 1


@pytest.mark.asyncio
async def test_get_photos_sent_since(repo: AnalyticsRepo, db: aiosqlite.Connection):
    user_id = await _insert_user(db, 100)
    topic_id = await _insert_topic(db, user_id)
    # Recent photo
    await _insert_sent_photo(db, topic_id, "p1")
    # Old photo
    await _insert_sent_photo(db, topic_id, "p2", sent_at="2020-01-01 00:00:00")
    count = await repo.get_photos_sent_since("2025-01-01 00:00:00")
    assert count == 1


@pytest.mark.asyncio
async def test_record_api_request(repo: AnalyticsRepo):
    await repo.record_api_request("pexels")
    count = await repo.get_api_requests_since("pexels", "2020-01-01 00:00:00")
    assert count == 1


@pytest.mark.asyncio
async def test_get_api_requests_since_filters_by_source(repo: AnalyticsRepo):
    await repo.record_api_request("pexels")
    await repo.record_api_request("pexels")
    await repo.record_api_request("unsplash")
    assert await repo.get_api_requests_since("pexels", "2020-01-01") == 2
    assert await repo.get_api_requests_since("unsplash", "2020-01-01") == 1


@pytest.mark.asyncio
async def test_cleanup_old_api_requests(repo: AnalyticsRepo, db: aiosqlite.Connection):
    # Insert an old request manually
    await db.execute(
        "INSERT INTO api_requests (source, requested_at) VALUES (?, ?)",
        ("pexels", "2020-01-01 00:00:00"),
    )
    await db.commit()
    # Insert a recent request
    await repo.record_api_request("pexels")

    deleted = await repo.cleanup_old_api_requests("2025-01-01 00:00:00")
    assert deleted == 1
    # Only the recent request remains
    remaining = await repo.get_api_requests_since("pexels", "2020-01-01")
    assert remaining == 1

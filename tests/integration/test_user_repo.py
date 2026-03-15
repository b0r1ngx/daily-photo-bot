"""Integration tests for UserRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.user_repo import UserRepo


@pytest.fixture
async def db():
    conn = await get_connection(":memory:")
    await init_db(conn)
    yield conn
    await conn.close()


@pytest.fixture
async def repo(db: aiosqlite.Connection):
    return UserRepo(db)


@pytest.mark.asyncio
async def test_get_or_create_new_user(repo: UserRepo):
    user = await repo.get_or_create(telegram_id=12345, username="testuser", first_name="Test")
    assert user.telegram_id == 12345
    assert user.username == "testuser"
    assert user.first_name == "Test"
    assert user.id is not None


@pytest.mark.asyncio
async def test_get_or_create_existing_user(repo: UserRepo):
    user1 = await repo.get_or_create(telegram_id=12345, username="testuser")
    user2 = await repo.get_or_create(telegram_id=12345, username="testuser")
    assert user1.id == user2.id
    assert user1.telegram_id == user2.telegram_id


@pytest.mark.asyncio
async def test_get_by_telegram_id_not_found(repo: UserRepo):
    result = await repo.get_by_telegram_id(99999)
    assert result is None


@pytest.mark.asyncio
async def test_get_by_telegram_id_found(repo: UserRepo):
    await repo.get_or_create(telegram_id=12345, username="testuser")
    result = await repo.get_by_telegram_id(12345)
    assert result is not None
    assert result.telegram_id == 12345

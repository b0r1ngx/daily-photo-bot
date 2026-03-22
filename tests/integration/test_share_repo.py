"""Integration tests for ShareRepo using in-memory SQLite."""
import aiosqlite
import pytest

from src.repo.database import get_connection, init_db
from src.repo.share_repo import ShareRepo
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
async def share_repo(db: aiosqlite.Connection):
    return ShareRepo(db)


@pytest.fixture
async def owner_id(user_repo: UserRepo):
    user = await user_repo.get_or_create(telegram_id=11111)
    return user.id


@pytest.fixture
async def subscriber_id(user_repo: UserRepo):
    user = await user_repo.get_or_create(telegram_id=22222)
    return user.id


@pytest.fixture
async def topic_id(topic_repo: TopicRepo, owner_id: int):
    topic = await topic_repo.create(user_id=owner_id, name="parrots")
    return topic.id


# ---------------------------------------------------------------------------
# Share token tests
# ---------------------------------------------------------------------------


async def test_get_share_token_none_by_default(
    share_repo: ShareRepo, topic_id: int,
):
    """A fresh topic has no share token."""
    token = await share_repo.get_share_token(topic_id)
    assert token is None


async def test_set_and_get_share_token(
    share_repo: ShareRepo, topic_id: int,
):
    """Setting a token makes it retrievable."""
    await share_repo.set_share_token(topic_id, "abc123")
    token = await share_repo.get_share_token(topic_id)
    assert token == "abc123"


async def test_set_share_token_nonexistent_topic(share_repo: ShareRepo):
    """Setting token on nonexistent topic raises ValueError."""
    with pytest.raises(ValueError, match="not found or inactive"):
        await share_repo.set_share_token(99999, "token")


async def test_set_share_token_inactive_topic(
    share_repo: ShareRepo, topic_repo: TopicRepo, topic_id: int,
):
    """Setting token on deleted topic raises ValueError."""
    await topic_repo.delete(topic_id)
    with pytest.raises(ValueError, match="not found or inactive"):
        await share_repo.set_share_token(topic_id, "token")


async def test_get_topic_id_by_share_token(
    share_repo: ShareRepo, topic_id: int,
):
    """Looking up topic by token returns the correct topic_id."""
    await share_repo.set_share_token(topic_id, "mytoken")
    result = await share_repo.get_topic_id_by_share_token("mytoken")
    assert result == topic_id


async def test_get_topic_id_by_share_token_not_found(share_repo: ShareRepo):
    """Looking up non-existent token returns None."""
    result = await share_repo.get_topic_id_by_share_token("nonexistent")
    assert result is None


async def test_get_topic_id_by_share_token_inactive_topic(
    share_repo: ShareRepo, topic_repo: TopicRepo, topic_id: int,
):
    """Token lookup returns None if topic is soft-deleted."""
    await share_repo.set_share_token(topic_id, "mytoken")
    await topic_repo.delete(topic_id)
    result = await share_repo.get_topic_id_by_share_token("mytoken")
    assert result is None


# ---------------------------------------------------------------------------
# Subscription CRUD tests
# ---------------------------------------------------------------------------


async def test_create_subscription(
    share_repo: ShareRepo, topic_id: int, subscriber_id: int,
):
    """Creating a subscription returns a valid TopicSubscription."""
    sub = await share_repo.create_subscription(topic_id, subscriber_id)
    assert sub.topic_id == topic_id
    assert sub.subscriber_user_id == subscriber_id
    assert sub.is_active is True
    assert sub.id is not None


async def test_get_subscription(
    share_repo: ShareRepo, topic_id: int, subscriber_id: int,
):
    """get_subscription returns the created subscription."""
    await share_repo.create_subscription(topic_id, subscriber_id)
    sub = await share_repo.get_subscription(topic_id, subscriber_id)
    assert sub is not None
    assert sub.is_active is True


async def test_get_subscription_not_found(
    share_repo: ShareRepo, topic_id: int,
):
    """get_subscription returns None if no subscription exists."""
    sub = await share_repo.get_subscription(topic_id, 99999)
    assert sub is None


async def test_deactivate_subscription(
    share_repo: ShareRepo, topic_id: int, subscriber_id: int,
):
    """Deactivating a subscription soft-deletes it."""
    await share_repo.create_subscription(topic_id, subscriber_id)
    result = await share_repo.deactivate_subscription(topic_id, subscriber_id)
    assert result is True
    sub = await share_repo.get_subscription(topic_id, subscriber_id)
    assert sub is not None
    assert sub.is_active is False


async def test_deactivate_nonexistent_subscription(
    share_repo: ShareRepo, topic_id: int,
):
    """Deactivating nonexistent subscription returns False."""
    result = await share_repo.deactivate_subscription(topic_id, 99999)
    assert result is False


async def test_reactivate_subscription(
    share_repo: ShareRepo, topic_id: int, subscriber_id: int,
):
    """Creating after deactivation reactivates the existing row."""
    sub1 = await share_repo.create_subscription(topic_id, subscriber_id)
    await share_repo.deactivate_subscription(topic_id, subscriber_id)
    sub2 = await share_repo.create_subscription(topic_id, subscriber_id)
    assert sub2.is_active is True
    assert sub2.id == sub1.id  # Same row reactivated


async def test_get_active_subscription_count(
    share_repo: ShareRepo,
    topic_id: int,
    subscriber_id: int,
    user_repo: UserRepo,
):
    """Count only counts active subscriptions."""
    assert await share_repo.get_active_subscription_count(topic_id) == 0
    await share_repo.create_subscription(topic_id, subscriber_id)
    assert await share_repo.get_active_subscription_count(topic_id) == 1

    # Add another subscriber
    user2 = await user_repo.get_or_create(telegram_id=33333)
    await share_repo.create_subscription(topic_id, user2.id)
    assert await share_repo.get_active_subscription_count(topic_id) == 2

    # Deactivate one
    await share_repo.deactivate_subscription(topic_id, subscriber_id)
    assert await share_repo.get_active_subscription_count(topic_id) == 1


async def test_get_subscriber_telegram_ids(
    share_repo: ShareRepo,
    topic_id: int,
    subscriber_id: int,
    user_repo: UserRepo,
):
    """get_subscriber_telegram_ids returns only active subscriber telegram IDs."""
    await share_repo.create_subscription(topic_id, subscriber_id)

    user2 = await user_repo.get_or_create(telegram_id=33333)
    await share_repo.create_subscription(topic_id, user2.id)

    ids = await share_repo.get_subscriber_telegram_ids(topic_id)
    assert set(ids) == {22222, 33333}


async def test_get_subscriber_telegram_ids_excludes_inactive(
    share_repo: ShareRepo, topic_id: int, subscriber_id: int,
):
    """Deactivated subscribers are excluded from fan-out list."""
    await share_repo.create_subscription(topic_id, subscriber_id)
    await share_repo.deactivate_subscription(topic_id, subscriber_id)
    ids = await share_repo.get_subscriber_telegram_ids(topic_id)
    assert ids == []


async def test_get_subscriber_telegram_ids_empty(
    share_repo: ShareRepo, topic_id: int,
):
    """No subscribers returns empty list."""
    ids = await share_repo.get_subscriber_telegram_ids(topic_id)
    assert ids == []

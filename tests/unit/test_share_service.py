"""Unit tests for ShareService."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.service.share_service import ShareService
from src.types.exceptions import InvalidShareTokenError, ShareLimitError
from src.types.share import TopicSubscription
from src.types.user import Topic, User


@pytest.fixture
def share_repo():
    return AsyncMock()


@pytest.fixture
def topic_repo():
    return AsyncMock()


@pytest.fixture
def user_repo():
    return AsyncMock()


@pytest.fixture
def service(share_repo, topic_repo, user_repo):
    return ShareService(
        share_repo=share_repo, topic_repo=topic_repo, user_repo=user_repo,
    )


# ---------------------------------------------------------------------------
# get_or_create_share_token
# ---------------------------------------------------------------------------


async def test_get_or_create_share_token_existing(
    service: ShareService, share_repo,
):
    """Returns existing token if one already exists."""
    share_repo.get_share_token.return_value = "existing_token"
    token = await service.get_or_create_share_token(1)
    assert token == "existing_token"
    share_repo.set_share_token.assert_not_awaited()


async def test_get_or_create_share_token_generates_new(
    service: ShareService, share_repo,
):
    """Generates new token when none exists."""
    share_repo.get_share_token.return_value = None
    token = await service.get_or_create_share_token(1)
    assert len(token) > 0
    share_repo.set_share_token.assert_awaited_once_with(1, token)


# ---------------------------------------------------------------------------
# get_share_link
# ---------------------------------------------------------------------------


async def test_get_share_link(service: ShareService, share_repo):
    """Returns a deep link URL with the correct format."""
    share_repo.get_share_token.return_value = "mytoken"
    link = await service.get_share_link(1, "testbot")
    assert link == "https://t.me/testbot?start=share_mytoken"


# ---------------------------------------------------------------------------
# can_add_subscriber / get_subscriber_count
# ---------------------------------------------------------------------------


async def test_can_add_subscriber_true(service: ShareService, share_repo):
    """Returns True when under the free limit."""
    share_repo.get_active_subscription_count.return_value = 0
    assert await service.can_add_subscriber(1) is True


async def test_can_add_subscriber_false(service: ShareService, share_repo):
    """Returns False when at the free limit."""
    share_repo.get_active_subscription_count.return_value = 1
    assert await service.can_add_subscriber(1) is False


async def test_get_subscriber_count(service: ShareService, share_repo):
    """Returns count from repo."""
    share_repo.get_active_subscription_count.return_value = 3
    assert await service.get_subscriber_count(1) == 3


# ---------------------------------------------------------------------------
# validate_token
# ---------------------------------------------------------------------------


async def test_validate_token_valid(service: ShareService, share_repo):
    """Returns topic_id for valid token."""
    share_repo.get_topic_id_by_share_token.return_value = 42
    topic_id = await service.validate_token("valid_token")
    assert topic_id == 42


async def test_validate_token_invalid(service: ShareService, share_repo):
    """Raises InvalidShareTokenError for unknown token."""
    share_repo.get_topic_id_by_share_token.return_value = None
    with pytest.raises(InvalidShareTokenError):
        await service.validate_token("bad_token")


# ---------------------------------------------------------------------------
# subscribe
# ---------------------------------------------------------------------------

TOPIC = Topic(id=1, user_id=10, name="parrots", is_free=True, is_active=True)
OWNER = User(id=10, telegram_id=11111, username="owner", first_name="Owner")
SUBSCRIBER = User(id=20, telegram_id=22222, username="sub", first_name="Sub")
SUBSCRIPTION = TopicSubscription(
    id=1, topic_id=1, subscriber_user_id=20, is_active=True,
)


async def test_subscribe_success(service: ShareService, share_repo, topic_repo, user_repo):
    """Successful subscription when all conditions are met."""
    share_repo.get_topic_id_by_share_token.return_value = 1
    topic_repo.get_by_id.return_value = TOPIC
    user_repo.get_by_telegram_id.return_value = SUBSCRIBER
    share_repo.get_subscription.return_value = None
    share_repo.get_active_subscription_count.return_value = 0
    share_repo.create_subscription.return_value = SUBSCRIPTION

    sub = await service.subscribe(token="valid", subscriber_telegram_id=22222)
    assert sub.topic_id == 1
    assert sub.subscriber_user_id == 20
    share_repo.create_subscription.assert_awaited_once_with(1, 20)


async def test_subscribe_own_topic_raises(
    service: ShareService, share_repo, topic_repo, user_repo,
):
    """Raises ValueError when user tries to subscribe to own topic."""
    share_repo.get_topic_id_by_share_token.return_value = 1
    topic_repo.get_by_id.return_value = TOPIC
    user_repo.get_by_telegram_id.return_value = OWNER  # owner = user_id 10

    with pytest.raises(ValueError, match="own topic"):
        await service.subscribe(token="valid", subscriber_telegram_id=11111)


async def test_subscribe_already_subscribed_raises(
    service: ShareService, share_repo, topic_repo, user_repo,
):
    """Raises ValueError when user is already subscribed."""
    share_repo.get_topic_id_by_share_token.return_value = 1
    topic_repo.get_by_id.return_value = TOPIC
    user_repo.get_by_telegram_id.return_value = SUBSCRIBER
    share_repo.get_subscription.return_value = SUBSCRIPTION

    with pytest.raises(ValueError, match="Already subscribed"):
        await service.subscribe(token="valid", subscriber_telegram_id=22222)


async def test_subscribe_limit_reached_raises(
    service: ShareService, share_repo, topic_repo, user_repo,
):
    """Raises ShareLimitError when free limit is reached."""
    share_repo.get_topic_id_by_share_token.return_value = 1
    topic_repo.get_by_id.return_value = TOPIC
    user_repo.get_by_telegram_id.return_value = SUBSCRIBER
    share_repo.get_subscription.return_value = None
    share_repo.get_active_subscription_count.return_value = 1

    with pytest.raises(ShareLimitError):
        await service.subscribe(token="valid", subscriber_telegram_id=22222)


async def test_subscribe_invalid_token_raises(
    service: ShareService, share_repo,
):
    """Raises InvalidShareTokenError for bad token."""
    share_repo.get_topic_id_by_share_token.return_value = None
    with pytest.raises(InvalidShareTokenError):
        await service.subscribe(token="bad", subscriber_telegram_id=22222)


async def test_subscribe_unknown_user_raises(
    service: ShareService, share_repo, topic_repo, user_repo,
):
    """Raises InvalidShareTokenError when subscriber is not in DB."""
    share_repo.get_topic_id_by_share_token.return_value = 1
    topic_repo.get_by_id.return_value = TOPIC
    user_repo.get_by_telegram_id.return_value = None

    with pytest.raises(InvalidShareTokenError):
        await service.subscribe(token="valid", subscriber_telegram_id=99999)


# ---------------------------------------------------------------------------
# unsubscribe
# ---------------------------------------------------------------------------


async def test_unsubscribe_success(service: ShareService, share_repo, user_repo):
    """Returns True when subscription was deactivated."""
    user_repo.get_by_telegram_id.return_value = SUBSCRIBER
    share_repo.deactivate_subscription.return_value = True
    result = await service.unsubscribe(1, 22222)
    assert result is True


async def test_unsubscribe_no_user(service: ShareService, user_repo):
    """Returns False when user not found."""
    user_repo.get_by_telegram_id.return_value = None
    result = await service.unsubscribe(1, 99999)
    assert result is False


# ---------------------------------------------------------------------------
# get_subscriber_telegram_ids / remove_subscriber_by_telegram_id
# ---------------------------------------------------------------------------


async def test_get_subscriber_telegram_ids(service: ShareService, share_repo):
    """Delegates to repo."""
    share_repo.get_subscriber_telegram_ids.return_value = [11111, 22222]
    ids = await service.get_subscriber_telegram_ids(1)
    assert ids == [11111, 22222]


async def test_remove_subscriber_by_telegram_id(
    service: ShareService, share_repo, user_repo,
):
    """Deactivates subscription for the given telegram_id."""
    user_repo.get_by_telegram_id.return_value = SUBSCRIBER
    await service.remove_subscriber_by_telegram_id(1, 22222)
    share_repo.deactivate_subscription.assert_awaited_once_with(1, 20)


async def test_remove_subscriber_unknown_user_no_op(
    service: ShareService, share_repo, user_repo,
):
    """Does nothing when user not in DB."""
    user_repo.get_by_telegram_id.return_value = None
    await service.remove_subscriber_by_telegram_id(1, 99999)
    share_repo.deactivate_subscription.assert_not_awaited()

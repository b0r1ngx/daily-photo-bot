"""Unit tests for share handlers."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from src.config.constants import STATE_MAIN_MENU, STATE_TOPIC_MANAGE
from src.runtime.handlers.share_handler import (
    handle_share_deep_link,
    share_accept_callback,
    share_decline_callback,
    share_topic_callback,
)
from src.types.exceptions import InvalidShareTokenError, ShareLimitError
from src.types.share import TopicSubscription
from src.types.user import Topic, User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OWNER = User(id=10, telegram_id=11111, username="owner", first_name="Owner")
SUBSCRIBER = User(id=20, telegram_id=22222, username="sub", first_name="Sub")
TOPIC = Topic(id=1, user_id=10, name="parrots", is_free=True, is_active=True)
SUBSCRIPTION = TopicSubscription(
    id=1, topic_id=1, subscriber_user_id=20, is_active=True,
)


def _make_callback_update(callback_data: str, user_id: int = 11111):
    """Create a mock Update with a callback query."""
    update = MagicMock()
    update.callback_query = MagicMock()
    update.callback_query.data = callback_data
    update.callback_query.answer = AsyncMock()
    update.callback_query.edit_message_text = AsyncMock()
    update.callback_query.from_user = MagicMock()
    update.callback_query.from_user.id = user_id
    update.callback_query.from_user.username = "testuser"
    update.callback_query.from_user.first_name = "Test"
    update.callback_query.from_user.language_code = "en"
    update.effective_user = MagicMock()
    update.effective_user.language_code = "en"
    return update


def _make_message_update(user_id: int = 22222):
    """Create a mock Update with a message."""
    update = MagicMock()
    update.message = MagicMock()
    update.message.reply_text = AsyncMock()
    update.effective_user = MagicMock()
    update.effective_user.id = user_id
    update.effective_user.language_code = "en"
    return update


def _make_context():
    """Create a mock context with services."""
    ctx = MagicMock()
    ctx.bot_data = {
        "topic_service": AsyncMock(),
        "share_service": AsyncMock(),
    }
    ctx.user_data = {}
    ctx.bot = AsyncMock()
    # Mock get_me to return a bot with a username
    me = MagicMock()
    me.username = "testbot"
    ctx.bot.get_me = AsyncMock(return_value=me)
    return ctx


# ---------------------------------------------------------------------------
# share_topic_callback tests (owner-side)
# ---------------------------------------------------------------------------


class TestShareTopicCallback:
    """Tests for the Share button in topic manage view."""

    async def test_generates_share_link(self):
        """Happy path: generates and shows share link."""
        update = _make_callback_update("share_1", user_id=11111)
        ctx = _make_context()

        ctx.bot_data["topic_service"].ensure_user.return_value = OWNER
        ctx.bot_data["topic_service"].get_topic.return_value = TOPIC
        ctx.bot_data["share_service"].get_share_link.return_value = (
            "https://t.me/testbot?start=share_abc123"
        )
        ctx.bot_data["share_service"].get_subscriber_count.return_value = 0

        state = await share_topic_callback(update, ctx)
        assert state == STATE_TOPIC_MANAGE
        update.callback_query.edit_message_text.assert_awaited_once()
        call_args = update.callback_query.edit_message_text.call_args
        assert "share_abc123" in str(call_args)

    async def test_topic_not_found(self):
        """Shows error when topic doesn't exist."""
        update = _make_callback_update("share_999", user_id=11111)
        ctx = _make_context()

        ctx.bot_data["topic_service"].ensure_user.return_value = OWNER
        ctx.bot_data["topic_service"].get_topic.return_value = None

        state = await share_topic_callback(update, ctx)
        assert state == STATE_TOPIC_MANAGE

    async def test_wrong_owner(self):
        """Shows error when user doesn't own the topic."""
        update = _make_callback_update("share_1", user_id=22222)
        ctx = _make_context()

        other_user = User(id=99, telegram_id=22222, username="other", first_name="Other")
        ctx.bot_data["topic_service"].ensure_user.return_value = other_user
        ctx.bot_data["topic_service"].get_topic.return_value = TOPIC

        state = await share_topic_callback(update, ctx)
        assert state == STATE_TOPIC_MANAGE

    async def test_limit_reached_shows_limit_message(self):
        """Shows limit reached message when at cap."""
        update = _make_callback_update("share_1", user_id=11111)
        ctx = _make_context()

        ctx.bot_data["topic_service"].ensure_user.return_value = OWNER
        ctx.bot_data["topic_service"].get_topic.return_value = TOPIC
        ctx.bot_data["share_service"].get_share_link.return_value = (
            "https://t.me/testbot?start=share_abc123"
        )
        ctx.bot_data["share_service"].get_subscriber_count.return_value = 1  # At limit

        state = await share_topic_callback(update, ctx)
        assert state == STATE_TOPIC_MANAGE

    async def test_no_query_returns_state(self):
        """Returns STATE_TOPIC_MANAGE when no callback query."""
        update = MagicMock()
        update.callback_query = None
        ctx = _make_context()

        state = await share_topic_callback(update, ctx)
        assert state == STATE_TOPIC_MANAGE


# ---------------------------------------------------------------------------
# handle_share_deep_link tests (subscriber-side)
# ---------------------------------------------------------------------------


class TestHandleShareDeepLink:
    """Tests for the deep link handler."""

    async def test_valid_token_shows_confirmation(self):
        """Shows confirmation prompt for valid token."""
        update = _make_message_update()
        ctx = _make_context()

        ctx.bot_data["share_service"].validate_token.return_value = 1
        ctx.bot_data["topic_service"].get_topic.return_value = TOPIC

        state = await handle_share_deep_link(update, ctx, "abc123")
        assert state == STATE_MAIN_MENU
        update.message.reply_text.assert_awaited_once()

    async def test_invalid_token(self):
        """Shows error for invalid token."""
        update = _make_message_update()
        ctx = _make_context()

        ctx.bot_data["share_service"].validate_token.side_effect = InvalidShareTokenError(
            "bad"
        )

        state = await handle_share_deep_link(update, ctx, "bad")
        assert state == STATE_MAIN_MENU

    async def test_topic_not_found(self):
        """Shows error when topic is gone."""
        update = _make_message_update()
        ctx = _make_context()

        ctx.bot_data["share_service"].validate_token.return_value = 1
        ctx.bot_data["topic_service"].get_topic.return_value = None

        state = await handle_share_deep_link(update, ctx, "abc123")
        assert state == STATE_MAIN_MENU

    async def test_no_message(self):
        """Returns STATE_MAIN_MENU when no message."""
        update = MagicMock()
        update.message = None
        update.effective_user = None
        ctx = _make_context()

        state = await handle_share_deep_link(update, ctx, "abc")
        assert state == STATE_MAIN_MENU


# ---------------------------------------------------------------------------
# share_accept_callback tests
# ---------------------------------------------------------------------------


class TestShareAcceptCallback:
    """Tests for the 'Yes, subscribe' button."""

    async def test_successful_subscription(self):
        """Subscribes and shows success message."""
        update = _make_callback_update("shareaccept_abc123", user_id=22222)
        ctx = _make_context()

        ctx.bot_data["share_service"].subscribe.return_value = SUBSCRIPTION
        ctx.bot_data["topic_service"].get_topic.return_value = TOPIC

        await share_accept_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_invalid_token(self):
        """Shows error for invalid token."""
        update = _make_callback_update("shareaccept_bad", user_id=22222)
        ctx = _make_context()

        ctx.bot_data["share_service"].subscribe.side_effect = InvalidShareTokenError("bad")

        await share_accept_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_limit_reached(self):
        """Shows limit reached message."""
        update = _make_callback_update("shareaccept_abc123", user_id=22222)
        ctx = _make_context()

        ctx.bot_data["share_service"].subscribe.side_effect = ShareLimitError(1)

        await share_accept_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_own_topic_error(self):
        """Shows own topic error."""
        update = _make_callback_update("shareaccept_abc123", user_id=11111)
        ctx = _make_context()

        ctx.bot_data["share_service"].subscribe.side_effect = ValueError(
            "Cannot subscribe to your own topic"
        )

        await share_accept_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_already_subscribed_error(self):
        """Shows already subscribed error."""
        update = _make_callback_update("shareaccept_abc123", user_id=22222)
        ctx = _make_context()

        ctx.bot_data["share_service"].subscribe.side_effect = ValueError(
            "Already subscribed"
        )

        await share_accept_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_no_query_returns(self):
        """Returns when no callback query."""
        update = MagicMock()
        update.callback_query = None
        ctx = _make_context()

        await share_accept_callback(update, ctx)


# ---------------------------------------------------------------------------
# share_decline_callback tests
# ---------------------------------------------------------------------------


class TestShareDeclineCallback:
    """Tests for the 'No thanks' button."""

    async def test_decline(self):
        """Shows declined message."""
        update = _make_callback_update("sharedecline_abc123", user_id=22222)
        ctx = _make_context()

        await share_decline_callback(update, ctx)
        update.callback_query.edit_message_text.assert_awaited_once()

    async def test_no_query_returns(self):
        """Returns when no callback query."""
        update = MagicMock()
        update.callback_query = None
        ctx = _make_context()

        await share_decline_callback(update, ctx)

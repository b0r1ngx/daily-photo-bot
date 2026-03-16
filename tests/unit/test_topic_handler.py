"""Unit tests for topic_handler — paid topic flow."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from src.config.constants import STATE_AWAITING_NEW_TOPIC, STATE_MAIN_MENU
from src.runtime.handlers.topic_handler import add_topic_menu, receive_new_topic
from src.types.user import Topic

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def topic_service() -> AsyncMock:
    svc = AsyncMock()
    svc.can_add_free_topic = AsyncMock(return_value=True)
    svc.add_topic = AsyncMock(
        return_value=Topic(id=1, user_id=1, name="parrots", is_free=True),
    )
    return svc


@pytest.fixture
def payment_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def context(topic_service, payment_service) -> MagicMock:
    ctx = MagicMock()
    ctx.bot_data = {
        "topic_service": topic_service,
        "payment_service": payment_service,
    }
    ctx.user_data = {"db_user_id": 1}
    return ctx


@pytest.fixture
def update() -> MagicMock:
    upd = MagicMock()
    upd.message = MagicMock()
    upd.message.reply_text = AsyncMock()
    upd.message.reply_invoice = AsyncMock()
    upd.message.text = "parrots"
    upd.effective_user = MagicMock()
    upd.effective_user.id = 12345
    upd.effective_user.language_code = "en"
    return upd


# ---------------------------------------------------------------------------
# add_topic_menu tests
# ---------------------------------------------------------------------------


async def test_add_topic_menu_paid_pending_skips_invoice(
    update,
    context,
    topic_service,
):
    """When paid_topic_pending is set, go straight to topic name input."""
    context.user_data["paid_topic_pending"] = True

    result = await add_topic_menu(update, context)

    assert result == STATE_AWAITING_NEW_TOPIC
    update.message.reply_text.assert_awaited_once()
    # Should NOT check can_add_free_topic or send invoice
    topic_service.can_add_free_topic.assert_not_awaited()
    update.message.reply_invoice.assert_not_awaited()


# ---------------------------------------------------------------------------
# receive_new_topic tests
# ---------------------------------------------------------------------------


async def test_receive_new_topic_paid_pending_creates_paid_topic(
    update,
    context,
    topic_service,
):
    """With paid_topic_pending, topic is created with is_free=False and flag is consumed."""
    context.user_data["paid_topic_pending"] = True
    topic_service.add_topic.return_value = Topic(
        id=2,
        user_id=1,
        name="parrots",
        is_free=False,
    )

    result = await receive_new_topic(update, context)

    assert result == STATE_MAIN_MENU
    topic_service.add_topic.assert_awaited_once_with(
        user_id=1,
        name="parrots",
        is_free=False,
    )
    # Flag must be consumed (popped)
    assert "paid_topic_pending" not in context.user_data


async def test_receive_new_topic_at_limit_without_payment_rejects(
    update,
    context,
    topic_service,
):
    """At free limit without paid_topic_pending, user is rejected."""
    topic_service.can_add_free_topic.return_value = False

    result = await receive_new_topic(update, context)

    assert result == STATE_MAIN_MENU
    topic_service.add_topic.assert_not_awaited()


async def test_receive_new_topic_free_capacity_creates_free_topic(
    update,
    context,
    topic_service,
):
    """With free capacity and no payment flag, topic is created as free."""
    topic_service.can_add_free_topic.return_value = True

    result = await receive_new_topic(update, context)

    assert result == STATE_MAIN_MENU
    topic_service.add_topic.assert_awaited_once_with(
        user_id=1,
        name="parrots",
        is_free=True,
    )


async def test_paid_flag_consumed_only_once(
    update,
    context,
    topic_service,
):
    """One payment allows exactly one paid topic — second call is subject to free check."""
    context.user_data["paid_topic_pending"] = True
    topic_service.add_topic.return_value = Topic(
        id=2,
        user_id=1,
        name="parrots",
        is_free=False,
    )

    # First call: consumes the flag
    result1 = await receive_new_topic(update, context)
    assert result1 == STATE_MAIN_MENU
    assert "paid_topic_pending" not in context.user_data

    # Second call: no flag, at limit → rejected
    topic_service.can_add_free_topic.return_value = False

    result2 = await receive_new_topic(update, context)
    assert result2 == STATE_MAIN_MENU
    # add_topic should have been called only once (from the first call)
    assert topic_service.add_topic.await_count == 1


# ---------------------------------------------------------------------------
# cancel_command tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_command_clears_paid_topic_pending():
    """cancel_command must clean up paid_topic_pending flag."""
    from src.runtime.handlers.help_handler import cancel_command

    update = AsyncMock()
    update.effective_user = MagicMock(language_code="en")
    update.message = AsyncMock()

    context = MagicMock()
    context.user_data = {"paid_topic_pending": True}

    await cancel_command(update, context)

    assert "paid_topic_pending" not in context.user_data
    update.message.reply_text.assert_awaited_once()

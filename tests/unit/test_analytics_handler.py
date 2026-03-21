"""Unit tests for analytics_handler."""
from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.runtime.handlers.analytics_handler import analytics_command, send_daily_analytics
from src.types.analytics import AnalyticsSnapshot


def _make_snapshot() -> AnalyticsSnapshot:
    return AnalyticsSnapshot(
        total_users=10,
        users_by_language={"en": 5, "ru": 3, "es": 2},
        active_users=4,
        paid_users=1,
        pexels_requests_today=20,
        unsplash_requests_today=5,
        photos_sent_today=15,
        generated_at="2026-03-21T00:00:00+00:00",
    )


def _make_context(analytics_service: AsyncMock | None = None) -> MagicMock:
    ctx = MagicMock()
    ctx.bot = AsyncMock()
    ctx.bot_data = {}
    if analytics_service:
        ctx.bot_data["analytics_service"] = analytics_service
    return ctx


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", -100123)
async def test_send_daily_analytics_happy_path():
    """Report is collected, formatted, and sent to the configured group."""
    svc = MagicMock()
    svc.collect_snapshot = AsyncMock(return_value=_make_snapshot())
    svc.format_message = MagicMock(return_value="<b>report</b>")

    ctx = _make_context(analytics_service=svc)

    await send_daily_analytics(ctx)

    svc.collect_snapshot.assert_awaited_once()
    svc.format_message.assert_called_once()
    ctx.bot.send_message.assert_awaited_once_with(
        chat_id=-100123,
        text="<b>report</b>",
        parse_mode="HTML",
    )


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", None)
async def test_send_daily_analytics_no_group_id():
    """When ANALYTICS_GROUP_ID is None, handler returns immediately."""
    ctx = _make_context()

    await send_daily_analytics(ctx)

    # Bot should never be called
    ctx.bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", -100123)
async def test_send_daily_analytics_handles_send_failure():
    """If send_message raises, the handler logs but does not crash."""
    svc = MagicMock()
    svc.collect_snapshot = AsyncMock(return_value=_make_snapshot())
    svc.format_message = MagicMock(return_value="<b>report</b>")

    ctx = _make_context(analytics_service=svc)
    ctx.bot.send_message = AsyncMock(side_effect=Exception("Telegram API error"))

    # Should not raise
    await send_daily_analytics(ctx)


# ---------------------------------------------------------------------------
# /analytics command tests
# ---------------------------------------------------------------------------

ANALYTICS_GROUP_ID = -100123


def _make_update(chat_id: int) -> MagicMock:
    upd = MagicMock()
    upd.message = AsyncMock()
    upd.message.reply_text = AsyncMock()
    upd.effective_chat = MagicMock()
    upd.effective_chat.id = chat_id
    return upd


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", ANALYTICS_GROUP_ID)
async def test_analytics_command_happy_path():
    """Report is collected, formatted, and replied in the analytics group."""
    svc = MagicMock()
    svc.collect_snapshot = AsyncMock(return_value=_make_snapshot())
    svc.format_message = MagicMock(return_value="<b>report</b>")

    ctx = _make_context(analytics_service=svc)
    upd = _make_update(chat_id=ANALYTICS_GROUP_ID)

    await analytics_command(upd, ctx)

    svc.collect_snapshot.assert_awaited_once()
    svc.format_message.assert_called_once()
    upd.message.reply_text.assert_awaited_once_with(
        "<b>report</b>",
        parse_mode="HTML",
    )


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", ANALYTICS_GROUP_ID)
async def test_analytics_command_no_message():
    """When update.message is None, handler returns immediately."""
    ctx = _make_context()
    upd = MagicMock()
    upd.message = None

    await analytics_command(upd, ctx)


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", None)
async def test_analytics_command_no_group_id():
    """When ANALYTICS_GROUP_ID is None, handler returns immediately."""
    upd = _make_update(chat_id=-100999)
    ctx = _make_context()

    await analytics_command(upd, ctx)

    upd.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", ANALYTICS_GROUP_ID)
async def test_analytics_command_wrong_chat():
    """When invoked outside the analytics group, handler is silently ignored."""
    svc = MagicMock()
    ctx = _make_context(analytics_service=svc)
    upd = _make_update(chat_id=-100999)

    await analytics_command(upd, ctx)

    upd.message.reply_text.assert_not_awaited()


@pytest.mark.asyncio
@patch("src.config.settings.ANALYTICS_GROUP_ID", ANALYTICS_GROUP_ID)
async def test_analytics_command_handles_exception():
    """If collect_snapshot raises, the handler logs but does not crash."""
    svc = MagicMock()
    svc.collect_snapshot = AsyncMock(side_effect=Exception("DB error"))

    ctx = _make_context(analytics_service=svc)
    upd = _make_update(chat_id=ANALYTICS_GROUP_ID)

    # Should not raise
    await analytics_command(upd, ctx)

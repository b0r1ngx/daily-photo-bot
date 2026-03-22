"""Unit tests for schedule_handler — Forbidden error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import Forbidden

from src.runtime.handlers.schedule_handler import (
    _fan_out_to_subscribers,
    _send_scheduled_photo,
)
from src.runtime.job_utils import deactivate_all_user_schedules
from src.types.photo import PhotoResult
from src.types.schedule import ScheduleConfig, ScheduleType
from src.types.user import MetadataPrefs, Topic

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

TOPIC_A = Topic(id=1, user_id=42, name="parrots", is_free=True, is_active=True)
TOPIC_B = Topic(id=2, user_id=42, name="cats", is_free=True, is_active=True)

ACTIVE_SCHEDULE_A = ScheduleConfig(
    topic_id=1,
    schedule_type=ScheduleType.INTERVAL,
    value="600",
    is_active=True,
    id=10,
)

ACTIVE_SCHEDULE_B = ScheduleConfig(
    topic_id=2,
    schedule_type=ScheduleType.INTERVAL,
    value="3600",
    is_active=True,
    id=20,
)

SAMPLE_PHOTO = PhotoResult(
    photo_id="123",
    url="https://images.pexels.com/123.jpg",
    photographer="Test",
    source_url="https://pexels.com/123",
    source="pexels",
    alt="A parrot",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def topic_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_topic = AsyncMock(return_value=TOPIC_A)
    svc.get_user_topics = AsyncMock(return_value=[TOPIC_A, TOPIC_B])
    svc.get_topic_with_language = AsyncMock(return_value=("parrots", "en"))
    svc.get_metadata_prefs = AsyncMock(return_value=MetadataPrefs())
    return svc


@pytest.fixture
def schedule_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_schedule = AsyncMock(side_effect=[ACTIVE_SCHEDULE_A, ACTIVE_SCHEDULE_B])
    svc.remove_schedule = AsyncMock()
    return svc


@pytest.fixture
def photo_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_photo = AsyncMock(return_value=SAMPLE_PHOTO)
    return svc


@pytest.fixture
def context(topic_service, photo_service, schedule_service) -> MagicMock:
    ctx = MagicMock()
    ctx.bot_data = {
        "topic_service": topic_service,
        "photo_service": photo_service,
        "schedule_service": schedule_service,
    }
    ctx.bot = AsyncMock()
    ctx.job = MagicMock()
    ctx.job.data = {"topic_id": 1}
    ctx.job.chat_id = 12345
    ctx.job.name = "photo_1"
    return ctx


# ===========================================================================
# _deactivate_all_user_schedules tests
# ===========================================================================


class TestDeactivateAllUserSchedules:
    """Tests for the deactivate_all_user_schedules helper."""

    @patch("src.runtime.job_utils.remove_job")
    async def test_deactivates_all_active_schedules(
        self,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
    ):
        """All active schedules for user are deactivated and jobs removed."""
        count = await deactivate_all_user_schedules(
            42, topic_service, schedule_service, context,
        )

        assert count == 2
        topic_service.get_user_topics.assert_awaited_once_with(42)
        assert schedule_service.remove_schedule.await_count == 2
        schedule_service.remove_schedule.assert_any_await(1)
        schedule_service.remove_schedule.assert_any_await(2)
        assert mock_remove_job.call_count == 2
        mock_remove_job.assert_any_call("photo_1", context)
        mock_remove_job.assert_any_call("photo_2", context)

    @patch("src.runtime.job_utils.remove_job")
    async def test_skips_inactive_schedules(
        self,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
    ):
        """Inactive schedules are not counted or removed."""
        inactive = ScheduleConfig(
            topic_id=1,
            schedule_type=ScheduleType.INTERVAL,
            value="600",
            is_active=False,
            id=10,
        )
        schedule_service.get_schedule = AsyncMock(side_effect=[inactive, ACTIVE_SCHEDULE_B])

        count = await deactivate_all_user_schedules(
            42, topic_service, schedule_service, context,
        )

        assert count == 1
        schedule_service.remove_schedule.assert_awaited_once_with(2)
        mock_remove_job.assert_called_once_with("photo_2", context)

    @patch("src.runtime.job_utils.remove_job")
    async def test_partial_failure_continues(
        self,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
    ):
        """If one topic's deactivation fails, the other still succeeds."""
        schedule_service.get_schedule = AsyncMock(
            side_effect=[ACTIVE_SCHEDULE_A, ACTIVE_SCHEDULE_B],
        )
        schedule_service.remove_schedule = AsyncMock(
            side_effect=[Exception("DB error"), None],
        )

        count = await deactivate_all_user_schedules(
            42, topic_service, schedule_service, context,
        )

        # First topic raised, second succeeded
        assert count == 1
        assert schedule_service.remove_schedule.await_count == 2
        mock_remove_job.assert_called_once_with("photo_2", context)


# ===========================================================================
# _send_scheduled_photo Forbidden handling tests
# ===========================================================================


class TestSendScheduledPhotoForbidden:
    """Tests for Forbidden error handling in _send_scheduled_photo."""

    @patch("src.runtime.job_utils.remove_job")
    @patch("src.runtime.handlers.schedule_handler.build_photo_caption", return_value="caption")
    async def test_forbidden_deactivates_all_user_schedules(
        self,
        mock_caption,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
        photo_service,
    ):
        """When send_photo raises Forbidden, all user schedules are deactivated."""
        context.bot.send_photo.side_effect = Forbidden("Forbidden: bot was blocked by the user")

        await _send_scheduled_photo(context)

        # Should have looked up the topic to get user_id
        topic_service.get_topic.assert_awaited_once_with(1)
        # Should have deactivated all schedules for user 42
        topic_service.get_user_topics.assert_awaited_once_with(42)
        assert schedule_service.remove_schedule.await_count == 2
        # mark_sent should NOT have been called
        schedule_service.mark_sent.assert_not_awaited()

    @patch("src.runtime.handlers.schedule_handler.remove_job")
    @patch("src.runtime.handlers.schedule_handler.build_photo_caption", return_value="caption")
    async def test_forbidden_topic_not_found_removes_job(
        self,
        mock_caption,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
        photo_service,
    ):
        """When send_photo raises Forbidden and topic is gone, remove just the job."""
        context.bot.send_photo.side_effect = Forbidden("Forbidden: bot was blocked by the user")
        topic_service.get_topic.return_value = None

        await _send_scheduled_photo(context)

        topic_service.get_topic.assert_awaited_once_with(1)
        # Should NOT try to get user topics (topic not found)
        topic_service.get_user_topics.assert_not_awaited()
        # Should deactivate the orphaned schedule in DB
        schedule_service.remove_schedule.assert_awaited_once_with(1)
        # Should remove the job directly
        mock_remove_job.assert_called_once_with("photo_1", context)
        schedule_service.mark_sent.assert_not_awaited()

    @patch("src.runtime.handlers.schedule_handler.remove_job")
    @patch("src.runtime.handlers.schedule_handler.build_photo_caption", return_value="caption")
    async def test_non_forbidden_exception_does_not_deactivate(
        self,
        mock_caption,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
        photo_service,
    ):
        """Regular exceptions from send_photo do NOT trigger deactivation."""
        context.bot.send_photo.side_effect = RuntimeError("Network timeout")

        await _send_scheduled_photo(context)

        # Should NOT try to deactivate schedules
        topic_service.get_topic.assert_not_awaited()
        topic_service.get_user_topics.assert_not_awaited()
        schedule_service.remove_schedule.assert_not_awaited()
        schedule_service.mark_sent.assert_not_awaited()

    @patch("src.runtime.handlers.schedule_handler.remove_job")
    @patch("src.runtime.handlers.schedule_handler.build_photo_caption", return_value="caption")
    async def test_forbidden_cleanup_error_is_caught(
        self,
        mock_caption,
        mock_remove_job,
        context,
        topic_service,
        schedule_service,
        photo_service,
    ):
        """If cleanup raises during Forbidden handling, error is logged, not propagated."""
        context.bot.send_photo.side_effect = Forbidden("Forbidden: bot was blocked by the user")
        topic_service.get_topic.side_effect = RuntimeError("DB connection lost")

        # Should NOT raise — the inner try/except catches the cleanup error
        await _send_scheduled_photo(context)

        topic_service.get_topic.assert_awaited_once_with(1)
        # Cleanup failed, so no further calls should have been made
        topic_service.get_user_topics.assert_not_awaited()
        schedule_service.remove_schedule.assert_not_awaited()
        schedule_service.mark_sent.assert_not_awaited()


# ===========================================================================
# _fan_out_to_subscribers tests
# ===========================================================================


class TestFanOutToSubscribers:
    """Tests for fan-out photo delivery to subscribers."""

    async def test_no_share_service_is_no_op(self):
        """Does nothing if share_service is not in bot_data."""
        ctx = MagicMock()
        ctx.bot_data = {}
        ctx.bot = AsyncMock()

        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "caption")
        ctx.bot.send_photo.assert_not_awaited()

    async def test_no_subscribers_is_no_op(self):
        """Does nothing if there are no subscribers."""
        ctx = MagicMock()
        share_service = AsyncMock()
        share_service.get_subscriber_telegram_ids.return_value = []
        ctx.bot_data = {"share_service": share_service}
        ctx.bot = AsyncMock()

        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "caption")
        ctx.bot.send_photo.assert_not_awaited()

    async def test_sends_to_all_subscribers(self):
        """Sends photo to each subscriber."""
        ctx = MagicMock()
        share_service = AsyncMock()
        share_service.get_subscriber_telegram_ids.return_value = [100, 200, 300]
        ctx.bot_data = {"share_service": share_service}
        ctx.bot = AsyncMock()

        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "cap")

        assert ctx.bot.send_photo.await_count == 3
        chat_ids = [call.kwargs["chat_id"] for call in ctx.bot.send_photo.await_args_list]
        assert chat_ids == [100, 200, 300]

    async def test_forbidden_removes_subscriber_not_owner(self):
        """Forbidden from subscriber removes only that subscription."""
        ctx = MagicMock()
        share_service = AsyncMock()
        share_service.get_subscriber_telegram_ids.return_value = [100, 200]
        ctx.bot_data = {"share_service": share_service}
        ctx.bot = AsyncMock()
        ctx.bot.send_photo.side_effect = [
            Forbidden("blocked"),
            None,  # second subscriber succeeds
        ]

        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "cap")

        share_service.remove_subscriber_by_telegram_id.assert_awaited_once_with(1, 100)
        assert ctx.bot.send_photo.await_count == 2

    async def test_non_forbidden_error_continues(self):
        """Non-Forbidden errors are logged but delivery continues."""
        ctx = MagicMock()
        share_service = AsyncMock()
        share_service.get_subscriber_telegram_ids.return_value = [100, 200]
        ctx.bot_data = {"share_service": share_service}
        ctx.bot = AsyncMock()
        ctx.bot.send_photo.side_effect = [
            RuntimeError("network timeout"),
            None,
        ]

        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "cap")

        share_service.remove_subscriber_by_telegram_id.assert_not_awaited()
        assert ctx.bot.send_photo.await_count == 2

    async def test_remove_subscriber_failure_is_caught(self):
        """If remove_subscriber_by_telegram_id fails, it's caught."""
        ctx = MagicMock()
        share_service = AsyncMock()
        share_service.get_subscriber_telegram_ids.return_value = [100]
        share_service.remove_subscriber_by_telegram_id.side_effect = RuntimeError("DB error")
        ctx.bot_data = {"share_service": share_service}
        ctx.bot = AsyncMock()
        ctx.bot.send_photo.side_effect = Forbidden("blocked")

        # Should NOT raise
        await _fan_out_to_subscribers(ctx, 1, "http://img.jpg", "cap")

    @patch("src.runtime.handlers.schedule_handler._fan_out_to_subscribers", new_callable=AsyncMock)
    @patch("src.runtime.handlers.schedule_handler.build_photo_caption", return_value="caption")
    async def test_send_scheduled_photo_calls_fan_out(
        self,
        mock_caption,
        mock_fan_out,
        context,
        topic_service,
        photo_service,
        schedule_service,
    ):
        """_send_scheduled_photo calls fan-out after successful owner send."""
        context.bot.send_photo.return_value = None
        schedule_service.get_schedule = AsyncMock(return_value=ACTIVE_SCHEDULE_A)

        await _send_scheduled_photo(context)

        mock_fan_out.assert_awaited_once()
        call_args = mock_fan_out.call_args
        assert call_args[0][1] == 1  # topic_id

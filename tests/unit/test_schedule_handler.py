"""Unit tests for schedule_handler — Forbidden error handling."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telegram.error import Forbidden

from src.runtime.handlers.schedule_handler import (
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

    @patch("src.runtime.handlers.schedule_handler.remove_job")
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

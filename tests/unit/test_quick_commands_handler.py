"""Unit tests for quick_commands_handler — /photo and /stop commands."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.config.constants import STATE_MAIN_MENU
from src.runtime.handlers.quick_commands_handler import photo_command, stop_command
from src.types.photo import PhotoResult
from src.types.schedule import ScheduleConfig, ScheduleType
from src.types.user import Topic

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_TOPIC = Topic(id=1, user_id=1, name="parrots", is_free=True, is_active=True)

SAMPLE_PHOTO = PhotoResult(
    photo_id="123",
    url="https://photo.url/img.jpg",
    photographer="John",
    source_url="https://pexels.com/123",
    source="pexels",
    alt="A parrot",
)

ACTIVE_SCHEDULE = ScheduleConfig(
    topic_id=1,
    schedule_type=ScheduleType.INTERVAL,
    value="3600",
    is_active=True,
    id=1,
    last_sent_at=None,
)

INACTIVE_SCHEDULE = ScheduleConfig(
    topic_id=2,
    schedule_type=ScheduleType.INTERVAL,
    value="3600",
    is_active=False,
    id=2,
    last_sent_at=None,
)


@pytest.fixture
def topic_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_user_topics = AsyncMock(return_value=[SAMPLE_TOPIC])
    svc.get_topic_with_language = AsyncMock(return_value=("parrots", "en"))
    return svc


@pytest.fixture
def photo_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_photo = AsyncMock(return_value=SAMPLE_PHOTO)
    return svc


@pytest.fixture
def schedule_service() -> AsyncMock:
    svc = AsyncMock()
    svc.get_schedule = AsyncMock(return_value=ACTIVE_SCHEDULE)
    svc.remove_schedule = AsyncMock()
    return svc


@pytest.fixture
def context(topic_service, photo_service, schedule_service) -> MagicMock:
    ctx = MagicMock()
    ctx.bot_data = {
        "topic_service": topic_service,
        "photo_service": photo_service,
        "schedule_service": schedule_service,
    }
    ctx.user_data = {"db_user_id": 1}
    return ctx


@pytest.fixture
def update() -> MagicMock:
    upd = MagicMock()
    upd.message = MagicMock()
    upd.message.reply_text = AsyncMock()
    upd.message.reply_photo = AsyncMock()
    upd.effective_user = MagicMock()
    upd.effective_user.id = 12345
    upd.effective_user.language_code = "en"
    return upd


# ===========================================================================
# photo_command tests
# ===========================================================================


class TestPhotoCommand:
    """Tests for the /photo command handler."""

    async def test_no_message_returns_none(self, context):
        """When update.message is None, return None immediately."""
        upd = MagicMock()
        upd.message = None

        result = await photo_command(upd, context)

        assert result is None

    async def test_no_db_user_replies_use_start_first(self, update, context):
        """When user_data has no db_user_id, reply with 'use_start_first'."""
        context.user_data = {}

        result = await photo_command(update, context)

        assert result is None
        update.message.reply_text.assert_awaited_once()
        call_args = update.message.reply_text.call_args
        assert "use_start_first" in call_args[0][0] or "start" in call_args[0][0].lower()

    async def test_no_topics_replies_photo_no_topics(
        self,
        update,
        context,
        topic_service,
    ):
        """When user has no topics, reply with 'photo_no_topics'."""
        topic_service.get_user_topics.return_value = []

        result = await photo_command(update, context)

        assert result is None
        topic_service.get_user_topics.assert_awaited_once_with(1)
        update.message.reply_text.assert_awaited_once()

    @patch("src.runtime.handlers.quick_commands_handler.random.choice")
    async def test_get_topic_with_language_none_replies_error(
        self,
        mock_choice,
        update,
        context,
        topic_service,
    ):
        """When get_topic_with_language returns None, reply with 'photo_error'."""
        mock_choice.return_value = SAMPLE_TOPIC
        topic_service.get_topic_with_language.return_value = None

        result = await photo_command(update, context)

        assert result is None
        topic_service.get_topic_with_language.assert_awaited_once_with(SAMPLE_TOPIC.id)
        update.message.reply_text.assert_awaited_once()

    @patch("src.runtime.handlers.quick_commands_handler.random.choice")
    async def test_get_photo_exception_replies_error(
        self,
        mock_choice,
        update,
        context,
        topic_service,
        photo_service,
    ):
        """When photo_service.get_photo raises, reply with 'photo_error'."""
        mock_choice.return_value = SAMPLE_TOPIC
        photo_service.get_photo.side_effect = Exception("API timeout")

        result = await photo_command(update, context)

        assert result is None
        photo_service.get_photo.assert_awaited_once()
        update.message.reply_text.assert_awaited_once()

    @patch("src.runtime.handlers.quick_commands_handler.random.choice")
    async def test_happy_path_sends_photo(
        self,
        mock_choice,
        update,
        context,
        topic_service,
        photo_service,
    ):
        """Happy path: topics exist, photo fetched → calls reply_photo."""
        mock_choice.return_value = SAMPLE_TOPIC

        result = await photo_command(update, context)

        assert result is None
        photo_service.get_photo.assert_awaited_once_with(
            topic="parrots",
            topic_id=SAMPLE_TOPIC.id,
            language_code="en",
        )
        update.message.reply_photo.assert_awaited_once()
        call_kwargs = update.message.reply_photo.call_args[1]
        assert call_kwargs["photo"] == SAMPLE_PHOTO.url
        assert call_kwargs["parse_mode"] == "Markdown"
        # reply_text should NOT have been called (no error)
        update.message.reply_text.assert_not_awaited()

    @patch("src.runtime.handlers.quick_commands_handler.random.choice")
    async def test_reply_photo_exception_falls_back_to_text(
        self,
        mock_choice,
        update,
        context,
        photo_service,
    ):
        """When reply_photo raises, fall back to reply_text with error."""
        mock_choice.return_value = SAMPLE_TOPIC
        update.message.reply_photo.side_effect = Exception("Telegram API error")

        result = await photo_command(update, context)

        assert result is None
        update.message.reply_photo.assert_awaited_once()
        update.message.reply_text.assert_awaited_once()


# ===========================================================================
# stop_command tests
# ===========================================================================


@patch("src.runtime.handlers.quick_commands_handler._remove_job")
class TestStopCommand:
    """Tests for the /stop command handler."""

    async def test_no_message_returns_main_menu(self, mock_remove_job, context):
        """When update.message is None, return STATE_MAIN_MENU."""
        upd = MagicMock()
        upd.message = None

        result = await stop_command(upd, context)

        assert result == STATE_MAIN_MENU
        mock_remove_job.assert_not_called()

    async def test_no_db_user_replies_use_start_first(
        self,
        mock_remove_job,
        update,
        context,
    ):
        """When user_data has no db_user_id, reply with 'use_start_first'."""
        context.user_data = {}

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        update.message.reply_text.assert_awaited_once()
        call_args = update.message.reply_text.call_args
        assert "use_start_first" in call_args[0][0] or "start" in call_args[0][0].lower()
        mock_remove_job.assert_not_called()

    async def test_no_active_schedules_replies_stop_no_schedules(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """When user has topics but no active schedules, reply with 'stop_no_schedules'."""
        schedule_service.get_schedule.return_value = INACTIVE_SCHEDULE

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        schedule_service.remove_schedule.assert_not_awaited()
        mock_remove_job.assert_not_called()
        update.message.reply_text.assert_awaited_once()

    async def test_no_schedule_at_all_replies_stop_no_schedules(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """When get_schedule returns None, reply with 'stop_no_schedules'."""
        schedule_service.get_schedule.return_value = None

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        schedule_service.remove_schedule.assert_not_awaited()
        mock_remove_job.assert_not_called()
        update.message.reply_text.assert_awaited_once()

    async def test_no_topics_replies_stop_no_schedules(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """When user has zero topics, reply with 'stop_no_schedules'."""
        topic_service.get_user_topics.return_value = []

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        schedule_service.get_schedule.assert_not_awaited()
        mock_remove_job.assert_not_called()
        update.message.reply_text.assert_awaited_once()

    async def test_happy_path_removes_active_schedules(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """Happy path: active schedules exist → removes them and replies 'stop_success'."""
        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        schedule_service.get_schedule.assert_awaited_once_with(SAMPLE_TOPIC.id)
        schedule_service.remove_schedule.assert_awaited_once_with(SAMPLE_TOPIC.id)
        mock_remove_job.assert_called_once_with(context, f"photo_{SAMPLE_TOPIC.id}")
        update.message.reply_text.assert_awaited_once()

    async def test_multiple_topics_stops_all_active(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """Multiple topics with active schedules → all are stopped."""
        topic_a = Topic(id=10, user_id=1, name="cats", is_free=True, is_active=True)
        topic_b = Topic(id=20, user_id=1, name="dogs", is_free=True, is_active=True)
        topic_service.get_user_topics.return_value = [topic_a, topic_b]

        schedule_a = ScheduleConfig(
            topic_id=10,
            schedule_type=ScheduleType.INTERVAL,
            value="3600",
            is_active=True,
            id=10,
            last_sent_at=None,
        )
        schedule_b = ScheduleConfig(
            topic_id=20,
            schedule_type=ScheduleType.INTERVAL,
            value="7200",
            is_active=True,
            id=20,
            last_sent_at=None,
        )
        schedule_service.get_schedule.side_effect = [schedule_a, schedule_b]

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        assert schedule_service.remove_schedule.await_count == 2
        assert mock_remove_job.call_count == 2

    async def test_partial_failure_continues_and_reports(
        self,
        mock_remove_job,
        update,
        context,
        topic_service,
        schedule_service,
    ):
        """When one topic's schedule removal raises, continue processing others."""
        topic_ok = Topic(id=10, user_id=1, name="cats", is_free=True, is_active=True)
        topic_fail = Topic(id=20, user_id=1, name="dogs", is_free=True, is_active=True)
        topic_service.get_user_topics.return_value = [topic_fail, topic_ok]

        schedule_fail = ScheduleConfig(
            topic_id=20,
            schedule_type=ScheduleType.INTERVAL,
            value="3600",
            is_active=True,
            id=20,
            last_sent_at=None,
        )
        schedule_ok = ScheduleConfig(
            topic_id=10,
            schedule_type=ScheduleType.INTERVAL,
            value="3600",
            is_active=True,
            id=10,
            last_sent_at=None,
        )

        # First call raises, second succeeds
        schedule_service.get_schedule.side_effect = [schedule_fail, schedule_ok]
        schedule_service.remove_schedule.side_effect = [
            Exception("DB error"),
            None,
        ]

        result = await stop_command(update, context)

        assert result == STATE_MAIN_MENU
        # Both topics attempted
        assert schedule_service.get_schedule.await_count == 2
        # Both attempted remove_schedule (both had active schedule)
        assert schedule_service.remove_schedule.await_count == 2
        # Only the successful one gets _remove_job
        assert mock_remove_job.call_count == 1
        mock_remove_job.assert_called_once_with(context, "photo_10")
        # Reply was sent (stop_success with count=1)
        update.message.reply_text.assert_awaited_once()

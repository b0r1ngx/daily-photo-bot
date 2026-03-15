"""Schedule configuration handler. Layer: Runtime."""
from __future__ import annotations

import datetime
import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import (
    STATE_MAIN_MENU,
    STATE_SCHEDULE_HOUR,
    STATE_SCHEDULE_INTERVAL,
    STATE_SCHEDULE_MINUTE,
    STATE_SCHEDULE_SELECT_TOPIC,
    STATE_SCHEDULE_TYPE,
)
from src.runtime.keyboards import (
    hour_keyboard,
    interval_keyboard,
    main_menu_keyboard,
    minute_keyboard,
    schedule_type_keyboard,
    topic_list_keyboard,
)
from src.service.schedule_service import ScheduleService
from src.service.topic_service import TopicService

logger = logging.getLogger(__name__)


async def schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '⏰ Schedule' button press — show topic list."""
    if not update.message:
        return STATE_MAIN_MENU

    topic_service: TopicService = context.bot_data["topic_service"]
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text("Please use /start first.")
        return STATE_MAIN_MENU

    topics = await topic_service.get_user_topics(user_id)
    if not topics:
        await update.message.reply_text(
            "You don't have any topics yet! Add one first.",
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    await update.message.reply_text(
        "📋 Select a topic to configure its schedule:",
        reply_markup=topic_list_keyboard(topics),
    )
    return STATE_SCHEDULE_SELECT_TOPIC


async def select_topic_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle topic selection from inline keyboard."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_SELECT_TOPIC

    await query.answer()

    # Parse topic_id from callback_data: "topic_42"
    topic_id = int(query.data.split("_")[1])
    context.user_data["schedule_topic_id"] = topic_id

    await query.edit_message_text(
        "⏰ How do you want to receive photos?",
        reply_markup=schedule_type_keyboard(),
    )
    return STATE_SCHEDULE_TYPE


async def select_schedule_type_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle schedule type selection (interval or fixed time)."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_TYPE

    await query.answer()

    if query.data == "stype_interval":
        await query.edit_message_text(
            "⏱ Select how often you want to receive photos:",
            reply_markup=interval_keyboard(),
        )
        return STATE_SCHEDULE_INTERVAL

    if query.data == "stype_fixed":
        await query.edit_message_text(
            "🕐 Select the hour (24h format):",
            reply_markup=hour_keyboard(),
        )
        return STATE_SCHEDULE_HOUR

    if query.data == "stype_remove":
        topic_id = context.user_data.get("schedule_topic_id")
        if topic_id is None:
            await query.edit_message_text("❌ Error: no topic selected.")
            return STATE_MAIN_MENU

        schedule_service: ScheduleService = context.bot_data["schedule_service"]
        await schedule_service.remove_schedule(topic_id)
        _remove_job(context, f"photo_{topic_id}")

        await query.edit_message_text(
            "✅ Schedule removed! You won't receive photos for this topic "
            "until you set a new schedule.",
        )
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text='Use the menu below to continue.',
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    return STATE_SCHEDULE_TYPE


async def select_interval_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle interval selection."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_INTERVAL

    await query.answer()

    seconds = int(query.data.split("_")[1])
    topic_id = context.user_data.get("schedule_topic_id")

    if not topic_id:
        await query.edit_message_text("❌ Error: topic not found. Please try again.")
        return STATE_MAIN_MENU

    schedule_service: ScheduleService = context.bot_data["schedule_service"]
    await schedule_service.set_interval_schedule(topic_id=topic_id, seconds=seconds)

    # Register the job
    chat_id = update.effective_chat.id if update.effective_chat else None
    _register_interval_job(context, topic_id, seconds, chat_id)

    await query.edit_message_text(
        f"✅ Schedule set! You'll receive a photo every {_format_interval(seconds)}.",
    )
    return STATE_MAIN_MENU


async def select_hour_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle hour selection for fixed-time schedule."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_HOUR

    await query.answer()

    hour = int(query.data.split("_")[1])
    context.user_data["schedule_hour"] = hour

    await query.edit_message_text(
        f"🕐 Selected hour: {hour:02d}\nNow select minutes:",
        reply_markup=minute_keyboard(),
    )
    return STATE_SCHEDULE_MINUTE


async def select_minute_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle minute selection for fixed-time schedule."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_MINUTE

    await query.answer()

    minute = int(query.data.split("_")[1])
    hour = context.user_data.get("schedule_hour", 0)
    topic_id = context.user_data.get("schedule_topic_id")

    if not topic_id:
        await query.edit_message_text("❌ Error: topic not found. Please try again.")
        return STATE_MAIN_MENU

    schedule_service: ScheduleService = context.bot_data["schedule_service"]
    await schedule_service.set_fixed_time_schedule(
        topic_id=topic_id, hour=hour, minute=minute
    )

    # Register the daily job
    chat_id = update.effective_chat.id if update.effective_chat else None
    _register_daily_job(context, topic_id, hour, minute, chat_id)

    await query.edit_message_text(
        f"✅ Schedule set! You'll receive a photo daily at {hour:02d}:{minute:02d}.",
    )
    return STATE_MAIN_MENU


def _register_interval_job(
    context: ContextTypes.DEFAULT_TYPE,
    topic_id: int,
    seconds: int,
    chat_id: int | None,
) -> None:
    """Register a repeating job for interval-based schedule."""
    job_name = f"photo_{topic_id}"
    _remove_job(context, job_name)
    context.job_queue.run_repeating(  # type: ignore[union-attr]
        _send_scheduled_photo,
        interval=seconds,
        first=seconds,  # Don't send immediately
        name=job_name,
        data={"topic_id": topic_id},
        chat_id=chat_id,
    )


def _register_daily_job(
    context: ContextTypes.DEFAULT_TYPE,
    topic_id: int,
    hour: int,
    minute: int,
    chat_id: int | None,
) -> None:
    """Register a daily job for fixed-time schedule."""
    job_name = f"photo_{topic_id}"
    _remove_job(context, job_name)
    context.job_queue.run_daily(  # type: ignore[union-attr]
        _send_scheduled_photo,
        time=datetime.time(hour=hour, minute=minute),
        name=job_name,
        data={"topic_id": topic_id},
        chat_id=chat_id,
    )


def _remove_job(context: ContextTypes.DEFAULT_TYPE, name: str) -> None:
    """Remove existing job by name if it exists."""
    if not context.job_queue:
        return
    current_jobs = context.job_queue.get_jobs_by_name(name)
    for job in current_jobs:
        job.schedule_removal()


async def _send_scheduled_photo(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: fetch and send a photo for a scheduled topic."""
    from src.service.photo_service import PhotoService

    job = context.job
    if not job or not job.data or not job.chat_id:
        return

    topic_id = job.data["topic_id"]
    photo_service: PhotoService = context.bot_data["photo_service"]
    schedule_service: ScheduleService = context.bot_data["schedule_service"]

    # Resolve topic name via direct DB query (acceptable shortcut for job callbacks)
    db = context.bot_data["db"]
    cursor = await db.execute(
        "SELECT name FROM topics WHERE id = ? AND is_active = 1", (topic_id,)
    )
    row = await cursor.fetchone()
    if not row:
        logger.warning("Topic %d not found or inactive, skipping.", topic_id)
        return

    topic_name = row[0]

    try:
        photo = await photo_service.get_photo(topic=topic_name, topic_id=topic_id)
    except Exception:
        logger.exception("Failed to fetch photo for topic '%s'", topic_name)
        return

    caption = (
        f"📸 *{topic_name}*\n"
        f"Photo by {photo.photographer} on "
        f"[{photo.source.title()}]({photo.source_url})"
    )

    try:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=photo.url,
            caption=caption,
            parse_mode="Markdown",
        )
    except Exception:
        logger.exception("Failed to send photo to chat %d", job.chat_id)
        return

    # Update last_sent_at
    schedule = await schedule_service.get_schedule(topic_id)
    if schedule and schedule.id:
        await schedule_service.mark_sent(schedule.id)


def _format_interval(seconds: int) -> str:
    """Format seconds into a human-readable interval string."""
    if seconds < 3600:
        return f"{seconds // 60} minutes"
    hours = seconds // 3600
    return f"{hours} hour{'s' if hours > 1 else ''}"

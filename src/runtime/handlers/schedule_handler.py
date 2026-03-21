"""Schedule configuration handler. Layer: Runtime."""

from __future__ import annotations

import datetime
import logging

from telegram import Update
from telegram.error import Forbidden
from telegram.ext import ContextTypes

from src.config.constants import (
    STATE_MAIN_MENU,
    STATE_SCHEDULE_HOUR,
    STATE_SCHEDULE_INTERVAL,
    STATE_SCHEDULE_MINUTE,
    STATE_SCHEDULE_SELECT_TOPIC,
    STATE_SCHEDULE_TYPE,
)
from src.config.i18n import t
from src.runtime.caption import build_photo_caption
from src.runtime.job_utils import deactivate_all_user_schedules, remove_job
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


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


async def schedule_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '⏰ Schedule' button press — show topic list."""
    if not update.message:
        return STATE_MAIN_MENU

    lang = _lang(update)
    topic_service: TopicService = context.bot_data["topic_service"]
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text(t("use_start_first", lang))
        return STATE_MAIN_MENU

    topics = await topic_service.get_user_topics(user_id)
    if not topics:
        await update.message.reply_text(
            t("no_topics_for_schedule", lang),
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    await update.message.reply_text(
        t("select_topic", lang),
        reply_markup=topic_list_keyboard(topics),
    )
    return STATE_SCHEDULE_SELECT_TOPIC


async def select_topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle topic selection from inline keyboard."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_SELECT_TOPIC

    await query.answer()

    lang = _lang(update)

    # Parse topic_id from callback_data: "topic_42"
    topic_id = int(query.data.split("_")[1])
    context.user_data["schedule_topic_id"] = topic_id

    await query.edit_message_text(
        t("schedule_type_prompt", lang),
        reply_markup=schedule_type_keyboard(lang),
    )
    return STATE_SCHEDULE_TYPE


async def select_schedule_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle schedule type selection (interval or fixed time)."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_TYPE

    await query.answer()

    lang = _lang(update)

    if query.data == "stype_interval":
        await query.edit_message_text(
            t("select_interval", lang),
            reply_markup=interval_keyboard(),
        )
        return STATE_SCHEDULE_INTERVAL

    if query.data == "stype_fixed":
        await query.edit_message_text(
            t("select_hour", lang),
            reply_markup=hour_keyboard(),
        )
        return STATE_SCHEDULE_HOUR

    if query.data == "stype_remove":
        topic_id = context.user_data.get("schedule_topic_id")
        if topic_id is None:
            await query.edit_message_text(t("schedule_no_topic", lang))
            return STATE_MAIN_MENU

        schedule_service: ScheduleService = context.bot_data["schedule_service"]
        await schedule_service.remove_schedule(topic_id)
        remove_job(f"photo_{topic_id}", context)

        await query.edit_message_text(t("schedule_removed", lang), parse_mode="MarkdownV2")
        await context.bot.send_message(
            chat_id=query.from_user.id,
            text=t("menu_continue", lang),
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    return STATE_SCHEDULE_TYPE


async def select_interval_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle interval selection."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_INTERVAL

    await query.answer()

    lang = _lang(update)

    seconds = int(query.data.split("_")[1])
    topic_id = context.user_data.get("schedule_topic_id")

    if not topic_id:
        await query.edit_message_text(t("schedule_topic_error", lang))
        return STATE_MAIN_MENU

    schedule_service: ScheduleService = context.bot_data["schedule_service"]
    await schedule_service.set_interval_schedule(topic_id=topic_id, seconds=seconds)

    # Register the job
    chat_id = update.effective_chat.id if update.effective_chat else None
    _register_interval_job(context, topic_id, seconds, chat_id)

    await query.edit_message_text(
        t("schedule_interval_set", lang, interval=_format_interval(seconds, lang)),
        parse_mode="MarkdownV2",
    )
    return STATE_MAIN_MENU


async def select_hour_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle hour selection for fixed-time schedule."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_HOUR

    await query.answer()

    lang = _lang(update)

    hour = int(query.data.split("_")[1])
    context.user_data["schedule_hour"] = hour

    await query.edit_message_text(
        t("select_minute", lang, hour=f"{hour:02d}"),
        reply_markup=minute_keyboard(),
    )
    return STATE_SCHEDULE_MINUTE


async def select_minute_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle minute selection for fixed-time schedule."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_SCHEDULE_MINUTE

    await query.answer()

    lang = _lang(update)

    minute = int(query.data.split("_")[1])
    hour = context.user_data.get("schedule_hour", 0)
    topic_id = context.user_data.get("schedule_topic_id")

    if not topic_id:
        await query.edit_message_text(t("schedule_topic_error", lang))
        return STATE_MAIN_MENU

    schedule_service: ScheduleService = context.bot_data["schedule_service"]
    await schedule_service.set_fixed_time_schedule(topic_id=topic_id, hour=hour, minute=minute)

    # Register the daily job
    chat_id = update.effective_chat.id if update.effective_chat else None
    _register_daily_job(context, topic_id, hour, minute, chat_id)

    await query.edit_message_text(
        t("schedule_fixed_set", lang, time=f"{hour:02d}:{minute:02d}"),
        parse_mode="MarkdownV2",
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
    remove_job(job_name, context)
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
    remove_job(job_name, context)
    context.job_queue.run_daily(  # type: ignore[union-attr]
        _send_scheduled_photo,
        time=datetime.time(hour=hour, minute=minute, tzinfo=datetime.UTC),
        name=job_name,
        data={"topic_id": topic_id},
        chat_id=chat_id,
    )


async def _send_scheduled_photo(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: fetch and send a photo for a scheduled topic."""
    from src.service.photo_service import PhotoService

    job = context.job
    if not job or not job.data or not job.chat_id:
        return

    topic_id = job.data["topic_id"]
    photo_service: PhotoService = context.bot_data["photo_service"]
    schedule_service: ScheduleService = context.bot_data["schedule_service"]
    topic_service: TopicService = context.bot_data["topic_service"]

    result = await topic_service.get_topic_with_language(topic_id)
    if not result:
        logger.warning("Topic %d not found or inactive, skipping.", topic_id)
        return

    topic_name, language_code = result

    try:
        photo = await photo_service.get_photo(
            topic=topic_name,
            topic_id=topic_id,
            language_code=language_code,
        )
    except Exception:
        logger.exception("Failed to fetch photo for topic '%s'", topic_name)
        return

    prefs = await topic_service.get_metadata_prefs(topic_id)

    caption = build_photo_caption(photo, topic_name, language_code, prefs)

    try:
        await context.bot.send_photo(
            chat_id=job.chat_id,
            photo=photo.url,
            caption=caption,
            parse_mode="MarkdownV2",
        )
    except Forbidden:
        try:
            topic = await topic_service.get_topic(topic_id)
            if topic:
                count = await deactivate_all_user_schedules(
                    topic.user_id, topic_service, schedule_service, context,
                )
                logger.warning(
                    "User blocked bot (chat_id=%d). Deactivated %d schedule(s) for user_id=%d.",
                    job.chat_id,
                    count,
                    topic.user_id,
                )
            else:
                logger.warning(
                    "User blocked bot (chat_id=%d). Topic %d not found, removing its job.",
                    job.chat_id,
                    topic_id,
                )
                await schedule_service.remove_schedule(topic_id)
                remove_job(f"photo_{topic_id}", context)
        except Exception:
            logger.exception(
                "Failed to handle Forbidden error for chat_id=%d, topic_id=%d",
                job.chat_id,
                topic_id,
            )
        return
    except Exception:
        logger.exception("Failed to send photo to chat %d", job.chat_id)
        return

    # Update last_sent_at
    schedule = await schedule_service.get_schedule(topic_id)
    if schedule and schedule.id:
        await schedule_service.mark_sent(schedule.id)


def _format_interval(seconds: int, language_code: str | None = None) -> str:
    """Format seconds into a localized human-readable interval string."""
    if seconds < 3600:
        return t("interval_minutes", language_code, count=seconds // 60)
    hours = seconds // 3600
    return t("interval_hours", language_code, count=hours)

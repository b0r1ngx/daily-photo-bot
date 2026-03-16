"""Quick action commands (/photo, /stop). Layer: Runtime."""

from __future__ import annotations

import logging
import random

from telegram import Update
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.config.constants import STATE_MAIN_MENU
from src.config.i18n import t
from src.runtime.job_utils import remove_job
from src.runtime.keyboards import main_menu_keyboard
from src.service.photo_service import PhotoService
from src.service.schedule_service import ScheduleService
from src.service.topic_service import TopicService

logger = logging.getLogger(__name__)


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Handle /photo — send an instant photo from a random user topic."""
    if not update.message:
        return None

    lang = _lang(update)
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text(t("use_start_first", lang))
        return None

    topic_service: TopicService = context.bot_data["topic_service"]
    photo_service: PhotoService = context.bot_data["photo_service"]

    topics = await topic_service.get_user_topics(user_id)

    if not topics:
        await update.message.reply_text(
            t("photo_no_topics", lang),
            reply_markup=main_menu_keyboard(),
        )
        return None

    topic = random.choice(topics)

    # Get language-aware topic name for better search enrichment
    topic_data = await topic_service.get_topic_with_language(topic.id)
    if not topic_data:
        await update.message.reply_text(
            t("photo_error", lang),
            reply_markup=main_menu_keyboard(),
        )
        return None

    topic_name, language_code = topic_data

    try:
        photo = await photo_service.get_photo(
            topic=topic_name,
            topic_id=topic.id,
            language_code=language_code,
        )
    except Exception:
        logger.exception("Failed to fetch photo for topic '%s'", topic_name)
        await update.message.reply_text(
            t("photo_error", lang),
            reply_markup=main_menu_keyboard(),
        )
        return None

    photographer = escape_markdown(photo.photographer, version=2)
    source_display = escape_markdown(photo.source.title(), version=2)
    url_safe = photo.source_url.replace("\\", "\\\\").replace(")", "\\)")
    source_with_link = f"[{source_display}]({url_safe})"

    caption = t(
        "photo_caption",
        language_code,
        name=escape_markdown(topic_name, version=2),
        photographer=photographer,
        source=source_with_link,
    )

    try:
        await update.message.reply_photo(
            photo=photo.url,
            caption=caption,
            parse_mode="MarkdownV2",
        )
    except Exception:
        logger.exception("Failed to send photo to user")
        await update.message.reply_text(
            t("photo_error", lang),
            reply_markup=main_menu_keyboard(),
        )

    return None


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /stop — pause all scheduled photo deliveries."""
    if not update.message:
        return STATE_MAIN_MENU

    lang = _lang(update)
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text(t("use_start_first", lang))
        return STATE_MAIN_MENU

    topic_service: TopicService = context.bot_data["topic_service"]
    schedule_service: ScheduleService = context.bot_data["schedule_service"]

    topics = await topic_service.get_user_topics(user_id)
    stopped_count = 0

    for topic in topics:
        try:
            schedule = await schedule_service.get_schedule(topic.id)
            if schedule and schedule.is_active:
                await schedule_service.remove_schedule(topic.id)
                remove_job(f"photo_{topic.id}", context)
                stopped_count += 1
        except Exception:
            logger.exception(
                "Failed to remove schedule for topic %d",
                topic.id,
            )

    if stopped_count == 0:
        await update.message.reply_text(
            t("stop_no_schedules", lang),
            reply_markup=main_menu_keyboard(),
        )
    else:
        await update.message.reply_text(
            t("stop_success", lang, count=stopped_count),
            parse_mode="MarkdownV2",
            reply_markup=main_menu_keyboard(),
        )

    return STATE_MAIN_MENU

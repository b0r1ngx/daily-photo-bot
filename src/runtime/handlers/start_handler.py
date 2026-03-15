"""Start/onboarding handler. Layer: Runtime."""
from __future__ import annotations

import logging

import httpx
from telegram import Update
from telegram.error import TelegramError
from telegram.ext import ContextTypes
from telegram.helpers import escape_markdown

from src.config.constants import STATE_AWAITING_TOPIC, STATE_MAIN_MENU
from src.config.i18n import t
from src.runtime.keyboards import main_menu_keyboard
from src.service.photo_service import PhotoService
from src.service.topic_service import TopicService
from src.types.exceptions import PhotoNotFoundError, PhotoSourceError

logger = logging.getLogger(__name__)


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /start command. Ask user for their first topic."""
    if not update.effective_user or not update.message:
        return STATE_AWAITING_TOPIC

    user = update.effective_user
    lang = user.language_code
    topic_service: TopicService = context.bot_data["topic_service"]

    db_user = await topic_service.ensure_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name,
        language_code=lang,
    )
    context.user_data["db_user_id"] = db_user.id

    # Check if user already has topics
    topics = await topic_service.get_user_topics(db_user.id)
    if topics:
        context.user_data.pop("paid_topic_pending", None)
        await update.message.reply_text(
            t("welcome_back", lang, count=len(topics)),
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    await update.message.reply_text(t("welcome_new", lang))
    return STATE_AWAITING_TOPIC


async def receive_first_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle the user's first topic input."""
    if not update.message or not update.message.text:
        return STATE_AWAITING_TOPIC

    lang = _lang(update)
    topic_name = update.message.text.strip()
    topic_service: TopicService = context.bot_data["topic_service"]
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text(t("use_start_first", lang))
        return STATE_AWAITING_TOPIC

    try:
        topic = await topic_service.add_topic(user_id=user_id, name=topic_name)
    except ValueError as exc:
        await update.message.reply_text(t("error_try_again", lang, error=str(exc)))
        return STATE_AWAITING_TOPIC

    await update.message.reply_text(
        t("topic_added_with_schedule_hint", lang, name=escape_markdown(topic.name)),
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )

    # Send first photo as a preview (best-effort, don't break the flow)
    if topic.id is not None:
        try:
            photo_service: PhotoService = context.bot_data["photo_service"]
            photo = await photo_service.get_photo(
                topic=topic.name, topic_id=topic.id, language_code=lang,
            )
            await update.message.reply_photo(
                photo=photo.url,
                caption=t("first_photo_caption", lang, name=escape_markdown(topic.name)),
                parse_mode="Markdown",
            )
        except (PhotoNotFoundError, PhotoSourceError, httpx.HTTPError, TelegramError) as exc:
            logger.warning("Could not send first preview photo for topic '%s': %s", topic.name, exc)

    return STATE_MAIN_MENU

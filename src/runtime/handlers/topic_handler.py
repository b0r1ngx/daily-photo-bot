"""Topic management handler. Layer: Runtime."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import STATE_AWAITING_NEW_TOPIC, STATE_MAIN_MENU
from src.runtime.keyboards import main_menu_keyboard
from src.service.payment_service import PaymentService
from src.service.topic_service import TopicService
from src.types.exceptions import TopicLimitError

logger = logging.getLogger(__name__)


async def add_topic_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle '➕ Add topic' button press."""
    if not update.message:
        return STATE_MAIN_MENU

    topic_service: TopicService = context.bot_data["topic_service"]
    payment_service: PaymentService = context.bot_data["payment_service"]
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text("Please use /start first.")
        return STATE_MAIN_MENU

    can_free = await topic_service.can_add_free_topic(user_id)

    if can_free:
        await update.message.reply_text(
            "📝 Type the name of your new topic (e.g., sunsets, puppies):"
        )
        return STATE_AWAITING_NEW_TOPIC

    # Need to pay — send invoice
    telegram_id = update.effective_user.id if update.effective_user else 0
    params = payment_service.create_invoice_params(user_id=telegram_id)
    await update.message.reply_invoice(
        title=params["title"],
        description=params["description"],
        payload=params["payload"],
        currency=params["currency"],
        prices=params["prices"],
    )
    return STATE_MAIN_MENU  # Payment flow will handle the rest via separate handlers


async def receive_new_topic(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new topic name input."""
    if not update.message or not update.message.text:
        return STATE_AWAITING_NEW_TOPIC

    topic_name = update.message.text.strip()
    topic_service: TopicService = context.bot_data["topic_service"]
    user_id = context.user_data.get("db_user_id")

    if not user_id:
        await update.message.reply_text("Please use /start first.")
        return STATE_MAIN_MENU

    # Determine if this should be free or paid
    is_free = await topic_service.can_add_free_topic(user_id)

    try:
        topic = await topic_service.add_topic(
            user_id=user_id, name=topic_name, is_free=is_free
        )
    except ValueError as exc:
        await update.message.reply_text(f"❌ {exc}\n\nPlease try again:")
        return STATE_AWAITING_NEW_TOPIC
    except TopicLimitError:
        await update.message.reply_text(
            "❌ You've reached the free topic limit. Please pay to add more.",
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    await update.message.reply_text(
        f"✅ Topic *{topic.name}* added! Now set up a schedule for it.",
        reply_markup=main_menu_keyboard(),
        parse_mode="Markdown",
    )
    return STATE_MAIN_MENU

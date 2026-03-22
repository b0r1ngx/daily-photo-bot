"""Share/subscribe/unsubscribe handlers. Layer: Runtime."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import STATE_MAIN_MENU, STATE_TOPIC_MANAGE
from src.config.i18n import t
from src.config.settings import FREE_SHARES_PER_TOPIC
from src.runtime.keyboards import main_menu_keyboard, share_confirm_keyboard
from src.service.share_service import ShareService
from src.service.topic_service import TopicService
from src.types.exceptions import InvalidShareTokenError, ShareLimitError

logger = logging.getLogger(__name__)


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


# ---------------------------------------------------------------------------
# Owner-side: "Share" button in topic manage view
# ---------------------------------------------------------------------------


async def share_topic_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Handle 'Share' button from topic manage view — generate and show link."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_TOPIC_MANAGE
    await query.answer()

    lang = _lang(update)

    try:
        topic_id = int(query.data.split("_", 1)[1])
    except (IndexError, ValueError):
        await query.edit_message_text(t("invalid_selection", lang))
        return STATE_TOPIC_MANAGE

    topic_service: TopicService = context.bot_data["topic_service"]
    share_service: ShareService = context.bot_data["share_service"]

    # IDOR check — verify ownership
    user = await topic_service.ensure_user(
        telegram_id=query.from_user.id,
        username=query.from_user.username or "",
        first_name=query.from_user.first_name or "",
        language_code=query.from_user.language_code,
    )
    topic = await topic_service.get_topic(topic_id)
    if not topic or not user.id or topic.user_id != user.id:
        await query.edit_message_text(t("topic_not_found", lang))
        return STATE_TOPIC_MANAGE

    # Check if user has a paid_share_pending flag for this topic
    paid_pending = context.user_data.get("paid_share_pending")
    if paid_pending == topic_id:
        context.user_data.pop("paid_share_pending", None)
        # Paid share: bypass free limit by temporarily not checking it
        # The service.subscribe() will check the actual count;
        # for paid flow, we just increase the effective limit.
        # For now, generate the link regardless — the limit is checked on accept.

    # Generate the share link
    bot_username = (await context.bot.get_me()).username or ""
    link = await share_service.get_share_link(topic_id, bot_username)
    sub_count = await share_service.get_subscriber_count(topic_id)

    can_share = sub_count < FREE_SHARES_PER_TOPIC

    if can_share or paid_pending == topic_id:
        await query.edit_message_text(
            t("share_link_text", lang, link=link),
        )
    else:
        await query.edit_message_text(
            t("share_limit_reached", lang),
        )

    return STATE_TOPIC_MANAGE


# ---------------------------------------------------------------------------
# Subscriber-side: deep link handler (called from start_handler)
# ---------------------------------------------------------------------------


async def handle_share_deep_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    token: str,
) -> int:
    """Process a share deep link — show confirmation prompt.

    Called from start_command when /start share_{token} is detected.
    """
    if not update.message or not update.effective_user:
        return STATE_MAIN_MENU

    lang = _lang(update)
    share_service: ShareService = context.bot_data["share_service"]
    topic_service: TopicService = context.bot_data["topic_service"]

    # Validate token
    try:
        topic_id = await share_service.validate_token(token)
    except InvalidShareTokenError:
        await update.message.reply_text(
            t("share_invalid_token", lang),
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    # Get topic name for the prompt
    topic = await topic_service.get_topic(topic_id)
    if not topic:
        await update.message.reply_text(
            t("share_invalid_token", lang),
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    # Show confirmation with accept/decline inline buttons
    await update.message.reply_text(
        t("share_confirm_prompt", lang, name=topic.name),
        reply_markup=share_confirm_keyboard(token, lang),
    )
    return STATE_MAIN_MENU


# ---------------------------------------------------------------------------
# Standalone callback handlers (registered outside ConversationHandler)
# ---------------------------------------------------------------------------


async def share_accept_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle 'Yes, subscribe' button press."""
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    lang = _lang(update)

    # Parse token from callback data: "shareaccept_{token}"
    token = query.data.split("_", 1)[1]

    share_service: ShareService = context.bot_data["share_service"]
    topic_service: TopicService = context.bot_data["topic_service"]

    try:
        subscription = await share_service.subscribe(
            token=token,
            subscriber_telegram_id=query.from_user.id,
        )
    except InvalidShareTokenError:
        await query.edit_message_text(t("share_invalid_token", lang))
        return
    except ShareLimitError:
        await query.edit_message_text(t("share_limit_reached", lang))
        return
    except ValueError as exc:
        error_str = str(exc)
        if "own topic" in error_str:
            await query.edit_message_text(t("share_own_topic", lang))
        elif "Already subscribed" in error_str:
            await query.edit_message_text(t("share_already_subscribed", lang))
        else:
            await query.edit_message_text(t("share_invalid_token", lang))
        return

    topic = await topic_service.get_topic(subscription.topic_id)
    topic_name = topic.name if topic else "Unknown"

    await query.edit_message_text(
        t("share_accepted", lang, name=topic_name),
    )


async def share_decline_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """Handle 'No thanks' button press."""
    query = update.callback_query
    if not query:
        return
    await query.answer()

    lang = _lang(update)
    await query.edit_message_text(t("share_declined", lang))

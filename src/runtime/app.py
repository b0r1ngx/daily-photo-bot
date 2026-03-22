"""Application builder and handler registration. Layer: Runtime."""

from __future__ import annotations

import re

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from src.config.constants import (
    KB_ADD_TOPIC,
    KB_MY_TOPICS,
    KB_SCHEDULE,
    STATE_AWAITING_NEW_TOPIC,
    STATE_AWAITING_TOPIC,
    STATE_EDIT_TOPIC_NAME,
    STATE_MAIN_MENU,
    STATE_METADATA_SETTINGS,
    STATE_SCHEDULE_HOUR,
    STATE_SCHEDULE_INTERVAL,
    STATE_SCHEDULE_MINUTE,
    STATE_SCHEDULE_SELECT_TOPIC,
    STATE_SCHEDULE_TYPE,
    STATE_TOPIC_MANAGE,
)
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.runtime.handlers.analytics_handler import analytics_command
from src.runtime.handlers.help_handler import (
    cancel_command,
    help_command,
    unknown_message,
    version_command,
)
from src.runtime.handlers.payment_handler import (
    pre_checkout_callback,
    successful_payment_callback,
)
from src.runtime.handlers.quick_commands_handler import photo_command, stop_command
from src.runtime.handlers.schedule_handler import (
    schedule_menu,
    select_hour_callback,
    select_interval_callback,
    select_minute_callback,
    select_schedule_type_callback,
    select_topic_callback,
)
from src.runtime.handlers.share_handler import (
    share_accept_callback,
    share_decline_callback,
    share_topic_callback,
)
from src.runtime.handlers.start_handler import receive_first_topic, start_command
from src.runtime.handlers.topic_handler import add_topic_menu, receive_new_topic
from src.runtime.handlers.topic_manage_handler import (
    delete_topic_callback,
    metaback_callback,
    metatoggle_callback,
    my_topics_menu,
    receive_new_topic_name,
    rename_topic_callback,
    schedule_from_topics_callback,
    settings_callback,
)


def build_application() -> Application:  # type: ignore[type-arg]
    """Build and configure the Telegram bot application."""
    app: Application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()  # type: ignore[type-arg]

    # Escape button labels for safe regex matching
    add_topic_pattern = f"^{re.escape(KB_ADD_TOPIC)}$"
    my_topics_pattern = f"^{re.escape(KB_MY_TOPICS)}$"
    schedule_pattern = f"^{re.escape(KB_SCHEDULE)}$"

    # Main conversation handler
    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start_command),
            MessageHandler(filters.Regex(add_topic_pattern), add_topic_menu),
            MessageHandler(filters.Regex(my_topics_pattern), my_topics_menu),
            MessageHandler(filters.Regex(schedule_pattern), schedule_menu),
        ],
        states={
            STATE_AWAITING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_first_topic),
            ],
            STATE_MAIN_MENU: [
                MessageHandler(filters.Regex(add_topic_pattern), add_topic_menu),
                MessageHandler(filters.Regex(my_topics_pattern), my_topics_menu),
                MessageHandler(filters.Regex(schedule_pattern), schedule_menu),
                MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_message),
            ],
            STATE_AWAITING_NEW_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_topic),
            ],
            STATE_SCHEDULE_SELECT_TOPIC: [
                CallbackQueryHandler(select_topic_callback, pattern=r"^topic_\d+$"),
            ],
            STATE_SCHEDULE_TYPE: [
                CallbackQueryHandler(select_schedule_type_callback, pattern=r"^stype_"),
            ],
            STATE_SCHEDULE_INTERVAL: [
                CallbackQueryHandler(select_interval_callback, pattern=r"^interval_\d+$"),
            ],
            STATE_SCHEDULE_HOUR: [
                CallbackQueryHandler(select_hour_callback, pattern=r"^hour_\d+$"),
            ],
            STATE_SCHEDULE_MINUTE: [
                CallbackQueryHandler(select_minute_callback, pattern=r"^minute_\d+$"),
            ],
            STATE_TOPIC_MANAGE: [
                CallbackQueryHandler(
                    schedule_from_topics_callback, pattern=r"^schedule_\d+$",
                ),
                CallbackQueryHandler(settings_callback, pattern=r"^settings_\d+$"),
                CallbackQueryHandler(share_topic_callback, pattern=r"^share_\d+$"),
                CallbackQueryHandler(delete_topic_callback, pattern=r"^delete_\d+$"),
                CallbackQueryHandler(rename_topic_callback, pattern=r"^rename_\d+$"),
            ],
            STATE_METADATA_SETTINGS: [
                CallbackQueryHandler(
                    metatoggle_callback, pattern=r"^metatoggle_\w+_\d+$",
                ),
                CallbackQueryHandler(metaback_callback, pattern=r"^metaback_\d+$"),
            ],
            STATE_EDIT_TOPIC_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_new_topic_name),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
            CommandHandler("version", version_command),
            CommandHandler("photo", photo_command),
            CommandHandler("stop", stop_command),
            MessageHandler(filters.Regex(add_topic_pattern), add_topic_menu),
            MessageHandler(filters.Regex(my_topics_pattern), my_topics_menu),
            MessageHandler(filters.Regex(schedule_pattern), schedule_menu),
        ],
    )

    app.add_handler(conv_handler)

    # Help command (outside conversation)
    app.add_handler(CommandHandler("help", help_command))

    # Analytics command (outside conversation, restricted to admin group)
    app.add_handler(CommandHandler("analytics", analytics_command))

    # Payment handlers (must be outside conversation handler)
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))

    # Share accept/decline handlers (standalone, outside conversation handler)
    app.add_handler(CallbackQueryHandler(share_accept_callback, pattern=r"^shareaccept_"))
    app.add_handler(CallbackQueryHandler(share_decline_callback, pattern=r"^sharedecline_"))

    return app

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
    KB_SCHEDULE,
    STATE_AWAITING_NEW_TOPIC,
    STATE_AWAITING_TOPIC,
    STATE_MAIN_MENU,
    STATE_SCHEDULE_HOUR,
    STATE_SCHEDULE_INTERVAL,
    STATE_SCHEDULE_MINUTE,
    STATE_SCHEDULE_SELECT_TOPIC,
    STATE_SCHEDULE_TYPE,
)
from src.config.settings import TELEGRAM_BOT_TOKEN
from src.runtime.handlers.help_handler import cancel_command, help_command, unknown_message
from src.runtime.handlers.payment_handler import (
    pre_checkout_callback,
    successful_payment_callback,
)
from src.runtime.handlers.schedule_handler import (
    schedule_menu,
    select_hour_callback,
    select_interval_callback,
    select_minute_callback,
    select_schedule_type_callback,
    select_topic_callback,
)
from src.runtime.handlers.start_handler import receive_first_topic, start_command
from src.runtime.handlers.topic_handler import add_topic_menu, receive_new_topic


def build_application() -> Application:  # type: ignore[type-arg]
    """Build and configure the Telegram bot application."""
    app: Application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()  # type: ignore[type-arg]

    # Escape button labels for safe regex matching
    add_topic_pattern = f"^{re.escape(KB_ADD_TOPIC)}$"
    schedule_pattern = f"^{re.escape(KB_SCHEDULE)}$"

    # Main conversation handler
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start_command)],
        states={
            STATE_AWAITING_TOPIC: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_first_topic),
            ],
            STATE_MAIN_MENU: [
                MessageHandler(filters.Regex(add_topic_pattern), add_topic_menu),
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
                CallbackQueryHandler(
                    select_schedule_type_callback, pattern=r"^stype_"
                ),
            ],
            STATE_SCHEDULE_INTERVAL: [
                CallbackQueryHandler(
                    select_interval_callback, pattern=r"^interval_\d+$"
                ),
            ],
            STATE_SCHEDULE_HOUR: [
                CallbackQueryHandler(select_hour_callback, pattern=r"^hour_\d+$"),
            ],
            STATE_SCHEDULE_MINUTE: [
                CallbackQueryHandler(
                    select_minute_callback, pattern=r"^minute_\d+$"
                ),
            ],
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command),
            CommandHandler("start", start_command),
        ],
    )

    app.add_handler(conv_handler)

    # Help command (outside conversation)
    app.add_handler(CommandHandler("help", help_command))

    # Payment handlers (must be outside conversation handler)
    app.add_handler(PreCheckoutQueryHandler(pre_checkout_callback))
    app.add_handler(
        MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback)
    )

    return app

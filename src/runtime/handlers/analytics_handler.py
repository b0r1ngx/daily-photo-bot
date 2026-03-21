"""Analytics handler. Layer: Runtime.

Sends a daily analytics report to the configured admin group.
"""
from __future__ import annotations

import logging

from telegram.ext import ContextTypes

from src.service.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)


async def send_daily_analytics(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback: collect analytics and send report to admin group.

    This callback is registered as a daily job in main.py.
    If anything fails, it logs the error but never crashes the bot.
    """
    from src.config.settings import ANALYTICS_GROUP_ID

    if ANALYTICS_GROUP_ID is None:
        return

    try:
        analytics_service: AnalyticsService = context.bot_data["analytics_service"]
        snapshot = await analytics_service.collect_snapshot()
        message = analytics_service.format_message(snapshot)

        await context.bot.send_message(
            chat_id=ANALYTICS_GROUP_ID,
            text=message,
            parse_mode="HTML",
        )
        logger.info("Daily analytics report sent to group %d.", ANALYTICS_GROUP_ID)
    except Exception:
        logger.exception("Failed to send daily analytics report.")

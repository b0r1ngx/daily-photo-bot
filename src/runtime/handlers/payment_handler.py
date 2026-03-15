"""Payment handler for Telegram Stars. Layer: Runtime."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config.i18n import t
from src.service.payment_service import PaymentService

logger = logging.getLogger(__name__)


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


async def pre_checkout_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle pre-checkout query — verify and approve payment."""
    query = update.pre_checkout_query
    if not query:
        return

    payment_service: PaymentService = context.bot_data["payment_service"]
    user_id = query.from_user.id
    lang = query.from_user.language_code if query.from_user else None

    if payment_service.verify_payment(query.invoice_payload, user_id):
        await query.answer(ok=True)
    else:
        await query.answer(ok=False, error_message=t("payment_failed", lang))


async def successful_payment_callback(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle successful payment — allow user to add a new topic."""
    if not update.message or not update.message.successful_payment:
        return

    logger.info(
        "Payment received from user %s: %s %s",
        update.effective_user.id if update.effective_user else "unknown",
        update.message.successful_payment.total_amount,
        update.message.successful_payment.currency,
    )

    # Mark that user can add a paid topic
    context.user_data["paid_topic_pending"] = True

    await update.message.reply_text(t("payment_success", _lang(update)))

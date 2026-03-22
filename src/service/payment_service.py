"""Payment service for Telegram Stars. Layer: Service (depends on: types, config)."""
from __future__ import annotations

import logging

from src.config.settings import SHARE_STAR_PRICE, STAR_PRICE
from src.types.payment import PaymentInfo

logger = logging.getLogger(__name__)


class PaymentService:
    """Handles Telegram Stars payment logic."""

    def create_invoice_params(self, user_id: int) -> dict[str, object]:
        """Create parameters for a Telegram Stars invoice.

        Returns a dict suitable for passing to telegram.Bot.send_invoice().
        """
        info = PaymentInfo(
            user_id=user_id,
            amount=STAR_PRICE,
            currency="XTR",
            description="Unlock an additional photo topic",
        )
        return {
            "title": "\u2795 Extra Photo Topic",
            "description": info.description,
            "payload": f"topic_unlock_{user_id}",
            "currency": info.currency,
            "prices": [{"label": "1 extra topic", "amount": info.amount}],
        }

    def verify_payment(self, payload: str, user_id: int) -> bool:
        """Verify that a payment payload matches the expected user.

        Args:
            payload: The payment payload string from Telegram.
            user_id: The Telegram user ID to verify against.

        Returns:
            True if the payload is valid for this user.
        """
        expected = f"topic_unlock_{user_id}"
        is_valid = payload == expected
        if is_valid:
            logger.info("Payment verified for user_id=%d", user_id)
        else:
            logger.warning(
                "Payment verification failed: payload='%s', expected='%s'",
                payload,
                expected,
            )
        return is_valid

    def create_share_invoice_params(
        self, user_id: int, topic_id: int,
    ) -> dict[str, object]:
        """Create parameters for a Telegram Stars invoice to unlock extra share slots.

        Returns a dict suitable for passing to telegram.Bot.send_invoice().
        """
        info = PaymentInfo(
            user_id=user_id,
            amount=SHARE_STAR_PRICE,
            currency="XTR",
            description="Unlock an additional subscriber slot for your topic",
        )
        return {
            "title": "\U0001f517 Extra Share Slot",
            "description": info.description,
            "payload": f"share_unlock_{user_id}_{topic_id}",
            "currency": info.currency,
            "prices": [{"label": "1 extra share slot", "amount": info.amount}],
        }

    def verify_share_payment(self, payload: str, user_id: int) -> int | None:
        """Verify a share payment payload.

        Args:
            payload: The payment payload string from Telegram.
            user_id: The Telegram user ID to verify against.

        Returns:
            The topic_id if the payload is valid, None otherwise.
        """
        prefix = f"share_unlock_{user_id}_"
        if payload.startswith(prefix):
            try:
                topic_id = int(payload[len(prefix):])
                logger.info(
                    "Share payment verified for user_id=%d, topic_id=%d",
                    user_id,
                    topic_id,
                )
                return topic_id
            except ValueError:
                pass
        return None

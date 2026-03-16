"""Payment data models. Layer: Types (zero dependencies)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentInfo:
    """Telegram Stars payment information."""

    user_id: int
    amount: int
    currency: str = "XTR"
    description: str = "Extra photo topic"

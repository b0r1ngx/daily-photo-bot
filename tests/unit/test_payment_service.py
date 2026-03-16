"""Unit tests for PaymentService."""
from __future__ import annotations

from src.service.payment_service import PaymentService


def test_create_invoice_params():
    service = PaymentService()
    params = service.create_invoice_params(user_id=12345)
    assert params["title"] == "\u2795 Extra Photo Topic"
    assert params["currency"] == "XTR"
    assert params["payload"] == "topic_unlock_12345"
    assert len(params["prices"]) == 1
    assert params["prices"][0]["amount"] == 1  # STAR_PRICE default


def test_verify_payment_valid():
    service = PaymentService()
    assert service.verify_payment("topic_unlock_12345", user_id=12345) is True


def test_verify_payment_invalid():
    service = PaymentService()
    assert service.verify_payment("topic_unlock_99999", user_id=12345) is False


def test_verify_payment_garbage():
    service = PaymentService()
    assert service.verify_payment("garbage", user_id=12345) is False

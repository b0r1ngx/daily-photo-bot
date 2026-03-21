"""Unit tests for AnalyticsService."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.service.analytics_service import AnalyticsService
from src.types.analytics import AnalyticsSnapshot


@pytest.fixture
def analytics_repo():
    repo = AsyncMock()
    repo.get_total_users.return_value = 100
    repo.get_users_by_language.return_value = {"en": 80, "ru": 15, "unknown": 5}
    repo.get_active_user_count.return_value = 25
    repo.get_paid_user_count.return_value = 3
    repo.get_api_requests_since.side_effect = lambda source, _: 150 if source == "pexels" else 30
    repo.get_photos_sent_since.return_value = 45
    repo.cleanup_old_api_requests.return_value = 0
    return repo


@pytest.fixture
def service(analytics_repo):
    return AnalyticsService(analytics_repo=analytics_repo)


@pytest.mark.asyncio
async def test_collect_snapshot_returns_all_fields(service: AnalyticsService):
    snapshot = await service.collect_snapshot()
    assert isinstance(snapshot, AnalyticsSnapshot)
    assert snapshot.total_users == 100
    assert snapshot.users_by_language == {"en": 80, "ru": 15, "unknown": 5}
    assert snapshot.active_users == 25
    assert snapshot.paid_users == 3
    assert snapshot.pexels_requests_today == 150
    assert snapshot.unsplash_requests_today == 30
    assert snapshot.photos_sent_today == 45
    assert snapshot.generated_at  # non-empty ISO string


@pytest.mark.asyncio
async def test_collect_snapshot_empty_database(analytics_repo):
    analytics_repo.get_total_users.return_value = 0
    analytics_repo.get_users_by_language.return_value = {}
    analytics_repo.get_active_user_count.return_value = 0
    analytics_repo.get_paid_user_count.return_value = 0
    analytics_repo.get_api_requests_since.return_value = 0
    analytics_repo.get_photos_sent_since.return_value = 0
    service = AnalyticsService(analytics_repo=analytics_repo)
    snapshot = await service.collect_snapshot()
    assert snapshot.total_users == 0
    assert snapshot.active_users == 0
    assert snapshot.photos_sent_today == 0


@pytest.mark.asyncio
async def test_collect_snapshot_triggers_cleanup(
    service: AnalyticsService, analytics_repo,
):
    await service.collect_snapshot()
    analytics_repo.cleanup_old_api_requests.assert_awaited_once()


def test_format_message_contains_all_sections(service: AnalyticsService):
    snapshot = AnalyticsSnapshot(
        total_users=100,
        users_by_language={"en": 80, "ru": 20},
        active_users=25,
        paid_users=3,
        pexels_requests_today=150,
        unsplash_requests_today=30,
        photos_sent_today=45,
        generated_at="2026-03-21T00:00:00+00:00",
    )
    msg = service.format_message(snapshot)
    assert "100" in msg  # total users
    assert "25" in msg  # active users
    assert "3" in msg  # paid users
    assert "150" in msg  # pexels
    assert "30" in msg  # unsplash
    assert "45" in msg  # photos sent
    assert "Daily Analytics Report" in msg


def test_format_message_language_flags(service: AnalyticsService):
    snapshot = AnalyticsSnapshot(
        total_users=100,
        users_by_language={"en": 80, "ru": 20},
        active_users=0,
        paid_users=0,
        pexels_requests_today=0,
        unsplash_requests_today=0,
        photos_sent_today=0,
        generated_at="2026-03-21T00:00:00+00:00",
    )
    msg = service.format_message(snapshot)
    assert "\U0001f1ec\U0001f1e7" in msg  # GB flag for en
    assert "\U0001f1f7\U0001f1fa" in msg  # RU flag for ru


def test_format_message_unknown_language(service: AnalyticsService):
    snapshot = AnalyticsSnapshot(
        total_users=1,
        users_by_language={"xx": 1},
        active_users=0,
        paid_users=0,
        pexels_requests_today=0,
        unsplash_requests_today=0,
        photos_sent_today=0,
        generated_at="2026-03-21T00:00:00+00:00",
    )
    msg = service.format_message(snapshot)
    assert "\U0001f3f3\ufe0f" in msg  # white flag for unknown


def test_format_message_empty_language_map(service: AnalyticsService):
    snapshot = AnalyticsSnapshot(
        total_users=0,
        users_by_language={},
        active_users=0,
        paid_users=0,
        pexels_requests_today=0,
        unsplash_requests_today=0,
        photos_sent_today=0,
        generated_at="2026-03-21T00:00:00+00:00",
    )
    msg = service.format_message(snapshot)
    assert "Total users" in msg
    assert "0" in msg


def test_format_message_zero_metrics(service: AnalyticsService):
    snapshot = AnalyticsSnapshot(
        total_users=0,
        users_by_language={},
        active_users=0,
        paid_users=0,
        pexels_requests_today=0,
        unsplash_requests_today=0,
        photos_sent_today=0,
        generated_at="2026-03-21T00:00:00+00:00",
    )
    msg = service.format_message(snapshot)
    # Should not crash, should produce a valid message
    assert isinstance(msg, str)
    assert len(msg) > 0

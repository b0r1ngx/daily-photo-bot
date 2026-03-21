"""Analytics service. Layer: Service (depends on: types, config).

Collects bot metrics and formats them for the daily admin report.
"""
from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from src.types.analytics import AnalyticsSnapshot
from src.types.protocols import AnalyticsRepository

logger = logging.getLogger(__name__)

# Language code -> flag emoji mapping (admin-facing display only)
_LANGUAGE_FLAGS: dict[str, str] = {
    "en": "\U0001f1ec\U0001f1e7",  # GB
    "es": "\U0001f1ea\U0001f1f8",  # ES
    "ru": "\U0001f1f7\U0001f1fa",  # RU
    "pt": "\U0001f1e7\U0001f1f7",  # BR
    "zh": "\U0001f1e8\U0001f1f3",  # CN
    "hi": "\U0001f1ee\U0001f1f3",  # IN
    "ar": "\U0001f1f8\U0001f1e6",  # SA
    "ms": "\U0001f1f2\U0001f1fe",  # MY
    "bn": "\U0001f1e7\U0001f1e9",  # BD
    "fr": "\U0001f1eb\U0001f1f7",  # FR
    "it": "\U0001f1ee\U0001f1f9",  # IT
    "de": "\U0001f1e9\U0001f1ea",  # DE
}
_UNKNOWN_FLAG = "\U0001f3f3\ufe0f"  # White flag


class AnalyticsService:
    """Collects and formats bot analytics."""

    def __init__(self, analytics_repo: AnalyticsRepository) -> None:
        self._repo = analytics_repo

    async def collect_snapshot(self) -> AnalyticsSnapshot:
        """Gather all analytics metrics into a point-in-time snapshot.

        Counts metrics for the previous 24 hours (midnight-to-midnight UTC).
        Also cleans up api_requests older than 30 days.
        """
        now = datetime.now(tz=UTC)
        yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d 00:00:00")

        # Cleanup old api_requests (30-day retention)
        cutoff = (now - timedelta(days=30)).strftime("%Y-%m-%d %H:%M:%S")
        deleted = await self._repo.cleanup_old_api_requests(cutoff)
        if deleted:
            logger.info("Cleaned up %d old api_request records.", deleted)

        total_users = await self._repo.get_total_users()
        users_by_language = await self._repo.get_users_by_language()
        active_users = await self._repo.get_active_user_count()
        paid_users = await self._repo.get_paid_user_count()
        pexels_requests = await self._repo.get_api_requests_since("pexels", yesterday)
        unsplash_requests = await self._repo.get_api_requests_since("unsplash", yesterday)
        photos_sent = await self._repo.get_photos_sent_since(yesterday)

        return AnalyticsSnapshot(
            total_users=total_users,
            users_by_language=users_by_language,
            active_users=active_users,
            paid_users=paid_users,
            pexels_requests_today=pexels_requests,
            unsplash_requests_today=unsplash_requests,
            photos_sent_today=photos_sent,
            generated_at=now.isoformat(),
        )

    def format_message(self, snapshot: AnalyticsSnapshot) -> str:
        """Format an analytics snapshot into a human-readable message (English only)."""
        lines: list[str] = []

        lines.append("<b>Daily Analytics Report</b>")
        lines.append("")

        # Users section
        lines.append(f"<b>Total users:</b> {snapshot.total_users}")

        if snapshot.users_by_language:
            lang_parts: list[str] = []
            for lang, count in snapshot.users_by_language.items():
                flag = _LANGUAGE_FLAGS.get(lang, _UNKNOWN_FLAG)
                lang_parts.append(f"{flag} {lang}: {count}")
            lines.append("  " + ", ".join(lang_parts))

        lines.append("")
        lines.append(f"<b>Active users</b> (with schedule): {snapshot.active_users}")
        lines.append(f"<b>Users with paid topics:</b> {snapshot.paid_users}")

        # API section
        lines.append("")
        lines.append("<b>API Requests (last 24h):</b>")
        lines.append(f"  Pexels: {snapshot.pexels_requests_today}")
        lines.append(f"  Unsplash: {snapshot.unsplash_requests_today}")

        # Photos section
        lines.append("")
        lines.append(f"<b>Photos sent (last 24h):</b> {snapshot.photos_sent_today}")

        return "\n".join(lines)

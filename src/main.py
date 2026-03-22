"""Bot entry point. Initializes all layers and starts polling."""
from __future__ import annotations

import asyncio
import datetime
import logging
import signal

from telegram.ext import Application

from src.config.logging import setup_logging
from src.config.settings import ANALYTICS_GROUP_ID, DATABASE_PATH
from src.service.schedule_service import ScheduleService
from src.service.topic_service import TopicService

logger = logging.getLogger(__name__)


async def _startup() -> None:
    """Initialize database, services, and start the bot."""
    from src.repo.analytics_repo import AnalyticsRepo
    from src.repo.database import get_connection, init_db
    from src.repo.schedule_repo import ScheduleRepo
    from src.repo.sent_photo_repo import SentPhotoRepo
    from src.repo.share_repo import ShareRepo
    from src.repo.topic_repo import TopicRepo
    from src.repo.user_repo import UserRepo
    from src.runtime.app import build_application
    from src.service.analytics_service import AnalyticsService
    from src.service.payment_service import PaymentService
    from src.service.photo_service import PhotoService
    from src.service.schedule_service import ScheduleService
    from src.service.share_service import ShareService
    from src.service.topic_service import TopicService

    # Initialize database
    db = await get_connection(DATABASE_PATH)
    await init_db(db)
    logger.info("Database initialized at %s", DATABASE_PATH)

    # Create repositories
    user_repo = UserRepo(db)
    topic_repo = TopicRepo(db)
    schedule_repo = ScheduleRepo(db)
    sent_photo_repo = SentPhotoRepo(db)
    analytics_repo = AnalyticsRepo(db)
    share_repo = ShareRepo(db)

    # Create services (inject repos)
    topic_service = TopicService(user_repo=user_repo, topic_repo=topic_repo)
    photo_service = PhotoService(
        sent_photo_repo=sent_photo_repo,
        api_request_recorder=analytics_repo,
    )
    schedule_service = ScheduleService(schedule_repo=schedule_repo)
    payment_service = PaymentService()
    analytics_service = AnalyticsService(analytics_repo=analytics_repo)
    share_service = ShareService(
        share_repo=share_repo, topic_repo=topic_repo, user_repo=user_repo,
    )

    # Build Telegram application
    app = build_application()

    # Store services in bot_data for handler access
    app.bot_data["topic_service"] = topic_service
    app.bot_data["photo_service"] = photo_service
    app.bot_data["schedule_service"] = schedule_service
    app.bot_data["payment_service"] = payment_service
    app.bot_data["analytics_service"] = analytics_service
    app.bot_data["share_service"] = share_service

    # Reload schedules from database
    await _reload_schedules(app, schedule_service, topic_service)

    # Register daily analytics job (if group configured)
    if ANALYTICS_GROUP_ID is not None:
        from src.runtime.handlers.analytics_handler import send_daily_analytics

        app.job_queue.run_daily(  # type: ignore[union-attr]
            send_daily_analytics,
            time=datetime.time(hour=0, minute=0, tzinfo=datetime.UTC),
            name="daily_analytics",
        )
        logger.info(
            "Analytics job registered: daily at 00:00 UTC -> group %d",
            ANALYTICS_GROUP_ID,
        )

    logger.info("🤖 Daily Photo Bot starting...")

    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()  # type: ignore[union-attr]

    logger.info("🤖 Bot is running! Press Ctrl+C to stop.")

    # Graceful shutdown via signal handlers
    loop = asyncio.get_running_loop()
    stop_event = asyncio.Event()

    def _signal_handler() -> None:
        logger.info("Received shutdown signal...")
        stop_event.set()

    try:
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, _signal_handler)
    except NotImplementedError:
        # Windows does not support loop.add_signal_handler().
        # Fallback: stop_event.wait() will block until KeyboardInterrupt
        # or SystemExit is raised. Note: This is less reliable on Windows
        # as KeyboardInterrupt may not always interrupt asyncio.Event.wait().
        # For production use, deploy on Linux/macOS.
        logger.warning(
            "Signal handlers not supported on this platform, using fallback."
        )

    try:
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        # Fallback for platforms without signal handler support
        logger.info("Received interrupt...")
    finally:
        logger.info("Shutting down...")
        await app.updater.stop()  # type: ignore[union-attr]
        await app.stop()
        await app.shutdown()
        await db.close()
        logger.info("Bot stopped gracefully.")


async def _reload_schedules(
    app: Application,
    schedule_service: ScheduleService,
    topic_service: TopicService,
) -> None:
    """Reload all active schedules from the database and register jobs."""
    from src.runtime.handlers.schedule_handler import _send_scheduled_photo
    from src.types.schedule import ScheduleType

    schedules = await schedule_service.get_all_active_schedules()
    logger.info("Reloading %d active schedule(s) from database.", len(schedules))

    for schedule in schedules:
        chat_id = await topic_service.get_owner_telegram_id(schedule.topic_id)
        if chat_id is None:
            logger.warning(
                "No user found for topic_id=%d, skipping schedule.",
                schedule.topic_id,
            )
            continue
        job_name = f"photo_{schedule.topic_id}"

        if schedule.schedule_type == ScheduleType.INTERVAL:
            seconds = int(schedule.value)
            app.job_queue.run_repeating(  # type: ignore[union-attr]
                _send_scheduled_photo,
                interval=seconds,
                first=seconds,
                name=job_name,
                data={"topic_id": schedule.topic_id},
                chat_id=chat_id,
            )
            logger.info(
                "Registered interval job for topic_id=%d: every %ds (chat %d)",
                schedule.topic_id,
                seconds,
                chat_id,
            )
        elif schedule.schedule_type == ScheduleType.FIXED_TIME:
            parts = schedule.value.split(":")
            hour, minute = int(parts[0]), int(parts[1])
            app.job_queue.run_daily(  # type: ignore[union-attr]
                _send_scheduled_photo,
                time=datetime.time(hour=hour, minute=minute, tzinfo=datetime.UTC),
                name=job_name,
                data={"topic_id": schedule.topic_id},
                chat_id=chat_id,
            )
            logger.info(
                "Registered daily job for topic_id=%d: at %02d:%02d (chat %d)",
                schedule.topic_id,
                hour,
                minute,
                chat_id,
            )


def main() -> None:
    """Main entry point."""
    setup_logging()
    logger.info("Starting Daily Photo Bot...")
    asyncio.run(_startup())


if __name__ == "__main__":
    main()

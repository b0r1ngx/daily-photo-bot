"""Bot entry point. Initializes all layers and starts polling."""
from __future__ import annotations

import asyncio
import datetime
import logging

from src.config.logging import setup_logging
from src.config.settings import DATABASE_PATH

logger = logging.getLogger(__name__)


async def _startup() -> None:
    """Initialize database, services, and start the bot."""
    from src.repo.database import get_connection, init_db
    from src.repo.schedule_repo import ScheduleRepo
    from src.repo.sent_photo_repo import SentPhotoRepo
    from src.repo.topic_repo import TopicRepo
    from src.repo.user_repo import UserRepo
    from src.runtime.app import build_application
    from src.service.payment_service import PaymentService
    from src.service.photo_service import PhotoService
    from src.service.schedule_service import ScheduleService
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

    # Create services (inject repos)
    topic_service = TopicService(user_repo=user_repo, topic_repo=topic_repo)
    photo_service = PhotoService(sent_photo_repo=sent_photo_repo)
    schedule_service = ScheduleService(schedule_repo=schedule_repo)
    payment_service = PaymentService()

    # Build Telegram application
    app = build_application()

    # Store services in bot_data for handler access
    app.bot_data["db"] = db
    app.bot_data["topic_service"] = topic_service
    app.bot_data["photo_service"] = photo_service
    app.bot_data["schedule_service"] = schedule_service
    app.bot_data["payment_service"] = payment_service
    app.bot_data["topic_repo"] = topic_repo

    # Reload schedules from database
    await _reload_schedules(app, schedule_service, db)

    logger.info("🤖 Daily Photo Bot starting...")

    # Start polling
    await app.initialize()
    await app.start()
    await app.updater.start_polling()  # type: ignore[union-attr]

    logger.info("🤖 Bot is running! Press Ctrl+C to stop.")

    # Keep running until interrupted
    try:
        stop_event = asyncio.Event()
        await stop_event.wait()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
    finally:
        await app.updater.stop()  # type: ignore[union-attr]
        await app.stop()
        await app.shutdown()
        await db.close()
        logger.info("Bot stopped gracefully.")


async def _reload_schedules(
    app: object,
    schedule_service: object,
    db: object,
) -> None:
    """Reload all active schedules from the database and register jobs."""
    from src.runtime.handlers.schedule_handler import _send_scheduled_photo
    from src.service.schedule_service import ScheduleService
    from src.types.schedule import ScheduleType

    svc: ScheduleService = schedule_service  # type: ignore[assignment]
    schedules = await svc.get_all_active_schedules()
    logger.info("Reloading %d active schedule(s) from database.", len(schedules))

    for schedule in schedules:
        # Find the chat_id for this topic's user
        cursor = await db.execute(  # type: ignore[union-attr]
            "SELECT u.telegram_id FROM users u "
            "JOIN topics t ON t.user_id = u.id "
            "WHERE t.id = ?",
            (schedule.topic_id,),
        )
        row = await cursor.fetchone()
        if not row:
            logger.warning("No user found for topic_id=%d, skipping.", schedule.topic_id)
            continue

        chat_id = row[0]
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
                time=datetime.time(hour=hour, minute=minute),
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

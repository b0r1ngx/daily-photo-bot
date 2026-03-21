"""Shared job-queue utilities for the runtime layer."""

from __future__ import annotations

import logging

from telegram.ext import ContextTypes

from src.service.schedule_service import ScheduleService
from src.service.topic_service import TopicService

logger = logging.getLogger(__name__)


def remove_job(name: str, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """Remove a job by name from the job queue.

    Returns True if a job was removed, False if no job with that name existed.
    """
    if not context.job_queue:
        return False
    current_jobs = context.job_queue.get_jobs_by_name(name)
    if not current_jobs:
        return False
    for job in current_jobs:
        job.schedule_removal()
    return True


async def deactivate_all_user_schedules(
    user_id: int,
    topic_service: TopicService,
    schedule_service: ScheduleService,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """Deactivate all schedules for a user and remove in-memory jobs.

    Used when a user blocks the bot (Forbidden error) to stop wasting API calls.
    Returns the number of schedules deactivated.
    """
    topics = await topic_service.get_user_topics(user_id)
    deactivated = 0
    for topic in topics:
        try:
            schedule = await schedule_service.get_schedule(topic.id)
            if schedule and schedule.is_active:
                await schedule_service.remove_schedule(topic.id)
                remove_job(f"photo_{topic.id}", context)
                deactivated += 1
        except Exception:
            logger.exception(
                "Failed to deactivate schedule for topic %d during user cleanup",
                topic.id,
            )
    return deactivated

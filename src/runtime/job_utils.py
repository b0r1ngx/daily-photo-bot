"""Shared job-queue utilities for the runtime layer."""

from __future__ import annotations

from telegram.ext import ContextTypes


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

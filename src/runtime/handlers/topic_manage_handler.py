"""Handlers for topic management (view, rename, delete). Layer: Runtime."""
from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import STATE_EDIT_TOPIC_NAME, STATE_MAIN_MENU, STATE_TOPIC_MANAGE
from src.runtime.keyboards import main_menu_keyboard, topic_manage_keyboard
from src.service.schedule_service import ScheduleService
from src.service.topic_service import TopicService

logger = logging.getLogger(__name__)


async def my_topics_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Show list of user's topics with manage buttons."""
    if not update.message:
        return STATE_MAIN_MENU

    topic_service: TopicService = context.bot_data['topic_service']
    user = await topic_service.ensure_user(
        telegram_id=update.effective_user.id,
        username=update.effective_user.username or '',
        first_name=update.effective_user.first_name or '',
    )
    topics = await topic_service.get_user_topics(user.id)

    if not topics:
        await update.message.reply_text(
            'You have no topics yet. Use "➕ Add topic" to create one!',
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    await update.message.reply_text('📋 *Your Topics:*', parse_mode='Markdown')
    for topic in topics:
        await update.message.reply_text(
            f'📌 *{topic.name}*',
            parse_mode='Markdown',
            reply_markup=topic_manage_keyboard(topic),
        )

    return STATE_TOPIC_MANAGE


async def delete_topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Delete a topic and clean up its schedule/job."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_TOPIC_MANAGE
    await query.answer()

    try:
        topic_id = int(query.data.split('_', 1)[1])
    except (IndexError, ValueError):
        await query.edit_message_text('❌ Invalid selection.')
        return STATE_TOPIC_MANAGE

    topic_service: TopicService = context.bot_data['topic_service']
    schedule_service: ScheduleService = context.bot_data['schedule_service']

    # Remove schedule first (if exists), then soft-delete topic
    await schedule_service.remove_schedule(topic_id)

    # Cancel job queue entry
    if context.job_queue:
        jobs = context.job_queue.get_jobs_by_name(f'photo_{topic_id}')
        for job in jobs:
            job.schedule_removal()

    await topic_service.remove_topic(topic_id)

    await query.edit_message_text('✅ Topic deleted.')
    return STATE_TOPIC_MANAGE


async def rename_topic_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start the rename flow — ask for new topic name."""
    query = update.callback_query
    if not query or not query.data:
        return STATE_TOPIC_MANAGE
    await query.answer()

    try:
        topic_id = int(query.data.split('_', 1)[1])
    except (IndexError, ValueError):
        await query.edit_message_text('❌ Invalid selection.')
        return STATE_TOPIC_MANAGE

    context.user_data['rename_topic_id'] = topic_id

    await query.edit_message_text(
        '✏️ Enter the new name for this topic (1-50 characters, letters, numbers, spaces, hyphens):',
    )
    return STATE_EDIT_TOPIC_NAME


async def receive_new_topic_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive the new name and apply the rename."""
    if not update.message or not update.message.text:
        return STATE_EDIT_TOPIC_NAME

    topic_id = context.user_data.get('rename_topic_id')
    if topic_id is None:
        await update.message.reply_text(
            '❌ Error: no topic selected for renaming.',
            reply_markup=main_menu_keyboard(),
        )
        return STATE_MAIN_MENU

    new_name = update.message.text.strip()
    topic_service: TopicService = context.bot_data['topic_service']

    try:
        await topic_service.rename_topic(topic_id, new_name)
    except ValueError as exc:
        await update.message.reply_text(f'❌ {exc}\n\nPlease try again:')
        return STATE_EDIT_TOPIC_NAME

    del context.user_data['rename_topic_id']

    await update.message.reply_text(
        f'✅ Topic renamed to *{new_name}*!',
        parse_mode='Markdown',
        reply_markup=main_menu_keyboard(),
    )
    return STATE_MAIN_MENU

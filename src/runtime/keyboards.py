"""Keyboard builders. Layer: Runtime (depends on: types, config, service)."""
from __future__ import annotations

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

from src.config.constants import (
    KB_ADD_TOPIC,
    KB_MY_TOPICS,
    KB_SCHEDULE,
    SCHEDULE_HOURS,
    SCHEDULE_INTERVALS,
    SCHEDULE_MINUTES,
)
from src.config.i18n import t
from src.types.user import Topic


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Build the main menu ReplyKeyboardMarkup."""
    return ReplyKeyboardMarkup(
        [[KB_ADD_TOPIC, KB_MY_TOPICS], [KB_SCHEDULE]],
        resize_keyboard=True,
    )


def topic_list_keyboard(topics: list[Topic]) -> InlineKeyboardMarkup:
    """Build inline keyboard with user's topics for selection."""
    buttons = [
        [InlineKeyboardButton(text=topic.name, callback_data=f"topic_{topic.id}")]
        for topic in topics
    ]
    return InlineKeyboardMarkup(buttons)


def topic_manage_keyboard(topic: Topic, language_code: str | None = None) -> InlineKeyboardMarkup:
    """Build inline keyboard with schedule/rename/delete actions for a topic."""
    if topic.id is None:
        raise ValueError(f'Cannot build manage keyboard for topic without id: {topic.name}')
    schedule_btn = InlineKeyboardButton(
        t('btn_schedule', language_code), callback_data=f"schedule_{topic.id}",
    )
    rename_btn = InlineKeyboardButton(
        t('btn_rename', language_code), callback_data=f"rename_{topic.id}",
    )
    delete_btn = InlineKeyboardButton(
        t('btn_delete', language_code), callback_data=f"delete_{topic.id}",
    )
    return InlineKeyboardMarkup([[schedule_btn], [rename_btn, delete_btn]])


def schedule_type_keyboard(language_code: str | None = None) -> InlineKeyboardMarkup:
    """Build inline keyboard for choosing schedule type."""
    interval_btn = InlineKeyboardButton(
        t('btn_repeat_interval', language_code), callback_data="stype_interval",
    )
    fixed_btn = InlineKeyboardButton(
        t('btn_fixed_time', language_code), callback_data="stype_fixed",
    )
    remove_btn = InlineKeyboardButton(
        t('btn_remove_schedule', language_code), callback_data="stype_remove",
    )
    return InlineKeyboardMarkup([[interval_btn], [fixed_btn], [remove_btn]])


def interval_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard with interval options."""
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for label, seconds in SCHEDULE_INTERVALS:
        row.append(InlineKeyboardButton(label, callback_data=f"interval_{seconds}"))
        if len(row) == 3:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def hour_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for hour selection (0-23)."""
    buttons: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for h in SCHEDULE_HOURS:
        row.append(InlineKeyboardButton(f"{h:02d}", callback_data=f"hour_{h}"))
        if len(row) == 6:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return InlineKeyboardMarkup(buttons)


def minute_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for minute selection."""
    buttons = [
        InlineKeyboardButton(f":{m:02d}", callback_data=f"minute_{m}")
        for m in SCHEDULE_MINUTES
    ]
    return InlineKeyboardMarkup([buttons])

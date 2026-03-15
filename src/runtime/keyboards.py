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
        [InlineKeyboardButton(text=t.name, callback_data=f"topic_{t.id}")]
        for t in topics
    ]
    return InlineKeyboardMarkup(buttons)


def topic_manage_keyboard(topic: Topic) -> InlineKeyboardMarkup:
    """Build inline keyboard with rename/delete actions for a topic."""
    if topic.id is None:
        raise ValueError(f'Cannot build manage keyboard for topic without id: {topic.name}')
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✏️ Rename", callback_data=f"rename_{topic.id}"),
            InlineKeyboardButton("🗑 Delete", callback_data=f"delete_{topic.id}"),
        ],
    ])


def schedule_type_keyboard() -> InlineKeyboardMarkup:
    """Build inline keyboard for choosing schedule type."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⏱ Every X minutes", callback_data="stype_interval")],
        [InlineKeyboardButton("🕐 At specific time", callback_data="stype_fixed")],
        [InlineKeyboardButton("🗑 Remove schedule", callback_data="stype_remove")],
    ])


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

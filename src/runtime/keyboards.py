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
from src.types.user import MetadataPrefs, Topic


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
    """Build inline keyboard with schedule/share/rename/delete actions for a topic."""
    if topic.id is None:
        raise ValueError(f'Cannot build manage keyboard for topic without id: {topic.name}')
    schedule_btn = InlineKeyboardButton(
        t('btn_schedule', language_code), callback_data=f"schedule_{topic.id}",
    )
    settings_btn = InlineKeyboardButton(
        t('btn_settings', language_code), callback_data=f"settings_{topic.id}",
    )
    share_btn = InlineKeyboardButton(
        t('btn_share', language_code), callback_data=f"share_{topic.id}",
    )
    rename_btn = InlineKeyboardButton(
        t('btn_rename', language_code), callback_data=f"rename_{topic.id}",
    )
    delete_btn = InlineKeyboardButton(
        t('btn_delete', language_code), callback_data=f"delete_{topic.id}",
    )
    return InlineKeyboardMarkup([
        [schedule_btn], [settings_btn], [share_btn], [rename_btn, delete_btn],
    ])


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


def metadata_settings_keyboard(
    topic_id: int,
    prefs: MetadataPrefs,
    language_code: str | None = None,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for toggling metadata display preferences."""
    fields = [
        ("description", prefs.show_description, "metadata_description"),
        ("location", prefs.show_location, "metadata_location"),
        ("camera", prefs.show_camera, "metadata_camera"),
    ]
    buttons: list[list[InlineKeyboardButton]] = []
    for field, enabled, label_key in fields:
        icon = "\u2705" if enabled else "\u274c"
        label = t(label_key, language_code)
        buttons.append([
            InlineKeyboardButton(
                f"{icon} {label}",
                callback_data=f"metatoggle_{field}_{topic_id}",
            ),
        ])
    buttons.append([
        InlineKeyboardButton(
            t('kb_back', language_code),
            callback_data=f"metaback_{topic_id}",
        ),
    ])
    return InlineKeyboardMarkup(buttons)


def share_confirm_keyboard(
    token: str, language_code: str | None = None,
) -> InlineKeyboardMarkup:
    """Build inline keyboard for share confirmation (accept/decline)."""
    accept_btn = InlineKeyboardButton(
        t("share_confirm_yes", language_code),
        callback_data=f"shareaccept_{token}",
    )
    decline_btn = InlineKeyboardButton(
        t("share_confirm_no", language_code),
        callback_data=f"sharedecline_{token}",
    )
    return InlineKeyboardMarkup([[accept_btn, decline_btn]])

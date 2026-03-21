"""Internationalization type definitions. Layer: Types (zero dependencies)."""

from enum import Enum
from typing import Literal


class SupportedLanguage(Enum):
    """Languages supported by the bot."""

    EN = "en"
    ES = "es"
    RU = "ru"
    PT = "pt"
    ZH = "zh"


# All valid message keys for translation lookup.
MessageKey = Literal[
    "welcome_back",
    "welcome_new",
    "use_start_first",
    "error_try_again",
    "topic_added_with_schedule_hint",
    "first_photo_caption",
    "help_text",
    "version_text",
    "action_cancelled",
    "unknown_message",
    "enter_new_topic",
    "topic_limit_reached",
    "topic_added",
    "no_topics",
    "your_topics",
    "topic_name_display",
    "invalid_selection",
    "topic_not_found",
    "topic_deleted",
    "enter_rename",
    "rename_no_topic",
    "topic_renamed",
    "no_topics_for_schedule",
    "select_topic",
    "schedule_type_prompt",
    "select_interval",
    "select_hour",
    "schedule_no_topic",
    "schedule_removed",
    "menu_continue",
    "schedule_topic_error",
    "schedule_interval_set",
    "select_minute",
    "schedule_fixed_set",
    "photo_caption",
    "payment_failed",
    "payment_success",
    "kb_add_topic",
    "kb_schedule",
    "kb_my_topics",
    "kb_back",
    "btn_repeat_interval",
    "btn_fixed_time",
    "btn_remove_schedule",
    "btn_rename",
    "btn_delete",
    "btn_schedule",
    "interval_minutes",
    "interval_hours",
    "photo_no_topics",
    "photo_error",
    "stop_success",
    "stop_no_schedules",
]

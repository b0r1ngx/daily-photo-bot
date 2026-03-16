"""Help and cancel handlers. Layer: Runtime."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import BOT_VERSION, STATE_MAIN_MENU
from src.config.i18n import t
from src.runtime.keyboards import main_menu_keyboard


def _lang(update: Update) -> str | None:
    """Extract language_code from the effective user."""
    return update.effective_user.language_code if update.effective_user else None


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.message:
        return

    await update.message.reply_text(
        t("help_text", _lang(update)),
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def version_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int | None:
    """Handle /version command — show bot version."""
    if not update.message:
        return None

    await update.message.reply_text(
        t("version_text", _lang(update), version=BOT_VERSION),
        reply_markup=main_menu_keyboard(),
    )
    return None


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command — return to main menu."""
    if not update.message:
        return STATE_MAIN_MENU

    # Clean up any pending state
    context.user_data.pop("rename_topic_id", None)
    context.user_data.pop("paid_topic_pending", None)

    await update.message.reply_text(
        t("action_cancelled", _lang(update)),
        reply_markup=main_menu_keyboard(),
    )
    return STATE_MAIN_MENU


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unknown messages in MAIN_MENU state."""
    if not update.message:
        return STATE_MAIN_MENU

    await update.message.reply_text(
        t("unknown_message", _lang(update)),
        reply_markup=main_menu_keyboard(),
    )
    return STATE_MAIN_MENU

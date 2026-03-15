"""Help and cancel handlers. Layer: Runtime."""
from __future__ import annotations

from telegram import Update
from telegram.ext import ContextTypes

from src.config.constants import STATE_MAIN_MENU
from src.runtime.keyboards import main_menu_keyboard


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /help command."""
    if not update.message:
        return

    await update.message.reply_text(
        "📸 *Daily Photo Bot — Help*\n\n"
        "*Commands:*\n"
        "/start — Start the bot or show main menu\n"
        "/help — Show this help message\n"
        "/cancel — Cancel current action\n\n"
        "*Menu options:*\n"
        "➕ *Add topic* — Add a new photo topic\n"
        "⏰ *Schedule* — Set up delivery schedule for your topics\n\n"
        "*How it works:*\n"
        "1. Choose a topic (e.g., parrots, mountains)\n"
        "2. Set a schedule (every X minutes or at a specific time)\n"
        "3. Receive beautiful photos automatically!\n\n"
        "💰 You get 1 free topic. Additional topics cost Telegram Stars.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(),
    )


async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command — return to main menu."""
    if not update.message:
        return STATE_MAIN_MENU

    await update.message.reply_text(
        "↩️ Action cancelled. Use the menu below.",
        reply_markup=main_menu_keyboard(),
    )
    return STATE_MAIN_MENU


async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle unknown messages in MAIN_MENU state."""
    if not update.message:
        return STATE_MAIN_MENU

    await update.message.reply_text(
        "🤔 I don't understand. Use the menu buttons below:",
        reply_markup=main_menu_keyboard(),
    )
    return STATE_MAIN_MENU

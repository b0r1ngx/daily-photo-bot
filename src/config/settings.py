"""Application settings. Layer: Config (depends on: types only).

Loads environment variables and validates them on import.
Fails fast if required variables are missing.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(_PROJECT_ROOT / ".env")


def _require_env(name: str) -> str:
    """Get a required environment variable or fail fast."""
    value = os.getenv(name)
    if not value:
        print(
            f"❌ FATAL: Required environment variable '{name}' is not set.\n"
            f"   Copy .env.example to .env and fill in the values.",
            file=sys.stderr,
        )
        sys.exit(1)
    return value


# --- Required ---
TELEGRAM_BOT_TOKEN: str = _require_env("TELEGRAM_BOT_TOKEN")
PEXELS_API_KEY: str = _require_env("PEXELS_API_KEY")

# --- Optional with defaults ---
UNSPLASH_ACCESS_KEY: str = os.getenv("UNSPLASH_ACCESS_KEY", "")
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "data/bot.db")
STAR_PRICE: int = int(os.getenv("STAR_PRICE", "1"))
FREE_TOPICS_LIMIT: int = int(os.getenv("FREE_TOPICS_LIMIT", "1"))
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

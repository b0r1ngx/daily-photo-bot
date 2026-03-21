# Daily Photo Bot

A Telegram bot that sends users photos based on chosen topics on a configurable schedule.

**Version:** 3.3.0

## Features

### Core (V1)
- **Topic-based delivery** — choose photo topics (e.g., "parrots", "sunsets", "cats") and get photos delivered automatically
- **Flexible scheduling** — set intervals (5 min to 12 hr) or a fixed daily time
- **Freemium model** — 1 free topic per user, additional topics via Telegram Stars payment
- **Dual photo sources** — Pexels (primary) and Unsplash (fallback)
- **Smart deduplication** — never sends the same photo twice per topic (resets after 500)
- **Persistent storage** — SQLite database survives restarts, schedules reload automatically

### V2 Enhancements
- 🌍 **Internationalization** — 5 languages (EN, ES, RU, PT, ZH) with 49 translation keys. Language auto-detected from Telegram client settings.
- 📋 **Topic Management** — "My Topics" menu with rename and delete functionality
- 🔍 **Search Quality** — multi-language topic translation via `search_terms.json` dictionary for better stock photo results
- 📸 **Instant Preview** — first photo sent immediately when creating a topic (no waiting for next schedule tick)
- 🗑 **Remove Schedule** — users can remove their photo delivery schedule
- ℹ️ **Version Command** — `/version` shows current bot version
- 🛡 **Security** — IDOR protection (users can only manage their own topics), Markdown injection prevention

## Setup

```bash
# Clone and install
git clone <repo-url> && cd daily-photo-bot
pip install -e ".[dev]"

# Configure environment
cp .env.example .env
# Edit .env with your TELEGRAM_BOT_TOKEN, PEXELS_API_KEY, UNSPLASH_ACCESS_KEY

# Run the bot
python -m src.main
```

Get your API keys:
- **Telegram bot token** from [@BotFather](https://t.me/BotFather)
- **Pexels API key** from [pexels.com/api](https://www.pexels.com/api/)
- **Unsplash access key** (optional) from [unsplash.com/developers](https://unsplash.com/developers)

## Development

```bash
python -m pytest tests/ -v                             # Run all tests
python -m pytest tests/ -v --cov=src                   # Run with coverage
python -m ruff check src/                              # Lint
python -m ruff check src/ --fix                        # Auto-fix lint issues
python tools/ai-linters/layer-dependency-check.py      # Check architecture
```

## Architecture

The project follows a strict 6-layer domain architecture. Dependencies flow downward only — lower layers never import from upper layers. See [`docs/architecture.md`](docs/architecture.md) for full details.

```
src/types/    → Data models, DTOs, enums, i18n types (zero dependencies)
src/config/   → Environment variables, constants, i18n system, translations/
src/repo/     → SQLite data access, external API clients
src/service/  → Business logic
src/runtime/  → Telegram bot handlers, ConversationHandler state machine
```

### Conversation State Machine

The bot uses a `ConversationHandler` with 10 states (0–9):

| State | Name | Purpose |
|-------|------|---------|
| 0 | `AWAITING_TOPIC` | First-time user entering their initial topic |
| 1 | `MAIN_MENU` | Primary menu (Add topic / My Topics / Schedule) |
| 2 | `AWAITING_NEW_TOPIC` | User typing a new topic name |
| 3 | `SCHEDULE_SELECT_TOPIC` | Picking which topic to schedule |
| 4 | `SCHEDULE_TYPE` | Choosing interval vs. fixed time |
| 5 | `SCHEDULE_INTERVAL` | Selecting interval duration |
| 6 | `SCHEDULE_HOUR` | Picking hour for fixed-time schedule |
| 7 | `SCHEDULE_MINUTE` | Picking minute for fixed-time schedule |
| 8 | `TOPIC_MANAGE` | My Topics list — rename/delete actions |
| 9 | `EDIT_TOPIC_NAME` | User typing a new name for a topic |

### Migration System

Forward-only migrations tracked in a `schema_version` table. `run_migrations()` in `src/repo/database.py` applies pending migrations on startup. Idempotent — safe to call multiple times.

### i18n System

Translation files live in `src/config/translations/` as JSON (one per language: `en.json`, `es.json`, `ru.json`, `pt.json`, `zh.json`). The `t(key, language_code, **kwargs)` function in `src/config/i18n.py` resolves the user's Telegram language, falls back to English for missing keys, and supports string formatting via kwargs. A separate `search_terms.json` maps common topics to multi-language search terms for better photo API results.

## Tech Stack

| Technology | Purpose |
|---|---|
| Python 3.11+ | Language |
| python-telegram-bot v21+ | Bot framework |
| SQLite + aiosqlite | Database |
| httpx | HTTP client for photo APIs |
| pytest | Testing |
| ruff | Linting |

## Deployment

Designed for single-instance VPS deployment. The bot persists all subscriptions and schedules to SQLite — on restart, active schedules reload from the database automatically. Migrations run on startup to handle schema changes between versions.

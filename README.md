# Daily Photo Bot

A Telegram bot that sends users photos based on chosen topics on a configurable schedule.

## Features

- **Topic-based delivery** — choose photo topics (e.g., "parrots", "sunsets", "cats") and get photos delivered automatically
- **Flexible scheduling** — set intervals (5 min to 12 hr) or a fixed daily time
- **Freemium model** — 1 free topic per user, additional topics via Telegram Stars payment
- **Dual photo sources** — Pexels (primary) and Unsplash (fallback)
- **Smart deduplication** — never sends the same photo twice per topic (resets after 500)
- **Persistent storage** — SQLite database survives restarts, schedules reload automatically

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
src/types/    → Data models, DTOs, enums (zero dependencies)
src/config/   → Environment variables, constants
src/repo/     → SQLite data access, external API clients
src/service/  → Business logic
src/runtime/  → Telegram bot handlers
```

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

Designed for single-instance VPS deployment. The bot persists all subscriptions and schedules to SQLite — on restart, active schedules reload from the database automatically.

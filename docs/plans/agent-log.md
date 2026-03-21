# AI Agent Log (Observability)

This file tracks the reasoning and autonomous actions taken by AI Agents in this repository. It provides observability for human engineers to understand *why* an agent made specific architectural or code choices.

---

## 🤖 [Agent Instruction]
**When you complete a complex task, append a new log entry at the bottom of this file using the format below.**

```markdown
### YYYY-MM-DD HH:MM - Task: [Short description of what you were asked to do]
**Agent:** [Claude/Copilot/OpenCode/Cursor]

**Reasoning:**
1. [What docs did you read? e.g., "Read docs/architecture.md and determined this belongs in Service layer"]
2. [What was the key technical decision? e.g., "Chose to use a mocked DB for tests to follow testing.md"]
3. [Did you encounter any linter errors? How did you fix them?]

**Files Changed:**
- `src/path/to/file.ts` (created)
- `src/path/to/test.spec.ts` (added tests)
```

---

### 2026-03-11 14:30 - Task: Initialize Harness Engineering Kit
**Agent:** OpenCode (Gemini 3.1 Pro)

**Reasoning:**
1. Read the provided OpenAI methodology analysis.
2. Created the core `AGENTS.md` and `docs/` structure to define the Layered Architecture.
3. Added `tools/ai-linters/layer-dependency-check.js` to enforce architectural boundaries and emit agent-friendly errors.
4. Created `docs/state.md` and this log file to ensure agent observability.

**Files Changed:**
- `AGENTS.md`
- `docs/architecture.md`, `docs/tech-stack.md`, `docs/state.md`
- `docs/plans/agent-log.md`
- `tools/ai-linters/layer-dependency-check.js`
- `.github/workflows/ai-garbage-collect.yml`

---

## 2026-03-15 — Full Bot Implementation (Phases 1–4)

**Agent:** OpenCode (Claude Opus 4.6)
**Duration:** Single extended session
**Task:** Implement the daily-photo-bot Telegram bot from scratch using Python

### What Was Done

**Phase 1: Foundation**
- Created `pyproject.toml` with all dependencies (python-telegram-bot, aiosqlite, httpx, python-dotenv, pytest, ruff)
- Built type layer: `User`, `Topic`, `PhotoResult`, `ScheduleConfig`, `ScheduleType`, `PaymentInfo` as frozen dataclasses
- Config layer: environment variable loading with fail-fast validation, constants for states/labels/API URLs/schedule options
- Updated `.gitignore` for Python, created `.env.example`

**Phase 1b: Plan Review Fixes**
- Created Python AST-based layer dependency linter (`tools/ai-linters/layer-dependency-check.py`)
- Added custom exception hierarchy (`BotError` base → `PhotoSourceError`, `RateLimitError`, etc.)
- Added Repository Protocol interfaces for dependency injection
- Added structured logging configuration

**Phase 2: Data Layer (20 integration tests)**
- SQLite database initialization with full DDL (users, topics, schedules, sent_photos tables)
- WAL mode + foreign keys enabled
- Repositories: user (get_or_create), topic (CRUD + soft-delete), schedule (UPSERT), sent_photo (dedup tracking)
- Integration tests using `:memory:` SQLite databases

**Phase 3: Services (21 unit tests)**
- Photo service: Pexels primary + Unsplash fallback, dedup filtering, exhaustion reset at 500 photos
- Topic service: user ensure, CRUD, free-tier limit (1 topic), name validation
- Schedule service: interval + fixed-time management with validation
- Payment service: Telegram Stars invoice creation, payload verification
- All service tests mock repos via Protocol interfaces

**Phase 4: Runtime**
- Telegram handlers: /start onboarding, topic add flow, schedule configuration (type→interval/fixed), payment (pre_checkout + successful), /help + /cancel
- ReplyKeyboardMarkup: main menu, topic list, schedule type, interval picker, hour/minute pickers
- ConversationHandler state machine wiring in `app.py`
- Entry point (`main.py`): DB init, DI wiring, schedule reload from DB on startup, polling loop

### Key Decisions
- **Pexels as primary photo source** — 200 req/hr, 20k/mo free, hotlinking allowed
- **Unsplash as fallback** — 50 req/hr demo tier, native `/photos/random` endpoint
- **Single-instance design** — JobQueue in-memory, schedules reload from DB on restart
- **Photo exhaustion strategy** — Reset sent_photos tracking after 500 per topic
- **SQLite over PostgreSQL** — zero-config, perfect for single VPS deployment

### Metrics
- 41 tests (20 integration + 21 unit), all passing
- 0 layer dependency violations
- 0 ruff lint errors (after Phase 5 fixes)
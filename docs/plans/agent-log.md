# AI Agent Log (Observability)

This file tracks the reasoning and autonomous actions taken by AI Agents in this repository. It provides observability for human engineers to understand *why* an agent made specific architectural or code choices.

---

## [Agent Instruction]
**When you complete a complex task, append a new log entry at the bottom of this file using the format below.**

```markdown
### YYYY-MM-DD HH:MM - Task: [Short description of what you were asked to do]
**Agent:** [Claude/Copilot/OpenCode/Cursor]

**Reasoning:**
1. [What docs did you read? e.g., "Read docs/architecture.md and determined this belongs in Service layer"]
2. [What was the key technical decision? e.g., "Chose to use a mocked DB for tests to follow testing.md"]
3. [Did you encounter any linter errors? How did you fix them?]

**Files Changed:**
- `src/path/to/file.py` (created)
- `tests/unit/test_file.py` (added tests)
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

## 2026-03-15 — Full Bot Implementation (Phases 1-4)

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
- Added custom exception hierarchy (`BotError` base -> `PhotoSourceError`, `RateLimitError`, etc.)
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
- Telegram handlers: /start onboarding, topic add flow, schedule configuration (type->interval/fixed), payment (pre_checkout + successful), /help + /cancel
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

---

### 2026-03-21 09:00 - Task: Harness Engineering Full Audit & Initialization
**Agent:** OpenCode (Claude Opus 4.6)

**Reasoning:**
1. Read all documentation: `AGENTS.md`, `docs/architecture.md`, `docs/tech-stack.md`, `docs/testing.md`, `docs/agent-linters.md`, `docs/deployment.md`, `docs/state.md`, `docs/plans/agent-log.md`, `docs/plans/garbage-collection.md`, `docs/plans/README.md`, `docs/plans/v2-feedback-strategy.md`.
2. Explored the complete `src/` directory tree and analyzed imports for every Python file across all 5 architecture layers (types, config, repo, service, runtime).
3. Ran all three verification tools:
   - `python tools/ai-linters/layer-dependency-check.py` — PASSED (0 violations)
   - `python -m pytest tests/ -v` — PASSED (108/108 tests)
   - `python -m ruff check src/` — PASSED (0 errors)
4. Checked dependency stack against `docs/tech-stack.md` — all dependencies aligned.
5. Identified 7 critical stale/broken artifacts from the original Harness Kit template, plus documentation drift.

**Key Findings:**
- **Architecture compliance: Excellent.** All 5 layers have strictly downward dependency flow. Protocol-based DI properly decouples service from repo layers. Zero violations.
- **Tech stack compliance: Full.** python-telegram-bot, aiosqlite, httpx, python-dotenv, pytest, ruff — all match approved stack.
- **Dead code:** `layer-dependency-check.js` (JS linter for a Python project), `ai-garbage-collect.yml` (Node.js workflow for a Python project).
- **Doc drift:** Test counts stale (docs say 79/106, actual is 108), version mismatch (`pyproject.toml` says 0.1.0, should be 0.2.3), `agent-linters.md` references ESLint/TypeScript, `state.md` referenced wrong branch and deployment status.

**Files Changed:**
- `audit-output/docs/plans/garbage-collection.md` (updated with 16 prioritized tech debt items, 7 new critical items)
- `audit-output/docs/state.md` (updated with correct version 0.2.3, branch master, production status, audit results)
- `audit-output/docs/plans/agent-log.md` (added this initialization entry)

---

### 2026-03-21 — Task: Critical Tech Debt Resolution (Garbage Collection)
**Agent:** OpenCode (Claude Opus 4.6)

**Reasoning:**
1. Read `docs/plans/garbage-collection.md` and the audit findings from the prior session. Identified 7 critical items — all stale Node.js/TypeScript template artifacts left from the Harness Kit initialization.
2. Systematically resolved each item, verifying before and after with tests, ruff, and layer linter.
3. All changes were documentation and config fixes — no source code changes required. The bot's architecture and code were already clean.

**Items Resolved:**
1. `pyproject.toml` — version `0.1.0` → `0.2.3` (matched `BOT_VERSION` in `src/config/constants.py`)
2. `opencode-init.md` — fixed linter reference from `.js` to `.py`
3. `docs/deployment.md` — fixed branch references from `implementing-daily-photo-bot` to `master` (2 occurrences)
4. `README.md` — removed hardcoded "79 tests" count, replaced with generic wording
5. `docs/testing.md` — updated test tree (added 2 missing test files) and counts to 108 (34 integration + 74 unit)
6. `docs/agent-linters.md` — full rewrite: removed ESLint/TypeScript references, documented Python AST linter + ruff
7. `docs/plans/README.md` — rewritten to list actual directory contents
8. `AGENTS.md` sections 3, 5, 6 — rewritten for Python (removed UI layer, npm→pytest/ruff, TypeScript→Python conventions)
9. `.github/workflows/ai-garbage-collect.yml` — deleted (broken Node.js workflow referencing non-existent scripts)
10. `docs/plans/garbage-collection.md` — moved resolved items to "Resolved" section, renumbered remaining 9 items
11. `docs/state.md` — updated with audit results, correct status, and next steps

**Files Changed:**
- `pyproject.toml` (version bump)
- `opencode-init.md` (linter reference fix)
- `AGENTS.md` (sections 3, 5, 6 rewritten)
- `README.md` (test count fix)
- `docs/state.md` (full status update)
- `docs/testing.md` (test tree and counts updated)
- `docs/deployment.md` (branch references fixed)
- `docs/agent-linters.md` (full rewrite)
- `docs/plans/README.md` (rewritten)
- `docs/plans/garbage-collection.md` (resolved items moved)
- `.github/workflows/ai-garbage-collect.yml` (deleted)

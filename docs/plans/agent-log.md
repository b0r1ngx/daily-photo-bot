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

---

### 2026-03-21 — Task: Todo-List Tasks (5 of 7 completed)
**Agent:** OpenCode (Claude Opus 4.6)

**Task:** Execute the 7 tasks from `docs/plans/todo-list.md`. Two planning sub-agents + comparison agent used per AGENTS.md section 8.

**Completed:**

1. **Task 3 (DB Investigation):** Analyzed full DB schema (users, topics, schedules, sent_photos). Found: user clicks NOT logged, photo sends tracked in `sent_photos`. Pre-built analytics SQL queries provided. Output: `output-task3-db-investigation.md`.

2. **Task 7 (Photo Delivery Debug):** Traced photo delivery pipeline through `schedule_handler.py` and `main.py`. Identified 5 silent failure points and 11 ranked root causes. Provided diagnostic SQL queries and log grep commands for production investigation. Output: `output-task7-diagnostics.md`.

3. **Task 6 (Reply Keyboard Bug Fix):** Root cause: `ConversationHandler` in `app.py` only had `/start` as entry point. Reply keyboard buttons (Add topic, My Topics, Schedule) were only handled in `STATE_MAIN_MENU`, so clicking from other states was silently ignored. Fix: added `MessageHandler`s to both `entry_points` and `fallbacks`.

4. **Task 5 (Schedule Button):** End-to-end implementation:
   - Added `btn_schedule` to `MessageKey` type and all 12 translation files
   - Added Schedule button to `topic_manage_keyboard()` — layout: `[[Schedule], [Rename, Delete]]`
   - Created `schedule_from_topics_callback` handler with IDOR protection (verifies topic ownership before allowing schedule access)
   - Wired `schedule_\d+` callback pattern in `STATE_TOPIC_MANAGE` in `app.py`

5. **Task 1 (i18n Expansion):** Added 7 new languages (hi, ar, ms, bn, fr, it, de) — total 12 languages:
   - Created 7 translation JSON files (54 keys each, `kb_*` keys kept as English)
   - Updated `SupportedLanguage` enum with 7 new values
   - Updated `search_terms.json` with native-language search terms for all 7 new languages
   - Added 14 new tests (7 per-language translation tests + 7 parametrize entries)
   - Updated test assertions for 12-language support (replaced `de`/`fr` unsupported examples with `ja`/`ko`)

**Blocked:**
- Task 4 (Analytics Group) — needs user answers on "active users" definition, daily stats timing, delivery mechanism
- Task 2 (Photo Metadata) — needs user answers on Pexels limitations (no location/camera data), settings UI, defaults

**Metrics:**
- 122 tests (34 integration + 88 unit), all passing
- 0 layer dependency violations
- 0 ruff lint errors

**Files Changed:**
- `src/runtime/app.py` (T6: entry_points + fallbacks fix; T5: schedule_\d+ callback wiring)
- `src/runtime/keyboards.py` (T5: Schedule button added to topic_manage_keyboard)
- `src/runtime/handlers/topic_manage_handler.py` (T5: schedule_from_topics_callback handler)
- `src/types/i18n.py` (T5: btn_schedule in MessageKey; T1: 7 new SupportedLanguage values)
- `src/config/translations/*.json` (T5: btn_schedule added to 5 existing; T1: 7 new language files created)
- `src/config/translations/search_terms.json` (T1: 7 new language entries)
- `tests/unit/test_i18n.py` (T1: 14 new tests, updated assertions for 12 languages)
- `docs/state.md` (documentation sync)
- `docs/testing.md` (test count updated to 122)
- `docs/plans/agent-log.md` (this entry)
- `output-task3-db-investigation.md` (T3 deliverable)
- `output-task7-diagnostics.md` (T7 deliverable)

---

### 2026-03-21 — Task: Todo-List Tasks 4 & 2 (Analytics Group + Photo Metadata)
**Agent:** OpenCode (Claude Opus 4.6)

**Task:** Complete the final 2 tasks from `docs/plans/todo-list.md`. Two planning sub-agents + comparison agent used per AGENTS.md section 8 for each task.

**Completed:**

1. **Task 4 (Analytics Group):** Full end-to-end analytics pipeline:
   - Types: `AnalyticsSnapshot` dataclass with 7 metrics fields
   - Repo: `AnalyticsRepo` with 8 query methods (total users, language breakdown, active users, paid users, photos sent since, API requests since, record API request, cleanup old records)
   - Service: `AnalyticsService` with `collect_snapshot()` (gathers all metrics) and `format_message()` (builds Telegram-formatted summary with emoji language flags)
   - Runtime: `send_daily_analytics` job callback, wired to `job_queue.run_daily()` at midnight UTC
   - DB: `api_requests` table added to DDL and migration v2, with 30-day retention cleanup
   - Config: `ANALYTICS_GROUP_ID` environment variable
   - Wiring: `main.py` updated with DI for AnalyticsRepo, AnalyticsService, api_request_recorder, daily job
   - Fixed `db.execute()` → `db.executescript()` for multi-statement SQL migrations
   - 26 new tests (15 integration + 8 service unit + 3 handler unit)

2. **Task 2 (Photo Metadata):** Per-topic metadata display preferences:
   - Types: 3 new fields on `PhotoResult` (description, location, camera), `MetadataPrefs` frozen dataclass, 6 new `MessageKey` values
   - Config: `STATE_METADATA_SETTINGS = 10`, `METADATA_VALUE_MAX_LENGTH = 100`, 6 new i18n keys in all 12 languages (59 keys total per file)
   - Repo: `metadata_prefs` column on topics table (DDL + migration v3), `get_metadata_prefs()` / `update_metadata_prefs()` on `TopicRepo`
   - Service: Metadata extraction helpers (`_extract_description`, `_extract_location`, `_extract_camera`) with truncation; `_fetch_from_unsplash()` populates new fields; `toggle_metadata_field()` business logic
   - Runtime: `build_photo_caption()` shared caption builder in `caption.py`; Settings button on topic manage keyboard; `metadata_settings_keyboard()` with ✅/❌ toggle buttons; 3 new handlers (`settings_callback`, `metatoggle_callback`, `metaback_callback`); `STATE_METADATA_SETTINGS` state in `ConversationHandler`; schedule_handler and quick_commands_handler refactored to use shared caption builder
   - 22 new tests: 5 caption, 10 photo_service (metadata extraction), 4 topic_service (metadata prefs), 3 topic_repo (metadata prefs integration)

**Key Decisions:**
- **Flat fields on PhotoResult** instead of nested `PhotoMetadata` dataclass — simpler, no null-checking needed, Pexels photos just use empty strings
- **NULL metadata_prefs = all defaults ON** — no backfill migration needed, existing topics just work
- **`build_photo_caption()` in `src/runtime/caption.py`** — deduplicated caption building from 2 handlers into one shared function
- **Unsplash `exif.name` and `location.name`** — use combined fields directly instead of concatenating make+model or city+country
- **Callback data format `metatoggle_{field}_{topic_id}`** — simple split on `_` with known 3-part structure

**Metrics:**
- 173 tests (49 integration + 124 unit), all passing
- 0 layer dependency violations
- 0 ruff lint errors

**Files Created:**
- `src/types/analytics.py` (T4)
- `src/repo/analytics_repo.py` (T4)
- `src/service/analytics_service.py` (T4)
- `src/runtime/handlers/analytics_handler.py` (T4)
- `src/runtime/caption.py` (T2)
- `tests/integration/test_analytics_repo.py` (T4)
- `tests/unit/test_analytics_service.py` (T4)
- `tests/unit/test_analytics_handler.py` (T4)
- `tests/unit/test_caption.py` (T2)

**Files Modified:**
- `src/types/photo.py`, `src/types/user.py`, `src/types/protocols.py`, `src/types/i18n.py`
- `src/config/constants.py`, `src/config/settings.py`, `.env.example`
- `src/repo/database.py`, `src/repo/topic_repo.py`
- `src/service/photo_service.py`, `src/service/topic_service.py`
- `src/runtime/app.py`, `src/runtime/keyboards.py`
- `src/runtime/handlers/topic_manage_handler.py`, `src/runtime/handlers/schedule_handler.py`, `src/runtime/handlers/quick_commands_handler.py`
- `src/main.py`
- `src/config/translations/*.json` (all 12 files)
- `tests/unit/test_photo_service.py`, `tests/unit/test_topic_service.py`, `tests/unit/test_i18n.py`
- `tests/integration/test_topic_repo.py`
- `docs/state.md`, `docs/testing.md`, `docs/plans/agent-log.md`

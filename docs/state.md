# Project State
**Last Updated:** 2026-03-22

## Active Task
All 7 tasks from `docs/plans/todo-list.md` are complete.
Copilot review fixes (rounds 1 and 2) for PR #4 are complete.
Copilot review fixes for PRs #5 and #6 are complete.
`/analytics` on-demand command added for the admin group.
Forbidden error handling added to scheduled photo delivery.

## Current Status
- **Version:** 3.3.0 (source: `src/config/constants.py:BOT_VERSION`)
- **Branch:** `v3.3`
- **VPS:** Running V2.3 (deployed, production)
- **Python:** 3.11+ required (dev environment running 3.13.7)

## V2.4 Completed (Todo-List Tasks — 7 of 7)

### Completed
1. **Task 3 (DB Investigation)** — Analyzed DB schema and data inventory. Users, topics, schedules, and sent_photos are tracked. User clicks are NOT logged. Photo sends ARE tracked via `sent_photos` table. Output: `output-task3-db-investigation.md`.
2. **Task 7 (Photo Delivery Debug)** — Investigated why user stopped receiving photos. Identified 5 silent failure points in `schedule_handler.py` and `main.py`. 11 root causes ranked by likelihood. Requires production DB/logs to diagnose. Output: `output-task7-diagnostics.md`.
3. **Task 6 (Reply Keyboard Bug Fix)** — Fixed `ConversationHandler` in `app.py`: reply keyboard buttons (Add topic, My Topics, Schedule) now work from ANY conversation state. Added `MessageHandler` entries to both `entry_points` and `fallbacks`.
4. **Task 5 (Schedule Button)** — Added "Schedule" button to topic management view. New keyboard layout: `[[Schedule], [Settings], [Rename, Delete]]`. Handler with IDOR protection (verifies topic ownership). New `btn_schedule` i18n key added to all 12 languages.
5. **Task 1 (i18n Expansion)** — Added 7 new languages: Hindi (hi), Arabic (ar), Bahasa Malaysia (ms), Bengali (bn), French (fr), Italian (it), German (de). Total: 12 languages, 59 translation keys each. Updated `search_terms.json` with terms for all 7 new languages. 14 new tests added.
6. **Task 4 (Analytics Group)** — Full analytics pipeline: `AnalyticsSnapshot` type, `AnalyticsRepo` (8 query methods), `AnalyticsService` (snapshot collection + message formatting), daily job at midnight UTC via `job_queue.run_daily()`. `api_requests` table with 30-day retention. Migration v2. 26 new tests (15 integration + 8 service + 3 handler).
7. **Task 2 (Photo Metadata)** — Per-topic metadata display preferences (description, location, camera). `MetadataPrefs` dataclass, `build_photo_caption()` shared caption builder, metadata extraction from Unsplash API (description/alt, location.name, exif.name). Settings UI with toggle keyboard (✅/❌). Migration v3. 22 new tests. 6 new i18n keys across 12 languages.

## Verification Status
- **191/191 tests passing** (55 integration + 136 unit)
- **Layer dependency linter:** passing (0 violations)
- **Ruff linter:** passing (0 errors)
- **Architecture compliance:** All 5 layers (types, config, repo, service, runtime) have correct downward-only dependency flow

## V3.3 Fixes (Branch: v3.3)

### Forbidden Error Handling
- **`telegram.error.Forbidden` handling** — When `send_photo` raises `Forbidden` (user blocked the bot), all schedules for that user are deactivated and in-memory jobs removed. Prevents wasted API calls on blocked users. Shared helper `deactivate_all_user_schedules()` in `job_utils.py` used by both Forbidden handler and `/stop` command. Fallback: if topic is deleted, deactivates orphaned schedule in DB and removes the triggering job. 6 new unit tests in `test_schedule_handler.py`.

### Copilot PR #7 Fixes
1. **Fix orphaned schedule on Forbidden + deleted topic** — When `send_photo` raises `Forbidden` and the topic no longer exists in DB, the schedule was only removed from memory but not deactivated in the database. On restart, the orphaned active schedule would be reloaded and keep failing. Now calls `schedule_service.remove_schedule()` before `remove_job()`.
2. **DRY: extract `deactivate_all_user_schedules` to `job_utils.py`** — The inline deactivation loop in `/stop` command (`quick_commands_handler.py`) and `_deactivate_all_user_schedules()` in `schedule_handler.py` were structurally identical. Extracted to shared `deactivate_all_user_schedules()` in `job_utils.py`.

### Copilot PR #5 Fixes
1. **Add `exc_info=True`** to corrupted `metadata_prefs` JSON warning in `topic_repo.py` — includes traceback for diagnostics.
2. **Add `assert_awaited()`** to unsplash fallback recorder test in `test_photo_service.py` — verifies the recorder was actually called.
3. **CancelledError concern** — Confirmed false positive. `asyncio.CancelledError` inherits from `BaseException` (not `Exception`) since Python 3.9, so `except Exception` cannot catch it.

### On-Demand Analytics Command
- **`/analytics` command** — Sends the same daily analytics report on demand when invoked in the analytics admin group. Restricted to `ANALYTICS_GROUP_ID` only (silently ignored elsewhere). Registered as standalone `CommandHandler` outside the `ConversationHandler`. 5 new unit tests.

## V2.4 Copilot Review Fixes (PR #4)

### Round 1
1. **Rename `since_iso` → `since_dt_text`** — Parameter names and docstrings in `AnalyticsRepository` protocol and `AnalyticsRepo` implementation renamed to accurately reflect SQLite datetime text format (`YYYY-MM-DD HH:MM:SS`), not ISO-8601. Also renamed `older_than_iso` → `older_than_dt_text`.
2. **Add `rowcount` check in `topic_repo.update_metadata_prefs`** — Silent failure on nonexistent/inactive topic now raises `ValueError`, matching the `update_name` pattern. Added `logger.info` call on success. 2 new integration tests added.

### Round 2
3. **Guard recorder calls in `photo_service.py`** — Wrapped 3 `record_api_request()` call sites in try/except so analytics recording failures don't break photo delivery. 2 new unit tests.
4. **Catch `JSONDecodeError` in `topic_repo.get_metadata_prefs`** — Corrupted JSON in `metadata_prefs` column now falls back to defaults with a warning log instead of crashing. 1 new integration test.
5. **Add explicit `tzinfo=UTC` to `run_daily` time** — Fixed 3 naive `datetime.time()` calls in `main.py` (2) and `schedule_handler.py` (1) to explicitly use UTC timezone.
6. **Filter `is_active=1` in `get_paid_user_count`** — Soft-deleted paid topics no longer inflate the paid user count in analytics. 2 new integration tests.

## Key Architecture Additions (V2.4)
- **New conversation state:** `STATE_METADATA_SETTINGS = 10` — metadata toggle UI
- **New module:** `src/runtime/caption.py` — shared `build_photo_caption()` used by schedule_handler and quick_commands_handler
- **New keyboard:** `metadata_settings_keyboard()` — inline toggle buttons for description/location/camera
- **DB migration v3:** `ALTER TABLE topics ADD COLUMN metadata_prefs TEXT DEFAULT NULL`
- **DB migration v2:** `CREATE TABLE api_requests` for analytics tracking
- **Translation keys:** 59 per language (was 53 before V2.4)

## V2.2 Completed (Quick Commands)
Two new slash commands for instant actions outside the conversation flow:

1. **`/photo` command** — Instantly sends a random photo from one of the user's topics.
2. **`/stop` command** — Pauses all scheduled photo deliveries.
3. **New i18n keys** — `photo_no_topics`, `photo_error`, `stop_success`, `stop_no_schedules` added to all 5 languages and `MessageKey` type.
4. **Handler registration** — Both commands registered as ConversationHandler fallbacks (accessible from any state).
5. **15 new tests** — 7 for `/photo`, 8 for `/stop` covering guard clauses, error paths, happy paths, and partial failures.

## V2.1 Completed (Copilot Review Fixes)
All 4 issues from GitHub Copilot's PR #1 review fixed, plus 6 additional review findings.

## V2 Completed Phases
- **Phase 1: Internationalization** — i18n system, 12 languages, 54 keys
- **Phase 2: Topic Management** — "My Topics" menu, rename/delete flows, IDOR protection
- **Phase 3: Search Quality & Instant Preview** — `search_terms.json` (12 languages), `enrich_query()`, instant preview
- **Phase 4: Schedule Removal & Version Command** — remove schedule, `/version`, Markdown injection prevention
- **Phase 5: Testing & Polish** — test coverage, edge cases, cleanup

## V1 Completed Phases
- **Phase 1: Foundation** — Types, Config, directory structure, pyproject.toml
- **Phase 1b: Review Fixes** — Layer linter (Python AST), exception hierarchy, Protocol interfaces, logging
- **Phase 2: Data Layer** — SQLite repos, WAL mode, 20 integration tests
- **Phase 3: Services** — Photo service, topic service, schedule service, payment service, 21 unit tests
- **Phase 4: Runtime** — Telegram handlers, ConversationHandler, keyboards, app builder, main entry point
- **Phase 5: Polish & Documentation** — README, architecture docs, testing docs, agent log

## Known Tech Debt
See `docs/plans/garbage-collection.md` for the full prioritized list (9 remaining items).

## Next Steps
- Set up Python CI/CD pipeline (pytest, ruff, layer linter) — see garbage-collection.md item #2
- Gather user feedback on V2 features
- Plan V3 based on feedback

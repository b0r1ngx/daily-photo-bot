# Project State
**Last Updated:** 2026-03-21

## Active Task
All 7 tasks from `docs/plans/todo-list.md` are complete.
Copilot review fixes for PR #4 are complete.

## Current Status
- **Version:** 0.2.3 (source: `src/config/constants.py:BOT_VERSION`)
- **Branch:** `master`
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
- **175/175 tests passing** (51 integration + 124 unit)
- **Layer dependency linter:** passing (0 violations)
- **Ruff linter:** passing (0 errors)
- **Architecture compliance:** All 5 layers (types, config, repo, service, runtime) have correct downward-only dependency flow

## V2.4 Copilot Review Fixes (PR #4)
1. **Rename `since_iso` → `since_dt_text`** — Parameter names and docstrings in `AnalyticsRepository` protocol and `AnalyticsRepo` implementation renamed to accurately reflect SQLite datetime text format (`YYYY-MM-DD HH:MM:SS`), not ISO-8601. Also renamed `older_than_iso` → `older_than_dt_text`.
2. **Add `rowcount` check in `topic_repo.update_metadata_prefs`** — Silent failure on nonexistent/inactive topic now raises `ValueError`, matching the `update_name` pattern. Added `logger.info` call on success. 2 new integration tests added.

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

# Project State
**Last Updated:** 2026-03-21

## Active Task
Harness Engineering audit complete. Awaiting deployment to VPS.

## Current Status
- **Version:** 0.2.2
- **Branch:** `implementing-daily-photo-bot`
- **VPS:** Running V1; V2+V2.1+V2.2 awaiting deployment
- **Python:** 3.11+ required (dev environment running 3.13.7)

## Blockers
- `docs/`, `tools/`, `.github/` files owned by different OS user (`boringx`). Agent cannot modify directly. Human must run: `sudo chown -R $(whoami) docs/ tools/ .github/ AGENTS.md opencode-init.md`

## Audit Results (2026-03-21)

### Verification Status
- **108/108 tests passing** (34 integration + 74 unit)
- **Layer dependency linter:** passing (0 violations)
- **Ruff linter:** passing (0 errors)
- **Architecture compliance:** All 5 layers (types, config, repo, service, runtime) have correct downward-only dependency flow

### Tech Debt Identified
7 critical items (stale/broken artifacts from Harness Kit template), 2 high priority, 4 medium, 3 low. See `docs/plans/garbage-collection.md` for full list.

### Key Findings
1. **Architecture: Clean.** Zero layer violations. Protocol-based DI properly decouples service from repo.
2. **Tech stack: Aligned.** All deps match `docs/tech-stack.md` approved list.
3. **Stale template artifacts:** JS linter, Node.js CI workflow, ESLint-referencing docs are dead code from the Harness Kit template.
4. **Doc drift:** Test counts and version number are stale in `testing.md` and `state.md`.

## V2.2 Completed (Quick Commands)
Two new slash commands for instant actions outside the conversation flow:

1. **`/photo` command** — Instantly sends a random photo from one of the user's topics. Picks a random topic, fetches a photo via the photo service with language-aware search enrichment, and delivers it with a formatted caption. Handles all edge cases (no topics, API failures, send failures).
2. **`/stop` command** — Pauses all scheduled photo deliveries. Iterates all user topics, removes active schedules from the database and cancels their job queue entries. Reports the count of stopped schedules. Continues processing on partial failures.
3. **New i18n keys** — `photo_no_topics`, `photo_error`, `stop_success`, `stop_no_schedules` added to all 5 languages and `MessageKey` type.
4. **Handler registration** — Both commands registered as ConversationHandler fallbacks (accessible from any state).
5. **15 new tests** — 7 for `/photo`, 8 for `/stop` covering guard clauses, error paths, happy paths, and partial failures.

## V2.1 Completed (Copilot Review Fixes)
All 4 issues from GitHub Copilot's PR #1 review fixed, plus 6 additional review findings:

**Copilot PR #1 Issues:**
1. **Architecture violation** — Removed raw SQL from `schedule_handler.py` and `main.py`. Added `get_by_id_with_user_language()` and `get_owner_telegram_id()` to TopicRepo/TopicService. Removed `bot_data["db"]` and `bot_data["topic_repo"]`
2. **Payment bypass** — `receive_new_topic()` now checks `paid_topic_pending` flag via `pop()` pattern. Two-phase: `get()` in `add_topic_menu` to route, `pop()` in `receive_new_topic` to consume
3. **Broken payment flow** — Updated `payment_success` translations in all 5 languages to tell user to press "Add topic" instead of typing topic name
4. **Graceful shutdown** — Added signal handlers (SIGINT/SIGTERM) with Windows fallback

**Post-implementation review fixes:**
5. Proper type hints in `_reload_schedules()` (replaced `object` with `Application`, `ScheduleService`, `TopicService`)
6. Stale `paid_topic_pending` cleared in `start_command()` welcome_back path
7. `get_owner_telegram_id` now filters by `is_active = 1`
8. Added `reply_markup=main_menu_keyboard()` to payment success message
9. Added test for `cancel_command` cleanup of `paid_topic_pending`
10. Added Windows signal handling limitation comment

## V2 Completed Phases
- **Phase 1: Internationalization** — i18n system (`t()` function, 5 language JSON files, 49 keys), language_code column + migration, `SupportedLanguage` enum, all handlers localized
- **Phase 2: Topic Management** — "My Topics" menu, rename/delete flows, IDOR protection, 2 new conversation states (TOPIC_MANAGE, EDIT_TOPIC_NAME)
- **Phase 3: Search Quality & Instant Preview** — `search_terms.json` dictionary for multi-language topic translation, `enrich_query()` in photo service, first photo sent immediately on topic creation
- **Phase 4: Schedule Removal & Version Command** — remove schedule option, `/version` command showing BOT_VERSION, Markdown injection prevention
- **Phase 5: Testing & Polish** — 79 tests (23 new), test coverage for i18n and enrich_query, edge cases, cleanup

## V1 Completed Phases
- **Phase 1: Foundation** — Types (dataclasses, enums), Config (env loading, constants), directory structure, pyproject.toml
- **Phase 1b: Review Fixes** — Layer linter (Python AST), exception hierarchy, Protocol interfaces for DI, logging config
- **Phase 2: Data Layer** — SQLite repos (user, topic, schedule, sent_photo) with full DDL, WAL mode, 20 integration tests
- **Phase 3: Services** — Photo service (Pexels+Unsplash fallback), topic service, schedule service, payment service (Telegram Stars), 21 unit tests
- **Phase 4: Runtime** — Telegram handlers (start, topic, schedule, payment, help), ConversationHandler state machine, keyboard layouts, app builder, main entry point with DI wiring and schedule reload
- **Phase 5: Polish & Documentation** — README, architecture docs, testing docs, agent log

## Known Tech Debt
See `docs/plans/garbage-collection.md` for the full prioritized list (16 items).

## Next Steps
- Fix file ownership: `sudo chown -R $(whoami) docs/ tools/ .github/ AGENTS.md opencode-init.md`
- Apply audit output files from `audit-output/` to `docs/`
- Deploy V2+V2.1+V2.2 to VPS
- Gather user feedback on V2 features
- Address critical tech debt items (dead JS linter, broken CI workflow)
- Plan V3 based on feedback

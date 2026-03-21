# Project State
**Last Updated:** 2026-03-21

## Active Task
Harness Engineering audit complete. Addressing identified tech debt.

## Current Status
- **Version:** 0.2.3 (source: `src/config/constants.py:BOT_VERSION`)
- **Branch:** `master`
- **VPS:** Running V2.3 (deployed, production)
- **Python:** 3.11+ required (dev environment running 3.13.7)

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
4. **Doc drift:** Test counts stale in `testing.md`. `pyproject.toml` version stuck at `0.1.0` (should be `0.2.3`). `state.md` referenced wrong branch and deployment status.

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
- **Phase 1: Internationalization** — i18n system, 5 languages, 49 keys
- **Phase 2: Topic Management** — "My Topics" menu, rename/delete flows, IDOR protection
- **Phase 3: Search Quality & Instant Preview** — `search_terms.json`, `enrich_query()`, instant preview
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
See `docs/plans/garbage-collection.md` for the full prioritized list (16 items).

## Next Steps
- Fix file ownership: `sudo chown -R $(whoami) docs/ tools/ .github/ AGENTS.md opencode-init.md`
- Apply audit output files from `audit-output/` to `docs/`
- Address critical tech debt items (dead JS linter, broken CI workflow, version mismatch in `pyproject.toml`)
- Gather user feedback on V2 features
- Plan V3 based on feedback

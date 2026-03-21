# Garbage Collection — Known Tech Debt

Items to address in future sessions. Ordered by priority.

**Last Audited:** 2026-03-21

## High Priority

### 1. Timezone Support
Currently all schedule times are UTC. Users may expect local time zones.
- Add `timezone` field to `schedules` table
- Accept timezone during schedule setup (or infer from Telegram locale)
- Convert fixed-time schedules to UTC internally

### 2. CI/CD Pipeline
No automated pipeline exists. Manual `python -m pytest` and `ruff check` only.
- Set up GitHub Actions for: pytest, ruff, layer linter
- Block merges on failure

## Medium Priority

### 3. E2E / Smoke Tests
No tests exercise the full Telegram bot flow (handler -> service -> repo).
- Create integration tests that mock only the Telegram API
- Test full conversation flows (start -> add topic -> set schedule)

### 4. mypy Integration
Type checking is not enforced beyond what ruff catches.
- Add `mypy --strict` to CI
- Fix any type errors that surface

### 5. Adapt `docs/architecture.md` for Python
The architecture doc is accurate as a pattern description but uses generic examples (mentions "GraphQL resolvers", "React, Vue" for UI layer). Could include Python-specific guidance and remove inapplicable layer descriptions.

### 6. Rate Limit Handling
Photo APIs have rate limits (Pexels: 200/hr, Unsplash: 50/hr) but we don't implement request throttling.
- Add rate limit tracking (headers return remaining count)
- Implement backoff when approaching limits
- Queue photo requests during rate-limited periods

## Low Priority

### 7. Multi-Instance Support
Current design assumes single bot instance (in-memory JobQueue).
- If scaling needed: move to external scheduler (APScheduler with Redis/DB backend)
- Or use webhook mode with a proper web server

### 8. Photo Caching
Currently every scheduled send makes an API call. Could cache photo URLs.
- Pre-fetch and cache N photo URLs per topic
- Refresh cache periodically
- Reduces API calls and improves reliability

### 9. User Analytics
No tracking of usage patterns.
- Add simple counters: photos sent per user, popular topics, schedule distributions
- Admin command to view stats

---

## Resolved (2026-03-21)

The following critical items from the original Harness Kit template were resolved:

1. **Dead JavaScript Linter** — `tools/ai-linters/layer-dependency-check.js` deleted (was already removed in a prior session). Python equivalent at `layer-dependency-check.py` is the active linter.
2. **Broken GitHub Actions Workflow** — `.github/workflows/ai-garbage-collect.yml` deleted. Used Node.js/npm for a Python project. CI pipeline is a separate task (see item #2 above).
3. **Stale `docs/agent-linters.md`** — Rewritten. Now describes the Python AST linter and ruff configuration instead of ESLint/TypeScript.
4. **Stale `docs/plans/README.md`** — Rewritten. Now lists actual directory contents instead of non-existent `roadmap.md`, `active-tasks/`, `arch-decisions/`.
5. **Version Mismatch in `pyproject.toml`** — Updated from `0.1.0` to `0.2.3` to match `BOT_VERSION` in `src/config/constants.py`.
6. **Stale Test Counts** — `docs/testing.md` updated to 108 tests (34 integration + 74 unit). `README.md` updated to use generic wording.
7. **`opencode-init.md` JS Reference** — Updated `layer-dependency-check.js` to `.py`.
8. **`AGENTS.md` Node.js/TypeScript References** — Sections 3, 5, 6 rewritten for Python (pytest, ruff, snake_case, 4-space indent, etc.).
9. **`docs/deployment.md` Wrong Branch** — Updated `implementing-daily-photo-bot` to `master`.

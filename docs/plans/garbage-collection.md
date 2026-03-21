# Garbage Collection — Known Tech Debt

Items to address in future sessions. Ordered by priority.

**Last Audited:** 2026-03-21

## Critical — Stale / Broken Artifacts

### 1. Dead JavaScript Linter
**File:** `tools/ai-linters/layer-dependency-check.js`
**Issue:** Scans for `.ts`/`.js`/`.tsx` files. This is a Python project — the file does nothing.
**Origin:** Carried over from the original Harness Engineering Kit template (Node.js-oriented).
**Fix:** Delete the file. The Python equivalent (`layer-dependency-check.py`) is the active linter.

### 2. Broken GitHub Actions Workflow
**File:** `.github/workflows/ai-garbage-collect.yml`
**Issue:** Uses `actions/setup-node@v4`, `npm install`, and `npx @anthropic-ai/claude-code` — none of which apply to this Python project. There is no `package.json`. This workflow will always fail.
**Fix:** Either delete the workflow or rewrite it for Python (setup-python, pip install, pytest, ruff, layer linter). Requires human decision on whether to use an AI agent for automated cleanup or a standard CI pipeline.

### 3. Stale `docs/agent-linters.md`
**Issue:** References ESLint, TypeScript, custom ESLint plugins, and `scripts/lint/`. This project uses Python + ruff + a custom Python AST linter.
**Fix:** Rewrite to describe the Python AST linter at `tools/ai-linters/layer-dependency-check.py` and ruff configuration in `pyproject.toml`.

### 4. Stale `docs/plans/README.md`
**Issue:** References non-existent directories: `roadmap.md`, `active-tasks/`, `arch-decisions/`. Actual contents are: `agent-log.md`, `garbage-collection.md`, `v2-feedback-strategy.md`.
**Fix:** Update to reflect actual directory contents.

### 5. Version Mismatch in `pyproject.toml`
**Issue:** `pyproject.toml` declares `version = "0.1.0"` but `docs/state.md` and `BOT_VERSION` constant say `0.2.2`.
**Fix:** Update `pyproject.toml` version to `"0.2.2"`.

### 6. Stale Test Counts in Documentation
**Issue:** `docs/testing.md` says "79 tests (20 integration + 59 unit)". `docs/state.md` says "106/106 tests passing". Actual count is **108 tests passing** (34 integration + 74 unit).
**Fix:** Update both files with correct counts.

### 7. `opencode-init.md` References JS Linter
**Issue:** Says "Pay attention to the execution of the `tools/ai-linters/layer-dependency-check.js` script" — should reference `.py`.
**Fix:** Update reference to `layer-dependency-check.py`.

## High Priority

### 8. Timezone Support
Currently all schedule times are UTC. Users may expect local time zones.
- Add `timezone` field to `schedules` table
- Accept timezone during schedule setup (or infer from Telegram locale)
- Convert fixed-time schedules to UTC internally

### 9. CI/CD Pipeline
No automated pipeline exists. Manual `python -m pytest` and `ruff check` only.
- Set up GitHub Actions for: pytest, ruff, layer linter
- Block merges on failure
- Replace the broken `ai-garbage-collect.yml` with a working Python CI workflow

## Medium Priority

### 10. E2E / Smoke Tests
No tests exercise the full Telegram bot flow (handler -> service -> repo).
- Create integration tests that mock only the Telegram API
- Test full conversation flows (start -> add topic -> set schedule)

### 11. mypy Integration
Type checking is not enforced beyond what ruff catches.
- Add `mypy --strict` to CI
- Fix any type errors that surface

### 12. Adapt Harness Kit Docs for Python
Some original Harness Kit docs still reference TypeScript/Node.js patterns:
- `docs/architecture.md` — examples are generic, could include Python-specific guidance
- `docs/agent-linters.md` — references JS linter (see item #3 above)

### 13. Rate Limit Handling
Photo APIs have rate limits (Pexels: 200/hr, Unsplash: 50/hr) but we don't implement request throttling.
- Add rate limit tracking (headers return remaining count)
- Implement backoff when approaching limits
- Queue photo requests during rate-limited periods

## Low Priority

### 14. Multi-Instance Support
Current design assumes single bot instance (in-memory JobQueue).
- If scaling needed: move to external scheduler (APScheduler with Redis/DB backend)
- Or use webhook mode with a proper web server

### 15. Photo Caching
Currently every scheduled send makes an API call. Could cache photo URLs.
- Pre-fetch and cache N photo URLs per topic
- Refresh cache periodically
- Reduces API calls and improves reliability

### 16. User Analytics
No tracking of usage patterns.
- Add simple counters: photos sent per user, popular topics, schedule distributions
- Admin command to view stats

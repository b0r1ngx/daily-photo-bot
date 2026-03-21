# Garbage Collection — Known Tech Debt

Items to address in future sessions. Ordered by priority.

## High Priority

### 1. Timezone Support
Currently all schedule times are UTC. Users may expect local time zones.
- Add `timezone` field to `schedules` table
- Accept timezone during schedule setup (or infer from Telegram locale)
- Convert fixed-time schedules to UTC internally

### 2. CI/CD Pipeline
No automated pipeline exists. Manual `python -m pytest` and `ruff check` only.
- Set up GitHub Actions (or equivalent) for: pytest, ruff, layer linter
- Block merges on failure

## Medium Priority

### 3. E2E / Smoke Tests
No tests exercise the full Telegram bot flow (handler → service → repo).
- Create integration tests that mock only the Telegram API
- Test full conversation flows (start → add topic → set schedule)

### 4. mypy Integration
Type checking is not enforced beyond what ruff catches.
- Add `mypy --strict` to CI
- Fix any type errors that surface

### 5. Adapt Harness Kit Docs for Python
Some original Harness Kit docs still reference TypeScript/Node.js patterns:
- `docs/architecture.md` — examples use TypeScript syntax
- `docs/agent-linters.md` — references JS linter

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

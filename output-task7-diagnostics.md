# Task 7: Diagnostic Report — Why @b0r1ngx Stopped Getting Images

**Generated:** 2026-03-21
**Bot Version:** 0.2.3

---

## How Photo Delivery Works

1. On bot startup, `_reload_schedules()` (`src/main.py:105-159`) loads ALL active schedules from DB and registers in-memory `JobQueue` jobs.
2. Each job periodically calls `_send_scheduled_photo()` (`src/runtime/handlers/schedule_handler.py:256-313`).
3. The job: gets topic name -> calls `photo_service.get_photo()` (Pexels primary, Unsplash fallback) -> sends via `context.bot.send_photo()` -> updates `last_sent_at`.
4. If any step fails, the exception is caught and logged, but **the job stays registered** — it will retry on the next trigger.

---

## Possible Root Causes (Ranked by Likelihood)

### Most Likely

| # | Cause | How to Check |
|---|---|---|
| 1 | **Schedule deactivated** — `/stop` command or topic deletion disabled the schedule | Check `schedules.is_active` (see SQL below) |
| 2 | **Topic soft-deleted** — `topics.is_active = 0`, so `_send_scheduled_photo` silently skips it | Check `topics.is_active` (see SQL below) |
| 3 | **Bot process crashed and wasn't restarted** — jobs only exist in memory | `systemctl status daily-photo-bot` on VPS |
| 4 | **API key expired or rate-limited** — both Pexels and Unsplash fail consistently | Check VPS logs for "Failed to fetch photo" |

### Less Likely

| # | Cause | How to Check |
|---|---|---|
| 5 | **Photo exhaustion** — all photos for the topic have been sent (500+ threshold, reset may have failed) | Check `sent_photos` count for the topic |
| 6 | **User blocked the bot** — `send_photo()` raises `Forbidden: bot was blocked by the user` | Check VPS logs for "Failed to send photo" |
| 7 | **`get_owner_telegram_id` returned None during reload** — schedule silently skipped at startup (`main.py:119-124`) | Check VPS logs for "No user found for topic_id" |
| 8 | **Timezone issue** — fixed-time schedule uses UTC, user expects local time. Not "stopped" but wrong timing. | Check `schedule_type` and `value` |

### Unlikely

| # | Cause | Description |
|---|---|---|
| 9 | Network issues on VPS | Both APIs unreachable |
| 10 | SQLite database corruption | Would affect all users |
| 11 | Chat ID changed | Extremely rare Telegram behavior |

---

## Silent Failure Points in Code

These are places where delivery can fail WITHOUT the user being notified:

1. **`schedule_handler.py:261-262`** — Returns silently if `job`, `job.data`, or `job.chat_id` is missing
2. **`schedule_handler.py:270-272`** — If topic is inactive, logs a warning and returns (no message to user)
3. **`schedule_handler.py:282-284`** — Photo fetch exception caught, logged, returns (no message to user)
4. **`schedule_handler.py:306-308`** — Telegram send exception caught, logged, returns (no message to user)
5. **`main.py:119-124`** — During schedule reload, if user not found for a topic, schedule is silently skipped

---

## Diagnostic SQL Queries

Run these on your VPS:

```bash
sqlite3 data/bot.db <<'SQL'
.mode column
.headers on

-- Step 1: Find the user
SELECT * FROM users WHERE username = 'b0r1ngx';

-- Step 2: Check their topics
SELECT t.id, t.name, t.is_free, t.is_active, t.created_at
FROM topics t
JOIN users u ON t.user_id = u.id
WHERE u.username = 'b0r1ngx';

-- Step 3: Check their schedules
SELECT s.id, s.topic_id, s.schedule_type, s.value, s.is_active, s.last_sent_at
FROM schedules s
JOIN topics t ON s.topic_id = t.id
JOIN users u ON t.user_id = u.id
WHERE u.username = 'b0r1ngx';

-- Step 4: Check last 20 photos sent to them
SELECT sp.topic_id, sp.photo_id, sp.source, sp.sent_at
FROM sent_photos sp
JOIN topics t ON sp.topic_id = t.id
JOIN users u ON t.user_id = u.id
WHERE u.username = 'b0r1ngx'
ORDER BY sp.sent_at DESC
LIMIT 20;

-- Step 5: Count total photos per topic (check exhaustion)
SELECT t.name, COUNT(sp.id) AS photos_sent
FROM topics t
JOIN users u ON t.user_id = u.id
LEFT JOIN sent_photos sp ON sp.topic_id = t.id
WHERE u.username = 'b0r1ngx'
GROUP BY t.id;
SQL
```

## Diagnostic Log Commands

```bash
# Check if bot is running
systemctl status daily-photo-bot

# Check recent errors
journalctl -u daily-photo-bot --since "1 week ago" | grep -i "error\|exception\|failed"

# Check if schedules were reloaded on last startup
journalctl -u daily-photo-bot --since "1 week ago" | grep -i "reload\|schedule\|registered"

# Check for your specific user's delivery issues
journalctl -u daily-photo-bot --since "1 week ago" | grep -i "b0r1ngx"

# Check for photo fetch failures
journalctl -u daily-photo-bot --since "1 week ago" | grep "Failed to fetch photo"

# Check for send failures
journalctl -u daily-photo-bot --since "1 week ago" | grep "Failed to send photo"

# Check for "No user found" during reload
journalctl -u daily-photo-bot --since "1 week ago" | grep "No user found"
```

---

## What You'll Learn From the Results

| SQL Result | Diagnosis | Fix |
|---|---|---|
| `schedules.is_active = 0` | Schedule was deactivated (by `/stop` or topic deletion) | Re-set the schedule via the bot |
| `topics.is_active = 0` | Topic was deleted | Re-add the topic via the bot |
| No schedule rows at all | Schedule was never created or was removed | Create a new schedule |
| `last_sent_at` is recent | Delivery IS working — check your Telegram notifications | No code fix needed |
| `last_sent_at` is old + bot is running | Job is registered but failing silently | Check logs for exceptions |
| Bot is not running | Process crashed | Restart: `systemctl restart daily-photo-bot` |
| Photos sent count >= 500 | Photo exhaustion — should auto-reset but may have bugged | Check `photo_service.py` exhaustion logic |

---

## Action Required

Please run the SQL queries and log commands above on your VPS and share the output. This will pinpoint the exact cause.

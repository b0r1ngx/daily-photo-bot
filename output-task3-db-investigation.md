# Task 3: Database & Statistics Investigation Report

**Generated:** 2026-03-21
**Bot Version:** 0.2.3
**Source:** `src/repo/database.py` (DDL), all repo files, all handler files

---

## 1. Complete Database Schema

### Table: `users`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment internal ID |
| `telegram_id` | INTEGER UNIQUE NOT NULL | Telegram user ID |
| `username` | TEXT | Telegram @username (nullable) |
| `first_name` | TEXT | Telegram display name (nullable) |
| `language_code` | TEXT | Telegram client language code, e.g. "en", "ru" (nullable) |
| `created_at` | TEXT | UTC timestamp, auto-set on insert |

### Table: `topics`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `user_id` | INTEGER FK->users | Owner |
| `name` | TEXT NOT NULL | Topic search term, e.g. "parrots" |
| `is_free` | INTEGER DEFAULT 1 | 1=free tier, 0=paid |
| `is_active` | INTEGER DEFAULT 1 | 1=active, 0=soft-deleted |
| `created_at` | TEXT | UTC timestamp |

### Table: `schedules`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `topic_id` | INTEGER FK->topics UNIQUE | One schedule per topic |
| `schedule_type` | TEXT | 'interval' or 'fixed_time' |
| `value` | TEXT | Seconds (interval) or "HH:MM" (fixed_time) |
| `is_active` | INTEGER DEFAULT 1 | 1=active, 0=deactivated |
| `last_sent_at` | TEXT | UTC timestamp of last successful send |

### Table: `sent_photos`
| Column | Type | Description |
|--------|------|-------------|
| `id` | INTEGER PK | Auto-increment |
| `topic_id` | INTEGER FK->topics | Which topic triggered the send |
| `photo_id` | TEXT NOT NULL | External API photo ID |
| `source` | TEXT NOT NULL | 'pexels' or 'unsplash' |
| `sent_at` | TEXT | UTC timestamp, auto-set |
| | UNIQUE | `(topic_id, photo_id, source)` — dedup constraint |

### Indexes
- `idx_sent_photos_topic` on `sent_photos(topic_id)`
- `idx_topics_user` on `topics(user_id)`
- `idx_schedules_active` on `schedules(is_active)`

---

## 2. What Data We Collect About Users

| Data | When Collected | How |
|------|---------------|-----|
| Telegram user ID | First `/start` | `user_repo.get_or_create()` |
| @username | Every handler call | `ensure_user()` in `topic_service.py` updates it |
| First name | First `/start` | From `update.effective_user` |
| Language code | `/start` + subsequent calls | Updated if Telegram client language changes |
| Account creation time | First `/start` | Auto-set by SQLite `datetime('now')` |
| Topic names | User adds a topic | Stored as search terms |
| Schedule preferences | User configures schedule | Type + value stored |
| Every photo sent | On successful send | `sent_photos` table records `(topic_id, photo_id, source, timestamp)` |

---

## 3. Statistics We CAN Extract (run on VPS via `sqlite3 data/bot.db`)

### User Analytics
```sql
-- Total users
SELECT COUNT(*) AS total_users FROM users;

-- New users today
SELECT COUNT(*) FROM users WHERE created_at >= date('now');

-- New users this week
SELECT COUNT(*) FROM users WHERE created_at >= date('now', '-7 days');

-- Language distribution
SELECT language_code, COUNT(*) AS count FROM users
GROUP BY language_code ORDER BY count DESC;

-- User growth per week
SELECT strftime('%Y-W%W', created_at) AS week, COUNT(*) AS new_users
FROM users GROUP BY week ORDER BY week;
```

### Topic Analytics
```sql
-- Topics per user
SELECT u.username, u.first_name, COUNT(t.id) AS topics
FROM users u LEFT JOIN topics t ON t.user_id = u.id AND t.is_active = 1
GROUP BY u.id ORDER BY topics DESC;

-- Most popular topic names
SELECT LOWER(name) AS topic, COUNT(*) AS count
FROM topics WHERE is_active = 1
GROUP BY topic ORDER BY count DESC;

-- Free vs paid topics
SELECT is_free, COUNT(*) FROM topics WHERE is_active = 1 GROUP BY is_free;

-- Deleted topics count (high = UX issue)
SELECT COUNT(*) AS deleted FROM topics WHERE is_active = 0;
```

### Schedule Analytics
```sql
-- Schedule adoption rate
SELECT
  (SELECT COUNT(*) FROM topics WHERE is_active = 1) AS active_topics,
  (SELECT COUNT(*) FROM schedules WHERE is_active = 1) AS with_schedule;

-- Schedule type distribution
SELECT schedule_type, COUNT(*) FROM schedules WHERE is_active = 1
GROUP BY schedule_type;

-- Removed schedules
SELECT COUNT(*) FROM schedules WHERE is_active = 0;
```

### Photo Delivery Analytics
```sql
-- Total photos ever sent
SELECT COUNT(*) FROM sent_photos;

-- Photos sent today
SELECT COUNT(*) FROM sent_photos WHERE sent_at >= date('now');

-- Photos per day (trend)
SELECT DATE(sent_at) AS day, COUNT(*) AS photos
FROM sent_photos GROUP BY day ORDER BY day;

-- Photo source distribution
SELECT source, COUNT(*) FROM sent_photos GROUP BY source;

-- Topics approaching exhaustion (near 500 threshold)
SELECT topic_id, COUNT(*) AS sent FROM sent_photos
GROUP BY topic_id HAVING sent > 400 ORDER BY sent DESC;
```

---

## 4. What We CANNOT See (Gaps)

| Missing Data | Impact | Recommendation |
|---|---|---|
| **User button clicks** | Cannot track which features users discover/use | Add METRIC log lines (see `v2-feedback-strategy.md` section 1B) |
| **Photo delivery failures** | Logged to stdout but lost on restart | Consider an `error_log` table or persistent log file |
| **User engagement** | No way to know if users view received photos | Telegram limitation — no read receipts for bots |
| **Schedule change history** | No audit trail of schedule modifications | Add an `events` table if needed |
| **Bot restart history** | No persistent record of when bot restarted | Add startup timestamp to a `bot_events` table |

---

## 5. Answers to Your Specific Questions

### "Do we log info about what the user clicked?"
**NO.** Handlers do not log user interactions. The `v2-feedback-strategy.md` document (section 1B) recommends adding structured `METRIC:` log lines but they were never implemented.

### "Do we log info about that we send a photo to a user?"
**YES, partially.** The `sent_photos` table is effectively a photo delivery log — it records every successful send with `(topic_id, photo_id, source, sent_at)`. To get per-user data, JOIN with `topics` and `users`:

```sql
-- All photos sent to a specific user
SELECT u.username, t.name AS topic, sp.photo_id, sp.source, sp.sent_at
FROM sent_photos sp
JOIN topics t ON sp.topic_id = t.id
JOIN users u ON t.user_id = u.id
WHERE u.username = 'b0r1ngx'
ORDER BY sp.sent_at DESC;
```

**Failed sends** are only logged to stdout via `logger.exception()` at `schedule_handler.py:283` and `schedule_handler.py:307`. These are lost after process restart unless the system captures stdout (e.g., `journalctl`).

---

## 6. Pre-Built Analytics Script

Run this on your VPS to get a full snapshot:

```bash
sqlite3 data/bot.db <<'SQL'
.mode column
.headers on

SELECT '=== USER STATS ===' AS section;
SELECT COUNT(*) AS total_users FROM users;
SELECT COUNT(*) AS new_this_week FROM users WHERE created_at >= date('now', '-7 days');
SELECT language_code, COUNT(*) AS count FROM users GROUP BY language_code ORDER BY count DESC;

SELECT '=== TOPIC STATS ===' AS section;
SELECT COUNT(*) AS active_topics FROM topics WHERE is_active = 1;
SELECT COUNT(*) AS deleted_topics FROM topics WHERE is_active = 0;
SELECT is_free, COUNT(*) AS count FROM topics WHERE is_active = 1 GROUP BY is_free;
SELECT LOWER(name) AS topic, COUNT(*) AS count FROM topics WHERE is_active = 1 GROUP BY topic ORDER BY count DESC LIMIT 10;

SELECT '=== SCHEDULE STATS ===' AS section;
SELECT COUNT(*) AS active_schedules FROM schedules WHERE is_active = 1;
SELECT schedule_type, COUNT(*) AS count FROM schedules WHERE is_active = 1 GROUP BY schedule_type;

SELECT '=== PHOTO DELIVERY ===' AS section;
SELECT COUNT(*) AS total_photos_sent FROM sent_photos;
SELECT COUNT(*) AS sent_today FROM sent_photos WHERE sent_at >= date('now');
SELECT source, COUNT(*) AS count FROM sent_photos GROUP BY source;
SELECT DATE(sent_at) AS day, COUNT(*) AS photos FROM sent_photos GROUP BY day ORDER BY day DESC LIMIT 14;
SQL
```

---

## Reference
- Database DDL: `src/repo/database.py:19-59`
- Pre-written SQL queries: `docs/plans/v2-feedback-strategy.md` (section 1A)
- Photo delivery logging: `src/runtime/handlers/schedule_handler.py:256-313`

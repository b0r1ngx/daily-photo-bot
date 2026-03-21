# V2 Feedback Collection Strategy

**Created:** 2026-03-16
**Bot Version:** 0.2.0
**Context:** V2 is about to be deployed. V1 had ~20 users (mostly Russian-speaking friends/family). V2 adds: i18n (EN/ES/RU/PT/ZH), topic management (rename/delete), search quality enrichment for non-English users, instant photo preview on topic creation, schedule removal, and /version command.

---

## 1. What to Measure — Quantitative Signals from Existing Data

### 1A. Metrics Extractable from Current SQLite Schema (Zero Code Changes)

The current schema (`users`, `topics`, `schedules`, `sent_photos`, `schema_version`) already contains rich behavioral data. All queries below can be run ad-hoc via `sqlite3 data/bot.db` on the VPS.

#### User Growth & Retention

```sql
-- New users per week
SELECT strftime('%Y-W%W', created_at) AS week, COUNT(*) AS new_users
FROM users GROUP BY week ORDER BY week;

-- Language distribution
SELECT language_code, COUNT(*) AS user_count
FROM users GROUP BY language_code ORDER BY user_count DESC;

-- Users who joined AFTER V2 deploy (replace date with actual deploy date)
SELECT COUNT(*) FROM users WHERE created_at >= '2026-03-16';
```

#### Topic Engagement

```sql
-- Topics per user
SELECT u.telegram_id, u.first_name, u.language_code, COUNT(t.id) AS topic_count
FROM users u LEFT JOIN topics t ON t.user_id = u.id AND t.is_active = 1
GROUP BY u.id ORDER BY topic_count DESC;

-- Free vs paid topics
SELECT is_free, COUNT(*) AS count FROM topics WHERE is_active = 1 GROUP BY is_free;

-- Deleted topics (high deletion rate = discoverability/quality issue)
SELECT COUNT(*) AS deleted_topics FROM topics WHERE is_active = 0;

-- Most popular topic names
SELECT name, COUNT(*) AS count FROM topics WHERE is_active = 1
GROUP BY LOWER(name) ORDER BY count DESC;

-- Topics by language
SELECT u.language_code, t.name, t.created_at
FROM topics t JOIN users u ON t.user_id = u.id
WHERE t.is_active = 1 ORDER BY u.language_code, t.created_at;
```

#### Schedule Behavior

```sql
-- Schedule adoption rate
SELECT
  (SELECT COUNT(*) FROM topics WHERE is_active = 1) AS total_active_topics,
  (SELECT COUNT(*) FROM schedules WHERE is_active = 1) AS topics_with_schedule;

-- Schedule type distribution
SELECT schedule_type, COUNT(*) FROM schedules WHERE is_active = 1 GROUP BY schedule_type;

-- Removed schedules (V2 feature)
SELECT COUNT(*) FROM schedules WHERE is_active = 0;
```

#### Photo Delivery Health

```sql
-- Photo source distribution (is Unsplash fallback triggering often?)
SELECT source, COUNT(*) FROM sent_photos GROUP BY source;

-- Photos sent per day (trend)
SELECT DATE(sent_at) AS day, COUNT(*) AS photos FROM sent_photos GROUP BY day ORDER BY day;

-- Topics approaching exhaustion (near 500 threshold)
SELECT topic_id, COUNT(*) AS sent_count FROM sent_photos
GROUP BY topic_id HAVING sent_count > 400 ORDER BY sent_count DESC;
```

### 1B. Recommended Lightweight Logging Additions

Add structured `logger.info` calls in handlers for `grep`-based analytics:

| Event | File | Log Line |
|---|---|---|
| Topic renamed | `topic_manage_handler.py` | `METRIC:topic_renamed user=%d lang=%s` |
| Topic deleted | `topic_manage_handler.py` | `METRIC:topic_deleted user=%d lang=%s` |
| Schedule removed | `schedule_handler.py` | `METRIC:schedule_removed user=%d lang=%s topic_id=%d` |
| My Topics opened | `topic_manage_handler.py` | `METRIC:my_topics_opened user=%d lang=%s count=%d` |
| First preview sent | `start_handler.py` | `METRIC:first_preview_sent user=%d lang=%s topic=%s` |
| First preview failed | `start_handler.py` | `METRIC:first_preview_failed user=%d lang=%s error=%s` |
| Query enriched | `photo_service.py` | `METRIC:query_enriched lang=%s original=%s enriched=%s` |
| /version used | `help_handler.py` | `METRIC:version_checked user=%d` |

**Extract from VPS logs:**
```bash
for event in topic_renamed topic_deleted schedule_removed my_topics_opened first_preview_sent query_enriched version_checked; do
  count=$(journalctl -u daily-photo-bot --since "2026-03-16" | grep -c "METRIC:$event")
  echo "$event: $count"
done
```

---

## 2. What to Ask Users — Targeted V2 Feedback Questions

### Short Survey (5 questions)

1. **Feature Discovery:** "Did you find the 📋 My Topics menu? Did you try renaming or deleting a topic?"
2. **Search Quality (non-English):** "Вы создавали темы на русском? Фотографии стали лучше?"
3. **Instant Preview:** "When you added a new topic, did you see the first photo right away? Was it relevant?"
4. **Schedule Management:** "Is it clear how to change or remove a schedule?"
5. **Open-ended:** "What's the ONE thing you'd most want added or changed?"

---

## 3. How to Collect Feedback

### Method 1: `/feedback` Command (Recommended)
~20 lines of code, logs feedback to stdout. Cost: 2 translation keys × 5 languages.

### Method 2: Direct Messages (Most Effective for Small Base)
One-time script to send survey to all users. Read replies in Telegram chat UI.

### Method 3: Behavioral Observation from DB (Passive)
Weekly `sqlite3` queries — zero user friction.

---

## 4. When to Collect — Timeline

| Phase | When | Action |
|---|---|---|
| Baseline | Day 0 (deploy) | Snapshot DB state, send "What's New" announcement |
| Silent observation | Days 1–7 | Watch METRIC logs and DB, don't ask users |
| Targeted outreach | Day 7–10 | Send personalized survey to all users |
| Data synthesis | Day 14 | Full analytics pass, compile findings |
| Decision point | Day 21 | Decide: iterate V2 or plan V3 |

---

## 5. Success Criteria

| Metric | Target | Failure Signal |
|---|---|---|
| Zero crash increase | No new error types post-deploy | New exceptions in logs |
| Schedules keep running | 100% of pre-V2 schedules still active | Schedule count drops |
| Topic management used | ≥3 users try My Topics within 14 days | 0 users open it |
| Rename/delete used | ≥1 rename OR delete within 14 days | Nobody uses it |
| Instant preview works | >80% success rate | High failure rate |
| No user loss | No users go silent post-V2 | Active users stop interacting |

### Decision Matrix

| Condition | Decision |
|---|---|
| Crashes or data issues | 🔴 Hotfix immediately |
| V2 features unused after 2 weeks | 🟡 Iterate V2 — focus on discoverability |
| Features used but users confused | 🟡 Iterate V2 — improve UX |
| Features used, users happy, want new things | 🟢 Move to V3 |

---

## Appendix: "What's New" Announcement

```
🎉 Daily Photo Bot v0.2.0 — What's New!

🌍 Multilingual — Bot now speaks your language (RU, ES, PT, ZH)
📋 My Topics — View, rename ✏️ or delete 🗑 your topics
📸 Instant Preview — Get your first photo immediately when you add a topic
🗑 Remove Schedule — Remove a schedule without deleting the topic
🔢 /version — Check which version you're on

Try the 📋 My Topics button to explore!
```

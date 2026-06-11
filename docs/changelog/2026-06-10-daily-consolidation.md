# Daily consolidation to keep health_checks table bounded

**Date:** 2026-06-10

## Problem

The `health_checks` table grows at ~1,440 rows/URL/day (one check every 60s). For 10 URLs that's ~5.2M rows/year with no cleanup.

## Solution: Option 3 — Daily consolidation + retention

A new `daily_health_summaries` table stores aggregated metrics per (url_id, date). Raw `health_checks` data older than `RETENTION_DAYS` (default: 7) is consolidated and purged.

### New files

- `src/healthchecker/domain/models/daily_summary.py` — DailySummary entity
- `src/healthchecker/domain/repositories/daily_summary_repository.py` — repository interface
- `src/healthchecker/infrastructure/persistence/daily_summary_repository.py` — MySQL implementation
- `src/healthchecker/application/use_cases/consolidate_summaries.py` — consolidation use case
- `tests/domain/test_daily_summary_model.py` — model tests
- `tests/application/test_consolidate_summaries.py` — use case tests

### Modified files

- `database.py` — added `daily_health_summaries` table to schema
- `config.py` — added `RETENTION_DAYS` setting (env var, default 7)
- `health_check_repository.py` — added `get_dates_needing_consolidation`, `get_raw_for_date`, `purge_older_than` methods
- `scheduler.py` — runs consolidation once per day (on startup + when date changes)
- `results.py` — falls back to daily summaries when raw data is exhausted (limit exceeds available rows)
- `bot.py` — accepts `summary_repo` dependency and passes it to ResultsHandler
- `main.py` — wires `ConsolidateDailySummariesUseCase` and `MySqlDailySummaryRepository`

### Schema

```sql
CREATE TABLE daily_health_summaries (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    url_id BIGINT NOT NULL,
    date DATE NOT NULL,
    checks_count INT NOT NULL,
    avg_ttfb_ms FLOAT,
    min_ttfb_ms FLOAT,
    max_ttfb_ms FLOAT,
    min_ssl_days_remaining INT,
    healthy_count INT NOT NULL,
    unhealthy_count INT NOT NULL,
    last_http_status INT,
    last_ssl_expiration_date DATETIME,
    last_checked_at DATETIME,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (url_id) REFERENCES urls(id) ON DELETE CASCADE,
    UNIQUE KEY uk_url_date (url_id, date)
);
```

### Retention flow

1. Consolidation use case finds all (url_id, date) combos in raw data without a summary
2. Aggregates TTFB (avg/min/max), SSL days (min), health count, last status
3. Saves to `daily_health_summaries` (upsert by url_id + date)
4. Purges raw rows where `DATE(checked_at) <= (today - RETENTION_DAYS)`

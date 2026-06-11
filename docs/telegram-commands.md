# Telegram Bot Commands

## Overview

The bot allows full management of monitored URLs and health check queries. All commands are available immediately after sending `/start`.

## Commands

### /start

Welcome message with available commands.

```
/start
```

### /add

Add a URL to monitor.

```
/add <url> [name] [--alert-days N]
```

**Arguments:**
- `url` (required) — Full URL including protocol (`https://example.com`)
- `name` (optional) — Human-readable name (defaults to the URL itself)
- `--alert-days N` (optional) — Override SSL expiry alert threshold (default: 30)

**Example:**
```
/add https://google.com Google --alert-days 14
```

### /list

List all monitored URLs with their latest health check status.

```
/list
```

Output format:
```
📋 Monitored URLs (3):

1. Example (https://example.com)
   ✅ HTTP 200 | 120ms | SSL: 45 days
   Last checked: 2026-06-10 12:00:00

2. My App (https://myapp.io/health)
   ❌ HTTP 503 | Error: Service Unavailable
   Last checked: 2026-06-10 12:00:00
```

### /delete

Remove a URL from monitoring.

```
/delete <id>
```

**Arguments:**
- `id` (required) — URL ID from `/list`

**Example:**
```
/delete 3
```

### /check

Run a health check immediately.

```
/check [id]
```

**Arguments:**
- `id` (optional) — Specific URL ID to check. If omitted, checks all URLs.

**Example:**
```
/check 1
```

### /results

Show health check history for a URL.

```
/results <id> [--limit N]
```

**Arguments:**
- `id` (required) — URL ID
- `--limit N` (optional) — Number of results to show (default: 5)

**Example:**
```
/results 1 --limit 10
```

## Alerts

Alerts are sent automatically by the bot when:
- **SSL_EXPIRY**: A URL's SSL certificate expires within the configured threshold
- **HTTP_DOWN**: A URL returns a non-2xx status code or is unreachable

There is no explicit command to configure alerts globally — use `--alert-days` in `/add`. Global defaults are set via the `DEFAULT_ALERT_DAYS` environment variable.

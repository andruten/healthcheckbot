# Domain Model

## Bounded Context

Single bounded context: **Health Monitoring**. All domain concepts relate to monitoring URL health and notifying about issues.

## Entities

### Url

```python
class Url:
    id: UrlId
    name: str
    url: str
    alert_before_days: int       # days threshold for SSL expiry alerts
    is_active: bool
    created_at: datetime
    updated_at: datetime
```

An `Url` is the central entity — it represents a monitored endpoint. It has identity (`UrlId`) and its state can change over time.

### Alert

```python
class Alert:
    id: AlertId
    url_id: UrlId
    alert_type: AlertType       # enum: SSL_EXPIRY, HTTP_DOWN
    message: str
    is_sent: bool
    created_at: datetime
```

An `Alert` represents a notification event triggered when a condition is met (SSL about to expire, HTTP down).

## Value Objects

| Value Object   | Attributes                    | Notes                        |
|----------------|-------------------------------|------------------------------|
| `UrlId`        | `value: int`                  | Wraps primary key            |
| `AlertId`      | `value: int`                  | Wraps primary key            |
| `HttpStatus`   | `code: int`                   | HTTP response status code    |
| `Ttfb`         | `milliseconds: float`         | Time To First Byte           |
| `SslInfo`      | `expiration_date: datetime`, `days_remaining: int` | SSL certificate data |
| `HealthCheck`  | `url_id`, `http_status`, `ttfb`, `ssl_info`, `is_healthy`, `error_message`, `checked_at` | Result of a single check |
| `AlertConfig`  | `alert_before_days: int`      | Threshold configuration      |
| `AlertType`    | enum: `SSL_EXPIRY`, `HTTP_DOWN` | Category of alert          |

### DailySummary (Value Object)

```python
@dataclass
class DailySummary:
    url_id: int
    summary_date: date
    checks_count: int
    avg_ttfb_ms: float
    min_ttfb_ms: float
    max_ttfb_ms: float
    min_ssl_days_remaining: int | None
    healthy_count: int
    unhealthy_count: int
    last_http_status: int | None
    last_ssl_expiration_date: datetime | None
    last_checked_at: datetime | None
```

Aggregated data for one URL over one day. Built by consolidating raw `HealthCheck` records.

### HealthCheck (Value Object)

Represents the immutable result of a health check at a point in time. Two checks on the same URL at different times are different objects — there is no identity.

```python
@dataclass(frozen=True)
class HealthCheck:
    url_id: int
    http_status: int | None
    ttfb_ms: float | None
    ssl_expiration_date: datetime | None
    ssl_days_remaining: int | None
    is_healthy: bool
    error_message: str | None
    checked_at: datetime
```

## Domain Services

### HealthCheckService

Pure business logic:

```python
class HealthCheckService:
    @staticmethod
    def evaluate_ssl(days_remaining: int, threshold_days: int) -> Alert | None
```

- Determines whether an SSL certificate is expiring within the configured threshold
- Creates an `Alert` if the threshold is breached
- Independent of any infrastructure

## Repository Interfaces

```
UrlRepository:
  - get_all_active() -> list[Url]
  - get_by_id(id: UrlId) -> Url | None
  - add(url: Url) -> Url
  - update(url: Url) -> Url
  - delete(id: UrlId) -> None

HealthCheckRepository:
  - save(check: HealthCheck) -> HealthCheck
  - get_by_url_id(url_id: UrlId, limit: int) -> list[HealthCheck]
  - get_latest_by_url_id(url_id: UrlId) -> HealthCheck | None

AlertRepository:
  - save(alert: Alert) -> Alert
  - get_unsent() -> list[Alert]
  - mark_as_sent(alert_id: AlertId) -> None

DailySummaryRepository:
  - save(summary: DailySummary) -> DailySummary
  - get_by_url_id(url_id: int, limit: int) -> list[DailySummary]
  - get_by_url_id_and_date(url_id: int, date: date) -> DailySummary | None
```

## Aggregate Root

**Url** is the aggregate root. `HealthCheck` and `Alert` belong to the `Url` aggregate — they are always accessed and persisted via the owning `Url`.

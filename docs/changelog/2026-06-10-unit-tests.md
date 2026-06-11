# Add unit tests

**Date:** 2026-06-10

## Summary

Added comprehensive unit test suite covering domain, application, infrastructure, and interface layers.

## Tests Added

### Domain (7 tests)
- `test_alert_model.py` — Alert creation, AlertType enum, mutation
- `test_health_check_model.py` — HealthCheck creation, frozen immutability, error state, equality
- `test_health_check_service.py` — Added test for `build_ssl_alert` with `expiration_date` parameter

### Application (12 tests)
- `test_manage_urls.py` — add, list, delete, get_by_id use cases with mock repository
- `test_get_results.py` — get_latest, get_history with default and custom limits
- `test_check_all_urls.py` — healthy URLs, unhealthy URL, timeout, SSL expiry alert, non-HTTPS skips SSL, exception handling

### Infrastructure (8 tests)
- `test_config.py` — default values and env var overrides
- `test_http_checker.py` — successful request, 404, timeout, request error, unexpected error (using respx)
- `test_ssl_checker.py` — host extraction from HTTPS, HTTP, invalid, and empty URLs

### Interfaces (2 tests)
- `test_scheduler.py` — start/stop cycle, alert generation during loop

## Infrastructure Changes

- Refactored `Settings` to read environment variables on instantiation (was class-level) to support test isolation with `monkeypatch`
- Added test dependencies to `pyproject.toml`: pytest, pytest-asyncio, pytest-mock, respx
- Fixed `pytest.ini_options` config to use `asyncio_mode = "auto"`

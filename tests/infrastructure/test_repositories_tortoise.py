from datetime import date, datetime, timezone

import pytest
from tortoise import Tortoise

from healthchecker.domain.models.url import Url
from healthchecker.domain.models.health_check import HealthCheck
from healthchecker.domain.models.alert import Alert, AlertType
from healthchecker.domain.models.daily_summary import DailySummary
from healthchecker.infrastructure.persistence.url_repository import (
    TortoiseUrlRepository,
)
from healthchecker.infrastructure.persistence.health_check_repository import (
    TortoiseHealthCheckRepository,
)
from healthchecker.infrastructure.persistence.alert_repository import (
    TortoiseAlertRepository,
)
from healthchecker.infrastructure.persistence.daily_summary_repository import (
    TortoiseDailySummaryRepository,
)


@pytest.fixture(scope="module", autouse=True)
async def init_tortoise():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={
            "models": [
                "healthchecker.infrastructure.persistence.tortoise_models",
            ]
        },
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest.fixture
async def url_repo():
    return TortoiseUrlRepository()


@pytest.fixture
async def hc_repo():
    return TortoiseHealthCheckRepository()


@pytest.fixture
async def alert_repo():
    return TortoiseAlertRepository()


@pytest.fixture
async def summary_repo():
    return TortoiseDailySummaryRepository()


@pytest.fixture
async def sample_url(url_repo):
    return await url_repo.add(
        Url.create("https://example.com", name="Example", alert_before_days=30)
    )


@pytest.mark.asyncio
class TestTortoiseUrlRepository:
    async def test_add_and_get_by_id(self, url_repo):
        url = await url_repo.add(Url.create("https://test.com", name="Test"))
        assert url.id is not None
        fetched = await url_repo.get_by_id(url.id)
        assert fetched is not None
        assert fetched.name == "Test"
        assert fetched.url == "https://test.com"

    async def test_get_all_active(self, url_repo):
        await url_repo.add(Url.create("https://a.com", name="A"))
        await url_repo.add(Url.create("https://b.com", name="B"))
        urls = await url_repo.get_all_active()
        assert len(urls) >= 2

    async def test_delete(self, url_repo):
        url = await url_repo.add(Url.create("https://del.com", name="Del"))
        await url_repo.delete(url.id)
        assert await url_repo.get_by_id(url.id) is None


@pytest.mark.asyncio
class TestTortoiseHealthCheckRepository:
    async def test_save_and_get_latest(self, hc_repo, sample_url):
        now = datetime.now(timezone.utc)
        check = HealthCheck(
            id=None,
            url_id=sample_url.id,
            http_status=200,
            ttfb_ms=100.0,
            ssl_expiration_date=now,
            ssl_days_remaining=50,
            is_healthy=True,
            error_message=None,
            checked_at=now,
        )
        saved = await hc_repo.save(check)
        assert saved.id is not None
        assert saved.http_status == 200

        latest = await hc_repo.get_latest_by_url_id(sample_url.id)
        assert latest is not None
        assert latest.http_status == 200

    async def test_get_by_url_id_with_limit(self, hc_repo, sample_url):
        now = datetime.now(timezone.utc)
        for i in range(5):
            await hc_repo.save(
                HealthCheck(
                    id=None,
                    url_id=sample_url.id,
                    http_status=200,
                    ttfb_ms=float(i),
                    ssl_expiration_date=now,
                    ssl_days_remaining=50,
                    is_healthy=True,
                    error_message=None,
                    checked_at=now,
                )
            )
        results = await hc_repo.get_by_url_id(sample_url.id, limit=3)
        assert len(results) == 3

    async def test_purge_older_than(self, hc_repo, sample_url):
        old = datetime(2025, 1, 1, tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        await hc_repo.save(
            HealthCheck(
                id=None,
                url_id=sample_url.id,
                http_status=200,
                ttfb_ms=10.0,
                ssl_expiration_date=now,
                ssl_days_remaining=50,
                is_healthy=True,
                error_message=None,
                checked_at=old,
            )
        )
        deleted = await hc_repo.purge_older_than(date(2025, 6, 1))
        assert deleted >= 1

    async def test_get_dates_needing_consolidation(self, hc_repo, sample_url):
        now = datetime.now(timezone.utc)
        await hc_repo.save(
            HealthCheck(
                id=None,
                url_id=sample_url.id,
                http_status=200,
                ttfb_ms=10.0,
                ssl_expiration_date=now,
                ssl_days_remaining=50,
                is_healthy=True,
                error_message=None,
                checked_at=now,
            )
        )
        pending = await hc_repo.get_dates_needing_consolidation(date(2099, 12, 31))
        filtered = [(uid, d) for uid, d in pending if uid == sample_url.id]
        assert len(filtered) >= 1


@pytest.mark.asyncio
class TestTortoiseAlertRepository:
    async def test_save_and_get_unsent(self, alert_repo, sample_url):
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=None,
            url_id=sample_url.id,
            alert_type=AlertType.SSL_EXPIRY,
            message="Test alert",
            is_sent=False,
            created_at=now,
        )
        saved = await alert_repo.save(alert)
        assert saved.id is not None

        unsent = await alert_repo.get_unsent()
        assert len(unsent) >= 1

    async def test_mark_as_sent(self, alert_repo, sample_url):
        now = datetime.now(timezone.utc)
        alert = Alert(
            id=None,
            url_id=sample_url.id,
            alert_type=AlertType.HTTP_DOWN,
            message="Down",
            is_sent=False,
            created_at=now,
        )
        saved = await alert_repo.save(alert)
        await alert_repo.mark_as_sent(saved.id)
        unsent = await alert_repo.get_unsent()
        assert all(a.id != saved.id for a in unsent)


@pytest.mark.asyncio
class TestTortoiseDailySummaryRepository:
    async def test_save_and_get(self, summary_repo, sample_url):
        s = DailySummary(
            id=None,
            url_id=sample_url.id,
            summary_date=date(2026, 6, 10),
            checks_count=100,
            avg_ttfb_ms=120.0,
            min_ttfb_ms=50.0,
            max_ttfb_ms=500.0,
            min_ssl_days_remaining=45,
            healthy_count=95,
            unhealthy_count=5,
            last_http_status=200,
            last_ssl_expiration_date=None,
            last_checked_at=None,
            created_at=None,
        )
        saved = await summary_repo.save(s)
        assert saved.id is not None

        fetched = await summary_repo.get_by_url_id(sample_url.id, limit=1)
        assert len(fetched) == 1
        assert fetched[0].checks_count == 100

    async def test_upsert(self, summary_repo, sample_url):
        s = DailySummary(
            id=None,
            url_id=sample_url.id,
            summary_date=date(2026, 6, 11),
            checks_count=50,
            avg_ttfb_ms=100.0,
            min_ttfb_ms=50.0,
            max_ttfb_ms=300.0,
            min_ssl_days_remaining=30,
            healthy_count=48,
            unhealthy_count=2,
            last_http_status=200,
            last_ssl_expiration_date=None,
            last_checked_at=None,
            created_at=None,
        )
        saved = await summary_repo.save(s)
        s.checks_count = 60
        updated = await summary_repo.save(s)
        assert updated.id == saved.id
        fetched = await summary_repo.get_by_url_id_and_date(
            sample_url.id, date(2026, 6, 11)
        )
        assert fetched.checks_count == 60

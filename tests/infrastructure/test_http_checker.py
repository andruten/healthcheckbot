import httpx
import pytest

from healthchecker.infrastructure.checker.http_checker import HttpCheckResult, HttpHealthChecker


class TestHttpHealthChecker:
    @pytest.fixture
    def checker(self):
        return HttpHealthChecker(timeout=5.0)

    async def test_successful_request(self, checker, respx_mock):
        route = respx_mock.get("https://example.com").mock(
            return_value=httpx.Response(200, content="ok"),
        )
        result = await checker.check("https://example.com")
        assert isinstance(result, HttpCheckResult)
        assert result.status_code == 200
        assert result.ttfb_ms is not None and result.ttfb_ms >= 0
        assert result.error is None
        assert route.called

    async def test_not_found(self, checker, respx_mock):
        respx_mock.get("https://example.com/404").mock(
            return_value=httpx.Response(404),
        )
        result = await checker.check("https://example.com/404")
        assert result.status_code == 404
        assert result.error is None

    async def test_timeout(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        result = await checker.check("https://example.com")
        assert result.status_code is None
        assert result.ttfb_ms is None
        assert result.error == "Timeout"

    async def test_request_error(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(
            side_effect=httpx.RequestError("DNS failure")
        )
        result = await checker.check("https://example.com")
        assert result.status_code is None
        assert result.ttfb_ms is None
        assert result.error == "DNS failure"

    async def test_unexpected_error(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(side_effect=RuntimeError("weird"))
        result = await checker.check("https://example.com")
        assert result.status_code is None
        assert result.ttfb_ms is None
        assert result.error == "weird"

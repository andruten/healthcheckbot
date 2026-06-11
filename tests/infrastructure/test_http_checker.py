import httpx
import pytest

from healthchecker.infrastructure.checker.http_checker import HttpHealthChecker


class TestHttpHealthChecker:
    @pytest.fixture
    def checker(self):
        return HttpHealthChecker(timeout=5.0)

    async def test_successful_request(self, checker, respx_mock):
        route = respx_mock.get("https://example.com").mock(
            return_value=httpx.Response(200, content="ok"),
        )
        status, ttfb, error = await checker.check("https://example.com")
        assert status == 200
        assert ttfb is not None and ttfb >= 0
        assert error is None
        assert route.called

    async def test_not_found(self, checker, respx_mock):
        respx_mock.get("https://example.com/404").mock(
            return_value=httpx.Response(404),
        )
        status, ttfb, error = await checker.check("https://example.com/404")
        assert status == 404
        assert error is None

    async def test_timeout(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(
            side_effect=httpx.TimeoutException("timeout")
        )
        status, ttfb, error = await checker.check("https://example.com")
        assert status is None
        assert ttfb is None
        assert error == "Timeout"

    async def test_request_error(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(
            side_effect=httpx.RequestError("DNS failure")
        )
        status, ttfb, error = await checker.check("https://example.com")
        assert status is None
        assert ttfb is None
        assert error == "DNS failure"

    async def test_unexpected_error(self, checker, respx_mock):
        respx_mock.get("https://example.com").mock(side_effect=RuntimeError("weird"))
        status, ttfb, error = await checker.check("https://example.com")
        assert status is None
        assert ttfb is None
        assert error == "weird"

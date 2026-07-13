import logging
import ssl

import pytest

from healthchecker.infrastructure.checker.ssl_checker import SslChecker


class TestSslChecker:
    @pytest.fixture
    def checker(self):
        return SslChecker()

    def test_extract_host_https(self, checker):
        host = checker._extract_host("https://example.com/path")
        assert host == "example.com"

    def test_extract_host_http(self, checker):
        host = checker._extract_host("http://sub.example.com:8080/page")
        assert host == "sub.example.com"

    def test_extract_host_invalid(self, checker):
        host = checker._extract_host("not-a-url")
        assert host is None

    def test_extract_host_empty(self, checker):
        host = checker._extract_host("")
        assert host is None

    async def test_certificate_verification_failure_logs_warning_without_traceback(
        self, checker, mocker, caplog
    ):
        mocker.patch.object(
            checker,
            "_open_tls_connection",
            side_effect=ssl.SSLCertVerificationError("self-signed certificate"),
        )

        with caplog.at_level(logging.WARNING):
            result = await checker.check("https://example.com")

        assert result is None
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
        assert "SSL certificate verification failed" in record.message

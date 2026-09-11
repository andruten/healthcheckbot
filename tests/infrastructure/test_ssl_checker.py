import logging
import ssl
from urllib.parse import urlparse

import pytest

from healthchecker.infrastructure.checker.ssl_checker import SslChecker


class TestSslChecker:
    @pytest.fixture
    def checker(self):
        return SslChecker()

    def test_extract_host_https(self, checker):
        host = checker._extract_host_and_port("https://example.com/path")
        assert host == ("example.com", 443)

    def test_extract_host_http_with_port(self, checker):
        host = checker._extract_host_and_port("https://sub.example.com:8443/page")
        assert host == ("sub.example.com", 8443)

    def test_extract_host_imaps_default_port(self, checker):
        host = checker._extract_host_and_port("imaps://mail.example.com")
        assert host == ("mail.example.com", 993)

    def test_extract_host_imaps_custom_port(self, checker):
        host = checker._extract_host_and_port("imaps://mail.example.com:1993")
        assert host == ("mail.example.com", 1993)

    @pytest.mark.parametrize(
        "url,expected_port",
        [
            ("pop3s://mail.example.com", 995),
            ("smtps://smtp.example.com", 465),
            ("ftps://ftp.example.com", 990),
            ("ldaps://ldap.example.com", 636),
        ],
    )
    def test_extract_host_tls_schemes_default_ports(self, checker, url, expected_port):
        result = checker._extract_host_and_port(url)
        assert result == (urlparse(url).hostname, expected_port)

    def test_extract_host_bare_host_port(self, checker):
        host = checker._extract_host_and_port("mail.example.com:993")
        assert host == ("mail.example.com", 993)

    def test_extract_host_bare_host_without_port(self, checker):
        host = checker._extract_host_and_port("mail.example.com")
        assert host is None

    def test_extract_host_unknown_scheme(self, checker):
        host = checker._extract_host_and_port("ftp://example.com")
        assert host is None

    def test_extract_host_http_scheme_not_tls(self, checker):
        host = checker._extract_host_and_port("http://example.com:8080")
        assert host is None

    def test_extract_host_invalid_port(self, checker):
        host = checker._extract_host_and_port("imaps://mail.example.com:notaport")
        assert host is None

    def test_extract_host_invalid(self, checker):
        host = checker._extract_host_and_port("not-a-url")
        assert host is None

    def test_extract_host_empty(self, checker):
        host = checker._extract_host_and_port("")
        assert host is None

    def test_is_pure_tls_url(self, checker):
        assert checker.is_pure_tls_url("imaps://mail.example.com")
        assert checker.is_pure_tls_url("pop3s://mail.example.com")
        assert checker.is_pure_tls_url("mail.example.com:993")
        assert not checker.is_pure_tls_url("https://example.com")
        assert not checker.is_pure_tls_url("http://example.com")
        assert not checker.is_pure_tls_url("mail.example.com")

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

    async def test_network_error_logs_warning_without_traceback(
        self, checker, mocker, caplog
    ):
        import socket

        mocker.patch.object(
            checker,
            "_open_tls_connection",
            side_effect=socket.gaierror("Name or service not known"),
        )

        with caplog.at_level(logging.WARNING):
            result = await checker.check("https://unknown.example.com")

        assert result is None
        assert len(caplog.records) == 1
        record = caplog.records[0]
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
        assert "Network error checking SSL" in record.message

    @pytest.mark.parametrize(
        "teardown_error",
        [
            ssl.SSLError(1, "application data after close notify"),
            OSError("Connection reset by peer"),
        ],
    )
    async def test_teardown_error_after_cert_still_returns_info(
        self, checker, mocker, caplog, teardown_error
    ):
        writer = mocker.MagicMock()
        writer.get_extra_info.return_value.getpeercert.return_value = {
            "notAfter": "Sep 30 23:59:59 2099 GMT"
        }
        writer.wait_closed = mocker.AsyncMock(side_effect=teardown_error)
        mocker.patch.object(
            checker,
            "_open_tls_connection",
            return_value=(mocker.Mock(), writer),
        )

        with caplog.at_level(logging.WARNING):
            info = await checker.check("https://github.com")

        assert info is not None
        assert info.expiration_date.year == 2099
        assert info.days_remaining > 0
        assert caplog.records == []

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

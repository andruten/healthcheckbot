import asyncio
import logging
import ssl
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

TLS_SCHEME_PORTS: dict[str, int] = {
    "https": 443,
    "imaps": 993,
    "pop3s": 995,
    "smtps": 465,
    "ftps": 990,
    "ldaps": 636,
}


@dataclass
class SslInfo:
    expiration_date: datetime
    days_remaining: int


class SslChecker:
    async def check(self, url: str) -> SslInfo | None:
        try:
            target = self._extract_host_and_port(url)
            if not target:
                return None

            host, port = target
            ctx = ssl.create_default_context()
            _reader, writer = await self._open_tls_connection(host, port, ctx)

            cert = writer.get_extra_info("ssl_object").getpeercert()
            try:
                writer.close()
                await writer.wait_closed()
            except ssl.SSLError, OSError:
                pass

            if not cert:
                return None

            exp_str = cert.get("notAfter", "")
            if not exp_str:
                return None

            exp_date = datetime.strptime(exp_str, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=UTC
            )
            now = datetime.now(UTC)
            days_remaining = (exp_date - now).days

            return SslInfo(expiration_date=exp_date, days_remaining=days_remaining)

        except ssl.SSLCertVerificationError as e:
            logger.warning("SSL certificate verification failed for %s: %s", url, e)
            return None
        except ssl.SSLError as e:
            logger.warning("SSL check failed for %s: %s", url, e)
            return None
        except OSError as e:
            logger.warning("Network error checking SSL for %s: %s", url, e)
            return None
        except Exception:
            logger.exception("SSL check error for %s", url)
            return None

    @classmethod
    def _extract_host_and_port(cls, url: str) -> tuple[str, int] | None:
        try:
            if "://" in url:
                parsed = urlparse(url)
                host = parsed.hostname
                scheme = parsed.scheme.lower()
                if not host or scheme not in TLS_SCHEME_PORTS:
                    return None
                port = parsed.port or TLS_SCHEME_PORTS[scheme]
                return host, port

            parsed = urlparse(f"tls://{url}")
            host = parsed.hostname
            if not host or parsed.port is None:
                return None
            return host, parsed.port
        except ValueError:
            return None

    @staticmethod
    def is_tls_url(url: str) -> bool:
        if "://" in url:
            scheme = urlparse(url).scheme.lower()
            return scheme in TLS_SCHEME_PORTS
        parsed = urlparse(f"tls://{url}")
        return parsed.hostname is not None and parsed.port is not None

    @classmethod
    def is_pure_tls_url(cls, url: str) -> bool:
        if "://" not in url:
            parsed = urlparse(f"tls://{url}")
            return parsed.hostname is not None and parsed.port is not None
        scheme = urlparse(url).scheme.lower()
        return scheme in TLS_SCHEME_PORTS and scheme != "https"

    async def _open_tls_connection(self, host: str, port: int, ctx: ssl.SSLContext):
        return await asyncio.open_connection(host, port, ssl=ctx, server_hostname=host)

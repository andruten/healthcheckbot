import logging
import ssl
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class SslInfo:
    expiration_date: datetime
    days_remaining: int


class SslChecker:
    async def check(self, url: str) -> SslInfo | None:
        try:
            host = self._extract_host(url)
            if not host:
                return None

            ctx = ssl.create_default_context()
            reader, writer = await self._open_tls_connection(host, ctx)

            cert = writer.get_extra_info("ssl_object").getpeercert()
            writer.close()
            await writer.wait_closed()

            if not cert:
                return None

            exp_str = cert.get("notAfter", "")
            if not exp_str:
                return None

            exp_date = datetime.strptime(exp_str, "%b %d %H:%M:%S %Y %Z").replace(
                tzinfo=timezone.utc
            )
            now = datetime.now(timezone.utc)
            days_remaining = (exp_date - now).days

            return SslInfo(expiration_date=exp_date, days_remaining=days_remaining)

        except ssl.SSLCertVerificationError as e:
            logger.warning("SSL certificate verification failed for %s: %s", url, e)
            return None
        except ssl.SSLError as e:
            logger.warning("SSL check failed for %s: %s", url, e)
            return None
        except Exception as e:
            logger.error("SSL check error for %s: %s", url, e, exc_info=True)
            return None

    @staticmethod
    def _extract_host(url: str) -> str | None:
        from urllib.parse import urlparse

        parsed = urlparse(url)
        host = parsed.hostname
        if host:
            return host
        return None

    async def _open_tls_connection(self, host: str, ctx: ssl.SSLContext):
        import asyncio

        return await asyncio.open_connection(host, 443, ssl=ctx, server_hostname=host)

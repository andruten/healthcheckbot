import asyncio
import logging
from dataclasses import dataclass

import httpx

logger = logging.getLogger(__name__)


@dataclass
class HttpCheckResult:
    status_code: int | None
    ttfb_ms: float | None
    error: str | None


class HttpHealthChecker:
    def __init__(
        self,
        timeout: float = 10.0,
        max_attempts: int = 4,
        retry_delay: float = 2.0,
        max_connections: int = 100,
        max_keepalive_connections: int = 20,
    ):
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._retry_delay = retry_delay
        self._limits = httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_keepalive_connections,
        )
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self._timeout,
                follow_redirects=True,
                limits=self._limits,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def check(self, url: str) -> HttpCheckResult:
        client = self._get_client()
        error: str | None = None
        for attempt in range(self._max_attempts):
            try:
                response = await client.get(url)
                return HttpCheckResult(
                    status_code=response.status_code,
                    ttfb_ms=response.elapsed.total_seconds() * 1000,
                    error=None,
                )
            except httpx.TimeoutException:
                error = "Timeout"
                logger.warning("Timeout checking %s", url)
            except httpx.TransportError as e:
                error = str(e)
                logger.warning("Transport error checking %s: %s", url, e)
            except httpx.RequestError as e:
                logger.warning("Request error checking %s: %s", url, e)
                return HttpCheckResult(status_code=None, ttfb_ms=None, error=str(e))
            except Exception as e:
                logger.exception("Unexpected error checking %s", url)
                return HttpCheckResult(status_code=None, ttfb_ms=None, error=str(e))

            if attempt < self._max_attempts - 1:
                await asyncio.sleep(self._retry_delay)

        return HttpCheckResult(status_code=None, ttfb_ms=None, error=error)

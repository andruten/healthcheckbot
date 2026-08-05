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
        retry_attempts: int = 2,
        retry_delay: float = 0.5,
    ):
        self._timeout = timeout
        self._retry_attempts = retry_attempts
        self._retry_delay = retry_delay

    async def check(self, url: str) -> HttpCheckResult:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            for attempt in range(self._retry_attempts + 1):
                try:
                    response = await client.get(url, follow_redirects=True)
                    ttfb = response.elapsed.total_seconds() * 1000
                    return HttpCheckResult(
                        status_code=response.status_code, ttfb_ms=ttfb, error=None
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

                if attempt == self._retry_attempts:
                    return HttpCheckResult(status_code=None, ttfb_ms=None, error=error)

                await asyncio.sleep(self._retry_delay)

        raise RuntimeError("HTTP health check completed without a result")

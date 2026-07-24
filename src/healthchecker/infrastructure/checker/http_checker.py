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
    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    async def check(self, url: str) -> HttpCheckResult:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, follow_redirects=True)
                ttfb = response.elapsed.total_seconds() * 1000
                return HttpCheckResult(status_code=response.status_code, ttfb_ms=ttfb, error=None)
        except httpx.TimeoutException:
            logger.warning("Timeout checking %s", url)
            return HttpCheckResult(status_code=None, ttfb_ms=None, error="Timeout")
        except httpx.RequestError as e:
            logger.warning("Request error checking %s: %s", url, e)
            return HttpCheckResult(status_code=None, ttfb_ms=None, error=str(e))
        except Exception as e:
            logger.error("Unexpected error checking %s: %s", url, e, exc_info=True)
            return HttpCheckResult(status_code=None, ttfb_ms=None, error=str(e))

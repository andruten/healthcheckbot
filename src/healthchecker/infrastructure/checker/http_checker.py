import logging

import httpx

logger = logging.getLogger(__name__)


class HttpHealthChecker:
    def __init__(self, timeout: float = 10.0):
        self._timeout = timeout

    async def check(self, url: str) -> tuple[int | None, float | None, str | None]:
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                response = await client.get(url, follow_redirects=True)
                ttfb = response.elapsed.total_seconds() * 1000
                return response.status_code, ttfb, None
        except httpx.TimeoutException:
            logger.warning("Timeout checking %s", url)
            return None, None, "Timeout"
        except httpx.RequestError as e:
            logger.warning("Request error checking %s: %s", url, e)
            return None, None, str(e)
        except Exception as e:
            logger.error("Unexpected error checking %s: %s", url, e, exc_info=True)
            return None, None, str(e)

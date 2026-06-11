from healthchecker.domain.repositories.health_check_repository import (
    HealthCheckRepository,
)


class GetResultsUseCase:
    def __init__(self, health_check_repo: HealthCheckRepository):
        self._health_check_repo = health_check_repo

    async def get_latest(self, url_id: int):
        return await self._health_check_repo.get_latest_by_url_id(url_id)

    async def get_history(self, url_id: int, limit: int = 5):
        return await self._health_check_repo.get_by_url_id(url_id, limit=limit)

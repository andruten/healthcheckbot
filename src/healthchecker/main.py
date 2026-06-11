import asyncio
import logging

from healthchecker.infrastructure.config import settings
from healthchecker.infrastructure.persistence.database import (
    connect_database,
    close_database,
)
from healthchecker.infrastructure.persistence.url_repository import (
    TortoiseUrlRepository,
)
from healthchecker.infrastructure.persistence.health_check_repository import (
    TortoiseHealthCheckRepository,
)
from healthchecker.infrastructure.persistence.alert_repository import (
    TortoiseAlertRepository,
)
from healthchecker.infrastructure.persistence.daily_summary_repository import (
    TortoiseDailySummaryRepository,
)
from healthchecker.infrastructure.checker.http_checker import HttpHealthChecker
from healthchecker.infrastructure.checker.ssl_checker import SslChecker

from healthchecker.application.use_cases.manage_urls import ManageUrlsUseCase
from healthchecker.application.use_cases.get_results import GetResultsUseCase
from healthchecker.application.use_cases.check_all_urls import CheckAllUrlsUseCase
from healthchecker.application.use_cases.consolidate_summaries import (
    ConsolidateDailySummariesUseCase,
)

from healthchecker.interfaces.telegram.bot import TelegramBot
from healthchecker.interfaces.scheduler import Scheduler

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
app_log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.getLogger("healthchecker").setLevel(app_log_level)
logger = logging.getLogger(__name__)


async def main():
    logger.info("Starting Health Checker...")

    await connect_database()

    url_repo = TortoiseUrlRepository()
    health_check_repo = TortoiseHealthCheckRepository()
    alert_repo = TortoiseAlertRepository()
    summary_repo = TortoiseDailySummaryRepository()

    http_checker = HttpHealthChecker()
    ssl_checker = SslChecker()

    manage_urls = ManageUrlsUseCase(url_repo)
    get_results = GetResultsUseCase(health_check_repo)
    check_all_urls = CheckAllUrlsUseCase(
        url_repo,
        health_check_repo,
        alert_repo,
        http_checker,
        ssl_checker,
    )
    consolidate = ConsolidateDailySummariesUseCase(
        health_check_repo,
        summary_repo,
        settings.retention_days,
    )

    bot = TelegramBot(manage_urls, get_results, check_all_urls, summary_repo)
    scheduler = Scheduler(check_all_urls, consolidate)

    try:
        await asyncio.gather(
            bot.start(),
            scheduler.start(),
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        await scheduler.stop()
        await bot.stop()
        await close_database()


if __name__ == "__main__":
    asyncio.run(main())

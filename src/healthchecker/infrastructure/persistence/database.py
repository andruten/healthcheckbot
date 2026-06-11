import logging

from tortoise import Tortoise

from healthchecker.infrastructure.persistence.tortoise_config import TORTOISE_CONFIG

logger = logging.getLogger(__name__)


async def connect_database():
    await Tortoise.init(config=TORTOISE_CONFIG)
    logger.info("Connected to database")


async def close_database():
    await Tortoise.close_connections()
    logger.info("Database connections closed")

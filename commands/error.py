import logging

logger = logging.getLogger(__name__)


async def error(update, context):
    """Log Errors caused by Updates."""
    logger.error('Update "%s" caused error "%s"', update, context.error)

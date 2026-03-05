import sys

from loguru import logger

from app.core.settings import settings


def configure_logger() -> None:
    """Configure loguru logger with settings."""
    logger.remove()

    log_level = (
        settings.LOG_LEVEL.value
        if hasattr(settings.LOG_LEVEL, "value")
        else str(settings.LOG_LEVEL)
    )

    logger.add(
        sys.stderr,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    )

    if settings.LOG_TO_FILE:
        logger.add(
            "logs/app.log",
            rotation="500 MB",
            retention="10 days",
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )
        logger.add(
            "logs/error.log",
            rotation="100 MB",
            retention="30 days",
            level="ERROR",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        )
        logger.add(
            "logs/trade_history.log",
            rotation="100 MB",
            retention="90 days",
            level="INFO",
            filter=lambda record: record["extra"].get("trade"),
            format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        )


configure_logger()
__all__ = ["logger", "configure_logger"]

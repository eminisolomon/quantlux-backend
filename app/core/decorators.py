"""
Centralized decorators for QuantLux.
Merged from app/core/decorators/ sub-package.
"""

import asyncio
import functools
import inspect
import time
from collections.abc import Callable
from typing import Any

from app.core import messages as msg
from app.utils.logger import logger


def retry_on_error(
    max_retries: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
):
    """Retry decorator with exponential backoff for async and sync functions."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    await asyncio.sleep(delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            delay = initial_delay
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} failed after {max_retries} retries: {e}"
                        )
                        raise

                    logger.warning(
                        f"{func.__name__} attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                    delay *= backoff_factor

            if last_exception:
                raise last_exception

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def fallback_on_failure(default_return: Any = None):
    """Decorator to catch exceptions and return a safe default fallback value."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{func.__name__} failed: {e}. Using fallback: {default_return}"
                )
                return default_return

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"{func.__name__} failed: {e}. Using fallback: {default_return}"
                )
                return default_return

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def require_feature(
    feature_flag: str,
    fallback_return: Any = None,
):
    """
    Decorator to guard functions behind a settings feature flag.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            from app.core.settings import settings  # local import to avoid circular

            is_enabled = getattr(settings, feature_flag, False)
            if not is_enabled:
                logger.debug(f"Skipping {func.__name__} - {feature_flag} is disabled.")
                return fallback_return
            return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            from app.core.settings import settings

            is_enabled = getattr(settings, feature_flag, False)
            if not is_enabled:
                logger.debug(f"Skipping {func.__name__} - {feature_flag} is disabled.")
                return fallback_return
            return func(*args, **kwargs)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def log_latency(level: str = "DEBUG"):
    """Decorator to log the execution time of a function."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return await func(*args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                msg = f"{func.__name__} executed in {elapsed:.4f}s"
                if hasattr(logger, level.lower()):
                    getattr(logger, level.lower())(msg)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed = time.time() - start_time
                msg = f"{func.__name__} executed in {elapsed:.4f}s"
                if hasattr(logger, level.lower()):
                    getattr(logger, level.lower())(msg)

        if inspect.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


__all__ = [
    "retry_on_error",
    "fallback_on_failure",
    "require_feature",
    "log_latency",
]

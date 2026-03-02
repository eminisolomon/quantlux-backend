"""MetaApi connection package with production features."""

from app.core.decorators import retry_on_error
from app.metaapi.connection.client import (
    MetaApiConnection,
    initialize_metaapi,
)
from app.metaapi.connection.health_monitor import ConnectionHealthMonitor
from app.metaapi.connection.latency import LatencyMonitor
from app.metaapi.connection.manager import ConnectionManager
from app.metaapi.rate_limiter import RateLimiter


def get_rate_limiter() -> RateLimiter:
    return MetaApiConnection.get_rate_limiter()


def get_latency_monitor() -> LatencyMonitor:
    return MetaApiConnection.get_latency_monitor()


__all__ = [
    "MetaApiConnection",
    "initialize_metaapi",
    "ConnectionManager",
    "ConnectionHealthMonitor",
    "retry_on_error",
    "get_rate_limiter",
    "RateLimiter",
    "get_latency_monitor",
    "LatencyMonitor",
]

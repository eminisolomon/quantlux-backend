"""MetaApi Cloud SDK connection management with production resilience."""

import asyncio
from typing import Optional

from metaapi_cloud_sdk import MetaApi

from app.core.decorators import retry_on_error
from app.core.settings import settings
from app.metaapi.connection.health_monitor import ConnectionHealthMonitor
from app.metaapi.connection.manager import ConnectionManager
from app.metaapi.rate_limiter import RateLimiter
from app.utils.logger import logger


class MetaApiConnection:
    """Manages MetaApi cloud connection lifecycle with auto-reconnect."""

    _api: MetaApi | None = None
    _account = None
    _connection = None
    _connection_manager: ConnectionManager | None = None
    _is_connected: bool = False
    _rate_limiter: RateLimiter | None = None
    _health_monitor: Optional["ConnectionHealthMonitor"] = None

    @classmethod
    @retry_on_error(max_retries=3, initial_delay=2.0)
    async def initialize(cls) -> bool:
        """Initialize connection to MetaApi cloud."""
        try:
            if not cls._validate_settings():
                return False

            if not await cls._init_api():
                return False

            if not await cls._setup_account():
                return False

            if not await cls._create_connection():
                return False

            cls._setup_connection_manager()

            cls._rate_limiter = RateLimiter(calls_per_second=10.0)

            await cls._setup_health_monitor()

            cls._is_connected = True
            logger.info(
                f"✅ MetaApi connected successfully to {cls._account.name} ({cls._account.type})"
            )
            return True

        except Exception as e:
            logger.error(f"MetaApi initialization failed: {e}")
            cls._is_connected = False
            return False

    @classmethod
    def _validate_settings(cls) -> bool:
        """Validate required settings."""
        if not settings.METAAPI_TOKEN:
            logger.error("METAAPI_TOKEN not configured")
            return False

        if not settings.METAAPI_ACCOUNT_ID:
            logger.error("METAAPI_ACCOUNT_ID not configured")
            return False

        return True

    @classmethod
    async def _init_api(cls) -> bool:
        """Initialize MetaApi SDK."""
        try:
            logger.info("Initializing MetaApi SDK...")
            cls._api = MetaApi(token=settings.METAAPI_TOKEN)
            return True
        except Exception as e:
            logger.error(f"Failed to initialize API: {e}")
            return False

    @classmethod
    async def _setup_account(cls) -> bool:
        """Setup and deploy account."""
        try:
            logger.info(f"Fetching account {settings.METAAPI_ACCOUNT_ID}...")
            cls._account = await cls._api.metatrader_account_api.get_account(
                settings.METAAPI_ACCOUNT_ID
            )

            if cls._account.state != "DEPLOYED":
                logger.warning(f"Account state is {cls._account.state}, deploying...")
                await cls._account.deploy()

            logger.info("Waiting for account deployment...")
            await cls._account.wait_deployed()

            return True
        except Exception as e:
            logger.error(f"Failed to setup account: {e}")
            return False

    @classmethod
    async def _create_connection(cls) -> bool:
        """Create and connect streaming connection."""
        try:
            logger.info("Creating streaming connection...")
            cls._connection = cls._account.get_streaming_connection()

            logger.info("Connecting to MetaTrader terminal...")
            await cls._connection.connect()

            logger.info("Waiting for terminal synchronization...")
            await cls._connection.wait_synchronized()

            return True
        except Exception as e:
            logger.error(f"Failed to create connection: {e}")
            return False

    @classmethod
    def _setup_connection_manager(cls):
        """Setup connection manager for auto-reconnect."""
        cls._connection_manager = ConnectionManager(
            connection=cls._connection, reconnect_delay=5.0, max_reconnect_attempts=10
        )
        cls._connection_manager.is_connected = True

    @classmethod
    async def _setup_health_monitor(cls):
        """Setup and start health monitoring."""
        from app.metaapi.connection.health_monitor import (
            ConnectionHealthMonitor,
        )

        if cls._connection_manager:
            cls._health_monitor = ConnectionHealthMonitor(
                connection_manager=cls._connection_manager
            )
            await cls._health_monitor.start_monitoring()
            logger.info("📡 Connection health monitoring active")

    @classmethod
    async def ensure_connected(cls) -> bool:
        """Ensure connection is active, reconnect if needed."""
        if cls._connection_manager:
            return await cls._connection_manager.ensure_connected()

        if cls._is_connected and cls._connection:
            try:
                if cls._connection.is_synchronized:
                    return True
                else:
                    logger.warning("Connection lost synchronization, reconnecting...")
                    return await cls.reconnect()
            except Exception:
                return await cls.reconnect()
        else:
            return await cls.initialize()

    @classmethod
    async def reconnect(cls) -> bool:
        """Attempt to reconnect to MetaApi."""
        logger.info("Reconnecting to MetaApi...")
        await cls.shutdown()
        return await cls.initialize()

    @classmethod
    async def shutdown(cls) -> None:
        """Shutdown MetaApi connection."""
        try:
            if cls._connection_manager:
                await cls._connection_manager.close()

            if cls._connection:
                logger.info("Closing MetaApi connection...")
                await cls._connection.close()

            if cls._health_monitor:
                await cls._health_monitor.stop_monitoring()

            cls._is_connected = False
            logger.info("MetaApi connection closed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

    @classmethod
    def get_connection(cls):
        """Get the active MetaApi streaming connection."""
        if not cls._connection:
            raise RuntimeError("MetaApi not connected. Call initialize() first.")
        return cls._connection

    @classmethod
    def get_account(cls):
        """Get the MetaApi account object."""
        if not cls._account:
            raise RuntimeError("MetaApi account not loaded. Call initialize() first.")
        return cls._account

    @classmethod
    def get_connection_manager(cls) -> ConnectionManager | None:
        """Get the connection manager instance."""
        return cls._connection_manager

    @classmethod
    def is_connected(cls) -> bool:
        """Check if connected to MetaApi."""
        return cls._is_connected and cls._connection is not None

    @classmethod
    async def health_check(cls) -> bool:
        """Perform health check on MetaApi connection."""
        try:
            if not cls._connection:
                return False
            return cls._connection.is_synchronized
        except Exception:
            return False

    @classmethod
    async def get_terminal_state(cls) -> dict:
        """Get current terminal state information."""
        try:
            connection = cls.get_connection()
            terminal_state = connection.terminal_state

            return {
                "connected": terminal_state.connected,
                "connected_to_broker": terminal_state.connected_to_broker,
                "account_information": terminal_state.account_information,
                "positions": terminal_state.positions,
                "orders": terminal_state.orders,
            }
        except Exception as e:
            logger.error(f"Failed to get terminal state: {e}")
            return {}

    @classmethod
    def get_rate_limiter(cls) -> RateLimiter:
        """Get the rate limiter instance."""
        if not cls._rate_limiter:
            cls._rate_limiter = RateLimiter(calls_per_second=10.0)
        return cls._rate_limiter

    @classmethod
    def get_latency_monitor(cls):
        """Get the latency monitor instance."""
        from app.metaapi.connection.latency import LatencyMonitor

        if not hasattr(cls, "_latency_monitor") or not cls._latency_monitor:
            cls._latency_monitor = LatencyMonitor(alert_threshold_ms=500.0)
        return cls._latency_monitor


def initialize_metaapi() -> bool:
    """Synchronous wrapper for MetaApi initialization."""
    return asyncio.run(MetaApiConnection.initialize())

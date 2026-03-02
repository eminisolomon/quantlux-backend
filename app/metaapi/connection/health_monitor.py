"""Connection health monitoring for MetaApi WebSocket."""

import asyncio

from app.core.settings import settings
from app.metaapi.connection.manager import ConnectionManager
from app.utils.logger import logger


class ConnectionHealthMonitor:
    """Monitor connection health and detect issues."""

    def __init__(
        self,
        connection_manager: ConnectionManager,
        check_interval: float = None,
        timeout_threshold: float = None,
    ):
        """Initialize health monitor."""
        self.connection_manager = connection_manager
        self.check_interval = (
            check_interval
            if check_interval is not None
            else settings.WS_HEALTH_CHECK_INTERVAL
        )
        self.timeout_threshold = (
            timeout_threshold
            if timeout_threshold is not None
            else settings.WS_HEALTH_TIMEOUT
        )
        self.monitor_task: asyncio.Task | None = None
        self.is_monitoring = False

    async def start_monitoring(self):
        """Start health monitoring."""
        if self.is_monitoring:
            logger.warning("Health monitoring already running")
            return

        self.is_monitoring = True
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Connection health monitoring started")

    async def stop_monitoring(self):
        """Stop health monitoring."""
        self.is_monitoring = False
        if self.monitor_task and not self.monitor_task.done():
            self.monitor_task.cancel()
        logger.info("Connection health monitoring stopped")

    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self.is_monitoring:
            try:
                await asyncio.sleep(self.check_interval)

                if not self.connection_manager.is_connected:
                    logger.warning("Health check: Connection is down")
                    continue

                healthy = await self._perform_health_check()

                if not healthy:
                    logger.warning("Health check failed, triggering reconnection")
                    self.connection_manager.on_disconnect()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitoring: {e}")

    async def _perform_health_check(self) -> bool:
        """Return True if connection responds within timeout."""
        try:
            await asyncio.wait_for(
                self.connection_manager.connection.get_account_information(),
                timeout=self.timeout_threshold,
            )
            return True
        except TimeoutError:
            logger.warning("Health check timed out")
            return False
        except Exception as e:
            logger.warning(f"Health check failed: {e}")
            return False

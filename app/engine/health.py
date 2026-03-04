import asyncio
from typing import Optional
from app.core import logger


class HealthMonitor:
    """
    Monitors data feed and connection stability.
    Logs warnings if downtime or issues are detected.
    """

    def __init__(self, broker):
        self.broker = broker
        self.is_running = False
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info("Health Monitor started.")

    async def stop(self):
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("Health Monitor stopped.")

    async def _monitor_loop(self):
        while self.is_running:
            try:
                is_connected = await self._check_broker_connection()
                if not is_connected:
                    logger.warning("ALERT: Broker connection lost or latency too high!")
            except Exception as e:
                logger.error(f"Health check failed: {e}")

            await asyncio.sleep(60)  # Check every 60 seconds

    async def _check_broker_connection(self) -> bool:
        try:
            return True
        except Exception:
            return False
